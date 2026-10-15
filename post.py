#!/usr/bin/env python3
"""33Studio Threads engine: publishes the next post in queue.json to Threads.

A post is plain text, a thread (several connected posts), or text with branded
image cards (1 card = image post, 2+ cards = carousel). The card look is the
33 Studio theme from the Instagram engine.

  python3 post.py render    # render next post's cards into media/ (if it has any)
  python3 post.py publish   # publish it (needs THREADS_TOKEN), then dequeue
  python3 post.py preview   # check every queued post; render all cards into preview/
"""
import json, os, sys, time, datetime, urllib.request, urllib.parse, urllib.error
from PIL import Image, ImageDraw, ImageFont

SITE = "33studio.org"
API = "https://graph.threads.net/v1.0"
MAX_LEN = 500                     # Threads text limit per post
W, H, M = 1080, 1350, 96          # 4:5 portrait, outer margin
HERE = os.path.dirname(os.path.abspath(__file__))
FONTS, ASSETS = os.path.join(HERE, "fonts"), os.path.join(HERE, "assets")

# 33 Studio looks. "paper" is the Instagram engine's studio theme; the others use the 33 palette.
COLORS = {
    "paper": dict(bg="#F1ECE3", ink="#141414", soft="#3D3A35", muted="#8A8378", accent="#B5452B", logo="33logo.png", dot="#53E6D4"),
    "cream": dict(bg="#F5F5DD", ink="#101616", soft="#033335", muted="#9DA89A", accent="#018081", logo="33logo.png", dot="#53E6D4"),
    "ink":   dict(bg="#101616", ink="#F5F5DD", soft="#CFCFBA", muted="#4E5A58", accent="#53E6D4", logo="33logoCream.png", dot="#53E6D4"),
    "teal":  dict(bg="#53E6D4", ink="#101616", soft="#033335", muted="#2E8F86", accent="#033335", logo="33logo.png", dot="#F5F5DD"),
}
# 33 Studio brand fonts: Barlow Condensed Black for headlines, Bold for paragraphs and labels
DISPLAY, BODY = "BarlowCondensed-Black.ttf", "BarlowCondensed-Bold.ttf"
SIZES, LH = (190, 128, 84), 0.94


def font(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name), size)


def clean(text):
    # drop emoji / symbols the fonts can't draw; curly apostrophes read less "default"
    return "".join(ch for ch in text if ord(ch) < 0x2190).replace("→", "").replace("'", "’")


def wrap(draw, text, fnt, width):
    lines = []
    for para in text.split("\n"):
        words, line = para.split(), ""
        for w in words:
            test = (line + " " + w).strip()
            if draw.textlength(test, font=fnt) <= width:
                line = test
            else:
                if line:
                    lines.append(line)
                line = w
        lines.append(line)
    return lines


def block_height(fnt, lines, lh):
    return int(fnt.size * lh * len(lines))


def fit(draw, text, fontname, max_size, min_size, width, max_h, lh):
    size = max_size
    while size > min_size:
        f = font(fontname, size)
        lines = wrap(draw, text, f, width)
        if block_height(f, lines, lh) <= max_h:
            return f, lines
        size -= 4
    f = font(fontname, min_size)
    return f, wrap(draw, text, f, width)


def draw_lines(draw, x, y, lines, fnt, lh, fill):
    for ln in lines:
        draw.text((x, y), ln, font=fnt, fill=fill)
        y += int(fnt.size * lh)
    return y


