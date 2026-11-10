/** CP7.5: bounded, content-addressed diffuse admission and asynchronous selection.
 * The trusted shipped manifest hash pins runtime bytes; it is NOT a new signature
 * authenticating Gaia. Provenance/admission remain in the retained CP7.1–7.3 record.
 * No observer, camera, atmosphere or rendered frame is cached here.
 */
import {sha256Hex} from './sha256.mjs';
import {validateCatalogue} from './catalogue.mjs';
import {bindRegisteredStarlight} from './diffuse-binding.mjs';
const DA_SOURCE='69f3c6ede4a730e0ca4699f5943fca59d0b203f37c4dfc4b7e6927f063250446';
function daFreeze(x){if(x&&typeof x==='object'&&!Object.isFrozen(x)){for(const v of Object.values(x))daFreeze(v);Object.freeze(x);}return x;}
function daHash(text){return sha256Hex(new TextEncoder().encode(text));}
function daCheckText(text,descriptor,label){if(typeof text!=='string')throw new TypeError(label+' must be exact UTF-8 text');const b=new TextEncoder().encode(text);if(b.byteLength!==descriptor.bytes)throw new RangeError(label+' byte size mismatch');if(sha256Hex(b)!==descriptor.sha256)throw new TypeError(label+' content hash mismatch');}
function daDescriptor(d,path,nside){if(!d||d.path!==path||!/^[0-9a-f]{64}$/.test(d.sha256??'')||!Number.isSafeInteger(d.bytes)||d.bytes<1||d.bytes>12000000)throw new TypeError('Invalid pinned asset descriptor');if(nside&&(d.nside!==nside||typeof d.id!=='string'||!d.id.length))throw new TypeError('Tier grid/identity mismatch');}
export function parseDiffuseManifest(text,expectedSha256){
 if(typeof text!=='string'||text.length>65536||!/^[0-9a-f]{64}$/.test(expectedSha256??'')||daHash(text)!==expectedSha256)throw new TypeError('Diffuse manifest hash mismatch');
 const m=JSON.parse(text);if(m.schema!=='salah-real-sky/diffuse-runtime-manifest/1'||m.sourceSha256!==DA_SOURCE)throw new TypeError('Unsupported diffuse manifest version/source');
 daDescriptor(m.catalogue,'data/bright-stars.json');
 if(!m.assets||Object.keys(m.assets).sort().join(',')!=='128,32,64')throw new TypeError('Expected exactly three runtime tiers');
 for(const tier of ['32','64','128'])daDescriptor(m.assets[tier],'data/registered-starlight/V-nside'+tier+'.json',Number(tier));
 return daFreeze(m);
}
export class DiffuseAssetStore{
 #cache=new Map();#serial=0;#controller=null;#disposed=false;#state;#text;
 constructor(manifestText,expectedManifestSha256,catalogueText){
  this.manifest=parseDiffuseManifest(manifestText,expectedManifestSha256);daCheckText(catalogueText,this.manifest.catalogue,'catalogue');
  this.catalogue=daFreeze(validateCatalogue(JSON.parse(catalogueText)));this.#text=catalogueText;
  this.#state=Object.freeze({status:'idle',generation:0,tier:null,binding:null,error:null});
  Object.defineProperty(this,'manifest',{writable:false,configurable:false});Object.defineProperty(this,'catalogue',{writable:false,configurable:false});
 }
 get snapshot(){return this.#state;}
 get cacheEntries(){return this.#cache.size;}
 async load(tier,readText,{reload=false}={}){
  if(this.#disposed)return this.#state;
  const generation=++this.#serial;this.#controller?.abort();const control=new AbortController();this.#controller=control;
  tier=String(tier);this.#state=Object.freeze({status:'loading',generation,tier,binding:null,error:null});
  try{
   const d=this.manifest.assets[tier];if(!d)throw new RangeError('Unsupported diffuse tier');
   if(typeof readText!=='function'||typeof reload!=='boolean')throw new TypeError('Reader and boolean reload required');
   if(reload)this.#cache.delete(d.sha256);
   let binding=this.#cache.get(d.sha256),cacheHit=!!binding;
   if(!binding){
    const text=await readText(d.path,{signal:control.signal,maxBytes:d.bytes});
    if(generation!==this.#serial||this.#disposed)return Object.freeze({status:'superseded',generation,tier,binding:null});
    daCheckText(text,d,'diffuse tier '+tier);const asset=JSON.parse(text);
    if(asset.grid?.nside!==d.nside||asset.id!==d.id)throw new TypeError('Manifest and decoded grid/identity disagree');
    binding=bindRegisteredStarlight(this.#text,asset);
   }
   if(generation!==this.#serial||this.#disposed)return Object.freeze({status:'superseded',generation,tier,binding:null});
   this.#cache.set(d.sha256,binding); // at most the three pinned manifest entries
   return this.#state=Object.freeze({status:'ready',generation,tier,binding,cacheHit,error:null,assetSha256:d.sha256});
  }catch(e){
   if(generation!==this.#serial||this.#disposed)return Object.freeze({status:'superseded',generation,tier,binding:null});
   return this.#state=Object.freeze({status:'unavailable',generation,tier,binding:null,error:String(e?.message??e)});
  }
 }
 dispose(){if(this.#disposed)return;this.#disposed=true;this.#serial++;this.#controller?.abort();this.#controller=null;this.#cache.clear();this.#text='';this.#state=Object.freeze({status:'disposed',generation:this.#serial,tier:null,binding:null,error:null});}
}
/** Bounded streaming UTF-8 read. A host may replace this with its authorised local
 * loader; cancellation/generation checks remain in the store even if a loader ignores abort.
 */
export async function readDiffuseAssetText(url,{signal,maxBytes=12000000}={}){
 if(!Number.isSafeInteger(maxBytes)||maxBytes<1||maxBytes>12000000)throw new RangeError('Asset byte budget required');
 const response=await fetch(url,{signal});if(!response.ok){await response.body?.cancel().catch(()=>{});throw new Error('Asset HTTP '+response.status);}
 const declared=response.headers.get('content-length');if(declared!==null&&Number(declared)>maxBytes){await response.body?.cancel().catch(()=>{});throw new RangeError('Asset exceeds byte budget');}
 if(!response.body)throw new Error('Asset response body missing');
 const reader=response.body.getReader(),decoder=new TextDecoder('utf-8',{fatal:true});let total=0,text='';
 try{for(;;){const {done,value}=await reader.read();if(done)break;total+=value.byteLength;if(total>maxBytes)throw new RangeError('Asset exceeds byte budget');text+=decoder.decode(value,{stream:true});}text+=decoder.decode();return text;}
 catch(e){await reader.cancel().catch(()=>{});throw e;}finally{reader.releaseLock();}
}
