#!/usr/bin/env python3
"""Publish the image post that `post.py render` just prepared (media/next.json) to the
33Studio Instagram account, with the same caption as on Threads. Run it before
`post.py publish`, which dequeues the post and deletes the images.

  QUEUE=photos-queue.json python3 ig.py   # needs IG_TOKEN; skips quietly if it isn't set
"""
import json, os, sys, time, urllib.request, urllib.parse, urllib.error
from post import load, parts, wait_public, QUEUE

API = "https://graph.instagram.com"


def api(method, path, params):
    data = urllib.parse.urlencode(params).encode()
    url = f"{API}/{path}"
    if method == "GET":
        url, data = url + "?" + data.decode(), None
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=data, method=method), timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f"Instagram API error {e.code}: {e.read().decode()}")


def wait_ready(cid, token):
    for _ in range(36):
        st = api("GET", cid, {"fields": "status_code", "access_token": token}).get("status_code")
        if st == "FINISHED":
            return
        if st in ("ERROR", "EXPIRED"):
            sys.exit(f"Instagram container {cid} failed with status {st}")
        time.sleep(5)
    sys.exit(f"Instagram container {cid} not ready in time")


def main():
    token = os.environ.get("IG_TOKEN")
    if not token:
        print("IG_TOKEN is not set; skipping Instagram.")
        return
    queue, names = load(QUEUE, []), load("media/next.json", [])
    if not queue or not names:
        print("Nothing with images to post; skipping Instagram.")
        return
    caption = parts(queue[0])[0]
    repo = os.environ.get("GITHUB_REPOSITORY") or sys.exit("GITHUB_REPOSITORY is not set.")
    branch = os.environ.get("GITHUB_REF_NAME", "main")
    urls = [f"https://raw.githubusercontent.com/{repo}/{branch}/media/{n}" for n in names[:10]]  # Instagram max 10
    for u in urls:
        wait_public(u)

    if len(urls) == 1:
        cid = api("POST", "me/media", {"image_url": urls[0], "caption": caption, "access_token": token})["id"]
    else:
        children = []
        for u in urls:
            child = api("POST", "me/media", {"image_url": u, "is_carousel_item": "true", "access_token": token})["id"]
            wait_ready(child, token)
            children.append(child)
        cid = api("POST", "me/media", {"media_type": "CAROUSEL", "children": ",".join(children),
                                        "caption": caption, "access_token": token})["id"]
    wait_ready(cid, token)
    pub = api("POST", "me/media_publish", {"creation_id": cid, "access_token": token})
    print(f"Published to Instagram (id {pub.get('id')}).")


if __name__ == "__main__":
    main()
