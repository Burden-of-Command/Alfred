const DATA_URL = "../game/game.json";
const $ = s => document.querySelector(s);
const $$ = s => [...document.querySelectorAll(s)];
const POS = {
  devon:[10,62],somerset:[28,49],dorset:[31,74],hampshire:[51,76],wiltshire:[46,52],
  berkshire:[61,35],kent:[82,68],thames_valley:[75,20],london:[89,39],mercia:[55,11]
};
const LETTERS={guthrum:"G",sea_kings:"S",hastein:"H",thames_army:"T"};
const INTENTS={raid:"RAID",seek_base:"SEEK CAMP",draw_fyrd:"DRAW FYRD",join:"JOIN"};
let data,spaces,state,mapMode;

const shuffle=a=>{a=[...a];for(let i=a.length-1;i;i--){const j=Math.floor(Math.random()*(i+1));[a[i],a[j]]=[a[j],a[i]]}return a};
const clamp=(n,a=0,b=7)=>Math.max(a,Math.min(b,n));
const name=id=>spaces[id]?.name||id;
const wessex=()=>data.spaces.filter(s=>s.kind==="wessex").map(s=>s.id);

async function init(){
  data=await fetch(DATA_URL).then(r=>r.json()); spaces=Object.fromEntries(data.spaces.map(s=>[s.id,s]));
  $("#scenarioSelect").innerHTML=data.scenarios.map(s=>`<option value="${s.id}">${s.name} (${s.years}) · difficulty ${s.difficulty}</option>`).join("");
  $("#startButton").onclick=startGame;$("#restartButton").onclick=()=>location.reload();$("#rulesButton").onclick=showRules;
}

async function startGame(){
  const scenario=data.scenarios.find(s=>s.id===$("#scenarioSelect").value);
  const priorities=shuffle(data.priorities).slice(0,2);
  const priorityId=await choose("Royal Priority","What kind of king will Alfred strive to become?",priorities.map(p=>({value:p.id,label:`${p.name} — ${p.resolve}`})));
  const deck=shuffle(data.commands);
  state={scenario,round:0,phase:"start",guided:$("#guidedToggle").checked,tracks:{...scenario.tracks,service:0},
    readiness:{...scenario.readiness},burhs:new Set(scenario.burhs),camps:new Set(),hosts:{},alfred:scenario.royal_seat,
    households:2,field:new Set(),deck,discard:[],hand:[deck.pop(),deck.pop(),deck.pop()],crisis:null,
    priority:data.priorities.find(p=>p.id===priorityId),priorityUsed:false,orders:[],wins:0,negotiated:false,
    log:[],gameOver:false,roundFlags:{},blocked:new Set()};
  for(const [id,[space,strength]] of Object.entries(scenario.armies))state.hosts[id]={space,strength,oath:false};
  const level=$("#difficultySelect").value;
  if(level==="chronicle")state.tracks.obligation=clamp(state.tracks.obligation+1);
  if(level==="ordeal"){state.tracks.wealth=Math.max(0,state.tracks.wealth-1);strongestHost().strength=clamp(strongestHost().strength+1,0,6)}
  $("#setupScreen").classList.add("hidden");$("#gameScreen").classList.remove("hidden");$("#restartButton").classList.remove("hidden");
  log(`<strong>${scenario.name}</strong> begins. Royal Priority: <strong>${state.priority.name}</strong>.`);
  beginRound();
}

async function beginRound(){
  if(state.gameOver)return;
  state.round++;state.orders=[];state.roundFlags={mustered:new Set(),raided:new Set(),built:new Set(),won:false};
  state.phase="crisis";const group=state.scenario.groups[state.round-1];
  state.crisis=shuffle(data.crises.filter(c=>c.group===group))[0];
  if(!state.hosts[state.crisis.army])state.hosts[state.crisis.army]={space:data.armies[state.crisis.army].entry,strength:2,oath:false};
  log(`<strong>Round ${state.round}:</strong> ${state.crisis.name}.`);
  await arrival(state.crisis);if(checkLoss())return;state.phase="command";render();
}

