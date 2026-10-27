"""Keep the latest comments the reply bot handled in replies-log.json, for Control House.

Each entry: the comment, the reply sent (or planned, in a dry run; null when the bot had
no answer), and when. Only the last KEEP entries are kept. Standard library only.
"""
import datetime
import json

LOG = "replies-log.json"
KEEP = 300


def log_reply(platform, comment, reply, dry=False, note=""):
    try:
        with open(LOG, encoding="utf-8") as f:
            items = json.load(f)
    except (OSError, ValueError):
        items = []
    cid = comment.get("id")
    old = next((i for i in items if i.get("id") == cid), None)
    # dry runs see the same comments every run: don't rewrite (and re-commit) an unchanged entry
    if old and old.get("reply") == reply and old.get("dry") == dry:
        return
    items = [i for i in items if i.get("id") != cid]
    items.append({
        "id": cid,
        "at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "platform": platform,
        "user": comment.get("username"),
        "comment": comment.get("text"),
        "reply": reply,
        "dry": dry,
        "note": note,
    })
    with open(LOG, "w", encoding="utf-8") as f:
        json.dump(items[-KEEP:], f, ensure_ascii=False, indent=1)
