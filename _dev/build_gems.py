"""Modificadores das gemas da Wheel of Destiny para o Grimório (data/gems.json): o que dá cada mod básico e supremo.

Lê, do Canary (opentibiabr/canary, ramo main), numa só pasta:
  player_wheel.hpp  (src/enums/player_wheel.hpp)  os enums WheelGemBasicModifier_t e WheelGemSupremeModifier_t, com os
                    valores numéricos (o enum tem um valor explícito, = 33, e um comentado, = 32: os implícitos contam-se)
  wheel_gems.cpp    (src/creatures/players/components/wheel/)  o switch de addStrategies (o que cada mod aplica e com que
                    número), os multiplicadores de grau e as tabelas de vida/mana/capacidade por vocação
  player_wheel.cpp  (mesma pasta; opcional)  as listas modsSupreme<Voc>Position, que dizem que vocação pode sortear cada mod
                    supremo; sem ele a vocação sai do prefixo do nome (Knight_, SorcererDruid_, General_...)
Escreve <raiz>/data/gems.json: {v, src, grade, tier, basic:[{id,k,n,fx}], supreme:[{id,k,voc,n,fx}]}, uma entrada por linha.

Valores já na unidade que o jogo mostra, no grau I (índice 0 de "grade"). Efeitos (fx):
  ["res", elemento, %]  ["hp"|"mp"|"cap", {vocação: valor}]  ["mit", %]  ["dodge", %]  ["crit", %]  ["lleech", %]
  ["mleech", %]  ["rev", cor, pontos]  ["spell", feitiço, "dmg"|"crit"|"heal"|"cd", valor]
Conversões (confirmadas com a TibiaWiki, páginas Basic Mod e Supreme Mod, e com os textos do cliente do jogo):
  resistências: o Canary guarda centésimos de % (100 = 1%; adjustDamageBasedOnResistanceAndSkill divide por 10000) → /100
  mitigação, dodge, dano crítico, life leech, mana leech: também centésimos de % (500 = 5%, 28 = 0,28%, 80 = 0,8%) → /100
  dano/crítico/cura dos feitiços: já em % (6 = +6%); cooldown: milissegundos → segundos, com sinal negativo (-900 = -900 s)
Como o grau multiplica (grade[g], de 0 a 3): tudo o que é positivo, menos "cd"; as fraquezas (res negativo) e o "cd" ficam fixos.
Nos mods de cooldown o grau não encurta mais: dá antes 0,33% / 0,66% / 1% de Momentum nos graus II / III / IV (wheelBonus.momentum).
Quantos mods tem cada gema (tier = [básicos, supremos]): Lesser 1+0, Regular 2+0, Greater 2+1 (revealGem em player_wheel.cpp; TibiaWiki, Gem Mods).

Onde o Canary e o jogo diferem ganha o jogo, e cada caso está em CORRECOES / MONK_CAP / NOME_REV com a fonte.
O Canary arredonda por dentro o dano do Groundshaker (6,5 passa a 7) e do Flurry of Blows (6,5 passa a 6), por serem int;
aqui vai o que o jogo mostra, 6,5%.

Uso: python -I -X utf8 build_gems.py [pasta do Canary] [--out FICHEIRO]
  pasta do Canary: por omissão a das fontes descarregadas (CANARY abaixo)
  --out: por omissão <raiz>\\data\\gems.json (raiz = a pasta-mãe de _dev)
No fim valida (ids e nomes únicos, todas as entradas do enum, um valor para cada uma das cinco vocações) e escreve as contagens."""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gjson

