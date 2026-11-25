'use strict';
// Research transformations and source-state experiments. Never writes product source.
// The accepted lifecycle, currentness and hide contracts are not amended by this tool.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const {pathToFileURL} = require('node:url');
const {harness, record} = require('../../tests/r0003-harness.cjs');
const {SCENARIOS, snapshot, runMatrix} = require('./r002f_a2_resume.cjs');
const {quarantineCandidate} = require('./r002f_a2_quarantine.cjs');
const repo = path.resolve(__dirname, '../..');
const read = name => fs.readFileSync(path.join(repo, name), 'utf8');
const sha = text => crypto.createHash('sha256').update(text).digest('hex');
const plain = x => String(x ?? '').replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim();

function once(source, from, to) {
  if (source.split(from).length !== 2) throw Error('expected unique source owner/anchor: ' + from.slice(0, 90));
  return source.replace(from, () => to);
}
function section(source, start, end) {
  if (source.split(start).length !== 2 || source.split(end).length !== 2) throw Error('expected unique section owners');
  const i = source.indexOf(start), j = source.indexOf(end, i + start.length);
  if (j < i) throw Error('source owner order changed');
  return source.slice(i, j);
}

function prayerOnlyCandidate(source) {
  if (source.includes('function publishRestoredPrayerResearch(')) throw Error('research transform already applied');
  const begin = '  let M=null, prayerPublished=false, modelDone=false;';
  const end = '  runRenderStage("weather-sync",syncWeather);';
  const stage = section(source, begin, end);
  const helper = 'function publishPrayerStageResearch(){\n' + stage + '  return {M,prayerPublished};\n}\n' +
    'function publishRestoredPrayerResearch(){\n' +
    '  _lastRender=null; // prayer publication is not a newly composed sky receipt\n' +
    '  if(!runRenderStage("resume-prayer-day",maintainPrayerDay)){runRenderStage("prayer-withdrawal",withdrawnPrayerStage);return;}\n' +
    '  if(!simulationReady()){runRenderStage("prayer",withdrawnPrayerStage);return;}\n' +
    '  publishPrayerStageResearch();\n}\n';
  let result = once(source, stage, '  const {M,prayerPublished}=publishPrayerStageResearch();\n');
  result = once(result, 'function render(){\n', helper + 'function render(){\n');
  return once(result, 'if(resumed){ try{ window.SalahMoonRuntime?.request(); updateSkySurface(); }catch(e){ recordRenderFault("moon-resume",e); } } }',
    'if(resumed){ runRenderStage("resume-prayer",publishRestoredPrayerResearch); try{ window.SalahMoonRuntime?.request(); updateSkySurface(); }catch(e){ recordRenderFault("moon-resume",e); } } }');
}