async function arrival(c){
  const h=state.hosts[c.army];
  if(c.id==="E01")deplete("berkshire"); if(c.id==="E02")h.strength=clamp(h.strength+1,0,6);
  if(c.id==="E03"&&state.field.size)state.tracks.service=clamp(state.tracks.service+1,0,3);
  if(c.id==="E04")track("legitimacy",-1); if(c.id==="E05"&&!defended("dorset"))h.space="dorset";
  if(c.id==="E06"){if(h.oath)h.oath=false;else h.strength=clamp(h.strength+1,0,6)}
  if(c.id==="E07")h.space=stepToward(h.space,"hampshire"); if(c.id==="E09")recover(["wiltshire","somerset"].find(x=>state.readiness[x]<2));
  if(c.id==="E11")h.strength=clamp(h.strength+1,0,6); if(c.id==="E12"&&!state.burhs.has("london"))track("wealth",-1);
  if(c.id==="E13"){h.strength=clamp(h.strength+1,0,6);const t=state.hosts.thames_army;if(t)t.strength=clamp(t.strength+1,0,6)}
  if(c.id==="E14")h.space="kent"; if(c.id==="E16")track("obligation",-1);
  render();
}

function render(){renderScenario();renderTracks();renderMap();renderCrisis();renderHand();renderActions();renderGuide()}
function renderScenario(){
  const s=state.scenario;$("#scenarioKicker").textContent=`Round ${state.round} of ${s.rounds} · ${s.years}`;
  $("#scenarioName").textContent=s.name;$("#mandate").innerHTML=`<strong>${s.mandate.name}:</strong> ${s.mandate.text}`;
  $("#objective").textContent=`Structured objective: ${objectiveText(s.objective)}`;
  $("#priorityCard").innerHTML=`<strong>${state.priority.name}${state.priorityUsed?" · USED":""}</strong><br>${state.priority.resolve}<br><small>${state.priority.legacy}</small>`;
  $("#phaseBadge").textContent=state.phase;
}
function objectiveText(o){return Object.entries(o).map(([k,v])=>`${k.replaceAll("_"," ")} ${v}`).join(" · ")}
function renderTracks(){
  const ready=wessex().filter(r=>state.readiness[r]===2).length;
  $("#tracks").innerHTML=[["legitimacy",state.tracks.legitimacy],["obligation",state.tracks.obligation],["wealth",state.tracks.wealth],["service",state.tracks.service],["reform",state.tracks.reform],["ready regions",ready]].map(([k,v])=>`<div class="track"><strong>${v}</strong><span>${k}</span></div>`).join("");
}
function renderMap(){
  const pairs=[];for(const s of data.spaces)for(const n of s.adjacent)if(s.id<n)pairs.push([s.id,n]);
  const routes=pairs.map(([a,b])=>{const [x,y]=POS[a],[x2,y2]=POS[b],dx=x2-x,dy=y2-y,w=Math.hypot(dx,dy),ang=Math.atan2(dy,dx)*180/Math.PI;const river=data.river_connections.some(p=>p.includes(a)&&p.includes(b));return `<div class="route ${river?"river":""}" style="left:${x}%;top:${y}%;width:${w}%;transform:rotate(${ang}deg)"></div>`}).join("");
  const nodes=data.spaces.map(s=>{const [x,y]=POS[s.id],hosts=Object.entries(state.hosts).filter(([,h])=>h.space===s.id&&h.strength>0);
    const readiness=["exhausted","depleted","ready"][state.readiness[s.id]??1];const pieces=[];
    if(state.alfred===s.id){pieces.push(`<span class="piece house">A</span>`);for(let i=0;i<state.households;i++)pieces.push(`<span class="piece house">H</span>`)}
    for(const r of state.field)if(state.alfred===s.id)pieces.push(`<span class="piece fyrd">${name(r)[0]}</span>`);
    hosts.forEach(([id,h])=>pieces.push(`<span class="piece host">${LETTERS[id]}${h.strength}</span>`));
    if(state.camps.has(s.id))pieces.push(`<span class="piece camp">C</span>`);if(state.burhs.has(s.id))pieces.push(`<span class="piece burh">B</span>`);
    return `<button class="space ${state.alfred===s.id?"alfred":""} ${mapMode?.allowed.includes(s.id)?"selectable":""}" data-space="${s.id}" style="left:${x}%;top:${y}%"><h4>${s.name}</h4><div class="badges"><span class="badge ${readiness}">${readiness[0].toUpperCase()}</span></div><div class="pieces">${pieces.join("")}</div></button>`}).join("");
  $("#map").innerHTML=routes+nodes;$$(".space").forEach(b=>b.onclick=()=>mapClick(b.dataset.space));$("#mapPrompt").textContent=mapMode?.prompt||"";
}
function renderCrisis(){const c=state.crisis,h=data.armies[c.army];$("#crisisCard").innerHTML=`<div class="crisis-card"><p class="eyebrow">${c.id} · Group ${c.group}</p><h3>${c.name}</h3><p><strong>Arrival:</strong> ${c.arrival}</p><p><strong>Design:</strong> ${c.design}</p><p><strong>${h.doctrine}:</strong> ${h.text}</p><div class="intent">${h.name}: ${INTENTS[c.intent]}</div></div>`}
function renderHand(){
  $("#deckCount").textContent=`${state.deck.length} cards`;
  $("#commandHand").innerHTML=state.hand.map(c=>`<article class="command-card"><p class="eyebrow">${c.id} · ${c.tag}</p><h4>${c.name}</h4><button class="card-side" data-id="${c.id}" data-side="command"><strong>COMMAND</strong><br>${c.command}</button><button class="card-side kingdom" data-id="${c.id}" data-side="kingdom"><strong>KINGDOM</strong><br>${c.kingdom}</button><button class="replace" data-replace="${c.id}">Replace</button></article>`).join("");
  $$(".card-side").forEach(b=>b.onclick=()=>useCard(b.dataset.id,b.dataset.side));$$(".replace").forEach(b=>b.onclick=()=>replaceCard(b.dataset.replace));
}
function renderActions(){
  const box=$("#actionButtons");box.innerHTML="";
  if(state.gameOver)return;
  if(state.phase==="command"){$("#actionTitle").textContent="Hold Council";$("#actionText").textContent="Choose one half of one card, or replace one card first.";return}
  if(state.phase==="orders"){
    $("#actionTitle").textContent=`Issue Orders (${state.orders.length}/2)`;$("#actionText").textContent="Choose two different orders.";
    const opts=[["Muster","Raise local and adjacent Ready fyrds.",muster],["March","Move Alfred's force one connection.",march],["Confront","Choose a battle purpose and fight.",confront],["Fortify","Spend 2 Wealth and activate a Burh.",fortify],["Negotiate","Pay 1 Wealth and seek terms.",negotiate],["Steward","Return fyrds and recover one region.",steward]];
    for(const [n,t,fn] of opts){const blocked=n==="Muster"&&state.roundFlags.noMuster;const d=document.createElement("div");d.className="order-option";d.innerHTML=`<button ${blocked||state.orders.includes(n.toLowerCase())||state.orders.length>=2?"disabled":""}>${n}</button><p>${t}</p>`;d.querySelector("button").onclick=fn;box.append(d)}
    if(state.orders.length===2){const b=document.createElement("button");b.className="primary resolve";b.textContent="Resolve Danish Design";b.onclick=enemyDesign;box.append(b)}
  }else{$("#actionTitle").textContent="Resolving the round";$("#actionText").textContent="The Danish Host and seasonal obligations act."}
}
function renderGuide(){
  if(!state.guided){$("#guide").classList.add("hidden");return}$("#guide").classList.remove("hidden");
  const m={command:"Use one card half. Kingdom effects sustain the realm; Command effects answer the immediate war.",orders:"Choose two different orders. The visible Danish Intent resolves afterward.",enemy:"The named Host follows its printed purpose, then Service, Harvest, and recovery resolve."};
  $("#guide").innerHTML=`<strong>${state.phase.toUpperCase()}.</strong> ${m[state.phase]||"Read the crisis and prepare."}`;
}

