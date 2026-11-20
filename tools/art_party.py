"""Taller, more detailed map sprites for the playable cast (18x26 art in 24x28 frames).

NPCs stay small (16x16), so the party reads at a glance: bigger heads, shaded hair, eye highlights,
outlined bodies, a weapon on the back and a signature detail per character."""
from art_common import Canvas, hexc, mix, shade, sheet

SKINS = ["#f6d7b8", "#e8b890", "#c08860", "#8a5a3a", "#5a3a28"]
K = (63, 38, 49, 255)
FW, FH = 24, 28

# per-character signature details
SIG = {
    "hero":    {"weapon": "blade", "scarf": "#e0c070"},
    "kael":    {"weapon": "greatblade", "scar": True, "vest": True, "big": True, "band": "#c03020"},
    "nerissa": {"weapon": "trident", "long_hair": True, "shells": True},
    "pip":     {"weapon": "bow", "goggles": True, "cap": True, "wings": True, "small": True},
    "durga":   {"weapon": "axe", "helm_lamp": True, "beard": True, "big": True},
    "sol":     {"weapon": "staff", "robe": True, "beads": True, "bald": True},
    "vesper":  {"weapon": "bow", "long_hair": True, "fade": True, "lantern": True},
}


def _weapon_back(c, kind, d, cx, top, el_col):
    """Weapon slung across the back; drawn behind the body except when facing up."""
    steel = hexc("#d8dce8")
    wood = hexc("#7a5030")
    if kind in ("blade", "greatblade"):
        ln = 13 if kind == "greatblade" else 10
        x0, y0 = cx + (4 if d != 1 else -4), top + 2
        c.line(x0, y0, x0 - (4 if d != 1 else -4), y0 + ln, steel, 2 if kind == "greatblade" else 1)
        c.rect(x0 - 1, y0 - 1, 3, 1, hexc("#c0a040"))
        c.px(x0, y0 - 2, hexc("#6a3a1a"))
    elif kind == "axe":
        x0, y0 = cx + (4 if d != 1 else -4), top
        c.line(x0, y0, x0, y0 + 14, wood)
        c.rect(x0 - 2, y0, 4, 4, steel)
        c.px(x0 - 2, y0, shade(steel, 0.3))
    elif kind in ("staff", "trident"):
        x0, y0 = cx + (5 if d != 1 else -5), top - 3
        c.line(x0, y0, x0, y0 + 18, wood if kind == "staff" else hexc("#5a7a8a"))
        if kind == "trident":
            for dx in (-1, 0, 1):
                c.line(x0 + dx * 2, y0 - 2, x0 + dx * 2, y0 + 1, steel)
            c.rect(x0 - 2, y0 + 1, 5, 1, steel)
        else:
            c.ellipse(x0 + 0.5, y0, 2, 2, el_col)
            c.px(x0, y0 - 1, (255, 255, 255, 255))
    elif kind == "bow":
        x0, y0 = cx + (3 if d != 1 else -3), top + 1
        for i in range(13):
            off = round(2.5 * (1 - ((i - 6) / 6) ** 2))
            c.px(x0 + (off if d != 1 else -off), y0 + i, wood)
        c.line(x0, y0, x0, y0 + 12, hexc("#e0e0e0"))


