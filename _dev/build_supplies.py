r"""Acrescenta a data/items.json os supplies que a linha 'Supplies' da ficha e a calculadora de lucro pedem (supRows) e
que ainda não lá estão: poções, munições do paladino e a paralyse rune. Dados da TibiaWiki, lidos pela API (páginas
públicas, User-Agent 'GrimorioDeTibia/1.0', um pedido de cada vez com pausa, cache em disco):
- a Infobox Object da página do item: nome, itemid (= id do Market), primarytype (cls), peso, value, npcvalue,
  stackable, marketable, implemented e 'Dropped By';
- Module:ItemPrices/data (as trocas de cada NPC, a mesma fonte da tabela 'Buy From' das páginas): quem vende (buy) e
  quem compra (sell), com o preço. Ficam de fora os NPCs com status 'npconly' (ex.: Festival Assistant, que vende tudo
  a 1 gp nas Boss Lairs), o Hireling Trader (só em casas com hireling) e as trocas com status 'itemonly'; as trocas
  noutra moeda ficam [NPC, preço, moeda] (o site só conta as de ouro).
Nunca muda uma chave que já existe; o que a wiki não der (página em falta, sem itemid) fica de fora e é dito no fim.
Uso: python -I build_supplies.py [raiz] [--cache PASTA] [--offline] [--dry]
  raiz: sem ela, a pasta-mãe de _dev quando o script está em _dev, senão C:\xampp\htdocs\grimorio
  --cache: pasta da cache (por omissão %GRIM_WIKI_CACHE%, senão <%GRIM_WORK% ou pasta temporária>\grim-wiki)
  --offline: só a cache (nada vai à rede); --dry: diz o que faria sem gravar
Formato de data/items.json: JSON compacto (ensure_ascii=False, separadores ',' e ':'), sem quebra de linha no fim.
Depois: python -I build_search.py <raiz> (a pesquisa global também lista os itens novos)."""
import json, os, re, sys, tempfile, time, urllib.parse, urllib.request

sys.dont_write_bytecode = True
API = 'https://tibia.fandom.com/api.php'
UA = 'GrimorioDeTibia/1.0'
PAUSE = 1.5  # segundos entre pedidos
MODULE = 'Module:ItemPrices/data'
# páginas da TibiaWiki (o nome em minúsculas é a chave de items.json, igual à que o supRows procura)
SUPPLIES = ['Ultimate Mana Potion', 'Superior Mana Potion', 'Ultimate Spirit Potion', 'Supreme Health Potion',
            'Diamond Arrow', 'Crystalline Arrow', 'Onyx Arrow', 'Shatterstorm Arrow', 'Firestorm Arrow', 'Sniper Arrow',
            'Froststorm Arrow', 'Drill Bolt', 'Spectral Bolt', 'Prismatic Bolt', 'Earth Arrow', 'Paralyse Rune']
SKIP_NPC = {'Hireling Trader'}


def default_root():
    here = os.path.dirname(os.path.abspath(__file__))
    if os.path.basename(here).lower() == '_dev':
        return os.path.dirname(here)
    return r'C:\xampp\htdocs\grimorio'


def args(argv):
    o = {'root': None, 'cache': None, 'offline': False, 'dry': False}
    it = iter(argv)
    for a in it:
        if a == '--cache':
            o['cache'] = next(it, None)
        elif a == '--offline':
            o['offline'] = True
        elif a == '--dry':
            o['dry'] = True
        elif a.startswith('--'):
            sys.exit('opção desconhecida: ' + a)
        elif o['root'] is None:
            o['root'] = a
    o['root'] = os.path.abspath(o['root'] or default_root())
    o['cache'] = o['cache'] or os.environ.get('GRIM_WIKI_CACHE') or os.path.join(os.environ.get('GRIM_WORK') or tempfile.gettempdir(), 'grim-wiki')
    return o


def cfile(cache, title):
    return os.path.join(cache, 'page_' + re.sub(r'[^A-Za-z0-9._-]+', '_', title) + '.json')


