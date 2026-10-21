"""Read a TibiaWiki page (from the local wiki cache, fetching it if needed) as plain text with coordinates.
Meant for guide writers checking how to reach / leave a place (Hellgate, Formorgar Mines, ...).

Usage: python tools/place.py "Hellgate"                 full page text, map links shown as [COORD x=.. y=.. z=..]
       python tools/place.py --find hellgate             list cached page titles containing the words
       python tools/place.py --routes [words]            list TibiaWiki "Route:" pages (step-by-step ways in/out)
       python tools/place.py "Hellgate" --max 6000        cap the printed text (default 9000 characters)
"""
import hashlib
import json
import os
import re
import sys
import urllib.parse

from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(ROOT, "cache", "wiki_html")
ALIASES = os.path.join(ROOT, "cache", "wiki_aliases.json")


def page_slug(title):
    base = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:70] or "page"
    return f"{base}-{hashlib.md5(title.encode()).hexdigest()[:5]}"


def load(title):
    aliases = json.load(open(ALIASES, encoding="utf-8")) if os.path.exists(ALIASES) else {}
    cands = [title, title[:1].upper() + title[1:], aliases.get(title)]
    for t in filter(None, cands):
        p = os.path.join(RAW, page_slug(t) + ".json")
        if os.path.exists(p):
            return json.load(open(p, encoding="utf-8"))
    # not cached: ask the wiki (following redirects) and keep it for the site's wiki too
    from fetch_wiki import api
    d = api({"action": "parse", "page": title, "redirects": "1", "prop": "text|categories",
             "disableeditsection": "1", "disablelimitreport": "1", "disabletoc": "1"})
    if "error" in d:
        return None
    raw = {"title": d["parse"]["title"], "html": d["parse"]["text"], "cats": [c["category"] for c in d["parse"].get("categories", [])]}
    json.dump(raw, open(os.path.join(RAW, page_slug(raw["title"]) + ".json"), "w", encoding="utf-8"), ensure_ascii=False)
    return raw


def coord(v):
    if "." in v:
        a, b = v.split(".", 1)
        return int(a) * 256 + int(float(b))
    return int(float(v))


def to_text(html):
    soup = BeautifulSoup(html, "html.parser")
    for t in soup(["script", "style", "table"]):
        if t.name == "table" and len(t.get_text()) < 3000:
            t.replace_with(" | ".join(r.get_text(" ", strip=True) for r in t.find_all("tr")) + "\n")
        else:
            t.decompose()
    for a in soup.find_all("a", href=re.compile(r"Mapper\?")):
        m = re.search(r"coords=([0-9.]+)-([0-9.]+)-(\d+)", a["href"].replace("&amp;", "&"))
        if m:
            a.replace_with(f"{a.get_text(strip=True)} [COORD x={coord(m.group(1))} y={coord(m.group(2))} z={m.group(3)}]")
    for h in soup.find_all(["h2", "h3", "h4"]):
        h.insert_before("\n## ")
        h.insert_after("\n")
    for li in soup.find_all("li"):
        li.insert_before("\n- ")
    text = soup.get_text(" ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n", text)
    return text.strip()


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return
    if args[0] == "--routes":
        path = os.path.join(ROOT, "cache", "route_pages.json")
        if not os.path.exists(path):
            print('Route list not downloaded yet. Try the page directly, e.g. python tools/place.py "Route:Hellgate"')
            return
        routes = json.load(open(path, encoding="utf-8"))
        words = [w.lower() for w in args[1:]]
        for r in routes:
            if all(w in r.lower() for w in words):
                print(r)
        return
    if args[0] == "--find":
        words = [w.lower() for w in args[1:]]
        for fn in sorted(os.listdir(RAW)):
            try:
                t = json.load(open(os.path.join(RAW, fn), encoding="utf-8"))["title"]
            except ValueError:
                continue
            if all(w in t.lower() for w in words):
                print(t)
        return
    limit = 9000
    if "--max" in args:
        limit = int(args[args.index("--max") + 1])
        args = args[:args.index("--max")]
    raw = load(urllib.parse.unquote(" ".join(args)).replace("_", " "))
    if not raw:
        print("page not found on TibiaWiki")
        return
    text = to_text(raw["html"])
    images = page_images(raw["html"])
    remember_images(raw["title"], images)
    print(f"# {raw['title']}\n")
    print(text[:limit] + ("\n[... truncated, use --max to see more]" if len(text) > limit else ""))
    if images:
        print("\n## IMAGES ON THIS PAGE (may be attached to guide steps with these exact names)")
        for name, cap in images:
            print(f"- {name}" + (f"  — {cap}" if cap else ""))


SPRITE_HINT = re.compile(r"\.gif$", re.I)


def page_images(html):
    """Screenshots/maps on the page (sprites and icons skipped), with their captions."""
    soup = BeautifulSoup(html, "html.parser")
    out = []
    for img in soup.find_all("img"):
        name = img.get("data-image-name")
        if not name:
            continue
        w = int(img.get("width") or 0)
        if (w and w <= 64) or (SPRITE_HINT.search(name) and w <= 96):
            continue
        fig = img.find_parent(["figure", "div"], class_=re.compile("thumb|gallerybox|pi-image"))
        cap = ""
        if fig:
            c = fig.find(["figcaption", "div"], class_=re.compile("caption|gallerytext|thumbcaption"))
            cap = c.get_text(" ", strip=True)[:160] if c else ""
        if name not in [n for n, _ in out]:
            out.append((name, cap))
    return out


def remember_images(title, images):
    """One small file per page (several guide writers run in parallel), merged by validate.py."""
    folder = os.path.join(ROOT, "cache", "extra_images")
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, page_slug(title) + ".json")
    tmp = f"{path}.{os.getpid()}.tmp"
    json.dump({title: [n for n, _ in images]}, open(tmp, "w", encoding="utf-8"), ensure_ascii=False)
    os.replace(tmp, path)


if __name__ == "__main__":
    main()
