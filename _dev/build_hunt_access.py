"""Liga hunts às fichas de acesso do Questski por nome, nunca por distância.

python -I _dev/build_hunt_access.py [raiz] [--check]
"""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from gjson import load_G

# Correspondências de nomes presentes no G e nas fichas de locais.
# Não alargar isto com correspondências por criatura, cidade ou coordenadas.
NAMES = {
    "oldmasonry": ["Old Masonry"],
    "werelions": ["Lion Sanctum"],
    "catacombs": ["Abandoned Sewers"],
}


def build(root):
    _, g, _ = load_G(str(root))
    source = json.loads((root / "quests/data/places.json").read_text(encoding="utf-8"))
    names = {n.casefold(): n for n in source["places"]}
    names.update({n.casefold(): v for n, v in source.get("alias", {}).items()})
    hunts = {}
    for key, p in g["places"].items():
        found = []
        for n in [p["n"], *p.get("wn", []), *NAMES.get(key, [])]:
            match = names.get(n.casefold())
            if match and match not in found:
                found.append(match)
        hunts[key] = found
    used = {n for ns in hunts.values() for n in ns}
    return {"v": 1, "h": hunts, "places": {
        n: {k: v for k, v in source["places"][n].items()
            if k in ("title", "requirements", "arrive", "leave", "warnings", "entrance")}
        for n in sorted(used)}}


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    root = Path(args[0]).resolve() if args else Path(__file__).resolve().parents[1]
    data = build(root)
    text = json.dumps(data, ensure_ascii=False, indent=1) + "\n"
    target = root / "data/hunt-access.json"
    if "--check" in sys.argv:
        if not target.exists() or target.read_text(encoding="utf-8") != text:
            sys.exit("hunt-access.json desatualizado")
    else:
        target.write_text(text, encoding="utf-8", newline="")
    print(f'{sum(bool(v) for v in data["h"].values())}/{len(data["h"])} hunts com ficha de acesso')


if __name__ == "__main__":
    main()
