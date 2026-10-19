"""Compara o XP/h e o lucro/h das linhas de G.hunts com o TibiaPal (r6-t2; a partir do audit-hunts da ronda r6).

Só entram as linhas medidas pelo TibiaPal: sem f (preenchida), sem w (TibiaWiki) e sem o (número do TibiaPal de antes do
rebalance de junho de 2026, que a página atual já não mostra). Cada linha tem de ter par (vocação, place, nível) no TibiaPal
de lote16/dl/tp_rows.json com o mesmo XP e o mesmo lucro ('-' no TibiaPal = sem número).

Uso: python -I tp_xp_check.py [raiz do site | G.json] [--tp tp_rows.json]
  Sem argumento: a pasta-mãe de _dev quando o script está em _dev, senão C:\\xampp\\htdocs\\grimorio (como o gjson.py).
  Sai com 0 quando diz '0 linhas diferentes', senão com 1."""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True
from gjson import load_G, default_root  # noqa: E402

TP = r'C:\xampp\_work\hunts\lote16\dl\tp_rows.json'
SEC = ['knight', 'paladin', 'monk', 'sorcerer', 'druid', 'team']


def num(s):
    s = s.strip().lower().replace(',', '.')
    if s in ('-', '', '?'):
        return None
    m = re.match(r'^(-?[\d.]+)\s*(kk|k)?$', s)
    if not m:
        return 'X'
    v = float(m.group(1))
    return v * (1e6 if m.group(2) == 'kk' else 1e3 if m.group(2) == 'k' else 1)


def load(arg):
    if arg and os.path.isfile(arg):
        with open(arg, encoding='utf-8') as f:
            return json.load(f)
    return load_G(arg or default_root())[1]


def main(argv):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    tp_path = TP
    if '--tp' in argv:
        i = argv.index('--tp')
        tp_path = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    args = [a for a in argv if not a.startswith('--')]
    G = load(args[0] if args else None)
    with open(tp_path, encoding='utf-8') as f:
        d = json.load(f)
    sec, tp = -1, {}
    for _, r in d:
        if r and r[0] == 'Level':
            sec += 1
            continue
        if sec < 0 or SEC[sec] == 'team':
            continue
        tp.setdefault((SEC[sec], r[1], int(re.sub(r'\D', '', r[0]))), []).append((num(r[2]), num(r[3])))
    n = old = 0
    for v in G['hunts']:
        for r in G['hunts'][v]:
            if r.get('f') or r.get('w'):
                continue
            if r.get('o'):
                old += 1
                continue
            k = (v, r['place'], r['l'])
            if k not in tp:
                print('SEM PAR', k)
                n += 1
                continue
            if not any(x == r.get('xp') and lo == r.get('lo') for x, lo in tp[k]):
                n += 1
                print(f"{v:8s} {r['place']:42s} {r['l']:5d} G xp={r.get('xp')} lo={r.get('lo')}  TibiaPal={tp[k]}")
    print(n, 'linhas diferentes', f'({old} linhas com o:1 ficaram de fora)')
    return 0 if n == 0 else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
