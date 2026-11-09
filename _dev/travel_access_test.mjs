// Regressões: portais remotos, fichas de viagem escondidas e locais omitidos.
import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
const read=p=>fs.readFileSync(new URL('../'+p,import.meta.url),'utf8');
const html=read('index.html'),app=read('quests/js/app.js');
const data=JSON.parse(read('data/hunt-access.json'));
assert(data.h.replica.includes('Replica Dungeon'));
assert(data.h.oldmasonry.includes('Old Masonry'));
assert(data.h.werelions.includes('Lion Sanctum'));
const replica=data.places['Replica Dungeon'];
assert(replica.arrive.some(t=>t.includes('Thais')));
assert(replica.arrive.some(t=>t.includes('Energy Portal')));
for(const ns of Object.values(data.h))for(const n of ns)assert(data.places[n]);
const g=JSON.parse(html.match(/<script[^>]*id="G"[^>]*>([\s\S]*?)<\/script>/)[1]);
const take=(text,a,b)=>{const start=text.indexOf(a);assert(start>=0,a);const end=text.indexOf(b,start);assert(end>start,b);return text.slice(start,end);};
const ctx={G:g,esc:x=>x,qName:x=>x,questReqTag:x=>x,elinkTxt:x=>x,
  mapBtn:()=>'<map-point>',vRoute:k=>`reviewed:${k}`,routeHTML:()=>'<recorded-directions>',
  routeUI:()=>{throw new Error('Não apresentar traçado automático como acesso');}};
vm.createContext(ctx);vm.runInContext(take(html,'function huntRoute(pid){','function routeHTML('),ctx);
assert.match(ctx.huntRoute('replica'),/data-haccess="replica"/);
assert.match(ctx.huntRoute('oldmasonry'),/reviewed:oldmasonry/);
assert(!ctx.huntRoute('oldmasonry').includes('data-rt='));
assert.match(ctx.huntRoute('inexistente'),/por confirmar/);
// Abrir uma hunt carrega o acesso textual ao portal, sem desenhar uma linha fictícia.
ctx.dload=async()=>data;ctx.hasKey=(o,k)=>Object.hasOwn(o,k);
ctx.travelPlaceHTML=p=>p.arrive.join(' ');
vm.runInContext(take(html,'let HACCESS=null;','document.addEventListener("click",e=>{ const b=e.target.closest("[data-hretry]");'),ctx);
const box={dataset:{haccess:'replica'},isConnected:true};
await ctx.hAccessFill(box);assert.match(box.innerHTML,/Energy Portal/);assert.match(box.innerHTML,/Thais/);
ctx.dload=async()=>{throw new Error('offline');};vm.runInContext('HACCESS=null;',ctx);
const failed={dataset:{haccess:'replica'},isConnected:true};
await ctx.hAccessFill(failed);assert.match(failed.innerHTML,/Tentar de novo/);assert(!failed.dataset.loaded);
// As quatro fichas continuam disponíveis, incluindo o passo de chegada e a cidade.
const places=['Replica Dungeon','Old Masonry','Thais','Lion Sanctum'].map(title=>({title,type:title==='Thais'?'cidade':'dungeon'}));
const qctx={placesInStep:()=>places,travelCard:p=>`[${p.title}]`,placeFor:()=>null,
  travelBody:p=>`rota:${p.title}`,esc:x=>x,plainText:x=>x,icon:()=>''};
vm.createContext(qctx);
vm.runInContext(take(app,'  function travelCardsFor(','  function stepHTML('),qctx);
const shown=new Set();const cards=qctx.travelCardsFor({title:'Chegar a Replica Dungeon'},shown);
for(const p of places)assert(cards.includes(`[${p.title}]`));
assert.equal(qctx.travelCardsFor({},shown),'');
const revisit=qctx.travelCardsFor({title:'Voltar a Replica Dungeon'},shown);
assert(revisit.includes('[Replica Dungeon]'));
vm.runInContext(take(app,'  function questArrival(','  function guideTab('),qctx);
qctx.placeFor=n=>places.find(p=>p.title===n)||null;
const arrival=qctx.questArrival({slug:'test',start:{label:'Replica Dungeon'},sections:[{steps:[{title:'Chegar ao portal'}]}]});
assert.match(arrival,/rota:Replica Dungeon/);assert.match(arrival,/guia\/0-0/);
assert(!arrival.includes('perto de'));
assert(!qctx.questArrival({slug:'mentioned-only',sections:[{steps:[{title:'Falar com o NPC'}]}]}).includes('rota:Replica Dungeon'));
qctx.placesInStep=()=>[];
assert.match(qctx.questArrival({slug:'sem-dados'}),/Ainda sem ficha de viagem/);
console.log(`${Object.keys(data.h).length} hunts: ligações válidas; portais, chegada, 4 locais e repetição verificados`);
