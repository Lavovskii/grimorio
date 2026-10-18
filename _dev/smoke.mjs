// Teste rápido do Grimório num browser sem janela (Edge/Chrome via CDP), sem usar o browser da sessão.
// Uso:
//   node C:\xampp\_tools\smoke.mjs [--url http://localhost/grimorio/] [--hash inicio] [--mode modern|original]
//        [--w 1440] [--h 900] [--shot C:\caminho\out.png] [--full] [--eval "expressão JS"] [--wait 2500] [--nochars] [--voc sorcerer]
// Escreve um JSON com: errors (exceções e erros da consola), warnings, eval (resultado de --eval), shot (ficheiro), title,
//   hscroll (a página sai para o lado), hscrollInner (caixas com scroll horizontal interno) e dir (pasta do perfil, já apagada).
// Limpeza: no fim fecha o browser (Browser.close e depois pelo nome da pasta) e apaga a pasta; no arranque o reap.ps1 limpa testes mortos.
import { spawn, execSync } from 'node:child_process';
import { mkdtempSync, readFileSync, writeFileSync, existsSync, rmSync, statfsSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, basename } from 'node:path';

const A = process.argv.slice(2), arg = (k, d) => { const i = A.indexOf('--' + k); return i < 0 ? d : (A[i + 1] && !A[i + 1].startsWith('--') ? A[i + 1] : true); };
const URL0 = arg('url', 'http://localhost/grimorio/'), HASH = arg('hash', 'inicio'), MODE = arg('mode', 'modern');
const W = +arg('w', 1440), H = +arg('h', 900), SHOT = arg('shot', null), FULL = !!arg('full', false), EVAL = arg('eval', null), WAIT = +arg('wait', 2500), NOCH = !!arg('nochars', false), VOC = arg('voc', 'sorcerer');
const EXE = ['C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe', 'C:/Program Files/Google/Chrome/Application/chrome.exe'].find(existsSync);
const sleep = ms => new Promise(r => setTimeout(r, ms));
let out = { url: URL0 + '#' + HASH, mode: MODE, size: [W, H], errors: [], warnings: [], eval: null, shot: null };
// escreve o JSON e sai (o callback garante que o JSON chega todo antes do exit)
const emit = code => new Promise(() => { let k = false; const end = () => { if (!k) { k = true; process.exit(code); } }; try { process.stdout.write(JSON.stringify(out, null, 1) + '\n', end); } catch (e) { end(); } setTimeout(end, 3000); });

// antes de abrir outro browser, limpa testes mortos (pastas sem dono vivo e os browsers delas); nunca toca em testes a correr
try { execSync(`powershell -NoProfile -ExecutionPolicy Bypass -File C:/xampp/_tools/reap.ps1 -Caller ${process.pid}`, { stdio: 'ignore', timeout: 20000, windowsHide: true }); } catch (e) { }

// espaço em disco: com o disco cheio o site também falha (cache do market, logs), por isso não abre o browser
const MINMB = +process.env.SMOKE_MIN_FREE_MB || 1024;
let freeMB = null; try { const s = statfsSync(tmpdir()); freeMB = Math.floor(s.bavail * s.bsize / 1048576); } catch (e) { }
if (freeMB !== null && freeMB < MINMB) { out.errors = [`disco quase cheio (${freeMB} MB livres)`]; await emit(2); }
if (freeMB !== null && freeMB < 2 * MINMB) out.warnings.push('pouco espaço em disco');

const dir = mkdtempSync(join(tmpdir(), 'grim-smoke-')), DIRN = basename(dir);
try { writeFileSync(join(dir, 'owner.pid'), String(process.pid)); } catch (e) { }
out.dir = DIRN;
const br = spawn(EXE, ['--headless=new', '--disable-gpu', '--no-first-run', '--no-default-browser-check', '--disable-extensions', '--disk-cache-size=1', '--disable-component-update', '--no-pings', '--disable-background-networking', '--disable-sync', '--remote-debugging-port=0', `--user-data-dir=${dir}`, `--window-size=${W},${H}`, 'about:blank'], { stdio: 'ignore', windowsHide: true });
br.on('error', () => { });

// No Windows o msedge.exe lançado é só um lançador que sai logo; o browser verdadeiro fica sem pai.
// Por isso: taskkill do PID só enquanto o lançador está vivo (o PID pode ser reaproveitado), e depois fecho pelo nome único da pasta.
const PSKILL = Buffer.from(`Get-CimInstance Win32_Process -Filter "Name='msedge.exe' OR Name='chrome.exe'" | Where-Object { $_.CommandLine -like '*${DIRN}*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }`, 'utf16le').toString('base64');
const killTree = () => {
  if (br.exitCode === null && br.signalCode === null) { try { execSync(`taskkill /PID ${br.pid} /T /F`, { stdio: 'ignore', timeout: 15000, windowsHide: true }); } catch (e) { try { br.kill(); } catch (e2) { } } }
  try { execSync(`powershell -NoProfile -NonInteractive -EncodedCommand ${PSKILL}`, { stdio: 'ignore', timeout: 15000, windowsHide: true }); } catch (e) { }
};
let tidied = false;
const tidy = () => { tidied = true; killTree(); try { rmSync(dir, { recursive: true, force: true, maxRetries: 10, retryDelay: 300 }); } catch (e) { } return !existsSync(dir); };
process.on('exit', () => { if (!tidied) tidy(); });
['SIGINT', 'SIGTERM', 'SIGHUP', 'SIGBREAK'].forEach(sg => { try { process.on(sg, () => process.exit(3)); } catch (e) { } });

