"""Structured data pulled out of the cached TibiaWiki pages, used to build the "Como obter" panel of each item.

extract(raw)            -> record: infobox fields, map spots, dropped-by, NPC trades, loot table, creature location
guide_item_refs(...)    -> where each item appears in our own guides (quest, step, coordinates)
build_howto(...)        -> the panel data for one item page
"""
import glob
import json
import os
import re
import urllib.parse

from bs4 import BeautifulSoup

from prepare_briefs import coord

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN_ITEM = re.compile(r"\{item:([^{}|]+)")
INVISIBLE = re.compile("[​-‏‪-‮⁠﻿]")
RARITY = {"loot-always": "sempre", "loot-common": "comum", "loot-uncommon": "pouco comum",
          "loot-semi-rare": "semi-raro", "loot-rare": "raro", "loot-very-rare": "muito raro"}


def clean_title(t):
    t = INVISIBLE.sub("", urllib.parse.unquote(t)).replace("_", " ").strip()
    return t[:1].upper() + t[1:] if t else t


def mapper_coord(href):
    """https://tibia.fandom.com/wiki/Mapper?coords=125.121-127.196-7-4-1-1 -> (x, y, z)"""
    m = re.search(r"Mapper\?(?:[^\"'\s]*&)?coords=([0-9.]+)-([0-9.]+)-(\d+)", href.replace("&amp;", "&"))
    if not m:
        return None
    x, y, z = coord(m.group(1)), coord(m.group(2)), int(m.group(3))
    if not (31744 <= (x or 0) <= 34303 and 30976 <= (y or 0) <= 33023 and 0 <= z <= 15):
        return None
    return {"x": x, "y": y, "z": z}


def _text(el, limit=260):
    t = re.sub(r"\s+", " ", el.get_text(" ", strip=True))
    return t if len(t) <= limit else t[:limit].rsplit(" ", 1)[0] + "…"


def _wiki_links(el):
    out = []
    for a in el.select('a[href^="/wiki/"]'):
        t = clean_title(a["href"][6:].split("#")[0])
        if t and ":" not in t and t not in out:
            out.append(t)
    return out


def _price(td):
    t = _text(td, 80)
    m = re.match(r"^([\d.,]+)\s*$", t.replace("gp", "").strip())
    return int(re.sub(r"[.,]", "", m.group(1))) if m else t


def extract(raw):
    soup = BeautifulSoup(raw["html"], "html.parser")
    rec = {"info": {}, "spots": [], "droppedby": [], "buy": [], "sell": [], "loot": {}, "loc": None}
    for d in soup.select("aside .pi-data"):
        k, v = d.get("data-source"), d.select_one(".pi-data-value")
        if k and v and k not in rec["info"]:
            rec["info"][k] = _text(v, 120)

    for a in soup.find_all("a", href=re.compile(r"Mapper\?")):
        c = mapper_coord(a["href"])
        if not c:
            continue
        holder = a.find_parent(["li", "p", "td", "dd"]) or a.parent
        c["text"] = _text(holder)
        if c not in rec["spots"]:
            rec["spots"].append(c)

    dd = soup.select_one("#item-droppedby")
    if dd:
        rec["droppedby"] = _wiki_links(dd)

    for box in soup.select("div.trades"):
        head = box.find(["h4", "h3"])
        kind = "buy" if head and "buy" in head.get_text().lower() else "sell" if head and "sell" in head.get_text().lower() else None
        table = box.find("table")
        if not kind or not table:
            continue
        for tr in table.find_all("tr")[1:]:
            tds = tr.find_all("td")
            if len(tds) < 3:
                continue
            npc = _wiki_links(tds[0])
            if not npc:
                continue
            rec[kind].append({"npc": npc[0], "where": _text(tds[1], 60), "price": _price(tds[2])})

    for table in soup.find_all("table"):
        heads = [th.get_text(" ", strip=True).lower() for th in table.find_all("th")]
        if "item" not in heads or not any(h.startswith("%") or h == "%" for h in heads):
            continue
        qi = heads.index("quantity") if "quantity" in heads else None
        for tr in table.find_all("tr")[1:]:
            tds = tr.find_all("td")
            if len(tds) < 3:
                continue
            links = _wiki_links(tds[1]) if len(tds) > 1 else []
            if not links:
                continue
            last = tds[-1]
            pct = last.get("data-sort-value")
            rarity = next((RARITY[c] for c in last.get("class", []) if c in RARITY), None)
            rec["loot"][links[0].lower()] = {
                "pct": round(float(pct), 3) if pct else None,
                "qty": _text(tds[qi], 20) if qi is not None and qi < len(tds) else None,
                "rarity": rarity,
            }

    loc = soup.select_one("#creature-location") or soup.select_one("#npc-location")
    if loc:
        head = loc.find(["h2", "h3"])
        if head:
            head.decompose()
        rec["loc"] = {"text": _text(loc, 600), "places": _wiki_links(loc)[:25]}
    return rec


