"""Collect every place the guides send the player to, with source material for writing its travel card.

Usage: python tools/prepare_places.py
Writes tools/places_src/<slug>.md   (wiki page text, route page, existing arrive/leave steps from guides)
       tools/places_src/_list.json  (title, slug, how many guides mention it)
"""
import glob
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

from build_wiki import KIND_BY_CAT, clean_title, page_slug, raw_path  # noqa: E402
from place import to_text  # noqa: E402

OUT = os.path.join(ROOT, "tools", "places_src")
LOCAL = dict(KIND_BY_CAT)["local"]
ARRIVE = re.compile(r"^(Chegar|Sair|Voltar|Entrar|Ir)\b", re.I)


def load_raw(title):
    p = raw_path(title)
    if os.path.exists(p):
        try:
            return json.load(open(p, encoding="utf-8"))
        except ValueError:
            return None
    return None


def main():
    os.makedirs(OUT, exist_ok=True)
    aliases = json.load(open(os.path.join(ROOT, "tools", "cache", "wiki_aliases.json"), encoding="utf-8"))
    routes = json.load(open(os.path.join(ROOT, "tools", "cache", "route_pages.json"), encoding="utf-8"))
    guides = {os.path.splitext(os.path.basename(p))[0]: json.load(open(p, encoding="utf-8"))
              for p in glob.glob(os.path.join(ROOT, "guides", "*.json"))}

    def canon(t):
        t = clean_title(t)
        return aliases.get(t) or t

    # places = {wiki:..} tokens whose page is a location
    mentions = {}
    for slug, g in guides.items():
        blob = json.dumps(g, ensure_ascii=False)
        for tok in re.findall(r"\{wiki:([^{}|]+)", blob):
            c = canon(tok)
            raw = load_raw(c)
            if raw and any(LOCAL(cat.replace("_", " ")) for cat in raw["cats"]) and not c.startswith("Route:"):
                mentions.setdefault(c, set()).add(slug)

    listing = []
    for title, slugs in sorted(mentions.items(), key=lambda kv: -len(kv[1])):
        raw = load_raw(title)
        names = {title.lower()} | {a.lower() for a, c in aliases.items() if c == title}
        steps, context = [], []
        for slug, g in guides.items():
            for si, sec in enumerate(g["sections"]):
                for ti, st in enumerate(sec["steps"]):
                    t = (st.get("title") or "")
                    blob = json.dumps(st, ensure_ascii=False).lower()
                    if not any(n in blob for n in names):
                        continue
                    entry = f"[{slug} {si}-{ti}] {t}\n{st['text']}\ncoords: {st.get('coords', [])}"
                    if ARRIVE.match(t) and any(n in t.lower() for n in names):
                        steps.append(entry)
                    elif len(context) < 4:
                        context.append(entry)
        route = next((r for r in routes if r.lower().replace("route: ", "route:") == f"route:{title.lower()}"), None)
        rtext = to_text(load_raw(route)["html"])[:5000] if route and load_raw(route) else ""
        slug = page_slug(title)
        md = [f"# PLACE: {title}", f"slug: {slug}", f"mentioned in {len(slugs)} guides: {', '.join(sorted(slugs))}", "",
              "## WIKI PAGE (location, how to get there, exits; [COORD] = map link)", to_text(raw["html"])[:7000], ""]
        if route:
            md += [f"## ROUTE PAGE ({route})", rtext, ""]
        md += ["## EXISTING ARRIVE/LEAVE STEPS IN OUR GUIDES (already researched — reuse them)", *(steps or ["(none)"]), "",
               "## OTHER GUIDE STEPS MENTIONING IT (context)", *(context or ["(none)"])]
        open(os.path.join(OUT, slug + ".md"), "w", encoding="utf-8").write("\n".join(md))
        listing.append({"title": title, "slug": slug, "guides": len(slugs), "has_steps": bool(steps)})
    json.dump(listing, open(os.path.join(OUT, "_list.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print(len(listing), "places;", sum(p["has_steps"] for p in listing), "with existing arrive/leave steps")


if __name__ == "__main__":
    main()
