"""Línguas do Grimório e do Questski — extrair, construir e ver o que falta.

O código e os dados ficam em PT-PT; as traduções vivem em i18n/ e o shared/i18n.js aplica-as no browser.

  python -I _dev/i18n.py extract            # i18n/src/: frases da interface (ui.json), do conteúdo do Grimório
                                            # (content.json) e dos dados do Questski (q.json)
  python -I _dev/i18n.py build              # i18n/ui.<língua>.js, i18n/content.en.js, i18n/q.en.js, i18n/en/q/…
  python -I _dev/i18n.py status             # quantas frases faltam em cada língua
  python -I _dev/i18n.py todo ui pl 400     # lote de frases por traduzir (JSON {chave: ""}) para quem traduz
  python -I _dev/i18n.py todo content en 300
  python -I _dev/i18n.py todo q en 200
  python -I _dev/i18n.py merge ui pl lote.json   # junta um lote traduzido ({chave: tradução})
  python -I _dev/i18n.py harvest misses.jsonl    # junta à interface as frases que o browser não encontrou (modo recolha)

Ficheiros:
  i18n/src/ui.json        {chave: {"k": "x"|"p", "c": "contexto"}}  (x = exata; p = modelo com {0}, {1}… = valores do código)
  i18n/src/content.json   {hkey: frase}   frases do conteúdo do Grimório (G e data/*.json)
  i18n/src/q.json         {hkey: texto}   textos dos dados do Questski (guias, locais, índice, wiki)
  i18n/ui/<língua>.json   {chave: tradução}
  i18n/tm/en.json         {hkey: [origem, tradução]}   conteúdo do Grimório
  i18n/tmq/en.json        {hkey: [origem, tradução]}   dados do Questski
Regras para quem traduz: manter {0}, {1}… (podem mudar de ordem), as marcas do Questski ({npc:…}, {item:…|texto},
{key:…}, {coord:…}, **negrito**), os nomes do jogo em inglês (itens, criaturas, NPCs, sítios, feitiços, quests) e
tudo o que o jogador escreve aos NPCs. Uma tradução igual à origem não é guardada (fica a origem).
"""
import glob
import html
import json
import os
import re
import struct
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
I18N = os.path.join(ROOT, 'i18n')
UI_LANGS = ['en', 'pt-BR', 'pl', 'es', 'de', 'sv', 'nl']
CONTENT_LANG = 'en'  # língua de reserva do conteúdo (as outras caem nela; o PT-BR cai no PT-PT)


