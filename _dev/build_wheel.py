"""Dados da Wheel of Destiny para o Grimório: o que dá cada uma das 36 fatias, por vocação, e validação contra as builds.

As 36 fatias seguem a ordem do enum WheelSlots_t do Canary (src/creatures/players/components/wheel/wheel_definitions.hpp),
que é a mesma ordem dos 36 primeiros bytes do código de exportação do jogo (letra da vocação + '0' + deflate cru em base64url):
uma grelha 6×6 lida por linhas, com o verde em cima à esquerda, o vermelho em cima à direita, o azul em baixo à esquerda e o
roxo em baixo à direita. Os 12 bytes seguintes são as gemas (255 = vazio).

Dedicação (vida/mana/capacidade/mitigação por ponto) e o tipo de convicção de cada fatia: io_wheel.cpp do Canary.
Os nomes dos feitiços aumentados e das revelações seguem o jogo atual (as builds do TibiaPal), porque o Canary ainda tem
os nomes de antes da revisão das vocações (ex.: Magic Shield → Death Echo no sorcerer).

Uso: python build_wheel.py            valida contra G.wheel (index.html) e escreve data/wheel.json
"""
import base64, json, os, sys, zlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gjson

ROOT = gjson.default_root()
VOCS = ['knight', 'paladin', 'sorcerer', 'druid', 'monk']
# por ponto: vida, mana, capacidade (io_wheel.cpp)
HP = {'knight': 3, 'paladin': 2, 'sorcerer': 1, 'druid': 1, 'monk': 2}
MP = {'knight': 1, 'paladin': 3, 'sorcerer': 6, 'druid': 6, 'monk': 2}
CAP = {'knight': 5, 'paladin': 4, 'sorcerer': 2, 'druid': 2, 'monk': 5}
MIT = 0.075  # % de mitigação por ponto (0,03 antes da atualização de junho de 2026; TibiaWiki, Dedication Perks)
DOMS = ['green', 'red', 'blue', 'purple']
VRN = {'green': 'Vessel Resonance Top Left', 'red': 'Vessel Resonance Top Right', 'blue': 'Vessel Resonance Bottom Left', 'purple': 'Vessel Resonance Bottom Right'}
SKILL = {'knight': 'Weapon Skill Boost', 'paladin': 'Distance Skill Boost', 'sorcerer': 'Magic Skill Boost', 'druid': 'Magic Skill Boost', 'monk': 'Fist Fighting Skill Boost'}
# grupos de feitiços aumentados (2 fatias cada): A = vermelho 200 / azul 50, B = verde meio 100 / roxo topo 100,
# C = vermelho meio 100 / azul meio 100, D = verde baixo 100 / roxo meio 100, E = vermelho 50 / azul 200
SPELLS = {
    # nomes do jogo atual, deduzidos das builds do TibiaPal; knight B/D e druid B/D não aparecem em nenhuma build e ficam
    # como no Canary (Shield Slam substitui o Chivalrous Challenge na revisão de 2026)
    'knight':   {'A': 'Front Sweep', 'B': 'Shield Slam', 'C': 'Groundshaker', 'D': 'Intense Wound Cleansing', 'E': 'Fierce Berserk'},
    'paladin':  {'A': 'Ethereal Barrage', 'B': 'Strong Ethereal Spear', 'C': 'Divine Dazzle', 'D': 'Divine Barrage', 'E': 'Divine Caldera'},
    'sorcerer': {'A': 'Focus Spells', 'B': 'Special Spells', 'C': 'Death Echo', 'D': 'Energy Wave', 'E': 'Great Fire Wave'},
    'druid':    {'A': 'Forked Spells', 'B': 'Mass Healing', 'C': 'Heal Friend', 'D': 'Terra Wave', 'E': 'Strong Ice Wave'},
    'monk':     {'A': 'Chained Penance', 'B': 'Mass Spirit Mend', 'C': 'Mystic Repulse', 'D': 'Flurry of Blows', 'E': 'Thousand Fist Blows'},
}
# perks das fatias de 200 (verde = G200, roxo = P200)
INST = {
    'G200': {'knight': 'Battle Instinct', 'paladin': 'Positional Tactics', 'sorcerer': 'Runic Mastery', 'druid': 'Healing Link', 'monk': 'Guiding Presence'},
    'P200': {'knight': 'Battle Healing', 'paladin': 'Ballistic Mastery', 'sorcerer': 'Focus Mastery', 'druid': 'Runic Mastery', 'monk': 'Sanctuary'},
}
# revelação de cada domínio (player_wheel.cpp: applyStageBonusForColor); 250/500/1000 pontos no domínio = estágio 1/2/3
REV = {
    'green': {v: 'Gift of Life' for v in VOCS},
    'red': {'knight': "Executioner's Throw", 'paladin': 'Divine Grenade', 'sorcerer': 'Beam Mastery', 'druid': 'Blessing of the Grove', 'monk': 'Spiritual Outburst'},
    'purple': {'knight': 'Avatar of Steel', 'paladin': 'Avatar of Light', 'sorcerer': 'Avatar of Storm', 'druid': 'Avatar of Nature', 'monk': 'Avatar of Balance'},
    'blue': {'knight': 'Combat Mastery', 'paladin': 'Divine Empowerment', 'sorcerer': 'Lord of Destruction', 'druid': 'Twin Bursts', 'monk': 'Ascetic'},
}
REVDH = [4, 9, 20]  # dano e cura por domínio no estágio 1/2/3
# fatias (ordem do enum): nome Canary, domínio, máximo, dedicação, convicção
S = [
    ('GREEN_200', 'green', 200, 'hpmp', 'inst:G200'), ('GREEN_TOP_150', 'green', 150, 'mit', 'mleech'), ('GREEN_TOP_100', 'green', 100, 'hp', 'vr'),
    ('RED_TOP_100', 'red', 100, 'mp', 'skill'), ('RED_TOP_150', 'red', 150, 'hp', 'vr'), ('RED_200', 'red', 200, 'hpmp', 'sp:A'),
    ('GREEN_BOTTOM_150', 'green', 150, 'mit', 'vr'), ('GREEN_MIDDLE_100', 'green', 100, 'hp', 'sp:B'), ('GREEN_TOP_75', 'green', 75, 'mp', 'lleech'),
    ('RED_TOP_75', 'red', 75, 'cap', 'vr'), ('RED_MIDDLE_100', 'red', 100, 'mp', 'sp:C'), ('RED_BOTTOM_150', 'red', 150, 'hp', 'mleech'),
    ('GREEN_BOTTOM_100', 'green', 100, 'hp', 'sp:D'), ('GREEN_BOTTOM_75', 'green', 75, 'mp', 'skill'), ('GREEN_50', 'green', 50, 'cap', 'vr'),
    ('RED_50', 'red', 50, 'mit', 'sp:E'), ('RED_BOTTOM_75', 'red', 75, 'cap', 'lleech'), ('RED_BOTTOM_100', 'red', 100, 'mp', 'vr'),
    ('BLUE_TOP_100', 'blue', 100, 'mit', 'vr'), ('BLUE_TOP_75', 'blue', 75, 'hp', 'mleech'), ('BLUE_50', 'blue', 50, 'mp', 'sp:A'),
    ('PURPLE_50', 'purple', 50, 'hp', 'vr'), ('PURPLE_TOP_75', 'purple', 75, 'mit', 'skill'), ('PURPLE_TOP_100', 'purple', 100, 'cap', 'sp:B'),
    ('BLUE_TOP_150', 'blue', 150, 'cap', 'lleech'), ('BLUE_MIDDLE_100', 'blue', 100, 'mit', 'sp:C'), ('BLUE_BOTTOM_75', 'blue', 75, 'hp', 'vr'),
    ('PURPLE_BOTTOM_75', 'purple', 75, 'mit', 'mleech'), ('PURPLE_MIDDLE_100', 'purple', 100, 'cap', 'sp:D'), ('PURPLE_TOP_150', 'purple', 150, 'mp', 'vr'),
    ('BLUE_200', 'blue', 200, 'hpmp', 'sp:E'), ('BLUE_BOTTOM_150', 'blue', 150, 'cap', 'vr'), ('BLUE_BOTTOM_100', 'blue', 100, 'mit', 'skill'),
    ('PURPLE_BOTTOM_100', 'purple', 100, 'cap', 'vr'), ('PURPLE_BOTTOM_150', 'purple', 150, 'mp', 'lleech'), ('PURPLE_200', 'purple', 200, 'hpmp', 'inst:P200'),
]
assert len(S) == 36


