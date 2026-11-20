"""Composes characters from the Universal LPC Spritesheet Character Generator's layers (CC-BY-SA 3.0 / GPL 3 / OGA-BY / CC0).

A character is a body type plus a list of items: (sheet-definition name, color or variant). Each item's layers are
recolored with the generator's palettes, stacked by zPos and cut into whole animation sheets.
Every definition used is recorded so the game can credit its artists.
"""
import glob
import json
import os

import numpy as np
from PIL import Image

LPC = os.environ.get("LPC_DIR", os.path.expanduser("~/liberatedpixelcup/universal-lpc-spritesheet-character-generator"))
SHEETS = os.path.join(LPC, "spritesheets")
ANIM_FRAMES = {"walk": 9, "slash": 6, "spellcast": 7, "thrust": 8, "shoot": 13, "hurt": 6, "idle": 2, "combat_idle": 2}
ROWS = {"hurt": 1}
CREDITS = {}          # definition file -> credits list

_defs = None
_pal = {}


def _index():
    global _defs
    if _defs is None:
        _defs = {}
        for f in glob.glob(os.path.join(LPC, "sheet_definitions", "**", "*.json"), recursive=True):
            name = os.path.basename(f)[:-5]
            if not name.startswith("meta_"):
                _defs[name] = f
    return _defs


def definition(name):
    path = _index()[name]
    d = json.load(open(path))
    if d.get("credits"):
        CREDITS[name] = d["credits"]
    return d


def palettes(material):
    if material not in _pal:
        meta = json.load(open(os.path.join(LPC, "palette_definitions", material, f"meta_{material}.json")))
        p = json.load(open(os.path.join(LPC, "palette_definitions", material, f"{material}_ulpc.json")))
        try:
            p.update({k: v for k, v in json.load(open(os.path.join(LPC, "palette_definitions", material,
                                                                    f"{material}_lpcr.json"))).items() if k not in p})
        except FileNotFoundError:
            pass
        _pal[material] = (meta.get("base"), p)
    return _pal[material]


def _hx(h):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def recolor(a, material, target, base=None):
    """Swap the material's base palette for the target palette (exact colors, +-1 tolerance)."""
    if not target:
        return a
    mbase, pals = palettes(material)
    if base and "." in base:
        base = base.split(".")[1]
    b = pals.get(base or mbase)
    t = pals.get(target)
    if not b or not t or b == t:
        return a
    out = a.copy()
    rgb = a[:, :, :3].astype(int)
    for src, dst in zip(b, t):
        s = np.array(_hx(src))
        m = (np.abs(rgb - s).max(axis=2) <= 1) & (a[:, :, 3] > 0)
        out[m, :3] = _hx(dst)
    return out


def _find(path, anim, variant):
    base = os.path.join(SHEETS, path)
    tries = [f"{anim}.png"]
    if variant:
        tries = [f"{anim}/{variant}.png", f"{variant}/{anim}.png", f"{anim}.png", f"{variant}.png"]
    else:
        tries += [f"{anim}/{os.path.basename(path.rstrip('/'))}.png"]
    for t in tries:
        p = os.path.join(base, t)
        if os.path.isfile(p):
            return p
    # single-variant folders (e.g. "walk/longsword.png")
    d = os.path.join(base, anim)
    if os.path.isdir(d):
        pngs = sorted(f for f in os.listdir(d) if f.endswith(".png"))
        if pngs:
            return os.path.join(d, pngs[0])
    return None


CUSTOM = {"slash_oversize": ("slash", 192), "slash_reverse_oversize": (None, 192), "thrust_oversize": ("thrust", 192),
          "walk_128": ("walk", 128), "slash_128": ("slash", 128), "backslash_128": (None, 128), "halfslash_128": (None, 128),
          # work tools: 6-frame swings over the body's slash (pickaxe, axe, hammer)
          "tool_axe": ("slash", 128), "tool_hammer": ("slash", 128)}    # paired by hand in art_lpc.job_sheet


MISSING = set()


