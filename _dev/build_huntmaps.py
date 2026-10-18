"""Regera huntmaps.png (miniaturas dos mapas das hunts) a partir de maps/floor-XX-map.png e atualiza o índice em G.hm.
Cada miniatura = recorte de 96×64 casas (1 px por casa) centrado nas coordenadas da hunt, como as originais.
Grelha: 10 colunas, células 96×64, índices contínuos 0..N-1 (o huntMap() do site assume isto).
Uso: python -I build_huntmaps.py [raiz do site] [--dry]"""
import json, re, sys, os
from PIL import Image

args = [a for a in sys.argv[1:] if not a.startswith('--')]
ROOT = args[0] if args else r'C:\xampp\htdocs\grimorio'
DRY = '--dry' in sys.argv
OX, OY, CW, CH, COLS = 31744, 30976, 96, 64, 10
P = os.path.join(ROOT, 'index.html')
s = open(P, encoding='utf-8').read()
m = re.search(r'(<script[^>]*id="G"[^>]*>)(.*?)(</script>)', s, re.S)
G = json.loads(m.group(2))
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
    out = json.dumps(G, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    open(P, 'w', encoding='utf-8', newline='').write(s[:m.start(2)] + out + s[m.end(2):])
    print('gravado')
