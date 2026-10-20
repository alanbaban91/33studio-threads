#!/usr/bin/env python3
"""33Studio reply bot: answers new comments that match known topics (price, working
together, location, jobs, thanks) in Kurdish, Arabic or English. No AI: comments that
match nothing get no reply, which is safer than a wrong one.

  python3 replies.py            # reply to new comments (needs THREADS_TOKEN)
  DRY_RUN=1 python3 replies.py  # print the replies it would send, post nothing
"""
import os, re, sys, zlib
from post import api, publish, load, save

SEEN = "replied.json"
MAX_REPLIES = 10      # per run, so a spam wave can't flood the account
RECENT_POSTS = 20     # how many of our latest posts to check for comments
KURDISH = set("\u0695\u06b5\u06ce\u06c6\u06d5\u067e\u0686\u0698\u06af\u06a4")   # ڕ ڵ ێ ۆ ە پ چ ژ گ ڤ

# Matches whole English words but lets Kurdish/Arabic stems take endings (کوێ -> کوێن).
# Checked in this order: the first topic that matches wins ("how much to work with you" is a price question).
TOPICS = [
    ("job", r"\b(job|jobs|intern|internship|vacanc\w*|hiring|are you hiring|portfolio review|دامەزراندن|کارمەند|ڕاهێنان|وظيفة|توظيف|تدريب)(?![a-z])"),
    ("price", r"\b(price|prices|pricing|cost|costs|how much|budget|rate|rates|نرخ|نرخی|چەند|پارە|سعر|اسعار|أسعار|كم(?!\w)|بكم(?!\w)|تكلفة)(?![a-z])"),
    ("where", r"\b(where are you|where is|location|address|office|لە کوێ|لەکوێ|ناونیشان|شوێن|وين|أين|اين|عنوان)(?![a-z])"),
    ("work", r"\b(work with|work together|hire you|collab\w*|your services|contact|dm|available|need a (logo|brand|website|designer)|پڕۆژە|پەیوەندی|خزمەتگوزاری|مشروع|تعاون|تواصل|خدمات)(?![a-z])"),
    ("thanks", r"\b(thank\w*|love|great|beautiful|amazing|nice|brilliant|well said|so true|facts|سوپاس|جوان|دەستخۆش|دەست خۆش|بژی|شكرا|شكراً|جميل|رائع|مبدع|حلو)(?![a-z])"),
]

# Doubt or criticism: never answer these with a cheerful thank-you (keywords can't read tone).
DOUBT = r"\b(but|not|meh|bad|ugly|worst|hate|boring|overrated|copy|copied|stolen|بەڵام|خراپ|ناشیرین|لكن|سيء|سيئ|مسروق)(?![a-z])"

# Several wordings per answer, picked per comment, so the profile doesn't fill with copies.
REPLIES = {
    "job": {
        "en": ["We're always happy to see good work. Send your portfolio to hello@33studio.org"],
        "ku": ["هەمیشە خۆشحاڵ دەبین کاری باش ببینین. پۆرتفۆلیۆکەت بنێرە بۆ hello@33studio.org"],
        "ar": ["يسعدنا دائمًا رؤية الأعمال الجيدة. أرسل ملف أعمالك إلى hello@33studio.org"],
    },
    "price": {
        "en": ["Every project is priced to its scope. Tell us what you need at hello@33studio.org and we'll send a clear number.",
               "It depends on what you need. Send us a few lines at hello@33studio.org and you'll get a clear price before anything starts."],
        "ku": ["نرخی هەر پڕۆژەیەک بەپێی قەبارەکەیەتی. پێمان بڵێ چیت پێویستە لە hello@33studio.org و نرخێکی ڕوونت بۆ دەنێرین."],
        "ar": ["سعر كل مشروع حسب حجمه. أخبرنا بما تحتاجه على hello@33studio.org وسنرسل لك سعرًا واضحًا."],
    },
    "where": {
        "en": ["Salim Street, Sulaymaniyah. Say hello first so we can put the tea on: hello@33studio.org"],
        "ku": ["شەقامی سالم، سلێمانی. پێشتر سڵاومان لێ بکە: hello@33studio.org"],
        "ar": ["شارع سالم، السليمانية. راسلنا أولًا: hello@33studio.org"],
    },
    "work": {
        "en": ["We'd love to hear about it. Tell us what you're building at 33studio.org",
               "Good things start with a conversation. Start ours at 33studio.org"],
        "ku": ["خۆشحاڵ دەبین. باسی پڕۆژەکەت بکە لە 33studio.org"],
        "ar": ["يسعدنا ذلك. حدّثنا عن مشروعك على 33studio.org"],
    },
    "thanks": {
        "en": ["Thank you. That means a lot to the studio.", "Appreciated. Glad it landed.", "Thank you for reading. More soon."],
        "ku": ["زۆر سوپاس، ئەمە زۆر بۆ ستۆدیۆکە بەنرخە."],
        "ar": ["شكرًا جزيلًا، هذا يعني لنا الكثير."],
    },
}


def language(text):
    if any("\u0600" <= ch <= "\u06ff" for ch in text):
        return "ku" if KURDISH & set(text) else "ar"
    return "en"


def answer(text, comment_id=""):
    """The reply for a comment, or None when it matches no topic."""
    low = text.lower()
    for topic, pattern in TOPICS:
        if topic == "thanks" and re.search(DOUBT, low):
            return None
        if re.search(pattern, low):
            options = REPLIES[topic][language(text)]
            return options[zlib.crc32(comment_id.encode()) % len(options)]
    return None


def main():
    token = os.environ.get("THREADS_TOKEN") or sys.exit("THREADS_TOKEN is not set.")
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
            reply = answer(c["text"], c["id"])
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
