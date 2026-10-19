"""Regera huntmaps.png (miniaturas dos mapas das hunts) a partir de maps/floor-XX-map.png e atualiza o índice em G.hm.
Cada miniatura = recorte de 96×64 casas (1 px por casa) centrado nas coordenadas da hunt, como as originais.
Grelha: 10 colunas, células 96×64, índices contínuos 0..N-1 (o huntMap() do site assume isto).
O G lê-se e grava-se com load_G/save_G de gjson.py (formato canónico, uma entrada por linha).
Uso: python -I build_huntmaps.py [raiz do site] [--dry]"""
import sys, os
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.dont_write_bytecode = True  # sem __pycache__ dentro do repositório
from gjson import load_G, save_G, default_root

args = [a for a in sys.argv[1:] if not a.startswith('--')]
ROOT = args[0] if args else default_root()
DRY = '--dry' in sys.argv
OX, OY, CW, CH, COLS = 31744, 30976, 96, 64, 10
s, G, span = load_G(ROOT)
floors = {}


def floor(z):
    if z not in floors:
        f = os.path.join(ROOT, 'maps', 'floor-%02d-map.png' % z)
        floors[z] = Image.open(f).convert('RGBA') if os.path.exists(f) else None
    return floors[z]


cells, skipped = [], []
for pid in sorted(G['hm'], key=lambda k: (G['hm'][k][4] if len(G['hm'][k]) > 4 and G['hm'][k][4] is not None and G['hm'][k][4] >= 0 else 10**6, k)):
    v = G['hm'][pid]
    x, y, z = v[0], v[1], v[2]
    fl = floor(z) if z is not None else None
    if fl is None or x is None:
        skipped.append(pid); v[4] = -1; continue
    cx, cy = x - OX, y - OY
    if not (0 <= cx < fl.width and 0 <= cy < fl.height):
        skipped.append(pid); v[4] = -1; continue
    crop = fl.crop((cx - CW // 2, cy - CH // 2, cx - CW // 2 + CW, cy - CH // 2 + CH))
    bg = Image.new('RGBA', (CW, CH), (0, 0, 0, 255)); bg.alpha_composite(crop)
    cells.append((pid, bg.convert('RGB')))
rows = (len(cells) + COLS - 1) // COLS
sheet = Image.new('RGB', (CW * COLS, CH * max(1, rows)), (0, 0, 0))
for i, (pid, im) in enumerate(cells):
    sheet.paste(im, ((i % COLS) * CW, (i // COLS) * CH))
    v = G['hm'][pid]
    while len(v) < 5: v.append(None)
    v[4] = i
print('miniaturas:', len(cells), '| sem mapa:', len(skipped), skipped[:10], '| folha', sheet.size)
if not DRY:
    sheet.save(os.path.join(ROOT, 'huntmaps.png'), optimize=True)
    save_G(ROOT, s, G, span)
    print('gravado')
