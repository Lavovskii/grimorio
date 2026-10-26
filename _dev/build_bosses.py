r"""Gera data/bosses.json: os bosses do Bosstiary (Bane, Archfoe e Nemesis) com o que o site precisa para dizer que bosses
cada personagem pode fazer no seu nível. Dados da TibiaWiki pela API (o mesmo fetch e a mesma cache do build_supplies.py):
- as categorias 'Bane Bosses', 'Archfoe Bosses' e 'Nemesis Bosses' (sem as páginas 'Deprecated');
- a Infobox Creature de cada boss: vida, XP, bosstiaryclass, cooldown (horas), spawntype, maxdmg (dano máximo por turno),
  behaviour (a % de cada elemento no dano que faz), location (só os nomes dos sítios ligados) e a 1.ª quest citada em
  notes/location;
- a Infobox Quest dessa quest: lvl (nível mínimo) e lvlrec (recomendado);
- a página 'Lever Bosses' (os bosses com alavanca: equipa de até 5, normalmente).
O loot e as resistências ficam no data/creatures.json (o site junta-os pela chave, o nome em minúsculas).
Formato: {"v":1, "fontes":…, "pts":{cls:[[kills,pontos]×3]}, "b":{chave:{…}}} com um boss por linha (o Git junta sem conflitos).
Campos de cada boss: n (nome), c ('b' Bane, 'a' Archfoe, 'n' Nemesis), hp, xp, cd (horas; null = desconhecido), sp ('t' por
quest/alavanca, 'r' raid, 'g' spawn normal; null), lv (1 = alavanca), q (quest), ql/qr (nível mínimo/recomendado da quest),
loc ([sítios]), md (dano máximo por turno, sem summons; null = desconhecido), dm ({elemento: %} do dano que faz),
pos ([x, y, z] no mapa: o {{Mapper Coords}} da localização na TibiaWiki; senão o 1.º spawn de data/spawns.json; senão a
entrada do 1.º sítio em quests/data/places.json do Questski, ou o 1.º {{Mapper Coords}} da página desse sítio na
TibiaWiki, e então pa = 1: aproximada, é a zona e não o sítio do boss).
Uso: python -I build_bosses.py [raiz] [--cache PASTA] [--offline] [--check] [--loot]
  --check: não grava; sai com 1 se o ficheiro gerado for diferente do que está no disco.
  --loot: acrescenta também a data/items.json os itens do loot destes bosses que lá faltam (ex.: Gold Token, Silver Token),
          com a mesma Infobox Object e os mesmos NPCs do build_supplies.py, para o site lhes dar preço (NPC e Market). Nunca
          muda uma chave que já existe. Depois: python -I build_search.py."""
import json, os, re, sys, time, urllib.parse, urllib.request

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_supplies as BS  # noqa: E402  (fetch com cache, args e default_root)

CATS = {'b': 'Category:Bane Bosses', 'a': 'Category:Archfoe Bosses', 'n': 'Category:Nemesis Bosses'}
# Bosstiary (TibiaWiki, Template:Bosstiary Table): mortes para Prowess, Expertise e Mastery e os pontos de cada nível
# bosses cuja página não liga à quest de acesso (a quest dá o nível na sua Infobox Quest)
ACCESS = {'Count Vlarkorth': 'Grave Danger Quest', 'Earl Osam': 'Grave Danger Quest', 'Sir Baeloc': 'Grave Danger Quest',
          'Lady Tenebris': 'Forgotten Knowledge Quest', 'Lloyd': 'Forgotten Knowledge Quest', 'The Time Guardian': 'Forgotten Knowledge Quest',
          'Soul of Dragonking Zyrtarch': 'Forgotten Knowledge Quest', 'The Enraged Thorn Knight': 'Forgotten Knowledge Quest',
          'The Last Lore Keeper': 'Forgotten Knowledge Quest', 'Melting Frozen Horror': 'Forgotten Knowledge Quest',
          'Abyssador': "Bigfoot's Burden Quest"}
