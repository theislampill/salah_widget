'use strict';
// R0041 (issue 143): phase-direction authority and same-scope presence.
// Drives the UNMODIFIED rig of moon/tests/host.test.cjs (extracted read-only) with the product's own ephemeris
// (moonIllum, src/native/index.html) stepped once per simulated minute, as the native host does, through a census
// interval in which the waxing flag (chi sign) disagrees with the direction of phase-angle motion.
// RED on main 47faae32: one host fallback (and one detail.clear) per minute step; GREEN: none.
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path'),crypto=require('node:crypto');
const root=path.join(__dirname,'../..');
const hostTest=fs.readFileSync(path.join(__dirname,'host.test.cjs'),'utf8');
const a=hostTest.indexOf('function rig('),b=hostTest.indexOf('\n}\n',a)+3;
const rig=new Function('require','__dirname','process','fs','vm','path','crypto','const src=path.join(__dirname,"../src");'+hostTest.slice(a,b)+';return rig;')(require,__dirname,process,fs,vm,path,crypto);
const html=fs.readFileSync(path.join(root,'src/native/index.html'),'utf8');
const s0=html.indexOf('const _RAD=Math.PI/180'),s1=html.indexOf('// Galactic centre',s0);
// The native snapshot (nativeLunarSnapshot) is the product's own producer of fraction, waxing and, after R0041, the
// phase direction. Run it as the reviewed native-lunar-factors test does (astro + scales + clamp + snapshot).
const snapSrc=html.slice(html.indexOf('function nativeLunarSnapshot('),html.indexOf('\nfunction renderMoon('));
const eph={Math,Date};vm.createContext(eph);
vm.runInContext(html.slice(s0,s1)+html.match(/const MOON_SCALE_MIN=.*?;/)[0]+html.match(/const clamp\s*=.*?;/)[0]+snapSrc+';this.moonIllum=moonIllum;this.snapshot=d=>nativeLunarSnapshot(d,24.47,39.61,{});',eph);
function drive({startISO,minutes,jobS=10,up=1}){
 const r=rig({initial:true,diameter:109});let clears=0;const dc=r.detail.clear.bind(r.detail);r.detail.clear=()=>{clears++;dc();};
 let composes=0;r.w.SalahRealSky={compose(){composes++;}};
 const start=Date.parse(startISO);Object.assign(r.state,{timeScale:1,up,utcMs:start});
 const snap=t=>{const il=eph.moonIllum(new Date(t));r.state.fraction=il.fraction;r.state.waxing=il.waxing;const pd=eph.snapshot(new Date(t)).phaseDirection;if(pd!=null)r.state.phaseDirection=pd;};
 snap(start);const worker=r.workers.at(-1);worker.emit({kind:'ready'});const rt=r.w.SalahMoonRuntime;
 let reply=null,last=null,renders=0,results=0,backToBack=0,lastResult=-1e9;
 for(let m=0;m<minutes;m++){snap(start+m*60000);
  for(let q=0;q<240;q++){const now=m*60000+q*250;rt.request();const req=r.request();
   if(req&&req.id!==last){if(now-lastResult<=250)backToBack++;last=req.id;renders++;reply={id:req.id,at:now+jobS*1000,msg:r.response('result')};}
   if(reply&&now>=reply.at&&r.request()?.id===reply.id){reply.msg.diagnostics={kernel:'metric-radial-terrain-wasm-mb1',quality:{status:'empirical-adaptive'}};worker.emit(reply.msg);results++;lastResult=now;reply=null;}
   r.advance(250);r.state.utcMs+=250;}}
 return {renders,results,fallbacks:r.fallbacks,clears,composes,initialRenders:r.initialRenders,backToBack,tier:rt.state.visibleSource};
}
const WINDOWS=[{startISO:'2026-11-24T16:30:00Z',up:1,label:'full Moon 24 Nov 2026'},{startISO:'2027-01-07T19:30:00Z',up:0,label:'new Moon 7 Jan 2027'}];
for(const w of WINDOWS){
 test(`R41-VM ${w.label}: no wrong-way expiry and no detail withdrawal on minute steps`,()=>{
  const o=drive({...w,minutes:30});
  assert.equal(o.fallbacks,0,`host fallbacks ${JSON.stringify(o)}`);
  assert.equal(o.clears,0,`detail.clear() on same-scope steps ${JSON.stringify(o)}`);
  assert.ok(o.renders<=6,`jobs ${o.renders} in 30 min`);
 });
 test(`R41-STV ${w.label}: 70 s jobs still reach the refined tier`,()=>{
  const o=drive({...w,minutes:30,jobS:70});assert.ok(o.results>=1,JSON.stringify(o));assert.equal(o.tier,'refined-terrain',JSON.stringify(o));
 });
}
test('R41-CRR: no back-to-back re-request (intervals and mid-phase controls)',()=>{
 for(const c of [...WINDOWS,{startISO:'2026-11-18T16:30:00Z',up:1},{startISO:'2026-11-23T16:30:00Z',up:1}]){const o=drive({...c,minutes:30});assert.equal(o.backToBack,0,JSON.stringify({c,o}));}
});
test('R41-CTL: normal operation unchanged in a control (job count as on main)',()=>{
 const o=drive({startISO:'2026-11-18T16:30:00Z',minutes:120,jobS:30,up:1});
 assert.equal(o.renders,18,JSON.stringify(o));assert.equal(o.fallbacks,0);assert.equal(o.clears,0);
});