let BURL = null, finishing = false, T = null;
// fecha o browser pelo CDP (fecha todos os processos dele), depois o recurso, apaga a pasta e só então escreve o JSON
const done = async code => {
  if (finishing) return; finishing = true; clearTimeout(T);
  try {
    if (BURL) {
      const s = new WebSocket(BURL);
      await new Promise(r => { s.onopen = r; s.onerror = r; setTimeout(r, 1500); });
      if (s.readyState === 1) { s.send(JSON.stringify({ id: 999999, method: 'Browser.close' })); await sleep(1200); }
    }
  } catch (e) { }
  if (!tidy()) out.warnings.push('a pasta do perfil ficou por apagar (o reap.ps1 apaga-a mais tarde)');
  await emit(code);
};
process.on('uncaughtException', e => { out.errors.push('falha do teste: ' + (e && e.message)); done(2); });
process.on('unhandledRejection', e => { out.errors.push('falha do teste: ' + (e && e.message)); done(2); });
T = setTimeout(() => { out.errors.push('timeout geral (60 s)'); done(2); }, 60000);
try {
  let port = null, bpath = null;
  for (let i = 0; i < 150 && !port; i++) { await sleep(100); try { const l = readFileSync(join(dir, 'DevToolsActivePort'), 'utf8').split('\n'); if (l[0].trim()) { port = l[0].trim(); bpath = (l[1] || '').trim(); } } catch (e) { } }
  if (!port) throw new Error('o browser não arrancou');
  if (bpath) BURL = `ws://127.0.0.1:${port}${bpath}`;
  try { const v = await (await fetch(`http://127.0.0.1:${port}/json/version`)).json(); if (v.webSocketDebuggerUrl) BURL = v.webSocketDebuggerUrl; } catch (e) { }
  const list = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json(), page = list.find(t => t.type === 'page');
  const ws = new WebSocket(page.webSocketDebuggerUrl); await new Promise((r, j) => { ws.onopen = r; ws.onerror = j; });
  let id = 0; const wait = {}, on = {};
  ws.onmessage = m => { const d = JSON.parse(m.data); if (d.id && wait[d.id]) { wait[d.id](d); delete wait[d.id]; } else if (d.method && on[d.method]) on[d.method](d.params); };
  const cdp = (method, params = {}) => new Promise(r => { const i = ++id; wait[i] = r; ws.send(JSON.stringify({ id: i, method, params })); });
  const ev = async expr => { const r = await cdp('Runtime.evaluate', { expression: expr, awaitPromise: true, returnByValue: true }); return r.result && r.result.exceptionDetails ? { error: r.result.exceptionDetails.exception && r.result.exceptionDetails.exception.description || r.result.exceptionDetails.text } : r.result && r.result.result ? r.result.result.value : null; };
  on['Runtime.exceptionThrown'] = p => out.errors.push('exceção: ' + ((p.exceptionDetails.exception && p.exceptionDetails.exception.description) || p.exceptionDetails.text).split('\n').slice(0, 3).join(' | '));
  on['Runtime.consoleAPICalled'] = p => { if (p.type === 'error') out.errors.push('console.error: ' + p.args.map(a => a.value || a.description || '').join(' ').slice(0, 300)); };
  on['Log.entryAdded'] = p => { if (p.entry.level === 'error' && !/favicon/.test(p.entry.url || '')) out.errors.push('log: ' + p.entry.text.slice(0, 200) + (p.entry.url ? ' ' + p.entry.url : '')); };
  await cdp('Page.enable'); await cdp('Runtime.enable'); await cdp('Log.enable');
  await cdp('Emulation.setDeviceMetricsOverride', { width: W, height: H, deviceScaleFactor: 1, mobile: W < 768 });
  if (W < 768) await cdp('Emulation.setTouchEmulationEnabled', { enabled: true, maxTouchPoints: 5 });
  const nav = async u => { await cdp('Page.navigate', { url: u }); for (let i = 0; i < 80; i++) { await sleep(100); if (await ev('document.readyState') === 'complete') break; } };
  await nav(URL0);
  const now = Date.now();
  // personagens de teste já "sincronizadas" agora (syncedAt e hs.at numéricos): a app não vai ao TibiaData (personagem nem highscores)
  const mk = (id, name, voc, level, world, ml, skill) => ({ id, tasks: [], name, voc, level, pct: 30, ml, skill, wtype: '', done: {}, charms: {}, imb: {}, owned: {}, target: 0, bonus: '1.5', prey: false, hunt: null, world, syncedAt: now, tib: { voc: 'x', level, guild: null, status: 'Premium Account', others: [], deaths: [], houses: [], former: [], res: 'Thais' }, hs: { at: now, w: world, sk: { v: (voc === 'sorcerer' || voc === 'druid') ? ml : skill, r: 500, k: voc === 'knight' ? 'sword' : undefined }, xp: null } });
  const CH = { sorcerer: mk('t1', 'Teste Sorc', 'sorcerer', 570, 'Bona', 106, 10), knight: mk('t2', 'Teste Knight', 'knight', 812, 'Antica', 12, 121), paladin: mk('t3', 'Teste Pally', 'paladin', 455, 'Secura', 30, 118), druid: mk('t4', 'Teste Druid', 'druid', 300, 'Bona', 85, 10), monk: mk('t5', 'Teste Monk', 'monk', 250, 'Antica', 8, 100) };
  const order = [VOC, ...Object.keys(CH).filter(k => k !== VOC)];
  const STv = NOCH ? null : { v: 4, active: CH[VOC].id, chars: order.map(k => CH[k]), custom: [], ui: { p: HASH, band: null, cat: 'all', qf: 'avail', eq: {} } };
  await ev(`localStorage.clear(); ${STv ? `localStorage.setItem('grimorio-tibia-v4', ${JSON.stringify(JSON.stringify(STv))});` : ''} localStorage.setItem('grimorio-ui', ${JSON.stringify(MODE)}); localStorage.setItem('grimorio-ui-hint','1'); true`);
  out.errors = [];
  await nav(URL0 + '?smoke=' + now + '#' + HASH);
  await sleep(WAIT);
  await ev(`document.getAnimations().forEach(a=>{try{const t=a.effect&&a.effect.getTiming&&a.effect.getTiming(); if(t&&t.iterations!==Infinity) a.finish();}catch(e){}}); true`);
  if (EVAL) { out.eval = await ev(`(async()=>{ ${String(EVAL).includes('return') ? EVAL : 'return (' + EVAL + ')'} })()`); await sleep(600); await ev(`document.getAnimations().forEach(a=>{try{const t=a.effect.getTiming(); if(t.iterations!==Infinity) a.finish();}catch(e){}}); true`); }
  out.title = await ev('document.title');
  // no telemóvel emulado o innerWidth cresce com o conteúdo: compara com a largura pedida
  out.hscroll = await ev('Math.max(document.documentElement.scrollWidth, innerWidth) > ' + W + ' + 1');
  // hscrollInner (até 10): primeiro, se a página sai para o lado, os culpados "pai>filho" (o primeiro elemento que passa da
  // largura com o pai ainda dentro, sem nada a cortá-lo; ignora camadas fixas do fundo); depois as caixas com scroll horizontal
  // próprio, sem contar as que são de propósito (abas, chips, tabelas largas...)
  out.hscrollInner = await ev(`(()=>{ const W=${W}, X='.seg.scroll,.tabs,.chars,.gsp-cats,.eqtabs,.settabs,.sltabs,.hotbar,#hotbar,.scroll-x,.tablewrap', r=[], B=document.body;
    const sel = e => { const c = typeof e.className === 'string' ? e.className.trim().split(/\\s+/).filter(Boolean).slice(0, 2) : []; return e.tagName.toLowerCase() + (e.id ? '#' + e.id : '') + (c.length ? '.' + c.join('.') : ''); };
    if (Math.max(document.documentElement.scrollWidth, innerWidth) > W + 1) for (const e of B.querySelectorAll('*')) { if (r.length >= 10) break;
      const b = e.getBoundingClientRect(); if (!b.width || b.right + scrollX <= W + 1) continue;
      const p = e.parentElement; if (p !== B && p.getBoundingClientRect().right + scrollX > W + 1) continue;
      let skip = getComputedStyle(e).position === 'fixed'; for (let a = p; !skip && a && a !== B; a = a.parentElement) { const s = getComputedStyle(a); skip = s.position === 'fixed' || s.overflowX !== 'visible'; }
      if (!skip) r.push((p !== B ? sel(p) + '>' : '') + sel(e)); }
    for (const e of document.querySelectorAll('*')) { if (r.length >= 10) break; if (e.scrollWidth <= e.clientWidth + 1) continue;
      const o = getComputedStyle(e).overflowX; if ((o === 'auto' || o === 'scroll') && !e.matches(X)) r.push(sel(e)); }
    return r; })()`);
  if (SHOT) { try { const r = await cdp('Page.captureScreenshot', { format: 'png', captureBeyondViewport: FULL }); writeFileSync(SHOT, Buffer.from(r.result.data, 'base64')); out.shot = SHOT; } catch (e) { out.errors.push('não consegui gravar a captura: ' + e.message); } }
  ws.close(); done(out.errors.length ? 1 : 0);
} catch (e) { out.errors.push('falha do teste: ' + e.message); done(2); }
