#!/usr/bin/env python3
"""
Render and check posts.

  python3 render.py check          validate all captions, write contact sheets to out/
  python3 render.py one 012        render one post to out/012.png
"""
import csv
import os
import sys

from PIL import Image

from engine import BG, HERE, post_svg, save_png
from scenes import render_scene

CAPTIONS = os.path.join(HERE, "captions.csv")
OUT = os.path.join(HERE, "out")


def load_rows(path=CAPTIONS):
    with open(path, newline="", encoding="utf-8") as f:
        return [{k: (v or "").strip() for k, v in r.items()} for r in csv.DictReader(f)]


def row_svg(row):
    art = render_scene(row["scene"], row["mood"], row["arms"], row["trend"], row["label"])
    return post_svg(row["header"], row["caption"], art)


def cmd_check():
    rows = load_rows()
    problems, ids = [], set()
    for r in rows:
        if r["id"] in ids:
            problems.append(f"{r['id']}: duplicate id")
        ids.add(r["id"])
        try:
            row_svg(r)
        except Exception as e:  # noqa: BLE001
            problems.append(f"{r['id']}: {e}")
    ready = sum(1 for r in rows if r["status"].lower() == "ready")
    print(f"{len(rows)} rows, {ready} ready, {len(rows) - ready} on hold")
    if problems:
        print("PROBLEMS:")
        for p in problems:
            print("  -", p)
        sys.exit(1)
    os.makedirs(os.path.join(OUT, "tmp"), exist_ok=True)
    cell, cols, per = 360, 5, 20
    for s in range(0, len(rows), per):
        chunk = rows[s:s + per]
        sheet = Image.new("RGB", (cell * cols, cell * ((len(chunk) + cols - 1) // cols)), BG)
        for i, r in enumerate(chunk):
            p = os.path.join(OUT, "tmp", r["id"] + ".png")
            save_png(row_svg(r), p)
            im = Image.open(p).convert("RGB").resize((cell, cell), Image.LANCZOS)
            sheet.paste(im, ((i % cols) * cell, (i // cols) * cell))
        sheet.save(os.path.join(OUT, f"sheet-{s // per + 1}.png"))
    print(f"all rows render; contact sheets in {OUT}")


def cmd_one(pid):
    for r in load_rows():
        if r["id"] == pid:
            p = os.path.join(OUT, pid + ".png")
            save_png(row_svg(r), p)
            print("wrote", p)
            return
    sys.exit(f"no row with id {pid}")


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["check"]:
        cmd_check()
    elif a[:1] == ["one"] and len(a) == 2:
        cmd_one(a[1])
    else:
        print(__doc__)