def layers_for(name, body, anim, color=None, variant=None):
    """[(z, rgba array, frame size)] for one item and animation."""
    if name not in _index():
        MISSING.add(name)
        return []
    d = definition(name)
    out = []
    has_custom_for_anim = any(
        CUSTOM.get(d[k].get("custom_animation", ""), (None,))[0] == anim for k in d if k.startswith("layer_"))
    for k in sorted(k for k in d if k.startswith("layer_")):
        L = d[k]
        path = L.get(body) or L.get("male") or (L.get("female") if body in ("teen", "male", "muscular") else None)
        if not path:
            continue
        if variant is None and color is not None and not d.get("recolors") and d.get("variants"):
            variant = color if isinstance(color, str) else None
        ca = L.get("custom_animation")
        if ca:
            a_name, fsize = CUSTOM.get(ca, (None, 64))
            if a_name != anim:
                continue
            # custom-animation layers keep their image directly in the folder
            cands = [os.path.join(SHEETS, path, f"{variant}.png")] if variant else []
            cands += sorted(glob.glob(os.path.join(SHEETS, path, "*.png")))
            cands.append(os.path.join(SHEETS, path.rstrip("/") + ".png"))      # e.g. tools/pickaxe/bg.png
            p = next((c for c in cands if os.path.isfile(c)), None)
        else:
            if has_custom_for_anim and k in ("layer_1", "layer_2") and anim in ("slash", "thrust") and "weapon" in path:
                continue     # the oversize attack replaces the universal weapon layer
            fsize = 64
            p = _find(path, anim, variant)
            if not p and anim in ("idle", "combat_idle"):
                # muscular bodies and some items have no idle poses: stand still on walk frame 0
                pw = _find(path, "walk", variant)
                if pw:
                    w = np.array(Image.open(pw).convert("RGBA"))
                    col = w[:, 0:64]
                    a = np.concatenate([col, col], axis=1)
                    out.append(_recolor_item(d, a, color, L.get("zPos", 0), fsize))
                continue
        if not p:
            continue
        a = np.array(Image.open(p).convert("RGBA"))
        out.append(_recolor_item(d, a, color, L.get("zPos", 0), fsize))
    return out


def _recolor_item(d, a, color, z, fsize):
    rc = d.get("recolors")
    if rc and color is not None:
        if "material" in rc:
            a = recolor(a, rc["material"], color if isinstance(color, str) else color.get("color_1"), rc.get("base"))
        else:
            cs = color if isinstance(color, dict) else {"color_1": color}
            for ck, cv in rc.items():
                if isinstance(cv, dict) and ck in cs:
                    a = recolor(a, cv["material"], cs[ck], cv.get("base"))
    return (z, a, fsize)


def compose(body, items, anim, frame=96):
    """Stack all items for one animation into a sheet with square `frame`-px cells (character centered, feet aligned)."""
    n = ANIM_FRAMES[anim]
    rows = ROWS.get(anim, 4)
    sheet = np.zeros((rows * frame, n * frame, 4), np.uint8)
    stack = []
    for it in items:
        name, opts = it[0], (it[1] if len(it) > 1 else {})
        stack += layers_for(name, body, anim, opts.get("color"), opts.get("variant"))
    stack.sort(key=lambda s: s[0])
    for z, a, fs in stack:
        r_avail = a.shape[0] // fs
        c_avail = a.shape[1] // fs
        for r in range(min(rows, r_avail)):
            for c in range(min(n, c_avail)):
                cell = a[r * fs:(r + 1) * fs, c * fs:(c + 1) * fs]
                # align the 64px body grid at the bottom-center of our cell
                off = (fs - 64) // 2
                ox = (frame - 64) // 2 - off
                oy = (frame - 64) - off - (8 if frame > 64 else 0)
                y0, x0 = r * frame + oy, c * frame + ox
                sy0 = max(0, -oy)
                sx0 = max(0, -ox)
                sy1 = min(fs, frame - oy)
                sx1 = min(fs, frame - ox)
                if sy1 <= sy0 or sx1 <= sx0:
                    continue
                src = cell[sy0:sy1, sx0:sx1]
                dst = sheet[y0 + sy0:y0 + sy1, x0 + sx0:x0 + sx1]
                # proper "over" blending: half-transparent pixels (hood linings, shading) must not punch holes
                sa = src[:, :, 3:4].astype(np.float32) / 255.0
                if not sa.any():
                    continue
                da = dst[:, :, 3:4].astype(np.float32) / 255.0
                oa = sa + da * (1.0 - sa)
                rgb = (src[:, :, :3] * sa + dst[:, :, :3] * da * (1.0 - sa)) / np.maximum(oa, 1e-6)
                dst[:, :, :3] = np.clip(rgb, 0, 255).astype(np.uint8)
                dst[:, :, 3:4] = np.clip(oa * 255.0 + 0.5, 0, 255).astype(np.uint8)
    return sheet


def frame_of(sheet, anim, row, col, frame=96):
    return sheet[row * frame:(row + 1) * frame, col * frame:(col + 1) * frame].copy()


def write_credits(path, used=None):
    rows = ["item,file,authors,licenses,urls"]
    for name, creds in sorted(CREDITS.items()):
        if used and name not in used:
            continue
        for c in creds:
            q = lambda v: '"' + str(v).replace('"', "'") + '"'
            rows.append(",".join([q(name), q(c.get("file", "")), q("; ".join(c.get("authors", []))),
                                  q("; ".join(c.get("licenses", []))), q(" ".join(c.get("urls", [])))]))
    open(path, "w").write("\n".join(rows) + "\n")