CANARY = r'C:\Users\finoa\AppData\Local\Temp\claude\C--Users-finoa-Desktop-Questski\a3385e27-235f-4215-9a7b-483bee3dde7f\scratchpad\canary'
SRC = 'Canary (opentibiabr/canary: wheel_gems.cpp, player_wheel.hpp) + TibiaWiki (Gem Atelier), outubro de 2026'
VOCS = ['knight', 'paladin', 'sorcerer', 'druid', 'monk']
VOC_ENUM = {'VOCATION_KNIGHT': 'knight', 'VOCATION_PALADIN': 'paladin', 'VOCATION_SORCERER': 'sorcerer',
            'VOCATION_DRUID': 'druid', 'VOCATION_MONK': 'monk'}
# sufixo das listas modsSupreme<Nome>Position de player_wheel.cpp → vocação
POS_VOC = {'Knight': 'knight', 'Paladin': 'paladin', 'Sorcerer': 'sorcerer', 'Druid': 'druid', 'Monk': 'monk'}
TIER = {'lesser': [1, 0], 'regular': [2, 0], 'greater': [2, 1]}
ELEM = {'PHYSICALDAMAGE': 'physical', 'HOLYDAMAGE': 'holy', 'DEATHDAMAGE': 'death', 'FIREDAMAGE': 'fire',
        'EARTHDAMAGE': 'earth', 'ICEDAMAGE': 'ice', 'ENERGYDAMAGE': 'energy', 'MANADRAIN': 'manadrain',
        'LIFEDRAIN': 'lifedrain'}
ELEM_NOME = {'physical': 'Physical', 'holy': 'Holy', 'death': 'Death', 'fire': 'Fire', 'earth': 'Earth', 'ice': 'Ice',
             'energy': 'Energy', 'manadrain': 'Mana Drain', 'lifedrain': 'Life Drain'}
STAT = {'DODGE': 'dodge', 'CRITICAL_DAMAGE': 'crit', 'LIFE_LEECH': 'lleech', 'MANA_LEECH': 'mleech'}
SPELL_KIND = {'damage': 'dmg', 'criticalDamage': 'crit', 'heal': 'heal'}
KIND_NOME = {'dmg': 'Damage', 'crit': 'Critical Extra Damage', 'heal': 'Healing', 'cd': 'Cooldown'}

# Mods básicos que existem no enum mas não no jogo: no cliente (SkillwheelStringsJsonLibrary.json, BasicModConfig 42 e 43)
# têm a lista de efeitos vazia, como o 32 (o Mana_Capacity comentado); o Canary nunca os sorteia (não estão em
# wheelGemBasicSlot1Allowed nem em wheelGemBasicSlot2Allowed) e o Mixed2 nem tem case em addStrategies. Ficam de fora.
SEM_USO = {'Vocation_Mixed', 'Vocation_Mixed2'}

# O Canary e o jogo diferem: o jogo (TibiaWiki, Supreme Mod e Basic Mod, edições de junho a agosto de 2026; e o cliente) ganha.
# cooldown em segundos: o Canary tem 300 s no Focus Serenity; a wiki e o cliente dizem -150 s
CORRECOES = {'Monk_FocusSerenity_Cooldown': 150}
# o getCapacityValue do Canary não tem o monk (devolveria 0); valores do monk na TibiaWiki, Basic Mod, secção Monks
MONK_CAP = {'Vocation_Capacity': 500, 'Vocation_Capacity_FireResistance': 250, 'Vocation_Capacity_EnergyResistance': 250,
            'Vocation_Capacity_EarthResistance': 250, 'Vocation_Capacity_IceResistance': 250}
# nomes de revelação que o jogo atual escreve de outra maneira (TibiaWiki, Wheel of Destiny/Revelation Perks, revisão de
# junho de 2026): o perk azul do sorcerer chama-se Lord of Destruction (no Canary, Drain Body) e o vermelho do monk
# Spiritual Outburst (no Canary, SpiritualBurst)
NOME_REV = {'DrainBody': 'Lord of Destruction', 'SpiritualBurst': 'Spiritual Outburst'}
AFINIDADE = {'Green': 'green', 'Red': 'red', 'Blue': 'blue', 'Purple': 'purple'}


