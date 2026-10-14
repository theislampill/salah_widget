import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import {nativeJob,nativeResultCurrent} from '../real-sky/native-contract.mjs';

// Execute both authored withdrawal owners. This checks the publication/class
// contract; it is not a browser-pixel substitute. B16 retains its original frames.
const authored=name=>fs.readFileSync(new URL('../real-sky/'+name,import.meta.url),'utf8');
function region(source,start,end){
  const a=source.indexOf(start),b=source.indexOf(end,a);
  assert.ok(a>=0&&b>a,'authored withdrawal anchors');return source.slice(a,b);
}
const fullClear=region(authored('native-host.mjs'),' function clear(',' // Identity/age fences');
const previewClear=region(authored('native-preview-host.mjs'),' function clear(',' function prepareForeground');
const initial=()=>({utcMs:1788806700016,lat:24.47,lon:39.61,heightM:0,
  generation:0,sceneIdentity:'24.47|39.61|Asia/Riyadh|wall',
  camera:{azDeg:180,altDeg:45,fovYDeg:90,rollDeg:0},weather:null,
  lp:0,reducedMotion:false,units:'c',tz:'Asia/Riyadh',timeScale:1});
function fixture(current,{hasPreview=true}={}){
  const classes=new Set(['real-sky-composed','real-sky-preview-ready','moon-ready']);
  let detailVisible=true;
  const card={classList:{contains:x=>classes.has(x),add:x=>classes.add(x),remove:x=>classes.delete(x)},style:{removeProperty(){}}};
  const window={SalahMoonDetail:{clear(){detailVisible=false;}}};
  const job=nativeJob(initial());
  const preview={card,window,value:{job},previewFrame:hasPreview?{current:()=>nativeResultCurrent(job,current)}:null,
    status:{status:'ready'},retireFirstPaint(){},canvas:{style:{visibility:'visible'}}};
  vm.createContext(preview);vm.runInContext(previewClear,preview);
  window.SalahSkyPreview={get frame(){return preview.previewFrame;},get state(){return preview.status;},clear:reason=>preview.clear(reason)};
  const full={card,window,frame:{},job:{},status:{},paintedFrame:{},paintedJob:{},previousPresentation:{},previousMoonBottom:100,
    ctx:{clearRect(){}},canvas:{style:{visibility:'visible'}},publish(){}};
  vm.createContext(full);vm.runInContext(fullClear,full);
  return {classes,preview,full,get detailVisible(){return detailVisible;},withdraw(){full.clear('accepted weather changed');}};
}

for(const [name,change] of [
  ['ordinary wet recovery',s=>{s.weather={src:'model-current',temp:24,cloud:70,code:63};s.heightM=100;}],
  ['preview age exceeds its unchanged30-second bound',s=>{s.utcMs+=30001;}],
  ['invalid accepted target',s=>{s.lat=null;}]
])test('refined withdrawal retires obsolete preview ownership: '+name,()=>{
  const current=initial();change(current);const h=fixture(current);
  assert.equal(h.preview.previewFrame.current(),false,'negative input reaches actual currentness predicate');
  h.withdraw();
  assert.equal(h.classes.has('real-sky-composed'),false);
  assert.equal(h.detailVisible,false,'obsolete refined atmosphere cannot remain on the Moon');
  assert.equal(h.classes.has('real-sky-preview-ready'),false,'invalid preview must not become the visible owner or hide the current SVG Moon');
  assert.equal(h.preview.canvas.style.visibility,'hidden');
  assert.equal(h.classes.has('moon-ready'),true,'sky withdrawal cannot revoke independently current lunar terrain');
});

test('withdrawal cannot expose a preview-ready flag without a corresponding frame',()=>{
  const h=fixture(initial(),{hasPreview:false});h.withdraw();
  assert.equal(h.classes.has('real-sky-preview-ready'),false);
});

test('a current preview retains its own authority when refined sky withdraws',()=>{
  const h=fixture(initial());assert.equal(h.preview.previewFrame.current(),true);h.withdraw();
  assert.equal(h.classes.has('real-sky-preview-ready'),true);
  assert.equal(h.preview.canvas.style.visibility,'visible');
});

test('explicit preview withdrawal still removes its own ready flag and detail',()=>{
  const h=fixture(initial());h.preview.clear('native target invalidated');
  assert.equal(h.classes.has('real-sky-preview-ready'),false);
  assert.equal(h.preview.canvas.style.visibility,'hidden');assert.equal(h.detailVisible,false);
});
