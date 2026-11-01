"""Grimório de Tibia — estatísticas próprias (r34): lê o que o api/stats.php guardou e mostra um resumo.

    python -I _dev/estatisticas.py              # últimos 30 dias
    python -I _dev/estatisticas.py --dias 7
    python -I _dev/estatisticas.py --dias 90 --top 25

Os ficheiros estão em api/cache/stats/stats-AAAA-MM-DD.json (fechados ao público). Cada dia tem: aberturas (entradas
no site), paginas (páginas vistas, contando as mudanças dentro do site), visitantes (únicos do dia), rotas, origens
(domínio de onde a pessoa veio; "(direto)" = escreveu o endereço, favorito ou app), linguas e aparelhos.
Sem cookies: um visitante que volta noutro dia conta outra vez (os visitantes por mês são a soma dos dias, por cima).
"""
import argparse
import datetime as dt
import glob
import json
import os
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--dias', type=int, default=30)
    ap.add_argument('--top', type=int, default=15)
    ap.add_argument('--pasta', default=os.path.join(ROOT, 'api', 'cache', 'stats'))
    a = ap.parse_args()
    desde = (dt.datetime.now(dt.timezone.utc).date() - dt.timedelta(days=a.dias - 1)).isoformat()
    dias = []
    for f in sorted(glob.glob(os.path.join(a.pasta, 'stats-*.json'))):
        d = os.path.basename(f)[6:16]
        if d < desde:
            continue
        try:
            x = json.load(open(f, encoding='utf-8'))
        except (OSError, ValueError):
            print('não li', f, file=sys.stderr)
            continue
        x['visitantes'] = len(x['uv']) if isinstance(x.get('uv'), dict) else x.get('visitantes', 0)
        dias.append(x)
    if not dias:
        print('Sem estatísticas em', a.pasta, '(o api/stats.php ainda não recebeu visitas?)')
        return
    print(f"{'dia':<11} {'visitantes':>10} {'entradas':>9} {'páginas':>8} {'pág./visit.':>11}")
    for x in dias:
        v = x['visitantes'] or 1
        print(f"{x['dia']:<11} {x['visitantes']:>10} {x.get('aberturas', 0):>9} {x.get('paginas', 0):>8} {x.get('paginas', 0) / v:>11.1f}")
    tv = sum(x['visitantes'] for x in dias)
    tp = sum(x.get('paginas', 0) for x in dias)
    print(f"\n{len(dias)} dias · média {tv / len(dias):.0f} visitantes/dia · {tp / len(dias):.0f} páginas/dia · "
          f"≈ {tp / len(dias) * 30:.0f} páginas/mês")

    for campo, nome in (('rotas', 'Páginas mais vistas'), ('origens', 'De onde vêm (entradas)'),
                        ('linguas', 'Línguas'), ('aparelhos', 'Aparelhos')):
        c = Counter()
        for x in dias:
            c.update(x.get(campo) or {})
        tot = sum(c.values()) or 1
        print(f"\n{nome}:")
        for k, n in c.most_common(a.top):
            print(f"  {n:>7}  {n / tot:6.1%}  {k}")


if __name__ == '__main__':
    main()