# ------------------------------------------------------------------ our guides
def guide_item_refs(alias_of):
    """{canonical item title: [{slug, quest, step, title, kind, coords}]}"""
    index = json.load(open(os.path.join(os.path.dirname(ROOT), "quests", "data", "index.json"), encoding="utf-8"))
    names = {q["slug"]: q["name"] for q in index["quests"]}
    npcs = json.load(open(os.path.join(ROOT, "tools", "cache", "npcs.json"), encoding="utf-8"))
    refs = {}

    def add(item, entry):
        canon = alias_of(clean_title(item))
        if not canon:
            return
        lst = refs.setdefault(canon, [])
        key = (entry["slug"], entry.get("step"), entry["kind"])
        if not any((e["slug"], e.get("step"), e["kind"]) == key for e in lst):
            lst.append(entry)

    for path in glob.glob(os.path.join(ROOT, "guides", "*.json")):
        slug = os.path.splitext(os.path.basename(path))[0]
        g = json.load(open(path, encoding="utf-8"))
        rewards = {clean_title(r["item"]).lower() for r in g.get("rewards", []) if r.get("item")}
        needed = {clean_title(r["item"]).lower(): r for r in g.get("items_needed", []) if r.get("item")}
        seen = set()
        n = 0
        for si, sec in enumerate(g.get("sections", [])):
            for ti, st in enumerate(sec.get("steps", [])):
                n += 1
                blob = json.dumps({k: st.get(k) for k in ("title", "text", "reward", "tip", "warning", "table")}, ensure_ascii=False)
                coords = [dict(x=c["x"], y=c["y"], z=c["z"], label=c.get("label", "")) for c in st.get("coords", [])]
                if st.get("map"):
                    coords += [dict(x=m["x"], y=m["y"], z=m.get("z", st["map"]["z"]), label=m.get("label", ""))
                               for m in st["map"].get("marks", [])] or [dict(x=st["map"]["x"], y=st["map"]["y"], z=st["map"]["z"], label="")]
                npc = npcs.get(st.get("npc") or "")
                if npc and "x" in npc and not coords:
                    coords = [dict(x=npc["x"], y=npc["y"], z=npc["z"], label=st["npc"])]
                for item in TOKEN_ITEM.findall(blob):
                    low = clean_title(item).lower()
                    in_reward = low in rewards or item.lower() in (st.get("reward") or "").lower()
                    kind = "reward" if in_reward and ("{item:" + item) in (st.get("reward") or "") or (in_reward and low in rewards) else \
                        "needed" if low in needed else "mention"
                    seen.add(low)
                    add(item, {"slug": slug, "quest": names.get(slug, slug), "step": f"{si}-{ti}", "n": n,
                               "title": st.get("title") or sec.get("title", ""), "kind": kind, "coords": coords[:6]})
        for r in rewards - seen:
            add(r, {"slug": slug, "quest": names.get(slug, slug), "kind": "reward"})
        for low, r in needed.items():
            if low not in seen:
                add(r["item"], {"slug": slug, "quest": names.get(slug, slug), "kind": "needed", "qty": r.get("qty")})
    order = {"reward": 0, "needed": 1, "mention": 2}
    for lst in refs.values():
        lst.sort(key=lambda e: (order[e["kind"]], e["quest"], e.get("n", 0)))
    return refs


# ------------------------------------------------------------------ the panel
def build_howto(title, rec, records, npcs, quest_refs, canon_of):
    howto = {}
    if quest_refs.get(title):
        howto["quests"] = quest_refs[title][:40]

    def npc_entry(row):
        name = canon_of(row["npc"]) or row["npc"]
        e = {"npc": name, "where": row["where"], "price": row["price"]}
        n = npcs.get(name) or npcs.get(row["npc"])
        if n and "x" in n:
            e["pos"] = {"x": n["x"], "y": n["y"], "z": n["z"]}
        return e

    if rec["buy"]:
        howto["buy"] = [npc_entry(r) for r in rec["buy"]]
    if rec["sell"]:
        howto["sell"] = [npc_entry(r) for r in rec["sell"]]

    drops = []
    for c in rec["droppedby"]:
        cname = canon_of(c) or c
        crec = records.get(cname)
        d = {"creature": cname}
        if crec:
            loot = crec["loot"].get(title.lower())
            if loot:
                d.update({k: v for k, v in loot.items() if v})
            for k in ("hp", "exp"):
                if crec["info"].get(k):
                    d[k] = crec["info"][k]
            if crec["loc"]:
                d["loc"] = crec["loc"]["text"]
                places = []
                for p in crec["loc"]["places"]:
                    pc = canon_of(p) or p
                    prec = records.get(pc)
                    if prec and prec["spots"]:
                        s = prec["spots"][0]
                        places.append({"name": pc, "x": s["x"], "y": s["y"], "z": s["z"]})
                if places:
                    d["places"] = places[:12]
            spots = [s for s in (crec["spots"] or [])][:8]
            if spots:
                d["spots"] = spots
        drops.append(d)
    if drops:
        drops.sort(key=lambda d: -(d.get("pct") or -1))
        howto["drops"] = drops[:60]
    if rec["spots"]:
        howto["spots"] = rec["spots"][:20]
    return howto
