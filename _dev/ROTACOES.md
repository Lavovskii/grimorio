# Motor de rotações (hotkeys de ataque)

Ligado à página **Rotação e hotkeys** (`#rotacao`, `renderRx` no index.html) desde a r13. Falta ligá-lo à ficha das hunts
(com o `eff` das criaturas) e ao montador da barra.

## Ficheiros
- `shared/rotacoes.js`: o motor, em JS sem dependências. No browser é `window.GrimRot` e no node é `require(...)`.
- `data/rotacoes.json`: os dados do motor, gerados por `_dev/build_rotacoes.py` a partir do `data/spells.json`, com uma
  entrada por linha. Volta a correr o build quando mudares o spells.json ou as tabelas do script. O build não vai à rede.
  - `python -I -X utf8 _dev/build_rotacoes.py [raiz]` escreve o ficheiro.
  - `--check` não escreve; diz se o ficheiro está igual.
- `_dev/rotacoes_test.mjs`: o teste. `node _dev/rotacoes_test.mjs` corre 600 planos (5 vocações × 4 cenários × 2 orçamentos ×
  15 níveis) e confirma as regras desta página. Sai com 1 se alguma falhar.

## Como se usa
```js
const P = GrimRot.plan(D, {
  voc: "druid", level: 500,            // obrigatórios
  scen: "boss",                        // boss | caixa (monstros colados) | espalhados (lure) | party
  budget: "max",                       // max | eco (limite pelo nível: GrimRot.ecoCap(nível)) | número em gp/h
  eff: G.places[pid].eff,              // opcional: % de dano que as criaturas levam por elemento (100 = neutro)
  ml: 0, skill: 0,                     // opcional: os da personagem sem equipamento; se faltarem, estima-se pelo nível
  gear: {ml, mlEl:{fire:1,…}, sk, atk},// opcional: bónus do equipamento (ML, ML por elemento, skill de ataque, ataque da arma + munição)
  shield: true,                        // knight: com escudo (Shield Bash/Slam) ou duas mãos
  wheel: null,                         // estágio dos feitiços da Wheel (0–3); por omissão pelo nível (300/550/1050)
  role: "dps",                         // party: knight 'dps' (senão Protector), druid 'healer' (Shared Conservation)
  lane: null,                          // força um elemento: gelo|terra, fogo|energia|morte, holy|fisico, fisico
  mix: false,                          // misturar elementos (só com eff e quando a criatura leva o mesmo dos dois)
  forkBoss: false,                     // Forked no boss (fora por omissão)
  price: (chave) => gp                 // opcional: preço dos materiais dos imbuements (ex.: buyOf/priceOf do site)
});
GrimRot.toHK(P);   // → [{g, k:[{k, c:[...], d}]}], o formato de G.voc[voc].hk
GrimRot.toRot(P);  // → {t, seq:[[palavras, nome]], why}, o formato de uma entrada de G.voc[voc].rot
```
O plano devolve:

| Campo | O que é |
|---|---|
| `lane` | O elemento escolhido. |
| `alts` | As outras linhas de elemento, com a % de dano face à escolhida. |
| `stance` | A stance a usar e o porquê. |
| `opener` | O que se lança ao abrir a luta: DoTs, Avatar, Divine Empowerment e as poções Mastermind, Berserk e Bullseye. |
| `rotation` | Por ordem de prioridade: nome, palavras, lançamentos por minuto, % do dano, dano por lançamento, se é para lançar em cooldown, se é enchimento, e o porquê. |
| `seq` | Os primeiros 12 lançamentos. |
| `out` | O que ficou de fora e porquê. |
| `econ` | gp/h, gp/h só em runas, mana por segundo, leech por segundo, mana que falta, poção, `dps` (ótimo do LP) e `dpsSeq` (sequência simulada). |
| `imbs` | Os imbuements, com números. |
| `notes` | As notas de jogo. |
| `mab` | Os Multi-Action Buttons: `mabs` (até 3 ações cada, por ordem), `keys` (teclas à parte, ex. spenders do monk), `dps` e `pct` (dano carregando nas MABs por ordem, em % do ótimo) e `gpH`. |

Demora cerca de 2 ms por plano.

## O modelo
1. **Dano de um lançamento.** É base power × alvos × % que a criatura leva desse elemento × escala da família:
   - **magic**: nível e ML.
   - **melee** e **fist**: nível, skill e ataque da arma.
   - **dist**: nível e distance.

   As escalas vêm das fórmulas da página Formulae da TibiaWiki, medidas antes de 2020, por isso são aproximadas:
   - magic: Sudden Death (BP 150) = nível + 6 × ML + 37;
   - melee: Fierce Berserk (BP 92) = 2,05 × (skill + 2 × ataque) + nível;
   - dist: Ethereal Spear (BP 25) = 2/3 × (skill + 25) + nível.

   O "nível" é o dano base da TibiaWiki ("Base Damage and Healing"), que cresce mais devagar depois do 500. Dentro de uma
   família, a ordem não depende destas fórmulas. Entre famílias depende, e por isso o paladino ethereal contra holy, as runas
   do monk e as runas do knight são estimativas (ver Limitações).
