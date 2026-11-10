"""Gera data/caminhos.json: o caminho de cada hunt e de cada boss (troços, passos, pontos, NPCs, pré-requisitos).

python3 -I _dev/build_caminhos.py [raiz]            grava
python3 -I _dev/build_caminhos.py [raiz] --check    sai com 1 se o ficheiro estiver desatualizado ou a validação falhar
python3 -I _dev/build_caminhos.py [raiz] --report   conta por estado, passos com ponto e com NPC
python3 -I _dev/build_caminhos.py [raiz] --lote N [--tam 25] [--tipo h|b] [--estado none,part,rev,ok]
                                                    N-ésimo grupo de chaves sem entrada no manual (parte C)

Origem, por ordem: _dev/caminhos_manual.json (à mão, tem prioridade) › G.hv › G.routes › p.acc (fica 'none').
As fichas de locais do Questski (data/hunt-access.json e data/boss-access.json, feitos a partir de
quests/data/places.json) entram como 1.º troço por referência. Nunca inventa passos nem deduz caminhos.
Formato: secção «Modelo de dados» de docs/superpowers/specs/2026-11-10-fichas-hunts-bosses-design.md.
"""
import datetime
import json
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from gjson import load_G
from build_guias import key as gkey   # a mesma normalização do gKey() do index.html

ST = ("ok", "rev", "part", "none")
PRE_K = ("quest", "level", "premium", "item", "text")
COORD = r"~?(\d{5}),\s*(\d{5})(?:,\s*(\d{1,2})\b)?"
AREA = r"~?\d{5}[-–]\d{5},\s*\d{5}[-–]\d{5}"                         # «32738-32767, 31264-31301»: zona, não ponto
DROP_RQ = re.compile(r"^sem |não necess|nenhum", re.I)       # como o vRoute
ITEM = re.compile(r"^(?i:pá|corda|picareta|pick|óleo|machete|balde|vial de sangue|helmet of the deep)$"
                  r"|^\d+\s*×?\s*[A-Z][A-Za-z' ]+$|×")
DLG = re.compile(r":\s*(?=['\"]?hi\b)", re.I)                  # «<Nome>: hi, a, b»
SPLIT = re.compile(r"\s*(?:→|->|;\s*depois\b)\s*")


def ok_c(c):
    return (isinstance(c, list) and len(c) == 3 and all(isinstance(v, int) for v in c)
            and 31000 < c[0] < 34500 and 30900 < c[1] < 33100 and 0 <= c[2] <= 15)


