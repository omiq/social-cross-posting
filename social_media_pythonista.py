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
            
        return results 