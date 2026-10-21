"""Build the site data from TibiaWiki metadata + the hand-written guides.

Usage: python tools/build.py [--no-images]
Reads   tools/cache/selected.json, tools/cache/npcs.json, guides/*.json
Writes  site/data/index.json, site/data/quests/<slug>.json, site/data/npcs.json,
        site/data/images.json and downloads every referenced wiki image into site/assets/wiki/
"""
import glob
import hashlib
import html
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

from fetch_wiki import api

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")
CACHE = os.path.join(TOOLS, "cache")
SITE = os.path.join(os.path.dirname(ROOT), "quests")
DATA = os.path.join(SITE, "data")
WIKI_IMG = os.path.join(SITE, "assets", "wiki")
TOKEN_RE = re.compile(r"\{(npc|item|creature|spell|wiki|key|coord):([^{}]+)\}")


# ---------- wiki markup -> plain text (for infobox fields) ----------

def plain(v):
    if not v:
        return ""
    v = re.sub(r"<br\s*/?>", ", ", v, flags=re.I)
    v = re.sub(r"\[\[(?:File|Image):[^\]]*\]\]", "", v, flags=re.I)
    v = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", v)
    v = re.sub(r"\[https?://\S+\s+([^\]]+)\]", r"\1", v)
    for _ in range(3):
        v = re.sub(r"\{\{[^{}]*\}\}", "", v)
    v = re.sub(r"<[^>]+>", "", v)
    v = html.unescape(v.replace("'''", "").replace("''", ""))
    v = re.sub(r"\s*,\s*,", ",", v)
    v = re.sub(r"\s+", " ", v).strip(" ,")
    return v


def yesno(v):
    v = (v or "").strip().lower()
    if v.startswith("yes"):
        return True
    if v.startswith("no"):
        return False
    return None


# ---------- images ----------

def safe_name(name):
    base, ext = os.path.splitext(name)
    slug = re.sub(r"[^A-Za-z0-9]+", "_", base).strip("_")[:60] or "img"
    h = hashlib.md5(name.lower().encode()).hexdigest()[:6]
    return f"{slug}_{h}{ext.lower() or '.png'}"


INVISIBLE = re.compile("[​-‏‪-‮⁠﻿]")


def norm(name):
    return INVISIBLE.sub("", name).replace("_", " ").strip().lower()


def resolve_images(names):
    """Return {norm(name): {url,w,h} | None} using the MediaWiki imageinfo API (cached)."""
    cache_path = os.path.join(CACHE, "imageinfo.json")
    cache = json.load(open(cache_path, encoding="utf-8")) if os.path.exists(cache_path) else {}
    todo = sorted({n for n in names if norm(n) not in cache})
    for i in range(0, len(todo), 50):
        chunk = todo[i:i + 50]
        data = api({"action": "query", "prop": "imageinfo", "iiprop": "url|size",
                    "titles": "|".join("File:" + n for n in chunk)})
        q = data.get("query", {})
        back = {}
        for n in q.get("normalized", []):
            back[n["to"]] = n["from"]
        for p in q.get("pages", []):
            title = p["title"]
            orig = back.get(title, title)[5:]
            info = (p.get("imageinfo") or [None])[0]
            entry = {"url": info["url"], "w": info.get("width"), "h": info.get("height")} if info else None
            cache[norm(orig)] = entry
            cache[norm(title[5:])] = entry
        for n in chunk:
            cache.setdefault(norm(n), None)
        time.sleep(0.3)
        print(f"  resolved {min(i + 50, len(todo))}/{len(todo)} images", flush=True)
    json.dump(cache, open(cache_path, "w", encoding="utf-8"), indent=0)
    return cache


BROWSER_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"


def download(url, dest):
    """The wiki image CDN only answers with a wiki referer, and stalls Python's TLS client: use curl."""
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return True
    for attempt in range(3):
        r = subprocess.run(["curl", "-s", "-f", "-L", "--max-time", "60", "-A", BROWSER_UA,
                            "-e", "https://tibia.fandom.com/", "-o", dest, url])
        if r.returncode == 0 and os.path.exists(dest) and os.path.getsize(dest) > 0:
            return True
        print("   download retry", attempt, url, file=sys.stderr)
        time.sleep(2)
    if os.path.exists(dest):
        os.remove(dest)
    return False


