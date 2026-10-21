"""Print everything that tells what a quest unlocks (areas, transport, NPCs, features), compactly.

Usage: python tools/access_ctx.py <slug>
"""
import glob
import html
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEY = re.compile(r"acesso|access|desbloque|unlock|permite|podes agora|passas a|rank|citizen|cidadão|teleport|portal|"
                 r"barco|boat|carpet|tapete|passage|viaja|entrar|aceder|porta|door|gate|chave|key", re.I)


def main(slug):
    g = json.load(open(os.path.join(ROOT, "guides", slug + ".json"), encoding="utf-8"))
    sel = {q["slug"]: q for q in json.load(open(os.path.join(ROOT, "tools", "cache", "selected.json"), encoding="utf-8"))}
    f = sel[slug]["fields"]
    name = html.unescape(f.get("name") or sel[slug]["title"])
    print(f"# {name}  [{slug}]  category={g.get('category')} region={g.get('region')}")
    print(f"aka: {f.get('aka', '')}")
    print(f"WIKI REWARD: {re.sub(r'\s+', ' ', f.get('reward', ''))[:900]}")
    print(f"\nSUMMARY: {g.get('summary', '')}")
    for k in ("requirements", "achievements", "notes"):
        for v in g.get(k, []) or []:
            print(f"{k.upper()}: {v}")
    for r in g.get("rewards", []):
        print("REWARD:", r.get("item") or r.get("text"), "|", r.get("note", ""))
    if g.get("unlocks"):
        print("CURRENT unlocks:", json.dumps(g["unlocks"], ensure_ascii=False))
    print("\nSTEPS THAT LOOK RELEVANT:")
    shown = 0
    for si, sec in enumerate(g.get("sections", [])):
        for ti, st in enumerate(sec.get("steps", [])):
            blob = " ".join(str(st.get(k, "")) for k in ("title", "text", "reward", "tip"))
            if KEY.search(blob) and shown < 18:
                shown += 1
                print(f"- [{si}-{ti}] {sec.get('title')} > {st.get('title', '')}: {re.sub(r'\s+', ' ', blob)[:330]}")
    names = [n.strip().lower() for n in [name] + re.split(r",| or ", f.get("aka", "")) if len(n.strip()) > 6]
    print("\nPLACE CARDS THAT NAME THIS QUEST AS A REQUIREMENT:")
    for p in glob.glob(os.path.join(ROOT, "places", "*.json")):
        pl = json.load(open(p, encoding="utf-8"))
        for line in (pl.get("requirements") or []) + (pl.get("arrive") or []):
            if any(n in line.lower() for n in names):
                print(f"- {pl['title']}: {line[:300]}")
                break


if __name__ == "__main__":
    main(sys.argv[1])
