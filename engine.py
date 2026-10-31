#!/usr/bin/env python3
"""
Pink Quocca drawing engine.

Draws the quokka, props and text for one 1080 x 1080 post. Scenes (what the
quokka is doing) live in scenes.py; captions live in captions.csv.
Needs: pip install cairosvg pillow
"""
import os
import shutil
import subprocess
import cairosvg
from PIL import Image, ImageFont

W = H = 1080
BG = "#FAF6E8"
INK = "#1B1B1B"
PINK = "#F2B5B5"
PINK_DARK = "#E79C9C"
RED = "#D8363D"
HEAD_RED = "#B3202A"
GREEN = "#2A9D5A"
GOLD = "#FFD66B"
ORANGE = "#FFB347"
SW = 7  # standard stroke width

FONT = "Patrick Hand"
HERE = os.path.dirname(os.path.abspath(__file__))
FONT_FILE = os.path.join(HERE, "fonts", "PatrickHand.ttf")


def ensure_font():
    """Make the bundled font visible to the renderer (works on any Linux/macOS box)."""
    for d in (os.path.expanduser("~/.fonts"), os.path.expanduser("~/.local/share/fonts")):
        if os.path.exists(os.path.join(d, "PatrickHand.ttf")):
            return
    dest = os.path.expanduser("~/.fonts")
    os.makedirs(dest, exist_ok=True)
    shutil.copy(FONT_FILE, dest)
    if shutil.which("fc-cache"):
        subprocess.run(["fc-cache", "-f", dest], check=False,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


ensure_font()


# ---------------------------------------------------------------- text sizing
def text_width(s, size):
    return ImageFont.truetype(FONT_FILE, 200).getlength(s) * size / 200


# Calibrated so type matches the reference posts (caption line 1 = 806px wide,
# header = 354px wide, handle = 141px wide).
CAP_SIZE = 806 / text_width("Portfolio is down. I'm choosing to", 1)
_hdr = "NOT FINANCIAL ADVICE"
HEAD_SIZE = 354 / (text_width(_hdr, 1) + 0.15 * (len(_hdr) - 1))
HANDLE_SIZE = 141 / text_width("@pink.quocca", 1)


# ------------------------------------------------------------------ primitives
def line(x1, y1, x2, y2, w=SW, color=INK):
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" '
            f'stroke-width="{w}" stroke-linecap="round"/>')


def path(d, fill="none", w=SW, stroke=INK):
    return (f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{w}" '
            f'stroke-linecap="round" stroke-linejoin="round"/>')


def tube(d, w=24):
    """A pink limb with a black outline."""
    return (f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="{w + 2 * SW}" '
            f'stroke-linecap="round" stroke-linejoin="round"/>'
            f'<path d="{d}" fill="none" stroke="{PINK}" stroke-width="{w}" '
            f'stroke-linecap="round" stroke-linejoin="round"/>')


def text(x, y, s, size, fill=INK, anchor="middle", spacing=0, bold=0):
    s = s.replace("&", "&amp;")
    extra = (f' stroke="{fill}" stroke-width="{bold}" stroke-linejoin="round"'
             if bold else "")
    return (f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size:.2f}" '
            f'fill="{fill}" text-anchor="{anchor}" letter-spacing="{spacing:.2f}"{extra}>{s}</text>')


# ------------------------------------------------------------------- scenery
def screen(x, y, w, h, trend="down", label=None):
    s = (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="#fff" '
         f'stroke="{INK}" stroke-width="{SW}"/>')
    if trend == "down":
        fr, col = (0.25, 0.36, 0.48, 0.62), RED
    elif trend == "flat":
        fr, col = (0.42, 0.47, 0.40, 0.45), "#B9B39C"
    else:
        fr, col = ((0.55, 0.46, 0.35, 0.24) if label else (0.62, 0.52, 0.40, 0.28)), GREEN
    bw, bh = w * 0.085, h * 0.19
    for i, f in enumerate(fr):
        cx, cy = x + w * (0.2 + 0.2 * i), y + h * f
        s += line(cx, cy - bh * 0.85, cx, cy + bh * 0.85, 4.5)
        s += (f'<rect x="{cx - bw / 2:.1f}" y="{cy - bh / 2:.1f}" width="{bw:.1f}" height="{bh:.1f}" '
              f'rx="2" fill="{col}" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>')
    if label:
        s += text(x + w / 2, y + h - 16, label, 30)
    return s


