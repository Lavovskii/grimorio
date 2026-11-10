"""Motor de calibração dos números das hunts (parte D do plano das fichas, rondas 3–4 Q10–Q14) → data/calib.json.

Uso: python3 -I _dev/calibrar.py [raiz] [--check]
  Lê o G (load_G), o G.ha, as sessões de _dev/sessoes/ (import_sessoes.py) e o _dev/cache/ks-*.json mais recente
  (tibiadata.py) e grava:
  - data/calib.json = {v: 1, gen (dia das estatísticas do TibiaData), k, kz: {pid: mortes/h}, dz: {pid: -1|0|1},
    ha: {pid: {v: {voc: [sessões, nível mínimo, nível mediano, XP/h, lucro/h]}}} (só as importadas), n: {sessoes, mundos}};
  - _dev/calib_relatorio.md: o k, os kz, o perigo e as hunts em que o huntEst (com o k novo, sem as sessões dessa
    vocação) se afasta mais de 25 % das sessões reais. O huntEst corre no node (_dev/calib_node.mjs), não em Python.
  --check: não grava; sai com 1 se o data/calib.json não for o que geraria (com o ks-<gen>.json do próprio ficheiro).
Regras:
  k   = mínimos quadrados de log(XP/h) contra log(nível) dentro de cada hunt e vocação (TibiaPal atual, G.ha e sessões
        importadas); menos de 10 pares com níveis diferentes → 0,5; limitado a 0,1–1.
  kz  = mediana de XP/h ÷ avgXp(pid) das sessões solo (G.ha e importadas); hunt sem sessões → mediana das 5 hunts com kz
        mais parecidas (nível recomendado, criaturas no mapa do G.pm e vida média, em log e a dividir pelo desvio-padrão).
  dz  = jogadores mortos ÷ criaturas mortas na semana, em todos os mundos, pesado pelo G.pm (criaturas do avgMon);
        10 % mais altos +1, 30 % mais baixos −1; menos de 1000 criaturas mortas na semana → 0.
Teste: python3 -I _dev/calib_test.py
"""
import json
import math
import statistics
import subprocess
import sys
from pathlib import Path

DEV = Path(__file__).resolve().parent
sys.path.insert(0, str(DEV))
from gjson import load_G  # noqa: E402
from import_sessoes import agrega, avg_mon, carrega, hunt_mons  # noqa: E402

K0, KMIN, KMAX, MINPARES = 0.5, 0.1, 1, 10


def fit_k(pts):
    """pts = [(grupo, nível, XP/h)] → (k, pares). Declive de log(XP/h) contra log(nível) com a média de cada grupo tirada."""
    gs = {}
    for g, L, x in pts:
        if L > 0 and x > 0:
            gs.setdefault(g, []).append((math.log(L), math.log(x)))
    sxy = sxx = pares = 0
    for a in gs.values():
        mx = sum(p[0] for p in a) / len(a)
        my = sum(p[1] for p in a) / len(a)
        sxy += sum((p[0] - mx) * (p[1] - my) for p in a)
        sxx += sum((p[0] - mx) ** 2 for p in a)
        pares += sum(1 for i in range(len(a)) for j in range(i) if a[i][0] != a[j][0])
    if pares < MINPARES or sxx <= 0:
        return K0, pares
    return round(min(KMAX, max(KMIN, sxy / sxx)), 2), pares


def kz_direto(ses, avg):
    """ses = [(pid, XP/h)], avg = {pid: XP média por morte} → {pid: mediana das mortes/h}."""
    by = {}
    for pid, x in ses:
        if avg.get(pid):
            by.setdefault(pid, []).append(x / avg[pid])
    return {p: round(statistics.median(v)) for p, v in sorted(by.items())}


def parecidas(feat, kz, n=5):
    """feat = {pid: (nível recomendado, criaturas no mapa, vida média)} → {pid sem kz: (mediana do kz das n mais parecidas, [pids])}."""
    lg = {p: [math.log(max(v, 1)) for v in f] for p, f in feat.items()}
    sd = [statistics.pstdev(c) or 1 for c in zip(*lg.values())] if lg else []
    z = {p: [v / s for v, s in zip(f, sd)] for p, f in lg.items()}
    com = [p for p in sorted(z) if p in kz]
    out = {}
    for p in sorted(z):
        if p in kz or not com:
            continue
        near = sorted(com, key=lambda q: (math.dist(z[p], z[q]), q))[:n]
        out[p] = (round(statistics.median(kz[q] for q in near)), near)
    return out


