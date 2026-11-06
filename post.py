#!/usr/bin/env python3
"""
Daily poster for @pink.quocca. Uses only Instagram's official publishing API.

  python3 post.py prepare [--count N]   render the next N ready posts to posts/*.jpg
  python3 post.py publish [--dry-run]   publish what 'prepare' made
  python3 post.py queue                 how many ready posts are left (exit 1 if low)
  python3 post.py refresh               refresh the 60-day token; prints ONLY the new token

Environment:
  IG_USER_ID, IG_ACCESS_TOKEN   from your Meta app (stored as GitHub secrets)
  IG_API_VERSION                default from config.json
  IG_AI_GENERATED               "true" to send Instagram's AI-disclosure flag
  IG_GRAPH_BASE                 default https://graph.instagram.com (tests override it)
  IMAGE_BASE_URL                override where images are fetched from (tests)
  GITHUB_REPOSITORY             owner/repo, set automatically in GitHub Actions
"""
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(HERE, "state.json")
NEXT = os.path.join(HERE, ".next.json")
POSTS = os.path.join(HERE, "posts")
CONFIG = os.path.join(HERE, "config.json")


# ------------------------------------------------------------------- helpers
def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def cfg():
    return load_json(CONFIG, {})


def ready_rows():
    from render import load_rows  # lazy: needs cairosvg, not needed for 'refresh'
    posted = load_json(STATE, {"posted": {}})["posted"]
    return [r for r in load_rows()
            if r["status"].lower() == "ready" and r["id"] not in posted]


def build_text(row, c):
    ctas = c["ctas"]
    cta = ctas[int(row["id"]) % len(ctas)]
    caption = row["caption"].replace("|", " ")
    return f"{caption}\n\n{cta}\n\nNot financial advice.\n\n{' '.join(c['hashtags'])}"


def build_alt(row):
    return f"Cartoon pink quokka in a red tie. {row['caption'].replace('|', ' ')}"[:100]


def fail(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


# ----------------------------------------------------------------- graph api
def graph_base(versioned=True):
    root = (os.environ.get("IG_GRAPH_BASE") or cfg().get("graph_base") or "https://graph.instagram.com").rstrip("/")
    if not versioned:
        return root
    version = os.environ.get("IG_API_VERSION") or cfg().get("api_version", "v23.0")
    return f"{root}/{version}"


def call(method, path, params, versioned=True):
    url = f"{graph_base(versioned)}/{path.lstrip('/')}"
    data = None
    if method == "GET":
        url += "?" + urllib.parse.urlencode(params)
    else:
        data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(url, data=data, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        try:
            err = json.loads(body).get("error", {})
            body = f"{err.get('message', body)} (code {err.get('code')}, subcode {err.get('error_subcode')})"
        except Exception:  # noqa: BLE001
            pass
        raise RuntimeError(f"{method} {path} -> HTTP {e.code}: {body}") from None


def image_url(item, dry=False):
    base = os.environ.get("IMAGE_BASE_URL")
    if base:
        return f"{base.rstrip('/')}/{os.path.basename(item['jpg'])}"
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not repo:
        if dry:
            return f"https://raw.githubusercontent.com/<owner>/<repo>/<commit>/{item['jpg']}"
        fail("GITHUB_REPOSITORY not set (this runs inside GitHub Actions) and no IMAGE_BASE_URL given")
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=HERE, text=True).strip()
    return f"https://raw.githubusercontent.com/{repo}/{sha}/{item['jpg']}"


def wait_until_reachable(url, tries=18, pause=5):
    for _ in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, method="HEAD"), timeout=20) as r:
                if r.status == 200:
                    return
        except Exception:  # noqa: BLE001
            pass
        time.sleep(pause)
    fail(f"image not reachable yet: {url}")