class Ctx:
    def __init__(self, root):
        def read(p):
            return json.loads((root / p).read_text(encoding="utf-8"))
        self.root = root
        s, self.G, _ = load_G(str(root))
        self.cities = [c[0] for c in json.loads(re.search(r"const CITIES=(\[.*?\]);", s).group(1))]
        self.hacc, self.bacc = read("data/hunt-access.json"), read("data/boss-access.json")
        self.bosses = read("data/bosses.json")["b"]
        self.npcs = read("data/npcs.json")
        self.guias = read("data/guias.json")
        self.manual = read("_dev/caminhos_manual.json")
        self.slugs = {g[0] for g in self.guias["g"]}
        self.qid = {}
        for q in self.G["quests"]:
            for n in (q["n"], q.get("w")):
                if n:
                    self.qid.setdefault(gkey(n), q["id"])
        self.qname = {q["id"]: q["n"] for q in self.G["quests"]}
        self.names = sorted((v["n"] for v in self.npcs.values() if v["n"].strip(". ")), key=len, reverse=True)
        self.secs = {}

    def sections(self, slug):
        if slug not in self.secs:
            p = self.root / "quests/data/quests" / (slug + ".json")
            self.secs[slug] = len(json.loads(p.read_text(encoding="utf-8")).get("sections", [])) if p.exists() else 0
        return self.secs[slug]

    def npc_pos(self, n):
        v = self.npcs.get(n.lower())
        c = v and [v.get("x"), v.get("y"), v.get("z")]
        return c if ok_c(c) else None

    # --- NPCs -------------------------------------------------------------------------------------------
    def npc_name(self, head):
        bare = re.sub(r"\([^)]*\)", " ", head)
        words = bare.split()
        for i in range(len(words)):                     # o maior sufixo antes dos dois pontos
            cand = " ".join(words[i:]).strip(" .,;:'\"*")
            if cand and cand[0].isupper() and cand.lower() in self.npcs:
                return self.npcs[cand.lower()]["n"]
        best = None                                     # senão, o nome mais comprido no texto (o último, se empatar)
        for n in self.names:
            if best and len(n) < len(best[0]):
                break
            for m in re.finditer(r"(?<!\w)" + re.escape(n) + r"(?!\w)", head):
                if not best or m.start() > best[1]:
                    best = (n, m.start())
        return best and best[0]

    def npc_of(self, t):
        if "{key:" in t:                                # marcação do Questski: {npc:X} {key:hi}, {key:a}…
            for m in re.finditer(r"\{npc:([^}|]+)[^}]*\}[^{}]{0,30}?((?:\{key:[^}]+\}(?:\s*,\s*|\s+e\s+)?)+)", t):
                say = [k.strip() for k in re.findall(r"\{key:([^}|]+)", m.group(2))]
                # a lista tem de acabar nas teclas: «{key:hi}, nome da cidade, {key:yes}» não se lê como falas
                if say[0].lower() == "hi" and m.group(1).strip().lower() in self.npcs and not re.search(r",\s*$", m.group(2)):
                    break
            else:
                return None
            gp = re.match(r"[^.;{]*?\((\d[\d.]*)\s*gp\)", t[m.end():])
            return {"n": self.npcs[m.group(1).strip().lower()]["n"], "say": say,
                    "gp": int(gp.group(1).replace(".", "")) if gp else None}
        m = DLG.search(t)
        if not m:
            return None
        name = self.npc_name(t[:m.start()])
        if not name:
            return None
        rest = t[m.end():]
        if rest[:1] in "'\"":
            cut = re.split(r"\s*(?:\(|;| — | e (?!['\"]))", rest)[0]
            say = [w.strip() for x in re.findall(r"['\"]([^'\"]+)['\"]", cut) for w in x.split(",") if w.strip()]
        else:
            cut = re.split(r"\s*(?:\(|\)|;|·|→|->| — | e | ou |\.(?:\s|$))", rest)[0]
            say = [w.strip(" .'\"") for w in cut.split(",") if w.strip(" .'\"")]
        gp = re.search(r"(\d[\d.]*)\s*gp\b", re.split(r";|→|->| — ", rest)[0])
        return {"n": name, "say": say, "gp": int(gp.group(1).replace(".", "")) if gp else None} if say else None

    # --- passos -----------------------------------------------------------------------------------------
    def steps(self, texts, z0):
        """Texto livre (G.hv, G.routes, p.acc) → [Passo]: tira as coordenadas para c e lê o diálogo do NPC."""
        zf = lambda z: "térreo" if int(z) == 7 else ("+" if int(z) < 7 else "−") + str(abs(int(z) - 7))
        out = []
        for raw in texts:
            if not raw or not raw.strip() or re.search(r"map_point|auto_route|canary", raw, re.I):
                continue
            parts, start = [], 0                       # «A: … → B: …» parte-se em dois passos
            for m in SPLIT.finditer(raw):
                if DLG.search(raw[start:m.start()]) and DLG.search(raw[m.end():]):
                    parts.append(raw[start:m.start()])
                    start = m.end()
            parts.append(raw[start:])
            for t in parts:
                t = re.sub(r"\s*\(z=[^)]*\)", "", t)
                t = re.sub(r"\s*\(x [\d–-]+, y [\d–-]+\)", "", t)
                t = re.sub(r"\b(?:pisos\s+)?z=(\d+)-(\d+)", lambda m: f"pisos {zf(m[1])} a {zf(m[2])}", t)
                area = re.search(AREA, t)
                t = re.sub(r"\s*\(\s*" + AREA + r"\s*\)|\s*" + AREA, "", t)
                m = re.search(COORD, t)
                c = [int(m[1]), int(m[2]), int(m[3]) if m[3] else z0] if m else None
                t = re.sub(r"\s*\(\s*(?:cerca de\s*)?" + COORD + r"\s*(?:aprox\.?)?\s*\)", "", t)
                t = re.sub(r",\s*(?:cerca de\s*)?" + COORD + r"(?=\s*\))", "", t)
                t = re.sub(r"(?<=\()\s*" + COORD + r"\s*,\s*", "", t)
                t = re.sub(r"\s*(?:\bcerca de|\bem)?\s*" + COORD, "", t)
                if m or area:                                   # o que a coordenada deixa pendurado: «perto de», «(≈)»
                    t = re.sub(r"\(\s*(?:≈|~|ou|aprox\.?)?\s*\)", "", t)
                    t = re.sub(r"\s+(?:perto de|à volta de|em torno de|a partir de|em|até|de|a)(?=\s*(?:[,.;:)]|$))"
                               r"|\s+(?:perto de|à volta de|em torno de|a partir de|em|até)(?=\s(?:e|ou)\s|\s\()", "", t)
                t = re.sub(r"\s+([,.;:)])", r"\1", re.sub(r"\s{2,}", " ", t)).strip(" ,;")
                if not t:
                    continue
                npc = self.npc_of(t)
                if npc and (not ok_c(c) or not m[3]):        # sem andar no texto, a posição do NPC é mais segura
                    c = self.npc_pos(npc["n"]) or c
                out.append({"s": t, "c": c if ok_c(c) else None, "npc": npc})
        return out

    def place_steps(self, texts):
        """Passos das fichas de locais: o texto fica igual; o 1.º {coord:} vai também para c."""
        out = []
        for t in texts or []:
            m = re.search(r"\{coord:(\d+),(\d+),(\d+)", t)
            npc = self.npc_of(t)
            c = [int(m[1]), int(m[2]), int(m[3])] if m else None
            if not ok_c(c):
                c = self.npc_pos(npc["n"]) if npc else None
            out.append({"s": t, "c": c, "npc": npc})
        return out

    def place(self, p):
        return {"title": p["title"], "entrance": p.get("entrance"), "arrive": self.place_steps(p.get("arrive")),
                "leave": self.place_steps(p.get("leave")), "warnings": p.get("warnings") or []}

    # --- pré-requisitos ---------------------------------------------------------------------------------
    def quest(self, n, qid=None, note=None):
        # o nome inteiro; depois sem parênteses; depois a parte antes de « — » ou «, » («Grimvale – An Ancient Feud»)
        cands = [n] + [re.split(r"\s+[–—-]\s+|,\s", n)[0]]
        cands = [gkey(x) for c in cands for x in (c, re.sub(r"\s*\(.*$", "", c), re.sub(r"\s+(iniciada|concluída|acabada)$", "", c))]
        qid = qid or next((self.qid[c] for c in cands if c in self.qid), None)
        slug = self.guias["q2s"].get(qid) or next((self.guias["n2s"][c] for c in cands if c in self.guias["n2s"]), None)
        return {"k": "quest", "n": n, "id": qid, "slug": slug, "sec": None, "note": note}

    def pre_of(self, r):
        r = re.sub(r"\s*\((?:a )?wiki[^)]*\)", "", r, flags=re.I).strip()
        if not r or DROP_RQ.search(r):
            return None
        if re.match(r"^(conta )?premium$", r, re.I):
            return {"k": "premium"}
        m = re.match(r"^Nível ~?(\d+)", r)
        if m:
            return {"k": "level", "n": int(m[1]), "rec": "recomendado" in r.lower()}
        m = re.match(r"^Quest:\s*([^()]+?)\s*\(((?:[^()]|\([^()]*\))*)\)$", r) or re.match(r"^Quest:\s*(.+)()$", r)
        if m:
            return self.quest(m[1].strip(), note=m[2] or None)
        if ITEM.search(r):
            return {"k": "item", "n": r}
        return {"k": "text", "s": r}

    @staticmethod
    def add_pre(pre, p):
        if not p:
            return
        if p["k"] == "quest":
            if any(x["k"] == "quest" and ((p["id"] and x["id"] == p["id"]) or (p["slug"] and x["slug"] == p["slug"])
                                          or x["n"] == p["n"]) for x in pre):
                return
        elif p in pre:
            return
        pre.append(p)

    # --- caminhos ---------------------------------------------------------------------------------------
    def from_of(self, legs, places):
        first = None
        for l in legs:
            ss = places[l["ref"]]["arrive"] if "ref" in l else l["steps"]
            if ss:
                first = ss[0]["s"]
                break
        for c in self.cities if first else []:
            if re.search(r"(?<!\w)" + re.escape(c) + r"(?!\w)", first):
                return c
        return None

    def with_places(self, names, acc, legs, places, pre=None):
        refs = []
        for n in names:
            p = self.place(acc["places"][n])
            if places.setdefault(n, p) != p:
                raise SystemExit(f"ficha de local diferente nos dois índices: {n}")
            refs.append({"ref": n})
            for r in acc["places"][n].get("requirements") or [] if pre is not None else []:
                self.add_pre(pre, {"k": "text", "s": r})
        return refs + legs

    def hunt(self, pid, p, places):
        hm = self.G["hm"].get(pid)
        pos = [int(v) for v in hm[:3]] if hm else None
        pos = pos if ok_c(pos) else None
        z0 = pos[2] if pos else 7
        hv, rt = self.G["hv"].get(pid) or {}, self.G["routes"].get(pid)
        pre, frm, st, legs = [], None, "none", []
        for r in hv.get("rq") or []:
            self.add_pre(pre, self.pre_of(r))
        steps = self.steps(([hv["t"]] if hv.get("t") else []) + hv["st"], z0) if hv.get("st") else []
        if steps:
            st = {"ok": "ok", "fix": "rev"}.get(hv.get("v"), "part")
        elif rt:
            de, travel, ss, req = rt
            steps = self.steps(([travel] if travel else []) + ss, z0)
            if steps:
                st, frm = "part", de or None
            r = (req or "").strip()
            if r and not DROP_RQ.search(r):
                self.add_pre(pre, {"k": "text", "s": r})
        if steps:
            legs = [{"t": "Caminho", "steps": steps}]
        else:
            legs = [{"t": "O que se sabe", "steps": self.steps([p.get("acc") or p["n"]], z0)}]
        names = self.hacc["h"].get(pid) or []
        legs = self.with_places(names, self.hacc, legs, places, pre)
        if names and st == "none":
            st = "part"
        q = p.get("q")
        for qid in (self.G.get("marapur") or []) if q == "marapur" else [q] if q else []:
            self.add_pre(pre, self.quest(self.qname.get(qid, qid), qid))
        if p.get("prem"):
            self.add_pre(pre, {"k": "premium"})
        return {"st": st, "from": frm or self.from_of(legs, places) or p.get("city") or None, "pos": pos,
                "pa": 1 if hm and len(hm) > 3 and hm[3] == "a" else 0, "pre": pre, "legs": legs, "refs": []}

    def boss(self, k, b, places):
        pos = b.get("pos") if ok_c(b.get("pos")) else None
        pre = []
        if b.get("q"):
            self.add_pre(pre, self.quest(b["q"]))
        if b.get("ql"):
            self.add_pre(pre, {"k": "level", "n": b["ql"], "rec": False})
        if b.get("qr") and b.get("qr") != b.get("ql"):
            self.add_pre(pre, {"k": "level", "n": b["qr"], "rec": True})
        acc = self.bacc["b"].get(k) or {}
        legs = self.with_places(acc.get("places") or [], self.bacc, [], places)   # pre dos bosses: só q/ql/qr
        refs = [{"slug": g["slug"], "sec": g["section"], "t": g["title"], "quest": g["quest"]} for g in acc.get("guides") or []]
        st = "part" if legs or refs else "none"
        if st == "none" and b.get("loc"):
            legs = [{"t": "O que se sabe", "steps": self.steps(["Fica em " + ", ".join(b["loc"]) + "."], pos[2] if pos else 7)}]
        return {"st": st, "from": self.from_of(legs, places), "pos": pos, "pa": 1 if b.get("pa") else 0,
                "pre": pre, "legs": legs, "refs": refs}