function calendarFixture(day) {
  const r = record(day, 'UTC', 'R002F-A2 synthetic calendar');
  const hd = day === '07-09-2026' ? '25' : '26';
  r.date.hijri = {...r.date.hijri, day:hd, date:hd + '-' + String(r.date.hijri.month.number).padStart(2, '0') + '-' + r.date.hijri.year};
  return r;
}
function prayerFixture(source, scenario) {
  const h = harness({source, epoch:scenario.before});
  h.seed(calendarFixture('07-09-2026'), scenario.next === false ? null : calendarFixture('08-09-2026'));
  h.run('var _wxDecisionCache=null;window.__archOptional=0;window.__archMoon=[];window.__archThrow=false;' +
    'window.SalahMoonRuntime={request(){__archMoon.push(document.querySelector(".cn").textContent);if(__archThrow)throw Error("optional Moon fault");},surface(){return null},observe(){return {state:{}}}};' +
    'syncWeather=()=>{__archOptional++;};renderMoon=()=>{__archOptional++;};projectStars=()=>{__archOptional++;};');
  h.run(`window.__stages={restore:0,publisher:0};
    if(typeof publishPrayerStageResearch==='function'){
      const shared=publishPrayerStageResearch,restored=publishRestoredPrayerResearch;
      publishPrayerStageResearch=function(){__stages.publisher++;return shared();};
      publishRestoredPrayerResearch=function(){__stages.restore++;return restored();};
    }`);
  h.run('render();startRenderLoop();');
  return h;
}
const prayerKeys=['Fajr','Sunrise','Dhuhr','Asr','Maghrib','Isha'];
const prayerTimes=['05:00','06:00','12:00','15:30','18:00','19:30'];
// Independent fixture expectations. Progress is the elapsed fraction of the
// current prayer interval. SVG hashes freeze the entire baseline callback output
// in addition to checking its six named markers, next event and sunrise ring.
const prayerGroups={
  fajr:['now on - - - -','2.5%','8a7413d4d7a1eac9df5d4804c9276c3d498a82330e3b07d1c432f08eb200acfc'],
  maghrib:['past past past past now on','1.7%','9a911b8a47794a0569e8ab7a9f045cc0fa96776cdd4c98fb7cd7161d79136775'],
  midnight:['on - - - - now','47.6%','67e0e58b3b8d86bd46fb61c164a0430dfd2aa302874d685fb40de7ac6d5ecf06'],
  'within-prayer':['past past now on - -','3.3%','d56bc95c818202bbd7357d774ec3b8aed61d144dff6d8eac3837c5b82c26fcbc']
};
function expectedGroup(name){
  const [roles,width,arcHash]=prayerGroups[name==='moon-fault'?'fajr':name]??['- - - - - -','',sha('')];
  const role=roles.split(' '),available=!!width;
  return {rows:prayerKeys.map((key,i)=>({key,label:key,time:available?prayerTimes[i]:'—',classes:role[i]==='-'?'p':'p '+role[i]})),
    progressWidth:width,progressVisibility:available?'':'hidden',arcSha256:arcHash,
    markers:available?prayerKeys.map((key,i)=>({key,classes:['dot',role[i]==='on'?'next':'',key==='Sunrise'?'ring':''].filter(Boolean).join(' ')})):[]};
}
function group(h) {
  const html=h.nodes.get('.times').innerHTML,arc=h.nodes.get('.arc').innerHTML;
  return {rows:[...html.matchAll(/<div class="([^"]*)" data-prayer-key="([^"]*)"><b>([^<]*)<\/b><span class="tm">([^<]*)<\/span><\/div>/g)].map(([,classes,key,label,time])=>({key,label,time,classes:classes.trim().split(/\s+/).join(' ')})),
    progressWidth:h.nodes.get('.bar>i').style.width,progressVisibility:h.nodes.get('.bar>i').style.visibility,arcSha256:sha(arc),
    markers:[...arc.matchAll(/<circle class="([^"]+)"[^>]*data-prayer-key="([^"]+)"/g)].map(([,classes,key])=>({key,classes}))};
}
function groupDiff(actual,expected) {
  return Object.keys(expected).filter(k=>JSON.stringify(actual[k])!==JSON.stringify(expected[k]));
}
async function prayerExperiment(source, repeats=5) {
  const candidateSource = prayerOnlyCandidate(source);
  const baseline = await runMatrix({source, repeats});
  const candidate = await runMatrix({source:candidateSource, repeats});
  const details = [];
  for (const s of SCENARIOS) {
    const h = prayerFixture(candidateSource, s);
    h.hide();h.elapse(s.gapMs);h.run('window.__archThrow=' + !!s.moonFault);
    const stages=()=>JSON.parse(h.run('JSON.stringify(__stages)'));
    const entry=stages();
    const before = {optional:h.run('__archOptional') + h.paints.length, timers:h.timers.size, requests:h.requests.length};
    h.show();
    const first = snapshot(h), timers = h.timers.size, requests = h.requests.length;
    const taskEnd=stages(),actual=group(h),expected=expectedGroup(s.name);
    const detail = {scenario:s.name, group:actual, expectedGroup:expected,groupDifferences:groupDiff(actual,expected),
      restoreEntries:taskEnd.restore-entry.restore,publisherEntries:taskEnd.publisher-entry.publisher, optionalCallsDuringReturn:h.run('__archOptional') + h.paints.length - before.optional,
      timerDelta:timers-before.timers, requestsDuringReturn:requests-before.requests, pendingCallbacks:h.frames.size,
      moonSawCurrentPrayer:h.run('__archMoon.at(-1)') === s.expected.current,
      fullRenderReceiptCleared:h.run('_lastRender===null')};
    h.show();
    Object.assign(detail, {repeatRestoreEntries:stages().restore-taskEnd.restore,repeatPublisherEntries:stages().publisher-taskEnd.publisher,repeatedVisibleChangedPrayer:JSON.stringify(first)!==JSON.stringify(snapshot(h)),
      repeatedVisibleAddedRequest:h.requests.length!==requests, repeatedVisibleAddedTimer:h.timers.size!==timers});
    const original = prayerFixture(source,s);
    original.hide();original.elapse(s.gapMs);original.show();await original.frame();
    Object.assign(detail,{baselineCallbackGroupDifferences:groupDiff(group(original),expected),requestCountMatchesBaselineCallback:requests===original.requests.length,
      timerCountMatchesBaselineCallback:timers===original.timers.size,
      requestUrlsMatchBaselineCallback:JSON.stringify(h.requests.map(r=>r.url))===JSON.stringify(original.requests.map(r=>r.url))});
    details.push(detail);
  }
  const h = prayerFixture(candidateSource, SCENARIOS[0]);
  h.hide();h.elapse(120000);
  h.run('model=()=>{throw Error("injected prayer selection failure");};');
  const optional = h.run('__archOptional') + h.paints.length;
  h.show();
  const prayerFault = {...snapshot(h), faults:h.run('_renderFaults.get("prayer")?.count || 0'),
    pendingCallbacks:h.frames.size, optionalCallsDuringReturn:h.run('__archOptional')+h.paints.length-optional, group:group(h)};
  prayerFault.groupDifferences=groupDiff(prayerFault.group,expectedGroup('model-fault'));
  const corrupt=once(candidateSource,'  publishPrayerStageResearch();\n',`  publishPrayerStageResearch();
  if($(".cn").textContent==="Maghrib"){$(".times").innerHTML="";$(".arc").innerHTML="";$(".bar>i").style.width="99.9%";}
`);
  const m=prayerFixture(corrupt,SCENARIOS[1]);m.hide();m.elapse(SCENARIOS[1].gapMs);m.show();
  const groupCorruptionDifferences=groupDiff(group(m),expectedGroup('maghrib'));
  const repeatMutant=once(candidateSource,'if(resumed){ runRenderStage("resume-prayer",','if(on){ runRenderStage("resume-prayer",');
  const duplicate=prayerFixture(repeatMutant,SCENARIOS[0]);duplicate.hide();duplicate.elapse(SCENARIOS[0].gapMs);duplicate.show();
  const duplicateBefore=group(duplicate),entriesBefore=duplicate.run('__stages.publisher');duplicate.show();
  const repeatedPublicationControl={publisherEntries:duplicate.run('__stages.publisher')-entriesBefore,groupChanged:groupDiff(group(duplicate),duplicateBefore).length>0};
  return {sourceSha256:sha(source), candidateSha256:sha(candidateSource), baseline, candidate, details, prayerFault,groupCorruptionDifferences,repeatedPublicationControl,
    scope:'actual prayer publisher and loop in VM; optional rendering, DOM layout and transport are boundary doubles',
    limitations:['Not a native first-frame or dispatch-cost measurement.', 'The restoring task still performs the existing synchronous Moon request after prayer; this does not eliminate its task cost.',
      'Helper extraction is an experimental source transformation, not an accepted production change.']};
}

