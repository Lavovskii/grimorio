"""Ícones pixel-art originais (12x12) para o menu — maqueta. Gera icons.json {id: svg} e sheet.html."""
import json, sys, os

PAL = {
    'o': '#120C06', 'g': '#E6C06A', 'h': '#FFE9A8', 'd': '#8C6A2E', 's': '#C9CDD6', 'S': '#737A88',
    'r': '#D04A30', 'R': '#8A2A1A', 'b': '#9A6634', 'B': '#5A3A1C', 'u': '#5AA0F0', 'U': '#2A5A9A',
    'G': '#6CC04A', 'D': '#2F6A22', 'w': '#F4F0E6', 'p': '#A070E0', 'P': '#5A3A9A', 'k': '#E8DCC0', 'K': '#A89878',
    'c': '#5FD0D0',
}

I = {
# casa (Início)
'inicio': """
.....oo.....
....orRo....
...orrrRo...
..orrrrrRo..
.orrrrrrrRo.
oooooooooooo
.okkkkkkkKo.
.okoookkkKo.
.okobbokkKo.
.okobboKoKo.
.okobboKKKo.
.oooooooooo.""",
# pergaminho com linhas (Novidades)
'novidades': """
.oooooooooo.
oKkkkkkkkkKo
.okoooookko.
.okkkkkkkko.
.okooookkko.
.okkkkkkkko.
.okoooookko.
.okkkkkkkko.
.okooookkko.
.okkkkkkkko.
oKkkkkkkkkKo
.oooooooooo.""",
# espada (Hunts)
'hunts': """
.........ooo
........oshо
.......oshSo
......oshSo.
.....oshSo..
.o..oshSo...
.ooosshSo...
..oohSSo....
..ogoSo.....
.ogoooo.....
ogo..oo.....
oo..........""",
# caveira com coroa (Bosses)
'bosses': """
..og.og.og..
..oggggggo..
...oooooo...
..okkkkkko..
.okkkkkkkko.
.okooKkookо.
.okooKkookо.
.okkkKKkkko.
..okkooKko..
..okKkKkKo..
...oooooo...
............""",
# lista com visto (Tarefas)
'tarefas': """
.oooooooooo.
.okkkkkkkkKo
.okGokoooKo.
.oGGokkkkKo.
.okkkkkkkKo.
.okGokoooKo.
.oGGokkkkKo.
.okkkkkkkKo.
.okGokoooKo.
.oGGokkkkKo.
.oKKKKKKKKo.
.oooooooooo.""",
# martelo (Build)
'build': """
...oooooo...
..osssssSo..
..osssssSo..
...ooboooo..
.....ob.....
.....ob.....
.....ob.....
.....ob.....
.....ob.....
.....oB.....
.....oB.....
......o.....""",
# runa (Rotação e hotkeys)
'rotacao': """
..oooooooo..
.oUuuuuuuUo.
.ouUuuuuUuo.
.ouuohhouuo.
.ouohuuhouo.
.ouuuhhuuuo.
.ouuhuuhuuo.
.ouohhhhouo.
.ouUuuuuUuo.
.oUuuuuuuUo.
..oooooooo..
............""",
# roda (Wheel)
'wheel': """
....oooo....
..oogddgoo..
.ogd.og.dgo.
.od..og..do.
og.d.og.d.go
oggggooggggo
oggggooggggo
og.d.og.d.go
.od..og..do.
.ogd.og.dgo.
..oogddgoo..
....oooo....""",
# armadura (Equipamento)
'equip': """
.oo......oo.
osSo....oSso
osssooooosso
.ossssssssо.
..osssSsso..
..ossSssso..
..osssSsso..
..ossSssso..
..osssSsso..
..ossssSso..
..oSSSSSSo..
..oooooooo..""",
# estrela (Progresso / Charms)
'prog': """
.....oo.....
.....oho....
....ohgo....
oooooggoooo.
ohhgggggggdo
.oggggggdo..
..oggggdo...
..oggdggdo..
.oggdoodgdo.
.ogdo..odgo.
.odo....odo.
.oo......oo.""",
'charms': """
.....oo.....
....ocpo....
...ocpppo...
..ocpppPpo..
.ocppppPPpo.
ocpppppPPPpo
.opppppPPPo.
..oppppPPo..
...opppPo...
....oppo....
.....oo.....
............""",
# livro de quests (Quests)
'guias': """
..oooooooo..
.obbbbbbbBo.
.obgggggbBo.
.obgoooogBo.
.obgggggbBo.
.obbbbbbbBo.
.obbbgobbBo.
.obbbggbbBo.
.obbbbbbbBo.
.okkkkkkkko.
.oKKKKKKKKo.
..oooooooo..""",
# livro aberto (Wiki)
'wiki': """
............
.ooo....ooo.
okkkoooookko
okookkkkoKko
okkkkkokkKko
okoookookKko
okkkkkokkKko
okoookookKko
okkkkkokkKko
oKKKKKoKKKKo
.oooooooooo.
............""",
'sistemas': """
.....oo.....
..oo.os.oo..
..ossssssо..
...osSSSo...
.ooso..osoo.
ossso..osSSo
oSsso..oSSso
.oosSooSsoo.
...osSSSo...
..osssSSSo..
..oo.oS.oo..
.....oo.....""",
# bolsa (Itens)
'itens': """
....oooo....
...oB..Bo...
...ob..bo...
..oooooooo..
.obbbbbbbBo.
obbgbbbbbbBo
obbbbbbbbbBo
obbbbbbbbbBo
obbbbbbbbbBo
obbbbbbbbBBo
.oBBBBBBBBo.
..oooooooo..""",
# dragão pequeno (Criaturas)
'criaturas': """
..o......o..
.oGo....oGo.
.oGGooooGGo.
..oGGGGGGo..
.oGGoGGoGGo.
.oGGoGGoGGo.
.oGGGGGGGGo.
..oGrrrrGo..
..oGGGGGGo..
...oGooGo...
...oo..oo...
............""",
# raio (Feitiços)
'feiticos': """
.......ooo..
......ohgo..
.....ohgo...
....ohgo....
...ohgooooo.
..ohggggggo.
.oooooohgo..
.....ohgo...
....ohgo....
...ohgo.....
...ogo......
...oo.......""",
# NPC com balão (NPCs)
'npcs': """
.....ooooooo
.....owwwwwo
..oo.owoooo.
.okKoowwwwo.
.okKo.ooooo.
..oo..o.....
.oooo.......
oUuuUo......
oUuuUo......
.oUUo.......
.o..o.......
.oo.oo......""",
# troféu (Coleções)
'colecoes': """
.oooooooooo.
ogohhgggdogo
ogoggggggogo
.oogggggdoo.
...oggggo...
....oggo....
.....oo.....
.....go.....
....oggo....
...oddddo...
...oooooo...
............""",
# saco de moedas (Mais)
'mais': """
............
............
............
.oo..oo..oo.
ohgoohgoohgo
ogdoogdoogdo
.oo..oo..oo.
............
............
............
............
............""",
# ábaco (Calculadoras)
'calc': """
.oooooooooo.
.obbbbbbbBo.
.okkkkkkkko.
.okoookookо.
.okkkkkkkko.
.ogoggogoggo
.okkkkkkkko.
.ogoggogoggo
.okkkkkkkko.
.ogoggogoggo
.oBBBBBBBBo.
.oooooooooo.""",
# escudo (Defesa)
'defesa': """
.oooooooooo.
oSssssssssSo
osgggsggggso
osgsgsgsgsso
osggssssggso
osgssggssgso
.osgssssgso.
.osggggggso.
..osgggsso..
...ossssо...
....oSSo....
.....oo.....""",
# balão de fala (Perguntar)
'ask': """
............
.oooooooooo.
owwwwwwwwwwo
owwoooowwwwo
owwwwwwwwwwo
owwooowwwwwo
owwwwwwwwwwo
.oooowwoooo.
....owwo....
....owo.....
....oo......
............""",
# cabeça (Personagens)
'perso': """
....oooo....
...obbbbo...
..obkkkkbo..
..okokkokо..
..okkkkkkо..
..okkKKkko..
...okkkko...
..ooooooooo.
.oUuuuuuuUo.
oUuuuuuuuuUo
oUuuuuuuuuUo
oooooooooooo""",
# corrente (Fontes)
'fontes': """
............
......oooo..
.....osssSo.
....osooosо.
...ooo..oso.
..osso.oso..
..osooSso...
.oso..oo....
osSo.oo.....
oSoooSo.....
.oSSSo......
..ooo.......""",
}
I['charms'] = I['charms']