def build(cx):
    places, h, b = {}, {}, {}
    for pid, p in cx.G["places"].items():
        h[pid] = cx.manual["h"][pid] if pid in cx.manual["h"] else cx.hunt(pid, p, places)
    for k, v in cx.bosses.items():
        b[k] = cx.manual["b"][k] if k in cx.manual["b"] else cx.boss(k, v, places)
    return {"v": 1, "h": h, "b": b, "places": places}


def validate(cx, d):
    err = []

    def step(where, s):
        if not isinstance(s.get("s"), str) or not s["s"].strip():
            err.append(where + ": passo vazio")
            return
        if not (s.get("c") is None or ok_c(s["c"])):
            err.append(where + ": ponto inválido")
        if re.search(r"\(\d{5},\s*\d{5}", s["s"]):
            err.append(where + ": coordenada no texto: " + s["s"])
        n = s.get("npc")
        if n and (not isinstance(n.get("n"), str) or n["n"].lower() not in cx.npcs or not n.get("say")):
            err.append(where + ": NPC desconhecido ou sem falas: " + str(n))

    def guide(where, slug, sec):
        if slug is not None and slug not in cx.slugs:
            err.append(where + ": guia desconhecido " + slug)
        elif sec is not None and not (slug and isinstance(sec, int) and 0 <= sec < cx.sections(slug)):
            err.append(where + f": secção inválida {slug} {sec}")

    if set(d["h"]) != set(cx.G["places"]):
        err.append("h não tem as mesmas chaves que G.places")
    if set(d["b"]) != set(cx.bosses):
        err.append("b não tem as mesmas chaves que data/bosses.json")
    for n, p in d["places"].items():
        for i, s in enumerate(p["arrive"] + p["leave"]):
            step(f"places[{n}] {i}", s)
    for kind in ("h", "b"):
        for k, c in d[kind].items():
            w = f"{kind}.{k}"
            if c.get("st") not in ST:
                err.append(w + ": estado inválido")
            if not (c.get("pos") is None or ok_c(c["pos"])) or c.get("pa") not in (0, 1):
                err.append(w + ": pos/pa inválidos")
            if not isinstance(c.get("pre"), list) or not isinstance(c.get("legs"), list):
                err.append(w + ": pre/legs em falta")
                continue
            for p in c["pre"]:
                if p.get("k") not in PRE_K:
                    err.append(w + ": pré-requisito inválido " + str(p))
                elif p["k"] == "quest":
                    guide(w, p.get("slug"), p.get("sec"))
            for i, l in enumerate(c["legs"]):
                if "ref" in l:
                    if l["ref"] not in d["places"]:
                        err.append(w + ": ref sem local " + str(l["ref"]))
                elif not l.get("t") or not l.get("steps"):
                    err.append(w + f": troço {i} vazio")
                else:
                    for j, s in enumerate(l["steps"]):
                        step(f"{w} {i}.{j}", s)
            for r in c.get("refs") or []:
                guide(w + " refs", r.get("slug"), r.get("sec"))
            if c["st"] == "none" and len(c["legs"]) > 1:
                err.append(w + ": none com passos")
    return err