def decode(code):
    s = code[2:]
    b = base64.urlsafe_b64decode(s + '=' * (-len(s) % 4))
    d = list(zlib.decompress(b, -15))
    return d[:36], d[36:48]


def conv_name(voc, conv, dom, spells):
    if conv == 'vr': return VRN[dom]
    if conv == 'skill': return SKILL[voc]
    if conv == 'mleech': return 'Mana Leech'
    if conv == 'lleech': return 'Life Leech'
    if conv.startswith('inst:'): return INST[conv[5:]][voc]
    if conv.startswith('sp:'): return 'Augmented ' + spells[conv[3:]]
    raise ValueError(conv)


def predict(voc, pts, spells):
    hp = mp = cap = 0; mit = 0.0; conv = {}; dom = {d: 0 for d in DOMS}
    for i, (nm, d, mx, ded, cv) in enumerate(S):
        p = pts[i]; dom[d] += p
        if ded in ('hp', 'hpmp'): hp += HP[voc] * p
        if ded in ('mp', 'hpmp'): mp += MP[voc] * p
        if ded == 'cap': cap += CAP[voc] * p
        if ded == 'mit': mit += MIT * p
        if p >= mx:
            n = conv_name(voc, cv, d, spells); conv[n] = conv.get(n, 0) + 1
    rev = {}
    for d in DOMS:
        st = 3 if dom[d] >= 1000 else 2 if dom[d] >= 500 else 1 if dom[d] >= 250 else 0
        if st: rev[REV[d][voc]] = st
    return hp, mp, cap, mit, conv, rev, dom