# ---------- guides ----------

def walk_strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, list):
        for v in obj:
            yield from walk_strings(v)
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from walk_strings(v)


def collect_refs(g):
    """Entity names (for sprites) and screenshot files used by a guide."""
    sprites, files, npcs = set(), set(), set()
    for s in walk_strings(g):
        for kind, val in TOKEN_RE.findall(s):
            name = val.split("|")[0].strip()
            if kind in ("item", "creature", "npc", "spell"):
                sprites.add(name)
            if kind == "npc":
                npcs.add(name)
    for k in ("items_needed", "rewards"):
        for it in g.get(k, []):
            if isinstance(it, dict) and it.get("item"):
                sprites.add(it["item"])
    for n in g.get("dangers", []) + g.get("npcs", []):
        sprites.add(n)
    npcs.update(g.get("npcs", []))
    for sec in g.get("sections", []):
        for st in sec.get("steps", []):
            if st.get("npc"):
                sprites.add(st["npc"])
                npcs.add(st["npc"])
            for im in st.get("images", []):
                files.add(INVISIBLE.sub("", im["file"]).replace("_", " ").strip())
    return sprites, files, npcs


def main():
    with_images = "--no-images" not in sys.argv
    selected = json.load(open(os.path.join(CACHE, "selected.json"), encoding="utf-8"))
    all_npcs = json.load(open(os.path.join(CACHE, "npcs.json"), encoding="utf-8"))
    os.makedirs(os.path.join(DATA, "quests"), exist_ok=True)
    os.makedirs(WIKI_IMG, exist_ok=True)

    guides = {}
    for path in glob.glob(os.path.join(ROOT, "guides", "*.json")):
        slug = os.path.splitext(os.path.basename(path))[0]
        try:
            guides[slug] = json.load(open(path, encoding="utf-8"))
        except Exception as e:  # noqa: BLE001
            print("skip broken guide", slug, e)

    all_sprites, all_files, used_npcs = set(), set(), set()
    centres = city_centres(all_npcs)
    quests = []
    for q in selected:
        f = q["fields"]
        wiki = "https://tibia.fandom.com/wiki/" + urllib.parse.quote(q["title"].replace(" ", "_"))
        meta = {
            "slug": q["slug"],
            "name": plain(f.get("name")) or q["title"],
            "aka": [a.strip() for a in re.split(r",| or ", plain(f.get("aka"))) if a.strip()],
            "lvl": q["lvl"] or 0,
            "lvl_note": plain(f.get("lvl")),
            "rec": q["lvlrec"],
            "rec_raw": plain(f.get("lvlrec")),
            "premium": yesno(f.get("premium")),
            "implemented": plain(f.get("implemented")),
            "location": plain(f.get("location")),
            "reward_raw": plain(f.get("reward")),
            "dangers_raw": plain(f.get("dangers")),
            "legend": plain(f.get("legend")),
            "log": yesno(f.get("log")),
            "rookgaard": yesno(f.get("rookgaardquest")),
            "wiki_type": plain(f.get("type")).lower(),
            "wiki": wiki,
            "spoiler": wiki + "/Spoiler",
        }
        g = guides.get(q["slug"])
        if g:
            sprites, files, npcs = collect_refs(g)
            all_sprites |= sprites
            all_files |= files
            used_npcs |= npcs
            full = dict(meta, **{k: v for k, v in g.items() if k != "slug"}, has_guide=True)
        else:
            full = dict(meta, has_guide=False, category=fallback_category(meta), region="Vários",
                        summary="", sections=[])
        with open(os.path.join(DATA, "quests", q["slug"] + ".json"), "w", encoding="utf-8") as fh:
            json.dump(full, fh, ensure_ascii=False, separators=(",", ":"))
        steps = sum(len(s.get("steps", [])) for s in full.get("sections", []))
        quests.append({
            "slug": meta["slug"], "name": meta["name"], "aka": meta["aka"],
            "lvl": meta["lvl"], "rec": meta["rec"], "rec_raw": meta["rec_raw"],
            "premium": meta["premium"], "category": full.get("category"),
            "region": full.get("region"), "difficulty": full.get("difficulty"),
            "duration": full.get("duration"), "summary": full.get("summary", ""),
            "location": meta["location"], "start": full.get("start"),
            "rewards": [r.get("item") or r.get("text") for r in full.get("rewards", [])] or
                       ([meta["reward_raw"]] if meta["reward_raw"] else []),
            "npcs": full.get("npcs", []), "steps": steps, "has_guide": bool(g),
            "pin": quest_pin(full, all_npcs),
            "regions": quest_regions(full, all_npcs, centres),
            "unlocks": full.get("unlocks", []),
        })

    quests.sort(key=lambda x: (x["rec"] or x["lvl"] or 1, x["lvl"], x["name"]))
    regions = []
    for city in REGION_CITIES:
        total = sum(city in q["regions"] for q in quests)
        if total and city in centres:
            regions.append({"name": city, "x": centres[city][0], "y": centres[city][1],
                            "main": sum(q["region"] == city for q in quests), "total": total})
    regions.sort(key=lambda r: -r["total"])
    index = {"generated": time.strftime("%Y-%m-%d %H:%M"), "count": len(quests),
             "guides": sum(q["has_guide"] for q in quests), "regions": regions, "quests": quests}
    with open(os.path.join(DATA, "index.json"), "w", encoding="utf-8") as fh:
        json.dump(index, fh, ensure_ascii=False, separators=(",", ":"))

    build_places(all_sprites, all_files, used_npcs)

    npcs_out = {n: all_npcs[n] for n in sorted(used_npcs) if n in all_npcs}
    with open(os.path.join(DATA, "npcs.json"), "w", encoding="utf-8") as fh:
        json.dump(npcs_out, fh, ensure_ascii=False, separators=(",", ":"))
    print(f"{len(quests)} quests, {index['guides']} with guides, {len(npcs_out)} NPCs")

    if with_images:
        build_images(all_sprites, all_files)