def dump(d):
    return json.dumps(d, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"


def report(cx, d):
    for kind, lab in (("h", "hunts"), ("b", "bosses")):
        cs = d[kind].values()
        n = {s: sum(c["st"] == s for c in cs) for s in ST}
        ss = [s for c in cs for l in c["legs"] for s in (d["places"][l["ref"]]["arrive"] if "ref" in l else l["steps"])]
        man = sum(k in cx.manual[kind] for k in d[kind])
        print(f"{lab}: {len(d[kind])} · " + " · ".join(f"{s} {n[s]}" for s in ST)
              + f" · manual {man} · passos {len(ss)} (com ponto {sum(bool(s['c']) for s in ss)},"
              f" com NPC {sum(bool(s['npc']) for s in ss)}) · com ficha de local"
              f" {sum(any('ref' in l for l in c['legs']) for c in cs)}")
    print(f"locais: {len(d['places'])} · {len(dump(d).encode()) // 1024} KB")


def lote(cx, d, argv):
    def opt(name, default):
        return argv[argv.index(name) + 1] if name in argv else default
    n, tam, kind = int(opt("--lote", "1")), int(opt("--tam", "25")), opt("--tipo", "h")
    est = set(opt("--estado", ",".join(ST)).split(","))
    keys = [k for k, c in d[kind].items() if k not in cx.manual[kind] and c["st"] in est]
    if kind == "h":
        lv = {}
        for rows in cx.G["hunts"].values():
            for r in rows:
                lv[r["c"]] = min(lv.get(r["c"], 10 ** 6), r.get("l") or 0)
        keys.sort(key=lambda k: (lv.get(k, 10 ** 6), k))
        info = lambda k: f'{lv.get(k, "-")}\t{cx.G["places"][k]["n"]}'
    else:
        keys.sort(key=lambda k: (cx.bosses[k].get("qr") is None, cx.bosses[k].get("qr") or 0, cx.bosses[k]["n"]))
        info = lambda k: f'{cx.bosses[k].get("qr", "-")}\t{cx.bosses[k]["n"]}'
    for k in keys[(n - 1) * tam:n * tam]:
        print(f"{k}\t{d[kind][k]['st']}\t{info(k)}")


def main():
    argv = sys.argv[1:]
    args = [a for i, a in enumerate(argv) if not a.startswith("--") and not (i and argv[i - 1] in ("--lote", "--tam", "--tipo", "--estado"))]
    root = Path(args[0]).resolve() if args else Path(__file__).resolve().parents[1]
    cx = Ctx(root)
    d = build(cx)
    err = validate(cx, d)
    target = root / "data/caminhos.json"
    old = json.loads(target.read_text(encoding="utf-8")) if target.exists() else None
    # gen só muda quando o conteúdo muda, para o --check não falhar no dia seguinte
    d["gen"] = old["gen"] if old and dump({**old, "gen": ""}) == dump({**d, "gen": ""}) else datetime.date.today().isoformat()
    text = dump(d)
    # só as fichas de locais do Questski já têm ~420 KB; o ficheiro substitui o hunt-access e o boss-access (~650 KB)
    if len(text.encode()) >= 1024 * 1024:
        err.append(f"caminhos.json com {len(text.encode()) // 1024} KB (máximo 1024)")
    if err:
        sys.exit("validação falhou:\n  " + "\n  ".join(err[:50]) + (f"\n  … e mais {len(err) - 50}" if len(err) > 50 else ""))
    if "--report" in argv:
        report(cx, d)
    elif "--lote" in argv:
        lote(cx, d, argv)
    elif "--check" in argv:
        if not target.exists() or target.read_text(encoding="utf-8") != text:
            sys.exit("caminhos.json desatualizado")
        print("caminhos.json em dia")
    else:
        target.write_text(text, encoding="utf-8", newline="")
        report(cx, d)


if __name__ == "__main__":
    main()