def mug(x, y, w=68, h=76, fill=RED, steam=True):
    s = path(f"M {x + w - 2},{y + h * 0.24} C {x + w + 34},{y + h * 0.16} "
             f"{x + w + 34},{y + h * 0.76} {x + w - 2},{y + h * 0.70}")
    s += (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="9" fill="{fill}" '
          f'stroke="{INK}" stroke-width="{SW}" stroke-linejoin="round"/>')
    if steam:
        for fx in (0.33, 0.64):
            s += path(f"M {x + w * fx:.1f},{y - 14} q -9,-10 0,-20", w=5)
    return s


def desk():
    return line(220, 800, 880, 800, SW + 1) + line(262, 800, 262, 890) + line(838, 800, 838, 890)


def piggy():
    P = "#F7B3C2"
    s = ""
    for x in (570, 610, 664, 706):
        s += line(x, 800, x, 846)
    s += path("M 522,722 C 500,726 498,694 512,690")
    s += (f'<ellipse cx="637" cy="730" rx="118" ry="72" fill="{P}" stroke="{INK}" '
          f'stroke-width="{SW}"/>')
    s += path("M 582,664 L 590,634 L 612,654", fill=P)
    s += line(608, 659, 666, 659, 9)
    s += (f'<ellipse cx="737" cy="733" rx="27" ry="21" fill="#F29BB0" stroke="{INK}" '
          f'stroke-width="{SW}"/>')
    s += (f'<circle cx="729" cy="736" r="3.5" fill="{INK}"/>'
          f'<circle cx="745" cy="736" r="3.5" fill="{INK}"/>')
    s += f'<circle cx="683" cy="706" r="6.5" fill="{INK}"/>'
    return s


def coin(cx, cy, r=27):
    return (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{GOLD}" stroke="{INK}" stroke-width="6"/>'
            + text(cx, cy + 11, "$", 32))


def sun(cx, cy, r=42):
    import math
    s = f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#FFD76B" stroke="{INK}" stroke-width="6.5"/>'
    for a in range(0, 360, 45):
        c, sn = math.cos(math.radians(a)), math.sin(math.radians(a))
        s += line(cx + c * (r + 20), cy + sn * (r + 20), cx + c * (r + 42), cy + sn * (r + 42), 6)
    return s


def umbrella(cx, top=538, bottom=858, half=112):
    s = line(cx, top + 60, cx, bottom)
    s += path(f"M {cx - half},{top + 60} C {cx - half + 32},{top + 22} {cx - 30},{top} {cx},{top} "
              f"C {cx + 30},{top} {cx + half - 32},{top + 22} {cx + half},{top + 60} Z",
              fill=RED)
    return s


def waves(x0, x1, y):
    d, x = f"M {x0},{y}", x0
    while x + 48 <= x1:
        d += " q 12,-20 24,0 t 24,0"
        x += 48
    return path(d, w=6)


def plant(cx, base):
    s = path(f"M {cx - 30},{base - 55} L {cx + 30},{base - 55} L {cx + 24},{base} L {cx - 24},{base} Z",
             fill=BG)
    s += line(cx, base - 55, cx, base - 88, 6)
    s += path(f"M {cx},{base - 88} C {cx - 8},{base - 112} {cx - 38},{base - 110} {cx - 40},{base - 98} "
              f"C {cx - 36},{base - 84} {cx - 14},{base - 80} {cx},{base - 88} Z", fill=GREEN, w=5)
    s += path(f"M {cx},{base - 88} C {cx + 8},{base - 114} {cx + 38},{base - 112} {cx + 40},{base - 100} "
              f"C {cx + 36},{base - 86} {cx + 14},{base - 80} {cx},{base - 88} Z", fill=GREEN, w=5)
    return s


