"""Liga o Grimório aos guias do Questski (quests/): escreve data/guias.json.

  g    lista curta dos guias para a pesquisa e as listas do Grimório:
       [slug, nome, nível mínimo, nível recomendado, premium (0/1), categoria, região, passos]
  q2s  id da quest no Grimório (G.quests) → slug do guia
  n2s  nome normalizado (sem 'The', sem 'Quest', sem pontuação) → slug, para ligar pelo nome
       (data/quests.json do Grimório, quests citadas nas hunts e nas criaturas)

O Questski lê o mesmo ficheiro (../data/guias.json) para sincronizar as quests concluídas com a personagem ativa.
Correr depois de atualizar os guias (python _questski/tools/build.py) ou as quests do Grimório.

Uso: python build_guias.py
"""
import json, os, re, sys, unicodedata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gjson

ROOT = gjson.default_root()


def key(s):
    s = unicodedata.normalize('NFD', str(s or '')).encode('ascii', 'ignore').decode().lower()
    s = s.replace('_', ' ')
    s = re.sub(r'\s*\(quest\)\s*$', '', s)
    s = re.sub(r'^the\s+', '', s)
    s = re.sub(r'\s+quest(\s+line)?$', '', s)
    s = re.sub(r"[^a-z0-9]+", ' ', s).strip()
    return s


def main():
    idx = json.load(open(os.path.join(ROOT, 'quests', 'data', 'index.json'), encoding='utf-8'))
    qs = idx['quests']
    g, n2s = [], {}
    for q in qs:
        g.append([q['slug'], q['name'], q.get('lvl') or 0, q.get('rec') or 0, 1 if q.get('premium') else 0, q.get('category') or '', q.get('region') or '', q.get('steps') or 0])
        for nm in [q['name']] + list(q.get('aka') or []):
            k = key(nm)
            if k and k not in n2s: n2s[k] = q['slug']
    G = [x for x in gjson.load_G(ROOT) if isinstance(x, dict)][0]
    q2s, miss = {}, []
    for q in G['quests']:
        s = n2s.get(key(q['n'])) or n2s.get(key(q.get('w') or ''))
        if s: q2s[q['id']] = s
        else: miss.append(q['n'])
    out = {'v': 1, 'gen': idx.get('generated', ''), 'g': g, 'q2s': q2s, 'n2s': n2s}
    p = os.path.join(ROOT, 'data', 'guias.json')
    with open(p, 'w', encoding='utf-8', newline='\n') as f: json.dump(out, f, ensure_ascii=False, separators=(',', ':'))
    print(f'{len(g)} guias · {len(q2s)} de {len(G["quests"])} quests do Grimório com guia · {os.path.getsize(p)//1024} KB')
    print('sem guia (nível acima de 100 ou com outro nome):', ', '.join(miss))


if __name__ == '__main__':
    main()
