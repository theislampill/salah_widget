'use strict';

// Browser-free counterexamples for the exact native recipe predicates. These
// synthetic CSS/font states prove setup discrimination, never native pixels,
// product rendering, first-frame recovery or a real font-service observation.
const test=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const recipes=JSON.parse(fs.readFileSync(process.env.R0007_RECIPES_FILE||path.join(__dirname,'rlgwo/R0007-next-event-recipes.json'),'utf8'));
const ids=['NE07-recovery24','NE07-recovery12','NE07-dst-recovery24','NE07-dst-recovery12','NE07-mut-remove-next-dirty'];
const predicates=ids.map(id=>{
  const recipe=recipes.cases.find(c=>c.caseId===id);
  assert(recipe,id+' exists');
  const index=recipe.orderedActions.findIndex(a=>a.type==='release'&&a.id==='tomorrow');
  const prior=recipe.orderedActions[index-1];
  assert.equal(prior.type,'wait',id+' has a barrier immediately before release');
  return {id,source:prior.predicate};
});
const authored=fs.readFileSync(path.join(__dirname,'../src/native/index.html'),'utf8');
const fontChanged=authored.match(/function cnFontChanged\(\)\{[^}]+\}/)[0];
const setFontChanged=authored.match(/function cnFontsChanged\(event\)\{[\s\S]*?\n\}/)[0];
const observerPath=path.join(__dirname,'../tools/cp9/r0007_font_observer.js');
const href='https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400..700&family=Inter:wght@400;500;600&display=swap';

function scene({event='load',media='all',dirty=false,status='loaded',url=href,tagName='LINK',linkPresent=true,layoutStartsLoad=false,faces=[]}={}){
  let settle;const fontPromise=new Promise(resolve=>{settle=resolve;});
  const state={dirty,status,readyReads:0,layoutReads:0,layoutStartsLoad,faces},listeners=new Map(),tasks=[];
  const fonts={get status(){return state.status;},get ready(){state.readyReads++;return state.status==='loading'?fontPromise:Promise.resolve(fonts);},*[Symbol.iterator](){yield* state.faces;},
    addEventListener(type,listener){if(!listeners.has(type))listeners.set(type,[]);listeners.get(type).push(listener);}};
  const nativeSetTimeout=fn=>tasks.push(fn);
  const context=vm.createContext({performance:{now:()=>state.layoutReads},setTimeout:nativeSetTimeout,document:{fonts,querySelector:()=>linkPresent?{href,media}:null},window:{setTimeout:nativeSetTimeout,__prayerFixture:{
    assets:event?[{event,tagName,url}]:[],
    readSnapshot(){state.layoutReads++;if(state.layoutStartsLoad){state.layoutStartsLoad=false;state.status='loading';}return {dirty:state.dirty};}
  }},_cnFit:'old',_renderDirty:dirty});
  // Old-candidate RED has no observer file. No substitute observer is supplied.
  if(fs.existsSync(observerPath))vm.runInContext(fs.readFileSync(observerPath,'utf8'),context);
  vm.runInContext('const cnRelevantFont=face=>/^(Fraunces|Inter)$/i.test(face.family.replace(/["\x27]/g,"").trim());'+fontChanged+'\n'+setFontChanged+";document.fonts.addEventListener('loadingdone',cnFontsChanged);document.fonts.addEventListener('loadingerror',cnFontsChanged);",context);
  return {state,context,settle(){state.status='loaded';settle(fonts);},
    fontChanged(){vm.runInContext('cnFontChanged();',context);state.dirty=context._renderDirty;},
    fire(type,eventFaces=state.faces){for(const listener of listeners.get(type)||[])listener({type,fontfaces:eventFaces});state.dirty=context._renderDirty;},
    flushObservers(){while(tasks.length)tasks.shift()();},clearDirty(){state.dirty=false;context._renderDirty=false;}};
}
async function evaluate(source,s){const value=vm.runInContext('('+source+')',s.context);return typeof value==='function'?value():value;}
async function each(check){for(const p of predicates)await check(p);}

