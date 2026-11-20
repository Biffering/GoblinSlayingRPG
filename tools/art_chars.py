"""Characters: 16x16 map sprites (in 20x20 frames) and 40x40 side-view battle sprites with weapons."""
import json
import math
import random
import sys

from art_common import Canvas, hexc, mix, shade, sheet, save, aura_map
import art_party as AP
import art_kenney as AK

SKINS = ["#f6d7b8", "#e8b890", "#c08860", "#8a5a3a", "#5a3a28"]
OUT = None
K = (20, 14, 28, 255)

# ------------------------------------------------------------------ map sprites (16x16 art, 20x20 frames)


def map_frame(lk, d, f, extra=None):
    """d: 0 down, 1 left, 2 right, 3 up.  f: 0 stand, 1 walk A, 2 walk B."""
    extra = extra or {}
    c = Canvas(16, 16)
    skin = hexc(SKINS[lk.get("skin", 1)])
    hair = hexc(lk["hair"])
    out = hexc(lk["outfit"])
    acc = hexc(lk["accent"])
    body = lk["body"]
    oy = 2 if body == "child" else 0
    hunch = 1 if body == "elder" else 0
    side = d in (1, 2)
    flip = d == 1
    # legs
    pants = shade(out, -0.35) if body not in ("woman",) else shade(out, -0.2)
    boots = hexc("#3a2a24")
    leg_y = 12 + (1 if body == "child" else 0)
    leg_len = 3 if body != "child" else 2
    robe = body in ("robe",) or lk.get("hat") == "hood" and body == "elder"
    if not robe and body != "woman":
        if not side:
            la = 1 if f == 1 else 0
            lb = 1 if f == 2 else 0
            c.rect(6, leg_y, 2, leg_len - la, pants)
            c.rect(8, leg_y, 2, leg_len - lb, pants)
            c.rect(6, leg_y + leg_len - la, 2, 1, boots)
            c.rect(8, leg_y + leg_len - lb, 2, 1, boots)
        else:
            if f == 0:
                c.rect(7, leg_y, 2, leg_len, pants)
                c.rect(7, leg_y + leg_len, 3, 1, boots)
            else:
                s = 1 if f == 1 else -1
                c.line(7, leg_y, 7 - s, leg_y + leg_len - 1, pants)
                c.line(8, leg_y, 8 + s, leg_y + leg_len - 1, pants)
                c.rect(6 - s, leg_y + leg_len, 2, 1, boots)
                c.rect(8 + s, leg_y + leg_len, 2, 1, boots)
    # torso
    ty = 8 + oy - (1 if body == "child" else 0)
    th = 4 if body != "child" else 3
    if body == "woman" or robe:
        # skirt / robe flares to the feet
        bot = 15
        for i, yy in enumerate(range(ty, bot + 1)):
            w = 6 + min(2, i // 2)
            x0 = 8 - w // 2
            c.rect(x0, yy, w, 1, out if yy < bot else shade(out, -0.3))
        if f and not side:
            c.px(5 if f == 1 else 10, bot, shade(out, -0.3))
    c.rect(5, ty, 6, th, out)
    c.rect(5, ty + th - 1, 6, 1, acc)  # belt / sash
    if lk.get("body") == "guard" or extra.get("pads"):
        c.rect(4, ty, 2, 2, hexc("#a0a0b0") if not extra.get("pads") else acc)
        c.rect(10, ty, 2, 2, hexc("#a0a0b0") if not extra.get("pads") else acc)
    # arms
    swing = 0 if f == 0 else (1 if f == 1 else -1)
    if not side:
        c.rect(4, ty, 1, 3 - max(0, swing), shade(out, -0.15))
        c.rect(11, ty, 1, 3 - max(0, -swing), shade(out, -0.15))
        c.px(4, ty + 3 - max(0, swing), skin)
        c.px(11, ty + 3 - max(0, -swing), skin)
    else:
        ax = 7 + swing
        c.rect(ax, ty + 1, 2, 2, shade(out, -0.15))
        c.px(ax + (1 if swing >= 0 else 0), ty + 3, skin)
    # cape (hero tier 2+)
    if extra.get("cape") and d != 0:
        cc = hexc(extra["cape"])
        if d == 3:
            c.rect(5, ty, 6, 6, cc)
            c.rect(5, ty + 5, 6, 1, shade(cc, -0.3))
        else:
            cx = 9 if d == 1 else 5
            c.rect(cx, ty, 2, 5, cc)
    # merchant pack
    if body == "merchant" and d != 0:
        if d == 3:
            c.rect(5, ty - 1, 6, 5, hexc("#8a6a3a"))
        else:
            c.rect(10 if d == 2 else 4, ty - 1, 2, 5, hexc("#8a6a3a"))
    # head
    hy = 1 + oy + hunch
    hx = 4 + (hunch if d == 2 else -hunch if d == 1 else 0)
    c.rect(hx + 1, hy, 6, 1, hair)
    c.rect(hx, hy + 1, 8, 6, skin)
    c.rect(hx + 1, hy + 7, 6, 0 if body == "child" else 0, skin)
    if d == 3:
        c.rect(hx, hy + 1, 8, 6, hair)
    elif d == 0:
        c.rect(hx, hy + 1, 8, 2, hair)
        c.px(hx, hy + 3, hair)
        c.px(hx + 7, hy + 3, hair)
        eye = hexc("#1a1424")
        c.px(hx + 2, hy + 4, eye)
        c.px(hx + 5, hy + 4, eye)
        if extra.get("glow_eyes"):
            c.px(hx + 2, hy + 4, hexc(extra["glow_eyes"]))
            c.px(hx + 5, hy + 4, hexc(extra["glow_eyes"]))
        c.px(hx + 1, hy + 5, shade(skin, -0.12))
        c.px(hx + 6, hy + 5, shade(skin, -0.12))
    else:
        # profile: face toward the facing side
        c.rect(hx, hy + 1, 8, 2, hair)
        if d == 2:
            c.rect(hx, hy + 1, 3, 5, hair)
            c.px(hx + 5, hy + 4, hexc("#1a1424"))
            c.px(hx + 8, hy + 4, skin)
        else:
            c.rect(hx + 5, hy + 1, 3, 5, hair)
            c.px(hx + 2, hy + 4, hexc("#1a1424"))
            c.px(hx - 1, hy + 4, skin)
    if body == "woman" and d != 0:
        if d == 3:
            c.rect(hx, hy + 6, 8, 3, hair)
        else:
            c.rect(hx + (0 if d == 2 else 5), hy + 5, 3, 4, hair)
    elif body == "woman":
        c.rect(hx - 1, hy + 2, 1, 6, hair)
        c.rect(hx + 8, hy + 2, 1, 6, hair)
    if lk.get("beard") and d != 3:
        if d == 0:
            c.rect(hx + 1, hy + 5, 6, 2, hair)
            c.rect(hx + 2, hy + 7, 4, 1, hair)
            c.px(hx + 3, hy + 5, skin)
            c.px(hx + 4, hy + 5, skin)
        else:
            bx = hx + 4 if d == 2 else hx + 1
            c.rect(bx, hy + 5, 3, 2, hair)
    hat = lk.get("hat")
    if hat == "hood":
        hc = shade(out, -0.1)
        c.rect(hx - 1, hy - 1, 10, 3, hc)
        c.rect(hx - 1, hy + 2, 1, 5, hc)
        c.rect(hx + 8, hy + 2, 1, 5, hc)
        if d == 3:
            c.rect(hx, hy, 8, 7, hc)
    elif hat == "cap":
        c.rect(hx, hy - 1, 8, 2, acc)
        if d == 0:
            c.rect(hx + 1, hy + 1, 6, 1, shade(acc, -0.3))
        elif d == 2:
            c.rect(hx + 5, hy + 1, 4, 1, shade(acc, -0.3))
        elif d == 1:
            c.rect(hx - 1, hy + 1, 4, 1, shade(acc, -0.3))
    elif hat == "helm":
        m = hexc("#9a9aa8")
        c.rect(hx - 1, hy - 1, 10, 4, m)
        c.rect(hx - 1, hy - 1, 10, 1, shade(m, 0.3))
        if d == 0:
            c.rect(hx + 3, hy + 3, 2, 2, m)
    elif hat == "wide":
        c.rect(hx - 2, hy + 1, 12, 1, acc)
        c.rect(hx + 1, hy - 2, 6, 3, acc)
    elif hat == "crown":
        g = hexc("#f0c040")
        c.rect(hx + 1, hy - 1, 6, 1, g)
        for k in (1, 3, 5):
            c.px(hx + k + 0.5, hy - 2, g)
    if extra.get("circlet") and d != 3:
        c.rect(hx, hy + 2, 8, 1, hexc("#f0d060"))
        c.px(hx + 3 if d != 1 else hx + 4, hy + 2, hexc("#ffffff"))
    if extra.get("fade"):
        # half-faded: dither out the lower body
        for y in range(12, 16):
            for x in range(16):
                if (x + y) % 2 == 0:
                    c.a[y, x] = 0
    c.outline()
    frame = Canvas(20, 20)
    frame.blit(c, 2, 2)
    return frame


def map_sheet(lk, extra=None):
    frames = []
    for d in range(4):
        for f in range(3):
            frames.append(map_frame(lk, d, f, extra))
    return sheet(frames, cols=3)


# ------------------------------------------------------------------ battle sprites (side view facing left, 40x40)

POSES = ["idle", "idle2", "ready", "attack", "cast", "hurt", "ko", "victory"]


def battle_frame(lk, pose, extra=None):
    """Side view facing LEFT. Returns canvas and the weapon hand position + weapon angle."""
    extra = extra or {}
    c = Canvas(40, 40)
    skin = hexc(SKINS[lk.get("skin", 1)])
    hair = hexc(lk["hair"])
    out = hexc(lk["outfit"])
    acc = hexc(lk["accent"])
    pants = shade(out, -0.35)
    boots = hexc("#3a2a24")
    body = lk["body"]
    small = body == "child"
    big = extra.get("big", False)
    sc = 0.85 if small else (1.08 if big else 1.0)
    # base anchor: feet at y=37, body center x=20
    bx, fy = 20, 37
    breath = 1 if pose == "idle2" else 0
    lean = {"ready": -2, "attack": -4, "hurt": 3, "ko": 0, "cast": 1, "victory": 0}.get(pose, 0)
    if pose == "ko":
        # kneeling slumped
        kx = bx + 2
        c.ellipse(kx + 2, fy - 2, 6 * sc, 2.5, pants)
        c.rect(kx - 6, fy - 2, 6, 2, boots)
        c.ellipse(kx, fy - 9, 5 * sc, 5 * sc, out)
        c.rect(kx - 5, fy - 7, 10, 1, acc)
        c.ellipse(kx - 5, fy - 12, 4 * sc, 4 * sc, skin)
        c.ellipse(kx - 4, fy - 14, 4 * sc, 3 * sc, hair)
        c.line(kx - 3, fy - 8, kx - 7, fy - 3, skin, 2)
        c.outline()
        c.rim_light(0.2, 0.25)
        return c, (kx - 7, fy - 3), 200
    hip_y = fy - int(11 * sc)
    sh_y = hip_y - int(10 * sc) + breath
    hx = bx + lean
    # back leg / front leg (front = left side since facing left)
    stride = {"ready": 4, "attack": 6, "hurt": 1, "victory": 2}.get(pose, 2)
    c.line(bx + 1, hip_y, bx + 2 + stride // 2, fy - 1, shade(pants, -0.15), 3)
    c.rect(bx + 1 + stride // 2, fy - 1, 4, 2, boots)
    if body != "woman" and not extra.get("robe"):
        c.line(bx - 1, hip_y, bx - 2 - stride // 2, fy - 1, pants, 3)
        c.rect(bx - 5 - stride // 2, fy - 1, 4, 2, boots)
    # back arm
    back_hand = (hx + 6, sh_y + 8)
    if pose == "cast":
        back_hand = (hx + 2, sh_y - 7)
    elif pose == "victory":
        back_hand = (hx + 5, sh_y + 7)
    c.line(hx + 3, sh_y + 1, back_hand[0], back_hand[1], shade(out, -0.25), 3)
    c.px(back_hand[0], back_hand[1] + 1, shade(skin, -0.15))
    # cape
    if extra.get("cape"):
        cc = hexc(extra["cape"])
        wave = 1 if pose in ("idle2", "attack") else 0
        c.poly([(hx + 1, sh_y), (hx + 5, sh_y), (bx + 8 + wave, fy - 2), (bx + 3, fy - 1)], cc)
        c.line(bx + 3, fy - 2, bx + 8 + wave, fy - 3, shade(cc, -0.3))
    # torso
    tw = int(8 * sc)
    c.poly([(hx - tw // 2, sh_y), (hx + tw // 2, sh_y), (bx + tw // 2, hip_y + 1), (bx - tw // 2, hip_y + 1)], out)
    if body == "woman" or extra.get("robe"):
        c.poly([(bx - tw // 2, hip_y - 1), (bx + tw // 2, hip_y - 1), (bx + tw // 2 + 4, fy - 1), (bx - tw // 2 - 4, fy - 1)],
               shade(out, -0.1))
        c.rect(bx - tw // 2 - 4, fy - 1, tw + 8, 1, shade(out, -0.4))
    c.rect(bx - tw // 2, hip_y - 1, tw + 1, 2, acc)
    if extra.get("pads"):
        c.ellipse(hx - 1, sh_y + 1, 4, 2.5, acc)
    if extra.get("vest"):  # bare arms, vest
        c.rect(hx - 2, sh_y + 1, 3, int(9 * sc), shade(out, 0.15))
    # head
    hr = 5.2 * sc
    hcx, hcy = hx - 1, sh_y - hr + 1
    c.ellipse(hcx, hcy, hr, hr, skin)
    # hair: back of head is to the right (facing left)
    c.ellipse(hcx + 1.5, hcy - 1.5, hr, hr * 0.75, hair)
    c.rect(int(hcx), int(hcy - hr), int(hr + 2), 3, hair)
    if body == "woman":
        c.poly([(hcx + 1, hcy - 2), (hcx + hr + 1, hcy - 1), (hcx + hr + 2, hcy + 9), (hcx + 2, hcy + 6)], hair)
    # face details
    eye_c = hexc(extra["glow_eyes"]) if extra.get("glow_eyes") else hexc("#1a1424")
    ex = int(hcx - hr * 0.55)
    ey = int(hcy)
    c.px(ex, ey, eye_c)
    c.px(ex, ey - 1, shade(hair, -0.2))
    c.px(int(hcx - hr) , ey + 1, skin)
    c.px(int(hcx - hr * 0.5), ey + 3, shade(skin, -0.25))
    if lk.get("beard"):
        c.ellipse(hcx - 1, hcy + 3, 3.5, 2.5, hair)
    hat = lk.get("hat")
    if hat == "helm":
        m = hexc("#9a9aa8")
        c.ellipse(hcx + 0.5, hcy - 1.5, hr + 0.8, hr * 0.8, m)
        c.rect(int(hcx - hr), int(hcy - 1), int(2 * hr + 1), 2, shade(m, -0.2))
        if extra.get("lamp"):
            c.ellipse(hcx - hr + 1, hcy - 3, 1.8, 1.8, hexc("#fff0a0"))
    elif hat == "cap":
        c.ellipse(hcx + 1, hcy - 2.5, hr, hr * 0.55, acc)
        c.rect(int(hcx - hr - 2), int(hcy - 2), 5, 2, shade(acc, -0.25))
        if extra.get("goggles"):
            c.rect(int(hcx - 2), int(hcy - 4), 5, 2, hexc("#d0e8f0"))
    elif hat == "hood":
        hc = shade(out, -0.1)
        c.ellipse(hcx + 1.5, hcy - 0.5, hr + 1.5, hr + 1.2, hc)
        c.ellipse(hcx - 1.5, hcy + 0.5, hr * 0.7, hr * 0.8, skin)
        c.px(ex, ey, eye_c)
    if extra.get("circlet"):
        c.line(hcx - hr, hcy - 2, hcx + hr, hcy - 3, hexc("#f0d060"))
        c.px(int(hcx - hr + 1), int(hcy - 2), hexc("#ffffff"))
    if extra.get("scar"):
        c.line(ex - 1, ey - 2, ex + 2, ey + 2, hexc("#c04040"))
    # signature details so each party member is recognisable at a glance
    if extra.get("band"):
        c.line(hcx - hr, hcy - 2, hcx + hr, hcy - 2, hexc(extra["band"]))
        c.line(hcx + hr, hcy - 2, hcx + hr + 3, hcy + 1 + (1 if pose == "idle2" else 0), hexc(extra["band"]))
    if extra.get("scarf"):
        sc_ = hexc(extra["scarf"])
        c.rect(int(hx - 3), int(sh_y - 1), 7, 2, sc_)
        wave = 1 if pose in ("idle2", "attack", "ready") else 0
        c.line(hx + 4, sh_y, hx + 8 + wave, sh_y + 4, sc_, 2)
    if extra.get("shells"):
        for k_ in range(3):
            c.px(int(hx - 2 + k_ * 2), int(sh_y + 2), hexc("#f0e0e8") if k_ != 1 else hexc("#f0a0b8"))
    if extra.get("beads"):
        for k_ in range(4):
            c.px(int(hx - 3 + k_), int(sh_y + 2 + (k_ % 2)), hexc("#8a3a2a") if k_ != 2 else hexc("#f0d060"))
    if extra.get("wings") and pose != "ko":
        wc = hexc("#d8e8f0")
        flap = -2 if pose in ("idle2", "attack") else 0
        c.poly([(hx + 3, sh_y + 2), (hx + 14, sh_y - 6 + flap), (hx + 12, sh_y + 7)], wc)
        c.line(hx + 3, sh_y + 2, hx + 14, sh_y - 6 + flap, shade(wc, -0.35))
    if extra.get("lantern") and pose not in ("ko",):
        lx_, ly_ = int(hx + 7), int(sh_y + 9)
        c.rect(lx_, ly_, 3, 4, hexc("#c090ff"))
        c.px(lx_ + 1, ly_ + 1, hexc("#ffffff"))
        c.px(lx_ + 1, ly_ - 1, hexc("#5a4a6a"))
    # front arm (holds the weapon)
    arm_c = skin if extra.get("vest") else shade(out, -0.05)
    if pose in ("idle", "idle2"):
        hand = (hx - 6, sh_y + 8 + breath)
        ang = 300
    elif pose == "ready":
        hand = (hx - 2, sh_y + 1)
        ang = 250
    elif pose == "attack":
        hand = (hx - 11, sh_y + 5)
        ang = 190
    elif pose == "cast":
        hand = (hx - 8, sh_y - 6)
        ang = 290
    elif pose == "hurt":
        hand = (hx - 3, sh_y + 7)
        ang = 330
    else:  # victory
        hand = (hx - 4, sh_y - 9)
        ang = 270
    c.line(hx - 2, sh_y + 1, hand[0], hand[1], arm_c, 3)
    c.ellipse(hand[0], hand[1], 1.6, 1.6, skin)
    if extra.get("fade"):
        for y in range(fy - 8, 40):
            for x in range(40):
                if (x + y) % 2 == 0 or (y > fy - 3 and (x * 3 + y) % 3 != 0):
                    c.a[y, x] = 0
    c.outline()
    c.rim_light(0.22, 0.28)
    if pose == "hurt":
        for y in range(40):
            for x in range(40):
                if c.a[y, x, 3] and tuple(c.a[y, x][:3]) != K[:3]:
                    c.a[y, x, :3] = [min(255, int(v * 0.7 + 255 * 0.3)) for v in c.a[y, x, :3]]
    return c, hand, ang


WEAPON_COLORS = {
    None: ("#c8ccd8", "#8a8e9a"), "fire": ("#ff7a3a", "#c02a10"), "water": ("#7ac0ff", "#2a5ab0"),
    "wind": ("#8af0e0", "#2aa090"), "stone": ("#a0d870", "#4a7a3a"), "spirit": ("#fffbe8", "#d0b050"),
    "void": ("#c090ff", "#4a2a7a"),
}


def weapon_frame(kind, el, pose, hand, ang):
    c = Canvas(40, 40)
    hi, lo = (hexc(x) for x in WEAPON_COLORS[el])
    grip = hexc("#5a3a24")
    x, y = hand
    a = math.radians(ang)
    dx, dy = math.cos(a), math.sin(a)
    if kind == "blade":
        # hilt behind hand, blade forward along angle
        c.line(x - dx * 2, y - dy * 2, x + dx * 1, y + dy * 1, grip, 2)
        px, py = -dy, dx
        c.line(x + dx * 1 - px * 2.5, y + dy * 1 - py * 2.5, x + dx * 1 + px * 2.5, y + dy * 1 + py * 2.5, hexc("#d0a040"), 1)
        c.line(x + dx * 2, y + dy * 2, x + dx * 13, y + dy * 13, lo, 3)
        c.line(x + dx * 2, y + dy * 2, x + dx * 14, y + dy * 14, hi, 1)
        if pose == "attack":
            # slash arc
            for t in range(9):
                aa = a - 1.2 + t * 0.22
                c.px(round(x + math.cos(aa) * 15), round(y + math.sin(aa) * 15), (255, 255, 255, 120 + t * 12))
    elif kind == "bow":
        # bow held vertically-ish in front of the hand
        bowx = x - 1
        top = (bowx + 2, y - 10)
        bot = (bowx + 2, y + 10)
        for t in range(21):
            yy = y - 10 + t
            xx = bowx - 3 * math.sin(t / 20 * math.pi)
            c.px(round(xx), yy, lo if t % 3 else hi)
            c.px(round(xx) + 1, yy, hi if t % 4 == 0 else lo)
        pull = 6 if pose in ("attack", "ready") else 2
        c.line(top[0], top[1], bowx + pull, y, hexc("#f0f0f0"))
        c.line(bot[0], bot[1], bowx + pull, y, hexc("#f0f0f0"))
        if pose in ("attack", "ready"):
            c.line(bowx - 7, y, bowx + pull, y, hexc("#d8c8a8"))
            c.px(bowx - 8, y, hi)
    else:  # staff
        c.line(x - dx * 8, y - dy * 8, x + dx * 9, y + dy * 9, grip, 2)
        gx, gy = x + dx * 10, y + dy * 10
        c.ellipse(gx, gy, 2.6, 2.6, lo)
        c.ellipse(gx - 0.5, gy - 0.5, 1.5, 1.5, hi)
        if pose == "cast":
            for t in range(8):
                aa = t / 8 * math.tau
                c.px(round(gx + math.cos(aa) * 5), round(gy + math.sin(aa) * 5), hi[:3] + (180,))
    c.outline()
    return c


# ------------------------------------------------------------------ cast list

PARTY_LOOKS = {
    "hero": ({"body": "man", "hair": "#6a3a1e", "outfit": "#2a6a7a", "accent": "#e0c070", "skin": 1}, {"scarf": "#e0c070"}),
    "kael": ({"body": "man", "hair": "#2a1a12", "outfit": "#7a2a18", "accent": "#d8c090", "skin": 2}, {"vest": True, "scar": True, "big": True, "band": "#c03020"}),
    "nerissa": ({"body": "woman", "hair": "#2a6a8a", "outfit": "#e4e0d0", "accent": "#1a5a9a", "skin": 0}, {"shells": True}),
    "pip": ({"body": "child", "hair": "#e0b030", "outfit": "#2a9a8a", "accent": "#f05030", "skin": 1, "hat": "cap"}, {"goggles": True, "wings": True}),
    "durga": ({"body": "man", "hair": "#8a3a1a", "outfit": "#5a6a3a", "accent": "#c0c0c0", "skin": 2, "hat": "helm", "beard": True}, {"lamp": True, "big": True}),
    "sol": ({"body": "man", "hair": "#1a1a1a", "outfit": "#e0b060", "accent": "#c04040", "skin": 1}, {"robe": True, "beads": True}),
    "vesper": ({"body": "woman", "hair": "#d0d0e0", "outfit": "#4a2a6a", "accent": "#a060f0", "skin": 0}, {"fade": True, "lantern": True}),
}

HERO_TIERS = [
    {},
    {"pads": True},
    {"pads": True, "cape": "#8a2030"},
    {"pads": True, "cape": "#8a2030", "circlet": True, "glow_eyes": "#fff4b0"},
]


def build_party(out):
    meta = {}
    for cid, (lk, ex) in PARTY_LOOKS.items():
        tiers = HERO_TIERS if cid == "hero" else [{}]
        for ti, tex in enumerate(tiers):
            extra = dict(ex)
            extra.update(tex)
            suffix = f"_t{ti}" if cid == "hero" else ""
            # map sheet: taller, more detailed than townsfolk
            ms = AP.tiny_map_sheet(cid, extra) if AK.available() else AP.party_sheet(cid, lk, extra)
            save(ms, f"{out}/chars/{cid}{suffix}.png")
            save(aura_map(ms, AP.FW, AP.FH, 3), f"{out}/chars/{cid}{suffix}_aura.png")
            # battle sheet: the same Tiny-style character, side view, doubled
            frames, hands = AP.tiny_battle_frames(cid, extra) if AK.available() else AP.battle_frames(cid, lk, extra)
            bs = AP.to_sheet(frames)
            save(bs, f"{out}/battle/{cid}{suffix}.png")
            save(aura_map(bs, 40, 40, 4), f"{out}/battle/{cid}{suffix}_aura.png")
            meta[cid + suffix] = [list(h) for h in hands]
    for cid in list(PARTY_LOOKS):
        hands = meta[cid if cid != "hero" else "hero_t0"]
        for kind in ("blade", "bow", "staff"):
            for el in WEAPON_COLORS:
                save(AP.to_sheet(AP.weapon_frames(kind, WEAPON_COLORS[el], hands)), f"{out}/weapons/{cid}_{kind}_{el or 'none'}.png")
    return meta


def build_npcs(out, maps_dir):
    import glob
    seen = set()
    for path in glob.glob(f"{maps_dir}/*.json"):
        m = json.load(open(path))
        for n in m["npcs"]:
            if n["id"] in seen:
                continue
            seen.add(n["id"])
            lk = n["look"]
            extra = {}
            if n["id"] in PARTY_LOOKS:
                lk, extra = PARTY_LOOKS[n["id"]]
                save(AP.tiny_map_sheet(n["id"], extra) if AK.available() else AP.party_sheet(n["id"], lk, extra),
                     f"{out}/chars/npc_{n['id']}.png")
                continue
            if AK.available():
                import zlib
                ms = AK.sheet_from_sprite(AK.npc_sprite(lk, zlib.crc32(n["id"].encode())))
                save(ms, f"{out}/chars/npc_{n['id']}.png")
                continue
            if lk["body"] == "merchant":
                lk = dict(lk)
            ms = map_sheet(lk, extra)
            save(ms, f"{out}/chars/npc_{n['id']}.png")
    return len(seen)


if __name__ == "__main__":
    out = sys.argv[1]
    maps_dir = sys.argv[2]
    meta = build_party(out)
    n = build_npcs(out, maps_dir)
    json.dump(meta, open(f"{out}/battle/hands.json", "w"))
    print("party sheets:", len(meta), "npcs:", n)