def num(x):
    """Número sem ruído de vírgula flutuante: 0.28, 1.5, 900 (inteiro quando é inteiro)."""
    x = round(float(x), 4)
    return int(x) if x == int(x) else x


def sem_comentarios(t):
    t = re.sub(r'/\*.*?\*/', '', t, flags=re.S)
    return re.sub(r'//[^\n]*', '', t)


def ler(pasta, nome, obrigatorio=True):
    p = os.path.join(pasta, nome)
    if not os.path.exists(p):
        if obrigatorio:
            sys.exit('falta ' + p)
        return None
    with open(p, encoding='utf-8') as f:
        return sem_comentarios(f.read())


def ler_enum(t, nome):
    """[(nome, valor)] de um enum class, a contar os valores implícitos (o anterior + 1) e a saltar os comentados."""
    m = re.search(r'enum class ' + nome + r'\s*:\s*\w+\s*\{(.*?)\};', t, re.S)
    if not m:
        sys.exit('enum ' + nome + ' não encontrado')
    out, n = [], 0
    for it in m.group(1).split(','):
        it = it.strip()
        if not it:
            continue
        mm = re.fullmatch(r'(\w+)(?:\s*=\s*(\d+))?', it)
        if not mm:
            sys.exit('item de enum que não percebo: ' + it)
        if mm.group(2) is not None:
            n = int(mm.group(2))
        out.append((mm.group(1), n))
        n += 1
    return out


def partir(s):
    """Parte uma lista de argumentos C++ pelas vírgulas de nível zero (ignora as de dentro de parênteses e <>)."""
    out, d, cur = [], 0, ''
    for c in s:
        if c in '(<{':
            d += 1
        elif c in ')>}':
            d -= 1
        if c == ',' and d == 0:
            out.append(cur.strip())
            cur = ''
        else:
            cur += c
    if cur.strip():
        out.append(cur.strip())
    return out


def valor(expr):
    """(número, se multiplica pelo grau) de uma expressão como '100 * gradeMultiplier', '-100' ou 'static_cast<int>(std::round(6.5 * gradeMultiplier))'."""
    m = re.search(r'-?\d+(?:\.\d+)?', expr)
    if not m:
        sys.exit('expressão sem número: ' + expr)
    return float(m.group(0)), 'gradeMultiplier' in expr


def ler_graus(corpo):
    g = [1.0]
    for n in (1, 2, 3):
        m = re.search(r'grade == ' + str(n) + r'\)\s*\{\s*gradeMultiplier = ([\d.]+);', corpo)
        if not m:
            sys.exit('multiplicador do grau ' + str(n) + ' não encontrado')
        g.append(float(m.group(1)))
    return g


def ler_tabelas(t):
    """{funcao: {modificador: {vocação: valor}}} de getHealthValue, getManaValue e getCapacityValue."""
    out = {}
    for fn in ('Health', 'Mana', 'Capacity'):
        m = re.search(r'int32_t WheelGemUtils::get' + fn + r'Value\(Vocation_t.*?\{(.*?)\n\}\n', t, re.S)
        if not m:
            sys.exit('get' + fn + 'Value não encontrada')
        tab = {}
        for mod, corpo in re.findall(r'WheelGemBasicModifier_t::(\w+),\s*\{(.*?)\n\t\t\t\},', m.group(1), re.S):
            tab[mod] = {VOC_ENUM[v]: int(x) for v, x in re.findall(r'Vocation_t::(VOCATION_\w+),\s*(\d+)', corpo)}
        out[fn] = tab
    return out


def ler_casos(corpo, tipo):
    """{modificador: [(estratégia, [argumentos])]} dos case ...: ... break; de um addStrategies; mais as linhas bonus.x.y = n;"""
    out = {}
    for mod, c in re.findall(r'case WheelGem' + tipo + r'Modifier_t::(\w+):(.*?)break;', corpo, re.S):
        st = [(s, partir(a)) for s, a in re.findall(r'make_unique<(\w+)>\(\s*m_wheel\s*,(.*?)\)\);', c, re.S)]
        bonus = re.findall(r'bonus\.(increase|decrease)\.(\w+)\s*=\s*([^;]+);', c)
        out[mod] = (st, bonus)
    return out


