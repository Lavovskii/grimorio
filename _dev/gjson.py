"""Lê e grava o G (os dados embebidos no index.html, <script type="application/json" id="G">) no formato canónico.

Formato canónico ("largura 200"): um valor fica em JSON compacto quando cabe em 200 caracteres; senão abre '{' ou '['
com um filho por linha, recuo de 1 espaço por nível, vírgula no fim de cada filho menos o último e a ordem das chaves
de sempre. Cada registo (uma hunt, um item, uma criatura pequena) fica numa linha, por isso o Git junta sem conflitos
as alterações de duas pessoas a registos diferentes. '</' e '<!--' ficam escapados ('<\\/' e '<\\u0021--'), para o
texto não fechar o <script>. O bloco começa e acaba numa quebra de linha (as tags ficam em linhas próprias).

Em scripts que mudam dados (nunca json.dumps à mão):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from gjson import load_G, save_G
    s, G, span = load_G(root)        # texto do index.html, dados, (início, fim) do bloco do G
    ...muda G...
    save_G(root, s, G, span)          # confirma que o JSON lê igual e grava em UTF-8 com newline=''

Linha de comando:
    python -I gjson.py [raiz] --format   reescreve o G no formato canónico (correr outra vez não muda nada)
    python -I gjson.py [raiz] --check    sai com 0 se o G lê bem e está no formato canónico; senão diz a linha
                                         e a coluna do problema no index.html e sai com 1
Sem raiz: a pasta-mãe de _dev quando o script está em _dev, senão C:\\xampp\\htdocs\\grimorio.
Depois de resolver um conflito no index.html: python -I _dev/gjson.py --check e o smoke.mjs."""
import json
import os
import re
import sys

WIDTH = 200
RX = re.compile(r'(<script[^>]*id="G"[^>]*>)(.*?)(</script>)', re.S)


def default_root():
    """Raiz do site quando não se indica nenhuma: a pasta-mãe de _dev (clone do repositório) ou o site público."""
    here = os.path.dirname(os.path.abspath(__file__))
    if os.path.basename(here).lower() == '_dev':
        return os.path.dirname(here)
    return r'C:\xampp\htdocs\grimorio'


def _c(v):
    # allow_nan=False: NaN/Infinity não são JSON válido para o JSON.parse do browser
    return json.dumps(v, ensure_ascii=False, separators=(',', ':'), allow_nan=False)


def _key(k):
    # chaves como o json.dumps as escreve (números, true/false/null passam a texto)
    return json.dumps(k if isinstance(k, str) else _c(k), ensure_ascii=False)


def _dump(v, ind=0, W=WIDTH):
    t = _c(v)
    if len(t) <= W or not isinstance(v, (dict, list)) or not v:
        return t
    pad = ' ' * (ind + 1)
    if isinstance(v, dict):
        return '{\n' + ',\n'.join(pad + _key(k) + ':' + _dump(x, ind + 1, W) for k, x in v.items()) + '\n' + ' ' * ind + '}'
    return '[\n' + ',\n'.join(pad + _dump(x, ind + 1, W) for x in v) + '\n' + ' ' * ind + ']'


def dump_G(G):
    """Texto canónico do bloco do G (com a quebra de linha no início e no fim)."""
    return '\n' + _dump(G).replace('</', '<\\/').replace('<!--', '<\\u0021--') + '\n'


def _strict(t):
    raise ValueError('valor %s não é JSON válido' % t)


def parse_G(text):
    """json.loads como o do browser: recusa NaN e Infinity."""
    return json.loads(text, parse_constant=_strict)


def load_G(root=None):
    """Lê <root>/index.html. Devolve (s, G, span): o texto todo, os dados e (início, fim) do bloco do G em s."""
    p = os.path.join(root or default_root(), 'index.html')
    with open(p, encoding='utf-8', newline='') as f:
        s = f.read()
    m = RX.search(s)
    if not m:
        raise ValueError('não encontrei <script ... id="G"> em ' + p)
    return s, parse_G(m.group(2)), (m.start(2), m.end(2))


