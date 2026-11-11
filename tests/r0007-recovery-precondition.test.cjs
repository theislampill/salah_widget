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

function scene({event='load',media='all',dirty=false,status='loaded',url=href,tagName='LINK',linkPresent=true,layoutStartsLoad=false,faces=[],trusted=true,differentTarget=false}={}){
  let settle;const fontPromise=new Promise(resolve=>{settle=resolve;});
  const state={dirty,status,readyReads:0,layoutReads:0,layoutStartsLoad,faces},listeners=new Map(),tasks=[];
  const fonts={get status(){return state.status;},get ready(){state.readyReads++;return state.status==='loading'?fontPromise:Promise.resolve(fonts);},*[Symbol.iterator](){yield* state.faces;},
    addEventListener(type,listener){if(!listeners.has(type))listeners.set(type,[]);listeners.get(type).push(listener);}};
  const nativeSetTimeout=fn=>tasks.push(fn),documentListeners=new Map();
  const link={href,media,tagName:'LINK',isConnected:true,relList:{contains:value=>value==='stylesheet'}};
  const document={fonts,querySelector:()=>linkPresent?link:null,addEventListener(type,listener,capture){
    assert.equal(capture,true,'observer must use document capture');
    if(!documentListeners.has(type))documentListeners.set(type,[]);documentListeners.get(type).push(listener);
  }};
  link.ownerDocument=document;
  const context=vm.createContext({performance:{now:()=>state.layoutReads},setTimeout:nativeSetTimeout,document,window:{setTimeout:nativeSetTimeout,__prayerFixture:{
    // DOM's Document parent rule excludes Window for element load. Error is
    // not excluded. This test double does not claim a native event occurred.
    assets:event&&event!=='load'?[{event,tagName,url}]:[],
    readSnapshot(){state.layoutReads++;if(state.layoutStartsLoad){state.layoutStartsLoad=false;state.status='loading';}return {dirty:state.dirty};}
  }},_cnFit:'old',_renderDirty:dirty});
  // Old-candidate RED has no observer file. No substitute observer is supplied.
  if(fs.existsSync(observerPath))vm.runInContext(fs.readFileSync(observerPath,'utf8'),context);
  const target=differentTarget||url!==href||tagName!=='LINK'?{...link,href:url,tagName}:link;
  if(event)for(const listener of documentListeners.get(event)||[])listener({type:event,target,isTrusted:trusted});
  vm.runInContext('const cnRelevantFont=face=>/^(Fraunces|Inter)$/i.test(face.family.replace(/["\x27]/g,"").trim());'+fontChanged+'\n'+setFontChanged+";document.fonts.addEventListener('loadingdone',cnFontsChanged);document.fonts.addEventListener('loadingerror',cnFontsChanged);",context);
  return {state,context,link,settle(){state.status='loaded';settle(fonts);},
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
test('synthetic and same-URL wrong-element terminals cannot release the authored link',()=>each(async p=>{
  for(const overrides of [{trusted:false},{differentTarget:true}])
    assert.equal(await evaluate(p.source,scene(overrides)),false,p.id+JSON.stringify(overrides));
}));
test('a terminal receipt cannot follow its element to another stylesheet URL',()=>each(async p=>{
  const s=scene();s.link.href='https://fonts.googleapis.com/css2?family=Other';
  assert.equal(await evaluate(p.source,s),false,p.id);
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

function secOnlyPredicate(){
  const c=recipes.cases.find(c=>c.caseId==='NE07-mut-dst-sec-only');
  assert(c,'literal NY sec-only native case exists');
  const release=c.orderedActions.findIndex(a=>a.type==='release'&&a.id==='tomorrow');
  const barrier=c.orderedActions[release-1];
  assert.equal(barrier.type,'wait');assert.equal(barrier.awaitResult,true);
  return barrier.predicate;
}
test('sec-only precondition accepts ignored dirty only after genuine font settlement; healthy still rejects it',async()=>{
  const source=secOnlyPredicate(),face={family:'Inter',weight:'400',style:'normal',status:'loaded'};
  const s=scene({dirty:true,faces:[face]});
  assert.equal(await evaluate(source,s),false,'queued native completion is not settlement');
  s.fire('loadingdone');assert.equal(await evaluate(source,s),false,'dispatch has not returned');
  s.flushObservers();assert.equal(await evaluate(source,s),true,'settled fonts do not require the mutant to consume dirty');
  assert.equal(s.state.dirty,true,'observer never clears product dirty');
  const healthy=predicates.find(p=>p.id==='NE07-dst-recovery24');
  assert.equal(await evaluate(healthy.source,s),false,'healthy recovery keeps the full clear-dirty precondition');
  s.clearDirty();assert.equal(await evaluate(healthy.source,s),true);
});
test('sec-only precondition retains real stylesheet identity, activation and typed font requirements',async()=>{
  const source=secOnlyPredicate();
  for(const options of [{event:null},{linkPresent:false},{media:'print'},{trusted:false},{differentTarget:true},
      {url:'https://fonts.googleapis.com/css2?family=Other'},{faces:[{family:'Inter',status:'loaded'}]}])
    assert.equal(await evaluate(source,scene({dirty:true,...options})),false,JSON.stringify(options));
  const face={family:'Inter',status:'error'},s=scene({dirty:true,faces:[face]});
  s.fire('loadingdone');s.flushObservers();assert.equal(await evaluate(source,s),false,'wrong terminal type');
  s.fire('loadingerror');s.flushObservers();assert.equal(await evaluate(source,s),true,'genuine failure permits settled fallback');
  s.state.faces=[{...face}];assert.equal(await evaluate(source,s),false,'replacement cannot inherit receipt');
});
test('sec-only precondition still awaits real pending fonts exposed by read-only layout',async()=>{
  const s=scene({dirty:true,layoutStartsLoad:true});let finished=false;
  const result=evaluate(secOnlyPredicate(),s).then(value=>{finished=true;return value;});
  await new Promise(resolve=>setImmediate(resolve));assert.equal(finished,false);
  assert(s.state.readyReads>0);s.settle();assert.equal(await result,true);assert.equal(s.state.dirty,true);
});