def ler_voc_supremos(t):
    """{modificador supremo: [vocações]} das listas modsSupreme<Voc>Position de player_wheel.cpp."""
    out = {}
    for nome, corpo in re.findall(r'std::vector<WheelGemSupremeModifier_t>\s+modsSupreme(\w+?)Position\s*=\s*\{(.*?)\};', t, re.S):
        for mod in re.findall(r'WheelGemSupremeModifier_t::(\w+)', corpo):
            out.setdefault(mod, []).append(POS_VOC[nome])
    return out


def voc_do_prefixo(k):
    p = k.split('_')[0]
    if p == 'General':
        return list(VOCS)
    if p == 'SorcererDruid':
        return ['sorcerer', 'druid']
    return [POS_VOC[p]]


def voc_saida(lst):
    lst = [v for v in VOCS if v in lst]
    if len(lst) == len(VOCS):
        return None
    return lst[0] if len(lst) == 1 else lst


def nome_res(fx):
    """Nome de um mod básico a partir dos efeitos, pela ordem do Canary: 'Mana and Fire Resistance', 'Holy Resistance and Death Weakness'."""
    partes = []
    for e in fx:
        if e[0] == 'res':
            partes.append((ELEM_NOME[e[1]], 'Resistance' if e[2] > 0 else 'Weakness'))
        else:
            partes.append(({'hp': 'Hit Points', 'mp': 'Mana', 'cap': 'Capacity', 'mit': 'Mitigation Multiplier'}[e[0]], ''))
    if len(partes) == 2 and partes[0][1] and partes[0][1] == partes[1][1]:
        return partes[0][0] + ' and ' + partes[1][0] + ' ' + partes[0][1]  # 'Fire and Earth Resistance'
    return ' and '.join((a + ' ' + b).strip() for a, b in partes)


def camel(s):
    """'AvatarOfSteel' → 'Avatar of Steel'."""
    p = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', s).split(' ')
    return ' '.join(w.lower() if w in ('Of', 'The') else w for w in p)


