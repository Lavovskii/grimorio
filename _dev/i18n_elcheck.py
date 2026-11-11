"""Elementos dos caminhos (negrito, itálico, links de NPC/item/criatura/feitiço, <kbd>) nas frases traduzidas.

O shared/i18n.js põe cada elemento de uma frase traduzida onde encontra o texto dele (ou a sua tradução, nas línguas do
conteúdo e na interface), por ordem; se não o encontra, junta-o outra vez no fim da frase (ex.: «… im ( Osten32735…»).
Este script faz o mesmo que o run() do i18n.js, com os dicionários de i18n/tm/ e i18n/ui/, para cada passo do
caminhos.json, do hunt-access.json e do boss-access.json (cam_units, na forma do ecrã).

Uso: python3 -I _dev/i18n_elcheck.py <língua> [--json saída.json]   ou   python3 -I _dev/i18n_elcheck.py --keys
  sem opções: frases em que um elemento fica repetido no fim («fim») ou só se acha a meio de uma palavra («palavra»:
  às vezes está bem, ex.: «Erd» em «Erdschaden»; às vezes não, ex.: o negrito «e» dentro de «the»)
  --keys: textos do ecrã (frases e elementos com rótulo) sem chave em i18n/src/content.json (vale para todas as línguas;
  são quase todos nomes do jogo e números, que ficam iguais: serve para ver a olho se escapou algum texto português)
Sai com 1 se houver um elemento repetido no fim (N=<n> mostra os primeiros n casos; 20 por omissão)."""
import importlib.util
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
spec = importlib.util.spec_from_file_location('i18n', os.path.join(ROOT, '_dev', 'i18n.py'))
I = importlib.util.module_from_spec(spec)
spec.loader.exec_module(I)
rd = lambda p: I.rd(os.path.join(ROOT, p), {}) or {}
ELK = {'npc', 'spell', 'item', 'creature', 'key'}  # as marcas que o qmd faz elemento (o {wiki:…} é só texto)
WORD = re.compile(r'[^\W_]')


def tok_txt(m):
    return (m.group(2) if m.group(1) == 'key' else (m.group(3) or m.group(2))).strip()


def els_of(raw):
    """[(texto de cada elemento, é um nome do jogo)] de um pedaço, por ordem, como o qmd do index.html o põe no ecrã: as marcas
    ficam guardadas (\x00n\x00) enquanto se fazem o negrito (\x01n\x01) e o itálico (\x02n\x02)."""
    tok, inner = [], []
    x = I.CAM_TOKEN.sub(lambda m: tok.append(m) or '\x00%d\x00' % (len(tok) - 1), raw)
    x = re.sub(r'\*\*([^*]+)\*\*', lambda m: inner.append(m.group(1)) or '\x01%d\x01' % (len(inner) - 1), x)
    x = re.sub(r'(^|[^*])\*([^*\s][^*]*)\*', lambda m: m.group(1) + (inner.append(m.group(2)) or '\x02%d\x02' % (len(inner) - 1)), x)
    MARK = r'([\x00\x01\x02])(\d+)\1'
    shown = lambda y: re.sub(MARK, lambda m: tok_txt(tok[int(m.group(2))]) if m.group(1) == '\x00' else shown(inner[int(m.group(2))]), y)
    els = []
    for m in re.finditer(MARK, x):
        k = tok[int(m.group(2))] if m.group(1) == '\x00' else None
        if not k:
            els.append((shown(inner[int(m.group(2))]), 0))
        elif k.group(1) in ELK:
            # (sem rótulo é o nome do NPC/item/criatura/feitiço ou a palavra do jogo: fica igual em todas as línguas)
            els.append((k.group(2), 1) if k.group(1) == 'key' or not k.group(3) else (k.group(3), 0))
    return [(I.norm(e), nm) for e, nm in els if I.norm(e)]


def pieces():
    """[(texto do ecrã, els_of)] de cada pedaço entre botões {coord:} de cada texto dos caminhos."""
    out, seen = [], set()
    for s, npc in I.cam_units():
        for t in {s, I.cam_say_cut(s, npc)}:
            for raw in re.split(r'\{coord:\d+,\d+,\d+\}', t):
                r = I.cam_render(raw)
                if len(r) != 1 or r[0] in seen:
                    continue
                seen.add(r[0])
                out.append((r[0], els_of(raw)))
    return out