const mergePreparation=`     let complete=image;
     if(pixels){const bytes=new Uint8ClampedArray(pixels.data);bytes.set(image.data,0);complete=new ImageData(bytes,pixels.width,pixels.height);}
`;
function singleUploadCandidate(source) {
  const fence='    const published=host.capture(false);';
  return once(once(source,fence,mergePreparation+fence),'     if(pixels)ctx.putImageData(pixels,0,0);\n     ctx.putImageData(image,0,0);','     ctx.putImageData(complete,0,0);');
}
async function publicationExperiment() {
  const contract = await import(pathToFileURL(path.join(repo, 'real-sky/native-contract.mjs')));
  const composition = await import(pathToFileURL(path.join(repo, 'real-sky/native-composition.mjs')));
  const state = {utcMs:1000,lat:51,lon:0,heightM:20,sceneIdentity:'research',generation:7,
    camera:{azDeg:0,altDeg:45,fovYDeg:60,rollDeg:0},weather:{src:'fixture',vis:12000,temp:12,cc:0},units:'c',timeScale:1,reducedMotion:false};
  const job = contract.nativeJob(state, true), current = changes => contract.nativeResultCurrent(job, {...state,...changes});
  const currentness = {unchanged:current({}), authorityLost:current({weather:null}),
    visibilityChanged:current({weather:{...state.weather,vis:12001}}),temperatureChanged:current({weather:{...state.weather,temp:13}}),
    generationChanged:current({generation:8}),expired:current({utcMs:31001}),
    sameInputsRenewed:current({utcMs:2000,weather:{...state.weather,srcAt:2000}}),cloudOnlyChanged:current({weather:{...state.weather,cc:90}})};
  const original = read('real-sky/native-preview-host.mjs'), candidate = singleUploadCandidate(original);
  const fixtureSource = read('tests/real-sky/native-preview-host.test.mjs');
  let hostFunction = section(fixtureSource, 'function host({', '\nfunction initialHead(){');
  // The fixture's canvas is a byte array. A selected put fails before any bytes
  // are written, like argument/context rejection; this is not a GPU-loss model.
  hostFunction=once(hostFunction,'putImageData(image){draws.push(now);visiblePixels.set(image.data);}', `putImageData(image){
    uploadControl.count++;
    if(uploadControl.failAt===uploadControl.count)throw Error("injected upload failure");
    uploadControl.writes.push({utcMs:now*timeScale,jobUtc:uploadControl.jobUtc,rows:image.height});
    draws.push(now);visiblePixels.set(image.data);
  }`);
  hostFunction=once(hostFunction,'renderNativeBackgroundPreview(c){','renderNativeBackgroundPreview(c){uploadControl.jobUtc=c.utcMs;uploadControl.frame++;');
  hostFunction=once(hostFunction,'ImageData:class{constructor(data,w,h){','ImageData:class{constructor(data,w,h){if(++uploadControl.images===3)now+=uploadControl.charge;');
  hostFunction=once(hostFunction,'nativeForegroundRows:()=>530,nativeCloudDisplayFrame:x=>x,encodeNativeFrame:()=>{const bytes=rgba.slice();bytes[0]=Math.round(now)%256;return bytes;},',
    'nativeForegroundRows:()=>fixtureRows,nativeCloudDisplayFrame:x=>{const y=x.slice();y[0]=77;y[4]=199;y[y.length-4]=87;return y;},encodeNativeFrame:()=>background(uploadControl.frame),');
  function background(frame) {
    const data=new Uint8ClampedArray(325*530*4);
    for(let i=0;i<data.length;i+=4){const n=i/4;data[i]=(frame*43+n*7)%251;data[i+1]=(frame*31+n*11)%253;data[i+2]=(frame*13+n*17)%249;data[i+3]=255;}
    return data;
  }
  function expected(frame,rows) {
    const bytes=background(frame);
    bytes[0]=77;bytes[4]=199;bytes[rows*325*4-4]=87;
    return bytes;
  }
  const equal=(a,b)=>Buffer.from(a).equals(Buffer.from(b));
  function make(source, failAt=Infinity,fixtureRows=530,timeScale=1,charge=0) {
    const uploadControl = {count:0,failAt,writes:[],images:0,charge,frame:0};
    const s = {source:source.replace(/^import .*;\r?\n/gm,'').replace('export function startNativeSkyPreview','function startNativeSkyPreview'),
      vm, structuredClone,fixtureRows,background,NativeForegroundCapture:composition.NativeForegroundCapture,NativeSolarMaskPublication:composition.NativeSolarMaskPublication,uploadControl};
    vm.createContext(s);vm.runInContext(hostFunction + '\nglobalThis.fixtureHost=host;', s);
    const h = s.fixtureHost({foregroundMs:0,skyMs:1,timeScale});
    return {h,uploadControl};
  }
  function failure(text,failAt){
    const f=make(text,failAt,64),before=f.h.visiblePixels.slice(),utc=f.h.state.utcMs;
    f.h.present(21000,21000);
    return {failedWriteChangedVisibleBytes:!equal(before,f.h.visiblePixels),retainedOldIdentity:f.h.state.utcMs===utc,
      retainedFlag:f.h.state.retained,attempts:f.uploadControl.count};
  }
  function render(text,rows) {
    const f=make(text,Infinity,rows),before=f.h.visiblePixels.slice();
    f.h.present(21000,21000);
    const bytes=f.h.visiblePixels.slice(),boundary=325*rows*4,oracle=expected(2,rows);
    f.h.present(21200,21200);
    return {bytes,checks:{matches:equal(bytes,oracle),headMatches:equal(bytes.subarray(0,boundary),oracle.subarray(0,boundary)),
      tailMatches:equal(bytes.subarray(boundary),oracle.subarray(boundary)),belowRegion:Array.from(bytes.slice(boundary,boundary+4)),
      finalPixel:Array.from(bytes.slice(-4)),tailChanged:!equal(before.subarray(boundary),bytes.subarray(boundary)),
      regionalRows:f.uploadControl.writes.at(-1).rows,regionalTailPreserved:equal(f.h.visiblePixels.subarray(boundary),bytes.subarray(boundary)),
      newBackgroundWrites:f.uploadControl.writes.slice(0,-1).length/2}};
  }
  function expiry(text) {
    const f=make(text,Infinity,64,600,60);
    return {writes:structuredClone(f.uploadControl.writes),allWritesCurrent:f.uploadControl.writes.every(w=>Math.abs(w.utcMs-w.jobUtc)<=30000),
      retries:f.h.state.deadlineRetries,misses:f.h.state.deadlineMisses,ready:f.h.state.status==='ready',recordedAge:f.h.state.publication?.ageMs};
  }
  const misplaced=once(candidate,'bytes.set(image.data,0);','bytes.set(image.data.subarray(0,image.data.length-4),4);');
  const late=once(once(candidate,mergePreparation,''),'     ctx.putImageData(complete,0,0);',mergePreparation+'     ctx.putImageData(complete,0,0);');
  const controls={omittedForeground:render(once(candidate,'bytes.set(image.data,0);',''),64).checks,
    fabricatedBlack:render(once(candidate,'new Uint8ClampedArray(pixels.data)','new Uint8ClampedArray(pixels.data.length).map((_,i)=>i%4===3?255:0)'),64).checks,
    previousTail:render(once(candidate,'new Uint8ClampedArray(pixels.data)','new Uint8ClampedArray(baseBytes??pixels.data)'),64).checks,
    misplacedRegion:render(misplaced,64).checks,latePreparation:expiry(late)};
  const full=render(candidate,530),partial=render(candidate,64);
  return {currentness,baselineUpload:failure(original,4),singleUpload:{...failure(candidate,2),
    successMatchesBaseline:equal(full.bytes,render(original,530).bytes),partialForegroundMatchesBaseline:equal(partial.bytes,render(original,64).bytes),
    omittedForegroundMutantDetected:!controls.omittedForeground.headMatches,visibleUploadsPerNewBackground:full.checks.newBackgroundWrites,
    full:full.checks,partial:partial.checks,expiry:expiry(candidate),controls},
    crossOwnerTransactionProven:false, sourceSha256:sha(original),candidateSha256:sha(candidate),fixtureSha256:sha(fixtureSource),
    scope:'real preview owner and solar-mask publication; numerical renderer, canvas, layout, detail and clock doubles',
    limitations:['A single full upload removes this two-write failure window only; atomic browser/GPU upload is not proved.',
      'Moon detail composition precedes final background publication and can have its own side effects; no cross-owner transaction is claimed.',
      'Expired weather changes accepted authority even when its physical inputs later renew identically. No relaxed currentness or held-weather rule is implemented.']};
}

