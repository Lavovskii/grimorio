r"""build_crdmg.py — dano que cada criatura faz (data/crdmg.json): {chave: {m, d:{elemento: dano}, u:[elementos sem número], src}}.

Fontes, por esta ordem (o huntProfile/hsetsHTML usa o d, ou o u quando o d está vazio; o 'Golpe mais forte' usa o m):
 1) TibiaWiki (páginas públicas lidas pela API e guardadas em disco): Infobox Creature, campos 'abilities' ({{Ability List}},
    {{Melee}}, {{Ability}}) e 'maxdmg' ({{Max Damage}}). d[elemento] = soma do dano máximo de cada ataque desse elemento;
    m = maxdmg da wiki (no {{Max Damage}} sem 'total': a soma dos elementos menos o manadrain); u = elementos que a criatura
    usa sem número na wiki.
 2) Canary (opentibiabr/canary, ramo main; ficheiros .lua públicos, só leitura, nunca executados), só para as criaturas
    das hunts (G.places[*].mons e G.pm[*].h) que a wiki deixa sem d e sem u. Em monster.attacks: 'melee' → físico;
    type = COMBAT_<X>DAMAGE, COMBAT_LIFEDRAIN ou COMBAT_MANADRAIN → esse elemento; um feitiço com nome e sem type → o
    COMBAT_PARAM_TYPE do ficheiro do feitiço (data-otservbr-global/scripts/spells/monster/<nome>.lua, ou a runa em
    data/scripts/runes/). d[elemento] = soma de max(|minDamage|, |maxDamage|) de cada ataque (a mesma regra da wiki: o
    número mais alto de cada ataque); um ataque 'condition' (type = CONDITION_POISON…, com dano) conta no elemento da
    condição; uma condição dentro de outro ataque (condition = {...}) não conta. m = o m da wiki quando é > 0,
    senão a soma do d sem o manadrain (a regra do {{Max Damage}}). src = 'canary'.
Só acrescenta (--write): no data/crdmg.json entram as chaves que ainda não existem e as que existem sem d e sem u
(estas só quando a nova tem d ou u); as outras ficam iguais. Formato: uma linha, chaves ordenadas, separadores ',' e ':'.

Uso: python -I build_crdmg.py [raiz] [--work PASTA] [--out FICHEIRO] [--write] [--fetch]
  raiz: sem ela, a pasta-mãe de _dev quando o script está em _dev, senão C:\xampp\htdocs\grimorio
  --work: pasta das caches e listas (por omissão %GRIM_CRDMG%, senão C:\xampp\_work\crdmg): keys.json, alts.json,
          extra_keys.json, dl\pages, dl\alt, dl\extra, dl\extra2 (páginas da wiki; a recolha mais recente, dl\extra2,
          ganha às outras) e dl\canary (tree.json = árvore do repositório; files\<caminho no repositório>)
  --out: ficheiro com o resultado completo das duas fontes (por omissão <work>\crdmg.json; não é o do site)
  --write: junta ao <raiz>\data\crdmg.json as chaves novas e as que lá estão sem d e sem u (nunca muda as outras)
  --fetch: o que faltar na cache vai à rede (TibiaWiki: 50 títulos por pedido; Canary: um pedido a
           raw.githubusercontent.com por ficheiro; User-Agent 'GrimorioDeTibia/1.0', 1,1 s entre pedidos). Sem --fetch
           nada vai à rede e o fim diz o que falta.
No fim lista as criaturas das hunts que continuam sem dano conhecido. Depois de --write: o smoke (ficha de uma hunt,
'Dano que vais levar')."""
import collections, glob, json, os, re, sys, time, urllib.parse, urllib.request

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
API = 'https://tibia.fandom.com/api.php'
RAW = 'https://raw.githubusercontent.com/opentibiabr/canary/main/'
UA = 'GrimorioDeTibia/1.0'
PAUSE = 1.1
ELS = ['physical', 'fire', 'ice', 'earth', 'energy', 'death', 'holy', 'drown', 'lifedrain', 'manadrain']


def default_root():
    if os.path.basename(HERE).lower() == '_dev':
        return os.path.dirname(HERE)
    return r'C:\xampp\htdocs\grimorio'


