"""Build Questski's internal wiki: every item, creature, NPC, spell, place and achievement the guides mention
(plus the NPCs and creatures those pages link to), copied from TibiaWiki with local images and internal links only.

Usage: python tools/build_wiki.py            (fetch what is missing, then process + download images)
       python tools/build_wiki.py --offline  (only re-process the cached pages)
Reads   guides/*.json, tools/cache/selected.json, tools/cache/npcs.json
Writes  tools/cache/wiki_html/*.json   raw parsed pages (cache)
        site/data/wiki/<slug>.json      cleaned pages
        site/data/wiki-index.json       titles, kinds, sprites, aliases
        site/assets/wiki/*              images used by the pages
"""
import glob
import hashlib
import json
import os
import re
import sys
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

from bs4 import BeautifulSoup, NavigableString

from build import WIKI_IMG, download, safe_name
from fetch_wiki import api, category_members
from wiki_extract import build_howto, extract, guide_item_refs, mapper_coord

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "tools", "cache")
RAW = os.path.join(CACHE, "wiki_html")
OUT = os.path.join(ROOT, "site", "data", "wiki")
TOKEN_RE = re.compile(r"\{(npc|item|creature|spell|wiki):([^{}|]+)")
INVISIBLE = re.compile("[​-‏‪-‮⁠﻿]")
IMG_URL_RE = re.compile(r"/tibia/images/[0-9a-f]/[0-9a-f]{2}/([^/?]+)")


def clean_title(t):
    t = INVISIBLE.sub("", urllib.parse.unquote(t)).replace("_", " ").strip()
    return t[:1].upper() + t[1:] if t else t


def page_slug(title):
    base = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:70] or "page"
    return f"{base}-{hashlib.md5(title.encode()).hexdigest()[:5]}"


def raw_path(title):
    return os.path.join(RAW, page_slug(title) + ".json")


# ------------------------------------------------------------------ what the guides reference
def guide_refs():
    refs, backlinks = {}, {}

    def add(name, kind, slug):
        name = clean_title(name)
        if not name:
            return
        refs.setdefault(name, kind)
        backlinks.setdefault(name, set()).add(slug)

    for path in glob.glob(os.path.join(ROOT, "guides", "*.json")):
        slug = os.path.splitext(os.path.basename(path))[0]
        g = json.load(open(path, encoding="utf-8"))
        for kind, val in TOKEN_RE.findall(json.dumps(g, ensure_ascii=False)):
            add(val, kind, slug)
        for it in g.get("items_needed", []) + g.get("rewards", []):
            if it.get("item"):
                add(it["item"], "item", slug)
        for c in g.get("dangers", []):
            add(c, "creature", slug)
        for n in g.get("npcs", []):
            add(n, "npc", slug)
        for a in g.get("achievements", []):
            add(a, "achievement", slug)
        for sec in g.get("sections", []):
            for st in sec.get("steps", []):
                if st.get("npc"):
                    add(st["npc"], "npc", slug)
    return refs, backlinks


# ------------------------------------------------------------------ fetching
def resolve(titles, aliases):
    """Fill aliases {asked title: canonical title or None if missing}."""
    todo = [t for t in titles if t not in aliases]
    for i in range(0, len(todo), 50):
        chunk = todo[i:i + 50]
        data = api({"action": "query", "titles": "|".join(chunk), "redirects": "1"})
        q = data.get("query", {})
        norm = {n["from"]: n["to"] for n in q.get("normalized", [])}
        redir = {r["from"]: r["to"] for r in q.get("redirects", [])}
        exists = {p["title"] for p in q.get("pages", []) if not p.get("missing") and not p.get("invalid")}
        for t in chunk:
            c = norm.get(t, t)
            c = redir.get(c, c)
            aliases[t] = c if c in exists else None
        time.sleep(0.2)


def fetch_page(title):
    path = raw_path(title)
    if os.path.exists(path):
        return True
    for attempt in range(4):
        try:
            d = api({"action": "parse", "page": title, "prop": "text|categories|displaytitle",
                     "disableeditsection": "1", "disablelimitreport": "1", "disabletoc": "1"})
            if "error" in d:
                return False
            p = d["parse"]
            json.dump({"title": p["title"], "html": p["text"], "cats": [c["category"] for c in p.get("categories", [])]},
                      open(path, "w", encoding="utf-8"), ensure_ascii=False)
            return True
        except Exception as e:  # noqa: BLE001
            print("  parse retry", title, e, file=sys.stderr)
            time.sleep(3 + attempt * 3)
    return False