async function crossOwnerExperiment(){
  const hostFixture=read('tests/real-sky/native-preview-host.test.mjs'),detailFixture=read('tests/real-sky/moon-projection-cache.test.mjs');
  const preview=read('real-sky/native-preview-host.mjs'),candidate=singleUploadCandidate(preview),detail=read('moon/src/moon-detail.mjs');
  const composition=await import(pathToFileURL(path.join(repo,'real-sky/native-composition.mjs')));
  const transfer=await import(pathToFileURL(path.join(repo,'real-sky/native-cloud-transfer.mjs')));
  const {encodeNativeFrame}=await import(pathToFileURL(path.join(repo,'real-sky/native-encoding.mjs')));
  // Reuse the existing real-detail geometry/canvas fixture. The storage and
  // observation hooks below are on the DOM/canvas doubles, outside the owners.
  let detailSetup=section(detailFixture,'function surface(level=1','\nassert.equal(sha(original)');
  detailSetup=once(detailSetup,"s.publishes.push({w:im.width,h:im.height,bytes:Buffer.from(im.data),style:cv.style});",
    "s.publishes.push({w:im.width,h:im.height,bytes:Buffer.from(im.data),style:cv.style});trace('detail-write');");
  detailSetup=once(detailSetup,'s.canvases.push(cv);return cv;',`cv.style=new Proxy(cv.style,{set(target,key,value){target[key]=value;if(key==='visibility'&&ownerReady)trace('detail-visibility');return true;}});
    s.canvases.push(cv);return cv;`);
  detailSetup=once(detailSetup,"vm.runInNewContext(instrumented+", "vm.runInNewContext(source+");
  const detailApi=new Function('vm','Buffer','assert','nativeCloudChannel','validateNativeRGBA','trace',
    'let ownerReady=false;'+detailSetup+';return source=>{const result=instance(source);result.adopt(surface());ownerReady=true;return result;};');
  let setup=section(hostFixture,'function host({','\nfunction initialHead(){');
  setup=once(setup,'const classes=new Set(),draws=[]','const classes=owner.classes,draws=[]');
  setup=once(setup,'putImageData(image){draws.push(now);visiblePixels.set(image.data);}',
    `putImageData(image){
      if(fault==='upload'&&jobUtc===21000){trace('background-rejected');throw Error('controlled preview canvas rejection');}
      draws.push(now);visiblePixels.set(image.data);trace('background-write');
    }`);
  setup=once(setup,'setProperty(){},removeProperty(){}','setProperty(key,value){this[key]=value;trace("mask-style-write");},removeProperty(key){delete this[key];}');
  setup=once(setup,'native:{}};','native:{cloudAuthority:authority.current},cloudAuthority:authority.current};');
  setup=once(setup,"cloudsCurrent:()=>true","cloudsCurrent:receipt=>receipt===authority.current");
  setup=once(setup,'const c={style:{},setAttribute(){}','const c={style:new Proxy({},{set(target,key,value){target[key]=value;if(key==="visibility")trace("preview-visibility");return true;}}),setAttribute(){}');
  setup=once(setup,'add:x=>classes.add(x),remove:x=>classes.delete(x)','add:x=>{classes.add(x);if(x==="real-sky-preview-ready")trace("preview-ready-added");},remove:x=>{const changed=classes.delete(x);if(changed&&x==="real-sky-preview-ready")trace("preview-ready-removed");}');
  setup=once(setup,'vm.createContext(s);vm.runInContext(source',`s.window.SalahMoonDetail=owner.api;
    s.encodeNativeFrame=encode;s.nativeCloudDisplayFrame=cloudFrame;
    s.renderNativeBackgroundPreview=c=>{
      jobUtc=c.utcMs;const width=325,height=530,base=jobUtc===0?.003:authority.current===3?.042:.026;
      const linear=Float64Array.from({length:width*height*3},(_,i)=>base*(1+((i%37)/40)));
      return {job:{utcMs:jobUtc,generation:c.generation},utcMs:jobUtc,quality:'fixture',
        raster:{width,height,effectiveExposure:12,linear,skyBackgroundLinear:linear,fixtureUtc:jobUtc,fixtureAuthority:authority.current,physicalState:{sun:{altDeg:30}}}};
    };
    attach(()=>({pixels:visiblePixels,visible:canvases[0]?.style.visibility==='visible'&&classes.has('real-sky-preview-ready'),
      state:s.window.SalahSkyPreview?.state,frame:s.window.SalahSkyPreview?.frame?.raster.fixtureUtc??null,
      frameAuthority:s.window.SalahSkyPreview?.frame?.raster.fixtureAuthority??null,mask:card.style['--native-sun-cloud-mask']??null,jobUtc}));
    vm.createContext(s);vm.runInContext(source`);
  function arm(text,fault){
    const events=[],authority={current:1};let readHost=null,owner;
    function trace(event){
      if(!readHost||!owner)return;
      const h=readHost(),st=h.state,d=owner.api.state,bytes=owner.s.publishes.at(-1)?.bytes;
      events.push({event,candidateUtc:h.jobUtc,previewFrameUtc:h.frame,authority:authority.current,frameAuthority:h.frameAuthority,receiptAuthority:st?.composition?.cloudAuthority??null,previewReceiptUtc:st?.utcMs??null,
        publicationUtc:st?.publication?.utcMs??null,retained:!!st?.retained,previewVisible:h.visible,
        detailVisible:d.visible,detailOwner:d.skyOwner??null,detailRenders:d.renders,mask:h.mask,
        detailBytes:bytes?sha(bytes):null,backgroundBytes:sha(Buffer.from(h.pixels))});
      if(event==='detail-write'&&fault==='revoke'&&authority.current===2){authority.current=3;trace('cloud-authority-revoked');}
    }
    owner=detailApi(vm,Buffer,assert,transfer.nativeCloudChannel,transfer.validateNativeRGBA,trace)(detail);
    owner.classes.delete('real-sky-composed');owner.classes.delete('real-sky-preview-ready');
    const context={vm,structuredClone,owner,fault,authority,jobUtc:null,trace,attach:read=>{readHost=read;},
      encode:encodeNativeFrame,cloudFrame:transfer.nativeCloudDisplayFrame,NativeForegroundCapture:composition.NativeForegroundCapture,
      NativeSolarMaskPublication:composition.NativeSolarMaskPublication,
      source:text.replace(/^import .*;\r?\n/gm,'').replace('export function startNativeSkyPreview','function startNativeSkyPreview')};
    const h=vm.runInNewContext(setup+'\nhost({foregroundMs:0,skyMs:0,timeScale:1});',context);
    trace('initial-settled');if(fault==='revoke')authority.current=2;h.changeMask();h.present(21000,21000);trace('return-settled');
    return {events,reason:h.state.reason,retries:h.state.deadlineRetries,misses:h.state.deadlineMisses};
  }
  return {owners:{previewSha256:sha(preview),singleUploadSha256:sha(candidate),moonDetailSha256:sha(detail),
    solarMaskModuleSha256:sha(read('real-sky/native-composition.mjs')),previewFixtureSha256:sha(hostFixture),detailFixtureSha256:sha(detailFixture)},
    baselineSuccess:arm(preview,null),singleUploadSuccess:arm(candidate,null),baselineFailure:arm(preview,'upload'),singleUploadFailure:arm(candidate,'upload'),
    baselineRevocation:arm(preview,'revoke'),singleUploadRevocation:arm(candidate,'revoke'),
    scope:'Actual Moon detail adoption, projection, join, encoding and canvas publication run inside the actual preview and solar-mask publication path. Atmospheric fields, canvas storage, layout, native host and decode transport are controlled fixtures. Buffer ordering does not establish a painted frame.'};
}

