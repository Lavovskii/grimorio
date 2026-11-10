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


if __name__ == '__main__':
    unittest.main()
