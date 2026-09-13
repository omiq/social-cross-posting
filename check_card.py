"""Check that a URL will produce a Bluesky link card, without posting it.

Runs everything post_link does for Bluesky (read the og: tags, upload the
thumbnail, build the embed) and stops before send_post, so it can be run
against a live URL safely.

    python3 check_card.py https://example.com/article
"""
import sys

import requests
from atproto import models
from bs4 import BeautifulSoup

from social_media import SocialMediaPoster


def main(url):
    poster = SocialMediaPoster()
    client = poster.clients.get('bluesky')
    if client is None:
        print("Bluesky client did not initialise, check BLUESKY_* in .env")
        return 1

    soup = BeautifulSoup(requests.get(url, timeout=20).text, 'html.parser')

    def og(name, fallback=''):
        tag = soup.find('meta', property=name)
        return tag.get('content', fallback) if tag else fallback

    title, description, image_url = og('og:title', url), og('og:description'), og('og:image')
    print(f"title:       {title!r}")
    print(f"description: {description[:80]!r}")
    print(f"image:       {image_url or 'none'}")

    thumb_blob = None
    if image_url:
        image_data = requests.get(image_url, timeout=20).content
        thumb_blob = client.upload_blob(image_data).blob
        print(f"thumb:       uploaded {len(image_data)} bytes, {thumb_blob.mime_type}")

    models.AppBskyEmbedExternal.Main(
        external=models.AppBskyEmbedExternal.External(
            title=title, description=description, uri=url, thumb=thumb_blob
        )
    )
    print("embed:       valid, card would post")
    return 0


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(__doc__)
        raise SystemExit(2)
    raise SystemExit(main(sys.argv[1]))
