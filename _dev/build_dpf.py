"""Perfil de dano recebido por vocação e faixa de nível (G.dpf), para os sets sem hunt (BiS do Início, Equipamento, notas).

    python -I _dev/build_dpf.py [raiz] [--dry]

Para cada vocação, faz a média do perfil de dano das hunts que o G.hunts dá a essa vocação em cada faixa de nível
(a mesma conta do huntProfile do site: data/crdmg.json, criaturas do mapa G.pm com a quantidade, peso √XP). Grava
G.dpf = {vocação: [[nível máximo da faixa, {elemento: parte do dano}], …]} com save_G; uma faixa com menos de 10 hunts
junta-se à anterior. Volta a correr quando mudarem as hunts ou o crdmg.json.
"""
import json
import math
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gjson import default_root, load_G, save_G  # noqa: E402

BANDS = [99, 199, 299, 399, 599, 99999]
VOCS = ['knight', 'paladin', 'sorcerer', 'druid', 'monk']


def profile(G, CR, pid):
    pm = (G['pm'].get(pid) or {}).get('h') or []
    lst = pm if pm else [[str(k).lower(), 1] for k in (G['places'].get(pid) or {}).get('mons', [])]
    acc, tot = Counter(), 0.0
    for k, n in lst:
        r = CR.get(k)
        if not r:
            continue
        d = r.get('d') or {e: 1 for e in (r.get('u') or [])}
        if not d:
            continue
        mx = max(d.values()) or 1
        w = (n or 1) * math.sqrt((G['mon'].get(k) or [0, 0, 100])[2] or 100)
        for e, v in d.items():
            acc[e] += w * v / mx
            tot += w * v / mx
    return {e: v / tot for e, v in acc.items()} if tot else None


def main(argv):
    args = [a for a in argv if not a.startswith('--')]
    root = args[0] if args else default_root()
    s, G, span = load_G(root)
    CR = json.load(open(os.path.join(root, 'data', 'crdmg.json'), encoding='utf-8'))
    out = {}
    for voc in VOCS:
        rows, lo, bands = G['hunts'][voc], 0, []
        acc, n = Counter(), 0
        for hi in BANDS:
            for r in rows:
                if r.get('c') and lo <= (r.get('l') or 0) <= hi:
                    p = profile(G, CR, r['c'])
                    if p:
                        n += 1
                        acc.update(p)
            lo = hi + 1
            if n < 10 and hi != BANDS[-1]:
                continue  # poucas hunts: juntam-se à faixa seguinte
            if not n:
                continue
            avg = {e: v / n for e, v in acc.items() if v / n >= 0.01}
            t = sum(avg.values())
            bands.append([hi, {e: round(v / t, 3) for e, v in sorted(avg.items(), key=lambda x: -x[1])}, n])
            acc, n = Counter(), 0
        out[voc] = [[hi, p] for hi, p, _ in bands]
        for hi, p, k in bands:
            print('%-8s até %5d (%3d hunts): %s' % (voc, hi, k, ', '.join('%s %.0f%%' % (e, v * 100) for e, v in p.items())))
    if '--dry' in argv:
        return 0
    G['dpf'] = out
    save_G(root, s, G, span)
    print('G.dpf gravado')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