NOTQ = {'World Quest'}   # 'World Quest' é o nome genérico das quests de mundo (eventos), não uma quest com nível
PTS = {'b': [[25, 5], [100, 15], [300, 30]], 'a': [[5, 10], [20, 30], [60, 60]], 'n': [[1, 10], [3, 30], [5, 60]]}
ELS = {'physical': 'physical', 'fire': 'fire', 'ice': 'ice', 'earth': 'earth', 'energy': 'energy', 'holy': 'holy', 'death': 'death',
       'life drain': 'lifedrain', 'lifedrain': 'lifedrain', 'mana drain': 'manadrain', 'manadrain': 'manadrain', 'drown': 'drown'}


def members(cat, cache, offline):
    """Títulos (ns 0) de uma categoria; cache em disco como as páginas."""
    cf = os.path.join(cache, 'cat_' + re.sub(r'[^A-Za-z0-9._-]+', '_', cat) + '.json')
    if os.path.exists(cf):
        with open(cf, encoding='utf-8') as f:
            return json.load(f)
    if offline:
        sys.exit('sem cache (--offline): ' + cat)
    out, cont = [], {}
    while True:
        p = dict({'action': 'query', 'list': 'categorymembers', 'cmtitle': cat, 'cmlimit': '500', 'format': 'json'}, **cont)
        req = urllib.request.Request(BS.API + '?' + urllib.parse.urlencode(p), headers={'User-Agent': BS.UA})
        time.sleep(BS.PAUSE)
        with urllib.request.urlopen(req, timeout=90) as r:
            d = json.loads(r.read().decode('utf-8'))
        out += [m['title'] for m in d['query']['categorymembers'] if m['ns'] == 0]
        if 'continue' not in d:
            break
        cont = d['continue']
    os.makedirs(cache, exist_ok=True)
    with open(cf, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False)
    return out


def infobox(text, kind):
    """Campos de {{Infobox <kind>|...}}: '| campo = valor' por linha (as linhas seguintes juntam-se ao campo)."""
    i = (text or '').find('{{Infobox ' + kind)
    if i < 0:
        return {}
    f, cur, depth = {}, None, 0
    for line in text[i:].split('\n')[1:]:
        m = re.match(r'^\s*\|\s*([A-Za-z0-9_]+)\s*=[ \t]?(.*)$', line)
        if m and depth <= 0:
            cur = m.group(1).strip().lower(); f[cur] = m.group(2).strip()
            depth = f[cur].count('{{') - f[cur].count('}}')
        elif line.strip() == '}}' and depth <= 0:
            break
        elif cur:
            f[cur] += '\n' + line
            depth += line.count('{{') - line.count('}}')
    return f


def num(s):
    """1.º número de um campo da wiki ('40,000~' → 40000; '?' → None)."""
    m = re.search(r'\d[\d,.]*', str(s or ''))
    if not m:
        return None
    t = m.group(0).replace(',', '')
    try:
        v = float(t)
    except ValueError:
        return None
    return int(v) if v == int(v) else v


def maxdmg(s):
    """Dano máximo por turno: o maior valor da {{Max Damage|...}} sem summons nem drenos de mana; um número solto; None."""
    s = str(s or '').strip()
    if not s or s.startswith('?'):
        return None
    if s.startswith('{{Max Damage'):
        m = re.search(r'\|\s*total\s*=\s*([^|}]*)', s, re.I)
        if m and num(m.group(1)):
            return int(num(m.group(1)))
        vals = []
        for k, v in re.findall(r'\|\s*([a-z ]+?)\s*=\s*([^|}]*)', s, re.I):
            if k.lower() in ('summons', 'manadrain', 'mana drain'):
                continue
            n = num(v)
            if n:
                vals.append(n)
        return int(max(vals)) if vals else None
    n = num(s.split('(')[0])
    return int(n) if n else None


def dmgmix(s):
    """'Deals approximately 70% physical damage, 20% death…' → {'physical': 70, 'death': 20}."""
    out = {}
    for p, e in re.findall(r'(\d{1,3})\s*%\s*(physical|fire|ice|earth|energy|holy|death|life ?drain|mana ?drain|drown)', str(s or ''), re.I):
        k = ELS.get(e.lower().replace('  ', ' '))
        if k and k not in out:
            out[k] = int(p)
    return out if sum(out.values()) >= 50 else {}


def links(s):
    """Nomes das páginas ligadas ([[A|b]] → A), sem ficheiros nem categorias."""
    out = []
    for t in re.findall(r'\[\[([^\]|#]+)', str(s or '')):
        t = t.strip()
        if ':' in t or t in out or not t[:1].isupper():
            continue
        out.append(t)
    return out


