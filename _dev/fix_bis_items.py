"""Correções de itens para os sets (r10), da TibiaWiki (22/10/2026). Pode correr-se várias vezes.

    python -I _dev/fix_bis_items.py [raiz]

- Flamingo Amulet of Nature / Valor / Precision / Destruction (as entradas do TibiaPal, sem atributos): passam a ter os
  da versão encantada (Enchanted Flamingo Amulet of …, nível 270, descarrega ao fim de 3 h e recarrega-se no Cledwyn),
  como o Enchanted Swan Amulet of Balance. Sem atributos, nunca entravam nos sets.
- Stellar Moonsilver Sceptre e Channeler: a TibiaWiki tem 'damagerange = 6' (ficha incompleta) e o site copiou 6–6;
  ficam com o dano da versão normal (os outros atributos já são iguais).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gjson import default_root, load_G, save_G  # noqa: E402

FLAMINGO = {
    900000: {'sk': {'ml': 3, 'ml_ice': 1}, 'ab': {'physical': 3, 'fire': 11}, 'arm': 3},                        # Nature (druid)
    900005: {'sk': {'sword': 4, 'axe': 4, 'club': 4, 'shield': 1}, 'ab': {'physical': 7, 'fire': 12}, 'arm': 4},  # Valor (knight)
    900019: {'sk': {'dist': 4, 'ml_holy': 1}, 'ab': {'physical': 5, 'fire': 14}, 'arm': 4},                      # Precision (paladin)
    900025: {'sk': {'ml': 3, 'ml_energy': 1}, 'ab': {'physical': 3, 'fire': 11}, 'arm': 3},                      # Destruction (sorcerer)
}
STELLAR = {900004: ['ice', 103, 127], 900028: ['death', 103, 133]}


def main(argv):
    root = argv[0] if argv else default_root()
    s, G, span = load_G(root)
    n = 0
    for it in G['items']:
        f = FLAMINGO.get(it['id'])
        if f:
            for k in ('ns', 'pe'):
                it.pop(k, None)
            it.update(f)
            it['dur'] = 10800
            n += 1
        w = STELLAR.get(it['id'])
        if w and it.get('wd') != w:
            it['wd'] = w
            n += 1
    save_G(root, s, G, span)
    print('itens atualizados:', n)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
