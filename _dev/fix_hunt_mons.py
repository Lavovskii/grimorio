"""Corrige G.pm[pid].h (criaturas e quantidades de cada hunt) para usar os monstros curados de G.places[pid].mons.
As áreas do mapa apanhavam criaturas de passagem (ex.: Demonwar Crypt com wild warriors e priestesses no topo).
Quantidade: a do mapa se > 0; senão a soma dos spawns dessa criatura perto da hunt (data/spawns.json); senão 1.
Uso: python -I fix_hunt_mons.py [raiz do site]"""
import json, re, sys, math
ROOT = sys.argv[1] if len(sys.argv) > 1 else r'C:\xampp\htdocs\grimorio'
P = ROOT + r'\index.html'
s = open(P, encoding='utf-8').read()
m = re.search(r'(<script[^>]*id="G"[^>]*>)(.*?)(</script>)', s, re.S)
raw = m.group(2)
G = json.loads(raw)
sp = json.load(open(ROOT + r'\data\spawns.json', encoding='utf-8'))
log = open(r'C:\xampp\_work\fix_hunt_mons.log', 'w', encoding='utf-8')
alias = {}
for k, v in G['mon'].items():
    alias.setdefault(str(v[0]).lower(), k)
for k in G['mon']:
    alias[k] = k  # a chave exata ganha (há duplicados do tipo 'carrion_worm')


def key_of(name):
    n = str(name).strip().lower()
    for c in (n, n.rstrip('s'), n[:-2] if n.endswith('es') else n, re.sub(r'\s*\(.*\)$', '', n)):
        if c in alias:
            return alias[c]
    return None


def near(k, hm, R=80):
    if not hm or k not in sp:
        return 0
    x, y, z = hm[0], hm[1], hm[2]
    t = 0
    for cl in sp[k]:
        if abs(cl[2] - z) <= 2 and math.hypot(cl[0] - x, cl[1] - y) <= R:
            t += cl[3]
    return t


changed = 0
missing = set()
for pid, p in G['places'].items():
    mons = [x for x in (p.get('mons') or []) if x]
    if not mons:
        continue
    pm = G['pm'].setdefault(pid, {})
    old = pm.get('h') or []
    cnt = {k: c for k, c in old}
    hm = G['hm'].get(pid)
    new, seen = [], set()
    for nm in mons:
        k = key_of(nm)
        if not k:
            missing.add(nm)
            continue
        if k in seen:
            continue
        seen.add(k)
        c = cnt.get(k, 0) or near(k, hm)
        new.append([k, c])
    if not new:
        continue
    nz = [c for _, c in new if c > 0]
    fill = max(1, min(nz)) if nz else 1
    new = [[k, c if c > 0 else fill] for k, c in new]
    # criaturas do mapa que não estão na lista curada só ficam se forem dominantes (mais do que qualquer curada)
    top = max(c for _, c in new)
    for k, c in old:
        if k not in seen and c > top and k in G['mon'] and G['mon'][k][2] > 0:
            new.append([k, c]); seen.add(k)
    new.sort(key=lambda x: -x[1])
    if [k for k, _ in old if _ > 0][:3] != [k for k, _ in new][:3]:
        changed += 1
        log.write(f"{pid} | {p['n']}\n  antes: {[(k, c) for k, c in old][:6]}\n  depois: {new[:6]}\n")
    pm['h'] = new
log.write(f"\nnomes curados sem criatura em G.mon: {sorted(missing)}\n")
log.close()
out = json.dumps(G, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
s = s[:m.start(2)] + out + s[m.end(2):]
open(P, 'w', encoding='utf-8', newline='').write(s)
print('hunts alteradas:', changed, '| tamanho G antes/depois:', len(raw), len(out), '| nomes sem criatura:', len(missing))
