"""Dark-fantasy UI kit to match the LPC art: riveted iron frames over worn leather, a sword cursor.

usage: python3 art_ui_lpc.py <assets_dir>
Writes ui/window.png (main), ui/window_dark.png (banners, hints), ui/window_gold.png (bosses, treasure)
and ui/cursor.png. 9-slice margin is 6px; the 24x24 center tiles.
"""
import random
import sys
from PIL import Image

M = 6          # frame margin
C = 24         # tiled center
S = M * 2 + C


def hexc(h, a=255):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def window(leather, iron, rivet, seed=1, alpha=255):
    """leather: (base, dark, light); iron: (outline, hi, mid, lo, inner); rivet: (hi, mid, lo)."""
    rng = random.Random(seed)
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    px = im.load()
    base, dark, light = [hexc(c, alpha) for c in leather]
    # leather: mottled, with a few scratches; wraps so the tiled center has no seams
    for y in range(S):
        for x in range(S):
            n = rng.random()
            px[x, y] = dark if n < 0.12 else light if n > 0.94 else base
    for _ in range(5):
        x, y = rng.randrange(S), rng.randrange(S)
        for k in range(rng.randint(3, 6)):
            px[(x + k) % S, (y + k // 2) % S] = dark
    out, hi, mid, lo, inner = [hexc(c) for c in iron]
    # iron band, 5px: outline, highlight (top/left) or shadow (bottom/right), mid, low, inner lip
    for y in range(S):
        for x in range(S):
            d = min(x, y, S - 1 - x, S - 1 - y)
            if d >= 5:
                continue
            br = x > S - 1 - y if x + y > S - 1 else False      # bottom-right half for bevel
            side_lo = (S - 1 - x == d) or (S - 1 - y == d)
            col = [out, lo if side_lo else hi, mid, lo, inner][d]
            if d == 1 and side_lo:
                col = lo
            px[x, y] = col
    # rough hammered spots on the band
    for _ in range(40):
        x, y = rng.randrange(S), rng.randrange(S)
        if min(x, y, S - 1 - x, S - 1 - y) == 2 and (M <= x < M + C or M <= y < M + C):
            px[x, y] = lo
    # clipped corners
    for (x, y) in [(0, 0), (S - 1, 0), (0, S - 1), (S - 1, S - 1)]:
        px[x, y] = (0, 0, 0, 0)
    for (x, y) in [(1, 0), (0, 1), (S - 2, 0), (S - 1, 1), (0, S - 2), (1, S - 1), (S - 1, S - 2), (S - 2, S - 1)]:
        px[x, y] = out
    # rivets in each corner
    rh, rm, rl = [hexc(c) for c in rivet]
    for cx, cy in [(2, 2), (S - 4, 2), (2, S - 4), (S - 4, S - 4)]:
        pat = [[out, rm, out], [rm, rh, rl], [out, rl, out]]
        pat = [[rl, rm, rl], [rm, rh, rm], [rl, rl, out]]
        for j in range(3):
            for i in range(3):
                px[cx + i, cy + j] = pat[j][i]
        px[cx, cy] = rh
    return im


def cursor():
    """A small sword pointing right: silver blade, brass guard, leather grip."""
    w, h = 15, 9
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = im.load()
    O = hexc("#0b0809")
    blade_hi, blade, blade_lo = hexc("#f2f0f6"), hexc("#b8b4c4"), hexc("#6c6878")
    g_hi, g, g_lo = hexc("#ffe08a"), hexc("#d0a040"), hexc("#7a5418")
    grip, grip_lo = hexc("#7a4a2a"), hexc("#3e2414")
    # pommel + grip (x 0..3)
    for y in range(3, 6):
        px[0, y] = O
    px[1, 3], px[1, 4], px[1, 5] = g_hi, g, g_lo
    for x in (2, 3):
        px[x, 3], px[x, 4], px[x, 5] = O, grip, grip_lo
        px[x, 3] = grip
    # crossguard (x 4..5, y 0..8)
    for y in range(0, 9):
        px[4, y] = O if y in (0, 8) else g_hi if y < 4 else g
        px[5, y] = O if y in (0, 8) else g if y < 5 else g_lo
    # blade (x 6..13)
    for x in range(6, 14):
        px[x, 2] = O
        px[x, 3] = blade_hi
        px[x, 4] = blade
        px[x, 5] = blade_lo
        px[x, 6] = O
    px[13, 3], px[13, 5] = O, O
    px[14, 4] = O
    px[13, 4] = blade_hi
    # outline left of grip
    for y in (2, 6):
        for x in range(1, 4):
            px[x, y] = O
    return im


def build(out):
    window(("#211719", "#160f11", "#2b1e20"),
           ("#0b0809", "#a8a2ac", "#6e6872", "#3a353c", "#120c0d"),
           ("#ffe8a0", "#c8963c", "#6a4612"), seed=3).save(f"{out}/ui/window.png")
    window(("#121012", "#0a0809", "#1a1618"),
           ("#060505", "#6a6670", "#45414a", "#26232a", "#0a0809"),
           ("#c8c4cc", "#7a7680", "#3a363e"), seed=5, alpha=245).save(f"{out}/ui/window_dark.png")
    window(("#2a0e0e", "#1a0808", "#3a1414"),
           ("#0b0604", "#ffe08a", "#c8963c", "#6a4612", "#140806"),
           ("#ffffff", "#ffd060", "#8a5a10"), seed=7).save(f"{out}/ui/window_gold.png")
    cursor().save(f"{out}/ui/cursor.png")


if __name__ == "__main__":
    build(sys.argv[1])
