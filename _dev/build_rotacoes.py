"""Dados do motor de rotações (shared/rotacoes.js) → data/rotacoes.json.

Junta o que o site já tem em data/spells.json (base power, mana, cooldowns, nível, elemento, área de cada feitiço) com as
mecânicas que lá não estão e que o motor precisa para escolher rotações: saltos dos feitiços em cadeia, DoTs, builders e
spenders do monk, feitiços só corpo a corpo ou só com escudo, estágios da Wheel, base power das runas, poções e imbuements.
Cada valor que não vem do spells.json tem a fonte ao lado (TibiaWiki e notas oficiais das Vocation Adjustments 2026:
16/06/2026, patch 15.25.3a4a52, e 07/07/2026, patch 15.25.bd5a04).

Também pré-calcula a geometria: quantos alvos apanha, em média, cada feitiço/runa em cada cenário (posições de monstros
sorteadas com semente fixa e a melhor pontaria possível), para o motor em JS não ter de o fazer no browser.

Uso: python -I -X utf8 _dev/build_rotacoes.py [raiz] [--check]
  --check: não escreve; compara com o data/rotacoes.json que existe e sai com 1 se for diferente.
Corre outra vez quando mudares data/spells.json ou as tabelas abaixo. Não vai à rede."""
import json
import os
import random
import sys