async function useCard(id,side){
  if(state.phase!=="command")return;const c=state.hand.find(x=>x.id===id);
  if(side==="kingdom"){
    if(id==="C01"){await recoverChoice();track("obligation",1)}
    if(id==="C02"&&state.households<2&&state.tracks.wealth>=2){track("wealth",-2);state.households++}
    if(id==="C03"&&state.tracks.wealth>=1){const sites=["berkshire","london"].filter(r=>!state.burhs.has(r));if(sites.length){const r=await chooseSpace("Fortified Bridge","Activate which Burh?",sites);track("wealth",-1);track("reform",1);state.burhs.add(r)}}
    if(id==="C04"){track("obligation",1);state.roundFlags.noMuster=true}
    if(id==="C05"&&state.readiness[state.alfred]===1)track("legitimacy",1)
    if(id==="C06"){if(state.tracks.legitimacy<2)state.tracks.legitimacy=2;state.readiness.somerset=Math.min(state.readiness.somerset,1)}
    if(id==="C08"){track("wealth",2);track("obligation",-1)}
    if(id==="C09"){track("obligation",2);track("wealth",-1)}
    if(id==="C10"&&!hostIdsAt("mercia").length){track("reform",1);track("legitimacy",1)}
    if(id==="C12"&&Object.values(state.hosts).some(h=>h.strength<=2)&&state.tracks.wealth){track("wealth",-1);track("reform",1);track("legitimacy",1)}
    if(id==="C13"&&state.tracks.wealth){track("wealth",-1);track("reform",1);await recoverChoice()}
    if(id==="C14"){track("reform",1);track(state.tracks.legitimacy<state.tracks.obligation?"legitimacy":"obligation",1)}
    if(id==="C15"&&!hostIdsAt("london").length&&state.tracks.wealth>=2){track("wealth",-2);track("reform",2);state.burhs.add("london")}
    if(id==="C16"&&state.tracks.wealth){track("wealth",-1);track("legitimacy",1);track("reform",1)}
    if(!state.priorityUsed&&state.priority.id==="P04"){track("obligation",1);state.priorityUsed=true}
  }
  else{if(["C02","C05","C06","C13"].includes(id)){const dest=await chooseSpace("Command movement","Move Alfred to an adjacent region.",spaces[state.alfred].adjacent);state.alfred=dest}if(["C01","C08"].includes(id))track("obligation",-1);if(id==="C09"){await recoverChoice();await recoverChoice()}if(id==="C14")track("obligation",1)}
  discardCard(c);state.phase="orders";log(`Used <strong>${c.name}</strong> for ${side.toUpperCase()}.`);render();
}
function replaceCard(id){if(state.phase!=="command"||state.roundFlags.replaced)return;const c=state.hand.find(x=>x.id===id);discardCard(c,false);state.roundFlags.replaced=true;log(`Replaced ${c.name}.`);render()}
function discardCard(c,used=true){state.hand=state.hand.filter(x=>x.id!==c.id);state.discard.push(c);drawCard();if(used)state.roundFlags.card=true}
function drawCard(){if(!state.deck.length){state.deck=shuffle(state.discard);state.discard=[];track(state.tracks.obligation>state.tracks.wealth?"obligation":"wealth",-1);log("The Command deck reshuffles; repeated command consumes the kingdom.")}if(state.deck.length)state.hand.push(state.deck.pop())}

