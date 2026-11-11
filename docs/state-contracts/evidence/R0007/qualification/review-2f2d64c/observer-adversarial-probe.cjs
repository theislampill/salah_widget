'use strict';
// Independent synthetic scheduling probes against exact committed code. They
// establish observer behavior, not any native browser/event-order incidence.
const fs = require('node:fs'), path = require('node:path'), vm = require('node:vm');
const test = require('node:test'), assert = require('node:assert/strict');
const root = path.join(__dirname, 'candidate');
const source = fs.readFileSync(path.join(root, 'tools/cp9/r0007_font_observer.js'), 'utf8');
const product = fs.readFileSync(path.join(root, 'src/native/index.html'), 'utf8');
const hooks = product.slice(product.indexOf('const cnRelevantFont='), product.indexOf('function cnFontSignature')) + '\n' + product.match(/function cnFontsChanged\(event\)\{[\s\S]*?\n\}/)[0];
const current = JSON.parse(fs.readFileSync(path.join(root, 'tests/rlgwo/R0007-next-event-recipes.json')));
const prior = JSON.parse(fs.readFileSync(path.join(__dirname, '../qualification-review-b20e3aa/snapshot/tests/rlgwo/R0007-next-event-recipes.json')));
const ids = ['NE07-recovery24', 'NE07-recovery12', 'NE07-dst-recovery24', 'NE07-mut-remove-next-dirty'];
const href = 'https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400..700&family=Inter:wght@400;500;600&display=swap';
const face = (status = 'loaded') => ({family:'Inter', weight:'400', style:'normal', status});
function predicate(packet, id) {
  const c = packet.cases.find(c => c.caseId === id);
  const release = c.orderedActions.findIndex(a => a.type === 'release' && a.id === 'tomorrow');
  return c.orderedActions[release-1].predicate;
}
function scene(faces = [face()]) {
  const listeners = new Map(), tasks = [];
  const state = {faces, status:'loaded', timerWrapperCalls:0};
  const fonts = {get status(){return state.status;}, get ready(){return Promise.resolve(fonts);},
    *[Symbol.iterator](){yield* state.faces;},
    addEventListener(type, handler){if(!listeners.has(type))listeners.set(type,[]);listeners.get(type).push(handler);}};
  const context = vm.createContext({_cnFit:'cached', _renderDirty:false,
    performance:{now:()=>0}, document:{fonts, querySelector:()=>({href, media:'all'})},
    window:{setTimeout:fn=>tasks.push(fn), __prayerFixture:{
      assets:[{tagName:'LINK', event:'load', url:href}], readSnapshot(){return {dirty:context._renderDirty};}}}});
  vm.runInContext(source, context);
  vm.runInContext(hooks + ";document.fonts.addEventListener('loadingdone',cnFontsChanged);document.fonts.addEventListener('loadingerror',cnFontsChanged);", context);
  // Deliberately replace the later public timer. The pre-document observer must
  // retain the native timer and stay outside fixture/product timer accounting.
  context.window.setTimeout = () => {state.timerWrapperCalls++; throw Error('later wrapper used');};
  return {state, context, tasks,
    evaluate:async text=>vm.runInContext('('+text+')',context)(),
    diagnostics:()=>context.window.__r0007FontSettlement.read(),
    clear(){context._renderDirty=false;},
    async fire(type, eventFaces = state.faces, between){
      let index=0;
      for(const handler of listeners.get(type)||[]){handler({type, fontfaces:eventFaces});if(between)await between(index++);}
    },
    flushOne(){assert(tasks.length);tasks.shift()();},
    flushAll(){while(tasks.length)tasks.shift()();}
  };
}

test('same queued-terminal schedule discriminates prior and successor for all four barriers', async()=>{
  for(const id of ids){
    const s=scene();
    assert.equal(await s.evaluate(predicate(prior,id)),true,id+' prior admits queued terminal event');
    assert.equal(await s.evaluate(predicate(current,id)),false,id+' successor holds');
    await s.fire('loadingdone');
    assert.equal(s.context._renderDirty,true);
    s.flushAll();
    assert.equal(await s.evaluate(predicate(current,id)),false,id+' product dirty still pending');
    s.clear();
    assert.equal(await s.evaluate(predicate(current,id)),true,id+' actual terminal event and consumed dirty');
  }
});

test('microtask checkpoint between observer and product listener cannot get terminal credit', async()=>{
  for(const id of ids){
    const s=scene();
    await s.fire('loadingdone',s.state.faces,async index=>{
      if(index===0){
        assert.equal(s.context._renderDirty,false,'product callback has not run');
        assert.equal(s.diagnostics().pendingDeferred,1);
        assert.equal(await s.evaluate(predicate(current,id)),false,id+' inter-listener continuation');
      }
    });
    assert.equal(s.context._renderDirty,true);
    s.flushAll();s.clear();
    assert.equal(await s.evaluate(predicate(current,id)),true);
    assert.equal(s.state.timerWrapperCalls,0);
    assert.deepEqual(Array.from(s.diagnostics().events,e=>e.kind),['dispatch','deferred-receipt']);
  }
});

test('pending count holds until every queued typed terminal receipt completes', async()=>{
  const a=face(),b={...face('error'),family:'Fraunces'},s=scene([a,b]);
  await s.fire('loadingdone',[a]);await s.fire('loadingerror',[b]);s.clear();
  assert.equal(s.diagnostics().pendingDeferred,2);s.flushOne();
  assert.equal(s.diagnostics().pendingDeferred,1);
  assert.equal(s.diagnostics().settled,false);s.flushOne();
  assert.equal(s.diagnostics().pendingDeferred,0);assert.equal(s.diagnostics().settled,true);
  assert.equal(s.state.timerWrapperCalls,0);
});

test('descriptor mutation cannot preserve stale terminal credit', async()=>{
  const a=face(),s=scene([a]);await s.fire('loadingdone');s.flushAll();s.clear();
  assert.equal(s.diagnostics().settled,true);a.weight='700';
  assert.equal(s.diagnostics().settled,false);
  assert(s.diagnostics().lifecycleErrors.some(e=>e.startsWith('changed:')));
  await s.fire('loadingdone');s.flushAll();s.clear();
  assert.equal(s.diagnostics().settled,false);
});

test('observed reload transition cannot reuse prior completion credit', async()=>{
  const a=face(),s=scene([a]);await s.fire('loadingdone');s.flushAll();s.clear();
  assert.equal(s.diagnostics().settled,true);a.status='loading';s.state.status='loading';
  await s.fire('loading',[]);
  assert(s.diagnostics().lifecycleErrors.some(e=>e.startsWith('restarted:')));
  a.status='loaded';s.state.status='loaded';await s.fire('loadingdone');s.flushAll();s.clear();
  assert.equal(s.diagnostics().settled,false);
});

test('an empty terminal event does not grant a loaded face a receipt', async()=>{
  const s=scene();await s.fire('loadingdone',[]);s.flushAll();
  assert.equal(s.diagnostics().settled,false);assert.equal(s.diagnostics().pendingDeferred,0);
});

test('a failed receipt does not credit a successful face', async()=>{
  const s=scene();await s.fire('loadingerror');s.flushAll();s.clear();
  assert.equal(s.diagnostics().settled,false);
  await s.fire('loadingdone');s.flushAll();s.clear();assert.equal(s.diagnostics().settled,true);
});