ROOT = os.path.abspath(next((a for a in sys.argv[1:] if not a.startswith('--')),
                            os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')))
SPELLS = json.load(open(os.path.join(ROOT, 'data', 'spells.json'), encoding='utf-8'))
ITEMS = json.load(open(os.path.join(ROOT, 'data', 'items.json'), encoding='utf-8'))
OUT = os.path.join(ROOT, 'data', 'rotacoes.json')
VOCS = ['knight', 'paladin', 'sorcerer', 'druid', 'monk']

# ---------- correções ao spells.json ----------
FIX = {
    # notas oficiais 16/06/2026: "Mystic Repulse: base power 72 → 85, cooldown 20 → 12" (o spells.json tem cd 8)
    'Mystic Repulse': {'bp': 85, 'cd': 12},
    # a TibiaWiki não publica o base power; 40 é o dos dados de feitiços do cliente 15.25 usados pelo Crystal Server
    # (zimbadev/crystalserver, data/scripts/spells/attack/ethereal_barrage.lua), cujos outros valores batem com a TibiaWiki
    'Ethereal Barrage': {'bp': 40, 'est': 1},
}

# ---------- mecânicas que o spells.json não tem ----------
# chain [saltos, distância do salto]: TibiaWiki (Forked Glacier/Thorns: até 6/5, 4 casas; Lightning: 2; Chained Penance:
# 4, salto 2 + 1 desde 16/06/2026; Spiritual Outburst: 7; Executioner's Throw: 2/3/4 por estágio da Wheel)
CHAIN = {'Forked Glacier': [6, 4], 'Forked Thorns': [5, 4], 'Lightning': [2, 3], 'Chained Penance': [4, 3],
         'Spiritual Outburst': [7, 3], "Executioner's Throw": [2, 3]}
# DoTs (não acumulam e o dano espalha-se por minutos; TibiaWiki: Electrify 25 de dano a cada 10–12 s, Holy Flash 20 a cada
# 10–12 s, Soulfire 10 a cada 9 s): abrem a luta contra um boss, não entram na rotação.
DOT = {'Envenom', 'Curse', 'Ignite', 'Electrify', 'Holy Flash', 'Inflict Wound', 'Soulfire'}
# Harmony do monk (TibiaWiki: Builder Spells / Spender Spells; o Forceful Uppercut gera Harmony segundo o site)
BUILDER = {'Swift Jab', 'Double Jab', 'Mystic Repulse', 'Flurry of Blows', 'Chained Penance', 'Greater Flurry of Blows',
           'Thousand Fist Blows', 'Forceful Uppercut'}
SPENDER = {'Tiger Clash', 'Greater Tiger Clash', 'Sweeping Takedown', 'Devastating Knockout', 'Spiritual Outburst'}
# só a uma casa (TibiaWiki: "adjacent enemy" / "in melee")
MELEE = {'Swift Jab', 'Double Jab', 'Tiger Clash', 'Greater Tiger Clash', 'Devastating Knockout', 'Forceful Uppercut',
         'Brutal Strike', 'Annihilation', 'Shield Bash', 'Inflict Wound'}
SHIELD = {'Shield Bash', 'Shield Slam'}            # só com escudo; dano pela defesa do escudo
QUEST = {'Mystic Repulse': 'Shrine of Respect (The Way of the Monk Quest)',
         'Forceful Uppercut': 'Shrine of Knowledge (The Way of the Monk Quest)'}
MULT = {'Death Echo': 1.5}                          # eco de 50% 1 s depois (TibiaWiki)
CURSOR = {'Death Echo'}                             # área 5×5 no cursor: pode cair em qualquer casa, como uma runa
# Wheel (TibiaWiki, Revelation Perks; 2026): por estágio 1/2/3
WHEEL = {
    'Ice Burst': {'cd': [22, 18, 14], 'twin': [0.2, 0.4, 0.6]},
    'Terra Burst': {'cd': [22, 18, 14], 'twin': [0.2, 0.4, 0.6]},
    "Executioner's Throw": {'cd': [18, 14, 10], 'chain': [2, 3, 4]},
    'Divine Grenade': {'cd': [26, 20, 14], 'bpx': [1.0, 1.16, 1.32]},
    'Spiritual Outburst': {'cd': [24, 20, 16], 'echo': [0.375, 0.5, 0.625]},
}
# Divine Grenade: 'Scene 2sqmballtarget' na TibiaWiki = bola de raio 2 no alvo (o spells.json só tem o alvo)
SHAPE_FIX = {'Divine Grenade': ('tarea', [(x, y, 1.0) for x in range(-2, 3) for y in range(-2, 3) if abs(x) + abs(y) <= 3])}

# ---------- runas (TibiaWiki, Infobox Object das runas; base power desde 16/06/2026) ----------
RUNE_BP = {'Sudden Death': 150, 'Icicle': 60, 'Fireball': 60, 'Holy Missile': 70, 'Heavy Magic Missile': 30,
           'Stalagmite': 30, 'Light Magic Missile': 15, 'Soulfire': 120, 'Great Fireball': 50, 'Avalanche': 50,
           'Thunderstorm': 50, 'Stone Shower': 50, 'Explosion': 60}

# ---------- poções de mana (TibiaWiki, Money Spent per Mana Point; GMP para todas as vocações desde 16/06/2026) ----------
# [chave items.json, nome, nível, mana média, preço NPC, vocações]
POTS = [['mana potion', 'Mana Potion', 1, 100, 56, 'kpsdm'],
        ['strong mana potion', 'Strong Mana Potion', 50, 150, 108, 'kpsdm'],
        ['great mana potion', 'Great Mana Potion', 80, 200, 158, 'kpsdm'],
        ['great spirit potion', 'Great Spirit Potion', 80, 150, 254, 'pm'],
        ['superior mana potion', 'Superior Mana Potion', 100, 300, 254, 'psdm'],
        ['ultimate spirit potion', 'Ultimate Spirit Potion', 130, 200, 488, 'pm'],
        ['ultimate mana potion', 'Ultimate Mana Potion', 130, 500, 488, 'sd']]
# parte das poções que pode ir para mana (o exhaust de 1 s é o mesmo das de vida; os magos curam-se com feitiços)
POT_SHARE = {'knight': 0.6, 'paladin': 0.7, 'monk': 0.7, 'sorcerer': 1.0, 'druid': 1.0}

# ---------- imbuements (TibiaWiki, Imbuing: 20 h de combate; taxa 7 500 / 60 000 / 250 000 gp) ----------
IMB_FEE = [7500, 60000, 250000]
IMBS = {
    'void': {'n': 'Void', 'fx': 'mana leech', 'v': [3, 5, 8],
             'slots': 'capacete, armas (espadas, maças, machados, arcos, bestas, wands, rods, fist)',
             'src': [['rope belt', 25], ['silencer claws', 25], ['some grimeleech wings', 5]]},
    'vampirism': {'n': 'Vampirism', 'fx': 'life leech', 'v': [5, 10, 25],
                  'slots': 'armas e armaduras', 'src': [['vampire teeth', 25], ['bloody pincers', 15], ['piece of dead brain', 5]]},
    'strike': {'n': 'Strike', 'fx': 'crítico', 'v': [5, 15, 40], 'chance': 5,
               'slots': 'espadas, maças, machados, arcos, bestas (e algumas wands/rods)',
               'src': [['protective charm', 20], ['sabretooth', 25], ['vexclaw talon', 5]]},
    'epiphany': {'n': 'Epiphany', 'fx': 'magic level', 'v': [1, 2, 4], 'slots': 'wands, rods e capacetes de mago',
                 'src': [['elvish talisman', 25], ['broken shamanic staff', 15], ['strand of medusa hair', 15]]},
    'precision': {'n': 'Precision', 'fx': 'distance', 'v': [1, 2, 4], 'slots': 'capacetes, arcos e bestas',
                  'src': [['elven scouting glass', 25], ['elven hoof', 20], ['metal spike', 10]]},
    'punch': {'n': 'Punch', 'fx': 'fist', 'v': [1, 2, 4], 'slots': 'capacetes e armas de monk',
              'src': [['tarantula egg', 25], ['mantassin tail', 20], ['gold-brocaded cloth', 15]]},
    'chop': {'n': 'Chop/Slash/Bash', 'fx': 'skill da arma', 'v': [1, 2, 4], 'slots': 'capacete e arma (o do teu tipo de arma)',
             'src': [['orc tooth', 20], ['battle stone', 25], ['moohtant horn', 20]]},
}

# ---------- cenários (posições dos monstros; (0,0) = tu) ----------
def ring(dmin, dmax, c=(0, 0)):
    return [(x + c[0], y + c[1]) for x in range(-dmax, dmax + 1) for y in range(-dmax, dmax + 1)
            if dmin <= max(abs(x), abs(y)) <= dmax and (x + c[0], y + c[1]) != (0, 0)]

SCEN = {
    # boss à distância, com kiting a 2–3 casas e alinhado contigo (mesma linha ou coluna, para beams e waves)
    'boss_r': lambda r: [r.choice([(d * sx, 0) for d in (2, 3) for sx in (1, -1)] + [(0, d * sy) for d in (2, 3) for sy in (1, -1)])],
    'boss_m': lambda r: [r.choice(ring(1, 1))],                 # boss colado (knight, monk)
    'caixa': lambda r: ring(1, 1),                               # 8 colados (box)
    'espalhados': lambda r: r.sample(ring(1, 3), 6),             # lure: 6 a 1–3 casas
    'party': lambda r: r.sample(ring(1, 2, (3, 0)), 10),         # bolo à volta do blocker, 3 casas à frente
    'party_m': lambda r: r.sample(ring(1, 2), 10),               # em party, colado ao bolo (knight/monk)
}
N_SAMPLES = 800

def cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))

