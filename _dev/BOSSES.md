# Bosses por nível

A página **Bosses** (Hunts → Bosses) diz que bosses do Bosstiary cada personagem pode fazer no seu nível: sozinho, em equipa ou
mais tarde. Mostra também quanto dá cada um e o progresso no Bosstiary.

## Ficheiros
- `_dev/build_bosses.py` → `data/bosses.json`: os bosses das categorias Bane, Archfoe e Nemesis da TibiaWiki, um por linha.
  - Campos: classe, vida, XP, cooldown, tipo de spawn, alavanca, quest de acesso com o nível mínimo e o recomendado, sítios,
    dano máximo por turno e % de cada elemento no dano que faz.
  - `--loot` acrescenta ao `data/items.json` os itens do loot dos bosses que lá faltavam (ex.: Gold e Silver Token), para terem
    preço do NPC e do Market. Depois corre `build_search.py`.
- `shared/bosses.js` (`window.GrimBoss`): o modelo (`judge`, `makeCurve`, Bosstiary). Teste: `node _dev/bosses_test.mjs`.
- O loot e as resistências vêm do `data/creatures.json`; o valor por kill sai do `lootPerKill` do site, aos preços do mundo.

## O modelo (por boss, com a vocação e o nível)
1. **Acesso:** abaixo do nível mínimo da quest (`ql`) não entras. Nunca se recomenda abaixo do nível recomendado (`qr`), porque
   as fases e mecânicas dos bosses de quest não entram nas contas.
2. **Aguentar:** a vida efetiva tem de chegar a 2 golpes do dano máximo por turno (`md`) sozinho, ou a 1,3 em equipa.
   - Knight, paladino e monk: vida × 1,35 / 1,15 / 1,25 (defesa média aproximada).
   - Magos: vida + Magic Shield (7 × ML + 7,6 × nível + máx(300, 0,4 × nível)).
3. **Matar:** vida do boss ÷ (70% do dano por segundo de boss × o melhor multiplicador de elemento das linhas da vocação).
   - Limites sozinho: Bane 2,5 min, Archfoe 5 min, Nemesis 10 min.
   - Em equipa: 4 personagens iguais e 1,5 vezes o tempo.
4. **Falta de dados:**
   - sem vida conhecida, não há "sozinho";
   - sem dano máximo, "sozinho" só até 20 000 de vida.

O dano de boss é o `GrimRot.plan` (cenário boss, com os ataques automáticos) nos níveis `GrimBoss.ANCHORS`, com stats estimados.
A curva é escalada pelo dano real da personagem no seu nível (o ML ou skill da ficha e o equipamento: o set, ou o BiS do nível).

## Bosstiary (Cyclopedia, TibiaWiki)

| Categoria | Mortes Prowess / Expertise / Mastery | Pontos |
|---|---|---|
| Bane | 25 / 100 / 300 | 5 + 15 + 30 |
| Archfoe | 5 / 20 / 60 | 10 + 30 + 60 |
| Nemesis | 1 / 3 / 5 | 10 + 30 + 60 |

Bónus de loot do boss no slot:
- 25% a 0 pontos e +1% a cada 10, até 250 pontos (50%);
- depois +1% a cada 20, até 1250 pontos (100%);
- depois cada 1% pede mais 5 pontos do que o anterior (25, 30, 35…).

## Limitações
- O modelo é uma estimativa. Ficam de fora:
  - mecânicas (fases, curas, summons, campos);
  - mitigação real;
  - prey, charms e imbuements;
  - a qualidade da equipa.
- A TibiaWiki não tem a vida de alguns bosses recentes. As notas de estratégia (texto livre, em inglês) não entram.
- A quest de acesso vem da 1.ª quest ligada nas notas ou na localização da página do boss, mais a tabela `ACCESS` do
  `build_bosses.py` para os que não a ligam. Sem quest, não há nível de acesso.
