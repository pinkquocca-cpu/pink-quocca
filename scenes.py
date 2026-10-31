"""
Scenes: what the quokka is doing in a post.

Each scene takes (mood, arms, trend, label) and returns an SVG fragment.
captions.csv picks a scene by name and fills in those four settings.
"""
from engine import (BG, GOLD, GREEN, INK, RED, W, coin, desk, line, mug, path, piggy,
                    plant, quokka, screen, sun, text, umbrella, waves)

MOODS = ("deadpan", "smile", "smug", "worried", "panic", "shades")
TRENDS = ("down", "up", "flat")


# ------------------------------------------------------------------ extra props
def coin_stacks():
    s = ""
    for cx, n in ((650, 3), (738, 5), (826, 7)):
        for k in range(n):
            y = 800 - 17 * (k + 1)
            s += (f'<rect x="{cx - 38}" y="{y}" width="76" height="17" rx="8" fill="{GOLD}" '
                  f'stroke="{INK}" stroke-width="5.5" stroke-linejoin="round"/>')
    return s


def calendar(label="MON"):
    x, y, w, h = 640, 462, 232, 236
    s = (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="#fff" '
         f'stroke="{INK}" stroke-width="7"/>')
    s += (f'<path d="M {x},{y + 54} L {x},{y + 10} Q {x},{y} {x + 10},{y} L {x + w - 10},{y} '
          f'Q {x + w},{y} {x + w},{y + 10} L {x + w},{y + 54} Z" fill="{RED}" stroke="{INK}" '
          f'stroke-width="7" stroke-linejoin="round"/>')
    for rx in (x + 56, x + w - 56):
        s += line(rx, y - 16, rx, y + 16, 9)
    s += text(x + w / 2, y + 42, label, 34, "#FFFFFF")
    gx0, gy0, cw, ch = x + 18, y + 72, (w - 36) / 4, (h - 90) / 3
    for i in range(1, 4):
        s += line(gx0 + cw * i, gy0, gx0 + cw * i, gy0 + ch * 3, 3, "#CFC8AE")
    for j in range(1, 3):
        s += line(gx0, gy0 + ch * j, gx0 + cw * 4, gy0 + ch * j, 3, "#CFC8AE")
    s += (f'<circle cx="{gx0 + cw * 2.5:.1f}" cy="{gy0 + ch * 1.5:.1f}" r="26" fill="none" '
          f'stroke="{RED}" stroke-width="6"/>')
    return s


def receipt(label="BILLS"):
    x0, x1, top, base = 650, 864, 428, 786
    teeth = 7
    step = (x1 - x0) / teeth
    d = f"M {x0},{top} L {x1},{top} L {x1},{base - 14}"
    for i in range(teeth):
        xr = x1 - step * (i + 1)
        d += f" L {xr + step / 2:.1f},{base} L {xr:.1f},{base - 14}"
    d += " Z"
    s = path(d, fill="#fff", w=7)
    s += text((x0 + x1) / 2, top + 52, label, 36)
    for i, ln in enumerate((150, 120, 168, 100, 140)):
        yy = top + 92 + i * 44
        s += line(x0 + 24, yy, x0 + 24 + ln, yy, 6)
    s += line(x0 + 24, base - 52, x1 - 24, base - 52, 9, RED)
    return s


# ---------------------------------------------------------------------- scenes
def scene_desk(mood, arms, trend, label, two_screens=False):
    arms = arms or "rest"
    if arms not in ("rest", "mug", "up", "shrug"):
        raise ValueError(f"desk scene: arms must be rest, mug, up or shrug (got {arms!r})")
    cx = {"rest": 520, "mug": 520, "up": 430, "shrug": 420}[arms]
    s = quokka(cx, 545, 1, mood, arms)
    if arms == "rest":
        s += mug(262, 724)
    s += screen(665, 485, 210, 165, trend, label or None)
    if two_screens and arms == "rest":
        s += screen(675, 683, 140, 115, trend)
    return s + desk()


def scene_desk2(mood, arms, trend, label):
    return scene_desk(mood, arms or "rest", trend, label, two_screens=True)


def scene_plant(mood, arms, trend, label):
    return (quokka(520, 545, 1, mood, "shrug") + plant(772, 800) + desk()
            + text(772, 852, label or "day 1,826", 30))


def scene_piggy(mood, arms, trend, label):
    return (line(205, 848, 875, 848)
            + quokka(345, 493, 1, mood, "coin", flat=False)
            + piggy() + coin(628, 592))


def scene_beach(mood, arms, trend, label):
    return (sun(215, 430) + quokka(430, 552, 0.9, mood, "drink") + umbrella(790)
            + line(200, 858, 900, 858) + waves(205, 895, 910))


def scene_coins(mood, arms, trend, label):
    return quokka(420, 545, 1, mood, "rest") + coin_stacks() + desk()


def scene_calendar(mood, arms, trend, label):
    return quokka(420, 545, 1, mood, "rest") + calendar(label or "MON") + desk()


def scene_bills(mood, arms, trend, label):
    return quokka(420, 545, 1, mood, "rest") + receipt(label or "BILLS") + desk()


# name -> (function, default mood, default trend)
SCENES = {
    "desk": (scene_desk, "deadpan", "down"),
    "desk2": (scene_desk2, "deadpan", "down"),
    "plant": (scene_plant, "worried", "flat"),
    "piggy": (scene_piggy, "smile", "flat"),
    "beach": (scene_beach, "shades", "flat"),
    "coins": (scene_coins, "smile", "flat"),
    "calendar": (scene_calendar, "deadpan", "flat"),
    "bills": (scene_bills, "worried", "flat"),
}


def render_scene(scene, mood="", arms="", trend="", label=""):
    scene = (scene or "desk").strip().lower()
    if scene not in SCENES:
        raise ValueError(f"unknown scene {scene!r}; choose from {', '.join(SCENES)}")
    fn, dmood, dtrend = SCENES[scene]
    mood = (mood or dmood).strip().lower()
    trend = (trend or dtrend).strip().lower()
    if mood not in MOODS:
        raise ValueError(f"unknown mood {mood!r}; choose from {', '.join(MOODS)}")
    if trend not in TRENDS:
        raise ValueError(f"unknown trend {trend!r}; choose from {', '.join(TRENDS)}")
    return fn(mood, (arms or "").strip().lower(), trend, (label or "").strip())
