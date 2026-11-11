'use strict';
// Independent pure schedule counterexample. No browser, server, product mutation,
// real font service, or native timing result. CSS Font Loading 3 §3.1 resolves
// ready before queuing loadingdone/loadingerror; callback source below is exact.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const test=require('node:test'),assert=require('node:assert/strict');
const root=path.join(__dirname,'snapshot');
const packet=JSON.parse(fs.readFileSync(path.join(root,'tests/rlgwo/R0007-next-event-recipes.json'),'utf8'));
const authored=fs.readFileSync(path.join(root,'src/native/index.html'),'utf8');
const hooks=authored.slice(authored.indexOf('const cnRelevantFont='),authored.indexOf('function cnFontSignature'))+'\n'+authored.match(/function cnFontsChanged\(event\)\{[\s\S]*?\n\}/)[0];
const href='https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400..700&family=Inter:wght@400;500;600&display=swap';
function makeScene(){
 let resolveReady;
 const state={fontStatus:'loading',layoutReads:0,terminalEventPending:true};
 const ready=new Promise(resolve=>{resolveReady=resolve;});
 const fonts={get status(){return state.fontStatus;},get ready(){return ready;}};
 const context=vm.createContext({_cnFit:'cached',_renderDirty:false,
  document:{fonts,querySelector:()=>({href,media:'all'})},
  window:{__prayerFixture:{assets:[{tagName:'LINK',event:'load',url:href}],
   readSnapshot(){state.layoutReads++;return {dirty:context._renderDirty};}}}});
 vm.runInContext(hooks,context);
 return {state,context,
  resolveAfterEarlierFaceCallbackWasConsumed(){
   // Face.loaded callback can dirty the old current render, then the native loop
   // consumes it before layout completion makes the set ready. The set-wide
   // loadingdone task remains pending as a distinct second dirty producer.
   vm.runInContext('cnFontChanged();',context);
   assert.equal(context._renderDirty,true);
   context._renderDirty=false;
   state.fontStatus='loaded';resolveReady(fonts);
  },
  terminalEvent(){vm.runInContext("cnFontsChanged({fontfaces:[{family:'Inter'}]});",context);state.terminalEventPending=false;}
 };
}
const ids=['NE07-recovery24','NE07-recovery12','NE07-dst-recovery24','NE07-mut-remove-next-dirty'];
for(const id of ids){
 const c=packet.cases.find(c=>c.caseId===id);
 const release=c.orderedActions.findIndex(a=>a.type==='release'&&a.id==='tomorrow');
 const predicate=c.orderedActions[release-1].predicate;
 test(id+' must not release while a real product font dirty callback is still queued',async()=>{
  const s=makeScene();
  const result=vm.runInContext('('+predicate+')',s.context)();
  s.resolveAfterEarlierFaceCallbackWasConsumed();
  const admitted=await result;
  const before={barrierAccepted:admitted,terminalEventPending:s.state.terminalEventPending,dirty:s.context._renderDirty};
  // A removed-next-dirty fixture can adopt tomorrow without waking, then the
  // independently queued font event wakes that new state on the next frame.
  const model={tomorrowAdopted:true,renderedTarget:'unavailable'};
  s.terminalEvent();
  if(s.context._renderDirty){s.context._renderDirty=false;model.renderedTarget='00:31';}
  console.log(JSON.stringify({id,before,afterTerminalEvent:{renderedTarget:model.renderedTarget},scope:'SYNTHETIC_SPEC_PERMITTED_ORDER_ONLY'}));
  assert.equal(admitted,false,'ready + loaded + clear-dirty admits before queued loadingdone');
 });
 test(id+' positive: a consumed terminal callback allows settled fallback',async()=>{
  const s=makeScene();s.resolveAfterEarlierFaceCallbackWasConsumed();s.terminalEvent();s.context._renderDirty=false;
  assert.equal(await vm.runInContext('('+predicate+')',s.context)(),true);
 });
}