def party_frame(lk, d, f, extra):
    """d: 0 down, 1 left, 2 right, 3 up.  f: 0 stand, 1 walk A, 2 walk B."""
    sig = dict(SIG.get(extra.get("cid", "hero"), {}))
    sig.update(extra)
    c = Canvas(FW, FH)
    skin = hexc(SKINS[lk.get("skin", 1)])
    hair = hexc(lk["hair"])
    out = hexc(lk["outfit"])
    acc = hexc(lk["accent"])
    small = sig.get("small")
    big = sig.get("big")
    cx = 12
    feet = 27
    bob = 1 if f in (1, 2) else 0
    side = d in (1, 2)
    left = d == 1
    el_col = hexc(sig.get("el_col", "#ffffff"))
    # ---------------------------------------------------------------- proportions
    head_h = 9 if not small else 8
    head_w = 11 if not small else 10
    body_h = 6 if not small else 5
    leg_h = 4 if not small else 3
    top = feet - leg_h - body_h - head_h + 1 + (2 if small else 0)
    hy = top + bob * 0 - (1 if f and not side else 0) * 0
    by = hy + head_h - 1          # torso top
    ly = by + body_h              # legs top
    bw = 9 if not big else 11
    # ---------------------------------------------------------------- back layer: weapon, wings, cape (not when facing up)
    wkind = sig.get("weapon", "blade") if not sig.get("no_back_weapon") else None
    if d != 3 and wkind:
        _weapon_back(c, wkind, d, cx, by - 2, el_col)
    if sig.get("wings") and d != 0:
        wc = hexc("#d8e8f0")
        for s_ in (-1, 1):
            if side and s_ == (1 if left else -1):
                continue
            c.poly([(cx + s_ * 3, by + 1), (cx + s_ * 10, by - 3), (cx + s_ * 9, by + 6)], wc)
            c.line(cx + s_ * 3, by + 1, cx + s_ * 10, by - 3, shade(wc, -0.3))
    if sig.get("cape") and d != 0:
        cc = hexc(sig["cape"])
        if d == 3:
            c.rect(cx - bw // 2, by, bw, body_h + 4, cc)
            c.rect(cx - bw // 2, by + body_h + 3, bw, 1, shade(cc, -0.35))
            c.rect(cx - bw // 2, by, bw, 1, shade(cc, 0.3))
        else:
            x0 = cx + (2 if left else -5)
            c.rect(x0, by, 3, body_h + 3, cc)
            c.px(x0 + (0 if left else 2), by + body_h + 3, shade(cc, -0.3))
    # ---------------------------------------------------------------- legs
    pants = shade(out, -0.4)
    boots = hexc("#3a2620")
    robe = sig.get("robe") or lk["body"] == "woman"
    if robe:
        for i, yy in enumerate(range(ly - 1, feet)):
            w = bw - 2 + min(4, i)
            col = out if yy < feet - 1 else shade(out, -0.35)
            c.rect(cx - w // 2, yy, w, 1, col)
        c.rect(cx - (bw + 2) // 2, ly + 2, bw + 2, 1, shade(acc, -0.1))  # hem trim
        if f:
            c.px(cx - 3 if f == 1 else cx + 2, feet - 1, boots)
        else:
            c.rect(cx - 3, feet - 1, 2, 1, boots)
            c.rect(cx + 1, feet - 1, 2, 1, boots)
    elif not side:
        la = 1 if f == 1 else 0
        lb = 1 if f == 2 else 0
        c.rect(cx - 4, ly, 3, leg_h - la, pants)
        c.rect(cx + 1, ly, 3, leg_h - lb, pants)
        c.rect(cx - 4, ly + leg_h - la - 2, 3, 2, boots)
        c.rect(cx + 1, ly + leg_h - lb - 2, 3, 2, boots)
        c.px(cx - 4, ly + leg_h - la - 2, shade(boots, 0.3))
        c.px(cx + 1, ly + leg_h - lb - 2, shade(boots, 0.3))
    else:
        s_ = 0 if f == 0 else (1 if f == 1 else -1)
        c.rect(cx - 2 + s_, ly, 3, leg_h, pants)
        c.rect(cx - 1 - s_, ly, 3, leg_h, shade(pants, -0.15))
        c.rect(cx - 2 + s_ + (-1 if left else 0), feet - 2, 4, 2, boots)
        c.rect(cx - 1 - s_ + (-1 if left else 0), feet - 2, 4, 2, shade(boots, -0.2))
    # ---------------------------------------------------------------- torso
    tx = cx - bw // 2
    c.rect(tx, by, bw, body_h, out)
    c.rect(tx, by, bw, 1, shade(out, 0.25))
    c.rect(tx + bw - 2, by + 1, 2, body_h - 1, shade(out, -0.2))   # side shading
    c.rect(tx, by + body_h - 2, bw, 1, acc)                         # belt
    c.px(cx, by + body_h - 2, shade(acc, 0.4))                      # buckle
    if sig.get("vest"):
        c.rect(cx - 1, by, 2, body_h - 2, skin)                     # open vest shows chest
        c.px(cx, by + 2, shade(skin, -0.2))
    if not side and d == 0:
        c.rect(cx - 1, by, 2, 2, shade(out, -0.3))                  # collar
    if sig.get("scarf") and d != 3:
        sc = hexc(sig["scarf"])
        c.rect(tx + 1, by, bw - 2, 2, sc)
        c.rect(tx + 1, by + 1, bw - 2, 1, shade(sc, -0.25))
        if not side:
            c.rect(cx + 2, by + 2, 2, 3, sc)
    if sig.get("beads") and d != 3:
        for i in range(5):
            c.px(cx - 2 + i, by + 2 + (1 if i in (1, 2, 3) else 0), hexc("#8a3a2a") if i != 2 else hexc("#f0d060"))
    if sig.get("shells") and d != 3:
        c.px(cx - 2, by + 1, hexc("#f0e8e0"))
        c.px(cx, by + 2, hexc("#f0b0c0"))
        c.px(cx + 2, by + 1, hexc("#f0e8e0"))
    if sig.get("pads"):
        pc = hexc("#b0b0c0") if not sig.get("cape") else acc
        c.rect(tx - 1, by, 3, 3, pc)
        c.rect(tx + bw - 2, by, 3, 3, pc)
        c.px(tx - 1, by, shade(pc, 0.4))
    # arms
    swing = 0 if f == 0 else (1 if f == 1 else -1)
    sleeve = shade(out, -0.12) if not sig.get("vest") else skin
    if not side:
        for s_, sw in ((-1, swing), (1, -swing)):
            ax = cx - bw // 2 - 2 if s_ < 0 else cx + bw // 2
            c.rect(ax, by + 1 + max(0, sw), 2, 5, sleeve)
            c.rect(ax, by + 6 + max(0, sw), 2, 2, skin)
    else:
        ax = cx - 1 + swing * (1 if not left else -1)
        c.rect(ax, by + 1, 3, 5, shade(sleeve, -0.1))
        c.rect(ax, by + 6, 3, 2, skin)
    if sig.get("lantern") and d != 3:
        lx = cx + (bw // 2 + 1 if not left else -bw // 2 - 3)
        c.rect(lx, by + 7, 2, 3, hexc("#c090ff"))
        c.px(lx, by + 7, (255, 255, 255, 255))
        c.px(lx + 1, by + 6, hexc("#5a4a6a"))
    # ---------------------------------------------------------------- head
    hx = cx - head_w // 2
    c.rect(hx + 1, hy + 1, head_w - 2, head_h - 1, skin)
    c.rect(hx, hy + 2, head_w, head_h - 3, skin)
    c.rect(hx + head_w - 2, hy + 3, 1, head_h - 4, shade(skin, -0.15))
    hair_hi = shade(hair, 0.3)
    hair_lo = shade(hair, -0.3)
    bald = sig.get("bald")
    if d == 3:
        if not bald:
            c.rect(hx, hy, head_w, head_h - 1, hair)
            c.rect(hx + 2, hy, head_w - 4, 1, hair_hi)
            c.rect(hx, hy + head_h - 3, head_w, 1, hair_lo)
        else:
            c.rect(hx + 2, hy, head_w - 4, 1, shade(skin, 0.2))
    else:
        if not bald:
            c.rect(hx, hy, head_w, 3, hair)
            c.rect(hx + 1, hy - 1, head_w - 2, 1, hair)
            c.rect(hx + 2, hy - 1, 4, 1, hair_hi)
            c.px(hx + 3, hy, hair_hi)
            if d == 0:
                c.rect(hx, hy + 3, 1, 4, hair)
                c.rect(hx + head_w - 1, hy + 3, 1, 4, hair)
                c.px(hx + 4, hy + 3, hair)   # fringe
                c.px(hx + 7, hy + 3, hair)
            else:
                back = hx + (head_w - 4 if left else 0)
                c.rect(back, hy, 4, 7, hair)
                c.rect(back, hy + 6, 4, 1, hair_lo)
        if d == 0:
            ey = hy + 5
            for ex in (hx + 3, hx + head_w - 5):
                c.rect(ex, ey, 2, 2, K)
                c.px(ex, ey, (255, 255, 255, 255))
                if sig.get("glow_eyes"):
                    c.px(ex + 1, ey + 1, hexc(sig["glow_eyes"]))
            c.px(hx + 2, ey + 2, mix(skin, hexc("#e07070"), 0.35))   # cheeks
            c.px(hx + head_w - 3, ey + 2, mix(skin, hexc("#e07070"), 0.35))
            c.px(cx, min(hy + head_h - 1, ey + 3), shade(skin, -0.3))     # mouth
        else:
            ex = hx + (2 if left else head_w - 4)
            ey = hy + 5
            c.rect(ex, ey, 2, 2, K)
            c.px(ex + (0 if left else 1), ey, (255, 255, 255, 255))
            nose = hx - 1 if left else hx + head_w
            c.px(nose, ey + 1, skin)
    if sig.get("long_hair") and not bald:
        if d == 3:
            c.rect(hx, hy + head_h - 3, head_w, 6, hair)
            c.rect(hx + 1, hy + head_h + 2, head_w - 2, 1, hair_lo)
        elif d == 0:
            c.rect(hx - 1, hy + 2, 2, 9, hair)
            c.rect(hx + head_w - 1, hy + 2, 2, 9, hair)
        else:
            back = hx + (head_w - 3 if left else -1)
            c.rect(back, hy + 3, 4, 9, hair)
    if sig.get("beard") and d != 3:
        if d == 0:
            c.rect(hx + 2, hy + head_h - 3, head_w - 4, 3, hair)
            c.px(cx, hy + head_h - 3, shade(skin, -0.3))
        else:
            c.rect(hx + (1 if left else head_w - 5), hy + head_h - 3, 4, 3, hair)
    if sig.get("scar") and d == 0:
        c.line(hx + head_w - 4, hy + 3, hx + head_w - 3, hy + 7, hexc("#b05040"))
    if sig.get("band") and d != 3:
        c.rect(hx, hy + 2, head_w, 1, hexc(sig["band"]))
    if sig.get("cap") or lk.get("hat") == "cap":
        cap = acc
        c.rect(hx, hy - 1, head_w, 3, cap)
        c.rect(hx + 1, hy - 2, head_w - 2, 1, cap)
        c.px(hx + 3, hy - 1, shade(cap, 0.35))
        if d == 0:
            c.rect(hx + 1, hy + 2, head_w - 2, 1, shade(cap, -0.35))
        elif side:
            c.rect(hx - 2 if left else hx + head_w - 3, hy + 1, 5, 1, shade(cap, -0.35))
    if sig.get("goggles") and d != 3:
        gx = hx + 2 if d == 0 else hx + (1 if left else head_w - 5)
        c.rect(gx, hy + 1, 3 if d == 0 else 4, 2, hexc("#a0e0ff"))
        if d == 0:
            c.rect(gx + 5, hy + 1, 3, 2, hexc("#a0e0ff"))
        c.rect(hx, hy + 1, head_w, 1, shade(hexc("#6a4a2a"), 0.1))
        c.px(gx, hy + 1, (255, 255, 255, 255))
    if sig.get("helm_lamp") or lk.get("hat") == "helm":
        m = hexc("#9a9aa8")
        c.rect(hx - 1, hy - 2, head_w + 2, 4, m)
        c.rect(hx - 1, hy - 2, head_w + 2, 1, shade(m, 0.35))
        c.rect(hx - 1, hy + 1, head_w + 2, 1, shade(m, -0.35))
        if sig.get("helm_lamp") and d != 3:
            lx = cx - 1 if d == 0 else (hx if left else hx + head_w - 2)
            c.rect(lx, hy - 2, 2, 2, hexc("#fff0a0"))
            c.px(lx, hy - 2, (255, 255, 255, 255))
    if sig.get("circlet") and d != 3:
        c.rect(hx, hy + 2, head_w, 1, hexc("#f0d060"))
        c.px(cx if d == 0 else (hx + 2 if left else hx + head_w - 3), hy + 2, (255, 255, 255, 255))
    if d == 3 and wkind:
        _weapon_back(c, wkind, d, cx, by - 2, el_col)
    if sig.get("fade"):
        for y in range(feet - 6, feet):
            for x in range(FW):
                if (x + y) % 2 == 0 and c.a[y, x, 3] > 0:
                    c.a[y, x, 3] = 90
    c.outline(K)
    c.rim_light(0.12, 0.12)
    return c


def party_sheet(cid, lk, extra):
    ex = dict(extra)
    ex["cid"] = cid
    frames = [party_frame(lk, d, f, ex) for d in range(4) for f in range(3)]
    return sheet(frames, cols=3)


# ------------------------------------------------------------------ battle sprites (Tiny style: 20x20 art doubled to 40x40)
import math
import numpy as np
from PIL import Image

POSES = ["idle", "idle2", "ready", "attack", "cast", "hurt", "ko", "victory"]
CROP = (2, 8)      # top-left of the 20x20 window taken from the 24x28 map frame


def _geom(lk, sig):
    small = sig.get("small")
    head_h = 9 if not small else 8
    body_h = 6 if not small else 5
    leg_h = 4 if not small else 3
    top = 27 - leg_h - body_h - head_h + 1 + (2 if small else 0)
    by = top + head_h - 1
    return top, by, body_h


def _arr(c):
    return c.a.copy()


def _shift_rows(a, r0, r1, dx=0, dy=0):
    out = a.copy()
    band = a[r0:r1].copy()
    out[r0:r1] = 0
    for y in range(band.shape[0]):
        ny = r0 + y + dy
        if 0 <= ny < a.shape[0]:
            row = np.roll(band[y], dx, axis=0)
            if dx > 0:
                row[:dx] = 0
            elif dx < 0:
                row[dx:] = 0
            m = row[:, 3] > 0
            out[ny][m] = row[m]
    return out


def _arm(a, x0, y0, x1, y1, sleeve, skin):
    n = max(abs(x1 - x0), abs(y1 - y0), 1)
    for i in range(n + 1):
        x = round(x0 + (x1 - x0) * i / n)
        y = round(y0 + (y1 - y0) * i / n)
        for ox in (0, 1):
            if 0 <= x + ox < a.shape[1] and 0 <= y < a.shape[0]:
                a[y, x + ox] = sleeve
    for oy in (0, 1):
        for ox in (0, 1):
            if 0 <= x1 + ox < a.shape[1] and 0 <= y1 + oy < a.shape[0]:
                a[y1 + oy, x1 + ox] = skin


def _crop2x(a):
    x0, y0 = CROP
    w = a[y0:y0 + 20, x0:x0 + 20]
    return np.repeat(np.repeat(w, 2, axis=0), 2, axis=1)


def battle_frames(cid, lk, extra):
    sig = dict(SIG.get(cid, {}))
    sig.update(extra)
    sig["cid"] = cid
    sig["no_back_weapon"] = True
    top, by, body_h = _geom(lk, sig)
    skin = hexc(SKINS[lk.get("skin", 1)])
    sleeve = shade(hexc(lk["outfit"]), -0.12) if not sig.get("vest") else skin
    left = lambda f: _arr(party_frame(lk, 1, f, sig))
    front = _arr(party_frame(lk, 0, 0, sig))
    waist = by + body_h
    cx = 12
    frames, hands = [], []
    for pose in POSES:
        if pose == "idle":
            a, hand, ang = left(0), (cx - 1, by + 6), 250
        elif pose == "idle2":
            a, hand, ang = _shift_rows(left(0), 0, by + 2, dy=1), (cx - 1, by + 7), 252
        elif pose == "ready":
            a = _shift_rows(left(1), 0, waist, dx=-1)
            hand, ang = (cx - 3, by + 4), 220
        elif pose == "attack":
            a = _shift_rows(_shift_rows(left(2), 0, waist, dx=-2), 0, 28, dx=-1)
            _arm(a, cx - 3, by + 1, cx - 7, by + 3, sleeve, skin)
            hand, ang = (cx - 7, by + 3), 180
        elif pose == "cast":
            a = left(0)
            _arm(a, cx - 2, by + 1, cx - 6, by - 4, sleeve, skin)
            hand, ang = (cx - 6, by - 4), 270
        elif pose == "hurt":
            a = _shift_rows(_shift_rows(left(0), 0, waist, dx=2), 0, 28, dx=1)
            m = (a[:, :, 3] > 0) & (a[:, :, :3].sum(axis=2) > 200)
            a[m, :3] = (a[m, :3] * 0.6 + 255 * 0.4).astype(np.uint8)
            hand, ang = (cx + 1, by + 6), 320
        elif pose == "ko":
            b = left(0)
            r = np.rot90(b, 1)                    # lying on their back, head toward the enemies
            ys, xs = np.nonzero(r[:, :, 3])
            r = r[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
            a = np.zeros((28, 24, 4), np.uint8)
            h, w = r.shape[:2]
            ox = max(0, (24 - w) // 2)
            a[27 - h + 1:28, ox:ox + w] = r[:h, :min(w, 24 - ox)]
            hand, ang = (cx - 6, 26), 180
        else:  # victory: turn to the player and raise the weapon
            a = _shift_rows(front, 0, 28, dy=-1)
            _arm(a, cx + 4, by, cx + 6, by - 4, sleeve, skin)
            hand, ang = (cx + 6, by - 4), 270
        frames.append(_crop2x(a))
        hands.append(((hand[0] - CROP[0]) * 2 + 1, (hand[1] - CROP[1]) * 2 + 1, ang))
    return frames, hands


def weapon_frames(kind, el_cols, hands):
    """Weapons drawn at Tiny scale (1px = 2 screen px) in each pose's hand."""
    hi, lo = (hexc(x) for x in el_cols)
    grip = hexc("#6a3a24")
    out = []
    for i, (hx, hy, ang) in enumerate(hands):
        c = Canvas(20, 20)
        x, y = (hx - 1) / 2, (hy - 1) / 2
        a = math.radians(ang)
        dx, dy = math.cos(a), math.sin(a)
        pose = POSES[i]
        if kind == "blade":
            c.px(round(x - dx), round(y - dy), grip)
            px_, py_ = -dy, dx
            c.px(round(x + px_), round(y + py_), hexc("#d0a040"))
            c.px(round(x - px_), round(y - py_), hexc("#d0a040"))
            for t in range(1, 7):
                c.px(round(x + dx * t), round(y + dy * t), hi if t % 2 else lo)
        elif kind == "bow":
            for t in range(-4, 5):
                c.px(round(x - 1 - (1 if abs(t) < 3 else 0)), round(y + t), lo if t % 2 else hi)
            pull = 2 if pose in ("attack", "ready") else 0
            c.px(round(x + pull), round(y), (240, 240, 240, 255))
            for t in (-3, -2, -1, 1, 2, 3):
                c.px(round(x - 1 + pull * (1 - abs(t) / 4)), round(y + t), (230, 230, 230, 255))
            if pose in ("attack", "ready"):
                for t in range(4):
                    c.px(round(x - 2 - t), round(y), hexc("#d8c8a8"))
        else:
            for t in range(-4, 6):
                c.px(round(x + dx * t), round(y + dy * t), grip)
            gx, gy = round(x + dx * 6), round(y + dy * 6)
            c.rect(gx - 1, gy - 1, 2, 2, lo)
            c.px(gx - 1, gy - 1, hi)
            if pose == "cast":
                for k in range(6):
                    aa = k / 6 * math.tau
                    c.px(round(gx + math.cos(aa) * 3), round(gy + math.sin(aa) * 3), hi[:3] + (200,))
        if ang == 180 and pose == "ko":
            c = Canvas(20, 20)
        c.outline(K)
        out.append(np.repeat(np.repeat(c.a, 2, axis=0), 2, axis=1))
    return out


def to_sheet(frames):
    return Image.fromarray(np.concatenate(frames, axis=1), "RGBA")


# ------------------------------------------------------------------ Tiny-style party (built on Kenney's Tiny Dungeon heroes)
TINY_BASE = {
    "hero":    (("dungeon", 85), {"#c0cbdc": "#2f9aa8", "#8b9bb4": "#1f6470", "#bd6c4a": "#7a4424", "#763b36": "#3a2a30"}),
    "kael":    (("dungeon", 112), {"#25956a": "#b02a1a", "#43e1b3": "#f05a3a", "#f7c282": "#c88a5e", "#e19a65": "#9a6444",
                                   "#bd6c4a": "#2a1a12", "#763b36": "#5a2418"}),
    "nerissa": (("dungeon", 99), {"#9b4ca3": "#e8e4d8", "#d176d0": "#ffffff", "#bd6c4a": "#2a7aa0", "#eaa56c": "#4a9ac0",
                                  "#763b36": "#1a5a9a"}),
    "pip":     (("ski", 82), {"#d176d0": "#2aa898", "#009adc": "#e84a2a", "#00c6f4": "#ff7a50"}),
    "durga":   (("dungeon", 87), {"#bd6c4a": "#9a4220", "#f7c282": "#c88a5e", "#e19a65": "#9a6444", "#52607c": "#5a6a3a",
                                  "#eaa56c": "#b06a3a"}),
    "sol":     (("dungeon", 86), {"#c0cbdc": "#f0c060", "#8b9bb4": "#c08a30", "#763b36": "#c04040", "#bd6c4a": "#1a1a1a"}),
    "vesper":  (("dungeon", 100), {"#8b9bb4": "#c8c8e0", "#c0cbdc": "#f0f0ff", "#763b36": "#5a2a8a", "#bd6c4a": "#8a4ac0"}),
}
TOUT = (63, 38, 49, 255)


def _hx(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _put_behind(a, x, y, col):
    if 0 <= x < a.shape[1] and 0 <= y < a.shape[0] and a[y, x, 3] == 0:
        a[y, x] = col


def _put(a, x, y, col):
    if 0 <= x < a.shape[1] and 0 <= y < a.shape[0]:
        a[y, x] = col


def tiny_base(cid, extra, with_back_weapon=True):
    """20x20 canvas: the recolored Tiny hero at (2,4) plus their signature details."""
    import art_kenney as AK
    (pack, idx), cmap = TINY_BASE[cid]
    t = AK.tile(pack, idx)
    for src, dst in cmap.items():
        m = np.all(t[:, :, :3] == np.array(_hx(src)), axis=2) & (t[:, :, 3] > 0)
        t[m, :3] = _hx(dst)
    a = np.zeros((20, 20, 4), np.uint8)
    a[4:20, 2:18] = t
    sig = dict(SIG.get(cid, {}))
    sig.update(extra)
    gold = (240, 200, 70, 255)
    # weapon slung on the back (drawn only where the body isn't)
    w = sig.get("weapon", "blade")
    if with_back_weapon:
        steel, wood = (216, 220, 232, 255), (122, 80, 48, 255)
        if w in ("blade", "greatblade", "axe"):
            for k in range(7 if w != "greatblade" else 9):
                _put_behind(a, 15 - k // 2, 3 + k, steel)
            _put_behind(a, 16, 3, gold if w != "axe" else steel)
            if w == "axe":
                for yy in (3, 4):
                    for xx in (15, 16, 17):
                        _put_behind(a, xx, yy, steel)
        elif w in ("staff", "trident"):
            for k in range(13):
                _put_behind(a, 16, 2 + k, wood)
            _put_behind(a, 16, 1, (120, 200, 255, 255) if w == "trident" else gold)
            if w == "trident":
                _put_behind(a, 15, 1, steel)
                _put_behind(a, 17, 1, steel)
        else:  # bow
            for k in range(10):
                _put_behind(a, 16 + (1 if 2 < k < 7 else 0), 4 + k, wood)
    if sig.get("wings"):
        wc = (216, 236, 248, 255)
        for (x, y) in [(1, 9), (0, 8), (1, 10), (0, 10), (1, 11), (18, 9), (19, 8), (18, 10), (19, 10), (18, 11), (0, 9), (19, 9)]:
            _put_behind(a, x, y, wc)
    if sig.get("cape"):
        cc = _hx(sig["cape"]) + (255,)
        for y in range(11, 19):
            _put_behind(a, 2, y, cc)
            _put_behind(a, 17, y, cc)
    if sig.get("scarf"):
        sc = _hx(sig["scarf"]) + (255,)
        for x in range(5, 15):
            if a[14, x, 3] and tuple(a[14, x, :3]) != TOUT[:3]:
                a[14, x] = sc
        _put(a, 12, 15, sc)
        _put(a, 12, 16, sc)
    if sig.get("pads"):
        for x, y in [(4, 15), (5, 15), (14, 15), (15, 15)]:
            if a[y, x, 3]:
                a[y, x] = gold
    if sig.get("circlet"):
        for x in range(6, 14):
            if a[6, x, 3] and tuple(a[6, x, :3]) != TOUT[:3]:
                a[6, x] = gold
        _put(a, 10, 6, (255, 255, 255, 255))
    if sig.get("glow_eyes"):
        m = np.all(a[:, :, :3] == np.array(_hx("#262b44")), axis=2) & (a[:, :, 3] > 0)
        a[m, :3] = _hx(sig["glow_eyes"])
    if sig.get("scar"):
        _put(a, 12, 8, (200, 70, 60, 255))
        _put(a, 12, 9, (200, 70, 60, 255))
    if sig.get("shells"):
        _put(a, 8, 15, (250, 240, 236, 255))
        _put(a, 10, 16, (240, 170, 190, 255))
        _put(a, 12, 15, (250, 240, 236, 255))
    if sig.get("beads"):
        for x in range(7, 13):
            _put(a, x, 15 + (1 if 8 < x < 11 else 0), (140, 58, 42, 255) if x != 10 else gold)
    if sig.get("lamp") or sig.get("helm_lamp"):
        _put(a, 9, 4, (255, 244, 160, 255))
        _put(a, 10, 4, (255, 255, 255, 255))
    if sig.get("lantern"):
        for x, y in [(3, 15), (3, 16), (2, 15), (2, 16)]:
            _put(a, x, y, (200, 150, 255, 255))
        _put(a, 3, 14, TOUT)
    if sig.get("fade"):
        for y in range(16, 20):
            for x in range(20):
                if (x + y) % 2 == 0 and a[y, x, 3] > 0:
                    a[y, x, 3] = 90
    return a


def tiny_map_sheet(cid, extra):
    """Exploring sheet in 24x28 frames (down, left, right, up), with a little hop while walking."""
    base = tiny_base(cid, extra)
    frames = []
    for d in range(4):
        src = base[:, ::-1].copy() if d == 1 else base
        for f in range(3):
            fr = np.zeros((FH, FW, 4), np.uint8)
            dy = -1 if f else 0
            s2 = src[:, ::-1].copy() if (f == 2 and d in (0, 3)) else src
            y0 = FH - 20 + dy
            region = fr[y0:y0 + 20, 2:22]
            m = s2[:, :, 3] > 0
            region[m] = s2[m]
            frames.append(fr)
    rows = [np.concatenate(frames[r * 3:(r + 1) * 3], axis=1) for r in range(4)]
    return Image.fromarray(np.concatenate(rows, axis=0), "RGBA")


def tiny_battle_frames(cid, extra):
    """Battle poses from the same Tiny hero (facing the enemies on the left), doubled to 40x40."""
    sig = dict(SIG.get(cid, {}))
    sig.update(extra)
    base = tiny_base(cid, extra, with_back_weapon=False)[:, ::-1].copy()
    skin = (247, 194, 130, 255) if cid not in ("kael", "durga") else (200, 138, 94, 255)
    sleeve = tuple(int(v) for v in base[14, 5])
    if sleeve[3] == 0 or sleeve[:3] == TOUT[:3]:
        sleeve = skin
    waist = 16
    frames, hands = [], []
    for pose in POSES:
        if pose == "idle":
            a, hand, ang = base.copy(), (4, 15), 250
        elif pose == "idle2":
            a, hand, ang = _shift_rows(base, 0, 12, dy=1), (4, 15), 252
        elif pose == "ready":
            a, hand, ang = _shift_rows(base, 0, waist, dx=-1), (3, 13), 220
        elif pose == "attack":
            a = _shift_rows(_shift_rows(base, 0, waist, dx=-2), 0, 20, dx=-1)
            _arm(a, 3, 13, 0, 13, sleeve, skin)
            hand, ang = (0, 13), 180
        elif pose == "cast":
            a = base.copy()
            _arm(a, 4, 12, 2, 7, sleeve, skin)
            hand, ang = (2, 7), 270
        elif pose == "hurt":
            a = _shift_rows(_shift_rows(base, 0, waist, dx=2), 0, 20, dx=1)
            m = (a[:, :, 3] > 0) & (a[:, :, :3].sum(axis=2) > 200)
            a[m, :3] = (a[m, :3] * 0.6 + 255 * 0.4).astype(np.uint8)
            hand, ang = (6, 15), 320
        elif pose == "ko":
            r = np.rot90(base, 1)
            ys, xs = np.nonzero(r[:, :, 3])
            r = r[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
            a = np.zeros((20, 20, 4), np.uint8)
            h, w = r.shape[:2]
            h, w = min(h, 20), min(w, 20)
            ox = (20 - w) // 2
            a[20 - h:20, ox:ox + w] = r[:h, :w]
            hand, ang = (1, 19), 180
        else:  # victory
            a = _shift_rows(tiny_base(cid, extra, with_back_weapon=False), 0, 20, dy=-1)
            _arm(a, 15, 12, 16, 7, sleeve, skin)
            hand, ang = (16, 7), 270
        frames.append(np.repeat(np.repeat(a, 2, axis=0), 2, axis=1))
        hands.append((hand[0] * 2 + 1, hand[1] * 2 + 1, ang))
    return frames, hands