async function muster(){
  const eligible=[state.alfred,...spaces[state.alfred].adjacent].filter((r,i,a)=>a.indexOf(r)===i&&state.readiness[r]===2&&!state.field.has(r));
  if(!eligible.length)return notice("Muster","No local or adjacent region is Ready.");
  const picks=await chooseMany("Call the Fyrd","Choose up to three Ready regions.",eligible.map(r=>({value:r,label:name(r)})),3);
  if(!picks.length)return;for(const r of picks){state.field.add(r);state.readiness[r]=1;state.roundFlags.mustered.add(r)}state.tracks.service=Math.max(1,state.tracks.service);addOrder("muster");log(`The fyrd answers from ${picks.map(name).join(", ")}.`)
}
function march(){mapMode={type:"march",allowed:spaces[state.alfred].adjacent,prompt:"Choose Alfred's destination."};renderMap()}
async function confront(){
  const hosts=hostIdsAt(state.alfred);if(!hosts.length)return notice("Confront","No Danish Host shares Alfred's region.");
  const id=hosts.length===1?hosts[0]:await choose("Confront","Choose a Host.",hosts.map(x=>({value:x,label:data.armies[x].name})));
  const purpose=await choose("Battle purpose","What must this battle accomplish?",[{value:"delay",label:"Delay: +1, but a win does not reduce Strength"},{value:"drive",label:"Drive Off: standard result"},{value:"force",label:"Force Decision: +2, risky; requires 3 forces",disabled:forceCount()<3},{value:"blockade",label:"Blockade: pay 1 Wealth; no roll",disabled:!state.burhs.has(state.alfred)&&!state.camps.has(state.alfred)}]);
  if(purpose==="blockade"){track("wealth",-1);state.blocked.add(id);log(`${data.armies[id].name} is blockaded.`);addOrder("confront");return}
  await battle(id,purpose);addOrder("confront");
}
async function battle(id,purpose,clash=false){
  const h=state.hosts[id];let saxon=forceCount()+roll()+((state.burhs.has(state.alfred))?1:0)+(purpose==="delay"?1:purpose==="force"?2:0),danish=h.strength+roll()+(state.camps.has(h.space)?1:0);
  if(!state.priorityUsed&&state.priority.id==="P07"&&await yesNo(state.priority.name,state.priority.resolve)){saxon+=1;state.priorityUsed=true}
  let margin=saxon-danish;if(!state.priorityUsed&&["P02","P08"].includes(state.priority.id)){const use=await yesNo(state.priority.name,`${state.priority.resolve} Use it now?`);if(use){margin+=2;state.priorityUsed=true}}
  log(`${data.armies[id].name}: West Saxon ${saxon} vs Danish ${danish}${margin>=0?" · held":" · defeated"}.`);
  if(margin>=3){if(purpose!=="delay")h.strength=Math.max(0,h.strength-2);state.camps.delete(h.space);track("legitimacy",1);state.wins++;state.roundFlags.won=true}
  else if(margin>=1){if(purpose!=="delay")h.strength=Math.max(0,h.strength-1);state.wins++;state.roundFlags.won=true}
  else if(margin===0){if(state.tracks.wealth)track("wealth",-1);else state.tracks.service=clamp(state.tracks.service+1,0,3)}
  else if(margin<=-3){track("legitimacy",-1);const first=[...state.field][0];if(first){state.field.delete(first);state.readiness[first]=0}else state.households=Math.max(0,state.households-1)}
  else{if(state.field.size)state.field.delete([...state.field][0]);else track("legitimacy",-1)}
  render();
}
async function fortify(){
  const eligible=data.spaces.filter(s=>s.burh&&!state.burhs.has(s.id)&&state.readiness[s.id]===2).map(s=>s.id);
  if(state.tracks.wealth<2||!eligible.length)return notice("Fortify","You need 2 Wealth and an eligible Ready Burh site.");
  const r=await chooseSpace("Fortify","Choose the Burh site.",eligible);let cost=2;
  if(!state.priorityUsed&&state.priority.id==="P03"&&await yesNo(state.priority.name,state.priority.resolve)){cost=1;state.priorityUsed=true}else state.readiness[r]=1;
  track("wealth",-cost);track("reform",1);state.burhs.add(r);state.roundFlags.built.add(r);addOrder("fortify");log(`${name(r)} is fortified.`)
}
async function negotiate(){
  if(state.tracks.wealth<1)return notice("Negotiate","You need 1 Wealth.");
  const near=Object.keys(state.hosts).filter(id=>state.hosts[id].strength>0&&(state.hosts[id].space===state.alfred||spaces[state.alfred].adjacent.includes(state.hosts[id].space)));
  if(!near.length)return notice("Negotiate","No Host is in or adjacent to Alfred's region.");
  const id=near.length===1?near[0]:await choose("Negotiate","Choose a Host.",near.map(x=>({value:x,label:data.armies[x].name})));track("wealth",-1);
  let total=roll()+(forceCount()>=state.hosts[id].strength?1:0)+(state.tracks.legitimacy>=5?1:0)+(state.hosts[id].strength<=2?1:0);
  if(!state.priorityUsed&&state.priority.id==="P05"&&await yesNo(state.priority.name,state.priority.resolve)){total+=2;state.priorityUsed=true}
  if(total>=4){state.negotiated=true;const effects=total>=6?2:1;for(let i=0;i<effects;i++){const effect=await choose("Terms",`Choose term ${i+1} of ${effects}.`,[{value:"retreat",label:"Host retreats to its entry"},{value:"camp",label:"Remove its fortified camp"},{value:"legitimacy",label:"Gain 1 Legitimacy"},{value:"strength",label:"Reduce Strength by 1"},{value:"oath",label:"Place an Oath"}]);if(effect==="retreat")state.hosts[id].space=data.armies[id].entry;if(effect==="camp")state.camps.delete(state.hosts[id].space);if(effect==="legitimacy")track("legitimacy",1);if(effect==="strength")state.hosts[id].strength--;if(effect==="oath")state.hosts[id].oath=true}log(`Terms are agreed with ${data.armies[id].name}.`)}
  else{state.hosts[id].strength=clamp(state.hosts[id].strength+1,0,6);log("The Host bargains from strength.")}
  addOrder("negotiate");
}
async function steward(){
  if(state.field.size&&await yesNo("Steward","Return all fyrds with Alfred to their home reserves?")){state.field.clear();state.tracks.service=0;track("obligation",1)}
  await recoverChoice();if(!state.priorityUsed&&state.priority.id==="P06"&&await yesNo(state.priority.name,state.priority.resolve)){await recoverChoice();state.priorityUsed=true}addOrder("steward")
}
async function recoverChoice(){const e=eligibleRecovery();if(!e.length)return notice("Recovery","No region is eligible.");const r=await chooseSpace("Recovery","Recover one region by one step.",e);recover(r);if(state.readiness[r]===2)track("wealth",1)}
function eligibleRecovery(){return Object.keys(state.readiness).filter(r=>state.readiness[r]<2&&!state.field.has(r)&&!hostIdsAt(r).length&&!state.camps.has(r)&&!state.roundFlags.raided.has(r)&&!state.roundFlags.mustered.has(r)&&!state.roundFlags.built.has(r))}
function recover(r){if(r)state.readiness[r]=Math.min(2,state.readiness[r]+1)}
function deplete(r){if(state.readiness[r]>0)state.readiness[r]--}
function addOrder(n){if(!state.orders.includes(n))state.orders.push(n);mapMode=null;render()}
function mapClick(id){if(!mapMode?.allowed.includes(id))return;if(mapMode.type==="march"){state.alfred=id;addOrder("march");log(`Alfred marches to ${name(id)}.`)}}

