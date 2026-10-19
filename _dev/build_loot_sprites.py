r"""build_loot_sprites.py — desenha no loot.png os itens de data/items.json que o site mostra com o saco genérico.

O itemSpr(nome) usa o ix de G.items (allitems.png) e depois G.lt (loot.png); sem nenhum dos dois mostra o saco (.ph-ic).
Este script procura, entre os supplies que o build_supplies.py junta a data/items.json (SUPPLIES) e o
'enchanted werewolf helmet' (ou os nomes dados na linha de comandos), os que não têm ix >= 0 pelo nome em G.items nem
G.lt, e para cada um:
  - client_outfits.render_item(id) com o 1.º id de items.json[nome].ids que o cliente Tibia instalado tenha (só leitura) e
    fit_cell(..., 32): o objeto recortado ao visível e centrado numa célula de 32x32 com fundo transparente, como as que
    já lá estão (comparado com as células da ultimate/great health potion, arrow e runas: mesma posição);
  - a célula entra a seguir ao maior índice de G.lt (32 colunas; linhas de 32 px novas quando é preciso).
O loot.png continua em modo P com a mesma paleta e a mesma transparência: cada pixel novo fica com a cor opaca mais
próxima da paleta (alfa < 128 = o índice transparente), por isso as células antigas ficam iguais byte a byte (o script
confirma antes de gravar e sai sem gravar nada se não ficarem). G.lt[nome] = índice, gravado com load_G/save_G.
Um item que o cliente não tenha fica sem imagem (é dito no fim); nunca se inventa um desenho.
Uso: python -I build_loot_sprites.py [raiz] [--dry] [nome ...]
  raiz: sem ela, a pasta-mãe de _dev quando o script está em _dev, senão C:\xampp\htdocs\grimorio
  --dry: diz o que faria sem gravar
Idempotente: correr outra vez não muda nada. Depois: muda o ?v= do loot.png no index.html (todos os URLs) e corre
python -I build_search.py <raiz>."""
import json, os, sys, tempfile

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, r'C:\xampp\_tools']  # client_outfits.py só existe em C:\xampp\_tools (lê o cliente instalado)
EXTRA = ['enchanted werewolf helmet']
CELL, COLS = 32, 32


def default_root():
    if os.path.basename(HERE).lower() == '_dev':
        return os.path.dirname(HERE)
    return r'C:\xampp\htdocs\grimorio'


def main(argv):
    dry = '--dry' in argv
    pos = [a for a in argv if not a.startswith('--')]
    root = None
    if pos and os.path.isdir(pos[0]):
        root = pos.pop(0)
    root = os.path.abspath(root or default_root())
    from gjson import load_G, save_G
    from build_supplies import SUPPLIES
    import client_outfits as co
    from PIL import Image

    s, G, span = load_G(root)
    items = json.load(open(os.path.join(root, 'data', 'items.json'), encoding='utf-8'))
    names = [n.lower() for n in (pos or (SUPPLIES + EXTRA))]
    has_ix = {str(it.get('n', '')).lower() for it in G['items'] if isinstance(it.get('ix'), int) and it['ix'] >= 0}
    lt = G['lt']
    todo, skip = [], []
    for n in names:
        if n in has_ix or n in lt:
            continue
        if n not in items:
            skip.append((n, 'não está em data/items.json'))
            continue
        cell = None
        for i in items[n].get('ids') or []:
            img = co.render_item(i)
            cell = co.fit_cell(img, CELL) if img is not None else None
            if cell is not None:
                todo.append((n, i, cell))
                break
        if cell is None:
            skip.append((n, 'o cliente não tem o objeto dos ids %s' % (items[n].get('ids') or [])))
    for n, why in skip:
        print('sem imagem:', n, '-', why)
    if not todo:
        print('loot.png: nada a acrescentar')
        return 0

    path = os.path.join(root, 'loot.png')
    old = Image.open(path)
    old.load()
    assert old.mode == 'P' and old.width == COLS * CELL, f'loot.png inesperado: {old.mode} {old.size}'
    pal = old.getpalette()[:768]
    pal += [0] * (768 - len(pal))
    trns = old.info.get('transparency')
    assert isinstance(trns, (bytes, bytearray)), 'loot.png sem tabela de transparência'
    alpha = [trns[i] if i < len(trns) else 255 for i in range(256)]
    tidx = alpha.index(0)
    opq = [i for i in range(256) if alpha[i] >= 250]
    near = {}

    def nearest(r, g, b):
        k = (r, g, b)
        if k not in near:
            near[k] = min(opq, key=lambda j: 2 * (r - pal[3 * j]) ** 2 + 4 * (g - pal[3 * j + 1]) ** 2 + 3 * (b - pal[3 * j + 2]) ** 2)
        return near[k]

    start = max(lt.values()) + 1
    idx = list(range(start, start + len(todo)))
    rows = (idx[-1] // COLS) + 1
    H = max(old.height, rows * CELL)
    new = Image.new('P', (old.width, H), tidx)
    new.putpalette(pal)
    new.paste(old, (0, 0))
    ocells = (old.height // CELL) * COLS
    for (n, i, cell), k in zip(todo, idx):
        x, y = (k % COLS) * CELL, (k // COLS) * CELL
        if k < ocells:
            assert old.convert('RGBA').crop((x, y, x + CELL, y + CELL)).getchannel('A').getbbox() is None, f'célula {k} já ocupada'
        q = Image.new('P', (CELL, CELL), tidx)
        q.putpalette(pal)
        q.putdata([tidx if a < 128 else nearest(r, g, b) for (r, g, b, a) in cell.getdata()])
        new.paste(q, (x, y))
    # as células antigas ficam iguais (índices da paleta, byte a byte)
    for k in range(ocells):
        if k in idx:
            continue
        x, y = (k % COLS) * CELL, (k // COLS) * CELL
        box = (x, y, x + CELL, y + CELL)
        assert new.crop(box).tobytes() == old.crop(box).tobytes(), f'célula antiga {k} mudou'
    for (n, i, _), k in zip(todo, idx):
        print(f'{"(dry) " if dry else ""}G.lt["{n}"] = {k}  (id {i}; coluna {k % COLS}, linha {k // COLS})')
    if dry:
        return 0
    fd, tmp = tempfile.mkstemp(suffix='.png', dir=root)
    os.close(fd)
    try:
        new.save(tmp, transparency=bytes(alpha), compress_level=9)
        chk = Image.open(tmp)
        chk.load()
        assert (chk.mode == 'P' and chk.size == new.size and chk.tobytes() == new.tobytes() and chk.getpalette()[:768] == pal
                and bytes(chk.info.get('transparency') or b'') == bytes(alpha)), 'loot.png gravado não lê igual'
        for (n, i, _), k in zip(todo, idx):
            lt[n] = k
        save_G(root, s, G, span)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
    print(f'loot.png: {len(todo)} células novas ({old.width}x{old.height} -> {new.width}x{new.height}); G.lt gravado')
    print('Falta: o ?v= do loot.png no index.html e python -I build_search.py', root)
    return 0


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.exit(main(sys.argv[1:]))