def fetch(titles, cache, offline):
    """{título: {'title','page','redirect','missing','ts','content'}}; vai à rede só pelo que não está na cache (lotes de 50)."""
    os.makedirs(cache, exist_ok=True)
    need = [t for t in titles if not os.path.exists(cfile(cache, t))]
    if need and offline:
        print('  sem cache (--offline):', ', '.join(need))
        need = []
    for i in range(0, len(need), 50):
        chunk = need[i:i + 50]
        params = {'action': 'query', 'prop': 'revisions', 'rvprop': 'content|timestamp', 'rvslots': 'main', 'titles': '|'.join(chunk),
                  'redirects': '1', 'format': 'json', 'formatversion': '2'}
        req = urllib.request.Request(API, data=urllib.parse.urlencode(params).encode(), headers={'User-Agent': UA})
        time.sleep(PAUSE)
        for a in range(3):
            try:
                with urllib.request.urlopen(req, timeout=90) as r:
                    d = json.loads(r.read().decode('utf-8'))
                break
            except Exception as e:  # rede em baixo: tenta mais 2 vezes, devagar
                if a == 2:
                    raise
                print('  nova tentativa:', e); time.sleep(5 * (a + 1))
        q = d.get('query') or {}
        norm = {x['from']: x['to'] for x in q.get('normalized') or []}
        red = {x['from']: x['to'] for x in q.get('redirects') or []}
        pages = {p.get('title'): p for p in q.get('pages') or []}
        for t in chunk:
            t2 = norm.get(t, t); t3 = red.get(t2, t2); p = pages.get(t3) or {}
            rv = (p.get('revisions') or [{}])[0]
            o = {'title': t, 'page': p.get('title', t3), 'redirect': t3 if t3 != t2 else None, 'missing': bool(p.get('missing')) or not rv,
                 'ts': rv.get('timestamp'), 'content': ((rv.get('slots') or {}).get('main') or {}).get('content')}
            with open(cfile(cache, t), 'w', encoding='utf-8') as f:
                json.dump(o, f, ensure_ascii=False)
    out = {}
    for t in titles:
        if os.path.exists(cfile(cache, t)):
            with open(cfile(cache, t), encoding='utf-8') as f:
                out[t] = json.load(f)
    return out


def infobox(text):
    """Campos da {{Infobox Object|...}} (uma linha '| campo = valor' por campo; as linhas seguintes juntam-se ao campo)."""
    i = (text or '').find('{{Infobox Object')
    if i < 0:
        return None
    f, cur = {}, None
    for line in text[i:].split('\n')[1:]:
        m = re.match(r'^\s*\|\s*([A-Za-z0-9_]+)\s*=\s?(.*)$', line)
        if m:
            cur = m.group(1).strip().lower(); f[cur] = m.group(2).strip()
        elif line.strip() == '}}':
            break
        elif cur:
            f[cur] += '\n' + line
    return f


def toint(s):
    m = re.search(r'-?\d[\d,]*', str(s or ''))
    return int(m.group(0).replace(',', '')) if m else None


def yes(s):
    return str(s or '').strip().lower() in ('yes', 'y', 'true', '1')


def value(s):
    """'130' → [130,130]; '1-3' → [1,3]; vazio, '?' ou 'Negotiable' → None."""
    s = re.sub(r'<[^>]*>|\[\[|\]\]', '', str(s or '')).replace(',', '').strip()
    m = re.match(r'^(\d+)\s*(?:-\s*(\d+))?\s*(?:gp)?$', s, re.I)
    if not m:
        return None
    a = int(m.group(1)); b = int(m.group(2)) if m.group(2) else a
    return [a, b]


def dropped(s):
    m = re.search(r'\{\{\s*Dropped By\s*\|?(.*?)\}\}', str(s or ''), re.S)
    return [x.strip() for x in m.group(1).split('|') if x.strip() and '=' not in x] if m else []


def trades(text):
    """Module:ItemPrices/data → {item em minúsculas: {'buy': [[NPC, preço(, moeda)]], 'sell': [...]}} (buy = o NPC vende)."""
    body = text[text.index('return {'):] if 'return {' in text else text
    fld = re.compile(r'\["(\w+)"\]\s*=\s*(notes\["[^"]*"\]|"(?:[^"\\]|\\.)*"|-?\d+(?:\.\d+)?)')
    out, npc, part, skip = {}, None, None, False
    for line in body.split('\n'):
        m = re.match(r'^\s*(?:\},\s*)?\["([^"]+)"\]\s*=\s*\{\s*$', line)
        if m:
            if m.group(1) in ('buys', 'sells'):
                part = m.group(1)
            else:
                npc, part, skip = m.group(1), None, m.group(1) in SKIP_NPC
            continue
        m = re.match(r'^\s*\["status"\]\s*=\s*"([^"]*)"', line)
        if m and part is None and npc:
            skip = skip or m.group(1) == 'npconly'
            continue
        m = re.match(r'^\s*\{(.*)\}\s*,?\s*(?:--.*)?$', line)
        if not (m and npc and part) or skip:
            continue
        e = {}
        for k, v in fld.findall(m.group(1)):
            e[k] = json.loads(v) if v.startswith('"') else v if v.startswith('notes') else (float(v) if '.' in v else int(v))
        if not e.get('item') or e.get('status') == 'itemonly':
            continue
        p, cur = e.get('price'), e.get('currency')
        if isinstance(p, str):  # '5,000 [[Trust Points]]' → 5000 e a moeda
            mm = re.match(r'^\s*([\d,]+)\s*(.*)$', p)
            if not mm:
                continue
            p = int(mm.group(1).replace(',', ''))
            c2 = re.sub(r'\[\[(?:[^\]|]*\|)?([^\]]*)\]\]', r'\1', mm.group(2)).strip()
            cur = cur or (re.sub(r's$', '', c2) if c2 else None)
        if not isinstance(p, (int, float)) or p <= 0:
            continue
        row = [npc, int(p)] + ([cur] if cur and not re.fullmatch(r'gold( coins?)?|gp', str(cur), re.I) else [])
        side = 'buy' if part == 'sells' else 'sell'
        lst = out.setdefault(e['item'].strip().lower(), {'buy': [], 'sell': []})[side]
        if row not in lst:
            lst.append(row)
    return out