test('QUAL-01 pending stylesheet with empty loaded font set cannot release',()=>each(async p=>{
  const s=scene({event:null});assert.equal(await evaluate(p.source,s),false,p.id);
}));
test('an unrelated LINK receipt and preconnect completion cannot supply stylesheet terminality',()=>each(async p=>{
  for(const overrides of [{url:'https://fonts.googleapis.com'},{tagName:'IMG'},{event:'loading'}])
    assert.equal(await evaluate(p.source,scene(overrides)),false,p.id+JSON.stringify(overrides));
}));
test('a loaded stylesheet must have its actual media activation applied',()=>each(async p=>{
  assert.equal(await evaluate(p.source,scene({media:'print'})),false,p.id);
}));
test('terminal stylesheet failure permits settled fallback with no registered font faces',()=>each(async p=>{
  assert.equal(await evaluate(p.source,scene({event:'error',media:'print'})),true,p.id);
}));
test('terminal active stylesheet and settled fonts with clear dirty flag permit release',()=>each(async p=>{
  const s=scene();assert.equal(await evaluate(p.source,s),true,p.id);assert(s.state.readyReads>0,p.id+' observes actual FontFaceSet.ready');
}));
test('font loading is awaited without releasing the held reply',()=>each(async p=>{
  const s=scene({status:'loading'});let finished=false;
  const result=evaluate(p.source,s).then(value=>{finished=true;return value;});
  await new Promise(resolve=>setImmediate(resolve));
  assert.equal(finished,false,p.id+' remains held while fonts load');s.settle();assert.equal(await result,true,p.id);
}));
test('read-only layout precedes ready so stylesheet application can expose pending font work',()=>each(async p=>{
  const s=scene({layoutStartsLoad:true});let finished=false;
  const result=evaluate(p.source,s).then(value=>{finished=true;return value;});
  await new Promise(resolve=>setImmediate(resolve));
  assert.equal(finished,false,p.id+' waits for load revealed by layout');assert(s.state.readyReads>0,p.id);
  s.settle();assert.equal(await result,true,p.id);
}));
test('actual product font completion callback keeps release held until original dirty work clears',()=>each(async p=>{
  const s=scene({status:'loading'});const result=evaluate(p.source,s);s.fontChanged();s.settle();
  assert.equal(await result,false,p.id);assert.equal(s.state.dirty,true,p.id+' exact product callback sets dirty');
  s.state.dirty=false;assert.equal(await evaluate(p.source,s),true,p.id+' later clear observation permits release');
}));
test('existing dirty work and a missing stylesheet cannot be treated as a settled barrier',()=>each(async p=>{
  assert.equal(await evaluate(p.source,scene({dirty:true})),false,p.id+' dirty');
  assert.equal(await evaluate(p.source,scene({linkPresent:false})),false,p.id+' missing stylesheet');
}));

test('ready before queued loadingdone cannot release before dispatch, deferred receipt and dirty clearance',()=>each(async p=>{
  const face={family:'Inter',weight:'400',style:'normal',status:'loaded'},s=scene({faces:[face]});
  assert.equal(await evaluate(p.source,s),false,p.id+' terminal event still queued');
  s.fire('loadingdone');s.clearDirty();
  assert.equal(await evaluate(p.source,s),false,p.id+' early observer must not credit event during dispatch');
  s.flushObservers();assert.equal(await evaluate(p.source,s),true,p.id+' actual deferred event and clear dirty');
}));
test('terminal event before ready is also supported without requiring a fabricated later event',()=>each(async p=>{
  const face={family:'Inter',weight:'400',style:'normal',status:'loading'},s=scene({status:'loading',faces:[face]});
  const pending=evaluate(p.source,s);face.status='loaded';s.fire('loadingdone');s.flushObservers();s.clearDirty();s.settle();
  assert.equal(await pending,true,p.id);
}));
test('mixed successful and failed faces require their own terminal type in either event order',()=>each(async p=>{
  for(const order of [['loadingdone','loadingerror'],['loadingerror','loadingdone']]){
    const good={family:'Inter',weight:'400',style:'normal',status:'loaded'},bad={family:'Fraunces',weight:'600',style:'normal',status:'error'};
    const s=scene({faces:[good,bad]});
    s.fire(order[0],[order[0]==='loadingdone'?good:bad]);s.flushObservers();s.clearDirty();
    assert.equal(await evaluate(p.source,s),false,p.id+' missing '+order[1]);
    s.fire(order[1],[order[1]==='loadingdone'?good:bad]);s.flushObservers();s.clearDirty();
    assert.equal(await evaluate(p.source,s),true,p.id+' both typed receipts');
  }
}));
test('loaded face without a real event receipt remains diagnostically unavailable',()=>each(async p=>{
  assert.equal(await evaluate(p.source,scene({faces:[{family:'Inter',status:'loaded'}]})),false,p.id);
}));
test('a replacement font object cannot inherit an old same-family completion receipt',()=>each(async p=>{
  const face={family:'Inter',weight:'400',style:'normal',status:'loaded'},s=scene({faces:[face]});
  s.fire('loadingdone');s.flushObservers();s.clearDirty();assert.equal(await evaluate(p.source,s),true,p.id+' original');
  s.state.faces=[{...face}];assert.equal(await evaluate(p.source,s),false,p.id+' replacement');
  s.fire('loadingdone');s.flushObservers();s.clearDirty();
  assert.equal(await evaluate(p.source,s),false,p.id+' replacement remains outside the static lifecycle even after a new event');
}));
test('a successful event cannot credit a failed face',()=>each(async p=>{
  const face={family:'Inter',status:'error'},s=scene({faces:[face]});
  s.fire('loadingdone');s.flushObservers();s.clearDirty();assert.equal(await evaluate(p.source,s),false,p.id+' wrong terminal type');
  s.fire('loadingerror');s.flushObservers();s.clearDirty();assert.equal(await evaluate(p.source,s),true,p.id+' matching terminal type');
}));
test('unused relevant faces and unrelated font families do not invent product dirty callbacks',()=>each(async p=>{
  for(const face of [{family:'Inter',status:'unloaded'},{family:'Unrelated',status:'loaded'}])
    assert.equal(await evaluate(p.source,scene({faces:[face]})),true,p.id+' '+face.family+' '+face.status);
}));
