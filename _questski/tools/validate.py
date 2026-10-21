"""Validate guide JSON files written in guides/<slug>.json.

Usage:
  python tools/validate.py guides/sams-old-backpack-quest.json [more files...]
  python tools/validate.py --all
Exit code 0 when every file passes (warnings are allowed), 1 otherwise.
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRIEFS = os.path.join(ROOT, "tools", "briefs")
NPCS_PATH = os.path.join(ROOT, "tools", "cache", "npcs.json")

CATEGORIES = {"historia", "tesouro", "outfit", "acesso", "tarefas", "troca",
              "world-change", "evento", "tutorial"}
REGIONS = {"Rookgaard", "Dawnport", "Thais", "Carlin", "Ab'Dendriel", "Kazordoon", "Venore",
           "Edron", "Darashia", "Ankrahmun", "Port Hope", "Liberty Bay", "Svargrond",
           "Yalahar", "Farmine", "Gray Beach", "Rathleton", "Roshamuul", "Krailos", "Issavi",
           "Feyrist", "Marapur", "Vários"}
BOUNDS = dict(xmin=31744, xmax=34303, ymin=30976, ymax=33023)
TOKEN_RE = re.compile(r"\{(npc|item|creature|spell|wiki|key|coord):([^{}]+)\}")
STEP_KEYS = {"title", "text", "npc", "dialogue", "coords", "map", "images", "table",
             "warning", "tip", "reward"}
TOP_KEYS = {"slug", "category", "region", "difficulty", "duration", "summary", "legend_pt",
            "start", "requirements", "items_needed", "rewards", "achievements", "dangers",
            "npcs", "tips", "sections", "notes", "unlocks"}
UNLOCK_KINDS = {"zona", "transporte", "npc", "loja", "funcionalidade", "missao"}


INVISIBLE = re.compile("[\u200b-\u200f\u202a-\u202e\u2060\ufeff]")


def norm_file(name):
    return INVISIBLE.sub("", name).replace("_", " ").strip().lower()


def brief_images(brief):
    files = {norm_file(f) for f in re.findall(r"\[\[(?:File|Image):([^|\]]+)", brief, re.I)}
    m = re.search(r"## IMAGES AVAILABLE[^\n]*\n(.*?)\n## ", brief, re.S)
    if m:
        for line in m.group(1).splitlines():
            if line.startswith("- "):
                files.add(norm_file(line[2:].split("  — ")[0]))
    return files


def _extra_images():
    """Images of wiki pages a writer looked at with tools/place.py (route maps etc.) are allowed too."""
    files = glob.glob(os.path.join(ROOT, "tools", "cache", "extra_images", "*.json"))
    legacy = os.path.join(ROOT, "tools", "cache", "extra_images.json")
    if os.path.exists(legacy):
        files.append(legacy)
    out = set()
    for path in files:
        try:
            data = json.load(open(path, encoding="utf-8"))
        except (ValueError, OSError):  # being written by another process
            continue
        out |= {norm_file(n) for names in data.values() for n in names}
    return out


EXTRA_IMAGES = _extra_images()


def check_coord(c, where, errors):
    if not isinstance(c, dict):
        errors.append(f"{where}: coordinate must be an object")
        return
    for k in ("x", "y", "z"):
        if not isinstance(c.get(k), int):
            errors.append(f"{where}: '{k}' must be an integer")
            return
    if not (BOUNDS["xmin"] <= c["x"] <= BOUNDS["xmax"] and BOUNDS["ymin"] <= c["y"] <= BOUNDS["ymax"]):
        errors.append(f"{where}: ({c['x']},{c['y']}) outside the Tibia map")
    if not 0 <= c["z"] <= 15:
        errors.append(f"{where}: z={c['z']} must be 0..15")


def check_text(s, where, errors, warnings, npcs):
    if not isinstance(s, str):
        errors.append(f"{where}: expected a string")
        return
    for kind, val in TOKEN_RE.findall(s):
        name = val.split("|")[0].strip()
        if kind == "coord":
            parts = name.split(",")
            if len(parts) != 3 or not all(p.strip().isdigit() for p in parts):
                errors.append(f"{where}: bad {{coord:{val}}} (use {{coord:x,y,z}})")
            else:
                check_coord(dict(x=int(parts[0]), y=int(parts[1]), z=int(parts[2])), where, errors)
        elif kind == "npc" and npcs and name not in npcs:
            warnings.append(f"{where}: NPC '{name}' not found in npcs.json (check spelling)")
    stray = re.findall(r"\{(?!npc:|item:|creature:|spell:|wiki:|key:|coord:)[a-z]+:", s)
    if stray:
        errors.append(f"{where}: unknown token type {stray}")
    if "[[" in s or "{{" in s or "'''" in s:
        errors.append(f"{where}: leftover wiki markup ([[ ]], {{{{ }}}} or ''')")


def validate(path, npcs):
    errors, warnings = [], []
    slug = os.path.splitext(os.path.basename(path))[0]
    try:
        g = json.load(open(path, encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        return [f"invalid JSON: {e}"], []
    brief_path = os.path.join(BRIEFS, slug + ".md")
    if not os.path.exists(brief_path):
        errors.append(f"no brief named {slug}.md - file name must be the quest slug")
        brief = ""
    else:
        brief = open(brief_path, encoding="utf-8").read()
    brief_files = brief_images(brief) | EXTRA_IMAGES

    if g.get("slug") != slug:
        errors.append(f"slug '{g.get('slug')}' must equal file name '{slug}'")
    unknown = set(g) - TOP_KEYS
    if unknown:
        errors.append(f"unknown top-level keys: {sorted(unknown)}")
    if g.get("category") not in CATEGORIES:
        errors.append(f"category must be one of {sorted(CATEGORIES)}")
    if g.get("region") not in REGIONS:
        errors.append(f"region must be one of {sorted(REGIONS)}")
    if g.get("difficulty") not in (1, 2, 3, 4, 5):
        errors.append("difficulty must be an integer 1..5")
    for k in ("summary", "duration"):
        if not isinstance(g.get(k), str) or not g.get(k).strip():
            errors.append(f"'{k}' is required (non-empty string)")
    if "start" in g:
        check_coord(g["start"], "start", errors)
    else:
        warnings.append("no 'start' coordinate (where the quest begins)")
    for k in ("requirements", "tips", "notes", "achievements", "dangers", "npcs"):
        if k in g and not (isinstance(g[k], list) and all(isinstance(v, str) for v in g[k])):
            errors.append(f"'{k}' must be a list of strings")
    for k in ("requirements", "tips", "notes", "summary", "legend_pt"):
        vals = g.get(k, [])
        for i, v in enumerate(vals if isinstance(vals, list) else [vals]):
            check_text(v, f"{k}[{i}]", errors, warnings, npcs)
    for k in ("items_needed", "rewards"):
        for i, it in enumerate(g.get(k, [])):
            if not isinstance(it, dict) or not ("item" in it or "text" in it):
                errors.append(f"{k}[{i}]: needs 'item' (wiki title) or 'text'")
                continue
            if "qty" in it and not isinstance(it["qty"], int):
                errors.append(f"{k}[{i}]: qty must be an integer")
            for f in ("text", "note"):
                if f in it:
                    check_text(it[f], f"{k}[{i}].{f}", errors, warnings, npcs)
    for n in g.get("npcs", []):
        if npcs and n not in npcs:
            warnings.append(f"npcs: '{n}' not found in npcs.json")
    unlocks = g.get("unlocks", [])
    if not isinstance(unlocks, list):
        errors.append("'unlocks' must be a list")
        unlocks = []
    for i, u in enumerate(unlocks):
        w = f"unlocks[{i}]"
        if not isinstance(u, dict) or not isinstance(u.get("what"), str) or not u["what"].strip():
            errors.append(f"{w}: needs 'what' (the area/transport/NPC/feature unlocked)")
            continue
        if u.get("kind") not in UNLOCK_KINDS:
            errors.append(f"{w}: kind must be one of {sorted(UNLOCK_KINDS)}")
        if set(u) - {"what", "kind", "place", "when", "note"}:
            errors.append(f"{w}: unknown keys {sorted(set(u) - {'what', 'kind', 'place', 'when', 'note'})}")
        for f in ("what", "when", "note"):
            if f in u:
                check_text(u[f], f"{w}.{f}", errors, warnings, npcs)

    sections = g.get("sections")
    if not isinstance(sections, list) or not sections:
        errors.append("'sections' must be a non-empty list")
        sections = []
    n_steps = 0
    for si, sec in enumerate(sections):
        w = f"sections[{si}]"
        if not isinstance(sec, dict) or not isinstance(sec.get("title"), str):
            errors.append(f"{w}: needs a 'title'")
            continue
        if "intro" in sec:
            check_text(sec["intro"], w + ".intro", errors, warnings, npcs)
        steps = sec.get("steps")
        if not isinstance(steps, list) or not steps:
            errors.append(f"{w}: 'steps' must be a non-empty list")
            continue
        for ti, st in enumerate(steps):
            n_steps += 1
            ws = f"{w}.steps[{ti}]"
            if not isinstance(st, dict) or not isinstance(st.get("text"), str) or not st["text"].strip():
                errors.append(f"{ws}: needs non-empty 'text'")
                continue
            extra = set(st) - STEP_KEYS
            if extra:
                errors.append(f"{ws}: unknown keys {sorted(extra)}")
            for f in ("title", "text", "warning", "tip", "reward"):
                if f in st:
                    check_text(st[f], f"{ws}.{f}", errors, warnings, npcs)
            if "npc" in st and npcs and st["npc"] not in npcs:
                warnings.append(f"{ws}.npc: '{st['npc']}' not found in npcs.json")
            for ci, c in enumerate(st.get("coords", [])):
                check_coord(c, f"{ws}.coords[{ci}]", errors)
            if "map" in st:
                check_coord(st["map"], f"{ws}.map", errors)
                for mi, mk in enumerate(st["map"].get("marks", [])):
                    check_coord(dict(mk, z=mk.get("z", st["map"].get("z"))), f"{ws}.map.marks[{mi}]", errors)
            for di, d in enumerate(st.get("dialogue", [])):
                if not isinstance(d, dict) or len(d) != 1 or next(iter(d)) not in ("you", "npc"):
                    errors.append(f"{ws}.dialogue[{di}]: must be {{\"you\": ...}} or {{\"npc\": ...}}")
            for ii, im in enumerate(st.get("images", [])):
                if not isinstance(im, dict) or "file" not in im:
                    errors.append(f"{ws}.images[{ii}]: needs 'file'")
                elif norm_file(im["file"]) not in brief_files:
                    errors.append(f"{ws}.images[{ii}]: '{im['file']}' is not referenced in the brief")
            if "table" in st:
                t = st["table"]
                if not isinstance(t, dict) or not isinstance(t.get("rows"), list):
                    errors.append(f"{ws}.table: needs 'head' and 'rows'")
                else:
                    for ri, row in enumerate(t["rows"]):
                        for ci, cell in enumerate(row):
                            check_text(str(cell), f"{ws}.table.rows[{ri}][{ci}]", errors, warnings, npcs)
    if n_steps == 0:
        errors.append("guide has no steps")
    return errors, warnings


def main():
    args = sys.argv[1:]
    if args == ["--all"]:
        args = sorted(glob.glob(os.path.join(ROOT, "guides", "*.json")))
    npcs = {}
    if os.path.exists(NPCS_PATH):
        npcs = json.load(open(NPCS_PATH, encoding="utf-8"))
    failed = 0
    for path in args:
        errors, warnings = validate(path, npcs)
        name = os.path.basename(path)
        if errors:
            failed += 1
            print(f"FAIL {name}")
            for e in errors:
                print("   error:", e)
        else:
            print(f"OK   {name}")
        for w in warnings:
            print("   warn:", w)
    print(f"{len(args) - failed}/{len(args)} passed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