def shape(name, entry):
    if name in SHAPE_FIX: return SHAPE_FIX[name]
    if name in CHAIN: return 'chain', None
    a = entry.get('ar')
    if not a: return 'single', None
    w, s = a[0], a[1]
    cells = [(i % w, i // w, c) for i, c in enumerate(s)]
    wt = {'1': 1.0, '3': 1.0, '4': 0.75}                    # '4' = segunda área a 75% (Sweeping Takedown)
    if any(c == '3' for _, _, c in cells):
        ax, ay = next((x, y) for x, y, c in cells if c == '3')
        off = [(x - ax, y - ay, wt[c]) for x, y, c in cells if c in wt]
        return ('single', None) if len(off) == 1 else ('tarea', off)
    ax, ay = next((x, y) for x, y, c in cells if c == '2')
    off = [(x - ax, y - ay, wt[c]) for x, y, c in cells if c in wt]
    cx = sum(o[0] for o in off) / len(off); cy = sum(o[1] for o in off) / len(off)
    return ('self' if abs(cx) < .01 and abs(cy) < .01 else 'wave'), off

def rot(off, k):
    for _ in range(k): off = [(-y, x, w) for x, y, w in off]
    return off

def hits(kind, off, chain, melee, rune, mons):
    S = set(mons)
    if melee and not any(cheb(m, (0, 0)) == 1 for m in mons): return 0.0
    if kind == 'single': return 1.0
    if kind == 'self': return sum(w for x, y, w in off if (x, y) in S)
    if kind == 'wave': return max(sum(w for x, y, w in rot(off, r) if (x, y) in S) for r in range(4))
    if kind == 'tarea':
        # runas: qualquer casa até 7; feitiços com alvo: centrados num monstro
        cands = [(cx, cy) for cx in range(-7, 8) for cy in range(-7, 8)] if rune else mons
        return max(sum(w for x, y, w in off if (c[0] + x, c[1] + y) in S) for c in cands)
    if kind == 'chain':
        n, d = chain
        return max(1 + min(n, sum(1 for m in mons if m != t and cheb(m, t) <= d)) for t in mons)
    raise ValueError(kind)

def geo(kind, off, chain, melee, rune):
    out = {}
    for k, f in SCEN.items():
        r = random.Random(7)
        tot = sum(hits(kind, off, chain, melee, rune, f(r)) for _ in range(N_SAMPLES))
        out[k] = round(tot / N_SAMPLES, 2)
    return out

def fam(voc, n):
    if voc in ('sorcerer', 'druid'): return 'magic'
    if voc == 'knight': return 'shield' if n in SHIELD else 'melee'
    if voc == 'paladin': return 'dist' if 'Ethereal' in n else 'magic'
    return 'fist'

def build():
    ab = {}
    for e in SPELLS.values():
        n = e['n']
        if e.get('t') == 'r' or e.get('g') != 'attack': continue
        bp = FIX.get(n, {}).get('bp', e.get('bp'))
        if not bp: continue
        kind, off = shape(n, e)
        wh = WHEEL.get(n, {})
        chain = CHAIN.get(n)
        rec = {'n': n, 'w': e['w'], 'v': e['v'], 'l': e.get('l', 0), 'el': e.get('el') or 'physical', 'bp': bp,
               'm': e.get('m') or 0, 'cd': FIX.get(n, {}).get('cd', e['cd']), 'gcd': e.get('gcd') or 2,
               'g2': e.get('g2'), 'cd2': e.get('gcd2') or (wh.get('cd') or [0])[0] if e.get('g2') else 0,
               'k': kind}
        if chain: rec['ch'] = chain
        if n in MULT: rec['x'] = MULT[n]
        if n in DOT: rec['dot'] = 1
        if n in BUILDER: rec['role'] = 'B'
        if n in SPENDER: rec['role'] = 'S'
        if n in MELEE: rec['mel'] = 1
        if n in SHIELD: rec['shd'] = 1
        if n in QUEST: rec['q'] = QUEST[n]
        if wh: rec['wh'] = wh
        if FIX.get(n, {}).get('est'): rec['est'] = 1
        if e.get('o') == 'wheel': rec['wheel'] = 1
        rec['fam'] = {v: fam(v, n) for v in e['v']}
        rec['h'] = geo(kind, off, chain, n in MELEE, n in CURSOR)
        if chain and wh.get('chain'):   # Executioner's Throw: alvos por estágio
            rec['hst'] = [geo(kind, off, [c, chain[1]], n in MELEE, False) for c in wh['chain']]
        ab[n] = rec
    runes = {}
    for e in SPELLS.values():
        if e.get('t') != 'r' or e.get('rn') is None: continue
        base = e['n']
        if base not in RUNE_BP: continue
        kind, off = shape(base, e)
        rv = e.get('rv') or VOCS
        runes[e['rn']] = {'n': e['rn'], 'base': base, 'v': rv, 'l': e.get('l', 0), 'ml': e.get('ml', 0),
                          'el': e.get('el') or 'physical', 'bp': RUNE_BP[base], 'gp': e.get('rp') or 0,
                          'k': 'rarea' if kind == 'tarea' else kind, 'dot': 1 if base in DOT else 0,
                          'h': geo(kind, off, None, False, True)}
    def npcval(k):
        it = ITEMS.get(k) or {}
        return it.get('npc') or None
    imbs = {}
    for k, v in IMBS.items():
        d = dict(v)
        d['src'] = [[n, q, npcval(n)] for n, q in v['src']]
        imbs[k] = d
    # ataque automático com munição de área (Shatterstorm, Diamond e as elementais: 13 casas = losango de raio 2 no alvo)
    ammo13 = [(x, y, 1.0) for x in range(-2, 3) for y in range(-2, 3) if abs(x) + abs(y) <= 2]
    auto = {'area13': geo('tarea', ammo13, None, False, False)}
    # ids do cliente (os useObject do clientoptions.json) → nome, para o site ler a barra do jogador sem o items.json
    oid = {}
    for n in list(runes) + [p[1] for p in POTS] + ['Health Potion', 'Strong Health Potion', 'Great Health Potion',
            'Ultimate Health Potion', 'Supreme Health Potion', 'Great Spirit Potion', 'Ultimate Spirit Potion']:
        for i in (ITEMS.get(n.lower()) or {}).get('ids') or []:
            oid[str(i)] = n
    # runas que o items.json não tem (ids do cliente na TibiaWiki)
    for i, n in ((3174, 'Light Magic Missile Rune'), (3198, 'Heavy Magic Missile Rune'), (3179, 'Stalagmite Rune'),
                 (3189, 'Fireball Rune'), (3182, 'Holy Missile Rune')):
        oid.setdefault(str(i), n)
    return {
        'v': 1,
        'fontes': 'data/spells.json do Grimório + TibiaWiki e notas oficiais das Vocation Adjustments 2026 '
                  '(16/06/2026 e 07/07/2026), outubro de 2026',
        'scen': list(SCEN),
        'ab': ab, 'runes': runes, 'auto': auto,
        'pots': POTS, 'potShare': POT_SHARE,
        'imbFee': IMB_FEE, 'imbs': imbs, 'oid': oid,
    }

def dump(D):
    # uma entrada por linha (como o G): o Git junta alterações a feitiços diferentes sem conflitos
    out = ['{']
    keys = list(D)
    for i, k in enumerate(keys):
        v = D[k]
        end = ',' if i < len(keys) - 1 else ''
        if isinstance(v, dict) and k in ('ab', 'runes', 'imbs'):
            out.append(json.dumps(k) + ': {')
            sub = list(v)
            for j, s in enumerate(sub):
                out.append(' ' + json.dumps(s, ensure_ascii=False) + ': ' +
                           json.dumps(v[s], ensure_ascii=False, separators=(',', ':')) + (',' if j < len(sub) - 1 else ''))
            out.append('}' + end)
        else:
            out.append(json.dumps(k) + ': ' + json.dumps(v, ensure_ascii=False, separators=(',', ':')) + end)
    out.append('}')
    return '\n'.join(out) + '\n'

if __name__ == '__main__':
    D = build()
    txt = dump(D)
    json.loads(txt)
    if '--check' in sys.argv:
        old = open(OUT, encoding='utf-8').read() if os.path.exists(OUT) else ''
        print('igual' if old == txt else 'DIFERENTE: corre sem --check para atualizar')
        sys.exit(0 if old == txt else 1)
    with open(OUT, 'w', encoding='utf-8', newline='') as f:
        f.write(txt)
    print(f"data/rotacoes.json: {len(D['ab'])} feitiços de ataque, {len(D['runes'])} runas, {len(D['imbs'])} imbuements")
