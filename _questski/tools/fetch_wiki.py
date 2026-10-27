"""Fetch TibiaWiki quest overview pages + their /Spoiler subpages into tools/cache/.

Usage: python tools/fetch_wiki.py
Produces:
  tools/cache/pages/<slug>.wiki          raw wikitext of each quest overview page
  tools/cache/spoilers/<slug>.wiki       raw wikitext of "<quest>/Spoiler" (when it exists)
  tools/cache/index.json                 parsed Infobox Quest fields for every quest
  tools/cache/selected.json              quests in scope (every quest not deprecated, any level)
"""
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://tibia.fandom.com/api.php"
UA = "TibiaQuestski/0.1 (personal localhost quest guide)"
ROOT = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(ROOT, "cache")
PAGES = os.path.join(CACHE, "pages")
SPOILERS = os.path.join(CACHE, "spoilers")


def api(params):
    params = dict(params, format="json", formatversion="2")
    url = API + "?" + urllib.parse.urlencode(params)
    for attempt in range(8):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 429:  # rate limited: back off as the server asks
                wait = int(e.headers.get("Retry-After") or 0) or 15 * (attempt + 1)
                print(f"rate limited, waiting {wait}s", file=sys.stderr)
                time.sleep(wait)
            else:
                print("retry", attempt, e, file=sys.stderr)
                time.sleep(2 + attempt * 3)
        except Exception as e:  # noqa: BLE001
            print("retry", attempt, e, file=sys.stderr)
            time.sleep(2 + attempt * 3)
    raise RuntimeError("API failed: " + url)


def slugify(title):
    s = title.lower().replace("'", "")
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s


def category_members(cat):
    out, cont = [], {}
    while True:
        data = api({"action": "query", "list": "categorymembers", "cmtitle": cat,
                    "cmlimit": "500", "cmnamespace": "0", **cont})
        out += [m["title"] for m in data["query"]["categorymembers"]]
        if "continue" not in data:
            return out
        cont = data["continue"]


def fetch_wikitext(titles):
    result = {}
    for i in range(0, len(titles), 50):
        chunk = titles[i:i + 50]
        data = api({"action": "query", "prop": "revisions", "rvprop": "content",
                    "rvslots": "main", "titles": "|".join(chunk)})
        for p in data["query"]["pages"]:
            if "revisions" in p:
                result[p["title"]] = p["revisions"][0]["slots"]["main"]["content"]
        time.sleep(0.5)
    return result


def template_body(text, name_re):
    """Return the inside of the first {{name ...}} template, honouring nested braces."""
    m = re.search(r"\{\{\s*" + name_re, text, re.I)
    if not m:
        return None
    i, depth = m.start(), 0
    while i < len(text):
        if text.startswith("{{", i):
            depth += 1
            i += 2
        elif text.startswith("}}", i):
            depth -= 1
            i += 2
            if depth == 0:
                return text[m.end():i - 2]
        else:
            i += 1
    return None


def split_top_level(body):
    parts, depth_c, depth_l, cur, i = [], 0, 0, [], 0
    while i < len(body):
        two = body[i:i + 2]
        if two in ("{{", "}}", "[[", "]]"):
            if two == "{{":
                depth_c += 1
            elif two == "}}":
                depth_c -= 1
            elif two == "[[":
                depth_l += 1
            else:
                depth_l -= 1
            cur.append(two)
            i += 2
            continue
        ch = body[i]
        if ch == "|" and depth_c == 0 and depth_l == 0:
            parts.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
        i += 1
    parts.append("".join(cur))
    return parts


def parse_infobox(text):
    return parse_infobox_named(text, r"Infobox[ _]Quest")


def parse_infobox_named(text, name_re):
    body = template_body(text, name_re)
    if body is None:
        return None
    fields = {}
    for part in split_top_level(body):
        if "=" not in part:
            continue
        k, v = part.split("=", 1)
        fields[k.strip().lower()] = v.strip()
    return fields


def to_int(v):
    if not v:
        return None
    m = re.search(r"\d+", v)
    return int(m.group(0)) if m else None


# quests with an Infobox Quest page that is missing from "Category:Quest Overview Pages" (checked 2026-10-27 against
# TibiaWiki BR, TibiaPal, Exevo Pan and the OpenTibiaBR quest log)
EXTRA_QUESTS = ["Ravenous Madness Quest"]


def in_scope(q):
    """Every quest that still exists in the game, at any level; only deprecated quests stay out.
    (Until 2026-10 the scope was level 1-100: minimum level <= 100 or no requirement.)"""
    status = (q["fields"].get("status") or "").lower()
    return "deprecated" not in status


def main():
    os.makedirs(PAGES, exist_ok=True)
    os.makedirs(SPOILERS, exist_ok=True)
    titles = category_members("Category:Quest Overview Pages")
    titles += [t for t in EXTRA_QUESTS if t not in titles]
    print(len(titles), "quest overview pages")
    texts = fetch_wikitext(titles)
    index = []
    for title, text in sorted(texts.items()):
        slug = slugify(title)
        with open(os.path.join(PAGES, slug + ".wiki"), "w", encoding="utf-8") as f:
            f.write(text)
        info = parse_infobox(text) or {}
        index.append({
            "title": title,
            "slug": slug,
            "has_infobox": bool(info),
            "lvl": to_int(info.get("lvl")),
            "lvl_raw": info.get("lvl"),
            "lvlrec": to_int(info.get("lvlrec")),
            "fields": info,
        })
    selected = [q for q in index if q["has_infobox"] and in_scope(q)]
    print(len(selected), "quests in scope (all levels, not deprecated)")

    spoilers = fetch_wikitext([q["title"] + "/Spoiler" for q in selected])
    for q in selected:
        sp = spoilers.get(q["title"] + "/Spoiler")
        q["has_spoiler"] = sp is not None
        if sp is not None:
            with open(os.path.join(SPOILERS, q["slug"] + ".wiki"), "w", encoding="utf-8") as f:
                f.write(sp)
        q["spoiler_size"] = len(sp or "")

    with open(os.path.join(CACHE, "index.json"), "w", encoding="utf-8") as f:
        json.dump(index, f, indent=1, ensure_ascii=False)
    with open(os.path.join(CACHE, "selected.json"), "w", encoding="utf-8") as f:
        json.dump(selected, f, indent=1, ensure_ascii=False)
    print("spoilers found:", sum(q["has_spoiler"] for q in selected))


if __name__ == "__main__":
    main()
