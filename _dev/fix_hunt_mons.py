"""Corrige G.pm[pid].h (criaturas e quantidades de cada hunt) para usar os monstros curados de G.places[pid].mons.
As áreas do mapa apanhavam criaturas de passagem (ex.: Demonwar Crypt com wild warriors e priestesses no topo).
Quantidade: a do mapa se > 0; senão a soma dos spawns dessa criatura perto da hunt (data/spawns.json); senão 1.
O G lê-se e grava-se com load_G/save_G de gjson.py (ao lado deste script ou em C:\\xampp\\_tools).
O registo (fix_hunt_mons.log) vai para a pasta GRIM_WORK (variável de ambiente) ou para a pasta temporária, só quando há algo a registar.
Uso: python -I fix_hunt_mons.py [raiz do site]"""
import json, re, sys, os, math, tempfile
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), r'C:\xampp\_tools']
sys.dont_write_bytecode = True  # sem __pycache__ dentro do repositório
from gjson import load_G, save_G, default_root

args = [a for a in sys.argv[1:] if not a.startswith('--')]
ROOT = args[0] if args else default_root()
WORK = os.environ.get('GRIM_WORK') or tempfile.gettempdir()
s, G, span = load_G(ROOT)
raw = s[span[0]:span[1]]
sp = json.load(open(os.path.join(ROOT, 'data', 'spawns.json'), encoding='utf-8'))
log = []
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
        log.append(f"{pid} | {p['n']}\n  antes: {[(k, c) for k, c in old][:6]}\n  depois: {new[:6]}\n")
    pm['h'] = new
if missing:
    log.append(f"\nnomes curados sem criatura em G.mon: {sorted(missing)}\n")
LOG = ''
if log:
    LOG = os.path.join(WORK, 'fix_hunt_mons.log')
    with open(LOG, 'w', encoding='utf-8') as f:
        f.write(''.join(log))
s2, span2 = save_G(ROOT, s, G, span)
print('hunts alteradas:', changed, '| tamanho G antes/depois:', len(raw), span2[1] - span2[0], '| nomes sem criatura:', len(missing), '| registo:', LOG or '(nada a registar)')
