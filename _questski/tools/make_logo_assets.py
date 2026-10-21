"""Turn the logo artwork (black background) into the site's logo files.

Usage: python tools/make_logo_assets.py <artwork image>
Writes site/assets/logo-full.webp   full logo, transparent background (home hero)
       site/assets/logo-mark.webp   witch + jetski without the lettering (top bar)
       site/assets/favicon.png      hat + face crop
"""
import os
import sys
from collections import deque

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "site", "assets")
BG_MAX = 26          # a pixel this dark (every channel) that touches the border counts as background
EDGE_MAX = 70        # darker edge pixels next to the background get partial transparency

# crops on the 1254x1254 artwork
MARK_BOX = (150, 0, 1150, 672)
FAVICON_BOX = (405, 15, 725, 335)


def remove_background(im):
    im = im.convert("RGBA")
    w, h = im.size
    px = im.load()
    bg = bytearray(w * h)
    q = deque()
    for x in range(w):
        q.append((x, 0)); q.append((x, h - 1))
    for y in range(h):
        q.append((0, y)); q.append((w - 1, y))
    while q:
        x, y = q.popleft()
        i = y * w + x
        if bg[i]:
            continue
        r, g, b, _ = px[x, y]
        if max(r, g, b) > BG_MAX:
            continue
        bg[i] = 1
        if x > 0: q.append((x - 1, y))
        if x < w - 1: q.append((x + 1, y))
        if y > 0: q.append((x, y - 1))
        if y < h - 1: q.append((x, y + 1))
    for y in range(h):
        for x in range(w):
            i = y * w + x
            if bg[i]:
                px[x, y] = (0, 0, 0, 0)
                continue
            near = (x > 0 and bg[i - 1]) or (x < w - 1 and bg[i + 1]) or (y > 0 and bg[i - w]) or (y < h - 1 and bg[i + w])
            r, g, b, _ = px[x, y]
            m = max(r, g, b)
            if near and m < EDGE_MAX:
                px[x, y] = (r, g, b, int(255 * max(0.35, m / EDGE_MAX)))
    return im


def trim(im, pad=6):
    box = im.getbbox()
    if not box:
        return im
    x0, y0, x1, y1 = box
    return im.crop((max(0, x0 - pad), max(0, y0 - pad), min(im.width, x1 + pad), min(im.height, y1 + pad)))


def main(src):
    art = Image.open(src)
    clean = remove_background(art)
    full = trim(clean)
    full.thumbnail((900, 900), Image.LANCZOS)
    full.save(os.path.join(OUT, "logo-full.webp"), quality=92, method=6)

    mark = trim(clean.crop(MARK_BOX))
    mark.thumbnail((360, 360), Image.LANCZOS)
    mark.save(os.path.join(OUT, "logo-mark.webp"), quality=92, method=6)

    fav = clean.crop(FAVICON_BOX).resize((64, 64), Image.LANCZOS)
    fav.save(os.path.join(OUT, "favicon.png"))
    clean.crop(FAVICON_BOX).resize((180, 180), Image.LANCZOS).save(os.path.join(OUT, "apple-touch-icon.png"))
    print("logo-full", full.size, "logo-mark", mark.size)


if __name__ == "__main__":
    main(sys.argv[1])