async function retentionExperiment() {
  const source = read('moon/src/moon-native.mjs');
  const declarations = section(source, ' const scope=s=>', ' function syncTexture(s){');
  const predicates = section(source, ' const clockDiscontinuous=', ' // R0033 M4 presence predicate');
  const s = {epoch:2,clock:{utcMs:1000,now:0,rate:1},performance:{now:()=>1000},PHASE_POSITION_BUDGET:0.0416};
  vm.createContext(s);vm.runInContext(declarations + '\n' + predicates + '\nglobalThis.inspect={scope,matches,phaseError,clockDiscontinuous};',s);
  const fresh = {generation:7,sceneIdentity:'research',fraction:.5,waxing:true,dpr:1,profileMode:'calendar',referenceIdentity:null,
    phaseDiameter:416,utcMs:2000,up:1,paused:false};
  const old = {scope:s.inspect.scope(fresh),epoch:1,scene:{mode:'calendar-canonical',fraction:.5,leadDirection:1}};
  // Re-admission is a hypothetical NEW current-epoch record made only after the
  // unchanged source predicates approve the quarantined geometry. The old epoch
  // itself is never accepted or resurrected.
  const proposed = {...old,epoch:2};
  const variants = [
    ['continuous-short-hide',{}],['same-scope-altitude-change',{up:0}],['changed-generation',{generation:8}],
    ['changed-scene',{sceneIdentity:'elsewhere'}],['changed-ratio',{dpr:2}],['changed-limb',{waxing:false}],
    ['reference-view',{referenceIdentity:'reference'}],['changed-profile',{profileMode:'reference'}],
    ['still-paused',{paused:true}],['clock-discontinuity',{utcMs:5001}],['phase-budget-exceeded',{fraction:.51}]
  ];
  const rows = variants.map(([name,delta]) => {
    const candidate = {...fresh,...delta};
    return {name,reusable:s.inspect.matches(proposed,candidate),phaseErrorPixels:s.inspect.phaseError(proposed,candidate),
      scopeMatches:proposed.scope===s.inspect.scope(candidate),clockContinuous:!s.inspect.clockDiscontinuous(candidate)};
  });
  return {sourceSha256:sha(source),phasePositionBudget:0.0416,existingRecordAfterHideMatches:s.inspect.matches(old,fresh),rows,
    presentationRetained:false,productionMutation:false,
    scope:'actual runtime scope/clock/phase predicates; hypothetical quarantined metadata, no receiver composition',
    limitations:['This evaluates re-admission constraints; it does not implement storage, byte custody, disposal or a public reuse path.',
      'Reuse also needs valid physical/profile identity and receiver bytes at the new adoption boundary; this predicate experiment alone is insufficient.',
      'No current pixels are kept during hide, no elapsed-time grace period is introduced, and no performance saving is measured.']};
}

