"""Aplica as correções das hunts (C:\\xampp\\_work\\hunts\\fix-*.json, geradas pela verificação online) ao G embebido no index.html.
- duplicate/remove: só apaga hunts importadas da wiki (pid w_*) — as outras ficam no registo para rever à mão.
- fix/ok: criaturas, bosses, cidade, acesso (PT-PT), nota, estrelas, equipa, quest, premium, coordenadas, níveis das linhas
  preenchidas (f) ou da wiki, XP/lucro medidos que faltavam, e eficácia dos elementos recalculada (média de 100 − resistência).
- criaturas que não existam em G.mon são criadas a partir de data/creatures.json (sem sprite).
- r2: tira a quest quando a verificação diz que não é precisa; tira as linhas da TibiaWiki (w) das vocações que não entram;
  linhas f ao lado de uma linha real saem; o nível vai para a linha mais baixa e marca v:1 nas linhas f (confiança high/medium;
  linhas v não mudam); as listas de equipa perdem as vocações a que a verificação deu nível solo. KEEP = exceções.
  O registo vai SEMPRE para C:\\xampp\\_work\\hunts\\apply.log (faz cópia antes de testar numa pasta à parte).
Depois correm fix_hunt_mons.py (criaturas e quantidades) e build_huntmaps.py (miniaturas).
Uso: python -I apply_hunt_fixes.py [raiz] [--dry]"""
import json, re, sys, os, glob, unicodedata, datetime

args = [a for a in sys.argv[1:] if not a.startswith('--')]
ROOT = args[0] if args else r'C:\xampp\htdocs\grimorio'
DRY = '--dry' in sys.argv
P = os.path.join(ROOT, 'index.html')
s = open(P, encoding='utf-8').read()
m = re.search(r'(<script[^>]*id="G"[^>]*>)(.*?)(</script>)', s, re.S)
G = json.loads(m.group(2))
CR = json.load(open(os.path.join(ROOT, 'data', 'creatures.json'), encoding='utf-8'))
EL = ['physical', 'fire', 'ice', 'earth', 'energy', 'holy', 'death']
VOCS = ['knight', 'paladin', 'sorcerer', 'druid', 'monk']
log = []
fold = lambda t: unicodedata.normalize('NFD', str(t or '')).encode('ascii', 'ignore').decode().lower().strip()
# r2-t1: linhas que ficam apesar de a verificação não dar nível a essa vocação (lvl None = sem medição, não "não entra")
KEEP = {('w_podzilla', 'knight')}

E = []
for f in sorted(glob.glob(r'C:\xampp\_work\hunts\fix-*.json')):
    try:
        E += json.load(open(f, encoding='utf-8'))
    except Exception as e:
        log.append(f'ERRO a ler {f}: {e}')

QID = {}
for q in G['quests']:
    for nm in (q.get('n'), (q.get('w') or '').replace('_', ' ')):
        if nm:
            QID[fold(nm)] = q['id']; QID[fold(re.sub(r'\s+quest$', '', nm, flags=re.I))] = q['id']


def mon_key(name):
    k = fold(name)
    if k in G['mon']:
        return k
    for kk, v in G['mon'].items():
        if fold(v[0]) == k:
            return kk
    # r2-t1: 'Monk (Creature)' / 'Sabretooth (Creature)' são as criaturas 'monk' / 'sabretooth' (sem duplicados em G.mon)
    k2 = re.sub(r'\s*\(creature\)$', '', k)
    if k2 != k and k2 in G['mon']:
        return k2
    c = CR.get(k) or next((v for kk, v in CR.items() if fold(v.get('n')) == k), None)
    if not c:
        return None
    el = c.get('el') or {}
    res = {e: 100 - el[e] for e in el if e in EL + ['drown'] and isinstance(el[e], (int, float)) and el[e] != 100}
    G['mon'][k] = [c.get('n') or name, c.get('hp') or 0, c.get('xp') or 0, -1, [], res, [], 1 if c.get('boss') else 0]
    cls = c.get('cls')
    if cls and cls in (G.get('mcn') or []):
        G['mc'][k] = G['mcn'].index(cls)
    log.append(f'criatura nova em G.mon: {k}')
    return k


def eff(keys):
    ks = [k for k in keys if k in G['mon']]
    if not ks:
        return None
    out, mn = {}, {}
    for e in EL:
        vals = [100 - (G['mon'][k][5].get(e, 0)) for k in ks]
        out[e] = round(sum(vals) / len(vals)); mn[e] = min(vals)
    out['min'] = mn
    return out