def num(s):
    return float(str(s).replace(',', '').replace('+', '').replace('%', ''))


ROMAN = {'I': 1, 'II': 2, 'III': 3}


def main():
    G = [x for x in gjson.load_G(ROOT) if isinstance(x, dict)][0]
    bad = 0; seen = {}
    for voc in VOCS:
        for w in G['wheel'][voc]:
            pts, gems = decode(w['c'])
            hp, mp, cap, mit, conv, rev, dom = predict(voc, pts, SPELLS[voc])
            ded = {k: num(v) for k, v in w['ded']}
            exp_conv = {}
            for k, v in w['conv']:
                v = str(v or '').strip()
                exp_conv[k] = ROMAN.get(v, None) if v in ROMAN else (int(num(v)) if v else 1)
            got_conv = {}
            for k, n in conv.items():
                if k in ('Mana Leech', 'Life Leech'): got_conv[k] = n
                elif k == SKILL[voc]: got_conv[k] = n
                else: got_conv[k] = n
            msg = []
            if abs(ded.get('Hit Points', 0) - hp) > 0.5: msg.append(f'HP {ded.get("Hit Points")} vs {hp}')
            if abs(ded.get('Mana', 0) - mp) > 0.5: msg.append(f'Mana {ded.get("Mana")} vs {mp}')
            if abs(ded.get('Capacity', 0) - cap) > 0.5: msg.append(f'Cap {ded.get("Capacity")} vs {cap}')
            if abs(ded.get('Mitigation Multiplier', 0) - mit) > 0.01: msg.append(f'Mit {ded.get("Mitigation Multiplier")} vs {mit:.2f}')
            ek = set(exp_conv); gk = set(got_conv)
            if ek != gk: msg.append(f'conv só no TibiaPal {sorted(ek - gk)} só previsto {sorted(gk - ek)}')
            exp_rev = {k: int(str(v).replace('Stage ', '')) for k, v in w['rev'] if k != 'Damage and Healing'}
            if exp_rev != {k: v for k, v in rev.items()}: msg.append(f'rev {exp_rev} vs {rev}')
            if msg:
                bad += 1; print(voc, w['p'], ' | '.join(msg))
    print('builds com diferenças:', bad)

