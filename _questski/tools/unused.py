"""Show what a guide does not use yet from its brief: images (with caption + surrounding brief text)
and coordinates.

Usage: python tools/unused.py <slug>
"""
import json
import os
import re
import sys

from validate import brief_images, norm_file

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main(slug):
    g = json.load(open(os.path.join(ROOT, "guides", slug + ".json"), encoding="utf-8"))
    brief = open(os.path.join(ROOT, "tools", "briefs", slug + ".md"), encoding="utf-8").read()
    blob = json.dumps(g, ensure_ascii=False)
    used = {norm_file(im["file"]) for s in g["sections"] for st in s["steps"] for im in st.get("images", [])}
    sprites = {norm_file(m + ".gif") for m in re.findall(r"\{(?:npc|item|creature|spell):([^|}]+)", blob)}
    sprites |= {norm_file(x + ".gif") for x in g.get("dangers", []) + g.get("npcs", [])}

    section = re.search(r"## IMAGES AVAILABLE[^\n]*\n(.*?)\n## ", brief, re.S)
    captions = {}
    if section:
        for line in section.group(1).splitlines():
            if line.startswith("- "):
                name, _, cap = line[2:].partition("  — ")
                captions[norm_file(name)] = (name.strip(), cap.strip())
    body = brief.split("## SPOILER PAGE", 1)[-1]
    print(f"== {slug}: images not used yet (sprites of items/creatures/NPCs are skipped) ==")
    n = 0
    for key in sorted(brief_images(brief)):
        if key in used or key in sprites:
            continue
        name, cap = captions.get(key, (key, ""))
        stem = re.escape(os.path.splitext(name)[0][:25])
        m = re.search(stem, body, re.I)
        ctx = ""
        if m:
            a = max(0, m.start() - 220)
            ctx = re.sub(r"\s+", " ", body[a:m.start() + 160])
        n += 1
        print(f"\n[{n}] {name}\n    caption: {cap or '-'}\n    context: ...{ctx}...")
    if not n:
        print("(none)")
    coords = set(re.findall(r"\[COORD x=(\d+) y=(\d+) z=(\d+)", brief))
    in_guide = set(re.findall(r'"x":\s*(\d+),\s*"y":\s*(\d+),\s*"z":\s*(\d+)', blob))
    missing = [c for c in coords if c not in in_guide]
    print(f"\n== coordinates in the brief not used in the guide: {len(missing)} ==")
    for x, y, z in missing:
        m = re.search(rf"\[COORD x={x} y={y} z={z}[^\]]*\]", brief)
        a = max(0, m.start() - 160)
        print(f"  {x},{y},{z}: ...{re.sub(chr(10), ' ', brief[a:m.end()])}")
    print(f"\nstart coordinate present: {'start' in g}")


if __name__ == "__main__":
    main(sys.argv[1])