def fetch_all(titles, label):
    titles = sorted(set(titles))
    todo = [t for t in titles if not os.path.exists(raw_path(t))]
    print(f"{label}: {len(titles)} pages, {len(todo)} to download", flush=True)
    done = 0
    with ThreadPoolExecutor(max_workers=3) as pool:
        for _ in pool.map(fetch_page, todo):
            done += 1
            if done % 250 == 0:
                print(f"  {done}/{len(todo)}", flush=True)


def links_in(html):
    return {clean_title(m.split("#")[0]) for m in re.findall(r'href="/wiki/([^"]+)"', html)}


# ------------------------------------------------------------------ processing
KIND_BY_CAT = [
    ("npc", lambda c: c == "NPCs"),
    ("creature", lambda c: c in ("Creatures", "Bosses")),
    ("achievement", lambda c: c == "Achievements"),
    ("spell", lambda c: c.endswith("Spells") or c == "Spells"),
    ("quest", lambda c: c in ("Quest Overview Pages", "Quests")),
    ("local", lambda c: c in ("Cities", "Hunting Places", "Geography", "Islands", "Mountains", "Areas",
                              "Dungeons", "Caves", "Streets", "Districts", "Buildings", "Temples", "Shops",
                              "Locations", "Geography of Tibia", "Towns", "Routes", "Intercity Streets",
                              "NPC Locations")),
    ("item", lambda c: "Items" in c or "Equipment" in c or c in ("Books", "Keys", "Weapons", "Armors", "Runes",
                                                                   "Containers", "Tools", "Food", "Potions",
                                                                   "Decorations", "Furniture", "Plants")),
]


def kind_of(cats, hint):
    cats = [c.replace("_", " ") for c in cats]
    for kind, test in KIND_BY_CAT:
        if any(test(c) for c in cats):
            return kind
    return {"wiki": "outro"}.get(hint, hint or "outro")


NOISE_CLASSES = ("mw-editsection", "navbox", "toc", "noprint", "printfooter", "mw-empty-elt", "references-small")


def image_name(img):
    name = img.get("data-image-name")
    if not name:
        for attr in ("data-src", "src"):
            m = IMG_URL_RE.search(img.get(attr) or "")
            if m:
                name = m.group(1)
                break
    return clean_title(name) if name else None


def original_url(url):
    url = url.replace("&amp;", "&")
    url = re.sub(r"/scale-to-width-down/\d+", "", url)
    url = re.sub(r"/smart/width/\d+/height/\d+", "", url)
    return url


def process(raw, ctx):
    soup = BeautifulSoup(raw["html"], "html.parser")
    for tag in soup(["script", "style", "noscript", "iframe", "video", "audio", "link", "meta"]):
        tag.decompose()
    for cls in NOISE_CLASSES:
        for el in soup.select("." + cls):
            el.decompose()
    for el in soup.select("[data-object-image]"):
        el.decompose()

    images, sprite = {}, None
    for img in soup.find_all("img"):
        name = image_name(img)
        url = img.get("data-src") or img.get("src") or ""
        if not name or "static.wikia.nocookie.net" not in url:
            img.decompose()
            continue
        images.setdefault(name, original_url(url))
        for a in ("srcset", "data-src", "decoding", "data-image-key", "data-relevant", "data-image-name"):
            img.attrs.pop(a, None)
        img["src"] = "assets/wiki/" + safe_name(name)
        img["loading"] = "lazy"
        img["class"] = [c for c in img.get("class", []) if c != "lazyload"]
        if sprite is None and img.find_parent("aside"):
            sprite = name
    if sprite is None and images:
        sprite = next(iter(images))

    for a in soup.find_all("a"):
        href = a.get("href", "")
        target = None
        if "Mapper?" in href:
            c = mapper_coord(href)
            if c:
                label = a.get_text(" ", strip=True)
                a.attrs = {"class": "coord-link", "data-coord": f"{c['x']},{c['y']},{c['z']}", "title": "Ver no mapa"}
                a.string = f"{label} ({c['x']}, {c['y']}, {c['z']})" if label else f"{c['x']}, {c['y']}, {c['z']}"
                continue
        if href.startswith("/wiki/"):
            title = clean_title(href[6:].split("#")[0].split("?")[0])
            if ":" not in title or title.split(":")[0] not in ("Category", "File", "Image", "Special", "Template",
                                                                 "User", "Help", "TibiaWiki", "Talk"):
                target = ctx["route"](title)
        if target:
            a.attrs = {"href": target}
        else:
            a.unwrap()

    for el in soup.find_all(id=True):
        el["id"] = "w-" + el["id"]
    for el in soup.find_all(style=re.compile("display:\\s*none")):
        del el["style"]
    html = str(soup.find("div", class_="mw-parser-output") or soup)
    html = re.sub(r"\n\s*\n+", "\n", html)
    return html, images, sprite


