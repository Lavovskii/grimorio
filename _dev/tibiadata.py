"""Estatísticas de mortes de todos os mundos (TibiaData /v4/killstatistics), para a calibração (parte D do plano das fichas).

Uso: python3 -I _dev/tibiadata.py [raiz]
  Pede /v4/worlds e depois /v4/killstatistics/<mundo> de cada mundo normal (1 pedido por segundo, 3 tentativas com espera)
  e grava a soma em _dev/cache/ks-AAAA-MM-DD.json (pasta no .gitignore; a data é a de hoje, em UTC):
  {gen, mundos: [nomes], falhas: [nomes], c: {criatura: [jogadores mortos ontem, criaturas mortas ontem,
  jogadores mortos na semana, criaturas mortas na semana]}}.
  A criatura fica com a chave do data/creatures.json (o TibiaData dá o plural: 'dragon lords' → 'dragon lord');
  as linhas entre parênteses ('(elemental forces)') saem. Teste: python3 -I _dev/calib_test.py
"""
import datetime
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

API = 'https://api.tibiadata.com/v4'
NUMS = ('last_day_players_killed', 'last_day_killed', 'last_week_players_killed', 'last_week_killed')


def _pl(w):
    """Plurais possíveis de uma palavra inglesa (os do Tibia: cyclopes, fungi, medusae, sabreteeth, henchmen)."""
    if re.search(r'[^aeiou]y$', w):
        return [w[:-1] + 'ies']
    if w.endswith('tooth'):
        return [w[:-5] + 'teeth']
    if w.endswith('man'):
        return [w[:-3] + 'men', w + 's']
    if w.endswith('fe'):
        return [w[:-2] + 'ves']
    if w.endswith('f'):
        return [w[:-1] + 'ves', w + 's']
    if w.endswith('us'):
        return [w[:-2] + 'i', w + 'es']
    if w.endswith('ps'):
        return [w[:-1] + 'es', w + 'es']
    if re.search(r'(s|x|ch|sh)$', w):
        return [w + 'es']
    if w.endswith('o'):
        return [w + 'es', w + 's']
    if w.endswith('a'):
        return [w + 'e', w + 's']
    return [w + 's']


def plurais(k):
    """'son of verminor' → 'sons of verminor'; 'cyclops drone' → também 'cyclopes drone' (o TibiaData faz assim)."""
    if ' of ' in k:
        a, b = k.split(' of ', 1)
        return [p + ' of ' + b for p in _pl(a)]
    ws = k.split(' ')
    out = [' '.join(ws[:-1] + [p]) for p in _pl(ws[-1])]
    if len(ws) > 1:
        out += [' '.join([p] + ws[1:]) for p in _pl(ws[0])]
    return out


def agrega(respostas, chaves=()):
    """Soma as respostas do /killstatistics por criatura: {chave: [4 números de NUMS]}. chaves = nomes do creatures.json."""
    chaves = set(chaves)
    pl = {}
    for k in sorted(chaves):
        for p in plurais(k):
            pl.setdefault(p, k)
    out = {}
    for r in respostas:
        for e in r['killstatistics']['entries']:
            n = str(e['race']).strip().lower()
            if n.startswith('('):
                continue
            k = n if n in chaves else pl.get(n, n)
            t = out.setdefault(k, [0, 0, 0, 0])
            for i, f in enumerate(NUMS):
                t[i] += int(e.get(f) or 0)
    return out


def get(url, tentativas=3):
    """GET JSON com 3 tentativas (espera 2, 4 s)."""
    for i in range(tentativas):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'grimorio-calib/1'})
            with urllib.request.urlopen(req, timeout=30) as f:
                return json.loads(f.read().decode('utf-8'))
        except Exception as e:  # rede, HTTP ou JSON: tenta outra vez
            if i == tentativas - 1:
                raise
            print(f'  {url}: {e}; nova tentativa', file=sys.stderr)
            time.sleep(2 ** (i + 1))


def main(argv):
    root = Path(argv[1] if len(argv) > 1 else Path(__file__).resolve().parent.parent)
    chaves = json.loads((root / 'data' / 'creatures.json').read_text(encoding='utf-8')).keys()
    t0 = time.time()
    mundos = sorted(w['name'] for w in get(API + '/worlds')['worlds']['regular_worlds'])
    resp, ok, falhas = [], [], []
    for w in mundos:
        time.sleep(1)
        try:
            r = get(f'{API}/killstatistics/{urllib.request.quote(w)}')
            if not r.get('killstatistics', {}).get('entries'):
                raise ValueError('sem entradas')
            resp.append(r)
            ok.append(w)
        except Exception as e:
            print(f'{w}: falhou ({e})', file=sys.stderr)
            falhas.append(w)
    if not ok:
        print('nenhum mundo respondeu; nada gravado', file=sys.stderr)
        return 1
    hoje = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d')
    c = agrega(resp, chaves)
    out = root / '_dev' / 'cache' / f'ks-{hoje}.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({'gen': hoje, 'mundos': ok, 'falhas': falhas, 'c': c}, ensure_ascii=False, sort_keys=True) + '\n',
                   encoding='utf-8')
    print(f'{len(ok)} mundos ({len(falhas)} falharam), {len(c)} criaturas, {time.time() - t0:.0f} s → {out}')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
