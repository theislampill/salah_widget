import test from 'node:test';import assert from 'node:assert/strict';
const mod=await import('../../real-sky/native-assets.mjs').catch(()=>({}));
const tick=async()=>{for(let i=0;i<8;i++)await Promise.resolve();};
function harness(options={}){assert.equal(typeof mod.NativeAssetLoader,'function','Optional native asset loader exists');const loads=[],started=[],states=[],resets=[];const loader=new mod.NativeAssetLoader({load:signal=>new Promise((resolve,reject)=>loads.push({signal,resolve,reject})),start:pack=>{started.push(pack);},onState:s=>states.push(s),onReset:()=>resets.push(true),timeoutMs:1000,...options});return{loader,loads,started,states,resets};}
test('slow optional asset stays loading until it is admitted',async()=>{const h=harness();const p=h.loader.retry();assert.equal(h.loader.state.status,'loading');assert.equal(h.started.length,0);h.loads[0].resolve({id:'retained'});await p;assert.equal(h.loader.state.status,'ready');assert.equal(h.started.length,1);h.loader.dispose();});
test('missing data is explicit unavailable and permits successful retry',async()=>{const h=harness();const a=h.loader.retry();h.loads[0].reject(new Error('404'));await a;assert.equal(h.loader.state.status,'unavailable');const b=h.loader.retry();h.loads[1].resolve({id:'restored'});await b;assert.equal(h.loader.state.status,'ready');assert.deepEqual(h.started,[{id:'restored'}]);h.loader.dispose();});
test('corrupt decoder/start cannot become ready',async()=>{const h=harness({start:()=>{throw new Error('Invalid pinned catalogue');}});const p=h.loader.retry();h.loads[0].resolve({bad:true});await p;assert.equal(h.loader.state.status,'unavailable');assert.match(h.loader.state.error,/Invalid pinned/);h.loader.dispose();});
test('late A completion cannot replace B after retry',async()=>{const h=harness();const a=h.loader.retry(),b=h.loader.retry();assert.equal(h.loads[0].signal.aborted,true);h.loads[1].resolve({id:'B'});await b;h.loads[0].resolve({id:'A'});await a;assert.deepEqual(h.started,[{id:'B'}]);assert.equal(h.loader.state.generation,2);h.loader.dispose();});
test('late obsolete rejection cannot erase successful recovery',async()=>{const h=harness();const a=h.loader.retry(),b=h.loader.retry();h.loads[1].resolve({id:'B'});await b;h.loads[0].reject(new Error('late A'));await a;assert.equal(h.loader.state.status,'ready');h.loader.dispose();});
test('hung load has a bounded timeout and abort',async()=>{const h=harness({timeoutMs:5});await h.loader.retry();assert.equal(h.loader.state.status,'unavailable');assert.equal(h.loads[0].signal.aborted,true);assert.match(h.loader.state.error,/timeout/i);h.loader.dispose();});
test('disposal prevents resurrection by any obsolete completion',async()=>{const h=harness();const p=h.loader.retry();h.loader.dispose();h.loads[0].resolve({id:'A'});await p;await h.loader.retry();assert.equal(h.started.length,0);assert.equal(h.loader.state.status,'disposed');});

test('retry supplies a distinct generation to the request factory so pending script requests cannot coalesce',async()=>{
 const generations=[];
 const loader=new mod.NativeAssetLoader({load:async(_signal,generation)=>{generations.push(generation);return {};},start:()=>{}});
 await loader.retry();await loader.retry();
 assert.deepEqual(generations,[1,2]);loader.dispose();
});
