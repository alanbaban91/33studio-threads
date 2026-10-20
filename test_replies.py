"""Run: python3 test_replies.py  (checks the reply bot's keyword rules)"""
from replies import answer, language, REPLIES

CASES = [  # comment, expected topic (None = no reply), expected language
    ("How much for a logo?", "price", "en"), ("How much does it cost to work with you?", "price", "en"),
    ("Are you hiring interns?", "job", "en"), ("Where are you located?", "where", "en"),
    ("I'd love to work with you on our cafe", "work", "en"), ("Love this, so true", "thanks", "en"),
    ("نرخی لۆگۆیەک چەندە؟", "price", "ku"), ("ئێوە لە کوێن؟", "where", "ku"), ("دەستخۆش زۆر جوانە", "thanks", "ku"),
    ("کم سعر تصميم الشعار؟", "price", "ar"), ("أين مكتبكم؟", "where", "ar"), ("شكرا عمل رائع", "thanks", "ar"),
    ("هل لديكم وظيفة؟", "job", "ar"), ("كم السعر؟", "price", "ar"),
    ("كما قلت تماما", None, None), ("@friend look at this", None, None), ("🔥🔥", None, None),
    ("I prefer the second one", None, None), ("nice vibes but meh", None, None), ("جوانە بەڵام", None, None),
    ("great post but how much is a logo?", "price", "en"), ("artwork is pretty", None, None), ("this is overrated", None, None),
]

for text, topic, lang in CASES:
    r = answer(text, "id")
    got = next((t for t, langs in REPLIES.items() for opts in langs.values() if r in opts), None) if r else None
    assert got == topic, f"{text!r}: expected {topic}, got {got}"
    assert r is None or language(text) == lang, f"{text!r}: wrong language"
print(f"all {len(CASES)} cases pass")
