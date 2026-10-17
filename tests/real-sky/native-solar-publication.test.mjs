import test from 'node:test';
import assert from 'node:assert/strict';
import * as owner from '../../real-sky/native-composition.mjs';
function fixture(){
 assert.equal(typeof owner.NativeSolarMaskPublication,'function','decoded mask publication owner required');
 const images=[],commits=[],errors=[];
 class Image{
  constructor(){images.push(this);}
  set src(value){this.url=value;this.modeAtLoad=this.crossOrigin;}
  decode(){return new Promise((resolve,reject)=>{this.resolve=resolve;this.reject=reject;});}
 }
 const publication=new owner.NativeSolarMaskPublication(()=>new Image());
 const publish=(n,accept=true)=>publication.publish('url("data:image/png;base64,'+n+'")',mask=>{commits.push(mask);return accept;},e=>errors.push(String(e)));
 const flush=async()=>{for(let i=0;i<4;i++)await Promise.resolve();};
 return {publication,images,commits,errors,publish,flush};
}
test('changing solar mask cannot expose an undecoded frame; CSS anonymous request mode is required',async()=>{
 const h=fixture();h.publish('a');assert.deepEqual(h.commits,[]);assert.equal(h.images[0].modeAtLoad,'anonymous');
 assert(h.publication.pending);h.images[0].resolve();await h.flush();assert.equal(h.commits.length,1);assert(!h.publication.pending);
 h.publish('b');assert.equal(h.commits.length,1,'old coherent framebuffer remains until new mask is ready');
 h.images[1].resolve();await h.flush();assert.equal(h.commits.length,2);
 h.publish('b');assert.equal(h.images.length,2,'same decoded resource is retained');assert.equal(h.commits.length,3);
});
test('one pending decode bounds work; cancellation fences late A after B and disposal',async()=>{
 const h=fixture();h.publish('a');h.publish('ignored');assert.equal(h.images.length,1);
 h.publication.cancel();h.publish('b');h.images[1].resolve();await h.flush();h.images[0].resolve();await h.flush();
 assert.deepEqual(h.commits,['url("data:image/png;base64,b")']);
 h.publish('c');h.publication.dispose();h.images[2].resolve();await h.flush();h.publish('d');assert.equal(h.images.length,3);assert.equal(h.commits.length,1);
});
test('decoded bytes can be reused after a rejected scene, but failed and cancelled decodes never enter the cache',async()=>{
 const h=fixture();h.publish('a',false);h.images[0].resolve();await h.flush();assert.equal(h.publication.displayed,null);
 h.publication.cancel();h.publish('a');assert.equal(h.images.length,1);assert.equal(h.commits.length,2,'fresh owner must still execute its commit guard');
 h.publish('b');h.images[1].reject(Error('controlled decode failure'));await h.flush();assert.equal(h.errors.length,1);assert(!h.publication.pending);
 h.publish('b');assert.equal(h.images.length,3);h.publication.cancel();h.images[2].reject(Error('obsolete'));await h.flush();assert.equal(h.errors.length,1);
 h.publish('b');assert.equal(h.images.length,4);h.publication.dispose();assert.equal(h.publication.decoded,null);
});
