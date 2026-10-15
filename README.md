# 33Studio Threads Engine

Posts to the 33Studio Threads account 3 times a day (09:00, 13:00, 19:00 Sulaymaniyah time, triggered by cron-job.org)
from `queue.json`, using the official Threads API and free GitHub Actions. Every 30 minutes it
also answers new comments in the 33 Studio voice, using a free Hugging Face AI model.

Each post is one of:
- **Text:** a single post.
- **Thread:** several connected posts (each one replies to the one before).
- **Image or carousel:** text plus branded 33 Studio cards (1 card = image, 2 to 20 = carousel).

Cards use the 33 brand fonts (mandatory): Barlow Condensed Black for headlines, Barlow
Condensed Bold for paragraphs and labels. Two looks:
- **Hand-drawn** (default): friendly studio style. A big hand-drawn gesture from `assets/marks/`
  on every card, sticker-style labels, round step numbers.
- **Classic** (`"style": "classic"`): the editorial layout from the Instagram engine.

## Writing posts
```json
[
  { "mood": "roast", "text": "One post, max 500 characters." },

  { "mood": "guide", "text": ["Thread opener.", "Part two.", "Part three, ending with 33studio.org"] },

  { "mood": "friendly", "kicker": "Made by hand", "color": "teal",
    "slides": [ { "title": "Big headline.", "body": "Optional smaller line." } ],
    "text": "The caption that sits above the image." }
]
```
- `mood`: `friendly`, `roast` or `guide`. Only a label, so you can keep the mix balanced.
- `color` (image posts): `cream`, `ink` or `teal` (also `paper`, made for the classic look).
- `mark` (optional, 1 to 20): which hand-drawn gesture to use. Set it per post, or per card
  inside `slides`. Left out, one is picked automatically. Good matches: 3 high-five,
  13 cheering, 18 holding something big, 20 idea/lightbulb, 14 scribble/drawing, 15 motion,
  12 tangled, 4 hug, 10 wave.
- `kicker`: the small label at the top of the card.
- Run `python3 post.py preview` to check lengths and see every card in `preview/`.

## Voice
Read `VOICE.md` before writing a batch. It's the 33 Studio tone of voice: principles, the three
moods, how to ask for work, banned words, and a checklist.

## Setup, step by step (about an hour)

### Step 1. Create a separate Meta app for 33Studio
33Studio gets its own app, under the 33 Studio business, fully separate from your personal one.
1. Go to developers.facebook.com > My Apps > **Create App**.
2. App name: `33Studio Threads`. Contact email: hello@33studio.org.
3. Use case: **Access the Threads API**. Next.
4. Business: pick the **33 Studio** business portfolio (the one that owns the 33Studio page).
   If Meta asks to verify it, you can skip; posting to your own account works without it.
5. Create the app.
6. Use cases > Access the Threads API > **Customize** > Permissions: add all four:
   `threads_basic`, `threads_content_publish`, `threads_read_replies`, `threads_manage_replies`.
7. Same screen > **Settings**: put `https://33studio.org/` in all three boxes
   (Redirect Callback URLs, Uninstall Callback URL, Delete Callback URL). Save.
   Copy the **Threads App ID** and **Threads App Secret** shown there.
8. App roles > Roles > Add people > **Threads Tester** > type the 33Studio Threads username.
9. On your phone, open Threads **logged in as 33Studio**: Settings > Account >
   Website permissions > Invites > **Accept**.

The app can stay in development mode: it only posts and replies on the 33Studio account.

### Step 2. Get the 33Studio token
1. In your browser, log out of Threads and log in **as 33Studio** at threads.net.
2. On your Mac, in this folder: `python3 get_token.py`
3. Paste the **33Studio Threads** App ID and App Secret, and `https://33studio.org/` as the redirect URI, open the link it prints, approve, then paste
   the URL you land on. Copy the long token it prints. That's `THREADS_TOKEN`.

### Step 3. Get a free Hugging Face token (for comment replies)
1. Sign up at huggingface.co (free).
2. Profile picture > Settings > **Access Tokens** > Create new token > **Fine-grained**.
3. Name it `33studio-threads`, tick **Make calls to Inference Providers**, create, and copy it.
   That's `HF_TOKEN`.
4. Free accounts get a small amount of monthly credit. Short replies cost a tiny fraction of a
   cent each, so normal comment volume fits. If you outgrow it, HF PRO is $9/month.

### Step 4. Create the GitHub repo
1. github.com > New repository > name `33studio-threads` > **Public** > Create.
   (Public so Threads can download the card images. Tokens stay hidden in Secrets.)
2. Add file > Upload files > drag in everything in this folder **except** `.github` and
   `preview`. Commit.
3. The `.github` folder won't drag in. For each of the three workflow files, use
   Add file > Create new file, type the path, paste the content, commit:
   - `.github/workflows/post.yml`
   - `.github/workflows/replies.yml`
   - `.github/workflows/refresh-token.yml`

### Step 5. Add the secrets
Repo > Settings > Secrets and variables > Actions > **Secrets** tab > New repository secret:
- `THREADS_TOKEN`: from step 2
- `HF_TOKEN`: from step 3
- `GH_PAT`: github.com > Settings > Developer settings > Fine-grained tokens > Generate.
  Repository access: only `33studio-threads`. Permissions: **Secrets: Read and write**.
  This lets the refresh workflow renew the Threads token every two weeks.

### Step 6. Test posting
Actions > **Post to Threads (33Studio)** > Run workflow. In about a minute the first post is live
on Threads, and `queue.json` has one post fewer.

### Step 7. Test replies safely first
1. Settings > Secrets and variables > Actions > **Variables** tab > New variable:
   `DRY_RUN` = `1`
2. Leave a test comment on the new post from your personal account.
3. Actions > **Reply to comments (33Studio)** > Run workflow > open the run > "Answer new
   comments". It prints each comment and the reply it **would** send. Nothing is posted.
4. Happy with the tone? Delete the `DRY_RUN` variable. From then on it answers for real,
   every 30 minutes.

### Step 8. Done
- 3 posts a day, comments answered every 30 minutes, token renewed automatically.
- GitHub emails you if anything fails, including when the queue runs empty.

## How the reply bot behaves
- Checks the latest 20 posts for comments it hasn't seen, and answers in the commenter's
  language (Kurdish, Arabic or English), in 1 to 3 sentences, no emoji.
- Price, timeline or availability questions: never gives numbers, points to
  hello@33studio.org or 33studio.org.
- Spam, abuse, politics, religion, or emoji-only comments: no reply.
- Never names clients, never invents facts, never argues.
- At most 10 replies per run. Each comment is answered once (tracked in `replied.json`).
- Change the AI model with a repository **variable** `HF_MODEL` (default
  `meta-llama/Llama-3.1-8B-Instruct`; `Qwen/Qwen2.5-7B-Instruct` is a good alternative).
- The bot's personality lives in `PROMPT` at the top of `replies.py`.

## Notes
- When the queue runs empty, the run fails on purpose and GitHub emails you. Add a new batch.
- If a thread breaks halfway, the opener stays live and is removed from the queue, so a rerun
  never double posts. The failed run tells you which part stopped.
- Post times are set in the cron-job.org job (`0 9,13,19 * * *`, timezone Asia/Baghdad). It calls GitHub with a token that has Actions: Read and write on this repo only.
- Hand-drawn marks: "20 Hand Drawn Marks / Hand Gestures" pack. Check its licence allows
  them in a public repo.
- Fonts: Barlow Condensed (SIL Open Font License, free to keep in a public repo).