def entry(title, pg, tr):
    """Entrada de items.json no formato das que já lá estão, ou (None, motivo)."""
    if not pg or pg.get('missing') or not pg.get('content'):
        return None, 'a página não existe na TibiaWiki'
    ib = infobox(pg['content'])
    if not ib:
        return None, 'a página não tem Infobox Object'
    ids = [int(x) for x in re.findall(r'\d+', ib.get('itemid') or '')]
    if not ids:
        return None, 'a infobox não tem itemid'
    k = (ib.get('actualname') or ib.get('name') or title).strip().lower()
    t = tr.get(k) or tr.get(title.lower()) or {'buy': [], 'sell': []}
    srt = lambda l: sorted(l, key=lambda x: (x[0], x[1], str(x[2:])))
    wt = ib.get('weight'); wt = float(re.sub(r'[^\d.]', '', wt)) if wt and re.search(r'\d', wt) else None
    return {'t': (ib.get('name') or title).strip(), 'ids': ids, 'cls': (ib.get('primarytype') or ib.get('objectclass') or '').strip() or None,
            'slot': (ib.get('slot') or '').strip() or None, 'wt': wt, 'val': value(ib.get('value')), 'npc': toint(ib.get('npcvalue')) or 0,
            'sell': srt(t['sell']), 'buy': srt(t['buy']), 'drop': dropped(ib.get('droppedby')), 'imb': toint(ib.get('imbueslots')),
            'up': toint(ib.get('upgradeclass')), 'stack': yes(ib.get('stackable')), 'mkt': yes(ib.get('marketable')), 'aug': None,
            'impl': (re.sub(r'\[\[|\]\]', '', ib.get('implemented') or '').strip() or None), 'quest': []}, k


def main(argv):
    o = args(argv)
    path = os.path.join(o['root'], 'data', 'items.json')
    with open(path, encoding='utf-8', newline='') as f:
        raw = f.read()
    items = json.loads(raw)
    want = [t for t in SUPPLIES if t.lower() not in items]
    print(f'items.json: {len(items)} itens; supplies em falta: {len(want)} de {len(SUPPLIES)}')
    if not want:
        print('nada a acrescentar'); return 0
    pages = fetch(want + [MODULE], o['cache'], o['offline'])
    if MODULE not in pages or not pages[MODULE].get('content'):
        print('  sem', MODULE, '(quem vende fica vazio)')
    tr = trades((pages.get(MODULE) or {}).get('content') or '')
    add, out = {}, []
    for t in want:
        e, k = entry(t, pages.get(t), tr)
        if e is None:
            out.append(f'{t}: {k}'); continue
        if k != t.lower():
            out.append(f'{t}: a wiki chama-lhe "{k}" (não acrescentado)'); continue
        add[k] = e
        gold = [x for x in e['buy'] if len(x) == 2]
        print(f'  + {k}: ids {e["ids"]}, {e["cls"]}, {len(gold)} NPC a vender' + (f' por {min(x[1] for x in gold)} gp' if gold else ' (nenhum NPC vende: só o Market)'))
    for x in out:
        print('  fora:', x)
    if not add:
        return 0
    for k, e in add.items():
        assert k not in items
        items[k] = e
    new = json.dumps(items, ensure_ascii=False, separators=(',', ':'))
    old = json.loads(raw)
    assert all(json.dumps(items[k], sort_keys=True) == json.dumps(v, sort_keys=True) for k, v in old.items()), 'uma chave antiga mudou'
    if o['dry']:
        print(f'--dry: acrescentaria {len(add)} itens'); return 0
    with open(path, 'w', encoding='utf-8', newline='') as f:
        f.write(new)
    print(f'gravado {path}: +{len(add)} itens ({len(items)} no total)')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