# ------------------------------------------------------------------ commands
def cmd_prepare(count):
    from engine import png_to_jpeg, save_png
    from render import OUT, row_svg
    c = cfg()
    rows = ready_rows()[:count]
    if not rows:
        fail("no ready posts left in captions.csv - add more rows")
    os.makedirs(POSTS, exist_ok=True)
    items = []
    for r in rows:
        png = os.path.join(OUT, "tmp", r["id"] + ".png")
        jpg = os.path.join(POSTS, r["id"] + ".jpg")
        save_png(row_svg(r), png)
        png_to_jpeg(png, jpg)
        items.append({"id": r["id"], "jpg": f"posts/{r['id']}.jpg",
                      "text": build_text(r, c), "alt": build_alt(r)})
        print(f"prepared {r['id']}: {r['caption'].replace('|', ' ')}")
    save_json(NEXT, items)


def publish_one(item, dry):
    token = os.environ.get("IG_ACCESS_TOKEN", "")
    uid = os.environ.get("IG_USER_ID", "")
    url = image_url(item, dry)
    params = {"image_url": url, "caption": item["text"], "alt_text": item["alt"],
              "access_token": token}
    if os.environ.get("IG_AI_GENERATED", "").lower() == "true":
        params["is_ai_generated"] = "true"
    if dry:
        shown = {k: v for k, v in params.items() if k != "access_token"}
        print(f"[dry run] POST /{uid or '<IG_USER_ID>'}/media")
        print(json.dumps(shown, indent=2, ensure_ascii=False))
        return None
    if not token or not uid:
        fail("IG_USER_ID and IG_ACCESS_TOKEN must be set")
    wait_until_reachable(url)
    container = call("POST", f"{uid}/media", params)["id"]
    status = ""
    for _ in range(20):
        time.sleep(float(os.environ.get("IG_POLL_SECONDS", "6")))
        status = call("GET", container, {"fields": "status_code", "access_token": token}
                      ).get("status_code", "")
        if status == "FINISHED":
            break
        if status in ("ERROR", "EXPIRED"):
            fail(f"container {container} ended with status {status}")
    else:
        fail(f"container {container} not ready (last status {status!r})")
    media_id = call("POST", f"{uid}/media_publish",
                    {"creation_id": container, "access_token": token})["id"]
    link = ""
    try:
        link = call("GET", media_id, {"fields": "permalink", "access_token": token}).get("permalink", "")
    except RuntimeError:
        pass
    return {"media_id": media_id, "permalink": link,
            "at": datetime.now(timezone.utc).isoformat(timespec="seconds")}


def cmd_publish(dry):
    items = load_json(NEXT, [])
    if not items:
        fail("nothing prepared - run 'prepare' first")
    state = load_json(STATE, {"posted": {}})
    gap = float(os.environ.get("IG_GAP_SECONDS", cfg().get("min_gap_seconds", 60)))
    for n, item in enumerate(items):
        if item["id"] in state["posted"]:
            print(f"{item['id']} already posted, skipping")
            continue
        if n and not dry:
            time.sleep(gap)
        result = publish_one(item, dry)
        if result:
            state["posted"][item["id"]] = result
            save_json(STATE, state)  # saved straight away so a later failure cannot cause a repost
            print(f"published {item['id']} -> {result['permalink'] or result['media_id']}")


def cmd_queue():
    left = len(ready_rows())
    warn = int(cfg().get("low_queue_warning", 7))
    print(f"{left} ready posts left")
    if left < warn:
        print(f"::warning::Only {left} posts left in captions.csv. Add more rows soon.")
        sys.exit(1)


def cmd_refresh():
    token = os.environ.get("IG_ACCESS_TOKEN", "")
    if not token:
        fail("IG_ACCESS_TOKEN not set")
    try:
        r = call("GET", "refresh_access_token",
                 {"grant_type": "ig_refresh_token", "access_token": token}, versioned=False)
    except RuntimeError as e:
        fail(str(e))
    new = r.get("access_token")
    if not new:
        fail("refresh response had no access_token")
    print(f"token refreshed; valid for about {int(r.get('expires_in', 0)) // 86400} days",
          file=sys.stderr)
    print(new)


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["prepare"]:
        n = int(a[a.index("--count") + 1]) if "--count" in a else 1
        cmd_prepare(max(1, min(n, 10)))
    elif a[:1] == ["publish"]:
        cmd_publish("--dry-run" in a)
    elif a[:1] == ["queue"]:
        cmd_queue()
    elif a[:1] == ["refresh"]:
        cmd_refresh()
    else:
        print(__doc__)
