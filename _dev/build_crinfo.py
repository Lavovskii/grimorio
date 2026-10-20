"""Gera data/crinfo.json (ataques e propriedades de cada criatura) a partir das páginas da TibiaWiki já descarregadas
(C:\\xampp\\_work\\crdmg\\dl\\pages\\p_*.json — wikitext com {{Infobox Creature}}).
Uso: python -I build_crinfo.py [raiz do site]
Formato por criatura (chave = nome em minúsculas, igual a data/creatures.json):
 ab: [[tipo, nome, dano, elemento, extra]]  tipo: melee|atk|heal|summon|haste|buff|debuff|outro
 sum/conv: custo de mana para invocar/convencer (null = não dá)
 ill/push/pobj/para/sinv: true/false (ilusionável, empurrável, empurra objetos, imune a paralisia, vê invisível)
 walk/thru: campos que evita / que atravessa;  run: foge com N de vida;  spawn: tipo de spawn
 att: tipo de ataque;  ptype: tipo principal;  bclass/blvl/occ: Bestiary;  boss: classe do Bosstiary
 maxdmg: dano máximo por turno;  heal: % de cura;  behav: comportamento (inglês curto)"""
import json, glob, re, sys, os

ROOT = sys.argv[1] if len(sys.argv) > 1 else r'C:\xampp\htdocs\grimorio'
SRC = r'C:\xampp\_work\crdmg\dl\pages'
ELS = {'physical': 'physical', 'fire': 'fire', 'ice': 'ice', 'earth': 'earth', 'energy': 'energy', 'death': 'death', 'holy': 'holy',
       'drown': 'drown', 'life drain': 'lifedrain', 'lifedrain': 'lifedrain', 'mana drain': 'manadrain', 'manadrain': 'manadrain',
       'poison': 'earth', 'bleeding': 'physical', 'burning': 'fire', 'electrified': 'energy', 'freezing': 'ice', 'cursed': 'death',
       'dazzled': 'holy', 'drowning': 'drown', 'agony': 'agony'}


def pages():
    out = {}
    for f in sorted(glob.glob(os.path.join(SRC, 'p_*.json'))):
        d = json.load(open(f, encoding='utf-8'))
        qs = d.get('query', {}).get('pages') if isinstance(d, dict) else None
        if qs is None and isinstance(d, dict):
            qs = d
        for p in (qs.values() if isinstance(qs, dict) else qs or []):
            if not isinstance(p, dict):
                continue
            rv = p.get('revisions') or []
            if not rv:
                continue
            m = rv[0].get('slots', {}).get('main', {})
            txt = m.get('*') or m.get('content') or rv[0].get('*')
            if p.get('title') and txt:
                out[p['title']] = txt
    return out


def block(txt, start):
    """devolve o conteúdo do template que começa em start ('{{'), com chavetas equilibradas"""
    i, depth = start, 0
    while i < len(txt):
        if txt.startswith('{{', i):
            depth += 1; i += 2; continue
        if txt.startswith('}}', i):
            depth -= 1; i += 2
            if depth == 0:
                return txt[start + 2:i - 2], i
            continue
        i += 1
    return txt[start + 2:], len(txt)


def split_top(s, sep='|'):
    parts, depth, cur, i = [], 0, '', 0
    while i < len(s):
        if s.startswith('{{', i) or s.startswith('[[', i):
            depth += 1; cur += s[i:i + 2]; i += 2; continue
        if s.startswith('}}', i) or s.startswith(']]', i):
            depth -= 1; cur += s[i:i + 2]; i += 2; continue
        if s[i] == sep and depth == 0:
            parts.append(cur); cur = ''; i += 1; continue
        cur += s[i]; i += 1
    parts.append(cur)
    return parts


def clean(v):
    v = re.sub(r'\[\[(?:[^|\]]*\|)?([^\]]*)\]\]', r'\1', v or '')
    v = re.sub(r'<[^>]+>', '', v)
    v = re.sub(r"'''?", '', v)
    return ' '.join(v.split()).strip()


def infobox(txt):
    i = txt.find('{{Infobox Creature')
    if i < 0:
        return None
    body, _ = block(txt, i)
    f = {}
    for part in split_top(body)[1:]:
        if '=' in part:
            k, v = part.split('=', 1)
            f[k.strip().lower()] = v.strip()
    return f


def el_of(args, kw):
    for v in [kw.get('element'), kw.get('condition')] + args[2:4]:
        if v:
            e = ELS.get(clean(v).lower())
            if e:
                return e
    return None