def dz(G, ks):
    """(dz para todas as hunts, {pid: razão jogadores mortos ÷ criaturas mortas} das hunts com 1000+ mortes na semana)."""
    ratio = {}
    for pid in G['places']:
        cs = [(k, q) for k, q in hunt_mons(G, pid) if k in ks]
        if sum(ks[k][3] for k, _ in cs) < 1000:
            continue
        ratio[pid] = sum(q * ks[k][2] for k, q in cs) / sum(q * ks[k][3] for k, q in cs)
    vs, n = sorted(ratio.values()), len(ratio)
    out = {p: 0 for p in G['places']}
    for p, r in ratio.items():
        if sum(1 for v in vs if v < r) / n >= 0.9:
            out[p] = 1
        elif sum(1 for v in vs if v <= r) / n <= 0.3:   # empates contam juntos: nenhum fica de fora a meio
            out[p] = -1
    return out, ratio


def desvios(linhas):
    """Linhas {pid, nome, voc, n, lmed, real, est, src} em que a estimativa se afasta mais de 25 % do real, da maior para a menor."""
    d = [dict(x, dev=x['est'] / x['real'] - 1) for x in linhas if x.get('est') and x.get('real')]
    return sorted([x for x in d if abs(x['dev']) > 0.25], key=lambda x: (-abs(x['dev']), x['pid'], x['voc']))


def _n(x):
    return f'{round(x):,}'.replace(',', ' ')


def relatorio_md(meta, st, desv):
    k = str(meta['k']).replace('.', ',')
    out = [f"# Calibração dos números das hunts ({meta['gen']})", '',
           f"Gerado por `python3 -I _dev/calibrar.py`. Fontes: {meta['n']['mundos']} mundos do TibiaData (semana), "
           f"{meta['n']['sessoes']} sessões solo reais (G.ha e `_dev/sessoes/`) e as linhas atuais do TibiaPal.", '',
           '## Ajuste ao nível', '',
           f"- k = **{k}** com {meta['pares']} pares de medições da mesma hunt e vocação em níveis diferentes"
           + (f" (menos de {MINPARES}: fica 0,5, a omissão)." if meta['pares'] < MINPARES else '.'), '',
           '## Mortes por hora', '',
           f"- {st['kz_dir']} hunts com mortes/h das sessões reais; {st['kz_par']} herdadas das 5 hunts mais parecidas; "
           f"{st['kz_sem']} sem valor (sem XP média conhecida).", '',
           '## Perigo (jogadores mortos ÷ criaturas mortas)', '',
           f"- +1: {st['dz'][1]} hunts · 0: {st['dz'][0]} · −1: {st['dz'][-1]}.", '']
    if st['mais']:
        out += ['Hunts com +1 (jogadores mortos por 10 000 criaturas mortas):', '']
        out += [f'- {nome}: {r * 1e4:.1f}' for nome, r in st['mais']]
        out += ['']
    out += ['## Estimativa contra sessões reais', '',
            f"{st['linhas']} combinações de hunt e vocação com sessões reais. O `huntEst` conta sem as sessões dessa vocação "
            f"nessa hunt, no nível mediano delas, com o k novo. Mais de 25 % de diferença: {len(desv)}.", '']
    if desv:
        out += ['| Hunt | Vocação | Sessões | Nível | XP/h real | Estimativa | Diferença | Origem |', '|---|---|---|---|---|---|---|---|']
        out += [f"| {x['nome']} (`{x['pid']}`) | {x['voc']} | {x['n']} | {x['lmed']} | {_n(x['real'])} | {_n(x['est'])} | "
                f"{x['dev'] * 100:+.0f} % | {x['src'] or '—'} |" for x in desv]
        out += ['']
    return '\n'.join(out)


def _ks(root, gen=None):
    fs = sorted((root / '_dev' / 'cache').glob(f"ks-{gen or '*'}.json"))
    return json.loads(fs[-1].read_text(encoding='utf-8')) if fs else None


