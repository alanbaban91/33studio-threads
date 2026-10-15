#!/usr/bin/env python3
"""One-time helper: get a long-lived (60-day) Threads access token.
Run on your own computer:  python3 get_token.py
"""
import json
import urllib.parse
import urllib.request

app_id = input("Threads App ID: ").strip()
secret = input("Threads App Secret: ").strip()
redirect = input("Redirect URI (exactly as set in your app, e.g. https://33studio.org/): ").strip()

auth_url = "https://threads.net/oauth/authorize?" + urllib.parse.urlencode({
    "client_id": app_id,
    "redirect_uri": redirect,
    "scope": "threads_basic,threads_content_publish,threads_read_replies,threads_manage_replies",
    "response_type": "code",
})
print("\n1) Open this link, log in, and approve:\n" + auth_url)
back = input("\n2) Paste the full URL you were redirected to: ").strip()
code = urllib.parse.parse_qs(urllib.parse.urlparse(back).query)["code"][0].split("#")[0]

# Exchange code for a short-lived token
data = urllib.parse.urlencode({
    "client_id": app_id, "client_secret": secret,
    "grant_type": "authorization_code", "redirect_uri": redirect, "code": code,
}).encode()
with urllib.request.urlopen("https://graph.threads.net/oauth/access_token", data=data) as r:
    short = json.load(r)["access_token"]

# Exchange for a long-lived token (60 days)
q = urllib.parse.urlencode({"grant_type": "th_exchange_token", "client_secret": secret, "access_token": short})
with urllib.request.urlopen("https://graph.threads.net/access_token?" + q) as r:
    long_lived = json.load(r)

print("\nYour long-lived token (save it as the THREADS_TOKEN secret on GitHub):\n")
print(long_lived["access_token"])
print(f"\nExpires in about {long_lived.get('expires_in', 0) // 86400} days (auto-refreshed by the workflow).")