def word_at(t, s, start):
    """O wordAt do i18n.js: onde está s em t (a partir de start) como palavra inteira, ou -1."""
    i = t.find(s, start)
    while i >= 0:
        if not (WORD.match(s[0]) and i and WORD.match(t[i - 1])) and not (WORD.match(s[-1]) and WORD.match(t[i + len(s):i + len(s) + 1] or ' ')):
            return i
        i = t.find(s, i + 1)
    return -1


def check(lang):
    cls = ['pt-BR'] if lang == 'pt-BR' else ['en'] if lang == 'en' else [lang, 'en']
    C = [{h: I.tm_text(e) for h, e in rd('i18n/tm/%s.json' % l).items() if I.tm_text(e)} for l in cls]
    src_ui = rd('i18n/src/ui.json')
    UI = {k: t for k, t in rd('i18n/ui/%s.json' % lang).items() if t and src_ui.get(k, {}).get('k') != 'p'}
    OUT = set(UI.values()) | {v for c in C for v in c.values()}
    cget = lambda h: next((c[h] for c in C if h in c), None)

    def content(p):
        t = cget(I.hkey(p))
        if t is not None:
            return t
        ss = I.sentences(p)
        if len(ss) < 2:
            return None
        tr = [cget(I.hkey(s)) or (None if s in OUT else UI.get(s)) for s in ss]
        return ' '.join(tr) if all(x is not None for x in tr) else None   # só uma tradução inteira põe os elementos

    bad, n = [], 0
    for plain, els in pieces():
        t = content(plain) if els else None
        if t is None:
            continue
        n += 1
        cur, miss = 0, []
        for e, _ in els:
            # como o run() do i18n.js: primeiro como palavra inteira (texto, depois traduções), só depois em qualquer sítio
            alts = [e] + [x for x in [c.get(I.hkey(e)) for c in C] + [UI.get(e)] if x]
            hit = next(((word_at(t, a, cur), a) for a in alts if word_at(t, a, cur) >= 0), None)
            if not hit:
                hit = next(((t.find(a, cur), a) for a in alts if t.find(a, cur) >= 0), None)
                if hit:
                    miss.append(('palavra', e, hit[1]))
            if hit:
                cur = hit[0] + len(hit[1])
            else:
                miss.append(('fim', e, alts[1] if len(alts) > 1 else None))
        if miss:
            bad.append({'h': I.hkey(plain), 'src': plain, 'tr': t, 'els': [e for e, _ in els], 'miss': miss})
    fim = sum(1 for b in bad if any(m[0] == 'fim' for m in b['miss']))
    print('%s: %d frases traduzidas com elementos; %d com um elemento repetido no fim, %d com um elemento a meio de uma palavra'
          % (lang, n, fim, len(bad) - fim))
    return bad


def keys():
    src = rd('i18n/src/content.json')
    bad = []
    for plain, els in pieces():
        for x in [plain] + [e for e, nm in els if not nm]:
            if I.hkey(x) not in src and WORD.search(x):
                bad.append({'h': I.hkey(x), 'src': x, 'in': plain if x != plain else None})
    print('%d textos do ecrã sem chave em i18n/src/content.json' % len(bad))
    return bad


if __name__ == '__main__':
    assert els_of('Paga **2 {item:Bloody Tears}** ao {npc:Hal} ({key:hi}) e *vai*.') == [('2 Bloody Tears', 0), ('Hal', 1), ('hi', 1), ('vai', 0)]
    assert word_at('Darashia (hi, yes', 'hi', 0) == 10 and word_at('Erdschaden', 'Erd', 0) == -1
    a = sys.argv[1:]
    if not a or a[0] in ('-h', '--help'):
        sys.exit(__doc__)
    res = keys() if '--keys' in a else check(a[0])
    if '--json' in a:
        json.dump(res, open(a[a.index('--json') + 1], 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    for b in res[:int(os.environ.get('N', '20'))]:
        print(json.dumps(b, ensure_ascii=False))
    sys.exit(1 if '--keys' not in a and any(m[0] == 'fim' for b in res for m in b['miss']) else 0)
