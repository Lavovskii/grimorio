# Monetização e tráfego do Grimório (r34, 1/11/2026)

Objetivo do dono: os anúncios pagam o servidor, por isso **toda a gente vê anúncios**. Este documento junta o que está
feito, quanto se pode esperar ganhar, se a Google é a melhor escolha e o plano para trazer mais visitas.

## 1. O que está feito (PR da r34)

- Anúncios do Google AdSense em todas as páginas: Grimório (Início, Hunts, item, criatura, rodapé, coluna lateral em
  ecrãs ≥ 1600 px) e Questski (início, fim de cada guia, rodapé). Configuração no topo de `shared/pub.js`.
- **Escolha de cada visitante: anúncios personalizados ou não personalizados.** Não existe a opção "sem anúncios".
- Quem usa bloqueador vê, no lugar de cada anúncio, um pedido curto para abrir uma exceção. Também se pode ligar a
  mensagem de recuperação da Google (`CFG.recuperar`), e escolher no AdSense se ela pode ser fechada.
- Política de privacidade (`privacidade.html`, 8 línguas), `ads.txt`, `robots.txt`, `sitemap.xml`, sem Google Fonts.
- Estatísticas próprias sem cookies (`api/stats.php` → `_dev/estatisticas.py`): visitantes, páginas, de onde vêm,
  língua e aparelho.

### Porque não "sem aceitar cookies não entras"
Na UE, um acesso que só abre depois de a pessoa aceitar cookies (cookie wall) não conta como consentimento válido:
o consentimento tem de ser livre (EDPB, diretrizes 05/2020 sobre consentimento). Uma queixa à CNPD pode dar coima, e
a Google também exige consentimento válido. A alternativa legal dá o mesmo resultado: **todos veem anúncios**; quem não
aceita vê anúncios não personalizados ou "limitados" (o modo da Google para quem não deu consentimento). Rende menos
por visita, mas não perde a visita.

## 2. Passos no AdSense (o dono faz, por esta ordem)

1. Criar a conta em adsense.google.com com o site `tibiagrimoire.me`. A Google revê o site (dias a semanas).
2. Pôr o código `ca-pub-…` em `CFG.client` (`shared/pub.js`) e no `ads.txt` (tirar o `#` da linha).
3. Criar 9 unidades "de display" (uma por espaço: inicio, hunts, item, criatura, rodape, lateral, q-inicio, q-guia,
   q-rodape) e pôr os números em `CFG.slots`. Uma unidade por espaço deixa ver nos relatórios qual rende mais.
4. **Privacidade e mensagens → Regulamentos europeus:** criar a mensagem com "Consentir" e "Gerir opções", nas línguas
   do site. Em **Controlo de marca → Publicação de anúncios**, confirmar que os "anúncios limitados" estão ligados.
   Com isto, `CFG.cmp = "google"` (já é o valor por omissão).
5. Opcional: **Recuperação de bloqueios de anúncios** → criar a mensagem e pôr `CFG.recuperar = true`.
6. Anúncios automáticos: deixar **desligados os anúncios na página** (partem o layout) e, se quiserem um anúncio fixo no
   telemóvel, ligar só o **anúncio âncora no topo**. O fundo do ecrã é a barra de navegação do site.
7. Bloquear categorias sensíveis em **Controlo de marca** (jogo a dinheiro, encontros) e, se aparecerem, anúncios de
   venda de gold, bots ou personagens, que são proibidos pelas regras do Tibia.

## 3. Quanto pode render

Não há números públicos fiáveis do AdSense para sites de jogos por país. Os que existem são de blogs de redes de
anúncios ou de YouTube. Valores de partida para planear, a confirmar com os relatórios do AdSense ao fim de 1 mês:

| Público | RPM da página (€ por 1000 páginas vistas) |
|---|---|
| Portugal, Alemanha, Suécia, Países Baixos, Polónia | 1 – 3 € |
| Brasil | 0,3 – 1 € |
| Mistura realista do Tibia (muito Brasil e Polónia) | ≈ 0,5 – 1,5 € |

Cada anúncio visto vale ≈ 0,0002 – 0,001 €. O RPM da página é a soma dos anúncios que se veem nessa página; por isso
o número e o sítio dos anúncios contam, mas só até começarem a afastar as pessoas.

Cenários com 4 páginas por visitante (medir com `_dev/estatisticas.py`):

| Visitantes/dia | Páginas/mês | Por mês (0,5 €) | Por mês (1,5 €) |
|---|---|---|---|
| 100 | 12 000 | 6 € | 18 € |
| 500 | 60 000 | 30 € | 90 € |
| 2 000 | 240 000 | 120 € | 360 € |

A Google paga a partir de 70 € acumulados. Com menos de ~300 visitantes por dia, os anúncios mal pagam um domínio e a
eletricidade de um PC ligado. **O que mais muda o resultado é o tráfego (secção 5), não a rede de anúncios.**

## 4. A Google é a melhor escolha?

Agora, sim. É a única rede boa sem mínimo de tráfego.

