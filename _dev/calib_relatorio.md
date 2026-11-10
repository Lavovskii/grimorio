# Calibração dos números das hunts (2026-11-10)

Gerado por `python3 -I _dev/calibrar.py`. Fontes: 90 mundos do TibiaData (semana), 231 sessões solo reais (G.ha e `_dev/sessoes/`) e as linhas atuais do TibiaPal.

## Ajuste ao nível

- k = **0,54** com 63 pares de medições da mesma hunt e vocação em níveis diferentes.

## Mortes por hora

- 49 hunts com mortes/h das sessões reais; 278 herdadas das 5 hunts mais parecidas; 0 sem valor (sem XP média conhecida).

## Perigo (jogadores mortos ÷ criaturas mortas)

- +1: 32 hunts · 0: 198 · −1: 97.

Hunts com +1 (jogadores mortos por 10 000 criaturas mortas):

- Time Travel Dungeon: 35.3
- Dark Grounds (Roshamuul): 33.3
- Issavi — sphinxes à superfície: 10.2
- Fire Sphere (Elemental Spheres): 8.8
- Dragon Lords (Fenrock): 7.5
- Lost Mines (Edron): 5.4
- Gazer Spectres: 4.8
- Dragon Lords (Pits of Inferno): 4.5
- Venore Corym Cave: 4.2
- Water Elemental Cave (Outlaw Camp): 4.1
- Dragonblaze Peaks (Zao): 3.9
- Secret Library: 3.9
- Dragon Lords (Darashia): 3.8
- Wyrms de Liberty Bay: 3.7
- Elder Wyrms (Drefia): 3.7
- Tiquanda Water Elemental Cave: 3.7
- Stonerefiners: 3.5
- Radiant Skyhold: 3.4
- Buried Cathedral: 3.4
- Putrid Mummies: 3.3
- Werebadgers (Grimvale −1): 3.3
- Hot Spot (Gnomebase Alpha): 3.3
- Kazordoon Dragon Lair: 3.3
- Werehyaenas (Darashia): 3.2
- Werehyaenas −1: 3.2
- Frost Dragons (Okolnir): 3.2
- Burster Spectres: 3.2
- Dragões de Yalahar: 2.9
- Grimvale −4: 2.9
- Mother of Scarabs Lair (Ancient Scarabs): 2.9
- Carlin Cults (Forbidden Temple): 2.8
- Old Fortress −2/−3 (Heroes): 2.8

## Estimativa contra sessões reais

77 combinações de hunt e vocação com sessões reais. O `huntEst` conta sem as sessões dessa vocação nessa hunt, no nível mediano delas, com o k novo. Mais de 25 % de diferença: 45.

