import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import {nativeJob,nativeResultCurrent} from '../real-sky/native-contract.mjs';
import {NativeSolarMaskPublication} from '../real-sky/native-composition.mjs';

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
function fixture(current,{hasPreview=true,hasTerrain=true,detailOwner='refined-sky'}={}){
  const classes=new Set(['real-sky-composed','real-sky-preview-ready']);
  if(hasTerrain)classes.add('moon-ready');
  let detailVisible=hasTerrain;
  const card={classList:{contains:x=>classes.has(x),add:x=>classes.add(x),remove:x=>classes.delete(x)},style:{removeProperty(){}}};
  const window={SalahMoonDetail:{clear(){detailVisible=false;},get state(){return {skyOwner:detailOwner,visible:detailVisible};}}};
  const job=nativeJob(initial());
  const preview={card,window,solarPublication:new NativeSolarMaskPublication(),pendingValue:{job},value:{job},previewFrame:hasPreview?{current:()=>nativeResultCurrent(job,current)}:null,
    status:{status:'ready'},retireFirstPaint(){},canvas:{style:{visibility:'visible'}}};
  vm.createContext(preview);vm.runInContext(previewClear,preview);
  window.SalahSkyPreview={get frame(){return preview.previewFrame;},get state(){return preview.status;},clear:reason=>preview.clear(reason)};
  const full={card,window,solarPublication:new NativeSolarMaskPublication(),pendingJob:{},frame:{},job:{},status:{},paintedFrame:{},paintedJob:{},previousPresentation:{},previousMoonBottom:100,
    ctx:{clearRect(){}},canvas:{style:{visibility:'visible'}},publish(){}};
  vm.createContext(full);vm.runInContext(fullClear,full);
  return {classes,preview,full,get detailVisible(){return detailVisible;},withdraw(){full.clear('accepted weather changed');
    assert.equal(full.solarPublication.revision,1,'withdrawal cancels the previous solar publication');
    assert.equal(full.pendingJob,null,'withdrawal drops the pending refined job');
  }};
}

for(const [name,change,hasTerrain=true] of [
  ['ordinary wet recovery',s=>{s.weather={src:'model-current',temp:24,cloud:70,code:63};s.heightM=100;}],
  ['preview age exceeds its unchanged30-second bound',s=>{s.utcMs+=30001;}],
  ['invalid accepted target',s=>{s.lat=null;},false]
])test('refined withdrawal retires obsolete preview ownership: '+name,()=>{
  const current=initial();change(current);const h=fixture(current,{hasTerrain});
  assert.equal(h.preview.previewFrame.current(),false,'negative input reaches actual currentness predicate');
  h.withdraw();
  assert.equal(h.classes.has('real-sky-composed'),false);
  assert.equal(h.detailVisible,false,'obsolete refined atmosphere cannot remain on the Moon');
  assert.equal(h.classes.has('real-sky-preview-ready'),false,'invalid preview must not become the visible owner or hide the current SVG Moon');
  assert.equal(h.preview.canvas.style.visibility,'hidden');
  assert.equal(h.classes.has('moon-ready'),hasTerrain,'sky withdrawal neither invents nor revokes independent terrain authority');
});

test('withdrawal cannot expose a preview-ready flag without a corresponding frame',()=>{
  const h=fixture(initial(),{hasPreview:false});h.withdraw();
  assert.equal(h.classes.has('real-sky-preview-ready'),false);
});

for(const ageMs of [0,30000])test(`a current preview retains its own visible detail at age${ageMs} when refined sky withdraws`,()=>{
  const current=initial();current.utcMs+=ageMs;
  const h=fixture(current,{detailOwner:'atmospheric-preview'});assert.equal(h.preview.previewFrame.current(),true);h.withdraw();
  assert.equal(h.classes.has('real-sky-preview-ready'),true);
  assert.equal(h.preview.canvas.style.visibility,'visible');
  assert.equal(h.detailVisible,true,'another sky owner cannot erase a current preview-owned Moon');
});

test('an expired preview-owned Moon is still withdrawn',()=>{
  const current=initial();current.utcMs+=30001;const h=fixture(current,{detailOwner:'atmospheric-preview'});h.withdraw();
  assert.equal(h.classes.has('real-sky-preview-ready'),false);assert.equal(h.detailVisible,false);
});

test('a current preview does not invent unavailable lunar terrain',()=>{
  const h=fixture(initial(),{hasTerrain:false,detailOwner:'atmospheric-preview'});h.withdraw();
  assert.equal(h.classes.has('real-sky-preview-ready'),true);assert.equal(h.classes.has('moon-ready'),false);assert.equal(h.detailVisible,false);
});

test('explicit preview withdrawal still removes its own ready flag and detail',()=>{
  const h=fixture(initial());h.preview.clear('native target invalidated');
  assert.equal(h.classes.has('real-sky-preview-ready'),false);
  assert.equal(h.preview.canvas.style.visibility,'hidden');assert.equal(h.detailVisible,false);
  assert.equal(h.preview.solarPublication.revision,1);assert.equal(h.preview.pendingValue,null);
});