# ------------------------------------------------------------------ utilidades
def rd(p, default=None):
    try:
        with open(p, encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return default


def wr(p, obj, compact=False):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        if compact:
            json.dump(obj, f, ensure_ascii=False, separators=(',', ':'))
        else:
            json.dump(obj, f, ensure_ascii=False, indent=1, sort_keys=True)
            f.write('\n')


def norm(s):
    return re.sub(r'[\s  ]+', ' ', s).strip()


def hkey(s):
    """A mesma dispersão que o shared/i18n.js: FNV-1a 32 bits + djb2, sobre as unidades UTF-16."""
    b = s.encode('utf-16-le')
    a, d = 2166136261, 5381
    for (c,) in struct.iter_unpack('<H', b):
        a ^= c
        a = (a * 16777619) & 0xffffffff
        d = (d * 33 + c) & 0xffffffff
    return '%08x%08x' % (a, d)


SENT_RE = re.compile(r'(?<=[.!?…:;])\s+(?=\S)')


def sentences(s):
    return SENT_RE.split(s)


LETTER = re.compile(r'[A-Za-zÀ-ÖØ-öø-ÿ]')
PT_HINT = re.compile(r"[ãõçáéíóúâêôàÃÕÇÁÉÍÓÚÂÊÔÀ]|\b(de|da|do|das|dos|para|com|não|uma|um|os|as|em|que|por|sem|mais|ou|ao|aos|na|no|nas|nos|é|se|à|às|tu|teu|tua|já|até|só|quando|onde|como|cada|este|esta|isto|vai|fala|usa|sobe|desce|mata|leva|tens|podes|fica)\b", re.I)


# palavras que também existem em inglês ('do', 'as', 'no', 'os', 'um', 'se', 'em', 'a') não chegam para dizer que é PT
PT_STRONG = re.compile(r"[ãõçáéíóúâêôàÃÕÇÁÉÍÓÚÂÊÔÀ]|\b(de|da|das|dos|para|com|não|uma|que|por|sem|mais|ou|ao|aos|na|nas|nos|é|à|às|tu|teu|tua|teus|tuas|já|até|só|quando|onde|como|cada|este|esta|isto|vai|fala|usa|sobe|desce|mata|leva|tens|podes|fica|entre|depois|antes|também|pelo|pela|pelos|pelas|num|numa|dum|duma|vez|vezes|ainda|muito|pouco|sempre|nunca|aqui|ali|então|porque|sobre|contra|desde|durante|segue|abre|clica|escolhe|mostra|ver|nível|níveis|preço|lucro|do|um|em|piso|pisos|acima|abaixo|norte|sul|leste|oeste|nordeste|noroeste|sudeste|sudoeste|lado|segundo|terceiro|primeiro|fracos?|fortes?|imunes?|fogo|gelo|energia|morte|veneno|vende|compra|equipamento|banco|templo|barco|ilha|cidade|rua|loja|andar|subsolo|escadas|entrada|perto|junto|dentro|debaixo|frente|curas?|feitiços?|armas?|escudo|ataque|dano|todos|todas|mão|mãos|os|e|nenhum|nenhuma|recompensas?|dois|duas|três|quatro|cinco|seis|sete|oito|nove|dez|confirmar|completar|receber|entregar|falar|matar|abrir|apanhar|procurar|encontrar|ciclos?|missão|missões|passos?|empurrar|queijos?)\b", re.I)


def looks_pt(s):
    return bool(PT_STRONG.search(re.sub(r'<[^>]+>|\{[a-z]+:[^}]*\}', ' ', s)))


# ------------------------------------------------------------------ JS: literais de texto (com templates aninhados)
REGEX_PREV = set('(,=:[!&|?{};+-*%<>~^')
REGEX_KW = ('return', 'typeof', 'case', 'in', 'of', 'delete', 'void', 'throw', 'new', 'else', 'do', 'yield', 'await')


def js_literals(src):
    """Devolve [(parts, contexto)], parts = [("t", texto) | ("s", expressão)] de cada string/template do código."""
    out = []
    n = len(src)

    def prev_sig(i):
        j = i - 1
        while j >= 0 and src[j] in ' \t\r\n':
            j -= 1
        if j < 0:
            return '', ''
        k = j
        while k >= 0 and (src[k].isalnum() or src[k] in '_$'):
            k -= 1
        return src[j], src[k + 1:j + 1]

    def skip_regex(i):
        j = i + 1
        cls = False
        while j < n:
            c = src[j]
            if c == '\\':
                j += 2
                continue
            if c == '\n':
                return i + 1
            if cls:
                if c == ']':
                    cls = False
            elif c == '[':
                cls = True
            elif c == '/':
                j += 1
                while j < n and src[j].isalpha():
                    j += 1
                return j
            j += 1
        return j

    def scan_string(i, q):
        j = i + 1
        buf = []
        while j < n and src[j] != q:
            if src[j] == '\\' and j + 1 < n:
                if src[j + 1] == 'u' and re.fullmatch(r'[0-9a-fA-F]{4}', src[j + 2:j + 6]):
                    buf.append(chr(int(src[j + 2:j + 6], 16)))
                    j += 6
                    continue
                buf.append(unesc(src[j:j + 2], src, j))
                j += 2
                continue
            if src[j] == '\n':
                break
            buf.append(src[j])
            j += 1
        return ''.join(buf), j + 1

    def scan_template(i):
        """i aponta para o `; devolve (parts, fim)."""
        parts, buf = [], []
        j = i + 1
        while j < n:
            c = src[j]
            if c == '\\' and j + 1 < n:
                if src[j + 1] == 'u' and re.fullmatch(r'[0-9a-fA-F]{4}', src[j + 2:j + 6]):
                    buf.append(chr(int(src[j + 2:j + 6], 16)))
                    j += 6
                    continue
                buf.append(unesc(src[j:j + 2], src, j))
                j += 2
                continue
            if c == '`':
                if buf:
                    parts.append(('t', ''.join(buf)))
                return parts, j + 1
            if c == '$' and j + 1 < n and src[j + 1] == '{':
                if buf:
                    parts.append(('t', ''.join(buf)))
                    buf = []
                k = scan_code(j + 2, True)
                parts.append(('s', src[j + 2:k - 1]))
                j = k
                continue
            buf.append(c)
            j += 1
        return parts, j

    def scan_code(i, stop_brace):
        depth = 0
        j = i
        while j < n:
            c = src[j]
            if c in '"\'':
                s, j2 = scan_string(j, c)
                out.append(([('t', s)], src[max(0, j - 60):j2 + 20]))
                j = j2
                continue
            if c == '`':
                parts, j2 = scan_template(j)
                out.append((parts, src[max(0, j - 60):min(n, j2 + 20)]))
                j = j2
                continue
            if c == '/' and j + 1 < n and src[j + 1] == '/':
                k = src.find('\n', j)
                j = n if k < 0 else k
                continue
            if c == '/' and j + 1 < n and src[j + 1] == '*':
                k = src.find('*/', j + 2)
                j = n if k < 0 else k + 2
                continue
            if c == '/':
                pc, word = prev_sig(j)
                if pc == '' or pc in REGEX_PREV or word in REGEX_KW:
                    j = skip_regex(j)
                    continue
            if c == '{':
                depth += 1
            elif c == '}':
                if stop_brace and depth == 0:
                    return j + 1
                depth -= 1
            j += 1
        return j

    scan_code(0, False)
    return out


def unesc(s, src, j):
    m = {'\\n': '\n', '\\t': '\t', "\\'": "'", '\\"': '"', '\\`': '`', '\\\\': '\\', '\\/': '/', '\\$': '$'}
    if s in m:
        return m[s]
    if s == '\\u':
        h = src[j + 2:j + 6]
        if re.fullmatch(r'[0-9a-fA-F]{4}', h):
            return chr(int(h, 16))  # (o \u fica com 4 caracteres a mais no buffer; raro em textos)
    return s[1:]


# ------------------------------------------------------------------ fragmentos de HTML → chaves (igual ao shared/i18n.js)
INLINE = {'a', 'b', 'strong', 'i', 'em', 'span', 'small', 'kbd', 'sup', 'sub', 'abbr', 'mark', 'u', 's', 'time', 'q', 'cite',
          'code', 'br', 'img', 'svg', 'var', 'data'}
VOID = {'br', 'img', 'input', 'hr', 'meta', 'link', 'wbr', 'source', 'col', 'area', 'base', 'embed', 'param', 'track'}
SKIPT = {'script', 'style', 'noscript', 'textarea', 'template', 'svg'}
ATTRS = ('title', 'placeholder', 'aria-label', 'alt', 'data-copied')
S0, S1 = '', ''
TAG_RE = re.compile(r'<(/?)([a-zA-Z][\w:-]*)((?:[^>"\']|"[^"]*"|\'[^\']*\')*)>')
ATTR_RE = re.compile(r'([\w:-]+)\s*=\s*("([^"]*)"|\'([^\']*)\')')


class Node:
    __slots__ = ('tag', 'kids', 'attrs')

    def __init__(self, tag):
        self.tag, self.kids, self.attrs = tag, [], {}


def parse_fragment(parts):
    """parts: [("t", texto) | ("s", expr)] → árvore (os valores do código ficam como ("slot",))."""
    s = ''.join(p[1] if p[0] == 't' else S0 + str(i) + S1 for i, p in enumerate(parts))
    root = Node('#root')
    stack = [root]
    pos = 0

    def text(t):
        for i, piece in enumerate(re.split(S0 + r'\d+' + S1, t)):
            if i:
                stack[-1].kids.append(('slot',))
            if piece:
                stack[-1].kids.append(('text', html.unescape(piece)))

    for m in TAG_RE.finditer(s):
        if m.start() > pos:
            text(s[pos:m.start()])
        pos = m.end()
        close, tg, rest = m.group(1), m.group(2).lower(), m.group(3)
        if close:
            for k in range(len(stack) - 1, 0, -1):
                if stack[k].tag == tg:
                    del stack[k:]
                    break
            continue
        nd = Node(tg)
        for am in ATTR_RE.finditer(rest):
            nd.attrs[am.group(1).lower()] = am.group(3) if am.group(3) is not None else am.group(4)
        stack[-1].kids.append(nd)
        if tg not in VOID and not rest.rstrip().endswith('/'):
            stack.append(nd)
    if pos < len(s):
        text(s[pos:])
    return root


def has_block(nd):
    for k in nd.kids:
        if isinstance(k, Node):
            if k.tag not in INLINE or has_block(k):
                return True
    return False


def transparent_kid(k):
    if isinstance(k, Node):
        return k.tag in ('svg', 'img')
    return k[0] == 'text' and not k[1].strip()


def seq_key(seq):
    """seq: filhos (texto, ('slot',), Node em linha) → chave com {n}."""
    out, n = [], 0
    for k in seq:
        if isinstance(k, Node) or k[0] == 'slot':
            out.append('{%d}' % n)
            n += 1
        else:
            out.append(k[1])
    return norm(''.join(out)), n


def variants(seq):
    """A chave inteira e as versões sem valores do código nas pontas (o ícone de um botão vem muitas vezes de ${…})."""
    a, z = 0, len(seq)
    while a < z and transparent_kid(seq[a]):
        a += 1
    while z > a and transparent_kid(seq[z - 1]):
        z -= 1
    seq = seq[a:z]
    outs = [seq]
    lead = 0
    while lead < len(seq) and not isinstance(seq[lead], Node) and seq[lead][0] == 'slot':
        lead += 1
    trail = len(seq)
    while trail > lead and not isinstance(seq[trail - 1], Node) and seq[trail - 1][0] == 'slot':
        trail -= 1
    if lead:
        outs.append(seq[lead:])
    if trail < len(seq):
        outs.append(seq[:trail])
    if lead and trail < len(seq):
        outs.append(seq[lead:trail])
    return outs


def renumber(k):
    c = iter(range(1000))
    return re.sub(r'\{\d+\}', lambda m: '{%d}' % next(c), k)


def keys_of(nd, add, ctx):
    if nd.tag in SKIPT:
        return
    for a in ATTRS:
        if a in nd.attrs:
            v = nd.attrs[a]
            parts = re.split(S0 + r'\d+' + S1, v)
            add(norm('{0}'.join(html.unescape(p) for p in parts)) if len(parts) > 1 else norm(html.unescape(v)), ctx, len(parts) > 1)
    kids = nd.kids
    # frases = texto, valores do código e elementos em linha seguidos, entre elementos de bloco (como o shared/i18n.js)
    run = []
    for k in kids + [None]:
        if k is None or (isinstance(k, Node) and (k.tag not in INLINE or has_block(k))):
            if run:
                for seq in variants(run):
                    kk, ns = seq_key(seq)
                    add(renumber(kk), ctx, ns > 0)
            run = []
        else:
            run.append(k)
    for k in kids:
        if isinstance(k, Node):
            keys_of(k, add, ctx)


CODEY = re.compile(r'^[\w$.\-#:\[\]=>*+()\'"/\\@!?%&|^~,;{}<>]+$')
JUNK = re.compile(r'https?://|^#|^\.|=>|\bfunction\b|\breturn\b|;\s*\w+\s*[:=]|^[a-z-]+\s*:\s*[\w#"().%-]+;$|^[a-z]+[A-Z][A-Za-z0-9]*$'
                  r'|^(?:color|background|display|width|height|margin|padding|font|border|top|left|right|bottom|position|opacity|transform|grid[\w-]*|flex[\w-]*|gap|z-index)\s*:'
                  r'|^[\w-]+\.(?:js|css|json|png|gif|webp|svg|html)$|^[a-z]{1,3}\d*$|^[a-z]+(?:-[a-z0-9]+)+-?$|^[a-z0-9_]+_[a-z0-9_]+$'
                  r'|^[A-Z0-9_]{2,}$|^--|-$|^\d+(?:px|em|rem|%|ms|s|deg|vh|vw)$|^<!--'
                  r'|^[MmLlHhVvCcSsQqTtAaZz0-9 .,\-]*\d[MmLlHhVvCcSsQqTtAaZz0-9 .,\-]*$'  # caminhos de SVG
                  r'|^(?:afterbegin|afterend|beforebegin|beforeend|auxclick|contextmenu|focusin|focusout|keydown|keyup|pointerdown|pointerup|mousedown|mouseup|mousemove|touchstart|touchend|scroll|resize|change|input|click|submit|load|error|hidden|visible|checked|disabled|boolean|number|string|object|undefined|function|canvas|button|dialog|figcaption)$')


def good_key(k):
    if len(k) < 2 or not re.search(r'[A-Za-zÀ-ÖØ-öø-ÿ]{2}', re.sub(r'\{\d+\}', '', k)):
        return False
    if JUNK.search(k):
        return False
    if ' ' not in k and CODEY.match(k) and (re.search(r'[_#:/\\=;{}()\[\]<>@$]', k) or re.search(r'\w\.\w', k)):
        return False
    if re.fullmatch(r'(\{\d+\}\s*)+', k):
        return False
    if re.search(r'[{}]', re.sub(r'\{\d+\}', '', k)):
        return False
    return True


def extract_ui():
    found = {}

    def add(k, ctx, is_pat):
        if not good_key(k):
            return
        e = found.get(k)
        kind = 'p' if is_pat and re.search(r'\{\d+\}', k) else 'x'
        if e is None:
            found[k] = {'k': kind, 'c': ctx}
        elif kind == 'p':
            e['k'] = 'p'

    # HTML fixo
    idx = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
    g0 = idx.index('<script type="application/json" id="G">')
    g1 = idx.index('</script>', g0)
    a = idx.index('<script>', g1)
    b = idx.index('</script>', a)
    app = idx[a + 8:b]
    body = idx[:g0] + idx[g1:a]
    body = re.sub(r'<script.*?</script>|<style.*?</style>|<!--.*?-->', '', body, flags=re.S)
    keys_of(parse_fragment([('t', body)]), add, 'index.html (HTML)')
    qhtml = open(os.path.join(ROOT, 'quests', 'index.html'), encoding='utf-8').read()
    qbody = re.sub(r'<script.*?</script>|<style.*?</style>|<!--.*?-->', '', qhtml, flags=re.S)
    keys_of(parse_fragment([('t', qbody)]), add, 'quests/index.html (HTML)')
    # código
    sources = [('index.html', app)] + [(os.path.relpath(p, ROOT).replace('\\', '/'), open(p, encoding='utf-8').read())
                                       for p in sorted(glob.glob(os.path.join(ROOT, 'quests', 'js', '*.js')))]
    for name, src in sources:
        for parts, ctx in js_literals(src):
            if not any(p[0] == 't' and LETTER.search(p[1]) for p in parts):
                continue
            c = name + ': ' + re.sub(r'\s+', ' ', ctx)[:220]
            keys_of(parse_fragment(parts), add, c)
    # recolhidas no browser (modo recolha) e acrescentadas à mão
    for k, v in (rd(os.path.join(I18N, 'src', 'ui-extra.json'), {}) or {}).items():
        if k not in found:
            found[k] = v
    wr(os.path.join(I18N, 'src', 'ui.json'), found)
    print('interface:', len(found), 'frases (', sum(1 for v in found.values() if v['k'] == 'p'), 'modelos )')


# ------------------------------------------------------------------ conteúdo do Grimório (G e data/*.json) → frases
G_SKIP = {'hm', 'sp', 'gems', 'pm', 'cr', 'lt', 'mon', 'np', 'mc', 'vr', 'ha', 'built', 'tpdate', 'spriteCols', 'wheel', 'towns', 'marapur'}
G_ALL = {'mcn'}  # nomes PT sem acentos nem palavras pequenas (ex. 'Humanos'): entram todos
DATA_SKIP = {'guias.json', 'spawns.json', 'crdmg.json', 'npcpos.json', 'items.json'}


def load_G():
    s = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
    g0 = s.index('<script type="application/json" id="G">')
    g1 = s.index('</script>', g0)
    return json.loads(s[g0 + len('<script type="application/json" id="G">'):g1])


def content_strings():
    out = []

    def walk(o, every=False):
        if isinstance(o, dict):
            for v in o.values():
                walk(v, every)
        elif isinstance(o, list):
            for v in o:
                walk(v, every)
        elif isinstance(o, str):
            if len(o) >= 3 and LETTER.search(o) and (every or looks_pt(o)) and not o.startswith('http'):
                out.append(o)

    G = load_G()
    for k, v in G.items():
        if k not in G_SKIP:
            walk(v, k in G_ALL)
    for p in sorted(glob.glob(os.path.join(ROOT, 'data', '*.json'))):
        if os.path.basename(p) in DATA_SKIP:
            continue
        walk(rd(p))
    return out


def extract_content():
    found = {}
    for s in content_strings():
        n = norm(re.sub(r'<[^>]+>', ' ', s)) if '<' in s else norm(s)
        for piece in [n] if len(sentences(n)) < 2 else sentences(n):
            if LETTER.search(piece) and len(piece) >= 3:
                found[hkey(piece)] = piece
                # nomes curtos aparecem também em minúsculas no meio de frases (ex. 'Demónios' → 'demónios')
                if len(piece.split()) <= 3 and piece[0].isupper():
                    low = piece[0].lower() + piece[1:]
                    found[hkey(low)] = low
    wr(os.path.join(I18N, 'src', 'content.json'), found)
    print('conteúdo do Grimório:', len(found), 'frases,', sum(len(v) for v in found.values()), 'caracteres')


# ------------------------------------------------------------------ dados do Questski → textos (sobreposições por caminho)
Q_KEYS = {'summary', 'duration', 'legend_pt', 'label', 'caption', 'text', 'title', 'intro', 'tip', 'warning', 'reward', 'note',
          'notes', 'requirements', 'tips', 'what', 'when', 'head', 'rows', 'entrance', 'arrive', 'leave', 'warnings', 'near',
          'type', 'items', 'location', 'how', 'desc', 'step', 'where', 'name_pt'}
Q_NEVER = {'slug', 'file', 'src', 'npc', 'item', 'creature', 'x', 'y', 'z', 'you', 'img', 'href', 'url', 'id', 'key', 'kind',
           'category', 'region', 'regions', 'html', 'aka', 'name', 'npcs', 'dangers', 'achievements', 'rewards_raw', 'reward_raw'}


def q_files():
    base = os.path.join(ROOT, 'quests')
    fs = [os.path.join(base, 'data', 'index.json'), os.path.join(base, 'data', 'places.json')]
    fs += sorted(glob.glob(os.path.join(base, 'data', 'quests', '*.json')))
    fs += sorted(glob.glob(os.path.join(base, 'data', 'wiki', '*.json')))
    return [(os.path.relpath(p, base).replace('\\', '/'), p) for p in fs]


def q_units(obj, rel):
    """[(caminho, texto)] dos textos traduzíveis de um JSON do Questski."""
    out = []
    wiki = rel.startswith('data/wiki/')

    def walk(o, path, live):
        if isinstance(o, dict):
            for k, v in o.items():
                if k in Q_NEVER:
                    continue
                if wiki and not path and k != 'howto':
                    continue
                walk(v, path + [k], live or k in Q_KEYS)
        elif isinstance(o, list):
            for i, v in enumerate(o):
                walk(v, path + [i], live)
        elif isinstance(o, str) and live and len(o) >= 3 and LETTER.search(o) and looks_pt(o):
            out.append((path, o))

    walk(obj, [], False)
    return out


def extract_q():
    found = {}
    for rel, p in q_files():
        for path, s in q_units(rd(p), rel):
            found[hkey(s)] = s
    wr(os.path.join(I18N, 'src', 'q.json'), found)
    print('dados do Questski:', len(found), 'textos,', sum(len(v) for v in found.values()), 'caracteres')


# ------------------------------------------------------------------ construir
def js_obj(o):
    return json.dumps(o, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')


def build():
    src = rd(os.path.join(I18N, 'src', 'ui.json'), {})
    for lang in UI_LANGS:
        tr = rd(os.path.join(I18N, 'ui', lang + '.json'), {}) or {}
        x, p = {}, []
        for k, t in sorted(tr.items()):
            if not t or t == k:
                continue
            if src.get(k, {}).get('k') == 'p':
                p.append([k, t])
            else:
                x[k] = t
        p.sort(key=lambda e: -len(re.sub(r'\{\d+\}', '', e[0])))
        with open(os.path.join(I18N, 'ui.%s.js' % lang), 'w', encoding='utf-8', newline='\n') as f:
            f.write('/* gerado por _dev/i18n.py build — traduz em i18n/ui/%s.json */\nwindow.I18N_UI=%s;\n' % (lang, js_obj({'x': x, 'p': p})))
        print('ui.%s.js: %d exatas, %d modelos' % (lang, len(x), len(p)))
    for lang in UI_LANGS:
        build_content(lang)


def tm_text(e):
    """Entrada da memória de tradução: [origem, tradução] (antigo) ou só a tradução."""
    if isinstance(e, list):
        return e[1] if len(e) > 1 else None
    return e if isinstance(e, str) else None


def build_content(lang):
    # conteúdo do Grimório: frases
    tm = rd(os.path.join(I18N, 'tm', lang + '.json'), {}) or {}
    src = rd(os.path.join(I18N, 'src', 'content.json'), {}) or {}
    c = {}
    for h, e in tm.items():
        t = tm_text(e)
        if t and t != src.get(h):
            c[h] = t
    with open(os.path.join(I18N, 'content.%s.js' % lang), 'w', encoding='utf-8', newline='\n') as f:
        f.write('/* gerado por _dev/i18n.py build — conteúdo do Grimório (frases), de i18n/tm/%s.json */\n'
                'window.I18N_C=window.I18N_C||{};window.I18N_C[%s]=%s;\n' % (lang, json.dumps(lang), js_obj(c)))
    # Questski: uma sobreposição por ficheiro de dados
    tmq = rd(os.path.join(I18N, 'tmq', lang + '.json'), {}) or {}
    files = {}
    outdir = os.path.join(I18N, lang, 'q')
    for rel, p in q_files():
        ov = []
        for path, s in q_units(rd(p), rel):
            h = hkey(s)
            t = tm_text(tmq.get(h))
            if t and t != s:
                ov.append([path, h, t])
        dst = os.path.join(outdir, rel)
        if ov:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            with open(dst, 'w', encoding='utf-8', newline='\n') as f:
                json.dump(ov, f, ensure_ascii=False, separators=(',', ':'))
            files[rel] = 1
        elif os.path.exists(dst):
            os.remove(dst)
    with open(os.path.join(I18N, 'q.%s.js' % lang), 'w', encoding='utf-8', newline='\n') as f:
        f.write('/* gerado por _dev/i18n.py build — ficheiros do Questski com tradução em i18n/%s/q/ */\n'
                'window.I18N_QF=window.I18N_QF||{};window.I18N_QF[%s]=%s;\n' % (lang, json.dumps(lang), js_obj(files)))
    print('%s: conteúdo %d frases, Questski %d ficheiros' % (lang, len(c), len(files)))


# ------------------------------------------------------------------ o que falta / lotes
def status():
    src = rd(os.path.join(I18N, 'src', 'ui.json'), {})
    print('interface: %d frases' % len(src))
    for lang in UI_LANGS:
        tr = rd(os.path.join(I18N, 'ui', lang + '.json'), {}) or {}
        miss = [k for k in src if k not in tr]
        print('  %-6s faltam %5d' % (lang, len(miss)))
    for name, tmn in (('content', 'tm'), ('q', 'tmq')):
        s = rd(os.path.join(I18N, 'src', name + '.json'), {})
        print('%s: %d textos (%d caracteres)' % (name, len(s), sum(len(v) for v in s.values())))
        for lang in UI_LANGS:
            tm = rd(os.path.join(I18N, tmn, lang + '.json'), {}) or {}
            miss = [h for h in s if h not in tm]
            print('  %-6s faltam %6d (%d caracteres)' % (lang, len(miss), sum(len(s[h]) for h in miss)))


def todo(kind, lang, n, skip=0):
    n = int(n)
    skip = int(skip)
    if kind == 'ui':
        src = rd(os.path.join(I18N, 'src', 'ui.json'), {})
        tr = rd(os.path.join(I18N, 'ui', lang + '.json'), {}) or {}
        keys = [k for k in sorted(src) if k not in tr][skip:skip + n]
        out = {k: {'ctx': src[k]['c'][:200], 'en': (rd(os.path.join(I18N, 'ui', 'en.json'), {}) or {}).get(k, '') if lang != 'en' else ''} for k in keys}
    else:
        s = rd(os.path.join(I18N, 'src', kind + '.json'), {})
        tm = rd(os.path.join(I18N, 'tm' if kind == 'content' else 'tmq', lang + '.json'), {}) or {}
        keys = [h for h in sorted(s, key=lambda h: s[h]) if h not in tm][skip:skip + n]
        out = {h: s[h] for h in keys}
    json.dump(out, sys.stdout, ensure_ascii=False, indent=1)
    print()


def merge(kind, lang, path):
    new = rd(path, {})
    if kind == 'ui':
        p = os.path.join(I18N, 'ui', lang + '.json')
        cur = rd(p, {}) or {}
        src = rd(os.path.join(I18N, 'src', 'ui.json'), {})
        bad = 0
        for k, t in new.items():
            if isinstance(t, dict):
                t = t.get('t') or t.get('tr') or ''
            if not isinstance(t, str) or not t:
                continue
            # um valor escondido num comentário (ex.: o "s" do plural português) passa a {n!}: o browser não o mostra
            t = re.sub(r'<!--\s*\{(\d+)\}\s*-->', lambda m: '{%s!}' % m.group(1), t)
            if sorted(re.findall(r'\{(\d+)\}', k)) != sorted(re.findall(r'\{(\d+)!?\}', t)):
                bad += 1
                continue
            cur[k] = t
        wr(p, cur)
        print('ui/%s.json: +%d (marcas {n} erradas: %d)' % (lang, len(new) - bad, bad))
    else:
        p = os.path.join(I18N, 'tm' if kind == 'content' else 'tmq', lang + '.json')
        cur = rd(p, {}) or {}
        s = rd(os.path.join(I18N, 'src', kind + '.json'), {})
        ok = bad = 0
        for h, t in new.items():
            if h in s and isinstance(t, str) and t:
                if kind == 'q' and sorted(re.findall(r'\{(?:npc|item|creature|spell|key|coord|wiki):', s[h])) != sorted(re.findall(r'\{(?:npc|item|creature|spell|key|coord|wiki):', t)):
                    bad += 1
                    continue
                cur[h] = [s[h], t] if kind == 'content' else t
                ok += 1
        wr(p, cur)
        print('%s/%s.json: +%d (marcas erradas: %d)' % ('tm' if kind == 'content' else 'tmq', lang, ok, bad))


NUM_RE = re.compile(r'(?<![\w{}])[-+−]?\d+(?:[.,   ]\d+)*(?:kk|k|%)?(?![\w}])')
TOKEN_RE = re.compile(r'\{(?:npc|item|creature|spell|wiki|key|coord):([^}|]*)(?:\|([^}]*))?\}')


class Cover:
    """Imita o shared/i18n.js para saber se uma frase vista no browser já tem tradução possível."""

    def __init__(self):
        self.src = rd(os.path.join(I18N, 'src', 'ui.json'), {}) or {}
        self.extra = rd(os.path.join(I18N, 'src', 'ui-extra.json'), {}) or {}
        self.cont = rd(os.path.join(I18N, 'src', 'content.json'), {}) or {}
        self.pats = []
        for k, v in list(self.src.items()) + list(self.extra.items()):
            if v.get('k') == 'p':
                parts = re.split(r'\{(\d+)\}', k)
                self.pats.append(re.compile('^' + ''.join('(.+?)' if i % 2 else re.escape(p) for i, p in enumerate(parts)) + '$'))
        q = rd(os.path.join(I18N, 'src', 'q.json'), {}) or {}
        self.qblob = '\n'.join(norm(TOKEN_RE.sub(lambda m: m.group(2) or m.group(1), v)).replace('**', '').replace('*', '') for v in q.values())

    def one(self, k):
        if k in self.src or k in self.extra or hkey(k) in self.cont:
            return True
        if any(p.match(k) for p in self.pats):
            return True
        ss = sentences(k)
        return len(ss) > 1 and all(hkey(s) in self.cont for s in ss)

    def text(self, k):
        if self.one(k):
            return True
        parts = k.split(' · ')
        return len(parts) > 1 and all(self.one(p) or not looks_pt(p) for p in parts)

    def __call__(self, k):
        if self.text(k):
            return True
        if re.search(r'\{\d+\}', k):
            pieces = [norm(p) for p in re.split(r'\{\d+\}', k) if LETTER.search(p)]
            if pieces and all(self.text(p) or not looks_pt(p) for p in pieces):
                return True
        return self.questski(k)

    def questski(self, k):
        # textos dos guias do Questski (traduzidos pelos dados, não pela interface)
        bits = [b.strip(' —–-·:;,.()') for b in re.split(r'\{\d+\}', k)]
        bits = [b for b in bits if len(b) >= 3 and LETTER.search(b)]
        return bool(bits) and all(b in self.qblob for b in bits)


SEPS = (' — ', ' · ', ': ', ' – ', ' - ')


def generalize(k):
    """Números → {n}; partes que não são PT (nomes próprios: 'Cael — abrir na wiki') → {n}; as marcas {n} ficam; tudo renumerado."""
    g = NUM_RE.sub('{9}', k)
    for sep in SEPS:
        if sep in g:
            parts = g.split(sep)
            if any(looks_pt(p) for p in parts):
                parts = [p if looks_pt(p) or not LETTER.search(re.sub(r'\{\d+\}', '', p)) else '{9}' for p in parts]
                g = sep.join(parts)
    g = renumber(g)
    return g, bool(re.search(r'\{\d+\}', g))


def harvest(path):
    extra_p = os.path.join(I18N, 'src', 'ui-extra.json')
    extra = rd(extra_p, {}) or {}
    done = set()
    for lang in UI_LANGS:
        done |= set((rd(os.path.join(I18N, 'ui', lang + '.json'), {}) or {}).values())
    cov = Cover()
    add = 0
    seen = set()
    with open(path, encoding='utf-8') as f:
        for line in f:
            try:
                row = json.loads(line)
            except ValueError:
                continue
            k = row.get('k')
            if not k or k in seen or k in done:
                continue
            seen.add(k)
            if not looks_pt(re.sub(r'\{\d+\}', ' ', k)) or cov(k):
                continue
            g, pat = generalize(k)
            if g in extra or g in cov.src or not good_key(g):
                continue
            if pat and not re.search(r'[A-Za-zÀ-ÖØ-öø-ÿ]{3}', re.sub(r'\{\d+\}', '', g)):
                continue
            extra[g] = {'k': 'p' if pat else 'x', 'c': 'recolhida: ' + str(row.get('page', '')) + ' · ex.: ' + k[:120]}
            add += 1
    wr(extra_p, extra)
    print('recolhidas: +%d (total %d); corre extract outra vez' % (add, len(extra)))


if __name__ == '__main__':
    a = sys.argv[1:]
    if not a or a[0] in ('-h', '--help'):
        print(__doc__)
    elif a[0] == 'extract':
        extract_ui()
        extract_content()
        extract_q()
    elif a[0] == 'build':
        build()
    elif a[0] == 'status':
        status()
    elif a[0] == 'todo':
        todo(*a[1:])
    elif a[0] == 'merge':
        merge(*a[1:])
    elif a[0] == 'harvest':
        harvest(a[1])
    else:
        print(__doc__)
