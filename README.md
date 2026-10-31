# pink.quocca autopilot

Draws one post a day and publishes it to Instagram by itself, for $0. No Anthropic API, no paid tools, and it runs on GitHub's servers, so your computer can be off.

**What happens every day**

1. GitHub wakes up at 12:30 Singapore time.
2. It picks the next unposted row in `captions.csv` and draws the image (`engine.py`, `scenes.py`).
3. It saves the image as a JPEG in this repo, which gives Instagram a public link to fetch.
4. It publishes through Instagram's official API (`post.py`) with the caption, a fixed call-to-action line, "Not financial advice." and hashtags.
5. It records the post in `state.json` so nothing is ever posted twice.
6. Twice a month it renews your Instagram token (they expire after 60 days).
7. When fewer than 7 captions are left, the run fails on purpose so GitHub emails you.

You start with 89 ready captions: about three months of daily posts.

## One-time setup (about 30 to 40 minutes)

### 1. Put the project on GitHub
1. Create a free GitHub account, then a **public** repository named `pink-quocca`. It has to be public so Instagram can download the images, and the images are public posts anyway. Your tokens stay private, because they live in GitHub Secrets.
2. Upload everything in this folder, including the hidden `.github` folder. Easiest: install GitHub Desktop, or run `git init`, `git add .`, `git commit`, then push.

### 2. Make Instagram ready
Your @pink.quocca account must be a **Professional** account (Settings, then Account type and tools, then switch to Creator). No Facebook Page is needed for the route used here.

### 3. Create the Meta app and get two values
You need `IG_USER_ID` (a number) and `IG_ACCESS_TOKEN` (a long string).
1. Go to developers.facebook.com, log in, and create an app (type: Business, or the closest option).
2. Add the **Instagram** product and open **API setup with Instagram login**.
3. Add your @pink.quocca account to the app and accept the invite if asked (Instagram: Settings, then Apps and websites, then Tester invites).
4. Use **Generate token** next to your account. Copy the token and the Instagram account ID shown beside it. Allow the permissions `instagram_business_basic` and `instagram_business_content_publish`.
5. Meta's docs say a long-lived token (60 days) is created on a server by exchanging the short one:
   `https://graph.instagram.com/access_token?grant_type=ig_exchange_token&client_secret=<APP_SECRET>&access_token=<SHORT_TOKEN>`
   If the dashboard already gives you a 60-day token, skip this.

Menu names change often, so follow the labels you see. If you get stuck, send me a screenshot.

### 4. Add three secrets in GitHub
Repository, then Settings, then Secrets and variables, then Actions, then New repository secret:

| Name | Value |
| --- | --- |
| `IG_USER_ID` | the Instagram account ID from step 3 |
| `IG_ACCESS_TOKEN` | the long-lived token from step 3 |
| `GH_PAT` | a GitHub personal access token (Settings, Developer settings, Fine-grained tokens) limited to this repository with **Secrets: Read and write**. Only the token-refresh job uses it. |

Also check Settings, then Actions, then General, then Workflow permissions is set to **Read and write**.

### 5. Test once
Actions tab, then **Daily post**, then **Run workflow**, with count `1`. In about two minutes a post should appear on the account. If it fails, open the run: the error message from Instagram is printed there (see Troubleshooting).

### 6. Launch week
Run **Daily post** by hand with count `3` on days 1, 2 and 3. Together with the scheduled run, that puts about nine posts on the grid in three days. After that, do nothing: the schedule posts one a day.

## Everyday use

- **Nothing**, mostly. Glance at the Actions tab once a week to see green ticks.
- **Add captions:** open `captions.csv` (Google Sheets or Excel is fine) and add rows. Nothing else needs to change. Run `python render.py check` on your computer, or just let the daily run check it.
- **Hold a post:** change its `status` from `ready` to `hold`. Post 010 is already on hold (see below).
- **Change the time:** edit the `cron` line in `.github/workflows/daily-post.yml` (it is in UTC; Singapore is UTC+8).

### The caption sheet

| Column | What it does |
| --- | --- |
| `id` | Order of posting. Keep unique. |
| `status` | `ready` posts; anything else is skipped. |
| `header` | Small red text above the caption. |
| `caption` | The joke. Max about 70 characters. A `\|` forces a line break. |
| `scene` | `desk`, `desk2` (two screens), `plant`, `piggy`, `beach`, `coins`, `calendar`, `bills` |
| `mood` | `deadpan`, `smile`, `smug`, `worried`, `panic`, `shades` |
| `arms` | `desk` scenes only: `rest`, `mug`, `up`, `shrug` |
| `trend` | `desk` scenes only: `down` (red), `up` (green), `flat` (grey) |
| `label` | Small text on the prop (plant tag, calendar header, receipt title, screen caption). |

Leave a cell blank to use that scene's default.

## What is deliberately not automated

Commenting, following, liking and messaging. Bots that do this break Meta's rules and are the fastest way to lose an account. Instagram's ranking rewards replies and saves, so spend ten minutes a day by hand on replies and a few real comments. Everything else here runs without you.

## Things to check

- **Index-funds post (010) is on hold.** It is the one caption that states a view on a product type. Under Singapore's rules, opinions on investment products can count as advice in some situations, so I held it back. Switch it to `ready` if you are comfortable.
- **AI label.** The art is drawn by code, not by an AI image tool. If you ever use AI-made art, set a repository variable `IG_AI_GENERATED` to `true` (Settings, Secrets and variables, Actions, Variables) and posts will carry Instagram's disclosure flag.
- **Not verified by me.** I tested the full posting flow against a simulated Instagram server, and the call sequence matches Meta's docs, but I could not test against the real Instagram. Two things I could not confirm from Meta's docs: whether your app can publish to your own account while it is in development mode without Meta's app review (it normally works for accounts you added to the app), and whether GitHub pauses scheduled runs after a long quiet spell (daily commits should keep the repo active; if you see a paused banner on the Actions tab, click enable).
- **API version.** `config.json` sets `v23.0`. If Instagram retires it, change it to the current version.

## Troubleshooting

| What you see | Likely cause |
| --- | --- |
| `Invalid OAuth access token` or code 190 | Token expired or wrong. Generate a new one and update `IG_ACCESS_TOKEN`. |
| `image not reachable` | Repo is private, or GitHub was slow. Make it public and re-run. |
| `Media upload has failed` or similar | Rare image fetch problem. Re-run the workflow; nothing is posted twice. |
| Permission or `(#10)` errors | Token lacks `instagram_business_content_publish`, or the account was not added to the app. |
| `Only N posts left` failure | Add more rows to `captions.csv`. The post itself already went out. |
| Token refresh fails | `GH_PAT` missing or lacks Secrets access. Fix it, then run **Refresh Instagram token** by hand. |

## Files

- `captions.csv` your content
- `engine.py`, `scenes.py` drawing code
- `render.py` checks and previews (`python render.py check` writes contact sheets to `out/`)
- `post.py` publishing, token refresh, queue alert
- `state.json` what has been posted
- `config.json` hashtags, call-to-action lines, API version
- `.github/workflows/` the two schedules
- `fonts/` Patrick Hand (SIL Open Font Licence)