# ------------------------------------------------------------------ the quokka
def face(kind):
    def dot(x, y, r=8):
        return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{INK}"/>'

    nose = f'<ellipse cx="0" cy="32" rx="22" ry="16" fill="{INK}"/>'
    s = ""
    if kind == "deadpan":
        s += dot(-45, 2) + dot(45, 2) + nose
        s += line(-66, -24, -28, -24, 5.5) + line(28, -24, 66, -24, 5.5)
        s += line(-28, 68, 28, 68, 6)
    elif kind == "smile":
        s += dot(-45, 2) + dot(45, 2) + nose
        s += path("M -30,64 Q 0,92 30,64", w=6)
    elif kind == "smug":
        s += path("M -66,8 Q -46,-16 -26,8", w=6) + path("M 26,8 Q 46,-16 66,8", w=6)
        s += nose + path("M -34,62 Q 0,98 34,62", w=6)
    elif kind == "worried":
        s += dot(-45, 4) + dot(45, 4) + nose
        s += line(-66, -14, -28, -30, 5.5) + line(28, -30, 66, -14, 5.5)
        s += path("M -32,72 q 10.7,-12 21.3,0 t 21.3,0 t 21.4,0", w=6)
    elif kind == "panic":
        for sx in (-1, 1):
            s += (f'<circle cx="{sx * 45}" cy="2" r="17" fill="#fff" stroke="{INK}" '
                  f'stroke-width="5"/>')
            s += dot(sx * 45 - 3, 6, 6)
        s += path("M -66,-26 Q -46,-42 -28,-30", w=5.5) + path("M 28,-30 Q 46,-42 66,-26", w=5.5)
        s += nose + f'<ellipse cx="0" cy="78" rx="13" ry="17" fill="{INK}"/>'
        # sweat drop and stress lines
        s += path("M 124,-42 C 114,-20 110,-10 122,-4 C 134,-10 134,-22 124,-42 Z",
                  fill="#A9DDF5", w=4)
        s += line(0, -152, 0, -124, 6)
        s += line(-150, -120, -132, -104, 6) + line(150, -120, 132, -104, 6)
    elif kind == "shades":
        s += (f'<rect x="-86" y="-22" width="74" height="44" rx="20" fill="{INK}"/>'
              f'<rect x="12" y="-22" width="74" height="44" rx="20" fill="{INK}"/>')
        s += line(-14, -8, 14, -8, 6) + nose
        s += path("M -32,64 Q 0,94 32,64", w=6)
    return s


def quokka(cx, cy, s=1.0, mood="deadpan", arms="rest", flat=True, tail=False):
    """cx, cy = centre of the head. Body bottom sits at cy + 340*s (flat)."""
    g = f'<g transform="translate({cx},{cy}) scale({s})">'
    if tail:
        g += tube("M 104,296 C 146,292 162,318 150,336", w=16)
    if not flat:
        for sx in (-1, 1):
            g += (f'<ellipse cx="{sx * 52}" cy="338" rx="42" ry="17" fill="{PINK}" '
                  f'stroke="{INK}" stroke-width="{SW}"/>')
    # ears
    for sx in (-1, 1):
        g += (f'<circle cx="{sx * 92}" cy="-78" r="37" fill="{PINK}" stroke="{INK}" '
              f'stroke-width="{SW}"/>')
        g += f'<circle cx="{sx * 92}" cy="-76" r="20" fill="{PINK_DARK}"/>'
    # body
    if flat:
        body = "M -96,60 C -112,150 -118,250 -112,340 L 112,340 C 118,250 112,150 96,60 Z"
    else:
        body = ("M -96,60 C -112,150 -118,250 -112,305 Q -110,340 -70,340 L 70,340 "
                "Q 110,340 112,305 C 118,250 112,150 96,60 Z")
    g += path(body, fill=PINK)
    # tie
    g += path("M -14,104 L 14,104 L 10,124 L -10,124 Z", fill=RED, w=5)
    g += path("M -10,124 L 10,124 L 21,160 L 0,200 L -21,160 Z", fill=RED, w=5)
    # arms
    left_rest = path("M -52,196 C -70,224 -62,248 -42,258")
    right_rest = path("M 52,196 C 70,224 62,248 42,258")
    if arms == "rest":
        g += left_rest + right_rest
    elif arms == "up":
        g += tube("M -96,135 C -168,135 -190,50 -165,-35")
        g += tube("M 96,135 C 168,135 190,50 165,-35")
    elif arms == "shrug":
        g += tube("M -96,140 C -145,165 -190,160 -214,126")
        g += tube("M 96,140 C 145,165 190,160 214,126")
    elif arms == "mug":
        g += left_rest
        g += mug(150, 150, 62, 68)
        g += tube("M 96,135 C 128,140 146,155 154,176")
    elif arms == "drink":
        g += left_rest
        g += (f'<path d="M 142,6 L 198,6 L 190,62 L 150,62 Z" fill="{ORANGE}" stroke="{INK}" '
              f'stroke-width="{SW}" stroke-linejoin="round"/>')
        g += line(184, 6, 206, -30, 6)
        g += tube("M 96,132 C 128,140 165,120 170,72")
    elif arms == "coin":
        g += left_rest
        g += tube("M 96,130 C 150,128 205,112 255,102")
    # head + face
    g += (f'<ellipse cx="0" cy="0" rx="118" ry="100" fill="{PINK}" stroke="{INK}" '
          f'stroke-width="{SW}"/>')
    g += face(mood)
    return g + "</g>"


