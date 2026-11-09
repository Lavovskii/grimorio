"""Liga bosses a acessos documentados; nunca deduz viagens pelas coordenadas.

Usa os dados já publicados pelo Questski. Correr depois dos builds do Questski
e dos bosses: python -I _dev/build_boss_access.py [raiz] [--check].
"""
import json
import re
import sys
from pathlib import Path


def build(root):
    def read(path):
        return json.loads((root / path).read_text(encoding="utf-8"))

    bosses = read("data/bosses.json")["b"]
    places = read("quests/data/places.json")
    names = {k.casefold(): k for k in places["places"]}
    names.update({k.casefold(): v for k, v in places.get("alias", {}).items()})
    guides = {}
    # Só referências explícitas nas secções: não se infere acesso por proximidade.
    for path in sorted((root / "quests/data/quests").glob("*.json")):
        q = json.loads(path.read_text(encoding="utf-8"))
        for i, sec in enumerate(q.get("sections", [])):
            refs = set(re.findall(r"\{creature:([^}|]+)", json.dumps(sec, ensure_ascii=False)))
            for name in refs:
                key = name.strip().casefold()
                if key in bosses:
                    guides.setdefault(key, []).append({"slug": q["slug"], "quest": q["name"],
                                                       "section": i, "title": sec["title"]})
    result = {}
    for key, boss in bosses.items():
        locs = []
        for loc in boss.get("loc", []):
            name = names.get(loc.casefold())
            if name and name not in locs:
                locs.append(name)
        links = guides.get(key, [])
        links.sort(key=lambda x: (x["quest"] != boss.get("q"), x["slug"], x["section"]))
        result[key] = {"places": locs, "guides": links}
    used = {name for b in result.values() for name in b["places"]}
    return {"v": 1, "b": result, "places": {
        name: {k: v for k, v in places["places"][name].items()
               if k in ("title", "requirements", "arrive", "leave", "warnings", "entrance")}
        for name in sorted(used)}}


def main():
    args = [x for x in sys.argv[1:] if not x.startswith("--")]
    root = Path(args[0]).resolve() if args else Path(__file__).resolve().parents[1]
    data = build(root)
    text = json.dumps(data, ensure_ascii=False, indent=1) + "\n"
    target = root / "data/boss-access.json"
    if "--check" in sys.argv:
        if not target.exists() or target.read_text(encoding="utf-8") != text:
            sys.exit("boss-access.json desatualizado")
    else:
        target.write_text(text, encoding="utf-8", newline="")
    print(f'{sum(bool(b["places"]) for b in data["b"].values())} bosses com ficha de acesso; '
          f'{sum(bool(b["guides"]) for b in data["b"].values())} com passos nos guias')


if __name__ == "__main__":
    main()