def main():
    a = sys.argv[1:]
    out = os.path.join(gjson.default_root(), 'data', 'gems.json')
    if '--out' in a:
        i = a.index('--out')
        out = a[i + 1]
        del a[i:i + 2]
    pasta = a[0] if a else CANARY

    enums = ler(pasta, 'player_wheel.hpp')
    gems = ler(pasta, 'wheel_gems.cpp')
    pw = ler(pasta, 'player_wheel.cpp', obrigatorio=False)
    basic_enum = ler_enum(enums, 'WheelGemBasicModifier_t')
    supreme_enum = ler_enum(enums, 'WheelGemSupremeModifier_t')

    i1 = gems.index('addStrategies(WheelGemBasicModifier_t modifier, uint8_t grade) {')
    i2 = gems.index('addStrategies(WheelGemSupremeModifier_t modifier, uint8_t grade) {')
    i3 = gems.index('WheelModifierContext::executeStrategies')
    corpo_b, corpo_s = gems[i1:i2], gems[i2:i3]
    grade = ler_graus(corpo_b)
    if ler_graus(corpo_s) != grade:
        sys.exit('os multiplicadores de grau dos básicos e dos supremos diferem')
    tab = ler_tabelas(gems)
    casos_b, casos_s = ler_casos(corpo_b, 'Basic'), ler_casos(corpo_s, 'Supreme')

    avisos = []
    # nomes bonitos dos feitiços (com apóstrofos) e normalização para os nomes de revelação
    feiticos = {}
    for st, _ in casos_s.values():
        for s, args in st:
            if s == 'GemModifierSpellBonusStrategy':
                n = args[0].strip('"')
                feiticos[re.sub(r'\W', '', n).lower()] = n

    # ---- mods básicos
    basic, ignorados = [], []
    for k, i in basic_enum:
        if k in SEM_USO or k not in casos_b:
            ignorados.append(k)
            continue
        st, _ = casos_b[k]
        fx = []
        for s, args in st:
            if s == 'GemModifierResistanceStrategy':
                v, esc = valor(args[1])
                fx.append(['res', ELEM[args[0].split('COMBAT_')[1]], num(v / 100)])
                if (v > 0) != esc:
                    avisos.append(k + ': resistência ' + args[1] + ' (positiva sem grau ou negativa com grau)')
            elif s == 'GemModifierStatStrategy':
                stat = args[0].split('::')[1]
                if stat == 'MITIGATION':
                    fx.append(['mit', num(valor(args[1])[0] / 100)])
                elif stat in ('HEALTH', 'MANA', 'CAPACITY'):
                    fn = {'HEALTH': 'Health', 'MANA': 'Mana', 'CAPACITY': 'Capacity'}[stat]
                    if 'get' + fn + 'Value' not in args[1]:
                        sys.exit(k + ': esperava get' + fn + 'Value em ' + args[1])
                    por = dict(tab[fn].get(k, {}))
                    if stat == 'CAPACITY' and 'monk' not in por and k in MONK_CAP:
                        por['monk'] = MONK_CAP[k]
                    falta = [v for v in VOCS if v not in por]
                    if falta:
                        sys.exit(k + ': sem valor para ' + ','.join(falta))
                    fx.append([{'HEALTH': 'hp', 'MANA': 'mp', 'CAPACITY': 'cap'}[stat], {v: por[v] for v in VOCS}])
                else:
                    sys.exit(k + ': stat que não conheço: ' + stat)
            else:
                sys.exit(k + ': estratégia que não conheço: ' + s)
        if not fx:
            sys.exit(k + ': sem efeitos')
        basic.append({'id': i, 'k': k, 'n': nome_res(fx), 'fx': fx})

    # ---- mods supremos
    voc_pos = ler_voc_supremos(pw) if pw else {}
    supreme = []
    for k, i in supreme_enum:
        if k not in casos_s:
            ignorados.append(k)
            continue
        st, bonus = casos_s[k]
        fx, n = [], None
        for s, args in st:
            if s == 'GemModifierStatStrategy':
                stat = args[0].split('::')[1]
                if stat not in STAT:
                    sys.exit(k + ': stat que não conheço: ' + stat)
                fx.append([STAT[stat], num(valor(args[1])[0] / 100)])
                n = {'dodge': 'Dodge', 'crit': 'Critical Extra Damage', 'lleech': 'Life Leech', 'mleech': 'Mana Leech'}[STAT[stat]]
            elif s == 'GemModifierRevelationStrategy':
                cor = AFINIDADE[args[0].split('::')[1]]
                fx.append(['rev', cor, num(valor(args[1])[0])])
                nm = k.split('_RevelationMastery_')[1]
                alvo = NOME_REV.get(nm) or feiticos.get(re.sub(r'\W', '', nm).lower()) or camel(nm)
                n = 'Revelation Mastery: ' + alvo
            elif s == 'GemModifierSpellBonusStrategy':
                feitico = args[0].strip('"')
                if len(bonus) != 1:
                    sys.exit(k + ': esperava um só bonus.x.y = n; e há ' + str(len(bonus)))
                lado, campo, expr = bonus[0]
                if lado == 'decrease' and campo == 'cooldown':
                    ms = re.fullmatch(r'\s*(\d+)\s*\*\s*1000\s*', expr)
                    if not ms:
                        sys.exit(k + ': cooldown que não percebo: ' + expr)
                    seg = int(ms.group(1))
                    if k in CORRECOES:
                        seg = CORRECOES[k]
                    fx.append(['spell', feitico, 'cd', -seg])
                    kind = 'cd'
                elif lado == 'increase' and campo in SPELL_KIND:
                    fx.append(['spell', feitico, SPELL_KIND[campo], num(valor(expr)[0])])
                    kind = SPELL_KIND[campo]
                else:
                    sys.exit(k + ': bonus que não conheço: ' + lado + '.' + campo)
                # 'Ultimate Healing Healing' → 'Ultimate Healing Boost' (o nome do feitiço já acaba em Healing)
                n = feitico + ' ' + ('Boost' if kind == 'heal' and feitico.endswith('Healing') else KIND_NOME[kind])
            else:
                sys.exit(k + ': estratégia que não conheço: ' + s)
        # um mod = um efeito; os Revelation do Canary aparecem duas vezes no código (strategy + addRevelationBonus direto)
        if len(fx) != 1:
            sys.exit(k + ': esperava um efeito e há ' + str(len(fx)))
        pref = voc_do_prefixo(k)
        if pw:
            voc = voc_pos.get(k)
            if not voc:
                avisos.append(k + ': não está em nenhuma lista modsSupreme*Position; vocação pelo prefixo')
                voc = pref
            elif sorted(voc) != sorted(pref):
                avisos.append(k + ': vocações das listas ' + ','.join(voc) + ' ≠ prefixo ' + ','.join(pref))
        else:
            voc = pref
        supreme.append({'id': i, 'k': k, 'voc': voc_saida(voc), 'n': n, 'fx': fx})

    # ---- validação
    for nome, lst, en in (('basic', basic, basic_enum), ('supreme', supreme, supreme_enum)):
        ids = [x['id'] for x in lst]
        assert len(ids) == len(set(ids)), nome + ': ids repetidos'
        ks = [x['k'] for x in lst]
        assert len(ks) == len(set(ks)), nome + ': nomes repetidos'
        falta = [k for k, _ in en if k not in ks and k not in ignorados]
        assert not falta, nome + ': entradas do enum em falta ' + str(falta)
        for x in lst:
            assert x['fx'] and x['n'], x
    for nome, lst in (('basic', basic), ('supreme', supreme)):
        ns = [x['n'] for x in lst]
        rep = sorted(set(n for n in ns if ns.count(n) > 1))
        assert not rep, nome + ': nomes (n) repetidos: ' + str(rep)
    for av in avisos:
        print('AVISO', av)

    # ---- escrita: uma entrada por linha, separadores compactos
    def c(v):
        return json.dumps(v, ensure_ascii=False, separators=(',', ':'), allow_nan=False)
    linhas = ['{', '"v":1,', '"src":' + c(SRC) + ',', '"grade":' + c([num(g) for g in grade]) + ',', '"tier":' + c(TIER) + ',']
    linhas.append('"basic":[')
    linhas.append(',\n'.join(c({'id': x['id'], 'k': x['k'], 'n': x['n'], 'fx': x['fx']}) for x in basic))
    linhas.append('],')
    linhas.append('"supreme":[')
    linhas.append(',\n'.join(c({'id': x['id'], 'k': x['k'], 'voc': x['voc'], 'n': x['n'], 'fx': x['fx']}) for x in supreme))
    linhas.append(']')
    linhas.append('}')
    texto = '\n'.join(linhas) + '\n'
    json.loads(texto)  # tem de ler
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, 'w', encoding='utf-8', newline='\n') as f:
        f.write(texto)
    print('escrito', out, len(texto.encode('utf-8')), 'bytes')
    print('básicos:', len(basic), '(enum', len(basic_enum), '; de fora:', ', '.join(k for k in ignorados if k in dict(basic_enum)) or '-', ')')
    print('supremos:', len(supreme), '(enum', len(supreme_enum), '; de fora:', ', '.join(k for k in ignorados if k in dict(supreme_enum)) or '-', ')')
    print('graus:', [num(g) for g in grade])


if __name__ == '__main__':
    main()
