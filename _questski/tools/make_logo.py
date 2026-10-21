"""Draw the provisional Tibia Questski logo: a pixel-art sorcerer riding a jetski.

Usage: python tools/make_logo.py [preview.png]
Writes site/assets/logo.svg, site/assets/logo-64.png, site/assets/favicon.png
"""
import os
import sys

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "site", "assets")
W, H = 64, 52

C = {
    "outline": (26, 18, 10),
    "robe": (44, 79, 163), "robe_d": (29, 51, 110), "robe_l": (86, 124, 214),
    "hat": (59, 42, 122), "hat_d": (38, 26, 84), "hat_l": (92, 70, 168),
    "gold": (242, 193, 78), "gold_d": (184, 134, 43),
    "skin": (240, 192, 138), "skin_d": (201, 143, 90),
    "beard": (244, 241, 232), "beard_d": (196, 190, 178),
    "eye": (26, 18, 10),
    "hull": (242, 239, 230), "hull_d": (185, 181, 171),
    "red": (200, 50, 42), "red_d": (142, 31, 26),
    "seat": (52, 44, 40), "seat_l": (84, 72, 64),
    "metal": (120, 120, 128), "glass": (127, 223, 255),
    "wand": (122, 74, 34), "wand_l": (168, 110, 58),
    "glow": (127, 243, 255), "glow_d": (47, 184, 214), "white": (255, 255, 255),
    "water": (42, 127, 201), "water_d": (27, 90, 152), "water_l": (88, 170, 230),
    "foam": (233, 247, 255),
}


NO_OUTLINE = {C["foam"], C["water"], C["water_d"], C["water_l"]}


def main():
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    P = lambda pts, c: d.polygon(pts, fill=C[c])  # noqa: E731
    R = lambda x0, y0, x1, y1, c: d.rectangle((x0, y0, x1, y1), fill=C[c])  # noqa: E731
    L = lambda pts, c, w=1: d.line(pts, fill=C[c], width=w)  # noqa: E731
    px = lambda x, y, c: d.point((x, y), fill=C[c])  # noqa: E731

    # --- water and wake ---
    P([(2, 42), (62, 41), (62, 49), (2, 49)], "water")
    P([(2, 46), (62, 45), (62, 49), (2, 49)], "water_d")
    for x in range(4, 60, 7):
        L([(x, 43), (x + 3, 43)], "water_l")
    for x in range(7, 60, 9):
        L([(x, 47), (x + 2, 47)], "water_l")
    # spray behind the jetski
    P([(2, 41), (8, 36), (14, 38), (18, 42), (10, 44)], "foam")
    for (x, y) in [(3, 34), (6, 32), (9, 33), (4, 38), (11, 35), (1, 37), (13, 33)]:
        R(x, y, x + 1, y + 1, "foam")
    P([(44, 42), (58, 40), (61, 42), (52, 44)], "foam")

    # --- jetski hull ---
    P([(12, 34), (52, 34), (59, 30), (57, 37), (50, 41), (17, 41), (12, 38)], "hull")
    P([(12, 38), (57, 37), (50, 41), (17, 41)], "hull_d")
    L([(13, 36), (56, 35)], "red", 2)
    L([(16, 40), (50, 40)], "red_d")
    L([(52, 34), (59, 30)], "red")
    # seat
    R(18, 31, 36, 33, "seat")
    L([(19, 31), (35, 31)], "seat_l")
    # windshield + steering column
    P([(46, 33), (49, 27), (52, 27), (51, 33)], "glass")
    L([(43, 33), (44, 25)], "metal", 2)
    L([(40, 24), (47, 23)], "metal", 2)

    # --- sorcerer ---
    # flowing cape behind
    P([(27, 19), (12, 25), (8, 29), (16, 28), (20, 31), (26, 30)], "robe_d")
    # body
    P([(27, 19), (36, 19), (39, 31), (23, 31)], "robe")
    P([(27, 19), (30, 19), (27, 31), (23, 31)], "robe_d")
    L([(35, 20), (38, 30)], "robe_l")
    # belt
    L([(25, 26), (37, 26)], "gold_d")
    px(31, 26, "gold")
    # front arm to handlebar
    L([(34, 21), (41, 24)], "robe", 3)
    L([(35, 20), (41, 23)], "robe_l")
    R(41, 23, 43, 25, "skin")
    # leg on the seat
    P([(30, 29), (40, 29), (41, 33), (31, 33)], "robe_d")
    R(40, 31, 43, 33, "seat")

    # raised back arm with wand
    L([(28, 21), (21, 15)], "robe", 3)
    L([(28, 20), (22, 14)], "robe_l")
    R(19, 13, 21, 15, "skin")
    L([(20, 14), (15, 4)], "wand", 2)
    L([(21, 13), (16, 4)], "wand_l")
    # glowing tip + sparkles
    R(13, 1, 16, 4, "glow")
    R(14, 2, 15, 3, "white")
    for (x, y) in [(11, 2), (18, 2), (14, 0), (12, 6), (17, 6)]:
        px(x, y, "glow_d")
    L([(9, 2), (10, 2)], "glow")
    L([(19, 1), (20, 0)], "glow")

    # head
    R(29, 13, 35, 18, "skin")
    L([(29, 18), (29, 14)], "skin_d")
    px(31, 15, "eye")
    px(34, 15, "eye")
    # beard
    P([(28, 17), (36, 17), (35, 21), (32, 25), (29, 21)], "beard")
    L([(29, 20), (32, 24)], "beard_d")
    # hat: brim + cone blown backwards
    L([(25, 12), (39, 12)], "hat_d", 2)
    P([(27, 11), (37, 11), (31, 4), (22, 1), (26, 6)], "hat")
    P([(27, 11), (30, 11), (26, 6), (22, 1)], "hat_d")
    L([(33, 10), (31, 5)], "hat_l")
    L([(27, 10), (37, 10)], "gold")
    px(32, 7, "gold")
    px(31, 8, "gold_d")
    px(33, 8, "gold_d")

    # --- auto outline ---
    src = im.copy()
    sp = src.load()
    op = im.load()
    for y in range(H):
        for x in range(W):
            if sp[x, y][3] == 0:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < W and 0 <= ny < H and sp[nx, ny][3] and sp[nx, ny][:3] not in NO_OUTLINE:
                        op[x, y] = C["outline"] + (255,)
                        break

    os.makedirs(OUT, exist_ok=True)
    im.save(os.path.join(OUT, "logo-64.png"))
    im.resize((W * 8, H * 8), Image.NEAREST).save(os.path.join(OUT, "logo-512.png"))
    fav = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    fav.paste(im, (0, 6))
    fav.save(os.path.join(OUT, "favicon.png"))
    write_svg(im)
    if len(sys.argv) > 1:
        im.resize((W * 8, H * 8), Image.NEAREST).save(sys.argv[1])


def write_svg(im):
    p = im.load()
    rects = []
    for y in range(H):
        x = 0
        while x < W:
            c = p[x, y]
            if c[3] == 0:
                x += 1
                continue
            start = x
            while x < W and p[x, y] == c:
                x += 1
            rects.append(f'<rect x="{start}" y="{y}" width="{x - start}" height="1" fill="#{c[0]:02x}{c[1]:02x}{c[2]:02x}"/>')
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" shape-rendering="crispEdges">'
           f'<title>Tibia Questski</title>{"".join(rects)}</svg>')
    with open(os.path.join(OUT, "logo.svg"), "w", encoding="utf-8") as f:
        f.write(svg)


if __name__ == "__main__":
    main()
