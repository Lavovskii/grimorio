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
const take=(text,a,b)=>{const start=text.indexOf(a);assert(start>=0,a);const end=text.indexOf(b,start);assert(end>start,b);return text.slice(start,end);};
// Fichas (Task 3): o caminho em troços do data/caminhos.json, o mapa do troço e os pré-requisitos.
const CAM=JSON.parse(read('data/caminhos.json'));
const cx={esc:x=>String(x),hasKey:(o,k)=>Object.hasOwn(o,k),qmd:x=>x,travelTextHTML:x=>x,
  elink:(k,n)=>`<npc:${n}>`,npcSpr:()=>'',mapBtn:()=>'<map>',guiaHref:s=>'quests/#/quest/'+s,
  qDone:(c,id)=>!!c.done[id],C:()=>null,dload:async()=>CAM,GrimFicha:{DIFF:[]}};
vm.createContext(cx);
vm.runInContext(take(html,'/* fichas:caminho */','/* fichas:caminho:fim */'),cx);
// caminho com passos, NPC e pontos
const h1=cx.camHTML(CAM.h.targuna_inf,'h:targuna_inf',CAM.places);
assert.match(cx.camHTML(CAM.h.upperspike,'h:upperspike',CAM.places),/Chegar a Upper Spike/);
assert.match(h1,/revisto/);assert.match(h1,/<npc:Emiliana>/);assert.match(h1,/<kbd>hi<\/kbd>/);assert.match(h1,/110 gp/);
assert.match(h1,/data-cammap="h:targuna_inf:\d+"/);assert.match(h1,/data-camstep="h:targuna_inf:\d+:\d+"/);
// troço por referência: os passos e a chegada vêm de CAM.places (o local fica uma só vez no ficheiro)
const up=cx.camHTML(CAM.h.upperspike,'h:upperspike',CAM.places);
assert(up.includes(CAM.places['Upper Spike'].arrive[0].s));assert.match(up,/data-cammap="h:upperspike:0"/);
// hunt por documentar: diz que falta e não desenha mapa de troço
const none=Object.entries(CAM.h).find(([,c])=>c.st==='none');
const h2=cx.camHTML(none[1],'h:'+none[0],CAM.places);
assert.match(h2,/por documentar/);assert(!h2.includes('data-cammap='));
// zona aproximada nunca é «entrada»
const aprox=Object.entries(CAM.h).find(([,c])=>c.pa===1&&c.pos);
const ha=cx.camHTML(aprox[1],'h:'+aprox[0],CAM.places);
assert.match(ha,/zona aproximada/);
assert(!/entrada/i.test(ha.replace(/<ol[\s\S]*?<\/ol>/g,'')));
// pré-requisitos
const pre=[{k:'quest',n:'Grimvale Quest',id:'grim',slug:'grimvale-quest',sec:10,note:'até entregares a ocarina'},
  {k:'level',n:250,rec:true},{k:'premium'},{k:'item',n:'Pá'},{k:'text',s:'Grupo recomendado'}];
const p0=cx.preHTML(pre,null);
assert.match(p0,/quests\/#\/quest\/grimvale-quest\/guia\/sec-10/);assert.match(p0,/até entregares a ocarina/);assert(!/por fazer|feita/.test(p0));
const p1=cx.preHTML(pre,{level:100,done:{}});assert.match(p1,/por fazer/);assert.match(p1,/nível 250/i);
assert.match(cx.preHTML(pre,{level:300,done:{grim:true}}),/feita/);
assert.match(cx.preHTML([],null),/Sem pré-requisitos/);
// enchimento e falha de rede
const box={dataset:{cam:'h:targuna_inf'},isConnected:true,parentElement:{querySelector:()=>null}};
await cx.camFill(box);assert.match(box.innerHTML,/Emiliana/);
const pbox={innerHTML:''},box2={dataset:{cam:'b:abyssador'},isConnected:true,parentElement:{querySelector:q=>q==='[data-campre]'?pbox:null}};
await cx.camFill(box2);assert.match(box2.innerHTML,/Nos guias das quests/);assert.match(pbox.innerHTML,/fx-pre/);
const box3={dataset:{cam:'h:nao-existe'},isConnected:true,parentElement:{querySelector:()=>null}};
await cx.camFill(box3);assert.match(box3.innerHTML,/por documentar/);
cx.dload=async()=>{throw new Error('offline');};vm.runInContext('CAMP=null;',cx);
const bad={dataset:{cam:'h:targuna_inf'},isConnected:true,parentElement:{querySelector:()=>null}};
await cx.camFill(bad);assert.match(bad.innerHTML,/Tentar de novo/);assert(!bad.dataset.loaded);
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
console.log(`${Object.keys(data.h).length} hunts: ligações válidas; caminho em troços, pré-requisitos, falha de rede, chegada, 4 locais e repetição verificados`);
