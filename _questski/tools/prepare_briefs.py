"""Turn the cached TibiaWiki pages into one readable "brief" per quest for guide writers.

Coordinates are normalised to absolute Tibia coordinates (x, y, z):
  {{Mapper Coords|130.244|121.61|8|2|text=here}}  ->  [COORD x=33524 y=31037 z=8 | here]
  {{Minimap|x=..|y=..|z=..|mark1=..}}             ->  [MINIMAP x=.. y=.. z=.. marks=(x,y) (x,y)]

Usage: python tools/prepare_briefs.py
Writes tools/briefs/<slug>.md and tools/briefs/_batches.json
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(ROOT, "cache")
OUT = os.path.join(ROOT, "briefs")


def coord(v):
    v = v.strip()
    if not v:
        return None
    if "." in v:
        a, b = v.split(".", 1)
        try:
            return int(a) * 256 + int(float(b))
        except ValueError:
            return None
    try:
        n = int(float(v))
    except ValueError:
        return None
    return n


def split_params(inner):
    parts, depth, cur = [], 0, ""
    for i, ch in enumerate(inner):
        if inner[i:i + 2] in ("{{", "[["):
            depth += 1
        if inner[i:i + 2] in ("}}", "]]"):
            depth -= 1
        if ch == "|" and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    parts.append(cur)
    return parts


def mapper_coords(m):
    params = split_params(m.group(1))
    pos = [p for p in params if "=" not in p]
    named = {k.strip(): v for k, v in (p.split("=", 1) for p in params if "=" in p)}
    if "coords" in named:
        bits = named["coords"].split(",")
        pos = bits + pos
    elif "x" in named and "y" in named:
        pos = [named["x"], named["y"], named.get("z", "7")] + pos
    if len(pos) < 3:
        return m.group(0)
    x, y, z = coord(pos[0]), coord(pos[1]), coord(pos[2])
    text = named.get("text", "").strip()
    return f"[COORD x={x} y={y} z={z} | {text}]"


def minimap(m):
    params = split_params(m.group(1))
    named = {}
    for p in params:
        if "=" in p:
            k, v = p.split("=", 1)
            named[k.strip()] = v.strip()
    x, y, z = coord(named.get("x", "")), coord(named.get("y", "")), named.get("z", "")
    marks = []
    for k, v in named.items():
        if k.startswith("mark") and v:
            bits = v.split(",")
            if len(bits) >= 2:
                mx, my = coord(bits[0]), coord(bits[1])
                if mx and my:
                    marks.append(f"({mx},{my})")
    return f"[MINIMAP x={x} y={y} z={z} marks={' '.join(marks) or 'none'}]"


INVISIBLE = re.compile("[\u200b-\u200f\u202a-\u202e\u2060\ufeff]")
IMG_EXT = r"\.(?:png|gif|jpe?g|webp|bmp)"


def mapper_url(m):
    """[https://tibia.fandom.com/wiki/Mapper?coords=129.174-122.118-7-2-1-1&mark1=... text]"""
    query, text = m.group(1), m.group(2).strip()
    parts = dict(p.split("=", 1) for p in query.split("&") if "=" in p)
    c = parts.get("coords", "").split("-")
    if len(c) < 3:
        return m.group(0)
    x, y, z = coord(c[0]), coord(c[1]), coord(c[2])
    if not (x and y) or z is None:
        return m.group(0)
    out = f"[COORD x={x} y={y} z={z} | {text}]"
    marks = []
    for k, v in parts.items():
        if k.startswith("mark"):
            b = v.split("-")
            if len(b) >= 2 and coord(b[0]) and coord(b[1]):
                mz = coord(b[2]) if len(b) > 2 else z
                marks.append(f"({coord(b[0])},{coord(b[1])},{mz})")
    if marks:
        out += f" [MINIMAP x={x} y={y} z={z} marks={' '.join(marks)}]"
    return out


def list_images(text):
    """Every image file the wiki page shows: [[File:]], <gallery> lines and {{Spoiler Image}}."""
    found = []

    def add(name, caption=""):
        name = INVISIBLE.sub("", name).replace("_", " ").strip()
        if re.search(IMG_EXT + "$", name, re.I) and name.lower() not in [f.lower() for f, _ in found]:
            caption = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", caption or "")
            found.append((name, re.sub(r"<[^>]+>", " ", caption).strip()))

    for m in re.finditer(r"\[\[(?:File|Image):([^|\]]+)((?:\|[^\]\[]*(?:\[\[[^\]]*\]\][^\]\[]*)*)*)\]\]", text, re.I):
        caption = m.group(2).split("|")[-1] if m.group(2) else ""
        if re.match(r"^\s*(thumb|left|right|center|\d+px|frame|none)?\s*$", caption, re.I):
            caption = ""
        add(m.group(1), caption)
    for g in re.finditer(r"<gallery[^>]*>(.*?)</gallery>", text, re.S | re.I):
        for line in g.group(1).splitlines():
            line = line.strip()
            if not line:
                continue
            name, _, caption = line.partition("|")
            add(re.sub(r"^(File|Image):", "", name.strip(), flags=re.I), caption)
    for m in re.finditer(r"\{\{\s*Spoiler Image2?\s*\|(.*?)\}\}", text, re.S | re.I):
        params = split_params(m.group(1))
        files = [p for p in params if "=" not in p and re.search(IMG_EXT, p, re.I)]
        named = [p.split("=", 1)[1] for p in params if re.match(r"\s*(file\d*|image\d*|img\d*\.src)\s*=", p, re.I)]
        rest = [p for p in params if "=" not in p and p not in files]
        for f in files + named:
            add(f, rest[-1] if rest else "")
    return found


def process(text):
    text = INVISIBLE.sub("", text)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    text = re.sub(r"\[https?://[^\s\]]*Mapper\?([^\s\]]+)\s*([^\]]*)\]", mapper_url, text)
    text = re.sub(r"\{\{\s*Mapper[ _]Coords\s*\|([^{}]*)\}\}", mapper_coords, text, flags=re.I)
    text = re.sub(r"\{\{\s*Minimap\s*\|([^{}]*)\}\}", minimap, text, flags=re.I)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def main():
    os.makedirs(OUT, exist_ok=True)
    selected = json.load(open(os.path.join(CACHE, "selected.json"), encoding="utf-8"))
    sizes = []
    for q in selected:
        overview = open(os.path.join(CACHE, "pages", q["slug"] + ".wiki"), encoding="utf-8").read()
        spoiler = ""
        sp_path = os.path.join(CACHE, "spoilers", q["slug"] + ".wiki")
        if os.path.exists(sp_path):
            spoiler = open(sp_path, encoding="utf-8").read()
        title = q["title"]
        url = "https://tibia.fandom.com/wiki/" + title.replace(" ", "_")
        images = list_images(overview + "\n" + spoiler)
        img_list = "\n".join(f"- {f}" + (f"  — {c}" if c else "") for f, c in images) or "(none)"
        brief = (
            f"# BRIEF: {title}\n"
            f"slug: {q['slug']}\n"
            f"wiki: {url}\n"
            f"spoiler: {url}/Spoiler\n\n"
            f"## IMAGES AVAILABLE (use these exact file names in \"images\")\n\n{img_list}\n\n"
            f"## OVERVIEW PAGE (Infobox Quest + notes)\n\n{process(overview)}\n\n"
            f"## SPOILER PAGE (walkthrough source)\n\n{process(spoiler)}\n"
        )
        with open(os.path.join(OUT, q["slug"] + ".md"), "w", encoding="utf-8") as f:
            f.write(brief)
        sizes.append((len(brief), q["slug"]))

    # balance into batches by size (greedy, largest first)
    n_batches = 20
    batches = [{"size": 0, "slugs": []} for _ in range(n_batches)]
    for size, slug in sorted(sizes, reverse=True):
        b = min(batches, key=lambda b: b["size"])
        b["size"] += size
        b["slugs"].append(slug)
    with open(os.path.join(OUT, "_batches.json"), "w", encoding="utf-8") as f:
        json.dump(batches, f, indent=1)
    print(len(sizes), "briefs;", [(b["size"], len(b["slugs"])) for b in batches])


if __name__ == "__main__":
    main()
