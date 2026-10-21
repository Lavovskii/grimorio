"""Fetch every TibiaWiki NPC infobox and save name -> position (x, y, z) + city.

Usage: python tools/fetch_npcs.py
Writes tools/cache/npcs.json (also copied to site/data/npcs.json by build.py)
"""
import json
import os

from fetch_wiki import CACHE, category_members, fetch_wikitext, parse_infobox_named
from prepare_briefs import coord


def main():
    titles = category_members("Category:NPCs")
    print(len(titles), "NPC pages")
    texts = fetch_wikitext(titles)
    npcs = {}
    for title, text in texts.items():
        info = parse_infobox_named(text, r"Infobox[ _]NPC")
        if not info:
            continue
        x, y = coord(info.get("posx", "")), coord(info.get("posy", ""))
        z = coord(info.get("posz", ""))
        entry = {
            "city": strip_links(info.get("city", "")),
            "job": strip_links(info.get("job", "")),
        }
        if x and y and z is not None:
            entry.update(x=x, y=y, z=z)
        npcs[title] = entry
    with open(os.path.join(CACHE, "npcs.json"), "w", encoding="utf-8") as f:
        json.dump(npcs, f, indent=0, ensure_ascii=False, sort_keys=True)
    print(len(npcs), "NPCs;", sum("x" in n for n in npcs.values()), "with coordinates")


def strip_links(v):
    import re
    v = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", v)
    return re.sub(r"<[^>]+>", "", v).strip()


if __name__ == "__main__":
    main()