def svg(grid):
    rows = [r for r in grid.strip('\n').split('\n')]
    rects = []
    for y, r in enumerate(rows):
        r = r.replace('о', 'o')  # (letras cirílicas escapadas no desenho)
        for x, ch in enumerate(r[:12]):
            if ch in PAL:
                rects.append(f'<rect x="{x}" y="{y}" width="1" height="1" fill="{PAL[ch]}"/>')
    return f'<svg viewBox="0 0 12 12" shape-rendering="crispEdges" aria-hidden="true">{"".join(rects)}</svg>'


out = {k: svg(v) for k, v in I.items()}
d = os.path.dirname(os.path.abspath(__file__))
json.dump(out, open(os.path.join(d, 'icons.json'), 'w'), ensure_ascii=False)
cells = ''.join(f'<figure><div class="i">{s}</div><div class="i2">{s}</div><figcaption>{k}</figcaption></figure>' for k, s in out.items())
open(os.path.join(d, 'sheet.html'), 'w').write(f'''<!doctype html><meta charset=utf8><style>
body{{background:#1A140E;color:#F0E6CE;font:13px Verdana;display:flex;flex-wrap:wrap;gap:14px;padding:16px;margin:0}}
figure{{margin:0;width:110px;text-align:center}} .i svg{{width:24px;height:24px}} .i2 svg{{width:72px;height:72px;background:#2B2318}}
</style>{cells}''')
print(len(out), 'ícones')
