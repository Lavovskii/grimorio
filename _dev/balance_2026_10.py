"""Aplica ao G os balanceamentos oficiais de outubro de 2026 (notícias do tibia.com de 20/10 e 27/10, lidas pela TibiaData).

- XP das criaturas (G.mon[k][2]) e sensibilidades (G.mon[k][5] = 100 − %% de dano que levam).
- Eficácia dos elementos de cada zona afetada (G.places[pid].eff: média e mínimo de 100 − resistência das criaturas).
- XP/h e lucro/h das linhas de G.hunts e das sessões de G.ha dessas zonas: o XP/h segue a razão do XP médio por criatura
  (mortes repartidas por igual) e o lucro perde a parte do loot que o ouro cortado tirava (loot esperado por morte de cada
  criatura, G.mon[k][6] = [[ix, nome, %%, valor]], × mortes por hora).
- Uma frase em G.places[pid].note com a data e o que mudou (o jogador vê-a em "Notas").
Correr outra vez não muda nada (as notas ficam marcadas e as mudanças já aplicadas são saltadas).
Uso: python -I _dev/balance_2026_10.py [raiz] [--dry]"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.dont_write_bytecode = True
from gjson import load_G, save_G, default_root

ARGS = [a for a in sys.argv[1:] if not a.startswith('--')]
ROOT = ARGS[0] if ARGS else default_root()
DRY = '--dry' in sys.argv

# criatura: (xp antigo, xp novo) | corte de ouro (fração) | sensibilidade {elemento: (antes, depois)} em % de dano
XP = {'true dawnfire asura': (7475, 8100), 'true midnight asura': (7313, 8200),
      'dworc shadowstalker': (8930, 7680), 'orclops bloodbreaker': (10250, 8820), 'gloom maw': (8770, 7550)}
GOLD = {'true dawnfire asura': .14, 'true midnight asura': .10, 'true frost flower asura': .10,
        'bulltaur brute': .10, 'bulltaur alchemist': .10, 'bulltaur forgepriest': .10,
        'oozing corpus': .12, 'mycobiontic beetle': .12, 'bloated man-maggot': .12, 'sopping corpus': .12,
        'darklight emitter': .12, 'darklight construct': .12, 'wandering pillar': .12, 'converter': .12}
SENS = {'oozing corpus': {'energy': (125, 115)}, 'mycobiontic beetle': {'energy': (115, 110)},
        'darklight striker': {'fire': (120, 115)}, 'darklight source': {'fire': (115, 110)}}
NOTE = {
    '20/10': 'Balanceamento de 20/10/2026: {o}. O XP/h e o lucro/h já têm este ajuste estimado.',
    '27/10': 'Balanceamento de 27/10/2026: {o}. O XP/h e o lucro/h já têm este ajuste estimado.',
}
DATE = {k: '20/10' for k in XP}
DATE.update({k: '20/10' for k in ('true frost flower asura', 'bulltaur brute', 'bulltaur alchemist', 'bulltaur forgepriest')})
DATE.update({k: '27/10' for k in GOLD if k not in DATE})
DATE.update({k: '27/10' for k in SENS})
EL_PT = {'energy': 'energia', 'fire': 'fogo'}

s, G, span = load_G(ROOT)
M = G['mon']
log = []


def loot(k):
    return sum(p / 100 * v for _, _, p, v in (M[k][6] if len(M[k]) > 6 and M[k][6] else []))


def avg_xp(mons, xpmap):
    xs = [xpmap(k) for k in mons if k in M]
    return sum(xs) / len(xs) if xs else 0


# 1) criaturas
old_xp = {k: M[k][2] for k in M}
for k, (a, b) in XP.items():
    if k in M and M[k][2] == a:
        M[k][2] = b
        log.append(f'mon {k}: xp {a} -> {b}')
for k, ch in SENS.items():
    if k not in M:
        continue
    for el, (a, b) in ch.items():
        res = M[k][5].get(el, 0)
        if res == 100 - a:
            M[k][5][el] = 100 - b
            log.append(f'mon {k}: {el} {a}% -> {b}%')

# 2) zonas
for pid, p in G['places'].items():
    mons = [m.lower() for m in p.get('mons', []) if isinstance(m, str)]
    hit = [m for m in mons if m in XP or m in GOLD or m in SENS]
    if not hit:
        continue
    note = p.get('note') or ''
    dates = sorted({DATE[m] for m in hit})
    done = all(f'Balanceamento de {d}/2026' in note for d in dates)
    if done:
        continue
    known = [m for m in mons if m in M]
    # eficácia: média e mínimo de 100 − resistência, só nos elementos que mudaram
    els = {el for m in hit if m in SENS for el in SENS[m]}
    eff = p.get('eff')
    for el in els:
        if eff and el in eff:
            vals = [100 - M[m][5].get(el, 0) for m in known]
            eff[el] = round(sum(vals) / len(vals))
            eff['min'][el] = min(vals)
    # XP/h e lucro/h
    ax_old = avg_xp(known, lambda k: old_xp[k])
    ax_new = avg_xp(known, lambda k: M[k][2])
    rx = ax_new / ax_old if ax_old else 1
    lost = sum(loot(m) * GOLD[m] for m in known if m in GOLD) / len(known) if known else 0  # ouro perdido por morte

    def fix(xp, lo, nd=-4):
        kills = xp / ax_old if ax_old else 0
        return round(xp * rx, nd), round(lo - kills * lost, nd)
    for v, rows in G['hunts'].items():
        for r in rows:
            if r['c'] == pid and r.get('xp') and r.get('lo') is not None:
                nx, nl = fix(r['xp'], r['lo'])
                log.append(f'hunt {v} {pid}: xp {r["xp"]:.0f} -> {nx:.0f}, lo {r["lo"]:.0f} -> {nl:.0f}')
                r['xp'], r['lo'] = float(nx), float(nl)
    ha = G['ha'].get(pid)
    if ha:
        for v, row in ha['v'].items():
            nx, nl = fix(row[3], row[4], 0)
            log.append(f'ha {v} {pid}: xp {row[3]} -> {int(nx)}, lo {row[4]} -> {int(nl)}')
            row[3], row[4] = int(nx), int(nl)
    # nota
    for d in dates:
        parts = []
        for m in hit:
            if DATE[m] != d:
                continue
            nm = M[m][0]
            if m in XP:
                a, b = XP[m]
                parts.append(f'{nm} dá {"mais" if b > a else "menos"} XP ({a:,} → {b:,})'.replace(',', ' '))
            if m in GOLD:
                parts.append(f'{nm} dá cerca de {round(GOLD[m] * 100)}% menos ouro')
            if m in SENS:
                for el, (a, b) in SENS[m].items():
                    parts.append(f'{nm} leva menos dano de {EL_PT[el]} ({a}% → {b}%)')
        txt = NOTE[d].format(o='; '.join(parts))
        p['note'] = (p['note'] + ' ' + txt).strip() if p.get('note') else txt
    log.append(f'place {pid}: rx={rx:.3f} lost/kill={lost:.0f} {dates}')

print('\n'.join(log) or 'nada a mudar')
if not DRY and log:
    save_G(ROOT, s, G, span)