RECORDS_PATH = os.path.join(CACHE, "wiki_records.json")
RECORDS = json.load(open(RECORDS_PATH, encoding="utf-8")) if os.path.exists(RECORDS_PATH) else {}


def cached_record(title, raw=None):
    """Structured data of a page (see wiki_extract.extract), cached by title + html length."""
    if raw is None:
        p = raw_path(title)
        if not os.path.exists(p):
            return None
        try:
            raw = json.load(open(p, encoding="utf-8"))
        except ValueError:
            return None
    key = raw["title"]
    hit = RECORDS.get(key)
    if hit and hit.get("_n") == len(raw["html"]):
        return hit
    rec = extract(raw)
    rec["_n"] = len(raw["html"])
    RECORDS[key] = rec
    return rec


def main():
    offline = "--offline" in sys.argv
    os.makedirs(RAW, exist_ok=True)
    os.makedirs(OUT, exist_ok=True)
    refs, backlinks = guide_refs()
    alias_path = os.path.join(CACHE, "wiki_aliases.json")
    aliases = json.load(open(alias_path, encoding="utf-8")) if os.path.exists(alias_path) else {}
    npcs = json.load(open(os.path.join(CACHE, "npcs.json"), encoding="utf-8"))

    if not offline:
        resolve(list(refs), aliases)
        level1 = {aliases[t] for t in refs if aliases.get(t)}
        fetch_all(level1, "level 1 (referenced by the guides)")
        # level 2: NPCs and creatures linked from those pages, so trade/loot/location links work
        creatures_path = os.path.join(CACHE, "creature_titles.json")
        if not os.path.exists(creatures_path):
            json.dump(category_members("Category:Creatures"), open(creatures_path, "w", encoding="utf-8"))
        creatures = set(json.load(open(creatures_path, encoding="utf-8")))
        linked = set()
        for t in level1:
            p = raw_path(t)
            if os.path.exists(p):
                linked |= links_in(json.load(open(p, encoding="utf-8"))["html"])
        wanted = [t for t in linked if t in npcs or t in creatures]
        resolve(wanted, aliases)
        level2 = {aliases[t] for t in wanted if aliases.get(t)} - level1
        fetch_all(level2, "level 2 (linked NPCs and creatures)")
        json.dump(aliases, open(alias_path, "w", encoding="utf-8"), ensure_ascii=False)
        # level 3: the places where the creatures that drop quest items live (for exact spawn coordinates)
        places = set()
        for t in level1:
            rec = cached_record(t)
            for c in (rec or {}).get("droppedby", []):
                crec = cached_record(aliases.get(c) or c)
                if crec and crec.get("loc"):
                    places.update(crec["loc"]["places"])
        resolve(list(places), aliases)
        level3 = {aliases[t] for t in places if aliases.get(t)} - level1 - level2
        fetch_all(level3, "level 3 (creature spawn places)")
        json.dump(aliases, open(alias_path, "w", encoding="utf-8"), ensure_ascii=False)
        json.dump(RECORDS, open(RECORDS_PATH, "w", encoding="utf-8"), ensure_ascii=False)

    # every cached page is part of the wiki
    pages = {}
    for path in glob.glob(os.path.join(RAW, "*.json")):
        try:
            raw = json.load(open(path, encoding="utf-8"))
        except ValueError:  # half-written by a fetch still running
            continue
        pages[raw["title"]] = raw
    canon_lower = {t.lower(): t for t in pages}
    alias_lower = dict(canon_lower)
    for a, c in aliases.items():
        if c in pages:
            alias_lower.setdefault(a.lower(), c)

    selected = json.load(open(os.path.join(CACHE, "selected.json"), encoding="utf-8"))
    quests = {q["title"].lower(): q["slug"] for q in selected}
    for q in selected:
        name = (q["fields"].get("name") or "").strip()
        if name:
            quests.setdefault(name.lower(), q["slug"])

    def route(title):
        low = title.lower()
        canon = alias_lower.get(low)
        if low in quests:
            return "#/quest/" + quests[low]
        if canon and canon.lower() in quests:
            return "#/quest/" + quests[canon.lower()]
        if canon:
            return "#/wiki/" + urllib.parse.quote(canon, safe="")
        return None

    backlinks_canon = {}
    for name, slugs in backlinks.items():
        c = aliases.get(name) or canon_lower.get(name.lower())
        if c:
            backlinks_canon.setdefault(c, set()).update(slugs)

    hint_by_canon = {}
    for a, c in aliases.items():
        if c and a in refs:
            hint_by_canon.setdefault(c, refs[a])

    def canon_of(name):
        return alias_lower.get(clean_title(name).lower())

    # structured data for items, creatures and places (NPC positions come from npcs.json)
    records = {}
    for title, raw in pages.items():
        if title not in npcs:
            records[title] = cached_record(title, raw)
    json.dump(RECORDS, open(RECORDS_PATH, "w", encoding="utf-8"), ensure_ascii=False)
    quest_refs = guide_item_refs(canon_of)
    print(f"structured records: {len(records)}; items used in guides: {len(quest_refs)}", flush=True)

    index, all_images = [], {}
    for title, raw in sorted(pages.items()):
        html, images, sprite = process(raw, {"route": route})
        all_images.update(images)
        hint = refs.get(title) or hint_by_canon.get(title)
        kind = kind_of(raw["cats"], hint or ("npc" if title in npcs else None))
        slug = page_slug(title)
        entry = {"t": title, "s": slug, "k": kind}
        if sprite:
            entry["i"] = "assets/wiki/" + safe_name(sprite)
        if backlinks_canon.get(title):
            entry["q"] = len(backlinks_canon[title])
        index.append(entry)
        page = dict(entry, html=html, quests=sorted(backlinks_canon.get(title, [])))
        if title in npcs and "x" in npcs[title]:
            n = npcs[title]
            page["pos"] = {"x": n["x"], "y": n["y"], "z": n["z"]}
        rec = records.get(title)
        if rec and (kind == "item" or rec["droppedby"] or rec["buy"] or rec["sell"] or quest_refs.get(title)):
            howto = build_howto(title, rec, records, npcs, quest_refs, canon_of)
            if howto:
                page["howto"] = howto
                for d in howto.get("drops", []):
                    c = canon_of(d["creature"])
                    if c and c in pages:
                        d["href"] = route(c)
                for kind_key in ("buy", "sell"):
                    for r in howto.get(kind_key, []):
                        c = canon_of(r["npc"])
                        if c and c in pages:
                            r["href"] = route(c)
                for d in howto.get("drops", []):
                    for p in d.get("places", []):
                        c = canon_of(p["name"])
                        if c and c in pages:
                            p["href"] = route(c)
        json.dump(page, open(os.path.join(OUT, slug + ".json"), "w", encoding="utf-8"), ensure_ascii=False,
                  separators=(",", ":"))

    alias_out = {a.lower(): c for a, c in aliases.items() if c in pages and a.lower() != c.lower()}
    json.dump({"pages": index, "alias": alias_out}, open(os.path.join(ROOT, "site", "data", "wiki-index.json"),
                                                         "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    kinds = {}
    for e in index:
        kinds[e["k"]] = kinds.get(e["k"], 0) + 1
    print(f"wiki: {len(index)} pages {kinds}; {len(all_images)} images referenced", flush=True)

    jobs = [(url, os.path.join(WIKI_IMG, safe_name(name))) for name, url in all_images.items()
            if not os.path.exists(os.path.join(WIKI_IMG, safe_name(name)))]
    print(f"downloading {len(jobs)} new images...", flush=True)
    ok = 0
    with ThreadPoolExecutor(max_workers=8) as pool:
        for i, good in enumerate(pool.map(lambda j: download(*j), jobs), 1):
            ok += bool(good)
            if i % 500 == 0:
                print(f"  {i}/{len(jobs)}", flush=True)
    print(f"images downloaded: {ok}/{len(jobs)}", flush=True)


if __name__ == "__main__":
    main()