# ------------------------------------------------------------------ text layout
MAX_LINE = 900      # widest allowed caption line, px
PREFER_LINE = 860   # first line fills up to this before breaking


def wrap_caption(caption):
    """Return 1 or 2 lines. A '|' in the caption forces a line break.
    Raises ValueError if the caption cannot fit (shorten it)."""
    if "|" in caption:
        lines = [p.strip() for p in caption.split("|") if p.strip()]
    elif text_width(caption, CAP_SIZE) <= PREFER_LINE:
        lines = [caption.strip()]
    else:
        words = caption.split()
        options = []
        for i in range(1, len(words)):
            a, b = " ".join(words[:i]), " ".join(words[i:])
            options.append((a, b, text_width(a, CAP_SIZE), text_width(b, CAP_SIZE)))
        fits = [o for o in options if max(o[2], o[3]) <= MAX_LINE]
        if not fits:
            raise ValueError(f"caption too long for two lines: {caption!r}")
        best = min(max(o[2], o[3]) for o in fits)
        near = [o for o in fits if max(o[2], o[3]) <= best * 1.12]
        punct = [o for o in near if o[0][-1] in ".:,;?!"]
        pick = min(punct or near, key=lambda o: max(o[2], o[3]))
        lines = [pick[0], pick[1]]
    if len(lines) > 2:
        raise ValueError(f"more than two lines: {caption!r}")
    for l in lines:
        if text_width(l, CAP_SIZE) > MAX_LINE:
            raise ValueError(f"line too wide ({text_width(l, CAP_SIZE):.0f}px): {l!r}")
    return lines


def post_svg(header, caption, art):
    """art = SVG fragment string for the scene."""
    lines = wrap_caption(caption)
    if text_width(header, HEAD_SIZE) + 0.15 * HEAD_SIZE * len(header) > 800:
        raise ValueError(f"header too long: {header!r}")
    ys = [242, 320] if len(lines) == 2 else [268]
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
           f'viewBox="0 0 {W} {H}"><rect width="{W}" height="{H}" fill="{BG}"/>')
    svg += text(540, 115, header.upper(), HEAD_SIZE, HEAD_RED, spacing=0.15 * HEAD_SIZE)
    for y, l in zip(ys, lines):
        svg += text(540, y, l, CAP_SIZE)
    svg += art
    svg += text(540, 1000, "@pink.quocca", HANDLE_SIZE, bold=0.8)
    return svg + "</svg>"


def save_png(svg, png_path):
    os.makedirs(os.path.dirname(png_path) or ".", exist_ok=True)
    cairosvg.svg2png(bytestring=svg.encode(), write_to=png_path,
                     output_width=W, output_height=H)


def png_to_jpeg(png_path, jpg_path, quality=92):
    """Instagram's publishing API accepts JPEG only."""
    Image.open(png_path).convert("RGB").save(jpg_path, "JPEG", quality=quality, optimize=True)
