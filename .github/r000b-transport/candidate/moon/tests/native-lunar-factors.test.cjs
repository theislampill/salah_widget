'use strict';
// Install beside fixtures/reviewed-native-lunar.json in moon/tests/. These are
// source equality and producer-boundary controls, not browser/pixel evidence.
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root=process.env.SALAH_TEST_ROOT?path.resolve(process.env.SALAH_TEST_ROOT):path.resolve(__dirname,'../..'),sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const fixtureBytes=fs.readFileSync(path.join(__dirname,'fixtures/reviewed-native-lunar.json'));
assert.equal(sha(fixtureBytes),'3ac9e4a882790b17a8ad509121f97e7e868b0b5753103ae90cb5444e163b0be4');
const f=JSON.parse(fixtureBytes);assert.equal(f.reviewedCommit,'f0647b44e10c9ce4f80895b52861893c347512fd');
const read=name=>fs.readFileSync(path.join(root,name),'utf8').replace(/\r\n/g,'\n');
const native=read('src/native/index.html'),precision=read('moon/src/moon-precision.mjs'),head=read('real-sky/native-first-paint.mjs');
function between(text,start,end){const a=text.indexOf(start),b=text.indexOf(end,a+start.length);assert.ok(a>=0&&b>a,'source boundary '+start);return text.slice(a,b);}
const astro=between(native,'const _RAD=','// Galactic centre'),phase=between(native,'function moonPhase(','// ---- PBR MOON:');
const scales=native.match(/const MOON_SCALE_MIN=.*?;/)[0],clamp=native.match(/const clamp\s*=.*?;/)[0];
const snapshotSource=between(native,'function nativeLunarSnapshot(','\nfunction renderMoon('),presentationSource=between(native,'function nativeLunarPresentation(','\nfunction lunarPresentation(');
function currentApi(s=snapshotSource,p=presentationSource,q=precision){return Function(astro+phase+scales+clamp+q+s+p+'\nreturn {nativeLunarSnapshot,nativeLunarPresentation,nativeCalendarMoonScene,phaseQuantum,canonicalFraction};')();}
const api=currentApi();
const oldSnapshot=Function('fixedDate','lat','lon','SIM',f.astro+f.phase+f.scales+f.clamp+'\nconst simDate=()=>fixedDate,moonNow=()=>moonPhase(fixedDate);\n'+f.renderMoonBodyBeforeDom+'\nreturn {frac,waxing,alt,H:Hm,up,x,y,scale,transform};');
const oldPresentation=Function('moonSky','_pbrFailed',f.clamp+f.lunarPresentation+'\nreturn lunarPresentation;');
const oldPrecision=Function(f.precision+'\nreturn {phaseQuantum,canonicalFraction};')();
const oldScene=Function(f.precision+'\nconst referenceScene=null,profile=()=>('+JSON.stringify(f.profile)+');\n'+f.scene+'\nreturn scene;')();
const simCases=[{}, {moon:'.01',wax:'0',moonAlt:'-5',moonH:'-140'},{moon:'.08',wax:'1',moonAlt:'20',moonH:'42'},{moon:'.92',wax:'0',moonAlt:'2',moonH:'120'}, {moon:'0',wax:'0',moonAlt:'0',moonH:'0'}, {moon:'1',wax:'1',moonAlt:'85',moonH:'180'}, {moon:'not-a-number',wax:'0',moonAlt:'-5',moonH:'0'}];
test('native lunar factor retains reviewed ephemeris/constants and known-observer geometry',()=>{
 assert.equal(astro,f.astro);assert.equal(phase,f.phase);assert.equal(scales,f.scales);assert.equal(clamp,f.clamp);
 for(const time of ['2026-10-09T00:00:00Z','2026-10-09T12:00:00Z','2026-10-20T03:00:00Z'])for(const observer of [[40.7128,-74.006],[24.47,39.61]])for(const sim of simCases){
  const date=new Date(time),expected=oldSnapshot(date,...observer,sim),actual=api.nativeLunarSnapshot(date,...observer,sim);
  for(const key of Object.keys(expected))assert.deepEqual(actual[key],expected[key],time+' '+JSON.stringify(sim)+' '+key);
  assert.equal(actual.utcMs,date.getTime());assert.equal(actual.valid,[expected.alt,expected.H,expected.frac,expected.up,expected.x,expected.y].every(Number.isFinite));
 }
});
test('pure lunar presentation retains exact twilight/calendar and physical light permissions',()=>{
 for(const sim of simCases.slice(0,-1)){
  const moon=api.nativeLunarSnapshot(new Date('2026-10-09T00:00:00Z'),40.7128,-74.006,sim);
  for(const elevation of [20,0,-3,-4.25,-8,-12])for(const failed of [false,true])assert.deepEqual(api.nativeLunarPresentation(moon,elevation,failed),oldPresentation(moon,failed)(elevation));
 }
});
test('calendar scene and sampled bucket-boundary values equal reviewed phase operator',()=>{
 // This checks source equality near selected numerical bucket boundaries. It
 // does NOT extend forty image cases into continuous photometric qualification.
 for(const diameter of [104,208,416]){
  const quantum=oldPrecision.phaseQuantum(diameter);assert.equal(api.phaseQuantum(diameter),quantum);
  const alphas=[0,quantum*.5-1e-8,quantum*.5+1e-8,quantum*1000.5-1e-8,quantum*1000.5+1e-8,Math.PI-quantum*.5-1e-8,Math.PI-quantum*.5+1e-8,Math.PI];
  for(const alpha of alphas){
   const fraction=(1+Math.cos(alpha))/2,physicalFraction=oldPrecision.canonicalFraction(fraction,diameter);assert.equal(api.canonicalFraction(fraction,diameter),physicalFraction);
   for(const waxing of [false,true])for(const timeScale of [0,1]){
    const s={fraction,physicalFraction,waxing,timeScale,phaseDiameter:diameter,maximumPhaseDiameter:Math.ceil(diameter*1.13/1.11),phaseQuantum:quantum};assert.deepEqual(api.nativeCalendarMoonScene(s,f.profile),oldScene(s));
   }
  }
 }
});
test('reviewed oracle discriminates a displaced slot and changed twilight/phase operators',()=>{
 const displaced=snapshotSource.replace('x=268+hd*1.5','x=269+hd*1.5');assert.notEqual(displaced,snapshotSource);
 const moon=api.nativeLunarSnapshot(new Date('2026-10-09T00:00:00Z'),40.7,-74,simCases[2]);assert.notDeepEqual(currentApi(displaced).nativeLunarSnapshot(new Date(moon.utcMs),40.7,-74,simCases[2]),moon);
 const changedPresentation=presentationSource.replace('solarElevation+3)/9','solarElevation+3)/10');assert.notEqual(changedPresentation,presentationSource);assert.notDeepEqual(currentApi(snapshotSource,changedPresentation).nativeLunarPresentation(moon,-4.25,false),api.nativeLunarPresentation(moon,-4.25,false));
 const changedPrecision=precision.replace('PHASE_POSITION_BUDGET=.0416','PHASE_POSITION_BUDGET=.05');assert.notEqual(changedPrecision,precision);
 const s={fraction:.08,physicalFraction:.08,waxing:true,timeScale:1,phaseDiameter:416,maximumPhaseDiameter:424,phaseQuantum:.0004};assert.notDeepEqual(currentApi(snapshotSource,presentationSource,changedPrecision).nativeCalendarMoonScene(s,f.profile),oldScene(s));
});
const nativeSim=Function('q',between(native,'const SIM = {','\nconst prayers')+'\nreturn SIM;');
const moonKeys=['moon','wax','moonAlt','moonH'],NOW=Date.parse('2026-10-09T00:00:00Z');
function executeHead(source,hash){
 let captured=null,clockReads=0;const cfg={lat:24.47,lon:39.61,tz:'Asia/Riyadh',units:'c',lp:0};
 const window={SalahConfig:{resolve(){return {cfg};}},SalahStarBootstrap:{render(){return {fixture:'catalogue boundary stub'};}},SalahMoonHead:{compose(preview,snapshot,sim){captured={snapshot,sim};return {visible:false};},backgroundRule(){return '.c{/* boundary fixture */}';}}};
 const document={head:{append(){}},createElement(){return {getContext(){return {putImageData(){}};},toDataURL(){return 'data:image/png;base64,fixture';}};}};
 class FixedDate extends Date{static now(){clockReads++;return NOW;}}
 class FixtureImageData{constructor(data,width,height){Object.assign(this,{data,width,height});}}
 const preview=()=>({job:{fixture:true},raster:{linear:new Float64Array(3),effectiveExposure:10,physicalState:{sun:{altDeg:-10}}}}),encode=()=>new Uint8ClampedArray(325*530*4),join=(p,rgba)=>({...p,rgba});
 const stripped=source.replace(/^import .*?;\s*$/gm,'').replace(/\bexport (?=function\b)/g,'');
 Function('window','location','document','Date','devicePixelRatio','matchMedia','ImageData','renderNativeBackgroundPreview','encodeNativeFrame','joinNativeStarPreview',stripped+'\nprepareNativeFirstPaint();')(window,{hash},document,FixedDate,2,()=>({matches:false}),FixtureImageData,preview,encode,join);
 return {captured,clockReads,error:window.SalahFirstPaint?.error};
}
const hashes=['#lat=24.47&lon=39.61','#lat=24.47&lon=39.61&simMoon=.08&simWax=0&simMoonAlt=-5&simMoonH=-142','#lat=24.47&lon=39.61&simMoon=.92&simWax=1&simMoonAlt=20&simMoonH=42','#lat=24.47&lon=39.61&simMoon=0&simWax=0&simMoonAlt=0&simMoonH=0','#lat=24.47&lon=39.61&simMoon=1&simWax=1&simMoonAlt=85&simMoonH=180','#lat=24.47&lon=39.61&simMoon=not-a-number&simWax=0&simMoonAlt=-5&simMoonH=0'];
test('actual head producer maps four forced lunar parameters to native SIM strings',()=>{
 for(const hash of hashes){
  const expected=nativeSim(new URLSearchParams(hash.slice(1))),value=executeHead(head,hash);assert.equal(value.error,undefined);assert.ok(value.captured,'actual prepareNativeFirstPaint must reach compose boundary');assert.equal(value.clockReads,1);assert.equal(value.captured.snapshot.utcMs,NOW);
  for(const key of moonKeys)assert.equal(value.captured.sim[key],expected[key],hash+' '+key);
  assert.deepEqual(api.nativeLunarSnapshot(new Date(NOW),24.47,39.61,value.captured.sim),api.nativeLunarSnapshot(new Date(NOW),24.47,39.61,expected));
 }
});
test('head producer leaves explicit temporal ownership to native without another clock read',()=>{
 for(const suffix of ['&simTime=00:00','&simDate=2026-10-09','&timeScale=0','&timeScale=1800']){const r=executeHead(head,hashes[1]+suffix);assert.equal(r.captured,null);assert.equal(r.clockReads,0);}
});
test('raw parameter regression control fails the native SIM mapping discriminator',()=>{
 const mutant=head.replace(/const sim=\{[\s\S]*?\};/,'const sim=Object.fromEntries(params);');assert.notEqual(mutant,head);
 const value=executeHead(mutant,hashes[1]);assert.ok(value.captured);assert.equal(value.captured.sim.moon,undefined);assert.equal(value.captured.sim.simMoon,'.08');
 assert.notDeepEqual(api.nativeLunarSnapshot(new Date(NOW),24.47,39.61,value.captured.sim),api.nativeLunarSnapshot(new Date(NOW),24.47,39.61,nativeSim(new URLSearchParams(hashes[1].slice(1)))));
});
