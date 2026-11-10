"""Testes da calibração (parte D do plano das fichas): tibiadata.py, import_sessoes.py e calibrar.py.
Uso: python3 -I _dev/calib_test.py   (dados pequenos inventados aqui; a fixture é uma resposta real do TibiaData, cortada)"""
import json
import sys
import unittest
from pathlib import Path

DEV = Path(__file__).resolve().parent
sys.path.insert(0, str(DEV))
import tibiadata  # noqa: E402

FX = json.loads((DEV / 'fixtures' / 'ks_antica.json').read_text(encoding='utf-8'))


class TibiaData(unittest.TestCase):
    KEYS = ['dragon lord', 'dragon', 'frost dragon', 'cyclops', 'cyclops drone', 'thief', 'medusa', 'hideous fungus',
            'sabretooth', 'ogre shaman', 'hero', 'werewolf', 'wolf', 'son of verminor', 'abyssador', 'ahau']

    def test_agrega_soma_por_criatura(self):
        a = tibiadata.agrega([FX, FX], self.KEYS)
        dl = next(e for e in FX['killstatistics']['entries'] if e['race'] == 'dragon lords')
        self.assertEqual(a['dragon lord'], [2 * dl['last_day_players_killed'], 2 * dl['last_day_killed'],
                                            2 * dl['last_week_players_killed'], 2 * dl['last_week_killed']])
        self.assertNotIn('(elemental forces)', a)
        self.assertTrue(all(not k.startswith('(') for k in a))
        self.assertTrue(all(k == k.lower() for k in a))

    def test_plurais_e_bosses(self):
        a = tibiadata.agrega([FX], self.KEYS)
        for k in ['dragon', 'frost dragon', 'cyclops', 'cyclops drone', 'thief', 'medusa', 'hideous fungus', 'sabretooth',
                  'ogre shaman', 'hero', 'werewolf', 'wolf', 'son of verminor', 'abyssador', 'ahau']:
            self.assertIn(k, a, k)
        self.assertNotIn('dragon lords', a)


# G pequeno inventado: rat dá 5 XP (avgXp = 5), troll 20; 4000 mortes/h → 20 000 XP/h no máximo em 'a'
GT = {'places': {'a': {'n': 'A', 'mons': ['Rat', 'Boss Rat']}, 'b': {'n': 'B', 'mons': ['Troll']}},
      'pm': {'a': {'h': [['rat', 2], ['boss rat', 1]]}, 'b': {'h': []}},
      'mon': {'rat': ['Rat', 20, 5, 0, [], {}, [], 0], 'boss rat': ['Boss Rat', 900, 500, 0, [], {}, [], 1],
              'troll': ['Troll', 50, 20, 0, [], {}, [], 0]}}


def ses(**kw):
    s = {'pid': 'a', 'voc': 'knight', 'lvl': 100, 'xph': 10000, 'loh': 5000, 'min': 60, 'data': '2026-11-01', 'src': 'manual'}
    s.update(kw)
    return s


class Sessoes(unittest.TestCase):
    def setUp(self):
        import import_sessoes
        self.m = import_sessoes

    def test_avg_mon(self):   # = avgMon do index.html: G.pm.h ∩ mons, sem bosses, pesada pela quantidade; sem h, mons com peso 1
        self.assertEqual(self.m.avg_mon(GT, 'a'), [5.0, 20.0])
        self.assertEqual(self.m.avg_mon(GT, 'b'), [20.0, 50.0])
        self.assertIsNone(self.m.avg_mon(GT, 'zz'))

    def test_valida(self):
        v = lambda s: self.m.valida(s, GT)
        self.assertIsNone(v(ses()))
        for campo in ('name', 'char', 'personagem'):
            self.assertIsNotNone(v(ses(**{campo: 'X'})), campo)
        self.assertIsNotNone(v(ses(pid='nada')))
        self.assertIsNotNone(v(ses(min=14)))
        self.assertIsNone(v(ses(min=15)))
        self.assertIsNotNone(v(ses(xph=20005)))     # 4001 mortes/h
        self.assertIsNone(v(ses(xph=20000)))
        self.assertIsNotNone(v(ses(voc='mage')))
        self.assertIsNotNone(v(ses(src='outro')))
        self.assertIsNone(v(ses(loh=None)))

    def test_agrega_como_G_ha(self):
        rows = [ses(lvl=100, xph=10000, loh=1000), ses(lvl=120, xph=12000, loh=None), ses(lvl=150, xph=14000, loh=3000),
                ses(pid='b', voc='druid', lvl=300, xph=50000, loh=-2000)]
        self.assertEqual(self.m.agrega(rows), {'a': {'v': {'knight': [3, 100, 120, 12000, 2000]}},
                                               'b': {'v': {'druid': [1, 300, 300, 50000, -2000]}}})

    def test_csv(self):
        import tempfile, os
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, 's.csv')
            with open(p, 'w', encoding='utf-8') as f:
                f.write('pid,voc,lvl,xph,loh,min,data,src\na,knight,100,10000,,60,2026-11-01,manual\n')
            self.assertEqual(self.m.le(p), [ses(loh=None)])


if __name__ == '__main__':
    unittest.main()
