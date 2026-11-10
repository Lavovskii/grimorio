"""Sessões reais importadas (_dev/sessoes/*.json|*.csv) para a calibração: validação e agregado no formato do G.ha.

Uso: python3 -I _dev/import_sessoes.py [raiz]
  Lê todos os ficheiros de _dev/sessoes/, diz quantas sessões passam e porque saem as outras, e mostra o agregado.
  Sai com 1 se alguma linha trouxer um campo de nome (name/char/personagem/…): esse ficheiro não pode ir para o repositório.
  Formato e recolha: _dev/SESSOES.md. O agregado vai para o data/calib.json pelo _dev/calibrar.py. Teste: python3 -I _dev/calib_test.py
"""
import csv
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gjson import load_G  # noqa: E402

CAMPOS = ('pid', 'voc', 'lvl', 'xph', 'loh', 'min', 'data', 'src')
NOMES = {'name', 'nome', 'char', 'character', 'personagem', 'player', 'jogador', 'world', 'mundo'}
VOCS = ('knight', 'paladin', 'sorcerer', 'druid', 'monk')
SRCS = ('huntanalyser', 'tibiaroute', 'manual')
MAX_KH = 4000   # a regra do G.ha: mais de 4000 mortes/h não é solo nem desta zona


def avg_mon(G, pid):
    """[XP, vida] média de uma morte na zona = avgMon(pid) do index.html (o calibrar.py confere-o contra o JS)."""
    p = G['places'].get(pid)
    if p is None:
        return None
    ms = list(dict.fromkeys(str(x).strip().lower() for x in p.get('mons') or []))
    ok = lambda k: k in G['mon'] and not G['mon'][k][7]
    h = [(k, n) for k, n in (G['pm'].get(pid) or {}).get('h') or [] if k in ms and ok(k)] or [(k, 1) for k in ms if ok(k)]
    t = v = w = 0
    for k, n in h:
        q = max(int(n or 0), 1)
        t += (G['mon'][k][2] or 0) * q
        v += (G['mon'][k][1] or 0) * q
        w += q
    return [t / w, v / w] if w and t > 0 else None


def _num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and x == x and abs(x) != float('inf')


def valida(s, G):
    """None se a sessão serve; senão o motivo (sem repetir valores de texto da linha)."""
    extra = set(s) - set(CAMPOS)
    if extra & NOMES:
        return 'tem um campo de nome (' + ', '.join(sorted(extra & NOMES)) + '): nunca nomes de personagens nem de mundos'
    if extra:
        return 'campos a mais: ' + ', '.join(sorted(extra))
    if s.get('pid') not in G['places']:
        return 'pid desconhecido'
    if s.get('voc') not in VOCS:
        return 'vocação desconhecida'
    if s.get('src') not in SRCS:
        return 'src tem de ser ' + ' | '.join(SRCS)
    for k in ('lvl', 'xph', 'min'):
        if not _num(s.get(k)) or s[k] <= 0:
            return k + ' em falta ou inválido'
    if s.get('loh') is not None and not _num(s['loh']):
        return 'loh inválido'
    if s['min'] < 15:
        return 'sessão com menos de 15 minutos'
    a = avg_mon(G, s['pid'])
    if a and s['xph'] / a[0] > MAX_KH:
        return f"{s['xph'] / a[0]:.0f} mortes/h (mais de {MAX_KH}: não é solo nem desta zona)"
    return None


def agrega(rows):
    """{pid: {v: {voc: [sessões, nível mínimo, nível mediano, XP/h, lucro/h]}}}: medianas, como o G.ha (lucro null sem nenhum)."""
    by = {}
    for s in rows:
        by.setdefault(s['pid'], {}).setdefault(s['voc'], []).append(s)
    out = {}
    for pid in sorted(by):
        for voc, ss in sorted(by[pid].items()):
            lo = [s['loh'] for s in ss if s.get('loh') is not None]
            out.setdefault(pid, {'v': {}})['v'][voc] = [
                len(ss), min(s['lvl'] for s in ss), round(statistics.median(s['lvl'] for s in ss)),
                round(statistics.median(s['xph'] for s in ss)), round(statistics.median(lo)) if lo else None]
    return out


def _csvval(k, x):
    x = x.strip()
    if k in ('pid', 'voc', 'data', 'src'):
        return x
    if x == '':
        return None
    f = float(x)
    return int(f) if f.is_integer() else f


def le(path):
    """Linhas de um ficheiro de sessões (.json = lista de objetos; .csv = cabeçalho com as colunas do formato)."""
    path = Path(path)
    if path.suffix.lower() == '.csv':
        with open(path, encoding='utf-8', newline='') as f:
            return [{k: _csvval(k, v or '') for k, v in r.items()} for r in csv.DictReader(f)]
    rows = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(rows, list) or not all(isinstance(r, dict) for r in rows):
        raise ValueError(f'{path.name}: tem de ser uma lista de objetos')
    return rows


def carrega(root, G):
    """(sessões válidas, [(ficheiro, linha, motivo)]) de todos os ficheiros de _dev/sessoes/."""
    ok, erros = [], []
    for p in sorted((Path(root) / '_dev' / 'sessoes').glob('*')):
        if p.suffix.lower() not in ('.json', '.csv'):
            continue
        for i, s in enumerate(le(p), 1):
            e = valida(s, G)
            (erros.append((p.name, i, e)) if e else ok.append(s))
    return ok, erros


def main(argv):
    root = Path(argv[1] if len(argv) > 1 else Path(__file__).resolve().parent.parent)
    _, G, _ = load_G(str(root))
    ok, erros = carrega(root, G)
    for f, i, e in erros:
        print(f'{f}, linha {i}: {e}')
    ag = agrega(ok)
    print(f'{len(ok)} sessões válidas em {len(ag)} hunts; {len(erros)} recusadas')
    return 1 if any('campo de nome' in e for _, _, e in erros) else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
