"""Wheel calculada: a melhor distribuição de pontos para cada total (0–4000), por vocação e foco.

Ideia: um modelo de valor linear (o que vale cada parte da roda) + um otimizador (procura em feixe por custo) que acha a
melhor roda para um total de pontos. Os pesos do modelo aprendem-se com as builds do TibiaPal (G.wheel): perceptrão
estruturado — se, com os mesmos pontos, o otimizador não dá a build do TibiaPal, sobe-se o peso do que ela tem e
desce-se o do que o otimizador escolheu. Assim, nos totais do TibiaPal dá (quase) as mesmas builds, e entre eles e
depois dos 1175 pontos (onde a lista acaba) continua com o mesmo critério.

Saída: data/wheelopt.json
  {v, src, step: 25, voc: {<vocação>: [{k, n, a: "<161 linhas de 36 caracteres>", ok, j}]}}
  a: para cada total 0, 25, 50 … 4000, os pontos das 36 fatias (ordem do código do jogo) em base 36, em passos de 5
     (um carácter por fatia: 0–40 → 0–200 pontos). ok/j: quantas builds do TibiaPal o otimizador reproduz e a
     semelhança média (Jaccard das fatias cheias) — para se ver se o modelo aprendeu bem.

Uso: python -I -X utf8 _dev/build_wheel_opt.py
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOM = ['green', 'red', 'blue', 'purple']
STEP = 25
MAXP = 4000
K = 40          # estados guardados por custo na procura em feixe
EPOCHS = 160
LR = 0.6

W = json.load(open(os.path.join(ROOT, 'data', 'wheel.json'), encoding='utf-8'))
html = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
g0 = html.index('<script type="application/json" id="G">')
g1 = html.index('</script>', g0)
G = json.loads(html[g0 + len('<script type="application/json" id="G">'):g1])

SL = W['slots']                      # [domínio, máximo, dedicação, convicção]
ADJ = W['adj']
N = len(SL)
THR = W['stage']                     # [250, 500, 1000]
DI = [DOM.index(s[0]) for s in SL]
MX = [s[1] for s in SL]
SPK = ['A', 'B', 'C', 'D', 'E']

# ---------- características (o que o modelo pesa) ----------
FEAT = (['ded_hp', 'ded_mp', 'ded_cap', 'ded_mit', 'vr1', 'vr2', 'vr3', 'skill', 'mleech', 'lleech', 'instG', 'instP']
        + ['sp1_' + x for x in SPK] + ['sp2_' + x for x in SPK]
        + ['rev_%d_%d' % (d, s) for d in range(4) for s in range(3)]
        + ['slot_%d' % i for i in range(36)])   # preferência dos peritos por cada fatia (caminhos que valem o mesmo)
FI = {f: i for i, f in enumerate(FEAT)}
NF = len(FEAT)

# pesos de partida (o que vale cada coisa antes de aprender): a revelação vale o Damage and Healing que dá (4 → 9 → 20)
# mais o efeito; as convicções valem pelo que fazem; a dedicação vale pouco por ponto
PRIOR = {'ded_hp': 1.5, 'ded_mp': 1.5, 'ded_cap': 0.4, 'ded_mit': 1.5, 'vr1': 6, 'vr2': 5, 'vr3': 8, 'skill': 6,
         'mleech': 3, 'lleech': 3, 'instG': 8, 'instP': 8}
for x in SPK:
    PRIOR['sp1_' + x] = 8
    PRIOR['sp2_' + x] = 5
for i in range(36):
    PRIOR['slot_%d' % i] = 0
for d in range(4):
    PRIOR['rev_%d_0' % d] = 16
    PRIOR['rev_%d_1' % d] = 11
    PRIOR['rev_%d_2' % d] = 22


def ded_feats(i):
    """(característica, peso por 100 pontos) da dedicação da fatia i"""
    d = SL[i][2]
    if d == 'hpmp':
        return [('ded_hp', 0.5), ('ded_mp', 0.5)]
    return [('ded_' + d, 1.0)]


def cv_key(i):
    cv = SL[i][3]
    if cv == 'vr':
        return 'vr'
    if cv.startswith('sp:'):
        return 'sp:' + cv[3:]
    if cv == 'inst:G200':
        return 'instG'
    if cv == 'inst:P200':
        return 'instP'
    return cv                         # skill, mleech, lleech


def phi_of(pts):
    """características de uma roda completa (com fatias parciais)"""
    f = [0.0] * NF
    dom = [0] * 4
    vr = [0] * 4
    sp = {x: 0 for x in SPK}
    for i, p in enumerate(pts):
        if not p:
            continue
        p = min(p, MX[i])
        dom[DI[i]] += p
        for k, w in ded_feats(i):
            f[FI[k]] += w * p / 100
        if p >= MX[i]:
            f[FI['slot_%d' % i]] += 1
            c = cv_key(i)
            if c == 'vr':
                vr[DI[i]] += 1
            elif c.startswith('sp:'):
                sp[c[3:]] += 1
            else:
                f[FI[c]] += 1
    for d in range(4):
        for k in range(min(vr[d], 3)):
            f[FI['vr%d' % (k + 1)]] += 1
        for s in range(3):
            if dom[d] >= THR[s]:
                f[FI['rev_%d_%d' % (d, s)]] += 1
    for x in SPK:
        if sp[x] >= 1:
            f[FI['sp1_' + x]] += 1
        if sp[x] >= 2:
            f[FI['sp2_' + x]] += 1
    return f


def dot(w, f):
    return sum(a * b for a, b in zip(w, f))


# ---------- otimizador ----------
def fillable(mask, i):
    a = ADJ[i]
    return not a or any(mask >> j & 1 for j in a)


def full_value(w, mask):
    pts = [MX[i] if mask >> i & 1 else 0 for i in range(N)]
    return dot(w, phi_of(pts))


def beam(w, maxc):
    """para cada custo (múltiplo de 25) até maxc: os K melhores conjuntos de fatias cheias"""
    nb = maxc // STEP + 1
    B = [dict() for _ in range(nb)]   # máscara → valor
    B[0][0] = 0.0
    for b in range(nb):
        if not B[b]:
            continue
        top = sorted(B[b].items(), key=lambda kv: -kv[1])[:K]
        B[b] = dict(top)
        for mask, _ in top:
            for i in range(N):
                if mask >> i & 1 or not fillable(mask, i):
                    continue
                nbk = b + MX[i] // STEP
                if nbk >= nb:
                    continue
                m2 = mask | (1 << i)
                if m2 in B[nbk]:
                    continue
                B[nbk][m2] = full_value(w, m2)
    return B


def place_left(w, mask, left):
    """reparte os pontos que sobram (menos do que mais uma fatia boa) pelas fatias que já se podem encher:
    primeiro para passar limiares das revelações, o resto na melhor dedicação. Devolve a roda (36 pontos)."""
    pts = [MX[i] if mask >> i & 1 else 0 for i in range(N)]
    if left <= 0:
        return pts
    open_ = [i for i in range(N) if not mask >> i & 1 and fillable(mask, i)]
    dom = [0] * 4
    for i in range(N):
        dom[DI[i]] += pts[i]
    cap = [0] * 4
    for i in open_:
        cap[DI[i]] += MX[i]
    best, bestx = None, None
    opts = []
    for d in range(4):
        o = [0]
        for s in range(3):
            gap = THR[s] - dom[d]
            if 0 < gap <= min(left, cap[d]):
                o.append(gap)
        opts.append(o)

    def rec(d, used, xs):
        nonlocal best, bestx
        if d == 4:
            val = 0.0
            for dd in range(4):
                for s in range(3):
                    if dom[dd] < THR[s] <= dom[dd] + xs[dd]:
                        val += w[FI['rev_%d_%d' % (dd, s)]]
            if best is None or val > best:
                best, bestx = val, list(xs)
            return
        for x in opts[d]:
            if used + x <= left:
                rec(d + 1, used + x, xs + [x])
    rec(0, 0, [])
    rest = left - sum(bestx)
    # pontos nos domínios escolhidos (fatias por ordem de melhor dedicação)
    def dedw(i):
        return sum(w[FI[k]] * c for k, c in ded_feats(i)) / 100
    for d in range(4):
        x = bestx[d]
        for i in sorted([i for i in open_ if DI[i] == d], key=lambda i: -dedw(i)):
            if x <= 0:
                break
            put = min(x, MX[i] - pts[i] - 1) if x < MX[i] - pts[i] else min(x, MX[i] - pts[i])
            pts[i] += put
            x -= put
        rest += x
    for i in sorted(open_, key=lambda i: -dedw(i)):
        if rest <= 0:
            break
        room = MX[i] - 1 - pts[i]
        if room <= 0:
            continue
        put = min(rest, room)
        pts[i] += put
        rest -= put
    return pts


def best_for(w, B, budget):
    """a melhor roda para um total de pontos, com o que sobra já repartido"""
    hi = min(budget // STEP, len(B) - 1)
    lo = max(0, hi - 10)
    best, bp = None, None
    for b in range(lo, hi + 1):
        for mask in B[b]:
            pts = place_left(w, mask, budget - b * STEP)
            v = dot(w, phi_of(pts))
            if best is None or v > best:
                best, bp = v, pts
    return bp


# ---------- famílias (focos) e aprendizagem ----------
FAMS = {
    'sorcerer': [('energy', 'energia', r'energy'), ('fire', 'fogo', r'fire')],
    'paladin': [('holy', 'holy', r'holy'), ('physical', 'física', r'physical')],
}


def anchors(voc, rx):
    out = []
    for wb in G['wheel'].get(voc, []):
        pts = W['b'].get(wb['c'])
        if not pts:
            continue
        note = (wb.get('note') or '').lower()
        if rx and note and not re.search(rx, note):
            continue
        out.append((wb['p'], [min(p, MX[i]) for i, p in enumerate(pts)], wb['t']))
    return out


def jacc(a, b):
    fa = {i for i in range(N) if a[i] >= MX[i]}
    fb = {i for i in range(N) if b[i] >= MX[i]}
    return 1.0 if not fa and not fb else len(fa & fb) / len(fa | fb)


def train(an):
    w = [PRIOR[f] for f in FEAT]
    avg = [0.0] * NF
    maxc = max(p for p, _, _ in an) + 200
    phis = [phi_of(pts) for _, pts, _ in an]
    for ep in range(EPOCHS):
        B = beam(w, maxc)
        grad = [0.0] * NF
        for (p, pts, _), fa in zip(an, phis):
            pred = best_for(w, B, p)
            fp = phi_of(pred)
            if dot(w, fp) >= dot(w, fa) + 1e-9 and pred != pts:
                for k in range(NF):
                    grad[k] += fa[k] - fp[k]
        for k in range(NF):
            w[k] += LR * grad[k] / len(an)
            avg[k] += w[k]
    return [a / EPOCHS for a in avg]


B36 = '0123456789abcdefghijklmnopqrstuvwxyzABCDE'   # 0–40 (0–200 pontos em passos de 5)


def enc36(pts):
    return ''.join(B36[min(40, int(round(p / 5)))] for p in pts)


def main():
    out = {'v': 1, 'src': 'calculada a partir das builds do TibiaPal (_dev/build_wheel_opt.py)', 'step': STEP, 'voc': {}}
    for voc in G['wheel']:
        fams = FAMS.get(voc, [('all', '', None)])
        out['voc'][voc] = []
        for k, n, rx in fams:
            an = anchors(voc, rx)
            w = train(an)
            B = beam(w, MAXP)
            rows = []
            for b in range(0, MAXP + 1, STEP):
                rows.append(enc36(best_for(w, B, b)))
            ok, js = 0, []
            for p, pts, t in an:
                pred = best_for(w, B, p)
                j = jacc(pred, pts)
                js.append(j)
                ok += j >= 0.999
            jm = sum(js) / len(js)
            print('%-9s %-9s builds %2d  iguais %2d  semelhança %.2f' % (voc, k, len(an), ok, jm))
            out['voc'][voc].append({'k': k, 'n': n, 'a': ''.join(rows), 'ok': ok, 'nb': len(an), 'j': round(jm, 3),
                                    'w': {f: round(x, 2) for f, x in zip(FEAT, w)}})
    with open(os.path.join(ROOT, 'data', 'wheelopt.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, separators=(',', ':'))
    print('data/wheelopt.json')


if __name__ == '__main__':
    sys.setrecursionlimit(10000)
    main()