2. **Alvos por cenário.** São pré-calculados no build: posições de monstros sorteadas com semente fixa, com as áreas reais do
   spells.json e a melhor pontaria possível.

   | Cenário | Posições dos monstros |
   |---|---|
   | boss à distância | 2–3 casas, na mesma linha ou coluna (kiting) |
   | boss colado | knight e monk |
   | caixa | 8 colados |
   | espalhados | 6 a 1–3 casas |
   | party | 10 num bolo 3 casas à frente; colado ao bolo no knight e no monk |

   Mecânicas que o build acrescenta:
   - Cadeias: Forked (6 e 5 saltos de 4 casas), Lightning, Chained Penance, Spiritual Outburst e Executioner's Throw.
   - Os Bursts são um anel que salta as casas coladas.
   - O Death Echo vale ×1,5 (o eco) e pode cair em qualquer casa.
   - O Sweeping Takedown tem uma 2.ª área a 75%.
   - O Divine Grenade é uma bola de raio 2.
3. **Regras de grupo.**
   - **Um elemento por rotação.** Uma rotação só usa os feitiços da vocação de UM elemento: gelo OU terra, fogo OU energia
     OU morte, holy OU físico. A criatura pode resistir a um e não ao outro. Os dois Forked não partilham cooldown (6 s cada,
     sem grupo secundário), mas não se juntam por isso. Runas e feitiços de outros elementos só entram se a criatura levar
     desse elemento pelo menos tanto como do da linha. `mix: true` deixa juntar quando o `eff` diz que leva o mesmo.
   - **Conversão do sorcerer.** Com a stance Master of X, um feitiço de outro elemento lançado logo a seguir a um da linha
     sai em X (notas oficiais de 16/06/2026). O LP impõe "convertidos ≤ feitiços da linha".
   - **Boss.**
     - Os Forked ficam de fora, porque só têm um alvo. O Burst, com kiting a 2–3 casas, faz mais e controla a zona.
     - Waves e beams contam com o jogador alinhado com o boss (há uma nota a dizê-lo).
     - Os DoTs (Envenom, Curse, Ignite, Electrify, Holy Flash, Inflict Wound) não acumulam e o dano espalha-se por minutos:
       vão para "abrir a luta", nunca para a rotação.
   - **Monk.** A Harmony entra no LP (um x por spender e por nível 1–5 de Harmony). O bónus é 7% × 2^(n−1), mais 3% (6% em
     Serene) com a Virtue of Harmony e mais 1/2/3% com o Ascetic. A Virtue of Harmony devolve 1 ponto. O Spiritual Outburst
     repete com 5 pontos. O Serene perde-se em party.
   - **Stances.** Só a partir do nível 20 (promoção). Cada uma é testada com números:
     - knight: Blood Rage +25% skill; em party, Protector;
     - paladin: Sharpshooter +32% distance ou Divine Defiance +6% do distance em ML holy;
     - druid: Elemental Synthesis +10% do ML em gelo e terra; em party como healer, Shared Conservation;
     - sorcerer: Master of X, com o bónus do Lord of Destruction pelo estágio;
     - monk: Virtue of Harmony ou Virtue of Justice +8/16% de fist.

     O ataque automático (arma, ou munição no paladino: as flechas de área apanham um losango de 13 casas) conta na escolha da
     stance, porque o Sharpshooter, a Virtue of Justice e a Blood Rage também o sobem. Aparece em `econ.autoDps`.
4. **Otimização: programação linear.** O simplex em JS (`GrimRot._simplex`, regra de Bland) escolhe as taxas de cada
   feitiço e runa (lançamentos por segundo) que dão mais dano, com estas restrições:
   - grupo de ataque (2 s; 4 s nos de foco);
   - cooldown próprio;
   - grupos secundários: special, ultimate, focus, beams, bursts;
   - Harmony (monk) e conversão (sorcerer);
   - mana: o que se gasta, menos o mana leech, tem de vir das poções, com um máximo por segundo;
   - orçamento em gp/s.

   Resolve-se uma vez por poção (a mais barata por mana dá menos mana por segundo) e por stance, e fica a melhor. O simplex
   foi comparado com o `scipy.optimize.linprog` em 300 problemas aleatórios: diferença máxima de 5×10⁻¹⁴.
5. **Sequência.** É uma simulação de 300 s com as taxas do LP (fichas por feitiço), os cooldowns, a Harmony, a conversão e
   os "bancos" de mana e de gold. Quando os cooldowns não encaixam, entra um enchimento (só feitiços, nunca runas). O teste
   exige 75–106% do ótimo do LP. Hoje dá 83–102% (média 97%).
