"""Classificação da Exaltation Forge nos itens do G (r21), para os tiers no Equipamento. Pode correr-se várias vezes.

    python -I _dev/add_item_class.py [raiz]

Cada item do G (G.items) com classificação em data/items.json (campo 'up', da TibiaWiki: 1 a 4) fica com 'up' igual;
a classificação diz o tier máximo (data/forge.json, maxTier: classe 1 → tier 1, 2 → 2, 3 → 3, 4 → 10). Os itens sem
classificação ficam sem o campo (não sobem de tier). Procura pelo nome em minúsculas, como o resto do site.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gjson import default_root, load_G, save_G  # noqa: E402


def main(argv):
    root = argv[1] if len(argv) > 1 else default_root()
    with open(os.path.join(root, 'data', 'items.json'), encoding='utf-8') as f:
        info = json.load(f)
    s, G, span = load_G(root)
    put = gone = 0
    for it in G['items']:
        x = info.get(str(it.get('n', '')).lower())
        up = x.get('up') if isinstance(x, dict) else None
        if isinstance(up, int) and 1 <= up <= 4:
            if it.get('up') != up:
                it['up'] = up
                put += 1
        elif 'up' in it:
            del it['up']
            gone += 1
    save_G(root, s, G, span)
    n = sum(1 for it in G['items'] if 'up' in it)
    print(f'itens com classificação: {n} de {len(G["items"])} (+{put} mudados, {gone} retirados)')


if __name__ == '__main__':
    main(sys.argv)