# textos em pt-PT para o site (efeitos: TibiaWiki, Conviction/Revelation Perks, outubro de 2026)
AUG_PT = {
    'Fierce Berserk': ['−30 de mana', '+10% de dano base'], 'Intense Wound Cleansing': ['+125% de cura base', '−60 s de cooldown'],
    'Shield Slam': ['+15% de life leech', '+25% de redução de dano (75% no total)'], 'Groundshaker': ['−2 s de cooldown', '+12,5% de dano base'],
    'Front Sweep': ['+40% de poder base', '+2 sqm de alcance'],
    'Divine Caldera': ['−20 de mana', '+10% de dano base'], 'Divine Barrage': ['+8% de dano base', '+12% de dano base'],
    'Divine Dazzle': ['+2 alvos em cadeia', '+4 s de duração e −8 s de cooldown'], 'Strong Ethereal Spear': ['−2 s de cooldown', '+380% de dano base'],
    'Ethereal Barrage': ['+10% de life leech', '+10% de chance de crítico'],
    'Heal Friend': ['+4% de cura base', '+6% de cura base'], 'Terra Wave': ['+6,5% de dano base', '+10% de life leech'],
    'Mass Healing': ['+4% de cura base', 'área maior'], 'Strong Ice Wave': ['+6% de dano base', 'área maior'], 'Forked Spells': ['−2 s de cooldown', '+1 alvo'],
    'Great Fire Wave': ['+10% de chance de crítico e +15% de dano crítico', '+5% de dano base'], 'Energy Wave': ['área maior', '+10% de dano base'],
    'Death Echo': ['−2 s de cooldown', '+12% de dano base'], 'Special Spells': ['−4 s de cooldown', '+50% de dano base'],
    'Focus Spells': ['+5% de dano base', '−4 s no cooldown secundário dos focus spells'],
    'Mass Spirit Mend': ['+8% de cura base', '−4 s de cooldown'], 'Flurry of Blows': ['área maior', '+15% de dano base'],
    'Mystic Repulse': ['−6 s de cooldown', '+40% de dano base'], 'Thousand Fist Blows': ['+40% de dano crítico extra', '−6 s de cooldown'],
    'Chained Penance': ['+1 alvo', '+18% de dano base'],
}
PERK_PT = {
    'Vessel Resonance': 'Ativa as gemas deste domínio: 1 ressonância chega para uma lesser gem, 2 para uma regular e 3 para uma greater. Com o número certo, +1 de dano e cura (+2 na greater).',
    'Mana Leech': '+0,25% de mana leech.', 'Life Leech': '+0,75% de life leech.',
    'Skill Boost': '+1 no skill principal da vocação.',
    'Battle Instinct': 'Os feitiços de cura curam +10%, o triplo com escudo.',
    'Battle Healing': 'Os feitiços de cura curam +10%, o triplo com escudo.',
    'Positional Tactics': '+3 de distance sem monstros a 1 sqm; com monstros ao lado, +3 de magic level holy e de cura.',
    'Ballistic Mastery': 'Crossbow: +10% de dano crítico extra. Bow: +4% de pierce físico e holy.',
    'Healing Link': 'Ao curar alguém com Nature\'s Embrace ou Heal Friend, curas-te 10% desse valor.',
    'Runic Mastery': 'Runas: 25% de chance de +10% de magic level nesse uso (+20% com runas da tua vocação).',
    'Focus Mastery': 'Depois de Hell\'s Core ou Rage of the Skies, o próximo feitiço de dano em 12 s faz +35%; −2 s no cooldown de grupo dos focus spells.',
    'Guiding Presence': 'Aura que partilha o teu mantra com o grupo e aumenta em 33% os bónus passivos de party.',
    'Sanctuary': 'Gastar Harmony cria um campo de 5 s: +2% de dano e cura por Harmony, +10% contra inimigos e aliados ao lado.',
}
REV_PT = {
    'Gift of Life': 'Em certas condições cura-te antes de um golpe fatal: uma segunda oportunidade.',
    'Avatar of Steel': 'Transforma-te num avatar com vários bónus durante uns segundos.', 'Avatar of Light': 'Transforma-te num avatar com vários bónus durante uns segundos.',
    'Avatar of Storm': 'Transforma-te num avatar com vários bónus durante uns segundos.', 'Avatar of Nature': 'Transforma-te num avatar com vários bónus durante uns segundos.',
    'Avatar of Balance': 'Transforma-te num avatar com vários bónus durante uns segundos.',
    "Executioner's Throw": 'Atira a arma ao alvo e salta para 2/3/4 inimigos; +100/125/150% de dano em alvos abaixo de 30% de vida. Cooldown 18/14/10 s.',
    'Combat Mastery': 'Levas menos dano quanto menos vida tens (o dobro com escudo) e fazes mais dano quanto menos vida o alvo tem (o dobro com arma de duas mãos).',
    'Divine Grenade': 'Marca o alvo e explode 3 s depois com dano holy. Cooldown 26/20/14 s.',
    'Divine Empowerment': 'Campo de 3×3 durante 5 s: +8/10/12% de dano enquanto estás lá dentro. Cooldown 32/28/24 s.',
    'Blessing of the Grove': 'As curas podem ser críticas e curam mais quanto menos vida o alvo tem (+5% a +20%).',
    'Twin Bursts': 'Ice Burst ou Terra Burst à tua volta: +20/40/60% de dano em alvos acima de 60% de vida. Cooldown 22/18/14 s.',
    'Beam Mastery': 'Os beams acertam também nos sqm ao lado e ganham dano e menos cooldown por cada alvo atingido no centro.',
    'Lord of Destruction': 'Melhora os stances: fogo +2/3/4% de poder, energia +2/3/4% de crítico, morte +15/25,5/30% de dano crítico.',
    'Spiritual Outburst': 'Ataque que gasta Harmony e salta para 7 inimigos; com Harmony cheio repete por 37,5/50/62,5%. Cooldown 24/20/16 s.',
    'Ascetic': 'Melhora os spenders: +1/2/3% de Harmony base e os ataques normais fazem +100/200/300% do teu mantra.',
}