def build_places(all_sprites, all_files, used_npcs):
    """places/<slug>.json travel cards -> site/data/places.json {places: {title: card}, alias: {lower name: title}}."""
    places = {}
    for path in sorted(glob.glob(os.path.join(ROOT, "places", "*.json"))):
        try:
            p = json.load(open(path, encoding="utf-8"))
        except Exception as e:  # noqa: BLE001
            print("skip broken place", path, e)
            continue
        places[p["title"]] = p
        for s in walk_strings(p):
            for kind, val in TOKEN_RE.findall(s):
                name = val.split("|")[0].strip()
                if kind in ("item", "creature", "npc", "spell"):
                    all_sprites.add(name)
                if kind == "npc":
                    used_npcs.add(name)
        for it in p.get("items", []):
            all_sprites.add(it)
        for im in p.get("images", []):
            all_files.add(INVISIBLE.sub("", im["file"]).replace("_", " ").strip())
    alias = {}
    alias_path = os.path.join(CACHE, "wiki_aliases.json")
    if os.path.exists(alias_path):
        for a, c in json.load(open(alias_path, encoding="utf-8")).items():
            if c in places and a.lower() != c.lower():
                alias[a.lower()] = c
    with open(os.path.join(DATA, "places.json"), "w", encoding="utf-8") as fh:
        json.dump({"places": places, "alias": alias}, fh, ensure_ascii=False, separators=(",", ":"))
    print(f"{len(places)} place travel cards")


