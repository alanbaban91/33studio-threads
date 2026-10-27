#!/usr/bin/env python3
"""Save numbers for recent posts to stats.json, for Control House.

Reads Threads (THREADS_TOKEN) and/or Instagram (IG_TOKEN), whichever is set.
A metric the token isn't allowed to read is left out and the reason goes in "errors",
so a missing permission never fails the run. Standard library only.
"""
import datetime
import json
import os
import urllib.error
import urllib.parse
import urllib.request

THREADS = "https://graph.threads.net/v1.0"
INSTAGRAM = "https://graph.instagram.com"
POSTS = 40


def get(base, path, params):
    url = f"{base}/{path}?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        try:
            body = json.loads(body)["error"]["message"]
        except (ValueError, KeyError, TypeError):
            pass
        raise RuntimeError(f"{e.code}: {body}") from None


def metric_values(data):
    out = {}
    for m in data.get("data", []):
        if "total_value" in m:
            out[m["name"]] = m["total_value"].get("value", 0)
        else:
            out[m["name"]] = sum(v.get("value", 0) for v in m.get("values", []))
    return out


def threads(token, errors):
    posts = get(THREADS, "me/threads", {"fields": "id,text,timestamp,permalink,media_type", "limit": POSTS,
                                        "access_token": token}).get("data", [])
    rows = []
    for p in posts:
        row = {"id": p["id"], "at": p.get("timestamp"), "text": p.get("text") or "", "link": p.get("permalink")}
        try:
            row.update(metric_values(get(THREADS, f"{p['id']}/insights",
                                         {"metric": "views,likes,replies,reposts,quotes,shares", "access_token": token})))
        except RuntimeError as e:
            errors.append(f"Threads insights: {e}")
            break   # same permission problem for every post
        rows.append(row)
    return rows


def instagram(token, errors):
    posts = get(INSTAGRAM, "me/media", {"fields": "id,caption,timestamp,permalink,like_count,comments_count",
                                        "limit": POSTS, "access_token": token}).get("data", [])
    rows, insights_ok = [], True
    for p in posts:
        row = {"id": p["id"], "at": p.get("timestamp"), "text": p.get("caption") or "", "link": p.get("permalink"),
               "likes": p.get("like_count", 0), "replies": p.get("comments_count", 0)}
        if insights_ok:
            try:
                row.update(metric_values(get(INSTAGRAM, f"{p['id']}/insights",
                                             {"metric": "views,reach,saved,shares", "access_token": token})))
            except RuntimeError as e:
                errors.append(f"Instagram insights (views, reach, saves): {e}")
                insights_ok = False   # keep likes and comments, skip the rest
        rows.append(row)
    return rows


def main():
    out = {"updated": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "errors": []}
    for key, env, fn in (("threads", "THREADS_TOKEN", threads), ("instagram", "IG_TOKEN", instagram)):
        token = os.environ.get(env)
        if not token:
            continue
        try:
            out[key] = fn(token, out["errors"])
        except RuntimeError as e:
            out["errors"].append(f"{key.title()}: {e}")
    with open("stats.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"Saved stats: {', '.join(f'{len(out[k])} {k}' for k in ('threads', 'instagram') if k in out) or 'nothing'}.")
    for e in out["errors"]:
        print(f"::warning::{e}")


if __name__ == "__main__":
    main()