MC = re.compile(r'\{\{\s*Mapper Coords\s*\|\s*(\d+)\.(\d+)\s*\|\s*(\d+)\.(\d+)\s*\|\s*(\d+)')


def mapper(s):
    """1.º {{Mapper Coords|x.x|y.y|z|...}} → [x, y, z] (cada coordenada é bloco.casa, 256 casas por bloco)."""
    m = MC.search(str(s or ''))
    return [int(m.group(1)) * 256 + int(m.group(2)), int(m.group(3)) * 256 + int(m.group(4)), int(m.group(5))] if m else None


def places(root):
    """Sítios do Questski com entrada no mapa: nome (e alias) em minúsculas → [x, y, z]."""
    P = json.load(open(os.path.join(root, 'quests', 'data', 'places.json'), encoding='utf-8'))
    out = {}
    for n, v in (P.get('places') or {}).items():
        e = (v or {}).get('entrance') or {}
        if all(isinstance(e.get(k), int) for k in 'xyz'):
            out[n.lower()] = [e['x'], e['y'], e['z']]
    for a, n in (P.get('alias') or {}).items():
        if isinstance(n, str) and n.lower() in out:
            out.setdefault(a.lower(), out[n.lower()])
    return out


def spawn(s):
    s = str(s or '').lower()
    return 't' if 'trigger' in s else 'r' if 'raid' in s else 'g' if 'regular' in s else None


def build(o):
    cache, off = o['cache'], o['offline']
    cls = {}
    for c, cat in CATS.items():
        for t in members(cat, cache, off):
            cls.setdefault(t, c)
    pages = BS.fetch(sorted(cls) + ['Lever Bosses'], cache, off)
    lever = set(links((pages.get('Lever Bosses') or {}).get('content')))
    raw = {}
    quests = set()
    for t, c in cls.items():
        txt = (pages.get(t) or {}).get('content') or ''
        if not txt or re.search(r'\{\{\s*Deprecated|\|\s*deprecated\s*=\s*yes', txt, re.I):
            continue
        f = infobox(txt, 'Creature')
        if not f:
            continue
        q = next((x for x in links(f.get('notes', '') + ' ' + f.get('location', '')) if re.search(r'\bQuest\b', x) and x not in NOTQ), None) or ACCESS.get(t)
        if q:
            quests.add(q)
        raw[t] = (c, f, q)
    qp = BS.fetch(sorted(quests), cache, off)
    qinfo = {}
    for q in quests:
        f = infobox((qp.get(q) or {}).get('content') or '', 'Quest')
        qinfo[q] = (num(f.get('lvl')), num(f.get('lvlrec')))
    crs = json.load(open(os.path.join(o['root'], 'data', 'creatures.json'), encoding='utf-8'))
    sps = json.load(open(os.path.join(o['root'], 'data', 'spawns.json'), encoding='utf-8'))
    pls = places(o['root'])
    # sítios sem entrada no Questski: o 1.º {{Mapper Coords}} da página do sítio na TibiaWiki
    need = sorted({x for t, (c, f, q) in raw.items() if not mapper(f.get('location')) and not sps.get(t.lower())
                   for x in links(f.get('location')) if not re.search(r'\bQuest\b', x) and x.lower() not in pls})
    lp = BS.fetch(need, cache, off)
    for x in need:
        m = mapper((lp.get(x) or {}).get('content'))
        if m:
            pls[x.lower()] = m
    out = {}
    for t, (c, f, q) in sorted(raw.items()):
        k = t.lower()
        cr = crs.get(k) or {}
        ql, qr = qinfo.get(q, (None, None)) if q else (None, None)
        cd = num(f.get('cooldown'))
        e = {'n': f.get('name') or t, 'c': c, 'hp': num(f.get('hp')) or cr.get('hp'), 'xp': num(f.get('exp')) or cr.get('xp'),
             'cd': cd if cd is not None and cd > 0 else None, 'sp': spawn(f.get('spawntype')), 'lv': 1 if t in lever else 0,
             'q': q, 'ql': ql, 'qr': qr,
             'loc': [x for x in links(f.get('location')) if not re.search(r'\bQuest\b', x)][:4],
             'md': maxdmg(f.get('maxdmg')), 'dm': dmgmix(f.get('behaviour'))}
        pos, pa = mapper(f.get('location')), 0
        if not pos and sps.get(k):
            pos = list(sps[k][0][:3])
        if not pos:
            pos = next((pls[x.lower()] for x in e['loc'] if x.lower() in pls), None)
            pa = 1 if pos else 0
        e['pos'], e['pa'] = pos, pa
        out[k] = {x: v for x, v in e.items() if v not in (None, [], {}, 0) or x in ('c', 'n')}
    return {'v': 1, 'fontes': 'TibiaWiki (Infobox Creature, Infobox Quest, Bosstiary e Lever Bosses), outubro de 2026',
            'pts': PTS, 'b': out}