def write_json():
    out = {'v': 1, 'src': 'Canary (io_wheel.cpp) + TibiaWiki (Wheel of Destiny, outubro de 2026), validado com as builds do TibiaPal',
           'mit': MIT, 'revdh': REVDH, 'stage': [250, 500, 1000],
           'slots': [[d, mx, ded, cv] for (nm, d, mx, ded, cv) in S],
           'voc': {v: {'hp': HP[v], 'mp': MP[v], 'cap': CAP[v], 'skill': SKILL[v], 'sp': SPELLS[v],
                       'inst': {k: INST[k][v] for k in INST}, 'rev': {d: REV[d][v] for d in DOMS}} for v in VOCS},
           'aug': AUG_PT, 'perk': PERK_PT, 'revd': REV_PT}
    # pontos de cada fatia de cada build (pelo código), para o site não ter de descomprimir os códigos
    G = [x for x in gjson.load_G(ROOT) if isinstance(x, dict)][0]
    out['b'] = {w['c']: decode(w['c'])[0] for v in VOCS for w in G['wheel'][v]}
    for v in VOCS:
        for n in SPELLS[v].values(): assert n in AUG_PT, n
        for k in INST: assert INST[k][v] in PERK_PT, INST[k][v]
        for d in DOMS: assert REV[d][v] in REV_PT, REV[d][v]
    p = os.path.join(ROOT, 'data', 'wheel.json')
    with open(p, 'w', encoding='utf-8', newline='\n') as f: json.dump(out, f, ensure_ascii=False, separators=(',', ':'))
    print('escrito', p, os.path.getsize(p), 'bytes')


if __name__ == '__main__':
    main()
    write_json()