async function main(args) {
  if(args[0]==='--prepare') {
    const target=args[1];if(!target)throw Error('usage: node tools/qa/r002f_a2_architecture.cjs --prepare <new-directory>');
    const manifest=prepareCandidates(target);console.log(JSON.stringify(manifest));return;
  }
  const output = args[0];
  if (!output) throw Error('usage: node tools/qa/r002f_a2_architecture.cjs <new-output.json>');
  const result = {schema:'r002f-a2-architecture/3',instrumentSha256:sha(fs.readFileSync(__filename)),
    prayer:await prayerExperiment(read('index.html')),preview:await publicationExperiment(),crossOwner:await crossOwnerExperiment(),retention:await retentionExperiment()};
  fs.writeFileSync(path.resolve(output),JSON.stringify(result,null,2)+'\n',{flag:'wx'});
  console.log(JSON.stringify({prayer:{baseline:result.prayer.baseline.summary,candidate:result.prayer.candidate.summary},
    preview:result.preview.baselineUpload,retention:result.retention.rows.map(r=>({name:r.name,reusable:r.reusable}))}));
}
function prepareCandidates(target) {
  const {execFileSync}=require('node:child_process');
  const changes=[['prayer','src/native/index.html',prayerOnlyCandidate],['preview','real-sky/native-preview-host.mjs',singleUploadCandidate],
    ['quarantine','moon/src/moon-native.mjs',quarantineCandidate]].map(([name,file,transform])=>({name,file,before:read(file),after:transform(read(file))}));
  const patches=JSON.parse(execFileSync('python',['-c','import json,sys,difflib\na=json.load(sys.stdin)\nprint(json.dumps(["".join(difflib.unified_diff(x["before"].splitlines(True),x["after"].splitlines(True),fromfile="a/"+x["file"],tofile="b/"+x["file"])) for x in a]))'],
    {input:JSON.stringify(changes),encoding:'utf8',maxBuffer:16*1024*1024}));
  fs.mkdirSync(path.resolve(target),{mode:0o700});
  const manifest={schema:'r002f-a2-research-patches/1',scope:'research only; apply to a disposable checkout and use canonical builders',
    changes:changes.map((c,i)=>{
      fs.writeFileSync(path.join(target,c.name+'.patch'),patches[i],{flag:'wx'});
      return {path:c.file,patch:c.name+'.patch',preimageSha256:sha(c.before),candidateSha256:sha(c.after),patchSha256:sha(patches[i])};
    })};
  fs.writeFileSync(path.join(target,'manifest.json'),JSON.stringify(manifest,null,2)+'\n',{flag:'wx'});return manifest;
}
module.exports = {prayerOnlyCandidate,prayerExperiment,singleUploadCandidate,publicationExperiment,crossOwnerExperiment,retentionExperiment,prepareCandidates};
if (require.main===module) main(process.argv.slice(2)).catch(e=>{console.error('INCOMPLETE: '+e.stack);process.exitCode=2;});
