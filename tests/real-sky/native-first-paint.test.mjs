import test from 'node:test';
import assert from 'node:assert/strict';
import {prepareNativeFirstPaint} from '../../real-sky/native-first-paint.mjs';

test('head presentation accepts only a resolved site and native ordinary wall time',()=>{
 const restore={window:globalThis.window,document:globalThis.document,location:globalThis.location,matchMedia:globalThis.matchMedia,ImageData:globalThis.ImageData};
 const now=Date.now;let admitted=null,styles=[];
 try{
  Date.now=()=>Date.parse('2026-10-07T15:09:00Z');
  globalThis.window={SalahConfig:{resolve:()=>({cfg:admitted})}};globalThis.location={hash:'#local=1'};globalThis.matchMedia=()=>({matches:false});
  globalThis.ImageData=class{constructor(data,w,h){assert.equal(data.length,w*h*4);}};
  globalThis.document={head:{append:s=>styles.push(s)},createElement:name=>name==='canvas'?{getContext:()=>({putImageData(){}}),toDataURL:()=> 'data:image/png;test'}:{}};
  prepareNativeFirstPaint();assert.equal(styles.length,0);assert.equal(window.SalahFirstPaint,undefined,'No invented observer or daytime state');
  admitted={lat:28.5383,lon:-81.3792,tz:'America/New_York',units:'c'};prepareNativeFirstPaint();
  assert.equal(window.SalahFirstPaint.snapshot.utcMs,Date.now());assert.equal(window.SalahFirstPaint.value.utcMs,Date.now());
  assert.equal(window.SalahFirstPaint.snapshot.sceneIdentity,'28.5383|-81.3792|America/New_York|wall');assert.equal(window.SalahFirstPaint.value.quality,'physical-background-preview');
  assert.match(styles[0].textContent,/background-image:url/);assert.doesNotMatch(styles[0].textContent,/visibility|opacity|display\s*:/);
  assert.match(styles[0].textContent,/--moon:0/);
  location.hash='#local=1&simTime=11:00';prepareNativeFirstPaint();assert.equal(styles.length,1,'Explicit temporal owner is not replaced with wall UTC');
 }finally{Date.now=now;for(const [k,v] of Object.entries(restore))if(v===undefined)delete globalThis[k];else globalThis[k]=v;}
});
