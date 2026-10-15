#!/usr/bin/env python3
"""33Studio reply bot: answers new comments on recent posts in the 33 Studio voice,
using a free Hugging Face chat model.

  python3 replies.py            # reply to new comments (needs THREADS_TOKEN, HF_TOKEN)
  DRY_RUN=1 python3 replies.py  # print the replies it would send, post nothing
"""
import json, os, re, sys, urllib.request, urllib.error
from post import api, publish, load, save, MAX_LEN

HF_URL = "https://router.huggingface.co/v1/chat/completions"
HF_MODEL = os.environ.get("HF_MODEL") or "meta-llama/Llama-3.1-8B-Instruct"
SEEN = "replied.json"
MAX_REPLIES = 10      # per run, so a spam wave can't flood the account
RECENT_POSTS = 20     # how many of our latest posts to check for comments

PROMPT = """You reply to comments on Threads for 33 Studio, a creative agency in Sulaymaniyah, Kurdistan.
Services: brand strategy & identity, naming, graphic design & packaging, illustration & ad concepts,
motion design, TVC & video production, AI TVC, AI workflows, 3D & VFX, social media & content systems,
website & app design. Work is made by hand: sketched first, argued over, redrawn, then built.
Website: 33studio.org. Email: hello@33studio.org.

Voice: warm, understanding, confident and brief, like a senior creative at a top agency. Witty when the
comment is playful, kind when someone is unsure or struggling, calm when someone disagrees.
Rules:
- Reply in the same language as the comment (Kurdish, Arabic or English).
- 1 to 3 short sentences. No emoji, no hashtags, no exclamation marks.
- Answer what they actually said. Thank people who are kind, briefly.
- If they ask about prices, timelines or availability: never give numbers; invite them to
  hello@33studio.org or 33studio.org so the team can answer properly.
- If they seem interested in working together, point them to 33studio.org.
- Never invent facts, clients, prices, awards or promises. Never name or discuss clients.
- Never argue, never be sarcastic about the commenter.
- If the comment is spam, abusive, political, religious, or doesn't need an answer (just an emoji
  or a tag), reply with exactly: SKIP
Output only the reply text."""


def ask_model(post_text, comment):
    body = json.dumps({
        "model": HF_MODEL, "max_tokens": 200, "temperature": 0.6,
        "messages": [{"role": "system", "content": PROMPT},
                     {"role": "user", "content": f"Our post:\n{post_text}\n\nTheir comment:\n{comment}"}],
    }).encode()
    req = urllib.request.Request(HF_URL, data=body, headers={
        "Authorization": f"Bearer {os.environ['HF_TOKEN']}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)["choices"][0]["message"]["content"].strip().strip('"')
    except urllib.error.HTTPError as e:
        sys.exit(f"Hugging Face error {e.code}: {e.read().decode()[:500]}")


def tidy(reply):
    # the voice has no emoji; models sometimes add them anyway
    reply = re.sub(r" {2,}", " ", "".join(ch for ch in reply if ord(ch) < 0x2190)).strip()   # keeps Latin, Arabic, Kurdish
    return None if not reply or reply.upper().startswith("SKIP") else reply[:MAX_LEN]


def main():
    token = os.environ.get("THREADS_TOKEN") or sys.exit("THREADS_TOKEN is not set.")
    os.environ.get("HF_TOKEN") or sys.exit("HF_TOKEN is not set.")
    dry = os.environ.get("DRY_RUN") == "1"
    seen = set(load(SEEN, []))
    me = api("GET", "me", {"fields": "username", "access_token": token})["username"]
    posts = api("GET", "me/threads", {"fields": "id,text", "limit": RECENT_POSTS, "access_token": token}).get("data", [])

    sent = 0
    for p in posts:
        convo = api("GET", f"{p['id']}/conversation",
                    {"fields": "id,text,username", "access_token": token}).get("data", [])
        for c in convo:
            if sent >= MAX_REPLIES:
                break
            if c["id"] in seen or c.get("username") == me or not c.get("text"):
                continue
            reply = tidy(ask_model(p.get("text", ""), c["text"]))
            print(f"@{c.get('username')}: {c['text']}\n  -> {reply or '(skipped)'}\n")
            if reply and not dry:
                publish({"media_type": "TEXT", "text": reply, "reply_to_id": c["id"]}, token)
                sent += 1
            if not dry:
                seen.add(c["id"])
                save(SEEN, sorted(seen))   # save as we go, so a crash never double-replies
    print(f"{'Would send' if dry else 'Sent'} replies. {sent} posted this run.")


if __name__ == "__main__":
    main()