def render_slide(post, idx):
    t = COLORS.get(post.get("color", "paper"), COLORS["paper"])
    slides = post["slides"]
    total, slide = len(slides), slides[idx]
    hero = idx == 0                        # cover or single card
    last = idx == total - 1 and total > 1
    hero_max, inner_max, min_size = SIZES

    img = Image.new("RGB", (W, H), t["bg"])
    d = ImageDraw.Draw(img)
    mono = font(BODY, 30)
    inner = W - 2 * M
    title, body = clean(slide["title"]), clean(slide.get("body", ""))

    # --- top bar: accent square + kicker, counter on the right
    top = M
    kb = d.textbbox((0, 0), "KICKER", font=mono)
    cy = top + (kb[1] + kb[3]) // 2
    d.rectangle([M, cy - 7, M + 14, cy + 7], fill=t["accent"])
    d.text((M + 30, top), clean(post.get("kicker", "33 Studio")).upper(), font=mono, fill=t["accent"])
    if total > 1:
        counter = f"{idx + 1:02d} / {total:02d}"
        d.text((W - M - d.textlength(counter, font=mono), top), counter, font=mono, fill=t["muted"])
    d.line([M, top + 58, W - M, top + 58], fill=t["muted"], width=1)

    # --- footer: 33 logo + site
    fy = H - M - 24
    d.line([M, fy - 34, W - M, fy - 34], fill=t["muted"], width=1)
    mark = Image.open(os.path.join(ASSETS, t["logo"])).convert("RGBA")
    mh = 40
    mark = mark.resize((int(mark.width * mh / mark.height), mh), Image.LANCZOS)
    img.paste(mark, (M, fy - 9), mark)
    d.text((M + mark.width + 18, fy), SITE, font=mono, fill=t["ink"])
    tag = "SWIPE" if hero and total > 1 else "WORK WITH US" if last else ""
    if tag:
        # Barlow has no arrow glyph, so draw one
        arrow(d, W - M, fy + 18, t["accent"])
        d.text((W - M - 40 - d.textlength(tag, font=mono), fy), tag, font=mono, fill=t["accent"])

    area_top, area_bot = top + 120, fy - 90

    if hero or last:
        bf, blines = font(BODY, 40), []
        if body:
            bf, blines = fit(d, body, BODY, 50, 32, inner - 40, 360, 1.25)
        body_h = block_height(bf, blines, 1.25) + (96 if blines else 0)
        tf, tlines = fit(d, title, DISPLAY, hero_max, min_size, inner, area_bot - area_top - body_h, LH)
        y = area_bot - body_h - block_height(tf, tlines, LH)
        y = draw_lines(d, M, y, tlines, tf, LH, t["ink"])
        if blines:
            y += 96
            d.rectangle([M, y - 40, M + 60, y - 37], fill=t["accent"])
            draw_lines(d, M, y, blines, bf, 1.25, t["soft"])
    else:
        tf, tlines = fit(d, title, DISPLAY, inner_max, min_size, inner, 440, LH)
        y = draw_lines(d, M, area_top + 20, tlines, tf, LH, t["ink"])
        if body:
            y += 84
            d.rectangle([M, y - 38, M + 60, y - 35], fill=t["accent"])
            bf, blines = fit(d, body, BODY, 52, 32, inner - 60, area_bot - y - 40, 1.25)
            draw_lines(d, M, y, blines, bf, 1.25, t["soft"])
        num = f"{idx:02d}"
        nf = font(DISPLAY, 300)
        nb = d.textbbox((0, 0), num, font=nf)
        d.text((W - M - (nb[2] - nb[0]) - nb[0], area_bot - (nb[3] - nb[1]) - nb[1] + 10),
               num, font=nf, fill=t["muted"])
    return img


def mark(n, color, width, max_h, angle):
    """Hand-drawn gesture n (1-20), recoloured, scaled and slightly tilted."""
    m = Image.open(os.path.join(ASSETS, "marks", f"mark-{(n - 1) % 20 + 1:02d}.png")).getchannel("A")
    scale = min(width / m.width, max_h / m.height)
    m = m.resize((int(m.width * scale), int(m.height * scale)), Image.LANCZOS).rotate(angle, Image.BICUBIC, expand=True)
    art = Image.new("RGBA", m.size, color)
    art.putalpha(m)
    return art