def calcula(root, G, ksd):
    ok, _ = carrega(root, G)
    avg = {p: avg_mon(G, p) for p in G['places']}
    tp = [((r['c'], v), r['l'], r['xp']) for v, rows in G['hunts'].items() for r in rows
          if r.get('c') and r.get('xp') and not (r.get('o') or r.get('f') or r.get('w'))]
    gha = [((p, v), a[2], a[3]) for p, h in sorted(G['ha'].items()) for v, a in sorted(h['v'].items())]
    k, pares = fit_k(tp + gha + [((s['pid'], s['voc']), s['lvl'], s['xph']) for s in ok])
    kzd = kz_direto([(g[0], x) for g, _, x in gha] + [(s['pid'], s['xph']) for s in ok], {p: a[0] for p, a in avg.items() if a})
    lrec = {}
    for rows in G['hunts'].values():
        for r in rows:
            if r.get('c'):
                lrec[r['c']] = min(r['l'], lrec.get(r['c'], r['l']))
    feat = {p: (lrec.get(p, 8), sum(int(q or 0) for _, q in (G['pm'].get(p) or {}).get('h') or []), a[1])
            for p, a in avg.items() if a}
    par = parecidas(feat, kzd)
    dzv, ratio = dz(G, ksd['c'])
    calib = {'v': 1, 'gen': ksd['gen'], 'k': k, 'kz': {**kzd, **{p: v for p, (v, _) in par.items()}}, 'dz': dzv,
             'ha': agrega(ok), 'n': {'sessoes': sum(a[0] for h in G['ha'].values() for a in h['v'].values()) + len(ok),
                                     'mundos': len(ksd['mundos'])}}
    st = {'pares': pares, 'kzd': kzd, 'par': par, 'ratio': ratio, 'avg': avg, 'ok': ok}
    return calib, st


def dump(calib):
    return json.dumps(calib, ensure_ascii=False, sort_keys=True, indent=1) + '\n'


def main(argv):
    args = [a for a in argv[1:] if not a.startswith('--')]
    root = Path(args[0] if args else DEV.parent)
    out = root / 'data' / 'calib.json'
    _, G, _ = load_G(str(root))
    if '--check' in argv:
        try:
            cur = out.read_text(encoding='utf-8')
            gen = json.loads(cur)['gen']
        except (OSError, ValueError, KeyError) as e:
            print(f'data/calib.json em falta ou inválido: {e}')
            return 1
        ksd = _ks(root, gen)
        if not ksd:
            print(f'sem _dev/cache/ks-{gen}.json: corre python3 -I _dev/tibiadata.py e depois python3 -I _dev/calibrar.py')
            return 1
        ok = dump(calcula(root, G, ksd)[0]) == cur
        print('data/calib.json em dia' if ok else 'data/calib.json desatualizado: corre python3 -I _dev/calibrar.py')
        return 0 if ok else 1
    ksd = _ks(root)
    if not ksd:
        print('sem _dev/cache/ks-*.json: corre primeiro python3 -I _dev/tibiadata.py')
        return 1
    calib, st = calcula(root, G, ksd)
    out.write_text(dump(calib), encoding='utf-8', newline='\n')

    # sessões reais por hunt e vocação (as importadas ganham ao G.ha) contra o huntEst sem elas, no node
    real = {(p, v): a for p, h in G['ha'].items() for v, a in h['v'].items()}
    real.update({(p, v): a for p, h in calib['ha'].items() for v, a in h['v'].items()})
    keys = sorted(real)
    res = subprocess.run(['node', str(DEV / 'calib_node.mjs')], cwd=str(root), check=True, capture_output=True, text=True,
                         input=json.dumps({'k': calib['k'], 'q': [{'pid': p, 'voc': v, 'pl': real[(p, v)][2], 'noha': True}
                                                                  for p, v in keys]})).stdout
    nd = json.loads(res)
    if nd['k'] != calib['k']:
        raise SystemExit(f"o calibOf do shared/fichas.js recusou o k {calib['k']}")
    for p, a in st['avg'].items():   # o avg_mon do Python tem de dar o mesmo que o avgMon do index.html
        b = nd['avg'].get(p)
        if (a is None) != (b is None) or (a and any(abs(x - y) > 1e-6 * max(1, abs(y)) for x, y in zip(a, b))):
            raise SystemExit(f'avg_mon({p}) = {a}, mas o avgMon do index.html dá {b}')
    linhas = [{'pid': p, 'nome': G['places'][p]['n'], 'voc': v, 'n': real[(p, v)][0], 'lmed': real[(p, v)][2],
               'real': real[(p, v)][3], 'est': (r or {}).get('xp'), 'src': (r or {}).get('src')}
              for (p, v), r in zip(keys, nd['r'])]
    dzv = calib['dz']
    mais = sorted(((G['places'][p]['n'], st['ratio'][p]) for p in dzv if dzv[p] == 1), key=lambda x: (-x[1], x[0]))
    md = relatorio_md({**calib, 'pares': st['pares']},
                      {'kz_dir': len(st['kzd']), 'kz_par': len(st['par']), 'kz_sem': len(G['places']) - len(calib['kz']),
                       'dz': {i: sum(1 for x in dzv.values() if x == i) for i in (1, 0, -1)}, 'mais': mais, 'linhas': len(linhas)},
                      desvios(linhas))
    (root / '_dev' / 'calib_relatorio.md').write_text(md, encoding='utf-8', newline='\n')
    print(md)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