def drop_place(pid, why):
    G['places'].pop(pid, None); G['hm'].pop(pid, None); G['pm'].pop(pid, None)
    for v in G['hunts']:
        G['hunts'][v] = [r for r in G['hunts'][v] if r.get('c') != pid]
    log.append(f'apagada {pid}: {why}')


MERGE = []
VERD = {x.get('pid'): (x.get('verdict'), x.get('dup_of')) for x in E}
stats = {'fix': 0, 'apagadas': 0, 'revisar': 0, 'niveis': 0, 'xp': 0, 'coords': 0}
for e in E:
    pid, vd = e.get('pid'), e.get('verdict')
    p = G['places'].get(pid)
    if not p:
        log.append(f'{pid}: já não existe'); continue
    if vd in ('duplicate', 'remove'):
        tgt = e.get('dup_of')
        if pid.startswith('w_') and (vd == 'remove' or (tgt and tgt in G['places'])):
            if vd == 'duplicate':
                MERGE.append((tgt, e))
            drop_place(pid, f"{vd}{' de ' + tgt if tgt else ''} — {e.get('problems', '')[:120]}"); stats['apagadas'] += 1
        elif vd == 'duplicate' and tgt and tgt in G['places'] and VERD.get(tgt, ('', ''))[1] != pid:
            # entrada do TibiaPal que é o mesmo sítio que outra: as linhas medidas passam para a que fica, depois apaga-se
            moved = 0
            for v in G['hunts']:
                for r in G['hunts'][v]:
                    if r.get('c') == pid:
                        r['c'] = tgt; moved += 1
            MERGE.append((tgt, e))
            drop_place(pid, f"duplicado de {tgt}; {moved} linhas medidas passaram para {tgt}"); stats['apagadas'] += 1
        else:
            log.append(f'mantida {pid} ({vd} {tgt or ""}): {e.get("problems", "")[:200]}'); stats['revisar'] += 1
        continue
    stats['fix'] += 1
    keys = [k for k in (mon_key(n) for n in (e.get('mons') or [])) if k]
    if keys:
        p['mons'] = [G['mon'][k][0] for k in keys]
        ef = eff(keys)
        if ef: p['eff'] = ef
    if e.get('boss'): p['boss'] = e['boss']
    if pid.startswith('w_') and e.get('name'): p['n'] = e['name']
    for src, dst in (('city', 'city'), ('access', 'acc'), ('note', 'note')):
        if e.get(src): p[dst] = e[src]
    for k in ('xs', 'ls'):
        if isinstance(e.get(k), int): p[k] = e[k]
    if e.get('team'): p['team'] = True
    elif e.get('confidence') == 'high' and p.get('team') is True: p.pop('team', None)
    elif e.get('team') is False and e.get('confidence') in ('high', 'medium') and isinstance(p.get('team'), list):
        # r2-t1: sai da lista "só em equipa" a vocação a que a verificação deu nível solo (ex.: cathedral sorcerer)
        keep = [v for v in p['team'] if not isinstance((e.get('lvl') or {}).get(v), int)]
        if keep != p['team']:
            log.append(f"{pid}: equipa {p['team']} -> {keep or 'sem equipa'}")
            if keep: p['team'] = keep
            else: p.pop('team', None)
    if e.get('premium') is not None: p['prem'] = bool(e['premium'])
    if e.get('quest'):
        qid = QID.get(fold(e['quest'])) or QID.get(fold(re.sub(r'\s+quest$', '', e['quest'], flags=re.I)))
        if qid: p['q'] = qid
        p['qn'] = e['quest']
    elif vd in ('fix', 'ok') and e.get('confidence') in ('high', 'medium') and re.search(r'quest', fold(e.get('problems'))) and not e.get('quest'):
        # r2-t1: a verificação diz que a quest não é precisa (quest vazia) — tira a que estava
        if p.get('q') or p.get('qn'): log.append(f"{pid}: quest tirada ({p.get('q')} / {p.get('qn')})")
        p['q'] = None; p.pop('qn', None)
    p['unc'] = e.get('confidence') == 'low'
    xyz = e.get('xyz')
    if isinstance(xyz, list) and len(xyz) == 3 and all(isinstance(v, int) for v in xyz):
        old = G['hm'].get(pid)
        G['hm'][pid] = [xyz[0], xyz[1], xyz[2], 'e' if e.get('confidence') == 'high' else 'a', old[4] if old and len(old) > 4 else -1]
        stats['coords'] += 1
    lvl = e.get('lvl') or {}
    xp = e.get('xp') or {}
    solo = any(isinstance(x, int) for x in lvl.values())  # r2-t1: há vocações com nível solo (as outras não entram / não são solo)
    hi = e.get('confidence') in ('high', 'medium')
    for v in VOCS:
        rows = [r for r in G['hunts'].get(v, []) if r.get('c') == pid]
        L = lvl.get(v)
        low = min(rows, key=lambda r: r.get('l') or 0) if rows else None
        for r in list(rows):
            if (pid, v) in KEEP:
                pass
            elif L is None and r.get('f') and lvl:
                G['hunts'][v].remove(r); log.append(f'{pid}: tirada a linha preenchida de {v} (não é solo para essa vocação)'); continue
            elif L is None and solo and not e.get('team') and (r.get('w') or pid.startswith('w_')):
                # r2-t1: linha da TibiaWiki (w) de uma vocação que não entra (ex.: Earth Sphere só para druids)
                G['hunts'][v].remove(r); log.append(f'{pid}: tirada a linha da TibiaWiki de {v} (essa vocação não entra / não é solo)'); continue
            # r2-t1: o nível da verificação é o de entrada — vai para a linha mais baixa (as variantes mais altas ficam);
            # não mexe em linhas v (nível já confirmado) nem muda linhas f com confiança 'low'
            if isinstance(L, int) and (r.get('f') or pid.startswith('w_')) and r.get('l') != L and not r.get('v') \
                    and (r is low or (r.get('l') or 0) < L) and (hi or not r.get('f')):
                r['l'] = L; stats['niveis'] += 1
                if r.get('f') and hi: r['v'] = 1
            mx = xp.get(v)
            if isinstance(mx, dict) and r.get('xp') is None and mx.get('xp'):
                r['xp'] = float(mx['xp']); r['lo'] = float(mx.get('lo') or 0)
                if 'tibiapal' in fold(mx.get('src')): r.pop('f', None)
                stats['xp'] += 1

