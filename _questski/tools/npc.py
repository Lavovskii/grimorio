"""Look up NPC positions: python tools/npc.py "Sam" "Kroox" ...  (case-insensitive, substring fallback)"""
import json
import os
import sys

npcs = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache", "npcs.json"),
                      encoding="utf-8"))
lower = {k.lower(): k for k in npcs}
for q in sys.argv[1:]:
    key = lower.get(q.lower())
    hits = [key] if key else [k for k in npcs if q.lower() in k.lower()][:8]
    if not hits:
        print(f"{q}: not found")
    for k in hits:
        n = npcs[k]
        pos = f"x={n['x']} y={n['y']} z={n['z']}" if "x" in n else "no position"
        print(f"{k}: {pos} | city={n.get('city')} | job={n.get('job')}")
