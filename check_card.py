"""Check that a URL will produce a Bluesky link card, without posting it.

Runs everything post_link does for Bluesky (read the og: tags, upload the
thumbnail, build the embed) and stops before send_post, so it can be run
against a live URL safely. Pass an image to check a card built with your own
picture instead of the page's.

    python3 check_card.py https://example.com/article [image.jpg]
"""
import sys

import requests
from atproto import models

from social_media import SocialMediaPoster


def main(url, image_path=None):
    poster = SocialMediaPoster()
    client = poster.clients.get('bluesky')
    if client is None:
        print("Bluesky client did not initialise, check BLUESKY_* in .env")
        return 1

    title, description, image_url = poster._scrape_card(url)
    print(f"title:       {title!r}")
    print(f"description: {description[:80]!r}")
    print(f"image:       {image_url or 'none'}")

    if image_path:
        image_data = poster._resize_image(image_path, max_size_kb=900)
        print(f"override:    {image_path}, {len(image_data)} bytes after re-encoding")
    else:
        image_data = requests.get(image_url, timeout=20).content if image_url else None

    thumb_blob = None
    if image_data:
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
    if len(sys.argv) not in (2, 3):
        print(__doc__)
        raise SystemExit(2)
    raise SystemExit(main(*sys.argv[1:]))