def pill(d, x, y, text, fnt, fg, outline, right=False, fill=None):
    w, h = int(d.textlength(text, font=fnt)) + 48, 56
    x = x - w if right else x
    d.rounded_rectangle([x, y, x + w, y + h], radius=h // 2, outline=outline, width=3, fill=fill)
    d.text((x + 24, y + h // 2 + 1), text, font=fnt, fill=fg, anchor="lm")
    return w


def arrow(d, x, y, color):
    d.line([x - 26, y, x, y], fill=color, width=3)
    d.line([x - 10, y - 9, x, y, x - 10, y + 9], fill=color, width=3, joint="curve")


def render_hand(post, idx):
    """Friendly studio look: big hand-drawn gestures, sticker pills, round step dots."""
    t = COLORS.get(post.get("color", "cream"), COLORS["cream"])
    slides = post["slides"]
    total, slide = len(slides), slides[idx]
    hero, last = idx == 0, idx == total - 1 and total > 1
    seed = sum(map(ord, post["slides"][0]["title"]))
    n = slide.get("mark", post.get("mark", seed % 20 + 1) + idx * 7)
    flip = (seed + idx) % 2                      # alternate which edge the gesture comes from

    img = Image.new("RGB", (W, H), t["bg"])
    d = ImageDraw.Draw(img)
    small = font(BODY, 28)
    inner = W - 2 * M
    title, body = clean(slide["title"]), clean(slide.get("body", ""))

    # --- top: kicker sticker, counter sticker
    pill(d, M, M - 10, clean(post.get("kicker", "33 Studio")).upper(), small, t["ink"], t["ink"])
    if total > 1:
        pill(d, W - M, M - 10, f"{idx + 1} / {total}", small, t["ink"], t["ink"], right=True)

    # --- footer: 33 logo + site, swipe / work-with-us sticker
    fy = H - M - 20
    logo = Image.open(os.path.join(ASSETS, t["logo"])).convert("RGBA")
    logo = logo.resize((int(logo.width * 44 / logo.height), 44), Image.LANCZOS)
    img.paste(logo, (M, fy - 4), logo)
    d.text((M + logo.width + 18, fy + 18), SITE, font=small, fill=t["ink"], anchor="lm")
    tag = "SWIPE" if hero and total > 1 else "WORK WITH US" if last else ""
    if tag:
        w = pill(d, W - M, fy - 10, tag + "     ", small, t["bg"], t["ink"], right=True, fill=t["ink"])
        arrow(d, W - M - 22, fy + 18, t["bg"])

    if hero or last:
        art = mark(n, t["ink"], W * 0.85, 420, 4 if flip else -4)
        x = W - art.width + 70 if flip else -70
        img.paste(art, (x, M + 90), art)
        text_top = M + 90 + art.height + 40
        bf, blines = font(BODY, 44), []
        if body:
            bf, blines = fit(d, body, BODY, 46, 32, inner - 40, 300, 1.22)
        body_h = block_height(bf, blines, 1.22) + (40 if blines else 0)
        tf, tlines = fit(d, title, DISPLAY, 170, 72, inner, fy - 60 - text_top - body_h, LH)
        y = fy - 60 - body_h - block_height(tf, tlines, LH)
        y = draw_lines(d, M, y, tlines, tf, LH, t["ink"])
        if blines:
            draw_lines(d, M, y + 40, blines, bf, 1.22, t["soft"])
    else:
        # step dot
        r = 54
        d.ellipse([M, M + 110, M + 2 * r, M + 110 + 2 * r], fill=t["dot"], outline=t["ink"], width=3)
        d.text((M + r, M + 110 + r + 4), str(idx), font=font(DISPLAY, 64), fill=t["ink"], anchor="mm")
        art = mark(n, t["ink"], W * 0.7, 330, -6 if flip else 6)
        ay = fy - 50 - art.height
        img.paste(art, (W - art.width + 60 if flip else -60, ay), art)
        y0 = M + 110 + 2 * r + 50
        tf, tlines = fit(d, title, DISPLAY, 128, 72, inner, 400, LH)
        y = draw_lines(d, M, y0, tlines, tf, LH, t["ink"])
        if body:
            bf, blines = fit(d, body, BODY, 48, 32, inner - 60, ay - y - 70, 1.22)
            draw_lines(d, M, y + 36, blines, bf, 1.22, t["soft"])
    return img


def render_post(post, folder, prefix):
    os.makedirs(folder, exist_ok=True)
    names = []
    for i in range(len(post.get("slides", []))):
        name = f"{prefix}-{i + 1:02d}.jpg"
        (render_slide if post.get("style") == "classic" else render_hand)(post, i).save(os.path.join(folder, name), "JPEG", quality=92, optimize=True)
        names.append(name)
    return names


def parts(post):
    """The post's text as a list: [main post, reply 1, reply 2, ...]."""
    text = post["text"]
    return [text] if isinstance(text, str) else text


def check(post, n):
    for i, p in enumerate(parts(post)):
        if not p.strip():
            sys.exit(f"Post {n}, part {i + 1} is empty.")
        if len(p) > MAX_LEN:
            sys.exit(f"Post {n}, part {i + 1} is {len(p)} chars (max {MAX_LEN}). Shorten it:\n{p}")
    if not 0 <= len(post.get("slides", [])) <= 20:
        sys.exit(f"Post {n} has {len(post['slides'])} cards (max 20).")


def load(path, default):
    return json.load(open(path, encoding="utf-8")) if os.path.exists(path) else default


def save(path, data):
    json.dump(data, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


# ---------------- Threads API ----------------
def api(method, path, params):
    data = urllib.parse.urlencode(params).encode()
    url = f"{API}/{path}"
    if method == "GET":
        url, data = url + "?" + data.decode(), None
    req = urllib.request.Request(url, data=data, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f"Threads API error {e.code}: {e.read().decode()}")


def wait_public(url):
    for _ in range(40):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, method="HEAD"), timeout=20) as r:
                if r.status == 200:
                    return
        except Exception:
            pass
        time.sleep(5)
    sys.exit(f"Image never became public: {url}")


def wait_ready(cid, token):
    for _ in range(36):
        res = api("GET", cid, {"fields": "status,error_message", "access_token": token})
        if res.get("status") == "FINISHED":
            return
        if res.get("status") in ("ERROR", "EXPIRED"):
            sys.exit(f"Container {cid} failed: {res}")
        time.sleep(5)
    sys.exit(f"Container {cid} not ready in time")


def publish(params, token):
    cid = api("POST", "me/threads", {**params, "access_token": token})["id"]
    wait_ready(cid, token)
    return api("POST", "me/threads_publish", {"creation_id": cid, "access_token": token})["id"]


def cmd_render():
    queue = load("queue.json", [])
    if not queue:
        # Fails on purpose so GitHub emails you: time to add a new batch.
        sys.exit("Threads queue is empty. Add a new batch to queue.json.")
    check(queue[0], 1)
    for f in os.listdir("media"):
        if f.endswith(".jpg"):
            os.remove(os.path.join("media", f))
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d%H%M")
    names = render_post(queue[0], "media", f"post-{stamp}")
    save("media/next.json", names)
    print(f"Rendered {len(names)} card(s)." if names else "Text post, nothing to render.")


def cmd_publish():
    token = os.environ.get("THREADS_TOKEN") or sys.exit("THREADS_TOKEN is not set.")
    queue, names = load("queue.json", []), load("media/next.json", [])
    post, texts = queue[0], parts(queue[0])

    if not names:
        root = publish({"media_type": "TEXT", "text": texts[0]}, token)
    else:
        repo = os.environ.get("GITHUB_REPOSITORY") or sys.exit("GITHUB_REPOSITORY is not set.")
        branch = os.environ.get("GITHUB_REF_NAME", "main")
        urls = [f"https://raw.githubusercontent.com/{repo}/{branch}/media/{n}" for n in names]
        for u in urls:
            wait_public(u)
        if len(urls) == 1:
            root = publish({"media_type": "IMAGE", "image_url": urls[0], "text": texts[0]}, token)
        else:
            children = []
            for u in urls:
                child = api("POST", "me/threads", {"media_type": "IMAGE", "image_url": u,
                                                   "is_carousel_item": "true", "access_token": token})["id"]
                wait_ready(child, token)
                children.append(child)
            root = publish({"media_type": "CAROUSEL", "children": ",".join(children), "text": texts[0]}, token)

    # The main post is live now, so dequeue it even if a reply fails (no double posting on rerun).
    ids, error = [root], None
    try:
        for reply in texts[1:]:
            ids.append(publish({"media_type": "TEXT", "text": reply, "reply_to_id": ids[-1]}, token))
    except SystemExit as e:
        error = f"Main post is live but the thread stopped after {len(ids)} part(s): {e}"

    posted = load("posted.json", [])
    posted.append({"ids": ids, "posted_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), **post})
    save("posted.json", posted)
    save("queue.json", queue[1:])
    for n in names + ["next.json"]:
        p = os.path.join("media", n)
        if os.path.exists(p):
            os.remove(p)
    if error:
        sys.exit(error)
    print(f"Published {len(ids)} part(s) (id {root}). {len(queue) - 1} posts left in queue.")


def cmd_preview():
    queue = load("queue.json", [])
    for i, post in enumerate(queue, 1):
        check(post, i)
        render_post(post, "preview", f"{i:02d}-{post.get('mood', 'post')}")
    print(f"All {len(queue)} posts pass the length check. Cards written to preview/")


if __name__ == "__main__":
    {"render": cmd_render, "publish": cmd_publish, "preview": cmd_preview}.get(
        sys.argv[1] if len(sys.argv) > 1 else "", lambda: sys.exit(__doc__))()
