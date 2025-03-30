import os
from typing import Optional, List, Dict, Any
from atproto import Client as BlueskyClient
from mastodon import Mastodon
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.page import Page
from facebook_business.adobjects.user import User
from linkedin_api import Linkedin
from instagram_private_api import Client as InstagramClient
from PIL import Image
import requests
import json
from dotenv import load_dotenv
from urllib.parse import urlencode
import webbrowser

# Load environment variables
load_dotenv()

class SocialMediaPoster:
    def __init__(self):
        """Initialize social media poster using environment variables"""
        self.clients = {}
        self._initialize_clients()

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
        except Exception as e:
            print(f"Failed to initialize Bluesky client: {e}")

        # Mastodon
        try:
            self.clients['mastodon'] = Mastodon(
                access_token=self._get_env_var('MASTODON_ACCESS_TOKEN'),
                api_base_url=self._get_env_var('MASTODON_API_BASE_URL')
            )
        except Exception as e:
            print(f"Failed to initialize Mastodon client: {e}")

        # Facebook
        try:
            FacebookAdsApi.init(access_token=self._get_env_var('FACEBOOK_ACCESS_TOKEN'))
            self.clients['facebook'] = FacebookAdsApi.get_instance()
        except Exception as e:
            print(f"Failed to initialize Facebook client: {e}")

        # LinkedIn
        try:
            self.clients['linkedin'] = Linkedin(
                client_id=self._get_env_var('LINKEDIN_CLIENT_ID'),
                client_secret=self._get_env_var('LINKEDIN_CLIENT_SECRET'),
                access_token=self._get_env_var('LINKEDIN_ACCESS_TOKEN')
            )
        except Exception as e:
            print(f"Failed to initialize LinkedIn client: {e}")

        # Instagram
        try:
            self.clients['instagram'] = InstagramClient(
                self._get_env_var('INSTAGRAM_USERNAME'),
                self._get_env_var('INSTAGRAM_PASSWORD')
            )
        except Exception as e:
            print(f"Failed to initialize Instagram client: {e}")

        # Threads (uses Instagram API)
        try:
            self.clients['threads'] = InstagramClient(
                self._get_env_var('THREADS_USERNAME'),
                self._get_env_var('THREADS_PASSWORD')
            )
        except Exception as e:
            print(f"Failed to initialize Threads client: {e}")

    @staticmethod
    def get_linkedin_auth_url(client_id: str, redirect_uri: str) -> str:
        """
        Generate LinkedIn OAuth URL for user authentication
        
        Args:
            client_id: LinkedIn client ID
            redirect_uri: Redirect URI after authentication
            
        Returns:
            OAuth URL
        """
        params = {
            'response_type': 'code',
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'scope': 'r_liteprofile r_emailaddress w_member_social',
            'state': 'random_state_string'  # In production, use a secure random string
        }
        return f"https://www.linkedin.com/oauth/v2/authorization?{urlencode(params)}"

    @staticmethod
    def get_facebook_auth_url(client_id: str, redirect_uri: str) -> str:
        """
        Generate Facebook OAuth URL for user authentication
        
        Args:
            client_id: Facebook client ID
            redirect_uri: Redirect URI after authentication
            
        Returns:
            OAuth URL
        """
        params = {
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'scope': 'pages_manage_posts,pages_read_engagement,publish_to_groups',
            'response_type': 'code',
            'state': 'random_state_string'  # In production, use a secure random string
        }
        return f"https://www.facebook.com/v12.0/dialog/oauth?{urlencode(params)}"

    def authenticate_linkedin(self, client_id: str, client_secret: str, redirect_uri: str):
        """
        Authenticate with LinkedIn using OAuth flow
        
        Args:
            client_id: LinkedIn client ID
            client_secret: LinkedIn client secret
            redirect_uri: Redirect URI after authentication
        """
        auth_url = self.get_linkedin_auth_url(client_id, redirect_uri)
        print(f"Please visit this URL to authenticate with LinkedIn: {auth_url}")
        webbrowser.open(auth_url)
        
        # In a real application, you would handle the redirect and get the code
        # For this example, we'll just print instructions
        print("\nAfter authenticating, you'll be redirected to your redirect_uri with a code parameter.")
        print("Use that code to get your access token and update your .env file.")

    def authenticate_facebook(self, client_id: str, client_secret: str, redirect_uri: str):
        """
        Authenticate with Facebook using OAuth flow
        
        Args:
            client_id: Facebook client ID
            client_secret: Facebook client secret
            redirect_uri: Redirect URI after authentication
        """
        auth_url = self.get_facebook_auth_url(client_id, redirect_uri)
        print(f"Please visit this URL to authenticate with Facebook: {auth_url}")
        webbrowser.open(auth_url)
        
        # In a real application, you would handle the redirect and get the code
        # For this example, we'll just print instructions
        print("\nAfter authenticating, you'll be redirected to your redirect_uri with a code parameter.")
        print("Use that code to get your access token and update your .env file.")

    def post_text(self, text: str, platforms: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Post text content to specified platforms
        
        Args:
            text: The text content to post
            platforms: List of platform names to post to. If None, posts to all initialized platforms.
            
        Returns:
            Dictionary containing results from each platform
        """
        if platforms is None:
            platforms = list(self.clients.keys())
            
        results = {}
        
        for platform in platforms:
            try:
                if platform == 'bluesky':
                    results['bluesky'] = self.clients['bluesky'].send_post(text=text)
                elif platform == 'mastodon':
                    results['mastodon'] = self.clients['mastodon'].toot(text)
                elif platform == 'facebook':
                    # Post to Facebook page
                    page = Page('me')
                    results['facebook_page'] = page.create_feed_entry(
                        fields=[],
                        params={'message': text}
                    )
                    # Post to Facebook profile
                    user = User('me')
                    results['facebook_profile'] = user.create_feed_entry(
                        fields=[],
                        params={'message': text}
                    )
                elif platform == 'linkedin':
                    results['linkedin'] = self.clients['linkedin'].post(
                        text=text,
                        visibility='PUBLIC'
                    )
                elif platform == 'instagram':
                    # Instagram doesn't support text-only posts
                    results['instagram'] = {'error': 'Text-only posts not supported'}
                elif platform == 'threads':
                    # Threads supports text-only posts
                    results['threads'] = self.clients['threads'].post_text(text)
            except Exception as e:
                results[platform] = {'error': str(e)}
                
        return results

    def post_image(self, text: str, image_path: str, alt_text: str = '', 
                  platforms: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Post image with caption to specified platforms
        
        Args:
            text: The caption text
            image_path: Path to the image file
            alt_text: Alt text for accessibility
            platforms: List of platform names to post to. If None, posts to all initialized platforms.
            
        Returns:
            Dictionary containing results from each platform
        """
        if platforms is None:
            platforms = list(self.clients.keys())
            
        results = {}
        
        # Read image file
        with open(image_path, 'rb') as f:
            image_data = f.read()
            
        for platform in platforms:
            try:
                if platform == 'bluesky':
                    # Get image dimensions
                    img = Image.open(image_path)
                    width, height = img.size
                    
                    # Upload image
                    results['bluesky'] = self.clients['bluesky'].send_image(
                        text=text,
                        image=image_data,
                        image_alt=alt_text,
                        image_aspect_ratio={'width': width, 'height': height}
                    )
                elif platform == 'mastodon':
                    # Upload media first
                    media = self.clients['mastodon'].media_post(
                        image_data,
                        description=alt_text
                    )
                    # Then post with media
                    results['mastodon'] = self.clients['mastodon'].toot(
                        text,
                        media_ids=[media['id']]
                    )
                elif platform == 'facebook':
                    # Post to Facebook page
                    page = Page('me')
                    results['facebook_page'] = page.create_photo(
                        fields=[],
                        params={
                            'message': text,
                            'source': image_data
                        }
                    )
                    # Post to Facebook profile
                    user = User('me')
                    results['facebook_profile'] = user.create_photo(
                        fields=[],
                        params={
                            'message': text,
                            'source': image_data
                        }
                    )
                elif platform == 'linkedin':
                    # LinkedIn requires image to be uploaded first
                    results['linkedin'] = self.clients['linkedin'].post(
                        text=text,
                        image_path=image_path,
                        visibility='PUBLIC'
                    )
                elif platform == 'instagram':
                    # Instagram requires image to be uploaded first
                    results['instagram'] = self.clients['instagram'].post_photo(
                        image_path,
                        caption=text
                    )
                elif platform == 'threads':
                    # Threads uses Instagram API
                    results['threads'] = self.clients['threads'].post_photo(
                        image_path,
                        caption=text
                    )
            except Exception as e:
                results[platform] = {'error': str(e)}
                
        return results

    def post_link(self, text: str, url: str, platforms: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Post link with text to specified platforms
        
        Args:
            text: The text content
            url: The URL to link to
            platforms: List of platform names to post to. If None, posts to all initialized platforms.
            
        Returns:
            Dictionary containing results from each platform
        """
        if platforms is None:
            platforms = list(self.clients.keys())
            
        results = {}
        
        for platform in platforms:
            try:
                if platform == 'bluesky':
                    # Get link preview data
                    response = requests.get(url)
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Extract metadata
                    title = soup.find('meta', property='og:title')['content']
                    description = soup.find('meta', property='og:description')['content']
                    image_url = soup.find('meta', property='og:image')['content']
                    
                    # Download and upload image
                    image_data = requests.get(image_url).content
                    
                    # Create link card
                    results['bluesky'] = self.clients['bluesky'].send_post(
                        text=text,
                        embed={
                            'type': 'app.bsky.embed.external',
                            'external': {
                                'uri': url,
                                'title': title,
                                'description': description,
                                'thumb': image_data
                            }
                        }
                    )
                elif platform == 'mastodon':
                    results['mastodon'] = self.clients['mastodon'].toot(f"{text}\n\n{url}")
                elif platform == 'facebook':
                    # Post to Facebook page
                    page = Page('me')
                    results['facebook_page'] = page.create_feed_entry(
                        fields=[],
                        params={'message': f"{text}\n\n{url}"}
                    )
                    # Post to Facebook profile
                    user = User('me')
                    results['facebook_profile'] = user.create_feed_entry(
                        fields=[],
                        params={'message': f"{text}\n\n{url}"}
                    )
                elif platform == 'linkedin':
                    results['linkedin'] = self.clients['linkedin'].post(
                        text=f"{text}\n\n{url}",
                        visibility='PUBLIC'
                    )
                elif platform == 'instagram':
                    # Instagram doesn't support clickable links in posts
                    results['instagram'] = {'error': 'Link posts not supported'}
                elif platform == 'threads':
                    # Threads supports clickable links
                    results['threads'] = self.clients['threads'].post_text(
                        text=f"{text}\n\n{url}"
                    )
            except Exception as e:
                results[platform] = {'error': str(e)}
                
        return results 