async function enemyDesign(){
  state.phase="enemy";render();const c=state.crisis,h=state.hosts[c.army];
  if(h.oath){h.oath=false;log(`${data.armies[c.army].name} is held by its Oath.`)}
  else if(state.blocked.has(c.army)){state.blocked.delete(c.army);log(`${data.armies[c.army].name} remains blockaded.`)}
  else if(h.space===state.alfred)await battle(c.army,"drive",true);
  else if(c.intent==="join"){const others=Object.entries(state.hosts).filter(([id,x])=>id!==c.army&&x.strength>0);if(others.length){const target=others.sort((a,b)=>b[1].strength-a[1].strength)[0][1].space;h.space=stepToward(h.space,target);if(h.space===target)h.strength=clamp(h.strength+1,0,6)}}
  else{const target=targetFor(c.intent,h.space);h.space=stepToward(h.space,target);if(!defended(h.space)&&(c.intent==="raid"||c.intent==="seek_base"))await raid(h.space,c.intent==="seek_base")}
  await season();if(checkLoss())return;if(state.round>=state.scenario.rounds)return endGame();beginRound();
}
function targetFor(intent,from){
  let candidates;if(intent==="seek_base")candidates=data.spaces.filter(s=>(s.burh&&!state.burhs.has(s.id))||s.id===state.scenario.royal_seat).map(s=>s.id);
  else candidates=wessex().filter(r=>state.readiness[r]===2);if(!candidates?.length)candidates=wessex().filter(r=>state.readiness[r]>0);return nearest(from,candidates);
}
function nearest(from,targets){return [...targets].sort((a,b)=>distance(from,a)-distance(from,b)||a.localeCompare(b))[0]||from}
function distance(a,b){const q=[[a,0]],seen=new Set([a]);while(q.length){const [x,d]=q.shift();if(x===b)return d;for(const n of spaces[x].adjacent)if(!seen.has(n)){seen.add(n);q.push([n,d+1])}}return 99}
function stepToward(from,target){if(from===target)return from;return spaces[from].adjacent.sort((a,b)=>distance(a,target)-distance(b,target)||a.localeCompare(b))[0]}
async function raid(r,camp=false){
  if(!state.priorityUsed&&state.priority.id==="P01"&&state.tracks.obligation>1&&await yesNo(state.priority.name,state.priority.resolve)){track("obligation",-1);state.priorityUsed=true;log(`${name(r)} answers the raid without losing Readiness.`)}
  else
  if(state.burhs.has(r)){state.burhs.delete(r);log(`The Burh at ${name(r)} absorbs the raid.`)}else deplete(r);
  if(state.tracks.wealth)track("wealth",-1);else track("legitimacy",-1);if(camp)state.camps.add(r);state.roundFlags.raided.add(r);log(`${name(r)} is raided${camp?" and fortified by the Host":""}.`)
}
async function season(){
  if(state.scenario.harvest_rounds.includes(state.round)){for(const r of [...state.field]){const keep=await yesNo("Harvest",`Keep the ${name(r)} fyrd in the field and deplete its home?`);if(keep)deplete(r);else state.field.delete(r)}const ready=wessex().filter(r=>state.readiness[r]===2).length;const gain=ready>=5?2:ready>=3?1:0;track("wealth",gain);log(`Harvest yields ${gain} Wealth from ${ready} Ready regions.`)}
  if(state.field.size){state.tracks.service=clamp(state.tracks.service+1,0,3);if(state.tracks.service>=3){const retain=await yesNo("Service exhausted","Retain the fyrd? This exhausts one home and costs 1 Obligation.");if(retain){const r=[...state.field][0];state.readiness[r]=0;track("obligation",-1);state.tracks.service=1}else{state.field.clear();state.tracks.service=0}}}
  const e=eligibleRecovery();if(e.length){const r=await chooseSpace("Natural recovery","Choose one safe region to recover.",e);recover(r)}
}