| Rede | Mínimo | Para o Grimório |
|---|---|---|
| **Google AdSense** | nenhum | Começar aqui. |
| Newor Media | ≈ 5 000 utilizadores/mês | Alternativa se o AdSense recusar o site. |
| Nitro (Overwolf, especialista em jogos) | ≈ 100 000 páginas/mês | Candidatar quando lá chegarmos; RPM de jogos melhor. |
| Venatus, Playwire (jogos) | centenas de milhares de páginas/mês | Mais tarde. |
| Ezoic | subiu muito em 2026 (≈ 250 000/mês, a confirmar) | Não serve. |

O código do `pub.js` está separado das páginas: mudar de rede é mudar esse ficheiro, o CSP e o `ads.txt`.

### Riscos para os anúncios
- **O logótipo do Questski** (bruxa de biquíni) pode ser classificado pela Google como conteúdo sugestivo e
  restringir os anúncios dessa parte do site. Vale a pena trocar a imagem antes de pedir a aprovação.
- Páginas que falem de bots, macros ou venda de personagens podem ser recusadas. O site já não tem links externos.

## 5. Plano de tráfego (por impacto)

1. **Páginas com endereço próprio (o maior problema de SEO).** Hoje tudo vive depois do `#` (`/#hunts`,
   `/#item/…`, `/quests/#/quest/…`). A Google não indexa essas páginas em separado: para ela, o site são 3 páginas.
   As centenas de hunts, criaturas, itens e 367 quests deviam ter endereços como `/hunts/edron-vampires`,
   `/quests/the-paradox-tower-quest`, cada um com título, descrição e texto no HTML. Como se faz: um script de
   construção (como o `build_guias.py`) gera uma página HTML estática por quest, hunt, criatura e item, com o conteúdo
   principal e o mesmo layout, e o site continua a abrir por cima. Junta-se tudo ao `sitemap.xml`. É um projeto próprio
   e precisa de desenho antes (é o próximo passo recomendado).
2. **Google Search Console:** verificar o domínio (registo DNS ou ficheiro HTML), enviar o `sitemap.xml` e ver as
   pesquisas que já trazem gente. É grátis e dá os números que o AdSense não dá.
3. **Comunidade Tibia:** o programa de fansites da CipSoft (uma fansite oficial aparece no tibia.com), o Reddit
   r/TibiaMMO, os fóruns e grupos brasileiros e polacos (os maiores públicos), e os Discords de guilds. O que mais se
   partilha: as hunts por nível e vocação, a Wheel e os guias de quests.
4. **Visitas que voltam (tráfego direto):** "Hoje no Tibia" (criatura e boss do dia) e o progresso das personagens já
   dão razões para voltar todos os dias. Falta um `manifest.webmanifest` para instalar o site como app no telemóvel.
   Os ícones já existem em `quests/assets/`.
5. **Medir:** `_dev/estatisticas.py` semanalmente (páginas mais vistas, origens, línguas) e os relatórios do AdSense
   por espaço. Se um espaço quase não rende e tem muita gente, muda-se de sítio; se uma página atrai muita gente,
   ganha um espaço a meio do conteúdo.

## 6. Número e sítio dos anúncios (regras usadas)

- No máximo 3 a 5 anúncios por página vista, e sempre mais conteúdo do que anúncios. As listas longas (Hunts) têm um a
  cada 12 cartões, no máximo 3.
- Um anúncio visível sem fazer scroll nas páginas de entrada (Início, item, criatura, início do Questski), um no fim do
  conteúdo e um no rodapé. A coluna lateral fixa só em ecrãs largos, e nunca na página da Wheel.
- Nada colado a botões ou campos, por causa dos cliques acidentais, que a Google pune.
- Espaço reservado antes de o anúncio chegar, para a página não saltar, e anúncios pedidos só quando ficam perto do ecrã.
- No telemóvel não há anúncio fixo em baixo, porque é onde está o menu.

## Fontes
- EDPB, diretrizes 05/2020 sobre consentimento (cookie walls):
  https://www.scl.org/10902-european-data-protection-board-cookie-walls-do-not-constitute-valid-consent/
- Google, anúncios limitados e não personalizados: https://ppc.land/limited-ads/ ·
  https://support.google.com/adsense/answer/7670013
- Google, CMP certificada na Europa: https://support.google.com/adsense/answer/13554116
- Redes de anúncios para jogos e mínimos: https://blog.nitropay.com/nitro-vs-playwire-vs-venatus-which-ad-network-is-right-for-gaming-publishers/ ·
  https://newormedia.com/blog/?p=1430 · https://www.monetizemore.com/blog/top-ad-networks-gaming-vertical/
- RPM por região (estimativas de mercado): https://weforads.com/blog/ad-revenue-benchmarks-2026/ ·
  https://dynamoi.com/data/youtube-adsense-rpm.html.md
- Endereços com "#" e SEO: https://developer.mozilla.org/de/docs/Glossary/Hash_routing ·
  https://seojuice.io/glossary/seo/programmatic-seo/url-fragment-indexing