def parse_args(argv):
    o = {'root': None, 'work': None, 'out': None, 'write': False, 'fetch': False}
    it = iter(argv)
    for a in it:
        if a in ('--work', '--out'):
            o[a[2:]] = next(it, None)
        elif a == '--write':
            o['write'] = True
        elif a == '--fetch':
            o['fetch'] = True
        elif a.startswith('--'):
            sys.exit('opção desconhecida: ' + a)
        elif o['root'] is None:
            o['root'] = a
    o['root'] = os.path.abspath(o['root'] or default_root())
    o['work'] = os.path.abspath(o['work'] or os.environ.get('GRIM_CRDMG') or r'C:\xampp\_work\crdmg')
    o['out'] = os.path.abspath(o['out'] or os.path.join(o['work'], 'crdmg.json'))
    return o


# ---------------------------------------------------------------- wikitext (sem dependências)
def find_close(s, i):
    """s[i:i+2]=='{{'; devolve o índice logo a seguir ao '}}' que fecha."""
    depth, n, j = 0, len(s), i
    while j < n:
        if s.startswith('{{', j):
            depth += 1; j += 2; continue
        if s.startswith('}}', j):
            depth -= 1; j += 2
            if depth == 0:
                return j
            continue
        j += 1
    return n


def split_args(body):
    parts, cur, db, dl, j, n = [], [], 0, 0, 0, len(body)
    while j < n:
        if body.startswith('{{', j): db += 1; cur.append('{{'); j += 2; continue
        if body.startswith('}}', j) and db > 0: db -= 1; cur.append('}}'); j += 2; continue
        if body.startswith('[[', j): dl += 1; cur.append('[['); j += 2; continue
        if body.startswith(']]', j) and dl > 0: dl -= 1; cur.append(']]'); j += 2; continue
        c = body[j]
        if c == '|' and db == 0 and dl == 0:
            parts.append(''.join(cur)); cur = []
        else:
            cur.append(c)
        j += 1
    parts.append(''.join(cur))
    return parts


def parse_template(s):
    """'{{...}}' → (nome, posicionais, {nome: valor})."""
    inner = s[2:-2] if s.endswith('}}') else s[2:]
    parts = split_args(inner)
    pos, named = [], {}
    for p in parts[1:]:
        m = re.match(r'\s*([^=\{\}\[\]\|]+?)\s*=(.*)\Z', p, re.S)
        if m:
            named[m.group(1).strip().lower()] = m.group(2).strip()
        else:
            pos.append(p.strip())
    return parts[0].strip(), pos, named


def top_templates(s):
    out, rest, i, last, n = [], [], 0, 0, len(s)
    while i < n:
        if s.startswith('{{', i) and not s.startswith('{{{', i):
            e = find_close(s, i)
            rest.append(s[last:i]); out.append(s[i:e])
            i = last = e
            continue
        i += 1
    rest.append(s[last:])
    return out, ''.join(rest)


def strip_markup(s):
    s = re.sub(r'<!--.*?-->', '', s, flags=re.S)
    s = re.sub(r'<ref[^>]*/>', '', s)
    s = re.sub(r'<ref.*?</ref>', '', s, flags=re.S)
    s = re.sub(r'<[^>]+>', ' ', s)
    s = re.sub(r'\[\[(?:[^\]\|]*\|)?([^\]]*)\]\]', r'\1', s)
    return s


def load_pages(d):
    """ficheiros de lotes da API → {título pedido: (título final, wikitexto ou None)}."""
    res = {}
    for f in sorted(glob.glob(os.path.join(d, '*.json'))):
        q = json.load(open(f, encoding='utf-8'))['query']
        pages = {p['title']: p for p in q.get('pages', [])}
        norm = {x['from']: x['to'] for x in q.get('normalized', [])}
        redir = {x['from']: x['to'] for x in q.get('redirects', [])}
        for r in set(norm) | set(redir) | set(pages):
            t, seen = norm.get(r, r), 0
            while t in redir and seen < 5:
                t = redir[t]; seen += 1
            p = pages.get(t)
            res[r] = (t, p['revisions'][0]['slots']['main']['content'] if p and 'revisions' in p else None)
    return res


# ---------------------------------------------------------------- TibiaWiki → dano (regras de sempre)
EMAP = [
    (r'mana ?drain', 'manadrain'), (r'life ?drain|hp ?drain|lifed rain|life leech', 'lifedrain'),
    (r'physical|melee|bleed', 'physical'), (r'fire|burn|flame', 'fire'),
    (r'\bice\b|freez|frozen|frost', 'ice'), (r'earth|poison', 'earth'),
    (r'energy|electri|lightning', 'energy'), (r'death|curse', 'death'),
    (r'holy|dazzl', 'holy'), (r'drown', 'drown'),
]
NONDMG = re.compile(r'^(none|buff|haste|slowed|slow|paralyze|paralysis|drunk|drunkenness|invisible|invisibility|healing|heal|summons?|'
                    r'shapeshifting|outfit|rooted|feared|fear|debuff|strengthened|teleport|hexed|powerless|agony)$')
