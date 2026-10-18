"""Gera data/search.json (índice global de pesquisa) a partir dos ficheiros de dados do Grimório.
Uso: python -I C:\\xampp\\_tools\\build_search.py [raiz do site]   (por omissão C:\\xampp\\htdocs\\grimorio)
Formato: {"v":1,"d":"AAAA-MM-DD","e":[[cat,key,nome,sub(,sinónimos)], ...]}  (sinónimos: palavras mágicas dos feitiços/runas)
cat: i item, c criatura, b boss, s feitiço, r runa, n NPC, a conquista, m montaria, o outfit, q quest.
As hunts, quests do G, charms e imbuements são indexados no browser a partir do JSON embebido."""
import json, os, re, sys, datetime

ROOT = sys.argv[1] if len(sys.argv) > 1 else r'C:\xampp\htdocs\grimorio'
D = os.path.join(ROOT, 'data')


def load(n):
    p = os.path.join(D, n + '.json')
    if not os.path.exists(p):
        return {}
    with open(p, encoding='utf-8') as f:
        return json.load(f)


def nf(n):
    try:
        return f'{int(round(float(n))):,}'.replace(',', ' ')
    except Exception:
        return str(n)


# tradução das classes dos itens (a mesma do site)
html = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
m = re.search(r'const CLS_IT=(\{.*?\});', html)
CLS = {}
if m:
    try:
        CLS = json.loads(m.group(1))
    except Exception:
        CLS = {}
VOC = {'knight': 'knight', 'paladin': 'paladin', 'sorcerer': 'sorcerer', 'druid': 'druid', 'monk': 'monk'}
GRP = {'attack': 'ataque', 'healing': 'cura', 'support': 'apoio'}

E = []
for k, it in load('items').items():
    n = it.get('t') or k
    E.append(['i', k, n, CLS.get(it.get('cls'), it.get('cls') or 'Item')])
for k, c in load('creatures').items():
    n = c.get('n') or k
    if c.get('boss'):
        E.append(['b', k, n[:1].upper() + n[1:], f"Boss{' · ' + nf(c['hp']) + ' de vida' if c.get('hp') else ''}"])
    else:
        E.append(['c', k, n[:1].upper() + n[1:], f"Criatura{' · ' + nf(c['xp']) + ' XP' if c.get('xp') else ''}"])
for k, s in load('spells').items():
    vs = ', '.join(VOC.get(v, v) for v in (s.get('v') or []))
    if s.get('t') == 'r':
        E.append(['r', k, s.get('rn') or s.get('n') or k, f"Runa · {s.get('w') or ''} · nível {s.get('l') or 0}", f"{s.get('n') or ''} {s.get('w') or ''}".strip()])
    else:
        E.append(['s', k, s.get('n') or k, f"{s.get('w') or 'Feitiço'} · {GRP.get(s.get('g'), s.get('g') or 'apoio')} · {vs} · nível {s.get('l') or 0}", s.get('w') or ''])
for k, o in load('npcs').items():
    n = o.get('n') or o.get('t') or k
    E.append(['n', k, n, ' · '.join(x for x in [o.get('job'), o.get('city')] if x) or 'NPC'])
for k, a in load('achievements').items():
    E.append(['a', k, a.get('n') or k, f"Conquista · {a.get('pts', 0)} {'ponto' if a.get('pts') == 1 else 'pontos'}{' · secreta' if a.get('secret') else ''}"])
for k, mo in load('mounts').items():
    E.append(['m', k, mo.get('n') or k, f"Montaria{' · ' + mo['src'] if mo.get('src') else ''}"])
for k, o in load('outfits').items():
    E.append(['o', k, o.get('n') or k, f"Outfit{' · ' + o['type'] if o.get('type') else ''}"])
for k, q in load('quests').items():
    E.append(['q', k.lower(), k, f"Quest{' · nível ' + str(q['lvl']) if q.get('lvl') else ''}"])

E = [e for e in E if e[2]]
E.sort(key=lambda e: (e[0], e[2].lower()))
out = {'v': 1, 'd': datetime.date.today().isoformat(), 'e': E}
p = os.path.join(D, 'search.json')
with open(p, 'w', encoding='utf-8', newline='') as f:
    json.dump(out, f, ensure_ascii=False, separators=(',', ':'))
from collections import Counter
print(p, os.path.getsize(p), 'bytes', dict(Counter(e[0] for e in E)))
for w in ['gold', 'dragon', 'exura']:
    print(w, dict(Counter(e[0] for e in E if w in (e[2]+' '+(e[4] if len(e)>4 else '')).lower())))
