# 33Studio Threads Engine

Posts text to the 33Studio Threads account daily from `queue.json` (times set in cron-job.org), and
image posts 3 times a week from `photos-queue.json` (Sun, Tue, Thu at 17:00 Sulaymaniyah time),
to Threads and to the 33Studio Instagram, with the same images and caption
from `queue.json`, using the official Threads API and free GitHub Actions. Every 30 minutes it
also answers new comments that ask about price, working together, location or jobs, or that
say thanks, in Kurdish, Arabic or English. No AI and no extra accounts.

Each post is one of:
- **Text:** a single post.
- **Thread:** several connected posts (each one replies to the one before).
- **Image or carousel:** text plus branded 33 Studio cards (1 card = image, 2 to 20 = carousel).
- **Photo:** text plus real photos. Put the photos in `photos/` and list them in the post:
  `{ "mood": "city", "photos": ["photos/sign-01.jpg"], "text": "..." }`. JPG or PNG,
  any size. They're straightened, resized and stripped of location data before posting.

Cards use the 33 brand fonts (mandatory): Barlow Condensed Black for headlines, Barlow
Condensed Bold for paragraphs and labels. Two looks:
- **Hand-drawn** (default): friendly studio style. A big hand-drawn gesture from `assets/marks/`
  on every card, sticker-style labels, big step numbers in the accent colour.
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
- `mood`: the culture territory (`city`, `script`, `craft`, `scene`, `take`) or, for the
  20% commerce share, `friendly` / `roast` / `guide`. Only a label, to keep the mix balanced.
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

### Step 3. Create the GitHub repo
1. github.com > New repository > name `33studio-threads` > **Public** > Create.
   (Public so Threads can download the card images. Tokens stay hidden in Secrets.)
2. Add file > Upload files > drag in everything in this folder **except** `.github` and
   `preview`. Commit.
3. The `.github` folder won't drag in. For each of the three workflow files, use
   Add file > Create new file, type the path, paste the content, commit:
   - `.github/workflows/post.yml`
   - `.github/workflows/replies.yml`
   - `.github/workflows/refresh-token.yml`

### Step 4. Add the secrets
Repo > Settings > Secrets and variables > Actions > **Secrets** tab > New repository secret:
- `THREADS_TOKEN`: from step 2
- `GH_PAT`: github.com > Settings > Developer settings > Fine-grained tokens > Generate.
  Repository access: only `33studio-threads`. Permissions: **Secrets: Read and write**.
  This lets the refresh workflow renew the Threads token every two weeks.

### Step 5. Test posting
Actions > **Post to Threads (33Studio)** > Run workflow. In about a minute the first post is live
on Threads, and `queue.json` has one post fewer.

### Step 6. Test replies safely first
1. Settings > Secrets and variables > Actions > **Variables** tab > New variable:
   `DRY_RUN` = `1`
2. Leave a test comment on the new post from your personal account.
3. Actions > **Reply to comments (33Studio)** > Run workflow > open the run > "Answer new
   comments". It prints each comment and the reply it **would** send. Nothing is posted.
4. Happy with the tone? Delete the `DRY_RUN` variable. From then on it answers for real,
   every 30 minutes.

### Step 7. Done
- 2 posts a day, comments answered every 30 minutes, token renewed automatically.
- GitHub emails you if anything fails, including when the queue runs empty.

## Instagram (image posts only)
Each image post goes to Instagram first, then Threads, in the same run. Until `IG_TOKEN` is set,
the Instagram step skips and only Threads posts. Uses the **33Studio Threads** Meta app, not a
personal one.

1. **Make the 33Studio Instagram a professional account** (Instagram > Settings > Account type and
   tools > Switch to professional account > Business). Skip if it already is.
2. **Add Instagram to the 33Studio Threads Meta app.** developers.facebook.com > the app >
   Use cases > **Add use cases** > *Manage messaging & content on Instagram*.
3. In that use case, open **API setup with Instagram login**. Under Permissions, make sure
   `instagram_business_basic` and `instagram_business_content_publish` are added.
4. If Meta asks for a tester: App roles > Roles > Add people > **Instagram Tester** > the 33Studio
   Instagram username. Accept on Instagram, logged in as 33Studio: Settings > Website permissions >
   Apps and websites > **Tester invites** > Accept.
5. Back in **API setup with Instagram login** > **Generate access tokens** > Add account > log in
   as **33Studio** (not your personal Instagram) > approve > copy the token.
6. GitHub repo > Settings > Secrets and variables > Actions > New repository secret:
   `IG_TOKEN` = the token. It's renewed automatically with the Threads token, twice a month.

Test: Actions > **Post photos to Instagram + Threads** > Run workflow. Note this posts the next
image post on both platforms for real.

## How the reply bot behaves
- Every 30 minutes it checks the latest 20 posts for comments it hasn't seen.
- It replies only when a comment matches a topic, in the commenter's language:
  - **Price** ("how much", "نرخ", "سعر"): no numbers, points to hello@33studio.org.
  - **Working together** ("work with", "پڕۆژە", "مشروع"): points to 33studio.org.
  - **Location** ("where", "کوێ", "أين"): Salim Street, Sulaymaniyah.
  - **Jobs** ("hiring", "کارمەند", "وظيفة"): asks for a portfolio by email.
  - **Thanks** ("love", "جوان", "شكرا"): a short thank-you, but never when the comment also
    sounds doubtful or critical ("but", "meh", "بەڵام", "لكن").
- Anything else (opinions, tags, emoji, questions it can't answer) gets **no reply**. Answer those
  yourself; they're the conversations that build culture.
- At most 10 replies per run. Each comment is answered once (tracked in `replied.json`).
- Keywords and reply wording live at the top of `replies.py`. After changing them, run
  `python3 test_replies.py` to check nothing broke.

## Notes
- When the queue runs empty, the run fails on purpose and GitHub emails you. Add a new batch.
- If a thread breaks halfway, the opener stays live and is removed from the queue, so a rerun
  never double posts. The failed run tells you which part stopped.
- Post times are set in the cron-job.org job (`0 9,20 * * *`, timezone Asia/Baghdad). It calls GitHub with a token that has Actions: Read and write on this repo only.
- Hand-drawn marks: "20 Hand Drawn Marks / Hand Gestures" pack. Check its licence allows
  them in a public repo.
- Fonts: Barlow Condensed (SIL Open Font License, free to keep in a public repo).