COND_EL = {'poisoned': 'earth', 'burning': 'fire', 'electrified': 'energy', 'freezing': 'ice', 'cursed': 'death',
           'dazzled': 'holy', 'drowning': 'drown', 'bleeding': 'physical'}
SPELL_HINTS = [
    (r'avalanche', 'ice'), (r'thunderstorm', 'energy'), (r'wrath of nature|envenom', 'earth'), (r'burst arrow', 'fire'),
    (r'groundshaker|whirlwind|berserk|exori|boulder|sniper arrow|throwing kni|knives|spears?\b|arrows?\b|\bbolt|explosion|stone|rock',
     'physical'),
]
COND_WORDS = [(r'bleed', 'physical'), (r'poison', 'earth'), (r'burn', 'fire'), (r'electrif', 'energy'), (r'freez', 'ice'),
              (r'curse', 'death'), (r'dazzl', 'holy'), (r'drown', 'drown')]
stats = collections.Counter()
unk_el = collections.Counter()


def norm_el(s):
    """lista de elementos de um texto de elemento; [] = sem dano; None = desconhecido ('?')."""
    s = strip_markup(s).lower().replace('_', ' ').replace('-', ' ')
    s = re.sub(r'\{\{[^}]*\}\}', '', s)
    s = s.replace('damage', '').replace('?', '').strip()
    s = re.sub(r'^element ', '', s)
    if not s:
        return None
    out = []
    for p in [p.strip() for p in re.split(r'/|,| and | or |&|\+', s) if p.strip()]:
        if NONDMG.match(p):
            continue
        hit = next((e for rx, e in EMAP if re.search(rx, p)), None)
        if hit:
            out.append(hit)
        else:
            unk_el[p] += 1
    return list(dict.fromkeys(out))


def name_el(name, hints=False):
    n = strip_markup(name).lower()
    if 'reflect' in n:
        return None
    if 'physical' in n:
        return 'physical'
    for rx, e in EMAP:
        if e != 'physical' and re.search(rx, n):  # nunca 'physical' por palavras como 'melee' no nome
            return e
    if hints:
        for rx, e in SPELL_HINTS:
            if re.search(rx, n):
                stats['spell_hint_' + e] += 1
                return e
    return None


def text_el(s):
    t = strip_markup(s).lower()
    found = [e for rx, e in EMAP if re.search(r'\b(' + rx + r')', t)]
    return found[0] if len(found) == 1 else None


def max_num(s, zero_ok=False):
    """maior número de dano num texto ('200-300?' → 300); None sem número."""
    if not s:
        return None
    s = re.sub(r'<!--.*?-->', '', s, flags=re.S)
    while re.search(r'\{\{[^{}]*\}\}', s):
        s = re.sub(r'\{\{[^{}]*\}\}', ' ', s)
    s = strip_markup(s).lower()
    if re.search(r'speed|% of', s):
        return None
    s = re.sub(r'(\d),(\d{3})(?!\d)', r'\1\2', s)
    s = re.sub(r'(\d)\.(\d{3})(?!\d)', r'\1\2', s)
    s = re.sub(r'(\d+)\s*k\b', lambda m: str(int(m.group(1)) * 1000), s)
    nums = []
    for m in re.finditer(r'(?<![\w.])(\d+)(?!\d)', s):
        tail, head = s[m.end():m.end() + 12], s[max(0, m.start() - 3):m.start()]
        if re.match(r'\s*(%|secs?\b|seconds?|s\b|turns?|rounds?|sqm|squares?|times|x\b|targets?|levels?|'
                    r'minutes?|min\b|ms\b|players?|tiles?|fields?|charges?|stacks?|bolts?|arrows?|spears?|stones?)', tail):
            continue
        if re.search(r'x\s*$', head):
            continue
        nums.append(int(m.group(1)))
    if not nums:
        return None
    mx = max(nums)
    return mx if (mx > 0 or zero_ok) else None  # '0-?' = desconhecido, não zero


def add(acc, unk, els, val, src):
    if not els:
        return
    if val is None:
        for e in els:
            unk[e] = True
        stats['nodmg_' + src] += 1
        return
    for e in els:
        acc[e] += val
    stats['counted_' + src] += 1