def abilities(raw):
    out = []
    i = 0
    while True:
        j = raw.find('{{', i)
        if j < 0:
            break
        body, i = block(raw, j)
        parts = split_top(body)
        name = parts[0].strip().lower()
        if name == 'ability list':
            out += abilities('|'.join(parts[1:]))
            continue
        args = [clean(p) for p in parts if '=' not in p or p.strip().startswith('{{')]
        kw = {}
        for p in parts[1:]:
            if '=' in p and not p.strip().startswith('{{'):
                k, v = p.split('=', 1)
                kw[k.strip().lower()] = v.strip()
        args = [a for a in args]
        if name == 'melee':
            out.append(['melee', 'Corpo a corpo', clean(args[1]) if len(args) > 1 else '', ELS.get(clean(kw.get('element', '')).lower(), 'physical'), ''])
        elif name in ('ability', 'abilities'):
            out.append(['atk', args[1] if len(args) > 1 else '', args[2] if len(args) > 2 and not ELS.get(args[2].lower()) else clean(kw.get('damage', '')), el_of(args, kw) or '', clean(kw.get('condition', ''))])
        elif name == 'healing':
            out.append(['heal', clean(kw.get('name', '')) or 'Cura', clean(kw.get('range', '')) or (args[1] if len(args) > 1 else ''), '', ''])
        elif name == 'summon':
            out.append(['summon', args[1] if len(args) > 1 else '', args[2] if len(args) > 2 else '', '', ''])
        elif name == 'haste':
            out.append(['haste', 'Haste', '', '', ''])
        elif name in ('debuff', 'buff'):
            out.append([name, args[1] if len(args) > 1 else name.title(), clean(kw.get('value', '')), '', clean(kw.get('duration', ''))])
        elif name not in ('scene',):
            out.append(['outro', clean(args[1] if len(args) > 1 else name), args[2] if len(args) > 2 else '', el_of(args, kw) or '', ''])
    return out


def yes(v):
    v = clean(v).lower()
    return True if v.startswith('yes') else False if v.startswith('no') else None


def mana(v):
    v = clean(v)
    m = re.search(r'\d+', v)
    return int(m.group()) if m and not v.startswith('--') else None


P = pages()
cr = json.load(open(os.path.join(ROOT, 'data', 'creatures.json'), encoding='utf-8'))
out = {}
for title, txt in P.items():
    f = infobox(txt)
    if not f:
        continue
    key = title.lower()
    if key not in cr:
        alt = clean(f.get('actualname', '')).lower()
        key = alt if alt in cr else key
    e = {'ab': abilities(f.get('abilities', ''))}
    for k, n in (('summon', 'sum'), ('convince', 'conv')):
        e[n] = mana(f.get(k, ''))
    for k, n in (('illusionable', 'ill'), ('pushable', 'push'), ('pushobjects', 'pobj'), ('paraimmune', 'para'), ('senseinvis', 'sinv')):
        v = yes(f.get(k, ''))
        if v is not None:
            e[n] = v
    for k, n in (('walksaround', 'walk'), ('walksthrough', 'thru'), ('runsat', 'run'), ('spawntype', 'spawn'), ('attacktype', 'att'),
                 ('primarytype', 'ptype'), ('bestiaryclass', 'bclass'), ('bestiarylevel', 'blvl'), ('occurrence', 'occ'),
                 ('bosstiaryclass', 'boss'), ('maxdmg', 'maxdmg'), ('healmod', 'heal'), ('behaviour', 'behav')):
        v = clean(f.get(k, ''))
        if v and v not in ('--', '?', 'none', 'None'):
            e[n] = v[:300]
    md = f.get('maxdmg', '')
    if '{{' in md:
        kv = dict((k.strip().lower(), v.strip()) for k, v in (x.split('=', 1) for x in split_top(block(md, md.find('{{'))[0])[1:] if '=' in x))
        num = lambda v: int(re.search(r'\d+', v).group()) if re.search(r'\d+', v or '') else 0
        tot = num(kv.get('total', '')) or sum(num(v) for k, v in kv.items() if k not in ('manadrain', 'summons', 'total'))
        if tot: e['maxdmg'] = str(tot)
        else: e.pop('maxdmg', None)
    for a in e['ab']:
        if a[0] == 'atk' and not re.search(r'\d', a[2] or '') and not a[3]:
            a[0] = 'outro'
    out[key] = e
dst = os.path.join(ROOT, 'data', 'crinfo.json')
with open(dst, 'w', encoding='utf-8', newline='') as fh:
    json.dump(out, fh, ensure_ascii=False, separators=(',', ':'))
n_ab = sum(1 for v in out.values() if v['ab'])
print(dst, os.path.getsize(dst), 'bytes |', len(out), 'criaturas |', n_ab, 'com ataques | em creatures.json:', sum(1 for k in out if k in cr))
for k in ('ferumbras', 'demon', 'dragon lord'):
    print(k, json.dumps(out.get(k), ensure_ascii=False)[:700])
