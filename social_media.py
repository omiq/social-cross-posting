import os
import json
import requests
from bs4 import BeautifulSoup
from PIL import Image
import base64
from io import BytesIO

class SocialMediaPoster:
    def __init__(self):
        """Initialize social media poster using environment variables"""
        self.credentials = self._load_credentials()
        self._validate_credentials()
        
    def _load_credentials(self):
        """Load credentials from .env file"""
        credentials = {}
        try:
            with open('.env', 'r') as f:
                for line in f:
                    if '=' in line:
                        key, value = line.strip().split('=', 1)
                        credentials[key] = value
        except Exception as e:
            print(f"Error loading credentials: {e}")
        return credentials
        
    def _validate_credentials(self):
        """Validate that required credentials are present"""
        required = {
            'BLUESKY_HANDLE': 'Bluesky handle',
            'BLUESKY_PASSWORD': 'Bluesky password',
            'MASTODON_ACCESS_TOKEN': 'Mastodon access token',
            'MASTODON_API_BASE_URL': 'Mastodon instance URL'
        }
        
        missing = []
        for key, description in required.items():
            if key not in self.credentials:
                missing.append(f"{description} ({key})")
                
        if missing:
            print("Missing required credentials:")
            for item in missing:
                print(f"- {item}")
                
    def _get_image_data(self, image_path):
        """Convert image to base64"""
        with Image.open(image_path) as img:
            buffered = BytesIO()
            img.save(buffered, format="JPEG")
            return base64.b64encode(buffered.getvalue()).decode()
            
    def post_text(self, text: str, platforms: list = None) -> dict:
        """Post text content to specified platforms"""
        if platforms is None:
            platforms = ['bluesky', 'mastodon']
            
        results = {}
        
        for platform in platforms:
            try:
                if platform == 'bluesky':
                    # Bluesky API call
                    url = 'https://bsky.social/xrpc/com.atproto.repo.createRecord'
                    headers = {
                        'Authorization': f'Bearer {self.credentials["BLUESKY_PASSWORD"]}',
                        'Content-Type': 'application/json'
                    }
                    data = {
                        'repo': self.credentials['BLUESKY_HANDLE'],
                        'collection': 'app.bsky.feed.post',
                        'record': {
                            'text': text,
                            'createdAt': '2024-03-30T00:00:00.000Z'
                        }
                    }
                    response = requests.post(url, headers=headers, json=data)
                    results['bluesky'] = response.json()
                    
                elif platform == 'mastodon':
                    # Mastodon API call
                    url = f"{self.credentials['MASTODON_API_BASE_URL']}/api/v1/statuses"
                    headers = {
                        'Authorization': f'Bearer {self.credentials["MASTODON_ACCESS_TOKEN"]}',
                        'Content-Type': 'application/json'
                    }
                    data = {
                        'status': text,
                        'visibility': 'public'
                    }
                    response = requests.post(url, headers=headers, json=data)
                    results['mastodon'] = response.json()
                    
            except Exception as e:
                results[platform] = {'error': str(e)}
                
        return results
        
    def post_image(self, text: str, image_path: str, alt_text: str = '', 
                  platforms: list = None) -> dict:
        """Post image with caption to specified platforms"""
        if platforms is None:
            platforms = ['bluesky', 'mastodon']
            
        results = {}
        
        try:
            # Convert image to base64
            image_data = self._get_image_data(image_path)
            
            for platform in platforms:
                try:
                    if platform == 'bluesky':
                        # Bluesky API call
                        url = 'https://bsky.social/xrpc/com.atproto.repo.createRecord'
                        headers = {
                            'Authorization': f'Bearer {self.credentials["BLUESKY_PASSWORD"]}',
                            'Content-Type': 'application/json'
                        }
                        data = {
                            'repo': self.credentials['BLUESKY_HANDLE'],
                            'collection': 'app.bsky.feed.post',
                            'record': {
                                'text': text,
                                'embed': {
                                    'type': 'app.bsky.embed.images',
                                    'images': [{
                                        'alt': alt_text,
                                        'image': image_data
                                    }]
                                },
                                'createdAt': '2024-03-30T00:00:00.000Z'
                            }
                        }
                        response = requests.post(url, headers=headers, json=data)
                        results['bluesky'] = response.json()
                        
                    elif platform == 'mastodon':
                        # Mastodon API call
                        url = f"{self.credentials['MASTODON_API_BASE_URL']}/api/v1/media"
                        headers = {
                            'Authorization': f'Bearer {self.credentials["MASTODON_ACCESS_TOKEN"]}',
                            'Content-Type': 'multipart/form-data'
                        }
                        files = {
                            'file': ('image.jpg', image_data, 'image/jpeg')
                        }
                        response = requests.post(url, headers=headers, files=files)
                        media_id = response.json()['id']
                        
                        # Post status with media
                        status_url = f"{self.credentials['MASTODON_API_BASE_URL']}/api/v1/statuses"
                        status_data = {
                            'status': text,
                            'media_ids': [media_id],
                            'visibility': 'public'
                        }
                        response = requests.post(status_url, headers=headers, json=status_data)
                        results['mastodon'] = response.json()
                        
                except Exception as e:
                    results[platform] = {'error': str(e)}
                    
        except Exception as e:
            results['error'] = str(e)
            
        return results
        
    def post_link(self, text: str, url: str, platforms: list = None) -> dict:
        """Post link with text to specified platforms"""
        if platforms is None:
            platforms = ['bluesky', 'mastodon']
            
        results = {}
        
        try:
            # Get link preview data
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract metadata
            title = soup.find('meta', property='og:title')['content']
            description = soup.find('meta', property='og:description')['content']
            image_url = soup.find('meta', property='og:image')['content']
            
            # Download image
            image_response = requests.get(image_url)
            image_data = base64.b64encode(image_response.content).decode()
            
            for platform in platforms:
                try:
                    if platform == 'bluesky':
                        # Bluesky API call
                        api_url = 'https://bsky.social/xrpc/com.atproto.repo.createRecord'
                        headers = {
                            'Authorization': f'Bearer {self.credentials["BLUESKY_PASSWORD"]}',
                            'Content-Type': 'application/json'
                        }
                        data = {
                            'repo': self.credentials['BLUESKY_HANDLE'],
                            'collection': 'app.bsky.feed.post',
                            'record': {
                                'text': text,
                                'embed': {
                                    'type': 'app.bsky.embed.external',
                                    'external': {
                                        'uri': url,
                                        'title': title,
                                        'description': description,
                                        'thumb': image_data
                                    }
                                },
                                'createdAt': '2024-03-30T00:00:00.000Z'
                            }
                        }
                        response = requests.post(api_url, headers=headers, json=data)
                        results['bluesky'] = response.json()
                        
                    elif platform == 'mastodon':
                        # Mastodon API call
                        api_url = f"{self.credentials['MASTODON_API_BASE_URL']}/api/v1/statuses"
                        headers = {
                            'Authorization': f'Bearer {self.credentials["MASTODON_ACCESS_TOKEN"]}',
                            'Content-Type': 'application/json'
                        }
                        data = {
                            'status': f"{text}\n\n{url}",
                            'visibility': 'public'
                        }
                        response = requests.post(api_url, headers=headers, json=data)
                        results['mastodon'] = response.json()
                        
                except Exception as e:
                    results[platform] = {'error': str(e)}
                    
        except Exception as e:
            results['error'] = str(e)
            
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
from bs4 import BeautifulSoup
import mimetypes

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
            self.clients['facebook'] = FacebookAdsApi()
        except Exception as e:
            print(f"Failed to initialize Facebook client: {e}")

        # LinkedIn
        try:
            self.clients['linkedin'] = Linkedin(
                username=self._get_env_var('LINKEDIN_USERNAME'),
                password=self._get_env_var('LINKEDIN_PASSWORD')
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

    def _get_image_size(self, image_path: str) -> tuple:
        """Get image dimensions"""
        with Image.open(image_path) as img:
            return img.size

    def post_text(self, text: str, platforms: Optional[List[str]] = None) -> Dict[str, Any]:
        """Post text content to specified platforms"""
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
                    results['threads'] = self.clients['threads'].post_direct_message(text)
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
        
        # Read image file
        with open(image_path, 'rb') as f:
            image_data = f.read()
            
        # Get mime type
        mime_type = mimetypes.guess_type(image_path)[0]
        if not mime_type or not mime_type.startswith('image/'):
            mime_type = 'image/jpeg'
            
        for platform in platforms:
            try:
                if platform == 'bluesky':
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
                        mime_type=mime_type,
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
                    results['linkedin'] = self.clients['linkedin'].post(
                        text=text,
                        image_path=image_path,
                        visibility='PUBLIC'
                    )
                elif platform == 'instagram':
                    results['instagram'] = self.clients['instagram'].post_photo(
                        image_path,
                        caption=text,
                        size=(width, height)
                    )
                elif platform == 'threads':
                    results['threads'] = self.clients['threads'].post_photo(
                        image_path,
                        caption=text,
                        size=(width, height)
                    )
            except Exception as e:
                results[platform] = {'error': str(e)}
                
        return results

    def post_link(self, text: str, url: str, platforms: Optional[List[str]] = None) -> Dict[str, Any]:
        """Post link with text to specified platforms"""
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
                    results['threads'] = self.clients['threads'].post_direct_message(f"{text}\n\n{url}")
            except Exception as e:
                results[platform] = {'error': str(e)}
                
        return results 