def add_split(acc, unk, els, dmg):
    """'<dano>; causes Bleeding up to N hp/turn' → o dano para o elemento declarado e o N para o da condição."""
    t = strip_markup(re.sub(r'\{\{[^{}]*\}\}', ' ', dmg or '')).lower()
    for rx, ce in COND_WORDS:
        mm = re.search(rx, t)
        if mm and ce not in els:
            add(acc, unk, els, max_num(t[:mm.start()]), 'ability')
            if max_num(t[mm.start():]):
                add(acc, unk, [ce], max_num(t[mm.start():]), 'ability_dot')
            return
    add(acc, unk, els, max_num(dmg), 'ability')


def walk(s, acc, unk):
    tpls, rest = top_templates(s)
    txt = strip_markup(rest)
    for m in re.finditer(r"([A-Za-z][A-Za-z '\-]{2,60})\(([\d\s\-~+?,]+)\)", txt):
        e = name_el(m.group(1))
        if not e and re.search(r'physical|melee', m.group(1), re.I):
            e = 'physical'
        if e:
            add(acc, unk, [e], max_num(m.group(2)), 'plain')
    for t in tpls:
        n, pos, nm = parse_template(t)
        n = n.replace('_', ' ').strip().lower()
        if n == 'ability list':
            for p in pos:
                walk(p, acc, unk)
            for v in nm.values():
                walk(v, acc, unk)
        elif n == 'melee':
            dmg = nm.get('damage') or (pos[0] if pos else '')
            el = nm.get('element') or (pos[1] if len(pos) > 1 else '')
            els = norm_el(el) if el.strip() else ['physical']
            if els is None:
                els = ['physical']
            add(acc, unk, els, max_num(dmg), 'melee')
            if nm.get('poison'):
                add(acc, unk, ['earth'], max_num(nm['poison']), 'meleepoison')
        elif n == 'ability':
            name = nm.get('name') or (pos[0] if pos else '')
            dmg = nm.get('damage') or (pos[1] if len(pos) > 1 else '')
            el = nm.get('element') or (pos[2] if len(pos) > 2 else '')
            cond = (nm.get('condition') or (pos[3] if len(pos) > 3 else '')).strip().lower()
            if 'reflect' in strip_markup(name).lower():
                continue
            if el.strip():
                els = norm_el(el)
                if els is None:
                    e = text_el(dmg) or COND_EL.get(cond) or name_el(name, hints=True)
                    if not e:
                        stats['unknown_element'] += 1
                        continue
                    els = [e]
            else:
                if cond in COND_EL:
                    els = [COND_EL[cond]]
                elif cond:
                    continue
                else:
                    e = text_el(dmg) or name_el(name)
                    if e is None and re.search(r'paraly|invisib|haste|heal|summon|speed|teleport|outfit|shapeshift|drunk|root|fear',
                                               strip_markup(name), re.I):
                        continue
                    els = [e or 'physical']
            add_split(acc, unk, els, dmg)
        else:
            stats['ignored_tpl_' + n] += 1


def parse_maxdmg(v):
    """campo maxdmg → (total ou None, {elemento: n}, elementos com '?')."""
    v = (v or '').strip()
    per, unknown = {}, set()
    tpls, rest = top_templates(v)
    for t in tpls:
        n, pos, nm = parse_template(t)
        if n.strip().lower() != 'max damage':
            continue
        for e in ELS:
            x = max_num(nm.get(e, ''))
            if x:
                per[e] = x
            elif nm.get(e, '').strip() and max_num(nm[e], zero_ok=True) is None:
                unknown.add(e)
        tot = max_num(nm.get('total', ''))
        if tot is None:  # regra do {{Max Damage}}: soma dos elementos menos o manadrain e as invocações
            vals = [per[e] for e in per if e != 'manadrain']
            tot = sum(vals) if vals else None
        return tot, per, unknown
    r = re.split(r'\(', strip_markup(rest))[0]  # 'N (N com invocações)' → N
    return max_num(r, zero_ok=True), per, unknown


def used_elements(v):
    out = set()
    for p in re.split(r'>|,|/|;| and ', strip_markup(v or '').lower()):
        p = re.sub(r'[\d%:\-~?]+', ' ', p).strip()
        for rx, e in EMAP:
            if p and re.search(rx, p):
                out.add(e)
                break
    return out


def infobox(c):
    m = re.search(r'\{\{\s*Infobox[ _]Creature', c, re.I)
    return parse_template(c[m.start():find_close(c, m.start())])[2] if m else None


