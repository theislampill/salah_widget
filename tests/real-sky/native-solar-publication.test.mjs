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

test('exactly transparent captured clouds need no encoded solar mask; one alpha code still does',()=>{
 const restore={document:globalThis.document,ImageData:globalThis.ImageData};let canvases=0,encoded=null;
 const ctx={clearRect(){},fillRect(){},putImageData(image){encoded=image.data;}};
 try{
  globalThis.document={createElement(){canvases++;return {getContext:()=>ctx,toDataURL:()=> 'data:image/png;base64,positive'};}};
  globalThis.ImageData=class{constructor(data){this.data=data;}};
  const pixels=new Uint8ClampedArray(325*4);for(let i=0;i<pixels.length;i+=4)pixels[i]=255;
  const capture={};
  assert.equal(owner.NativeForegroundCapture.prototype.prepareSolarMask.call(capture,pixels,1),'linear-gradient(#fff,#fff)');
  assert.equal(canvases,0,'Fully transmitted Sun needs neither PNG nor browser decode');
  pixels[pixels.length-1]=1;
  assert.equal(owner.NativeForegroundCapture.prototype.prepareSolarMask.call(capture,pixels,1),'url("data:image/png;base64,positive")');
  assert.equal(canvases,1);assert.equal(encoded.at(-1),254,'Even one alpha code retains the original mask transfer');
  assert.throws(()=>owner.NativeForegroundCapture.prototype.prepareSolarMask.call(capture,pixels,2),/dimensions/);
 }finally{for(const [key,value]of Object.entries(restore))if(value===undefined)delete globalThis[key];else globalThis[key]=value;}
});

test('full transmission publishes synchronously through the same commit guard',()=>{
 const h=fixture();let commits=0;
 assert.equal(h.publication.publish('linear-gradient(#fff,#fff)',()=>{commits++;return false;},e=>h.errors.push(String(e))),true);
 assert.equal(commits,1);assert.equal(h.images.length,0);assert.equal(h.publication.pending,null);assert.equal(h.publication.displayed,null);
 h.publication.publish('linear-gradient(#fff,#fff)',()=>{commits++;},e=>h.errors.push(String(e)));
 assert.equal(commits,2);assert.equal(h.publication.displayed.mask,'linear-gradient(#fff,#fff)');assert.deepEqual(h.errors,[]);
});

test('clear/cloud/clear transition retains decode and cancellation fences',async()=>{
 const h=fixture(),clear=()=>h.publication.publish('linear-gradient(#fff,#fff)',mask=>h.commits.push(mask),e=>h.errors.push(String(e)));
 clear();h.publish('cloud');assert.equal(clear(),false,'An active cloudy decode still owns the pending slot');
 assert.deepEqual(h.commits,['linear-gradient(#fff,#fff)']);assert.equal(h.images[0].modeAtLoad,'anonymous');
 h.publication.cancel();clear();h.images[0].resolve();await h.flush();
 assert.deepEqual(h.commits,['linear-gradient(#fff,#fff)','linear-gradient(#fff,#fff)'],'Cancelled cloudy result cannot overwrite fresh clear inputs');
 h.publish('cloud');h.images[1].resolve();await h.flush();clear();
 assert.deepEqual(h.commits,['linear-gradient(#fff,#fff)','linear-gradient(#fff,#fff)','url("data:image/png;base64,cloud")','linear-gradient(#fff,#fff)']);
 assert.equal(h.publication.pending,null);h.publication.dispose();clear();assert.equal(h.commits.length,4);
});