function forceCount(){return state.households+state.field.size}
function defended(r){return state.alfred===r&&forceCount()>0}
function hostIdsAt(r){return Object.entries(state.hosts).filter(([,h])=>h.space===r&&h.strength>0).map(([id])=>id)}
function strongestHost(){return Object.values(state.hosts).sort((a,b)=>b.strength-a.strength)[0]}
function track(k,n){state.tracks[k]=clamp((state.tracks[k]||0)+n,k==="reform"?0:0,k==="reform"?6:7)}
function roll(){return Math.floor(Math.random()*6)+1}
function checkLoss(){if(state.tracks.legitimacy<=0||state.tracks.obligation<=0||hostIdsAt(state.scenario.royal_seat).length){endGame(true);return true}return false}
function structuredWin(){const o=state.scenario.objective,ready=wessex().filter(r=>state.readiness[r]===2).length;return state.wins>=(o.wins||0)&&ready>=(o.min_ready||0)&&state.tracks.legitimacy>=(o.min_legitimacy||0)&&state.tracks.obligation>=(o.min_obligation||0)&&state.tracks.reform>=(o.min_reform||0)&&state.camps.size<=(o.max_bases??99)&&state.burhs.size>=(o.active_burhs||0)&&(!o.guthrum_max||state.hosts.guthrum?.strength<=o.guthrum_max)&&(!o.successful_negotiation||state.negotiated)&&(!o.london_clear||!state.camps.has("london"))}
async function endGame(loss=false){
  state.gameOver=true;state.phase="end";const ready=wessex().filter(r=>state.readiness[r]===2).length;let score=state.tracks.legitimacy+state.tracks.obligation+state.tracks.wealth+ready+state.burhs.size-state.camps.size;
  const legacy={
    P01:()=>!wessex().some(r=>state.readiness[r]===0),P02:()=>state.wins>=2,P03:()=>state.burhs.size>=3,
    P04:()=>state.tracks.reform>=4,P05:()=>state.negotiated,P06:()=>ready>=4,
    P07:()=>state.readiness.mercia===2&&!hostIdsAt("london").length&&!state.camps.has("london"),P08:()=>state.households===2
  };
  if(legacy[state.priority.id]?.())score+=2;
  const result=loss?"Wessex falls.":structuredWin()?"The structured objective is complete. Check the printed Historical Mandate to confirm victory.":"Wessex survives, but the structured objective is incomplete.";
  await notice("Legacy",`${result}\n\nLegacy score: ${score}. ${score>=19?"The Great":score>=15?"Enduring Realm":score>=10?"Recovery":"Survival"}.`);render()
}
function log(text){state.log.unshift(text);$("#log").innerHTML=state.log.map(x=>`<li>${x}</li>`).join("")}