def build_images(sprites, files):
    names = {s + ".gif" for s in sprites} | set(files)
    print(f"resolving {len(names)} images...")
    info = resolve_images(names)
    manifest, missing = {}, 0
    jobs = []
    for n in sorted(names):
        e = info.get(norm(n))
        if not e:
            missing += 1
            continue
        jobs.append((n, e, safe_name(n)))

    def fetch(job):
        n, e, local = job
        return job, download(e["url"], os.path.join(WIKI_IMG, local))

    with ThreadPoolExecutor(max_workers=8) as pool:
        for i, ((n, e, local), good) in enumerate(pool.map(fetch, jobs), 1):
            if good:
                manifest[norm(n)] = {"src": "assets/wiki/" + local, "w": e["w"], "h": e["h"]}
            if i % 200 == 0:
                print(f"  downloaded {i}/{len(jobs)}", flush=True)
    ok = len(manifest)
    with open(os.path.join(DATA, "images.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, separators=(",", ":"))
    print(f"images: {ok} downloaded/cached, {missing} not on the wiki")


REGION_CITIES = ["Rookgaard", "Dawnport", "Thais", "Carlin", "Ab'Dendriel", "Kazordoon", "Venore", "Edron", "Darashia",
                 "Ankrahmun", "Port Hope", "Liberty Bay", "Svargrond", "Yalahar", "Farmine", "Gray Beach", "Rathleton",
                 "Roshamuul", "Krailos", "Issavi", "Feyrist", "Marapur"]
TRANSIT = re.compile(r"barco|captain|capit|tapete|carpet|navio|ferry|steamship|porto\b|boat|ship", re.I)
# island / far-away regions: a point belongs to them only within this many tiles of the city
REGION_RADIUS = {"Rookgaard": 150, "Dawnport": 80, "Feyrist": 140, "Marapur": 170, "Gray Beach": 180, "Krailos": 210,
                 "Roshamuul": 180, "Issavi": 240, "Rathleton": 230, "Yalahar": 260, "Farmine": 330, "Svargrond": 330}


def city_centres(npcs):
    """Median position of each city's NPCs = where the city is."""
    pts = {}
    for n in npcs.values():
        if n.get("city") in REGION_CITIES and "x" in n and n["z"] in (5, 6, 7, 8):
            pts.setdefault(n["city"], []).append((n["x"], n["y"]))
    out = {}
    for city, ps in pts.items():
        xs, ys = sorted(p[0] for p in ps), sorted(p[1] for p in ps)
        out[city] = (xs[len(xs) // 2], ys[len(ys) // 2])
    return out


def quest_regions(g, npcs, centres):
    """Cities a quest happens in: its main region + the nearest city of every place the steps send you to
    (boat/carpet stops are only transit and do not count)."""
    hits = {}

    def near(x, y):
        best, best_d = None, None
        for city, (cx, cy) in centres.items():
            d = ((cx - x) ** 2 + (cy - y) ** 2) ** 0.5
            if d > REGION_RADIUS.get(city, 1e9):
                continue  # island regions only own what is actually on (or under) them
            if best_d is None or d < best_d:
                best, best_d = city, d
        return best

    def add(c, label=""):
        if not c or not isinstance(c.get("x"), int) or TRANSIT.search(label or c.get("label") or ""):
            return
        city = near(c["x"], c["y"])
        if city:
            hits[city] = hits.get(city, 0) + 1

    add(g.get("start") or {})
    for sec in g.get("sections", []):
        for st in sec.get("steps", []):
            for c in st.get("coords", []):
                add(c)
            if st.get("map"):
                for m in st["map"].get("marks", []) or [st["map"]]:
                    add(m)
            n = npcs.get(st.get("npc") or "")
            if n and "x" in n and not TRANSIT.search(n.get("job") or ""):
                add(n, st["npc"] if TRANSIT.search(st["npc"]) else "")
    main = g.get("region")
    regions = [main] if main in REGION_CITIES else []
    total = sum(hits.values())
    for city, n in sorted(hits.items(), key=lambda kv: -kv[1]):
        # a city counts when the quest really does something there, not for a single stray point
        if city not in regions and (n >= 2 or total <= 3 or n / total >= 0.2):
            regions.append(city)
    return regions


def quest_pin(q, npcs):
    """Where to put the quest on the overview map: start, else first step coordinate, else first NPC."""
    if q.get("start"):
        return q["start"]
    for sec in q.get("sections", []):
        for st in sec.get("steps", []):
            for c in st.get("coords", []):
                return c
            if st.get("map"):
                return {k: st["map"][k] for k in ("x", "y", "z")}
            n = npcs.get(st.get("npc") or "")
            if n and "x" in n:
                return {"x": n["x"], "y": n["y"], "z": n["z"], "label": st["npc"]}
    for name in q.get("npcs", []):
        n = npcs.get(name)
        if n and "x" in n:
            return {"x": n["x"], "y": n["y"], "z": n["z"], "label": name}
    return None


def fallback_category(meta):
    t = meta["wiki_type"]
    if "outfit" in t or "addon" in t:
        return "outfit"
    if "mwc" in t or "change" in t:
        return "world-change"
    if "event" in t:
        return "evento"
    if "exchange" in t:
        return "troca"
    if "task" in t:
        return "tarefas"
    return "tesouro"


if __name__ == "__main__":
    main()
