// Regressões de navegação: salas remotas não determinam a cidade de entrada.
import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
const root=new URL('../',import.meta.url);
const read=p=>fs.readFileSync(new URL(p,root),'utf8');
const d=JSON.parse(read('data/boss-access.json'));
const lloyd=d.b.lloyd.places.map(p=>d.places[p]);
assert(lloyd.some(p=>p.arrive.some(t=>t.includes('Thais'))&&p.arrive.some(t=>t.includes('Energy Portal'))));
assert(!lloyd.some(p=>p.arrive.some(t=>/Sai.*Port Hope/.test(t))));
for(const [key,b] of Object.entries(d.b)){
  for(const g of b.guides){
    const q=JSON.parse(read(`quests/data/quests/${g.slug}.json`));
    assert.equal(q.sections[g.section].title,g.title,`${key}: âncora desatualizada`);
  }
  for(const p of b.places)assert(d.places[p],`${key}: local em falta`);
}
const html=read('index.html');
// O fallback não pode mandar sair de uma cidade nem descer pisos inventados.
const route=html.slice(html.indexOf('function routeHTML('),html.indexOf('/* r2-t5 */ // painel de detalhe'));
const ctx={G:{routes:{}},esc:x=>x,elinkTxt:x=>x};
vm.createContext(ctx);vm.runInContext(route,ctx);
assert.match(ctx.routeHTML(null,32000,32800,14),/Percurso por confirmar/);
ctx.G.routes.real=['Thais','Barco',['Usa o portal'],'Quest'];
assert.match(ctx.routeHTML('real'),/Usa o portal/);
assert(!route.includes('nearCity('));assert(!route.includes('nearPlace('));
// Um spawn de boss junto a outra hunt nunca herda o caminho dessa hunt.
const start=html.indexOf('document.addEventListener("click", async e=>{ const b=e.target.closest("[data-area]");');
assert(start>=0);
const handler=html.slice(start,html.indexOf('function bestArea(',start));
let click,opened;
const button={dataset:{area:'remote'},isConnected:true};
const area={mon:'Lloyd',cl:[32786,32818,13,1,'Sala remota','wrong-hunt']};
const ui={document:{addEventListener:(name,fn)=>{click=fn;}},AREAS:{remote:area},
  location:{hash:'#criatura/lloyd'},bsAccessData:async()=>d,hasKey:(o,k)=>Object.hasOwn(o,k),
  bsAccessHTML:(data,k)=>`acesso:${k}`,openSheet:t=>{opened=t;},esc:t=>t,cap1:t=>t,
  huntRows:()=>{throw new Error('Não pode herdar a hunt vizinha');}};
vm.createContext(ui);vm.runInContext(handler,ui);
await click({target:{closest:()=>button}});
assert.match(opened,/acesso:lloyd/);
opened=null;ui.bsAccessData=async()=>{throw new Error('offline');};
await click({target:{closest:()=>button}});
assert.match(opened,/Não consegui confirmar o acesso/);
console.log(`${Object.keys(d.b).length} bosses: locais e âncoras válidos; portal de Lloyd e fallback verificados`);