function choose(title,text,options){return new Promise(resolve=>{const m=$("#modal"),c=$("#modalContent");c.innerHTML=`<div class="modal-body"><h2>${title}</h2><p>${text}</p><div class="modal-actions">${options.map(o=>`<button data-value="${o.value}" ${o.disabled?"disabled":""}>${o.label}</button>`).join("")}</div></div>`;c.querySelectorAll("button").forEach(b=>b.onclick=()=>{m.close();resolve(b.dataset.value)});m.showModal()})}
function chooseSpace(title,text,allowed){return choose(title,text,allowed.map(r=>({value:r,label:name(r)})))}
function yesNo(title,text){return choose(title,text,[{value:"yes",label:"Yes"},{value:"no",label:"No"}]).then(x=>x==="yes")}
function notice(title,text){return new Promise(resolve=>{const m=$("#modal"),c=$("#modalContent");c.innerHTML=`<div class="modal-body"><h2>${title}</h2><p>${text.replaceAll("\n","<br>")}</p><div class="modal-actions"><button>Continue</button></div></div>`;c.querySelector("button").onclick=()=>{m.close();resolve()};m.showModal()})}
function chooseMany(title,text,options,max){return new Promise(resolve=>{const m=$("#modal"),c=$("#modalContent");c.innerHTML=`<div class="modal-body"><h2>${title}</h2><p>${text}</p><div class="check-list">${options.map(o=>`<label><input type="checkbox" value="${o.value}"> ${o.label}</label>`).join("")}</div><div class="modal-actions"><button class="primary">Confirm</button></div></div>`;const checks=[...c.querySelectorAll("input")];checks.forEach(x=>x.onchange=()=>{if(checks.filter(y=>y.checked).length>max)x.checked=false});c.querySelector("button").onclick=()=>{const values=checks.filter(x=>x.checked).map(x=>x.value);m.close();resolve(values)};m.showModal()})}
function showRules(){notice("How to play","Each round: reveal a Crisis, use one Command card half, take two different Orders, resolve the visible Danish Intent, then Service, Harvest, and recovery. You lose if Legitimacy or Obligation reaches 0, or a Host occupies the royal seat at round end. Complete both the structured objective and Historical Mandate to win.")}

init().catch(error=>{document.body.innerHTML=`<main class="panel"><h2>Could not load the game</h2><p>${error.message}</p><p>Run this folder through a local web server.</p></main>`});