def wiki_entry(ib):
    acc, unk = collections.Counter(), {}
    walk(ib.get('abilities', ''), acc, unk)
    m, per, munk = parse_maxdmg(ib.get('maxdmg', ''))
    fills = []
    for e, x in per.items():  # o {{Max Damage}} preenche elementos sem número nas habilidades
        if acc[e] == 0 or (unk.get(e) and x > acc[e]):
            fills.append((e, acc[e], x))
            acc[e] = x
    d = {e: int(acc[e]) for e in ELS if acc[e] > 0}
    u_set = (set(unk) | munk | used_elements(ib.get('usedelements', ''))) - set(d)
    u = [e for e in ELS if e in u_set]
    if m == 0 and (d or u):
        m = None  # a wiki diz 0 mas lista ataques → desconhecido
    if m is None and not d and not u:
        return None, fills
    r = {'m': m, 'd': d}
    if u:
        r['u'] = u
    return r, fills


# ---------------------------------------------------------------- Canary
CTYPE = {'PHYSICALDAMAGE': 'physical', 'FIREDAMAGE': 'fire', 'ICEDAMAGE': 'ice', 'EARTHDAMAGE': 'earth', 'ENERGYDAMAGE': 'energy',
         'DEATHDAMAGE': 'death', 'HOLYDAMAGE': 'holy', 'DROWNDAMAGE': 'drown', 'LIFEDRAIN': 'lifedrain', 'MANADRAIN': 'manadrain',
         'HEALING': '-', 'UNDEFINEDDAMAGE': None, 'AGONYDAMAGE': None, 'NEUTRALDAMAGE': None}
CCOND = {'POISON': 'earth', 'FIRE': 'fire', 'ENERGY': 'energy', 'BLEEDING': 'physical', 'FREEZING': 'ice', 'CURSED': 'death',
         'DAZZLED': 'holy', 'DROWN': 'drown'}
MON_DIRS = ('data-otservbr-global/monster/', 'data-canary/monster/')
SPELL_DIRS = ('data-otservbr-global/scripts/spells/monster/', 'data-canary/scripts/spells/monster/', 'data/scripts/runes/', 'data/scripts/spells/')


def N(s):
    return re.sub(r'[^a-z0-9]', '', str(s).lower())


def lua_clean(s):
    s = re.sub(r'--\[(=*)\[.*?\]\1\]', '', s, flags=re.S)
    return re.sub(r'--[^\n]*', '', s)


def brace_end(s, i):
    """s[i]=='{' → índice logo a seguir à '}' que fecha (ignora o que está entre aspas)."""
    depth, j, n, q = 0, i, len(s), None
    while j < n:
        c = s[j]
        if q:
            if c == '\\':
                j += 2; continue
            if c == q:
                q = None
        elif c in '"\'':
            q = c
        elif c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                return j + 1
        j += 1
    return n


def top_tables(body):
    """tabelas { ... } ao nível de cima de um corpo de tabela Lua."""
    out, j = [], 0
    while True:
        i = body.find('{', j)
        if i < 0:
            return out
        e = brace_end(body, i)
        out.append(body[i + 1:e - 1])
        j = e


