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


class Calibrar(unittest.TestCase):
    def setUp(self):
        import calibrar
        self.c = calibrar

    def test_k_minimos_quadrados(self):
        # 4 hunts × 3 níveis com xph = A × nível^0,3 → k = 0,3 (12 pares)
        pts = [(g, L, a * L ** 0.3) for g, a in (('a', 1e4), ('b', 3e4), ('c', 5e5), ('d', 2e3)) for L in (100, 200, 400)]
        self.assertEqual(self.c.fit_k(pts), (0.3, 12))
        # menos de 10 pares: fica 0,5
        self.assertEqual(self.c.fit_k(pts[:9]), (0.5, 9))
        # níveis iguais não fazem par
        self.assertEqual(self.c.fit_k([('a', 100, 1e4), ('a', 100, 2e4)] * 6)[0], 0.5)
        # fora de 0,1–1: limita
        self.assertEqual(self.c.fit_k([(g, L, L ** 3) for g in 'abcd' for L in (100, 200, 400)])[0], 1)
        self.assertEqual(self.c.fit_k([(g, L, 1e6 / L) for g in 'abcd' for L in (100, 200, 400)])[0], 0.1)

    def test_kz_mediana(self):
        ses = [('a', 10000), ('a', 20000), ('a', 30000), ('b', 5000), ('z', 9000)]
        self.assertEqual(self.c.kz_direto(ses, {'a': 10, 'b': 2.5}), {'a': 2000, 'b': 2000})

    def test_parecidas(self):
        # 6 hunts com kz: as 5 de nível 100–140 parecem-se com 'x' (nível 120); 'longe' (nível 1500, outras criaturas) não
        feat = {'h%d' % i: (100 + 10 * i, 50, 400) for i in range(5)}
        feat.update({'longe': (1500, 400, 30000), 'x': (120, 50, 400)})
        kz = {'h0': 100, 'h1': 200, 'h2': 300, 'h3': 400, 'h4': 500, 'longe': 9000}
        r = self.c.parecidas(feat, kz)
        self.assertEqual(set(r), {'x'})
        self.assertEqual(r['x'][0], 300)
        self.assertEqual(sorted(r['x'][1]), ['h0', 'h1', 'h2', 'h3', 'h4'])

    def test_dz(self):
        G = {'places': {}, 'pm': {}, 'mon': {}}
        ks = {}
        for i in range(10):   # 10 hunts, uma criatura cada, 10 000 mortes; jogadores mortos 1..10
            k = 'm%d' % i
            G['places']['p%d' % i] = {'n': k, 'mons': [k]}
            G['pm']['p%d' % i] = {'h': [[k, 1]]}
            G['mon'][k] = [k, 100, 10, 0, [], {}, [], 0]
            ks[k] = [0, 0, i + 1, 10000]
        G['places']['pouco'] = {'n': 'pouco', 'mons': ['raro']}
        G['pm']['pouco'] = {'h': [['raro', 1]]}
        G['mon']['raro'] = ['raro', 100, 10, 0, [], {}, [], 0]
        ks['raro'] = [0, 0, 500, 999]   # menos de 1000 mortes na semana → 0
        dz, ratio = self.c.dz(G, ks)
        self.assertEqual(dz['p9'], 1)
        self.assertEqual([dz['p%d' % i] for i in range(10)], [-1, -1, -1, 0, 0, 0, 0, 0, 0, 1])
        self.assertEqual(dz['pouco'], 0)
        self.assertNotIn('pouco', ratio)
        # pesada pelo G.pm: 3 × (30 ÷ 1000) e 1 × (0 ÷ 9000) → 90 ÷ 12 000
        G2 = {'places': {'h': {'n': 'h', 'mons': ['x', 'y']}}, 'pm': {'h': {'h': [['x', 3], ['y', 1]]}},
              'mon': {'x': ['x', 1, 1, 0, [], {}, [], 0], 'y': ['y', 1, 1, 0, [], {}, [], 0]}}
        self.assertAlmostEqual(self.c.dz(G2, {'x': [0, 0, 30, 1000], 'y': [0, 0, 0, 9000]})[1]['h'], 90 / 12000)

    def test_relatorio(self):
        linhas = [{'pid': 'a', 'nome': 'Hunt A', 'voc': 'knight', 'n': 5, 'lmed': 200, 'real': 100000, 'est': 130000, 'src': 'tp'},
                  {'pid': 'b', 'nome': 'Hunt B', 'voc': 'druid', 'n': 4, 'lmed': 300, 'real': 100000, 'est': 110000, 'src': 'tp'},
                  {'pid': 'c', 'nome': 'Hunt C', 'voc': 'paladin', 'n': 3, 'lmed': 300, 'real': 100000, 'est': 40000, 'src': 'mx'},
                  {'pid': 'd', 'nome': 'Hunt D', 'voc': 'monk', 'n': 3, 'lmed': 300, 'real': 100000, 'est': None, 'src': None}]
        d = self.c.desvios(linhas)
        self.assertEqual([x['pid'] for x in d], ['c', 'a'])   # mais de 25 %, do maior para o menor
        t = self.c.relatorio_md({'gen': '2026-11-10', 'k': 0.5, 'pares': 3, 'n': {'sessoes': 9, 'mundos': 2}},
                                {'kz_dir': 1, 'kz_par': 2, 'kz_sem': 0, 'dz': {1: 0, 0: 1, -1: 0}, 'mais': [], 'linhas': 4}, d)
        self.assertIn('Hunt A', t)
        self.assertIn('Hunt C', t)
        self.assertNotIn('Hunt B', t)
        self.assertIn('fica 0,5', t)   # menos de 10 pares


if __name__ == '__main__':
    unittest.main()