| Hunt | Vocação | Sessões | Nível | XP/h real | Estimativa | Diferença | Origem |
|---|---|---|---|---|---|---|---|
| Vampire Crypt (Edron) (`edronvamp`) | monk | 1 | 82 | 215 649 | 818 000 | +279 % | est |
| Water Elementals (Port Hope) (`waterel`) | monk | 1 | 88 | 247 837 | 800 000 | +223 % | tp |
| Oramond West (`oramondwest`) | monk | 1 | 181 | 845 696 | 2 250 000 | +166 % | old |
| Book World — Chapter II (`bookworld2`) | knight | 1 | 247 | 1 403 996 | 3 145 000 | +124 % | est |
| Alchemist Quarter (Yalahar) (`alchemist`) | monk | 1 | 94 | 419 562 | 862 000 | +105 % | est |
| Ferumbras' Ascendant — seals (`feruseals`) | paladin | 2 | 874 | 5 443 059 | 11 113 000 | +104 % | mx |
| Warzone 5 (`warzone5`) | sorcerer | 1 | 337 | 2 480 353 | 4 816 000 | +94 % | tp |
| Medusa Tower (`medusa`) | knight | 1 | 265 | 1 568 429 | 3 016 000 | +92 % | est |
| Norcferatu Dungeons (`norcdungeons`) | druid | 1 | 653 | 5 397 901 | 9 977 000 | +85 % | est |
| Issavi — sphinxes à superfície (`issavisurf`) | sorcerer | 2 | 610 | 6 440 567 | 1 038 000 | -84 % | tp |
| Medusa Tower (`medusa`) | druid | 1 | 407 | 1 661 025 | 3 013 000 | +81 % | est |
| Exotic Cave (`exotic`) | knight | 1 | 130 | 1 035 706 | 1 830 000 | +77 % | tp |
| Summer Court (`summercourt`) | druid | 3 | 504 | 4 902 880 | 7 921 000 | +62 % | est |
| Ingol (`ingol`) | druid | 8 | 1227 | 7 695 319 | 12 084 000 | +57 % | hao |
| Falcon Bastion (`falcons`) | sorcerer | 1 | 596 | 4 669 745 | 7 316 000 | +57 % | tp |
| Draken Walls (Zao) (`draken`) | knight | 1 | 247 | 1 974 245 | 3 055 000 | +55 % | est |
| Werecrocodiles (Oskayaat) (`werecrocs`) | paladin | 1 | 455 | 3 175 281 | 4 875 000 | +54 % | tp |
| Azzilon (`azzwalls`) | druid | 2 | 1316 | 8 693 391 | 12 951 000 | +49 % | est |
| Asura Mirror (`asuramirror`) | knight | 3 | 567 | 4 673 943 | 6 930 000 | +48 % | est |
| Gazer Spectres (`gazers`) | druid | 1 | 851 | 8 077 755 | 4 181 000 | -48 % | est |
| Flimsies (Lost Souls) (`flimsy`) | paladin | 1 | 922 | 19 998 205 | 11 340 000 | -43 % | tp |
| Summer Court (`summercourt`) | knight | 1 | 678 | 4 815 086 | 6 888 000 | +43 % | est |
| Azzilon (`azzwalls`) | knight | 3 | 643 | 6 567 097 | 9 370 000 | +43 % | est |
| Carnivoras (`carnivoras`) | druid | 1 | 324 | 1 540 661 | 2 181 000 | +42 % | est |
| Azzilon (`azzwalls`) | paladin | 1 | 842 | 7 349 316 | 10 320 000 | +40 % | tp |
| Upper Roshamuul (`upperrosh`) | paladin | 2 | 816 | 7 630 182 | 10 620 000 | +39 % | tp |
| Warzone 6 (`warzone6`) | knight | 1 | 568 | 2 615 581 | 3 630 000 | +39 % | old |
| Iksupan — Last Stand (`laststand`) | paladin | 1 | 580 | 4 007 621 | 5 500 000 | +37 % | tp |
| Warzone 2 (`warzone2`) | paladin | 1 | 657 | 4 419 571 | 6 032 000 | +36 % | tp |
| Werecrocodiles (Oskayaat) (`werecrocs`) | knight | 1 | 613 | 4 057 771 | 5 488 000 | +35 % | old |
| Warzone 6 (`warzone6`) | paladin | 2 | 676 | 6 671 100 | 4 375 000 | -34 % | tp |
| Warzone 6 (`warzone6`) | druid | 4 | 369 | 2 557 207 | 3 405 000 | +33 % | est |
| Nimmersatt's (Dragões) (`nimmersatt`) | druid | 27 | 756 | 8 324 726 | 11 046 000 | +33 % | est |
| Warzone 1 (`warzone1`) | paladin | 1 | 680 | 7 434 318 | 5 074 000 | -32 % | tp |
| Medusa Tower (`medusa`) | paladin | 1 | 266 | 2 313 280 | 3 042 000 | +32 % | tp |
| Abandoned Sewers (Oramond) (`w_abandoned_sewers`) | paladin | 2 | 554 | 2 998 360 | 3 875 000 | +29 % | tp |
| Summer Court (`summercourt`) | paladin | 1 | 592 | 4 847 830 | 6 250 000 | +29 % | tp |
| Crumbling Caverns (`crumbling`) | druid | 5 | 465 | 3 495 083 | 4 503 000 | +29 % | est |
| Falcon Bastion (`falcons`) | paladin | 2 | 659 | 6 324 230 | 8 120 000 | +28 % | tp |
| Ingol (`ingol`) | paladin | 3 | 1202 | 11 987 334 | 8 630 000 | -28 % | hao |
| Asura Mirror (`asuramirror`) | paladin | 3 | 531 | 5 382 518 | 6 863 000 | +28 % | tp |
| Bashmu (`bashmu`) | paladin | 2 | 903 | 4 068 936 | 5 125 000 | +26 % | tp |
| Bashmu (`bashmu`) | druid | 2 | 513 | 2 972 842 | 3 743 000 | +26 % | est |
| Crypt Warriors (`cryptwarriors`) | sorcerer | 1 | 600 | 5 319 305 | 6 696 000 | +26 % | tp |
| Crypt Warriors (`cryptwarriors`) | druid | 2 | 843 | 7 189 718 | 5 360 000 | -25 % | mx |