class Canary:
    def __init__(self, work, fetch):
        self.dir = os.path.join(work, 'dl', 'canary')
        self.fetch = fetch
        self.last = 0.0
        self.missing, self.fetched, self.errors = [], [], []
        tp = os.path.join(self.dir, 'tree.json')
        tree = json.load(open(tp, encoding='utf-8'))['tree'] if os.path.exists(tp) else []
        if not tree:
            self.errors.append('sem ' + tp + ' (árvore do repositório: api.github.com/repos/opentibiabr/canary/git/trees/main?recursive=1)')
        paths = [x['path'] for x in tree if x.get('type') == 'blob' and x['path'].endswith('.lua')]
        self.mons = {}
        for d in MON_DIRS:
            for p in paths:
                if p.startswith(d):
                    self.mons.setdefault(N(p.rsplit('/', 1)[1][:-4]), p)
        self.spells = collections.defaultdict(list)  # N(nome do ficheiro) → caminhos, pela ordem de SPELL_DIRS
        self.mspells = []
        for d in SPELL_DIRS:
            for p in paths:
                if p.startswith(d):
                    b = N(p.rsplit('/', 1)[1][:-4])
                    self.spells[b].append(p)
                    if d.endswith('runes/'):
                        self.spells[b + 'rune'].append(p)
                    if '/spells/monster/' in d:
                        self.mspells.append(p)
        self.spell_cache = {}

    def get(self, path):
        fp = os.path.join(self.dir, 'files', *path.split('/'))
        if os.path.exists(fp):
            return open(fp, encoding='utf-8', errors='replace').read()
        if not self.fetch:
            if path not in self.missing:
                self.missing.append(path)
            return None
        wait = PAUSE - (time.time() - self.last)
        if wait > 0:
            time.sleep(wait)
        self.last = time.time()
        try:
            req = urllib.request.Request(RAW + urllib.parse.quote(path), headers={'User-Agent': UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                body = r.read()
        except Exception as e:
            self.errors.append(f'{path}: {e}')
            return None
        os.makedirs(os.path.dirname(fp), exist_ok=True)
        with open(fp, 'wb') as f:
            f.write(body)
        self.fetched.append(path)
        return body.decode('utf-8', errors='replace')

    @staticmethod
    def declared(text):
        m = re.search(r'(?:spell|rune|combat)\s*:\s*name\(\s*"([^"]+)"', text)
        return m.group(1) if m else None

    @staticmethod
    def ptype(text):
        ts = [CTYPE.get(t) for t in re.findall(r'COMBAT_PARAM_TYPE\s*,\s*COMBAT_(\w+)', text)]
        ts = [t for t in ts if t]
        return ts[0] if ts else None

    def spell_el(self, name):
        """elemento de um feitiço de monstro pelo nome (None = desconhecido)."""
        n = N(name)
        if n in self.spell_cache:
            return self.spell_cache[n]
        el, cands = None, list(self.spells.get(n, []))
        hit, gap = None, False
        for p in cands:
            t = self.get(p)
            if t is None:
                gap = True  # sem --fetch e fora da cache: não se procura mais (o fim diz o que falta)
                continue
            dn = self.declared(t)
            if dn is None or N(dn) == n:
                hit = t
                break
        if hit is None and not gap:  # ficheiro com outro nome (ex.: 'quarasmallicering' em quara_looter_small_icering.lua)
            group = [p for p in self.mspells if N(p.rsplit('/', 1)[1][:-4]).startswith(n[:5]) and p not in cands][:15]
            for p in group:
                t = self.get(p)
                if t is not None and N(self.declared(t) or '') == n:
                    hit = t
                    break
        if hit is not None:
            el = self.ptype(hit)
        self.spell_cache[n] = el
        return el

    def monster(self, keys):
        for k in keys:
            p = self.mons.get(N(k))
            if p:
                return p
        return None

    def damage(self, text, log):
        """monster.attacks → (d, u)."""
        s = lua_clean(text)
        m = re.search(r'monster\.attacks\s*=\s*\{', s)
        if not m:
            return {}, []
        body = s[m.end() - 1:brace_end(s, m.end() - 1)][1:-1]
        acc, seen = collections.Counter(), set()
        for e in top_tables(body):
            top = e
            while re.search(r'\{[^{}]*\}', top):  # tira as tabelas de dentro (condition = {...})
                top = re.sub(r'\{[^{}]*\}', ' ', top)
            nm = re.search(r'\bname\s*=\s*"([^"]*)"', top)
            nm = nm.group(1).strip().lower() if nm else ''
            ty = re.search(r'\btype\s*=\s*COMBAT_(\w+)', top)
            vals = [abs(int(x)) for x in re.findall(r'\b(?:minDamage|maxDamage)\s*=\s*(-?\d+)', top)]
            val = max(vals) if vals else 0
            if ty:
                el = CTYPE.get(ty.group(1))
                if el is None:
                    log.append(('tipo desconhecido', nm, ty.group(1), val))
                    continue
            elif nm == 'melee':
                el = 'physical'
            elif nm == 'condition':
                cc = re.search(r'\btype\s*=\s*CONDITION_(\w+)', top)
                el = CCOND.get(cc.group(1)) if cc else None
                if el is None:
                    continue  # paralisia, bebedeira… sem dano
            elif nm == 'combat' or not nm:
                continue
            elif not val:
                continue  # feitiço sem dano (drunk, speed, outfit, invisible…)
            else:
                el = self.spell_el(nm)
                if el is None:
                    log.append(('feitiço sem elemento', nm, None, val))
                    continue
            if el == '-':
                continue  # cura
            seen.add(el)
            if val > 0:
                acc[el] += val
        d = {e: int(acc[e]) for e in ELS if acc[e] > 0}
        return d, [e for e in ELS if e in seen and e not in d]


# ---------------------------------------------------------------- principal
def wiki_fetch(titles, outdir, prefix='x2'):
    os.makedirs(outdir, exist_ok=True)
    ex = [int(m.group(1)) for f in os.listdir(outdir) for m in [re.match(prefix + r'_(\d+)\.json$', f)] if m]
    nxt, last = (max(ex) + 1 if ex else 0), 0.0
    for i in range(0, len(titles), 50):
        params = {'action': 'query', 'prop': 'revisions', 'rvprop': 'content', 'rvslots': 'main',
                  'titles': '|'.join(titles[i:i + 50]), 'redirects': '1', 'format': 'json', 'formatversion': '2'}
        wait = PAUSE - (time.time() - last)
        if wait > 0:
            time.sleep(wait)
        last = time.time()
        req = urllib.request.Request(API, data=urllib.parse.urlencode(params).encode(), headers={'User-Agent': UA})
        with urllib.request.urlopen(req, timeout=60) as r:
            body = r.read()
        json.loads(body)
        out = os.path.join(outdir, f'{prefix}_{nxt:03d}.json')
        with open(out, 'wb') as f:
            f.write(body)
        nxt += 1
        print('wiki: gravado', out)


def main(argv):
    o = parse_args(argv)
    W, root = o['work'], o['root']
    sys.path[:0] = [HERE, r'C:\xampp\_tools']  # o gjson.py ao lado (_tools = _dev/) ou, noutra pasta, o de C:\xampp\_tools
    from gjson import load_G
    _, G, _ = load_G(root)
    crp = os.path.join(root, 'data', 'creatures.json')
    CR = json.load(open(crp, encoding='utf-8')) if os.path.exists(crp) else {}
    kp = os.path.join(W, 'keys.json')
    K = json.load(open(kp, encoding='utf-8')) if os.path.exists(kp) else {'keys': [], 'kt': {}}
    ap = os.path.join(W, 'alts.json')
    ALTS = json.load(open(ap, encoding='utf-8')) if os.path.exists(ap) else {}
    ep = os.path.join(W, 'extra_keys.json')
    EXTRA = json.load(open(ep, encoding='utf-8')) if os.path.exists(ep) else {}

    def title(k):
        n = (CR.get(k) or {}).get('n') or (G['mon'].get(k) or [None])[0] or k
        return n[0].upper() + n[1:]

    hunt = set()
    for p in G['places'].values():
        hunt.update(str(m).strip().lower() for m in p.get('mons', []) if str(m).strip())
    for v in G['pm'].values():
        hunt.update(k for k, _ in (v.get('h') or []))
    for k, n in list(EXTRA.items()) + [(k, title(k)) for k in sorted(hunt)]:
        if k not in K['kt']:
            K['kt'][k] = n[0].upper() + n[1:]
            K['keys'].append(k)

    dl = os.path.join(W, 'dl')

    def pages_load():
        pg = load_pages(os.path.join(dl, 'pages'))
        for sub in ('alt', 'extra'):
            pg.update({k: v for k, v in load_pages(os.path.join(dl, sub)).items() if k not in pg or not pg[k][1]})
        pg.update({k: v for k, v in load_pages(os.path.join(dl, 'extra2')).items() if v[1]})  # recolha mais recente
        return pg

    pages = pages_load()

    def base_keys(k):
        out = []
        b = re.sub(r'\s+(stop|invu|inv|fake|stuck|summon|dirty|east|west|north|south)$|\d+$', '', k).strip()
        out.append(b)
        if b.endswith('s'):
            out.append(b[:-1])
        out.append(re.sub(r'^beast\s+', '', b))
        return [x for x in dict.fromkeys(out) if x != k and x in K['kt']]

    def cands(k):
        return [K['kt'][k]] + ALTS.get(k, []) + [K['kt'][b] for b in base_keys(k)]

    nopage = [k for k in sorted(hunt) if not any(pages.get(t) and pages[t][1] for t in cands(k))]
    if nopage and o['fetch']:
        wiki_fetch([K['kt'][k] for k in nopage], os.path.join(dl, 'extra2'))
        pages = pages_load()

    res, src_title, fill_log = {}, {}, []
    for k in K['keys']:
        ib = None
        for t in cands(k):
            r = pages.get(t)
            if r and r[1]:
                ib = infobox(r[1])
                if ib is not None:
                    src_title[k] = r[0]
                    break
        if ib is None:
            stats['no_page'] += 1
            continue
        r, fills = wiki_entry(ib)
        fill_log += [(k,) + f for f in fills]
        if r is None:
            stats['page_but_no_data'] += 1
            continue
        res[k] = r

    # Canary: criaturas das hunts sem d e sem u na wiki
    can = Canary(W, o['fetch'])
    clog, cpath, cempty, nofile = [], {}, [], []
    for k in sorted(hunt):
        r = res.get(k)
        if r and (r['d'] or r.get('u')):
            continue
        p = can.monster([k, K['kt'].get(k, k)] + ALTS.get(k, []))
        if not p:
            nofile.append(k)
            continue
        t = can.get(p)
        if t is None:
            continue
        mn = re.search(r'createMonsterType\(\s*"([^"]+)"', t)
        if mn and N(mn.group(1)) not in (N(k), N(K['kt'].get(k, k))):
            clog.append(('nome diferente', k, mn.group(1), p))
        lg = []
        d, u = can.damage(t, lg)
        clog += [(x[0], k) + x[1:] for x in lg]
        if not d and not u:
            cempty.append(k)
            continue
        mw = r['m'] if r else None
        m = mw if isinstance(mw, (int, float)) and mw > 0 else (sum(v for e, v in d.items() if e != 'manadrain') or None)
        e = {'m': m, 'd': d}
        if u:
            e['u'] = u
        e['src'] = 'canary'
        res[k] = e
        cpath[k] = p

    os.makedirs(os.path.dirname(o['out']), exist_ok=True)
    with open(o['out'], 'w', encoding='utf-8', newline='') as f:
        json.dump(dict(sorted(res.items())), f, separators=(',', ':'), ensure_ascii=False)
    with open(os.path.join(W, 'build_log.json'), 'w', encoding='utf-8', newline='') as f:
        json.dump({'src': src_title, 'fill': fill_log, 'canary': cpath, 'canary_log': clog}, f, ensure_ascii=False, indent=0)
    withd = {k for k, v in res.items() if v['d']}
    print('resultado:', o['out'])
    print('entradas', len(res), 'com d', len(withd), 'com d ou u', len({k for k, v in res.items() if v['d'] or v.get('u')}),
          '| do Canary', len(cpath))
    print('wiki:', dict(stats))
    if unk_el:
        print('palavras de elemento desconhecidas:', unk_el.most_common(20))
    for x in clog:
        print('canary:', *x)
    if can.fetched:
        print('canary: descarregados', len(can.fetched))
    if can.missing:
        print('canary: faltam na cache (corre com --fetch):', len(can.missing), can.missing[:20])
    for x in can.errors:
        print('canary: ERRO', x)

    if o['write']:
        dp = os.path.join(root, 'data', 'crdmg.json')
        raw = open(dp, encoding='utf-8').read()
        cur = json.loads(raw)
        added, filled = [], []
        for k, v in sorted(res.items()):
            if k not in cur:
                if k in CR or k in G['mon']:  # só chaves do site (o keys.json também tem nomes de página como 'monk (creature)')
                    cur[k] = v
                    added.append(k)
            elif not cur[k].get('d') and not cur[k].get('u') and (v['d'] or v.get('u')):
                if isinstance(cur[k].get('m'), (int, float)) and cur[k]['m'] > 0 and v.get('src') == 'canary':
                    v = dict(v, m=cur[k]['m'])  # o m que o site já tinha (da wiki) fica
                cur[k] = v
                filled.append(k)
        txt = json.dumps(dict(sorted(cur.items())), separators=(',', ':'), ensure_ascii=False)
        if txt != raw:
            with open(dp, 'w', encoding='utf-8', newline='') as f:
                f.write(txt)
        print(f'{dp}: {len(added)} chaves novas, {len(filled)} preenchidas (estavam sem d e sem u)'
              + ('' if txt != raw else ' — sem mudanças'))
        if added:
            print('  novas:', ', '.join(added))
        if filled:
            print('  preenchidas:', ', '.join(filled))
        final = cur
    else:
        final = res
    miss = sorted(k for k in hunt if not (final.get(k) and (final[k].get('d') or final[k].get('u'))))
    print(f'criaturas das hunts sem dano conhecido ({len(miss)}):', ', '.join(miss))
    if nofile:
        print('  sem ficheiro no Canary:', ', '.join(nofile))
    if cempty:
        print('  no Canary sem ataques com dano:', ', '.join(cempty))
    if nopage and not o['fetch']:
        print('  sem página da wiki na cache (corre com --fetch):', ', '.join(nopage))
    return 0


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.exit(main(sys.argv[1:]))
