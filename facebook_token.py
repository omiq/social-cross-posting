#!/usr/bin/env python3
"""Get a Facebook Page access token that does not expire.

    python3 facebook_token.py                  # token from .env or the clipboard
    python3 facebook_token.py --page "Retro"   # pick a Page when there are several

Copy the short-lived user token from the Graph API Explorer (generated with
pages_show_list, pages_read_engagement and pages_manage_posts) with the copy
button beside it, then run this. It reads the clipboard rather than asking,
because Claude Code's ! prompt has no terminal to type into, and it is never
printed. It is swapped for a 60-day user token, and
that is used to ask for the Page's own token, which does not expire as long as
the app keeps its permissions and you stay an admin of the Page.

Needs FACEBOOK_APP_ID and FACEBOOK_APP_SECRET in .env, from the app's
Settings > Basic. FACEBOOK_PAGE_ID and FACEBOOK_ACCESS_TOKEN are written back
to .env and never printed.
"""
import argparse
import subprocess
import sys

import requests
from dotenv import dotenv_values

from threads_token import ENV, check, save

GRAPH = "https://graph.facebook.com/v21.0"


def main():
    values = dotenv_values(ENV)
    missing = [k for k in ("FACEBOOK_APP_ID", "FACEBOOK_APP_SECRET") if not values.get(k)]
    if missing:
        sys.exit(f"missing from {ENV}: {', '.join(missing)} (the app's Settings > Basic)")

    ap = argparse.ArgumentParser()
    ap.add_argument("--page", help="part of the Page's name, when you run more than one")
    args = ap.parse_args()

    # A FACEBOOK_USER_TOKEN line in .env wins over the clipboard: Chrome's copy
    # button did not always reach the system clipboard. The line is removed
    # once it has been used, since the token is dead in an hour anyway.
    short = (values.get("FACEBOOK_USER_TOKEN") or "").strip() or \
        subprocess.run(["pbpaste"], capture_output=True, text=True).stdout.strip()
    if not short.startswith("EA"):
        sys.exit("no Facebook token found: paste it into .env as FACEBOOK_USER_TOKEN=... and run again")

    long_lived = check(requests.get(f"{GRAPH}/oauth/access_token", params={
        "grant_type": "fb_exchange_token",
        "client_id": values["FACEBOOK_APP_ID"],
        "client_secret": values["FACEBOOK_APP_SECRET"],
        "fb_exchange_token": short,
    }, timeout=30), "exchanging for a long-lived user token")["access_token"]

    pages = check(requests.get(f"{GRAPH}/me/accounts", params={
        "fields": "id,name,access_token,tasks", "access_token": long_lived,
    }, timeout=30), "listing your Pages").get("data", [])
    if not pages:
        sys.exit("no Pages came back: tick the Page in the Explorer's approval popup and try again")

    for number, page in enumerate(pages, 1):
        can_post = "CREATE_CONTENT" in (page.get("tasks") or [])
        print(f"  {number}. {page['name']} ({page['id']}){'' if can_post else '  (cannot post)'}")
    matches = [p for p in pages if not args.page or args.page.lower() in p["name"].lower()]
    if not matches:
        sys.exit(f"no Page matching {args.page!r} came back: tick it in the Explorer's approval popup")
    if len(matches) > 1:
        sys.exit("more than one Page: run again with --page and part of its name")
    choice = matches[0]

    save({"FACEBOOK_PAGE_ID": choice["id"], "FACEBOOK_ACCESS_TOKEN": choice["access_token"]})
    ENV.write_text("".join(line for line in ENV.read_text().splitlines(keepends=True)
                           if not line.startswith("FACEBOOK_USER_TOKEN=")))
    print(f"saved the Page token for {choice['name']} to {ENV}")


if __name__ == "__main__":
    main()