def dump(D):
    lines = ['{', '"v": 1,', '"fontes": ' + json.dumps(D['fontes'], ensure_ascii=False) + ',',
             '"pts": ' + json.dumps(D['pts'], separators=(',', ':')) + ',', '"b": {']
    ks = list(D['b'])
    for i, k in enumerate(ks):
        lines.append(' ' + json.dumps(k, ensure_ascii=False) + ': ' + json.dumps(D['b'][k], ensure_ascii=False, separators=(',', ':')) + (',' if i < len(ks) - 1 else ''))
    lines += ['}', '}']
    return '\n'.join(lines) + '\n'


def add_loot(o, keys):
    """Itens do loot dos bosses (data/creatures.json) que faltam em data/items.json, pelo mesmo caminho do build_supplies."""
    path = os.path.join(o['root'], 'data', 'items.json')
    with open(path, encoding='utf-8', newline='') as f:
        raw = f.read()
    items = json.loads(raw)
    crs = json.load(open(os.path.join(o['root'], 'data', 'creatures.json'), encoding='utf-8'))
    want = sorted({l[0] for k in keys for l in (crs.get(k) or {}).get('loot') or [] if l and l[0] and l[0].lower() not in items
                   and not re.search(r'\((Quest|Deprecated)\)', l[0])})
    print(f'loot dos bosses: {len(want)} itens fora do items.json')
    if not want:
        return 0
    pages = BS.fetch(want + [BS.MODULE], o['cache'], o['offline'])
    tr = BS.trades((pages.get(BS.MODULE) or {}).get('content') or '')
    add, skip = {}, 0
    for t in want:
        e, k = BS.entry(t, pages.get(t), tr)
        if e is None or k != t.lower() or k in items:
            skip += 1; continue
        add[k] = e
    for k, e in add.items():
        items[k] = e
    old = json.loads(raw)
    assert all(json.dumps(items[k], sort_keys=True) == json.dumps(v, sort_keys=True) for k, v in old.items()), 'uma chave antiga mudou'
    with open(path, 'w', encoding='utf-8', newline='') as f:
        f.write(json.dumps(items, ensure_ascii=False, separators=(',', ':')))
    print(f'gravado {path}: +{len(add)} itens ({len(items)} no total); {skip} sem página, sem itemid ou com outro nome na wiki')
    return 0


def main(argv):
    chk = '--check' in argv
    o = BS.args([a for a in argv if a not in ('--check', '--loot')])
    D = build(o)
    txt = dump(D)
    json.loads(txt)
    dst = os.path.join(o['root'], 'data', 'bosses.json')
    if chk:
        old = open(dst, encoding='utf-8').read() if os.path.exists(dst) else ''
        print('igual' if old == txt else 'diferente'); return 0 if old == txt else 1
    with open(dst, 'w', encoding='utf-8', newline='\n') as f:
        f.write(txt)
    b = D['b']
    print(dst, len(b), 'bosses |', sum(1 for x in b.values() if x['c'] == 'b'), 'Bane,', sum(1 for x in b.values() if x['c'] == 'a'), 'Archfoe,',
          sum(1 for x in b.values() if x['c'] == 'n'), 'Nemesis | com quest:', sum(1 for x in b.values() if 'q' in x),
          '| com dano máximo:', sum(1 for x in b.values() if 'md' in x), '| alavanca:', sum(1 for x in b.values() if 'lv' in x),
          '| no mapa:', sum(1 for x in b.values() if 'pos' in x), f"({sum(1 for x in b.values() if 'pa' in x)} pela entrada da zona)")
    if '--loot' in argv:
        return add_loot(o, list(b))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
