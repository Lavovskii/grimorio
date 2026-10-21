"""Validate place travel cards in places/<slug>.json.

Usage: python tools/validate_places.py places/<slug>.json [...]   or   --all
"""
import glob
import json
import os
import sys

from validate import EXTRA_IMAGES, check_coord, check_text, norm_file

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TYPES = {"cidade", "ilha", "gruta", "dungeon", "montanha", "zona", "edificio", "outro"}
KEYS = {"title", "type", "near", "summary", "entrance", "requirements", "items", "arrive", "leave",
        "coords", "images", "warnings"}


def known_images():
    path = os.path.join(ROOT, "site", "data", "images.json")
    names = set(json.load(open(path, encoding="utf-8"))) if os.path.exists(path) else set()
    return names | EXTRA_IMAGES


def validate(path, images, npcs):
    errors, warnings = [], []
    try:
        p = json.load(open(path, encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        return [f"invalid JSON: {e}"], []
    slug = os.path.splitext(os.path.basename(path))[0]
    if not os.path.exists(os.path.join(ROOT, "tools", "places_src", slug + ".md")):
        errors.append(f"no dossier tools/places_src/{slug}.md — file name must be the dossier slug")
    if set(p) - KEYS:
        errors.append(f"unknown keys {sorted(set(p) - KEYS)}")
    for k in ("title", "summary"):
        if not isinstance(p.get(k), str) or not p[k].strip():
            errors.append(f"'{k}' is required")
    if p.get("type") not in TYPES:
        errors.append(f"type must be one of {sorted(TYPES)}")
    for k in ("arrive", "leave"):
        v = p.get(k)
        if not isinstance(v, list) or not v or not all(isinstance(s, str) and s.strip() for s in v):
            errors.append(f"'{k}' must be a non-empty list of strings")
    for k in ("requirements", "warnings", "items"):
        if k in p and not (isinstance(p[k], list) and all(isinstance(s, str) for s in p[k])):
            errors.append(f"'{k}' must be a list of strings")
    for k in ("summary",):
        check_text(p.get(k, ""), k, errors, warnings, npcs)
    for k in ("arrive", "leave", "requirements", "warnings"):
        for i, s in enumerate(p.get(k, []) or []):
            check_text(s, f"{k}[{i}]", errors, warnings, npcs)
    if "entrance" in p:
        check_coord(p["entrance"], "entrance", errors)
    for i, c in enumerate(p.get("coords", [])):
        check_coord(c, f"coords[{i}]", errors)
    for i, im in enumerate(p.get("images", [])):
        if not isinstance(im, dict) or "file" not in im:
            errors.append(f"images[{i}] needs 'file'")
        elif norm_file(im["file"]) not in images:
            errors.append(f"images[{i}]: '{im['file']}' unknown — use names listed by tools/place.py")
    return errors, warnings


def main():
    args = sys.argv[1:]
    if args == ["--all"]:
        args = sorted(glob.glob(os.path.join(ROOT, "places", "*.json")))
    npcs = json.load(open(os.path.join(ROOT, "tools", "cache", "npcs.json"), encoding="utf-8"))
    images = known_images()
    failed = 0
    for path in args:
        errors, warnings = validate(path, images, npcs)
        name = os.path.basename(path)
        print(("FAIL " if errors else "OK   ") + name)
        for e in errors:
            print("   error:", e)
        for w in warnings:
            print("   warn:", w)
        failed += bool(errors)
    print(f"{len(args) - failed}/{len(args)} passed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