def _put(s, G, span):
    block = dump_G(G)
    if parse_G(block) != parse_G(_c(G)):
        raise ValueError('o G gravado não lê igual aos dados')
    out = s[:span[0]] + block + s[span[1]:]
    if '\r' in out:
        raise ValueError("o index.html tem '\\r' (fins de linha CRLF): repõe os fins de linha LF antes de gravar")
    return out, (span[0], span[0] + len(block))


def put_G(s, G, span):
    """Devolve o texto do index.html com o G no formato canónico no lugar de span (não grava nada)."""
    return _put(s, G, span)[0]


def save_G(root, s, G, span):
    """Grava o G em <root>/index.html no formato canónico (só se mudou). Devolve (s, span) novos."""
    out, span2 = _put(s, G, span)
    if out != s:
        with open(os.path.join(root or default_root(), 'index.html'), 'w', encoding='utf-8', newline='') as f:
            f.write(out)
    return out, span2


def _where(s, pos):
    line = s.count('\n', 0, pos) + 1
    return line, pos - (s.rfind('\n', 0, pos) + 1) + 1


def check(root=None):
    """0 = G lê bem e está no formato canónico; 1 = há um problema (escreve qual e onde)."""
    p = os.path.join(root or default_root(), 'index.html')
    with open(p, encoding='utf-8', newline='') as f:
        s = f.read()
    if '\r' in s:
        ln, col = _where(s, s.index('\r'))
        print(f"ERRO: o index.html tem '\\r' (fins de linha CRLF), a primeira na linha {ln}. O Git deve guardar o ficheiro tal e qual (.gitattributes: * -text).")
        return 1
    m = RX.search(s)
    if not m:
        print('ERRO: não encontrei <script ... id="G"> no index.html')
        return 1
    try:
        G = parse_G(m.group(2))
    except ValueError as e:
        pos = m.start(2) + getattr(e, 'pos', 0)
        ln, col = _where(s, pos)
        print(f'ERRO: o JSON do G não lê: {getattr(e, "msg", e)} — linha {ln}, coluna {col} do index.html')
        k = pos - 1
        while k > m.start(2) and s[k] in ' \t\n':
            k -= 1
        if str(getattr(e, 'msg', '')).startswith("Expecting ',' delimiter") and _where(s, k)[0] < ln:
            print(f'  Provavelmente falta uma vírgula no fim da linha {_where(s, k)[0]}.')
        txt = s[s.rfind('\n', 0, pos) + 1:s.find('\n', pos) if s.find('\n', pos) >= 0 else len(s)]
        print('  ' + (txt if len(txt) <= 240 else txt[:240] + '…'))
        return 1
    want = dump_G(G)
    have = m.group(2)
    if have != want:
        i = next((k for k in range(min(len(have), len(want))) if have[k] != want[k]), min(len(have), len(want)))
        ln, col = _where(s, m.start(2) + i)
        print(f'ERRO: o G lê bem mas não está no formato canónico (a primeira diferença é na linha {ln}, coluna {col}).')
        print('  Corre: python -I _dev/gjson.py --format')
        return 1
    lines = want.split('\n')
    print(f'G ok: {len(lines) - 2} linhas, a mais longa com {max(len(x) for x in lines)} caracteres')
    return 0


def main(argv):
    try:  # na consola o Python já escreve Unicode; num pipe (Git Bash, editores) usa UTF-8
        sys.stdout.reconfigure(errors='replace') if sys.stdout.isatty() else sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    args = [a for a in argv if not a.startswith('--')]
    root = args[0] if args else default_root()
    if '--check' in argv:
        return check(root)
    if '--format' in argv:
        s, G, span = load_G(root)
        out, _ = save_G(root, s, G, span)
        print('já estava no formato canónico' if out == s else 'G reescrito no formato canónico', '|', os.path.join(root, 'index.html'))
        return 0
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
