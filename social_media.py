import os
import json
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

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SocialMediaPoster:
    def __init__(self):
        """Initialize social media poster using environment variables"""
        self.clients = {}
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
                    results['bluesky'] = self.clients['bluesky'].send_post(text=text)
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
            except Exception as e:
                results[platform] = {'error': str(e)}
                
        return results 