6. **Economia.**
   - **Runas:** ao preço do NPC.
   - **Mana:** ao preço da poção escolhida. A Mana Potion é a mais barata por mana (0,56 gp) e a UMP a mais cara (0,98 gp),
     mas dá mais mana por segundo. O exhaust de 1 s é o mesmo das poções de vida: o knight pode usar 60% para mana, o
     paladino e o monk 70%, os magos 100%.
   - **Mana leech do Void:** por lançamento, dano × leech × (0,1 × alvos + 0,9), da TibiaWiki. Os magos usam 2 Void
     (capacete + wand/rod) e os outros 1. O tier vai pelo nível: Basic abaixo do 100, Intricate até ao 250 e Powerful
     depois. O leech que sobra não paga runas.
   - **Orçamento `eco`:** 20 000 + 180 × nível gp/h, arredondado a 5k. O site pode passar outro valor (ex.: uma fração do
     lucro/h da hunt).
7. **Imbuements.**
   - **Void:** a mana por segundo que devolve e as poções que poupa (gp/h), contra o custo (taxa 7 500/60 000/250 000 gp a
     cada 20 h, mais os materiais, com `price`).
   - **Epiphany, Precision, Punch e Chop/Slash/Bash:** a % de dano pela mesma fórmula da família.
   - **Strike:** +5% de crítico com +5/15/40% de dano.
   - **Vampirism:** o argumento é que as poções de vida e as de mana partilham o mesmo exhaust.

## Multi-Action Buttons
No jogo (Winter Update 2025), um MAB tem até 3 ações (feitiços ou objetos, como runas) e cada toque dispara a 1.ª que não está em
cooldown. O `buildMab` passa a rotação a MABs:
- os feitiços com cooldown vão à frente, por prioridade, e o enchimento sem cooldown (normalmente uma runa) fica no fim do último MAB;
- se a rotação não tiver enchimento, entra o melhor do kit (para não ficares parado);
- carrega-se nas MABs por ordem (MAB 1, depois MAB 2): uma MAB sem nada pronto não gasta o grupo de ataque;
- os spenders do monk ficam numa tecla à parte, porque o MAB não sabe a Harmony e gastava com menos de 5 pontos;
- no sorcerer, os feitiços da linha vêm antes dos que saem convertidos.

A simulação de carregar nas MABs por ordem dá 86–100% do ótimo do LP (às vezes mais, porque o enchimento gasta acima do orçamento).

## Responde ao nível
- O kit muda com o nível e com o estágio da Wheel (pontos = nível − 50: estágio 1 a 300, 2 a 550, 3 a 1050). Os feitiços da
  Wheel mudam com o estágio:
  - Twin Bursts +20/40/60% e cooldown 22/18/14 s;
  - Executioner's Throw com 2/3/4 saltos;
  - Divine Grenade +16% por estágio;
  - Spiritual Outburst repete a 37,5/50/62,5%.
- As runas exigem nível e ML. O ML estimado do knight e do monk deixa-os fora da SD durante muito tempo.
- As poções têm nível e vocação: Strong a 50, Great a 80, Superior a 100 (sem knights) e Ultimate a 130 (magos).
- O ML e o skill seguem as curvas do `chStats` do index.html, ou vêm da personagem (`ml`, `skill`).

## Limitações
- As fórmulas de escala são de antes de 2020. Para a ordem dentro de uma vocação mono-família isso não conta. No paladino conta,
  e foi verificado sem ir ao jogo: a TibiaWiki não tem o base power do Ethereal Barrage, mas os dados de feitiços do cliente
  15.25 usados pelo Crystal Server (zimbadev/crystalserver) dão 40. Com as escalas do motor, um paladino 500 com Sharpshooter
  faz 40 × distance ≈ 360 e 130 × ML holy ≈ 353: os dois Barrages ficam iguais, como o desenho do jogo sugere. Um teste no
  training dummy (Divine Missile contra Ethereal Spear) continua a ser a confirmação definitiva.
- Fora do modelo: críticos, armadura e mitigação das criaturas, overkill (grupos que encolhem), Beam Mastery,
  augments da Wheel e o mana que a wand/rod gera desde 2026.
- Cooldown do Mystic Repulse: o spells.json diz 8 s e as notas oficiais dizem 12 s. Usam-se 12 s e base power 85 (a
  TibiaWiki ainda tem 72).

## Ligar ao site (o que falta)
1. `<script src="shared/rotacoes.js?v=…">` no index.html, e `dload("rotacoes")` quando a página das hotkeys ou a ficha da
   hunt abrir.
2. Hotkeys da vocação: `GrimRot.plan(D, {voc: C().voc, level: C().level, ml: C().ml, skill: C().skill, scen, budget})`,
   com um seletor de cenário (Boss, Caixa, Espalhados, Party) e outro de gasto (Máximo, Económico). Desenha-se com o mesmo
   HTML das hotkeys de hoje (`toHK`).
3. Ficha da hunt: o mesmo com `eff: G.places[pid].eff`, e `budget` pode vir do lucro/h da linha do TibiaPal.
4. Imbuements: `price: k => buyOf(k, mundo).v` (preços do Market) para o custo do Void.
5. Textos já em PT-PT. O i18n do site traduz o DOM, por isso não é preciso nada à parte.
