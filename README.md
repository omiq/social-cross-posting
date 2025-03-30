# Social Media Poster

A Python library for posting content to multiple social media platforms including Bluesky, Mastodon, Facebook, LinkedIn, Instagram, and Threads.

## Features

- Post text content
- Post images with captions
- Post links with previews (where supported)
- OAuth authentication support for Facebook and LinkedIn
- Environment variable based configuration
- Error handling for each platform

## Installation

1. Clone this repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

1. Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

2. Set up your environment variables in `.env`:

### Bluesky
- `BLUESKY_HANDLE`: Your Bluesky handle
- `BLUESKY_PASSWORD`: Your Bluesky password

### Mastodon
- `MASTODON_ACCESS_TOKEN`: Your Mastodon access token
- `MASTODON_API_BASE_URL`: Your Mastodon instance URL

### Facebook
- `FACEBOOK_ACCESS_TOKEN`: Your Facebook access token
- `FACEBOOK_PAGE_ID`: Your Facebook page ID (if posting to a page)

### LinkedIn
- `LINKEDIN_CLIENT_ID`: Your LinkedIn application client ID
- `LINKEDIN_CLIENT_SECRET`: Your LinkedIn application client secret
- `LINKEDIN_ACCESS_TOKEN`: Your LinkedIn access token

### Instagram
- `INSTAGRAM_USERNAME`: Your Instagram username
- `INSTAGRAM_PASSWORD`: Your Instagram password

### Threads
- `THREADS_USERNAME`: Your Threads username
- `THREADS_PASSWORD`: Your Threads password

## OAuth Authentication

For Facebook and LinkedIn, you can use OAuth authentication:

1. Create a Facebook/LinkedIn application in their respective developer consoles
2. Get your client ID and client secret
3. Set up a redirect URI in your application settings
4. Use the authentication methods:

```python
poster = SocialMediaPoster()

# LinkedIn OAuth
poster.authenticate_linkedin(
    client_id='your_client_id',
    client_secret='your_client_secret',
    redirect_uri='your_redirect_uri'
)

# Facebook OAuth
poster.authenticate_facebook(
    client_id='your_client_id',
    client_secret='your_client_secret',
    redirect_uri='your_redirect_uri'
)
```

## Usage

```python
from social_media import SocialMediaPoster

# Initialize the poster
poster = SocialMediaPoster()

# Post text to all platforms
poster.post_text("Hello, world!")

# Post text to specific platforms
poster.post_text("Hello, world!", platforms=['bluesky', 'mastodon'])

# Post image with caption
poster.post_image(
    "Check out this photo!",
    "path/to/image.jpg",
    alt_text="Description of the image"
)

# Post link with text
poster.post_link(
    "Check out this article!",
    "https://example.com/article"
)
```

## Security Notes

1. Never commit your `.env` file to version control
2. Keep your API keys and tokens secure
3. Use environment variables in production
4. Consider using a secrets management service in production

## Platform Limitations

- Instagram doesn't support text-only posts
- Instagram doesn't support clickable links in posts
- Threads supports both text-only posts and clickable links
- Some platforms may have rate limits or other restrictions

## License

This project is licensed under the GNU General Public License v3 - see the LICENSE file for details.
