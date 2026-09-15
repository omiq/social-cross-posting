#!/usr/bin/env python3
"""Get and keep a Threads access token for posting.

    python3 threads_token.py login     # once: approve in the browser, store a 60-day token
    python3 threads_token.py adopt     # or: after pasting a dashboard-generated token into .env
    python3 threads_token.py refresh   # keep it alive: run monthly

The token and user id are written to .env beside this file and never printed.
Threads tokens expire after 60 days unless refreshed, and a refresh is refused
until a token is at least 24 hours old, so refresh on a schedule rather than
waiting for a post to fail.

The redirect URI must match one listed in the app's Threads settings exactly.
It defaults to https://localhost/threads-callback; set THREADS_REDIRECT_URI in
.env to use another.
"""
import sys
import time
import urllib.parse
import webbrowser
from pathlib import Path

import requests
from dotenv import dotenv_values

HERE = Path(__file__).resolve().parent
ENV = HERE / ".env"
SCOPES = "threads_basic,threads_content_publish"
DEFAULT_REDIRECT = "https://localhost/threads-callback"


def settings():
    values = dotenv_values(ENV)
    missing = [key for key in ("THREADS_APP_ID", "THREADS_APP_SECRET") if not values.get(key)]
    if missing:
        sys.exit(f"missing from {ENV}: {', '.join(missing)}")
    return values


def save(updates):
    """Rewrite only the given keys, leaving every other line of .env alone."""
    lines = ENV.read_text().splitlines() if ENV.exists() else []
    seen = set()
    for index, line in enumerate(lines):
        key = line.split("=", 1)[0].strip()
        if key in updates:
            lines[index] = f"{key}={updates[key]}"
            seen.add(key)
    lines += [f"{key}={value}" for key, value in updates.items() if key not in seen]
    ENV.write_text("\n".join(lines) + "\n")


def check(response, step):
    """Meta's error bodies say what went wrong and carry no secrets. The
    request can carry the token or the app secret, so only the body is shown."""
    if response.status_code != 200:
        sys.exit(f"{step} failed: HTTP {response.status_code} {response.text[:300]}")
    return response.json()


def valid_until(expires_in):
    expires = int(time.time()) + int(expires_in or 0)
    return expires, time.strftime("%Y-%m-%d", time.localtime(expires))


def login():
    env = settings()
    redirect = env.get("THREADS_REDIRECT_URI") or DEFAULT_REDIRECT
    authorise = "https://threads.com/oauth/authorize?" + urllib.parse.urlencode({
        "client_id": env["THREADS_APP_ID"],
        "redirect_uri": redirect,
        "scope": SCOPES,
        "response_type": "code",
    })

    print("Opening the Threads authorisation page. Approve it, and the browser will")
    print(f"land on {redirect}, which will not load. That is expected.")
    print("Copy the full address from the address bar and paste it here.\n")
    webbrowser.open(authorise)
    landed = input("Address: ").strip()

    query = urllib.parse.parse_qs(urllib.parse.urlparse(landed).query)
    if query.get("error"):
        sys.exit(f"authorisation refused: {query['error'][0]}")
    # Threads appends #_ to the redirect, and it is not part of the code.
    code = query.get("code", [""])[0].split("#")[0]
    if not code:
        sys.exit("no code in that address")

    short = check(requests.post("https://graph.threads.com/oauth/access_token", data={
        "client_id": env["THREADS_APP_ID"],
        "client_secret": env["THREADS_APP_SECRET"],
        "grant_type": "authorization_code",
        "redirect_uri": redirect,
        "code": code,
    }, timeout=30), "code exchange")

    long = check(requests.get("https://graph.threads.net/access_token", params={
        "grant_type": "th_exchange_token",
        "client_secret": env["THREADS_APP_SECRET"],
        "access_token": short["access_token"],
    }, timeout=30), "long-lived exchange")

    expires, until = valid_until(long.get("expires_in"))
    save({
        "THREADS_ACCESS_TOKEN": long["access_token"],
        "THREADS_USER_ID": str(short["user_id"]),
        "THREADS_TOKEN_EXPIRES": str(expires),
    })
    print(f"\nSaved to {ENV.name}. Token valid until {until}.")


def adopt():
    """Take a token made by the dashboard's User Token Generator.

    The generator skips the whole login: it hands a Threads tester a long-lived
    token directly. Paste it into .env as THREADS_ACCESS_TOKEN, then run this to
    fill in the user id posting needs. The generator does not say when the
    token expires, so the date recorded is the 60 days it is documented to last,
    counted from now, and a refresh straight away gives a real one once the
    token is a day old.
    """
    env = dotenv_values(ENV)
    token = env.get("THREADS_ACCESS_TOKEN")
    if not token:
        sys.exit(f"paste the generated token into {ENV.name} as THREADS_ACCESS_TOKEN first")
    me = check(requests.get("https://graph.threads.net/v1.0/me", params={
        "fields": "id,username",
        "access_token": token,
    }, timeout=30), "profile lookup")
    expires, until = valid_until(60 * 24 * 60 * 60)
    save({"THREADS_USER_ID": str(me["id"]), "THREADS_TOKEN_EXPIRES": str(expires)})
    print(f"Token works for @{me.get('username')}. User id saved; expiry recorded as about {until}.")


def refresh():
    env = settings()
    token = env.get("THREADS_ACCESS_TOKEN")
    if not token:
        sys.exit("no THREADS_ACCESS_TOKEN yet: run login first")
    fresh = check(requests.get("https://graph.threads.net/refresh_access_token", params={
        "grant_type": "th_refresh_token",
        "access_token": token,
    }, timeout=30), "refresh")
    expires, until = valid_until(fresh.get("expires_in"))
    save({"THREADS_ACCESS_TOKEN": fresh["access_token"], "THREADS_TOKEN_EXPIRES": str(expires)})
    print(f"Refreshed. Valid until {until}.")


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    if command == "login":
        login()
    elif command == "adopt":
        adopt()
    elif command == "refresh":
        refresh()
    else:
        sys.exit(__doc__)