# duplicados apagados: os dados bons passam para a entrada que fica, só onde lhe faltam (a verificação dela ganha)
for tgt, e in MERGE:
    t = G['places'].get(tgt)
    if not t:
        continue
    keys = [k for k in (mon_key(n) for n in (e.get('mons') or [])) if k]
    if keys and not t.get('mons'):
        t['mons'] = [G['mon'][k][0] for k in keys]
        ef = eff(keys)
        if ef: t['eff'] = ef
        log.append(f'{tgt}: recebeu as criaturas do duplicado {e["pid"]}')
    if e.get('boss') and not t.get('boss'): t['boss'] = e['boss']
    for src, dst in (('access', 'acc'), ('note', 'note'), ('city', 'city')):
        if e.get(src) and not t.get(dst): t[dst] = e[src]
    for k in ('xs', 'ls'):
        if isinstance(e.get(k), int) and not t.get(k): t[k] = e[k]
    xyz = e.get('xyz')
    if tgt not in G['hm'] and isinstance(xyz, list) and len(xyz) == 3:
        G['hm'][tgt] = [xyz[0], xyz[1], xyz[2], 'a', -1]
        log.append(f'{tgt}: recebeu as coordenadas do duplicado {e["pid"]}')

# r2-t1: linha preenchida (f) ao lado de uma linha real (sem f) da mesma hunt e vocação: fica só a real
for v in G['hunts']:
    real = {r.get('c') for r in G['hunts'][v] if r.get('c') and not r.get('f')}
    keep = []
    for r in G['hunts'][v]:
        if r.get('f') and r.get('c') in real and (r['c'], v) not in KEEP:
            log.append(f"{r['c']}: tirada a linha preenchida de {v} {r.get('l')} (há linha real)"); continue
        keep.append(r)
    G['hunts'][v] = keep

log.append('\nRESUMO ' + json.dumps(stats, ensure_ascii=False))
open(r'C:\xampp\_work\hunts\apply.log', 'w', encoding='utf-8').write('\n'.join(log))
print(json.dumps(stats, ensure_ascii=False), '| entradas', len(E), '| registo: C:\\xampp\\_work\\hunts\\apply.log')
if not DRY:
    out = json.dumps(G, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    open(P, 'w', encoding='utf-8', newline='').write(s[:m.start(2)] + out + s[m.end(2):])
    print('gravado', P)
