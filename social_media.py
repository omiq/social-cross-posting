import os
import json
import re
import requests
from bs4 import BeautifulSoup
from PIL import Image
import base64
from io import BytesIO
from typing import Optional, List, Dict, Any
from atproto import Client as BlueskyClient
from mastodon import Mastodon
from dotenv import load_dotenv
import mimetypes
import logging
import time

# Load environment variables
load_dotenv()

# A Bluesky handle is dotted (adrian.bsky.social, adriansdigitalbasement.com),
# so require a dot and let resolution decide the rest. The lookbehind keeps an
# email address out of it: the @ in "me@example.com" follows a word character.
MENTION = re.compile(rb'(?<![\w.@/-])@((?:[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?\.)+[A-Za-z]{2,})')
URL_IN_TEXT = re.compile(rb'https?://[^\s<>"\)\]]+')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SocialMediaPoster:
    def __init__(self):
        """Initialize social media poster using environment variables"""
        self.clients = {}
        # Handle -> DID, so a run that credits the same channel twice asks once.
        self._dids: Dict[str, Optional[str]] = {}
        self._initialize_clients()
        
    def print_setup_guide(self):
        """Print a guide for setting up the social media poster"""
        print("\n===== SOCIAL MEDIA POSTER SETUP GUIDE =====")
        print("This guide will help you set up your credentials for each platform.")
        print("\n1. BLUESKY")
        print("   - Create an account at https://bsky.social if you don't have one")
        print("   - Add these to your .env file:")
        print("     BLUESKY_HANDLE=your.handle.here")
        print("     BLUESKY_PASSWORD=your_app_password")
        print("   - Note: Use an app password if you have 2FA enabled")
        
        print("\n2. MASTODON")
        print("   - Create an account on your preferred Mastodon instance")
        print("   - Go to Preferences > Development > New Application")
        print("   - Create an app with 'read' and 'write' permissions")
        print("   - Add these to your .env file:")
        print("     MASTODON_ACCESS_TOKEN=your_access_token")
        print("     MASTODON_API_BASE_URL=https://your.instance.url")
        
    # Platforms only posted to when named. Everything else is the default.
    OPT_IN = {'facebook'}

    def _get_env_var(self, key: str) -> str:
        """Get environment variable or raise error if not set"""
        value = os.getenv(key)
        if not value:
            raise ValueError(f"Environment variable {key} is not set")
        return value

    def _initialize_clients(self):
        """Initialize API clients for each platform using environment variables"""
        # Bluesky
        try:
            self.clients['bluesky'] = BlueskyClient()
            self.clients['bluesky'].login(
                self._get_env_var('BLUESKY_HANDLE'),
                self._get_env_var('BLUESKY_PASSWORD')
            )
            print("✓ Bluesky client initialized successfully")
        except Exception as e:
            print(f"✗ Failed to initialize Bluesky client: {e}")

        # Mastodon
        try:
            self.clients['mastodon'] = Mastodon(
                access_token=self._get_env_var('MASTODON_ACCESS_TOKEN'),
                api_base_url=self._get_env_var('MASTODON_API_BASE_URL')
            )
            print("✓ Mastodon client initialized successfully")
        except Exception as e:
            print(f"✗ Failed to initialize Mastodon client: {e}")

        # Threads. No SDK: a token and two HTTP calls. The token comes from
        # threads_token.py and lasts 60 days unless refreshed.
        try:
            self.clients['threads'] = {
                'token': self._get_env_var('THREADS_ACCESS_TOKEN'),
                'user_id': self._get_env_var('THREADS_USER_ID'),
            }
            print("✓ Threads client initialized successfully")
        except Exception as e:
            print(f"✗ Failed to initialize Threads client: {e}")

        # Facebook Page. Like Threads, a token and plain Graph calls. It needs a
        # Page access token (pages_manage_posts), not a user token, and it is
        # opt-in: left out of the default platform list, so a caller that says
        # nothing about platforms never starts posting to the Page.
        try:
            page_id = self._get_env_var('FACEBOOK_PAGE_ID')
            if not page_id.isdigit():
                raise ValueError("FACEBOOK_PAGE_ID is not a numeric page id")
            self.clients['facebook'] = {
                'token': self._get_env_var('FACEBOOK_ACCESS_TOKEN'),
                'page_id': page_id,
            }
            print("✓ Facebook Page client initialized successfully")
        except Exception as e:
            print(f"✗ Failed to initialize Facebook Page client: {e}")

        # Print summary of available platforms
        print("\n===== AVAILABLE PLATFORMS =====")
        for platform, client in self.clients.items():
            status = "✓ Available" if client is not None else "✗ Not available"
            print(f"{platform}: {status}")

    def _get_image_size(self, image_path: str) -> tuple:
        """Get image dimensions"""
        with Image.open(image_path) as img:
            return img.size
            
    def _resize_image(self, image_path: str, max_size_kb: int = 900) -> bytes:
        """Resize image to be under max_size_kb while maintaining aspect ratio"""
        with Image.open(image_path) as img:
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            # Start with original size
            width, height = img.size
            quality = 95
            
            while True:
                # Save to bytes with current quality
                buffer = BytesIO()
                img.save(buffer, format='JPEG', quality=quality)
                size_kb = len(buffer.getvalue()) / 1024
                
                if size_kb <= max_size_kb or quality <= 5:
                    return buffer.getvalue()
                
                # Reduce quality or size
                if quality > 5:
                    quality -= 5
                else:
                    width = int(width * 0.9)
                    height = int(height * 0.9)
                    img = img.resize((width, height), Image.Resampling.LANCZOS)
                    quality = 95

    def post_text(self, text: str, platforms: Optional[List[str]] = None) -> Dict[str, Any]:
        """Post text content to specified platforms"""
        if platforms is None:
            platforms = list(self.clients.keys())
            
        results = {}
        
        for platform in platforms:
            try:
                if platform == 'bluesky':
                    results['bluesky'] = self.clients['bluesky'].send_post(
                        text=text, facets=self._facets(text))
                elif platform == 'mastodon':
                    results['mastodon'] = self.clients['mastodon'].toot(text)
            except Exception as e:
                results[platform] = {'error': str(e)}
                
        return results

    def post_image(self, text: str, image_path: str, alt_text: str = '', 
                  platforms: Optional[List[str]] = None) -> Dict[str, Any]:
        """Post image with caption to specified platforms"""
        if platforms is None:
            platforms = list(self.clients.keys())
            
        results = {}
        
        # Get image dimensions
        width, height = self._get_image_size(image_path)
        
        # Resize image for Bluesky (max 976.56KB)
        resized_image = self._resize_image(image_path, max_size_kb=900)
            
        # Get mime type
        mime_type = mimetypes.guess_type(image_path)[0]
        if not mime_type or not mime_type.startswith('image/'):
            mime_type = 'image/jpeg'
            
        for platform in platforms:
            try:
                if platform == 'bluesky':
                    results['bluesky'] = self.clients['bluesky'].send_image(
                        text=text,
                        image=resized_image,
                        image_alt=alt_text,
                        facets=self._facets(text),
                        image_aspect_ratio={'width': width, 'height': height}
                    )
                elif platform == 'mastodon':
                    # Upload media first
                    media = self.clients['mastodon'].media_post(
                        resized_image,
                        mime_type=mime_type,
                        description=alt_text
                    )
                    # Then post with media
                    results['mastodon'] = self.clients['mastodon'].status_post(
                        text,
                        media_ids=[media['id']]
                    )
            except Exception as e:
                results[platform] = {'error': str(e)}
                
        return results

    def _resolve_handle(self, handle: str) -> Optional[str]:
        """A Bluesky handle as the DID a mention has to carry. None if nobody
        answers to it, which is how a typo stays plain text instead of tagging
        a stranger."""
        if handle in self._dids:
            return self._dids[handle]
        did = None
        try:
            did = self.clients['bluesky'].com.atproto.identity.resolve_handle(
                {'handle': handle}).did
        except Exception as e:
            logger.info(f"bluesky handle {handle} did not resolve: {e}")
        self._dids[handle] = did
        return did

    def _facets(self, text: str) -> List[Any]:
        """Mentions and links in the text, marked up so Bluesky treats them as
        mentions and links.

        A plain string carries no markup of its own, so "@adrian.bsky.social"
        posts as grey text: not a link, and no notification for the person
        being credited. Mastodon and Threads resolve handles server-side and
        need none of this.

        The ranges are byte offsets into the UTF-8, not character positions:
        an emoji earlier in the post shifts everything after it by three.
        """
        if 'bluesky' not in self.clients:
            return []
        from atproto import models

        raw = text.encode('utf-8')
        facets = []

        for match in MENTION.finditer(raw):
            did = self._resolve_handle(match.group(1).decode('utf-8'))
            if not did:
                continue
            facets.append(models.AppBskyRichtextFacet.Main(
                index=models.AppBskyRichtextFacet.ByteSlice(
                    byteStart=match.start(), byteEnd=match.end()),
                features=[models.AppBskyRichtextFacet.Mention(did=did)]))

        for match in URL_IN_TEXT.finditer(raw):
            found = match.group(0).decode('utf-8')
            # Trailing punctuation belongs to the sentence, not the address.
            trimmed = found.rstrip('.,;:!?')
            facets.append(models.AppBskyRichtextFacet.Main(
                index=models.AppBskyRichtextFacet.ByteSlice(
                    byteStart=match.start(),
                    byteEnd=match.start() + len(trimmed.encode('utf-8'))),
                features=[models.AppBskyRichtextFacet.Link(uri=trimmed)]))

        return facets

    def _scrape_card(self, url: str) -> tuple:
        """Title, description and image URL from a page's og: tags.

        Any of the three can be missing, so read them defensively: indexing
        straight off the soup raises TypeError on a page without them.
        """
        soup = BeautifulSoup(requests.get(url, timeout=20).text, 'html.parser')

        def og(name, fallback=''):
            tag = soup.find('meta', property=name)
            return tag.get('content', fallback) if tag else fallback

        return og('og:title', url), og('og:description'), og('og:image')

    def _threads_call(self, method: str, path: str, **fields) -> Dict[str, Any]:
        """One Threads Graph call. Errors carry Meta's message, never the
        request: its URL or body holds the access token, and an exception from
        requests would put that in the result the picker shows."""
        client = self.clients['threads']
        fields['access_token'] = client['token']
        url = f"https://graph.threads.net/v1.0/{path}"
        if method == 'GET':
            response = requests.get(url, params=fields, timeout=30)
        else:
            response = requests.post(url, data=fields, timeout=30)
        if response.status_code != 200:
            raise RuntimeError(f"Threads HTTP {response.status_code}: {response.text[:300]}")
        return response.json()

    @staticmethod
    def _threads_topic(text: str) -> tuple:
        """Hashtags out of the text, the first one back as the post's topic.

        Threads allows one topic per post. Written in the text, the first tag
        becomes the topic and loses its hash, so "#retrogaming #retrocomputing"
        printed as "retrogaming #retrocomputing", which reads as a typo. The
        topic_tag field is Meta's preferred route, and it leaves the text clean.
        Topics are 1 to 50 characters with no periods or ampersands.
        """
        import re
        tag = r'(?<![\w#])#([A-Za-z][\w-]*)'
        tags = re.findall(tag, text)
        lines = []
        for line in text.splitlines():
            # A run of tags ending a line, or a line of nothing but tags, goes.
            # A tag inside a sentence keeps its word: deleting it turned
            # "Loving the #C64 scene" into "Loving the  scene".
            line = re.sub(r'(?:\s*(?<![\w#])#[A-Za-z][\w-]*)+\s*$', '', line)
            lines.append(re.sub(tag, r'\1', line).rstrip())
        body = re.sub(r'\n{3,}', '\n\n', '\n'.join(lines)).strip()
        topic = tags[0][:50] if tags else None
        return body, topic

    def _post_threads(self, text: str, topic: Optional[str] = None) -> Dict[str, Any]:
        """A text post. Threads builds its link preview from the first URL in
        the text, the way Mastodon crawls its card, so there is no card to set.

        Publishing is two steps, a container then a publish. Meta suggests
        waiting about 30 seconds between them; polling the container's status
        publishes as soon as it is ready instead of always waiting.
        """
        if len(text) > 500:
            raise ValueError(f"Threads allows 500 characters and this is {len(text)}")
        user_id = self.clients['threads']['user_id']
        fields = {'media_type': 'TEXT', 'text': text}
        if topic:
            fields['topic_tag'] = topic
        container = self._threads_call('POST', f"{user_id}/threads", **fields)['id']

        for _ in range(20):
            state = self._threads_call('GET', container, fields='status,error_message')
            if state.get('status') == 'FINISHED':
                break
            if state.get('status') in ('ERROR', 'EXPIRED'):
                raise RuntimeError(f"Threads container {state['status']}: {state.get('error_message')}")
            time.sleep(2)

        return self._threads_call('POST', f"{user_id}/threads_publish", creation_id=container)

    def post_link(self, text: str, url: str, platforms: Optional[List[str]] = None,
                  title: Optional[str] = None, description: Optional[str] = None,
                  image_path: Optional[str] = None,
                  image_url: Optional[str] = None) -> Dict[str, Any]:
        """Post link with text to specified platforms.

        The picture can come from a local file (image_path, a grabbed video
        still) or from the web (image_url, a better picture found inside the
        article than the one its feed offered). image_path wins if both are
        given; neither means the page's own og:image.

        title, description and image_path override what the target page says
        about itself on the Bluesky card, which is worth doing when the page
        describes something bigger than the thing being posted: a single story
        inside a round-up video, where the page's own og: tags are the whole
        video's title and the channel's boilerplate. Anything not passed is
        scraped as before. Mastodon builds its own card by crawling the URL and
        takes no say from us, so these do not reach it.
        """
        if platforms is None:
            platforms = [p for p in self.clients if p not in self.OPT_IN]

        results = {}

        for platform in platforms:
            try:
                if platform == 'bluesky':
                    from atproto import models

                    image_data = None
                    if image_path:
                        # Re-encodes, so an oversized still cannot blow the
                        # ~976KB blob limit.
                        image_data = self._resize_image(image_path, max_size_kb=900)
                    elif image_url:
                        image_data = requests.get(image_url, timeout=20).content

                    if title is None or description is None or image_data is None:
                        scraped_title, scraped_description, scraped_image = self._scrape_card(url)
                        if title is None:
                            title = scraped_title
                        if description is None:
                            description = scraped_description
                        if image_data is None and scraped_image:
                            image_data = requests.get(scraped_image, timeout=20).content

                    # The image has to be uploaded as a blob and the embed has
                    # to be a typed model. Passing a plain dict with raw bytes
                    # fails validation with "Unable to extract tag using
                    # discriminator 'py_type'", which is what used to happen.
                    thumb_blob = None
                    if image_data:
                        thumb_blob = self.clients['bluesky'].upload_blob(image_data).blob

                    embed_external = models.AppBskyEmbedExternal.Main(
                        external=models.AppBskyEmbedExternal.External(
                            title=title, description=description, uri=url, thumb=thumb_blob
                        )
                    )
                    results['bluesky'] = self.clients['bluesky'].send_post(
                        text=text, embed=embed_external, facets=self._facets(text)
                    )
                elif platform == 'mastodon':
                    results['mastodon'] = self.clients['mastodon'].toot(f"{text}\n\n{url}")
                elif platform == 'threads':
                    body, topic = self._threads_topic(text)
                    results['threads'] = self._post_threads(f"{body}\n\n{url}", topic)
                elif platform == 'facebook':
                    results['facebook'] = self._post_facebook(text, url)
            except Exception as e:
                results[platform] = {'error': str(e)}

        return results

    def _post_facebook(self, text: str, url: str) -> Dict[str, Any]:
        """A link post on the Page. Facebook crawls the URL for its own card,
        as Mastodon does. Errors carry Meta's message, never the request, which
        holds the token."""
        if 'facebook' not in self.clients:
            raise RuntimeError("Facebook Page is not configured (FACEBOOK_PAGE_ID, FACEBOOK_ACCESS_TOKEN)")
        client = self.clients['facebook']
        response = requests.post(
            f"https://graph.facebook.com/v21.0/{client['page_id']}/feed",
            data={'message': text, 'link': url, 'access_token': client['token']},
            timeout=30)
        if response.status_code != 200:
            raise RuntimeError(f"Facebook HTTP {response.status_code}: {response.text[:300]}")
        return response.json()