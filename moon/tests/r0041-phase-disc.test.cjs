'use strict';
// R0041 (issue 143), owner decision of 2026-11-17: the receiver-independent PHASE DISC (moon/src/moon-phase-disc.mjs)
// and its wiring in the Moon runtime (moon-native.mjs initialPresentation).
//  - Pure cases execute the REAL authored units.
//  - Route cases execute the GENERATED, shipped moon/moon-host.js (real receiver, real phase disc, real detail owner)
//    in the UNMODIFIED realm of r0033-recovery.test.cjs (extracted read-only). They include the twins of R33-10 and
//    R33-11: those accepted cases run a rig that does not load the phase-disc unit and stay unamended; the twins assert
//    the SAME receiver-call counts at the same instants in the shipped configuration, where the slot is filled.
//  - Two fault cases use the UNMODIFIED R0033 rig with a counting stub producer.
//  - R41-PD-REPORT reads the NON-ADOPTING observe() path and the authored qaState().moonTruth expression in each state.
// Run: node --test moon/tests/r0041-phase-disc.test.cjs
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path'),crypto=require('node:crypto');
const SRC=path.join(__dirname,'../src'),read=f=>fs.readFileSync(path.join(SRC,f),'utf8');
const r33=fs.readFileSync(path.join(__dirname,'r0033-recovery.test.cjs'),'utf8');
const cut=(from,to)=>{const a=r33.indexOf(from),b=r33.indexOf(to,a);assert.ok(a>=0&&b>a,'rig boundary '+from);return r33.slice(a,b);};
const body=cut('const src=','const boots=')+cut('function realm(){','test(\'R33-13 a construction failure');
const {rig,realm,generated}=new Function('require','__dirname','process','fs','vm','path','crypto','assert',body+';return {rig,realm,generated};')(require,__dirname,process,fs,vm,path,crypto,assert);
const native=read('moon-native.mjs'),unit=read('moon-phase-disc.mjs');
const BOUND=.0416;
const PROFILE={schema:'lunar-presentation/5',profile_id:'calendar-neutral-v5-01',mode:'calendar',exposure:2.9195482731525044,lift:0.003,knee:5.388411226362526e-6,colour_basis:'linear-sRGB',gamut:'luminance-preserving-neutral-axis'};

// ---- pure units ------------------------------------------------------------------------------------------------
let pureApi=null;
function pure(){
 if(pureApi)return pureApi;
 const c=vm.createContext({performance:{now:()=>0},Float32Array,Float64Array,Uint8Array,Uint8ClampedArray,Uint16Array,Uint32Array,DataView,Math,JSON});
 vm.runInContext(['asset-digest.mjs','surface_v5.mjs','moon-detail.mjs','moon-calendar.mjs','moon-initial.mjs','moon-precision.mjs','moon-phase-disc.mjs'].map(read).join('\n'),c);
 return pureApi=vm.runInContext('({createInitialMoon,renderPhaseDisc,nativeCalendarMoonScene,phaseQuantum,canonicalFraction,assetDigest,PHASE_DISC_MATERIAL,blendCalendarBytes})',c);
}
function sceneFor(api,f,waxing,patch={}){
 const D=104,s={fraction:f,waxing,timeScale:1,phaseDiameter:D,maximumPhaseDiameter:Math.ceil(D*1.13/1.11),phaseQuantum:api.phaseQuantum(D),physicalFraction:api.canonicalFraction(f,D)};
 return {...api.nativeCalendarMoonScene(s,PROFILE),...patch};
}
const Y=(d,i)=>.2126*d[i]+.7152*d[i+1]+.0722*d[i+2];
let realReceiver=null;
function receiver(api){
 if(realReceiver)return realReceiver;
 const bytes=new Uint8Array(fs.readFileSync(path.join(__dirname,'../assets/initial-receivers.bin'))),pin=JSON.parse(fs.readFileSync(path.join(__dirname,'../initial-manifest.json'),'utf8'));
 return realReceiver={bytes,pin,moon:api.createInitialMoon(bytes,{schema:pin.schema,size:pin.size,records:pin.records,bytes:pin.bytes,sha256:pin.sha256})};
}

test('R41-PD-SRC: the phase disc is a producer only; adopt() stays the one setter; no legacy Moon',()=>{
 const code=unit.replace(/\/\*[\s\S]*?\*\//g,'').replace(/^\s*\/\/.*$/gm,'');
 for(const banned of ['window','document','SalahMoon','initialRetry','Worker','classList','.style','Date','setTimeout','requestAnimationFrame','fetch(','_mAlb','MOON_ALBEDO','renderMoonCalendarFallback'])assert.ok(!code.includes(banned),'the producer must not reference '+banned);
 const sets=[...native.matchAll(/calendarBytes=([^;,]+)/g)].map(m=>m[1]);
 assert.deepEqual([...new Set(sets)].sort(),['m.calendarRgba','null'].sort(),'calendar bytes are still set only in adopt() from an adopted message');
 assert.equal((native.match(/\baccepted=\{/g)||[]).length,1,'one place creates an accepted record: adopt()');
 assert.equal((native.match(/renderPhaseDisc\(/g)||[]).length,1,'the phase disc is produced in one place (phaseDiscPresentation)');
 assert.equal((native.match(/SalahMoonInitial\.render\(/g)||[]).length,1,'the receiver still renders in one place');
 assert.ok(!/renderMoonCalendarFallback|SalahMoonLegacy|legacyFallback=true/.test(native+unit),'the deprecated legacy Moon is never a producer');
 // The R0033 M2 budget constants and the bound are untouched.
 assert.match(native,/initialRetry\.notBefore=capturedAt\+60000;initialRetry\.state=initialRetry\.count>=3\?'exhausted':'waiting';/);
 assert.match(read('moon-precision.mjs'),/const PHASE_POSITION_BUDGET=\.0416;/);
 // The head is not wired to the phase disc, and a construction failure still gives it nothing (R0033 DG-1 = B).
 assert.match(fs.readFileSync(path.join(__dirname,'../moon-host.js'),'utf8'),/const moonHeadInitial=moonConstructionError\?null:window\.SalahMoonInitial;/);
});

test('R41-PD-ALB: the uniform material is the disc mean of the accepted receiver material, not an invented tone',()=>{
 const api=pure(),{bytes}=receiver(api),view=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength),N=view.getUint16(4,true);
 let at=6+Math.ceil(N*N/8),n=0;const sum=[0,0,0];
 for(let i=0;i<N*N;i++)if(bytes[6+(i>>3)]&(1<<(i&7))){for(let k=0;k<3;k++)sum[k]+=view.getUint16(at+10+k*2,true)/65535;n++;at+=20;}
 assert.equal(n,196435);
 for(let k=0;k<3;k++)assert.ok(Math.abs(sum[k]/n-api.PHASE_DISC_MATERIAL[k])<=5e-7,`channel ${k}: ${sum[k]/n} vs ${api.PHASE_DISC_MATERIAL[k]}`);
});

test('R41-PD-LAW: the phase disc is the accepted V5 initial operator applied to a smooth uniform sphere',()=>{
 // A synthesised receiver file for a featureless sphere (uniform material, no terrain horizon) is admitted by the REAL
 // createInitialMoon; its render must equal the phase disc up to the receiver's own float32/int16 quantisation.
 const api=pure(),N=128,D=384400,R=1737.4,half=1.08*R/Math.sqrt((D-R)*(D+R)),maskBytes=Math.ceil(N*N/8),cells=[];
 for(let y=0;y<N;y++)for(let x=0;x<N;x++){const u=2*(x+.5)/N-1,v=1-2*(y+.5)/N,k2=half*half*(u*u+v*v),q=D*D-(1+k2)*(D*D-R*R);if(q<0)continue;
  const t=(D-Math.sqrt(q))/(1+k2);cells.push([y*N+x,D-t,t*u*half,t*v*half]);}
 const bytes=new Uint8Array(6+maskBytes+20*cells.length),view=new DataView(bytes.buffer);view.setUint32(0,0x31494d53,true);view.setUint16(4,N,true);
 cells.forEach(([i,px,py,pz],r)=>{bytes[6+(i>>3)]|=1<<(i&7);const at=6+maskBytes+20*r;view.setFloat32(at,px,true);
  [px,py,pz].forEach((p,k)=>view.setInt16(at+4+2*k,Math.round(32767*p/R),true));
  for(let k=0;k<3;k++)view.setUint16(at+10+2*k,Math.round(65535*api.PHASE_DISC_MATERIAL[k]),true);view.setUint16(at+16,65535,true);view.setUint16(at+18,65535,true);});
 const smooth=api.createInitialMoon(bytes,{schema:'moon-initial-receivers/1',size:N,records:cells.length,bytes:bytes.length,sha256:api.assetDigest(bytes)});
 for(const [f,waxing] of [[.08,true],[.5,false],[.93,true]]){
  const scene=sceneFor(api,f,waxing,{size:N}),a=smooth.render(scene),b=api.renderPhaseDisc(scene);
  assert.deepEqual(Array.from(b.surfaceCoverage),Array.from(a.surfaceCoverage),'identical silhouette');
  let max=0,sum=0,lit=0;for(let i=0;i<a.surfaceLinear.length;i++){const d=Math.abs(a.surfaceLinear[i]-b.surfaceLinear[i]);max=Math.max(max,d);sum+=d;if(b.surfaceLinear[i]>.02)lit++;}
  assert.ok(lit>300,'the comparison is not vacuous: lit samples '+lit);
  assert.ok(sum/a.surfaceLinear.length<2e-4,`f=${f}: mean linear difference ${sum/a.surfaceLinear.length}`);
  assert.ok(max<.02,`f=${f}: maximum linear difference ${max} (int16 normals at the terminator)`);
  // Display codes, where the pixel has coverage (the colour under a near-zero alpha at the limb is prefix-sum noise).
  let codes=0,judged=0;for(let i=0;i<a.rgba.length;i+=4){assert.equal(a.rgba[i+3],b.rgba[i+3],'alpha');if(a.rgba[i+3]<32)continue;judged++;for(let k=0;k<3;k++)codes=Math.max(codes,Math.abs(a.rgba[i+k]-b.rgba[i+k]));}
  assert.ok(judged>60000&&codes<=2,`f=${f}: display codes differ by at most the quantisation (${codes} over ${judged} pixels)`);
 }
});

test('R41-PD-GEO / R41-PD-OPQ: same scene as the receiver, correct lit side, opaque disc, same terminator and overall brightness',()=>{
 const api=pure(),{moon}=receiver(api);
 for(const [f,waxing] of [[.3,true],[.72,false]]){
  const scene=sceneFor(api,f,waxing),v5=moon.render(scene),pd=api.renderPhaseDisc(scene),N=pd.surfaceSize;
  assert.equal(pd.kind,'phase-disc');assert.equal(JSON.stringify(pd.scene),JSON.stringify(v5.scene),'the scene the receiver would have been given');
  assert.equal(pd.width,v5.width);assert.equal(pd.surfaceSize,v5.surfaceSize);assert.equal(pd.surfaceExtent,v5.surfaceExtent);
  // Opacity: binary coverage, complete inside the limb, lit or dark; alpha complete; calendar alpha equals surface alpha.
  let inside=0,covered=0;for(let y=0;y<N;y++)for(let x=0;x<N;x++){const a=pd.surfaceCoverage[y*N+x];assert.ok(a===0||a===1);covered+=a;
   if(Math.hypot(2*(x+.5)/N-1,1-2*(y+.5)/N)<1/1.08-2/N){inside++;assert.equal(a,1,'hole inside the limb');}}
  assert.ok(inside>190000&&covered>=inside);
  const M=pd.width;let opaque=0;for(let y=0;y<M;y++)for(let x=0;x<M;x++){const i=4*(y*M+x);assert.equal(pd.calendarRgba[i+3],pd.rgba[i+3]);
   if(Math.hypot(x+.5-M/2,y+.5-M/2)<143){opaque++;assert.equal(pd.rgba[i+3],255,'transparent pixel inside the disc');}}
  assert.ok(opaque>60000);assert.doesNotThrow(()=>api.blendCalendarBytes(pd.rgba,pd.calendarRgba,.5));
  // Lit side follows waxing (right when waxing), as on the receiver.
  const half=(img,right)=>{let s=0;for(let y=0;y<M;y++)for(let x=right?M/2:0;x<(right?M:M/2);x++)s+=Y(img,4*(y*M+x));return s;};
  assert.equal(half(pd.rgba,true)>half(pd.rgba,false),waxing);assert.equal(half(v5.rgba,true)>half(v5.rgba,false),waxing);
  // Terminator: the sunlit boundary agrees with the receiver's in the median over rows (V5's is rugged, this one smooth).
  const edge=r=>{const L=r.surfaceLinear,C=r.surfaceCoverage,out=[];for(let y=Math.round(N*.3);y<=Math.round(N*.7);y+=6){const row=[];for(let x=0;x<N;x++)if(C[y*N+x])row.push([x,Y(L,3*(y*N+x))]);
   const dark=(waxing?row.slice(0,40):row.slice(-40)).map(p=>p[1]).sort((a,b)=>a-b)[20],lit=row.filter(p=>p[1]>Math.max(4*dark,.004));out.push(waxing?lit[0][0]:lit.at(-1)[0]);}return out;};
  const a=edge(v5),b=edge(pd),d=a.map((x,i)=>b[i]-x).sort((p,q)=>p-q);assert.ok(Math.abs(d[d.length>>1])<=1,'median sunlit-boundary offset in surface cells: '+d[d.length>>1]);
  // Overall brightness: mean disc luminance within 6 display codes of the receiver tier, lit and below-horizon token.
  const mean=img=>{let s=0,n=0;for(let i=0;i<img.length;i+=4)if(img[i+3]>=128){s+=Y(img,i);n++;}return s/n;};
  assert.ok(Math.abs(mean(pd.rgba)-mean(v5.rgba))<6,`lit mean step ${mean(pd.rgba)-mean(v5.rgba)}`);
  assert.ok(Math.abs(mean(pd.calendarRgba)-mean(v5.calendarRgba))<2,`token mean step ${mean(pd.calendarRgba)-mean(v5.calendarRgba)}`);
  // No lunar detail: along a lit row well inside the disc the luminance is smooth (no markings).
  const y=N>>1,xs=[];for(let x=0;x<N;x++)if(pd.surfaceCoverage[y*N+x]&&Y(pd.surfaceLinear,3*(y*N+x))>.05)xs.push(Y(pd.surfaceLinear,3*(y*N+x)));
  let jump=0;for(let i=6;i<xs.length-6;i++)jump=Math.max(jump,Math.abs(xs[i]-xs[i-1]));assert.ok(xs.length>100&&jump<.02,'a featureless surface: largest neighbour step '+jump);
 }
});

test('R41-PD-ADM: a scene the phase disc cannot represent truthfully is refused, never approximated',()=>{
 const api=pure(),ok=sceneFor(api,.4,true);assert.doesNotThrow(()=>api.renderPhaseDisc({...ok,size:128}));
 for(const [name,patch] of [['reference camera',{mode:'physical-reference'}],['reference profile',{profile:{...PROFILE,mode:'reference',lift:0,profile_id:'unboosted-v5-01'}}],['tilt',{tilt:.1}],['other basis',{basis:[1,0,0,0,1,0,0,0,1]}],
  ['off-plane Sun',{sun:[0,0,1]}],['non-unit Sun',{sun:[.5,.5,0]}],['fraction inconsistent with the Sun',{fraction:.9}],['non-finite fraction',{fraction:NaN}],['no lit-side sense',{waxing:undefined}],['surface size',{size:1024}]])
  assert.throws(()=>api.renderPhaseDisc({...ok,size:128,...patch}),/Phase disc|profile|display/,name);
});

// ---- the shipped bundle ----------------------------------------------------------------------------------------
// state.fraction/waxing/up are the native capture; the page clock and UTC advance together (rate 1).
function boot({decodeFails=false,night=true}={}){
 const {wrapper,tail}=generated(),r=realm();let clock=0;r.c.performance.now=()=>clock;
 if(decodeFails)r.c.atob=()=>{throw new Error('injected receiver decode failure');};
 const state={utcMs:1e6,generation:0,sceneIdentity:'A',fraction:.6,waxing:true,up:1,dpr:1,timeScale:1,paused:false,presentationReady:true,initialWarranted:night},counts={fallbacks:0,publishes:0,clears:0,composes:0,receiver:0};
 const visibility=[],add=r.c.document.addEventListener;r.c.document.addEventListener=(n,f)=>{if(n==='visibilitychange')visibility.push(f);add(n,f);};
 r.w.SalahMoonHost.capture=()=>state.sceneIdentity===null?{...state}:{...state,paused:state.paused||r.c.document.hidden,maximumPresentationRatio:1};
 r.w.SalahMoonHost.fallback=()=>{counts.fallbacks++;};r.w.SalahMoonHost.publish=()=>{if(counts.publishThrows)throw new Error('injected publication failure');counts.publishes++;};
 r.w.SalahRealSky.compose=()=>{counts.composes++;};
 r.run(wrapper);
 const rt=()=>r.w.SalahMoonRuntime,d=r.w.SalahMoonDetail,clear=d.clear.bind(d);d.clear=()=>{counts.clears++;clear();};
 // Wrap the real receiver: count its calls and inject throws, as tools/qa/r0041/witness.cjs does natively.
 const real=r.w.SalahMoonInitial;let throwsLeft=0;
 const wrap=()=>{r.w.SalahMoonInitial={identity:real.identity,render(scene,consume){counts.receiver++;if(throwsLeft!==0){throwsLeft--;throw new Error('injected initial render failure');}return real.render(scene,consume);}};};
 if(real)wrap();
 const advance=ms=>{clock+=ms;state.utcMs+=ms*state.timeScale;};
 const tick=(ms,step=250)=>{for(let t=0;t<ms;t+=step){advance(Math.min(step,ms-t));rt().request();}};
 // Move the phase past the unchanged bound in the same scope (D = 416 device px without a layout rectangle).
 const expire=()=>{const a=Math.acos(2*state.fraction-1)-3*BOUND*2/416;state.fraction=(1+Math.cos(a))/2;advance(250);};
 const setHidden=h=>{r.c.document.hidden=h;visibility.forEach(f=>f());};
 const frames=()=>{const f=[...r.frames.values()];r.frames.clear();f.forEach(g=>g(clock));};
 return {r,rt,state,counts,real,wrap,advance,tick,expire,setHidden,frames,tail,throws:n=>{throwsLeft=n;},removeReceiver(){r.w.SalahMoonInitial=null;},restoreReceiver(){wrap();}};
}
// R0041 G2 (owner decision 2026-11-22): a presented phase disc is disclosed as the renderer-failure fallback it is.
const FALLBACK=/^phase-disc fault fallback, untextured: start-up renderer unavailable \((receiver-missing|receiver-decode-failed|initial-exhausted|initial-waiting|initial-throw)\); uniform sphere with the current phase, no lunar detail$/;
const presented=(b,source)=>{const s=b.rt().state;assert.equal(s.visibleSource,source);assert.equal(s.current,true);assert.ok(b.rt().surface(),'a presented surface');assert.equal(b.rt().presentable,true);return s;};

test('R41-PD-1 (start-up failure: the embedded receiver does not decode): the first presentation is the phase disc; expiry, invalidation and resume keep it',()=>{
 const b=boot({decodeFails:true});assert.match(b.r.w.SalahMoonInitialError,/injected receiver decode failure/);assert.equal(b.r.w.SalahMoonInitial,undefined);
 assert.equal(b.r.w.SalahMoonConstructionError,undefined,'a registered runtime: this is NOT the DG-1 = B construction failure');
 b.rt().request();let s=presented(b,'phase-disc');
 assert.equal(s.initialRetry.state,'permanent');assert.equal(s.initialEligible,false);assert.equal(s.phaseDisc.state,'presented');assert.equal(s.phaseDisc.cause,'receiver-decode-failed');
 assert.equal(s.quality,'phase-disc');assert.equal(s.slot,'presented-fault-fallback');assert.match(s.limitation,FALLBACK);assert.equal(s.legacyFallback,false);assert.equal(b.counts.clears,0);assert.ok(b.counts.composes>=1,'composed in the adopting task');
 assert.ok(Math.abs(s.phasePrecision.signedPositionDrift)<=BOUND+1e-9);assert.equal(s.phasePrecision.maximumPositionErrorDevicePixels,BOUND);
 // Steady state: no re-render per poll.
 const renders=s.phaseDisc.renders;b.tick(5000);assert.equal(b.rt().state.phaseDisc.renders,renders,'never re-rendered per poll');
 // Expiry: the successor for the CURRENT phase is adopted in the same task; nothing is withdrawn first.
 const before=b.rt().state.accepted.scene.fraction,host=b.counts.fallbacks;b.expire();b.rt().request();s=presented(b,'phase-disc');
 assert.notEqual(s.accepted.scene.fraction,before,'never the expired record');assert.equal(s.phaseDisc.renders,renders+1);
 assert.ok(Math.abs(s.phasePrecision.signedPositionDrift)<=BOUND+1e-9);assert.equal(b.counts.clears,0);assert.equal(b.counts.fallbacks,host,'no host withdrawal on expiry');
 // Same-identity invalidation: adopted before anything presented is withdrawn; the host is notified as before.
 b.rt().invalidate('r0041 test');s=presented(b,'phase-disc');assert.equal(b.counts.clears,0);assert.equal(s.phaseDisc.renders,renders+2);
 // Hide withdraws everything (ISM-MOON-019 unchanged); resume presents the phase disc in the resuming task.
 b.setHidden(true);assert.equal(b.rt().surface(),null);assert.equal(b.counts.clears,1);assert.equal(b.rt().state.limitation,null,'hidden is withheld, not a limitation');
 b.advance(1000);b.setHidden(false);presented(b,'phase-disc');assert.equal(b.counts.clears,1);
 // Below the horizon it is the calendar token of the same disc (weight 1); light stays with the native rules.
 b.state.up=0;b.rt().request();assert.equal(b.rt().state.calendarProxyWeight,1);presented(b,'phase-disc');
});

test('R41-PD-2 (missing receiver): removed after a healthy start, the next withdrawal presents the phase disc; a restored receiver replaces it in place',()=>{
 const b=boot();b.rt().request();presented(b,'initial-v5');assert.equal(b.counts.receiver,1);
 b.removeReceiver();b.rt().invalidate('r0041 test');let s=presented(b,'phase-disc');assert.equal(s.phaseDisc.cause,'receiver-missing');assert.equal(b.counts.clears,0);assert.equal(b.counts.receiver,1);
 b.expire();b.rt().request();presented(b,'phase-disc');assert.equal(b.counts.clears,0);
 b.restoreReceiver();b.rt().request();s=presented(b,'initial-v5');assert.equal(s.phaseDisc.state,'idle');assert.equal(b.counts.clears,0,'replaced in place: no withdrawal between the two');assert.equal(b.counts.receiver,2);
});

test('R41-PD-M2a (twin of R33-10, shipped bundle): one receiver throw is re-attempted after 60 s exactly as before; the slot is filled meanwhile',()=>{
 const b=boot();b.throws(1);b.rt().request();
 let s=presented(b,'phase-disc');assert.match(s.initialError,/injected/);assert.equal(s.initialEligible,false);assert.equal(s.initialRetry.state,'waiting');assert.equal(s.phaseDisc.cause,'initial-throw');
 b.tick(59750);assert.equal(b.counts.receiver,1,'never re-attempted per frame/poll (R0033 M2 unchanged)');presented(b,'phase-disc');
 b.tick(500);s=presented(b,'initial-v5');assert.equal(b.counts.receiver,2);assert.equal(s.initialEligible,true);assert.match(s.initialError,/injected/,'the record is retained for diagnostics');
 assert.equal(b.counts.clears,0,'phase disc -> V5 tier in place');
});

test('R41-PD-M2b (twin of R33-10, shipped bundle): an epoch is one eligibility event, three throws exhaust the tier, and the slot is never empty',()=>{
 const b=boot();b.throws(-1);b.rt().request();presented(b,'phase-disc');
 for(let i=0;i<10;i++){b.rt().invalidate('native beginSkyScene');presented(b,'phase-disc');b.rt().request();b.rt().request();presented(b,'phase-disc');}
 assert.equal(b.counts.receiver,3);const s=b.rt().state;assert.equal(s.initialRetry.state,'exhausted');assert.equal(s.initialRetry.count,3);assert.equal(s.phaseDisc.cause,'initial-exhausted');
 b.tick(3600000,5000);assert.equal(b.counts.receiver,3,'exhausted for the page: the budget is not relaxed');assert.equal(b.counts.clears,0);
});

test('R41-PD-M2c (twin of R33-11, shipped bundle): receiver throw plus worker failure: the slot is filled, and both tiers recover as before',()=>{
 const b=boot();b.r.run(b.tail);b.frames();b.frames();assert.equal(b.r.workers.length,1);
 b.throws(1);b.rt().request();b.r.workers[0].onmessage({data:{kind:'boot-error',error:'controlled'}});
 let s=presented(b,'phase-disc');assert.equal(s.status,'unavailable');assert.equal(s.recovery.state,'scheduled');
 b.tick(60250);s=presented(b,'initial-v5');assert.equal(b.counts.receiver,2);assert.equal(b.r.workers.length,2,'and the refinement worker recovered');assert.equal(b.counts.clears,0);
});

test('R41-PD-UP: a validated worker result replaces the phase disc in place (no withdrawal), and the worker is still asked to refine',()=>{
 const b=boot({decodeFails:true});b.r.run(b.tail);b.frames();b.frames();b.rt().request();presented(b,'phase-disc');
 const w=b.r.workers[0];w.onmessage({data:{kind:'ready'}});const job=w.sent.findLast(m=>m.kind==='render');assert.ok(job,'a provisional tier still requests refinement');
 const n=job.scene.size,out=job.scene.outSize,host=b.counts.fallbacks;
 w.onmessage({data:{kind:'result',id:job.id,identity:job.identity,scene:structuredClone(job.scene),width:out,height:out,rgba:new Uint8ClampedArray(out*out*4),calendarRgba:new Uint8ClampedArray(out*out*4),surfaceSize:n,surfaceExtent:job.scene.extent,
  surfaceLinear:new Float32Array(n*n*3),calendarLinear:new Float32Array(n*n*3),surfaceCoverage:new Float32Array(n*n),physicalIdentity:'physical',profileIdentity:'profile',diagnostics:{kernel:'metric-radial-terrain-wasm-mb1',quality:{status:'empirical-adaptive'}}}});
 const s=presented(b,'refined-terrain');assert.equal(b.counts.clears,0);assert.equal(b.counts.fallbacks,host);assert.equal(s.phaseDisc.state,'idle');
 // The phase disc is PROVISIONAL, like the initial tier: after an invalidation presents it again, an ordinary poll (not
 // only the forced one at worker readiness) asks the worker to refine it.
 const jobs=()=>w.sent.filter(m=>m.kind==='render').length;b.rt().invalidate('r0041 test');presented(b,'phase-disc');const before=jobs();
 b.advance(250);b.rt().request();assert.equal(jobs(),before+1,'a presented phase disc still requests refinement');
});

test('R41-PD-ABS: when the information for a truthful Moon is absent nothing is drawn and the limitation is reported',()=>{
 // No accepted native scene (no location / clock): reported.
 let b=boot({decodeFails:true});b.state.sceneIdentity=null;b.rt().request();
 let s=b.rt().state;assert.equal(b.rt().surface(),null);assert.equal(b.rt().presentable,false);assert.match(s.limitation,/no accepted native lunar scene/);assert.equal(s.phaseDisc.renders,0);
 // Non-finite phase: reported, never guessed.
 b=boot({decodeFails:true});b.state.fraction=NaN;b.rt().request();assert.equal(b.rt().surface(),null);assert.match(b.rt().state.limitation,/no accepted native lunar scene/);assert.equal(b.rt().state.phaseDisc.renders,0);
 // A reference view: neither the receiver nor the phase disc may substitute.
 b=boot({decodeFails:true});b.rt().setProfile('reference');b.rt().request();assert.equal(b.rt().surface(),null);assert.match(b.rt().state.limitation,/reference view/);assert.equal(b.rt().state.phaseDisc.renders,0);
 // Withheld is not a limitation: the sky scene is not established, or the Moon is not warranted (day).
 b=boot({decodeFails:true});b.state.presentationReady=false;b.rt().request();assert.equal(b.rt().surface(),null);assert.equal(b.rt().state.limitation,null);assert.equal(b.rt().state.phaseDisc.renders,0);
 b=boot({decodeFails:true,night:false});b.rt().request();assert.equal(b.rt().surface(),null);assert.equal(b.rt().state.limitation,null);assert.equal(b.rt().state.phaseDisc.renders,0);
});

test('R41-PD-FAULT (presenter): a publication fault withdraws truthfully, is reported, and is attempted once per epoch, never per poll',()=>{
 const b=boot({decodeFails:true});b.counts.publishThrows=true;b.rt().request();
 let s=b.rt().state;assert.equal(b.rt().surface(),null);assert.equal(b.rt().presentable,false,'no light without a presented surface');
 assert.equal(s.phaseDisc.state,'failed');assert.match(s.limitation,/phase-disc producer or presenter fault: texture publication failure/);
 const adoptions=s.lastAdoption?.at;b.tick(5000);assert.equal(b.rt().state.lastAdoption?.at,adoptions,'no further attempt in this epoch');
 b.counts.publishThrows=false;b.rt().invalidate('new epoch');b.rt().request();presented(b,'phase-disc');
});

test('R41-PD-FAULT (producer, R0033 rig with a stub): a producer throw is reported once per epoch; a result that no longer matches is never adopted',()=>{
 let calls=0;const r=rig({initial:false,deferWorker:true});r.c.renderPhaseDisc=()=>{calls++;throw new Error('injected phase-disc failure');};
 r.rt().request();let s=r.rt().state;assert.equal(r.rt().surface(),null);assert.equal(s.phaseDisc.state,'failed');assert.match(s.limitation,/injected phase-disc failure/);
 // The same report on the non-adopting observe() path (qaState reads this one): the fault text, not absent information.
 {const o=r.rt().observe().state;assert.equal(o.slot,'fault');assert.match(o.limitation,/^phase-disc producer or presenter fault: .*injected phase-disc failure/);assert.doesNotMatch(o.limitation,/no accepted native lunar scene/);}
 r.tick(5000);assert.equal(calls,1,'one attempt per epoch');r.rt().invalidate('new epoch');r.rt().request();r.rt().request();assert.equal(calls,2);
 // The scene moves past the bound while the producer runs: the stale result is rejected, not presented.
 const q=rig({initial:false,deferWorker:true});Object.assign(q.state,{timeScale:1,fraction:.6,waxing:true});
 q.c.renderPhaseDisc=scene=>{const a=Math.acos(2*q.state.fraction-1)-3*BOUND*2/104;q.state.fraction=(1+Math.cos(a))/2;const size=2,out=scene.outSize;
  return {kind:'phase-disc',scene:{...scene,size},width:out,height:out,rgba:new Uint8ClampedArray(out*out*4),calendarRgba:new Uint8ClampedArray(out*out*4),surfaceSize:size,surfaceExtent:scene.extent,surfaceLinear:new Float32Array(size*size*3),calendarLinear:new Float32Array(size*size*3),surfaceCoverage:new Float32Array(size*size),physicalIdentity:'stub',profileIdentity:'profile',diagnostics:{quality:{status:'phase-disc'},totalMs:0}};};
 q.rt().request();assert.equal(q.rt().state.initialRejected,1);assert.equal(q.rt().state.accepted,null,'a record outside the unchanged bound is never adopted');
});

test('R41-PD-ABSENT (R0033 rig, no unit): with no producer installed the accepted behaviour is exactly as before, and it is reported',()=>{
 const r=rig({initial:true,initialThrows:1,deferWorker:true});r.rt().request();const s=r.rt().state;
 assert.equal(r.rt().surface(),null);assert.equal(s.phaseDisc.state,'absent');assert.match(s.limitation,/start-up renderer unavailable \(initial-throw\) and phase-disc producer not installed/);
 {const o=r.rt().observe().state;assert.equal(o.slot,'renderer-unavailable');assert.equal(o.limitation,s.limitation,'observe() reports the same limitation');}
});

test('R41-PD-R33: the DG-1 = B construction-failure state is unchanged; the phase disc cannot run without a runtime',()=>{
 const {wrapper,tail}=generated(),r=realm();r.c.setInterval=()=>{throw Error('controlled interval failure');};
 assert.throws(()=>r.run(wrapper),/controlled interval failure/);
 assert.equal(r.w.SalahMoonRuntime??null,null);assert.equal(r.w.SalahMoonDetail??null,null,'no presenter handle: no Moon of any kind');
 assert.match(r.w.SalahMoonConstructionError,/controlled interval failure/);assert.doesNotThrow(()=>r.run(tail));
});

test('R41-PD-LIGHT: light eligibility is the unchanged presence predicate (R0033 M4): a genuinely presented phase disc carries the light the ephemeris rules grant, and nothing else does (owner decision 2026-11-22, G1; magnitudes in R41-G1-*)',()=>{
 const b=boot({decodeFails:true});b.rt().request();const o=b.rt().observe();
 assert.equal(b.rt().presentable,true);assert.equal(o.current,true);assert.equal(o.wouldPresent,b.rt().presentable,'one predicate');
 assert.match(native,/get presentable\(\)\{if\(disposed\)return false;return presentableAt\(capture\(!!\(accepted\|\|waitingPreview\)\)\);\}/,'the predicate text is unchanged');
});

// ---- the report, on the diagnostic path --------------------------------------------------------------------------
// qaState().moonTruth reads SalahMoonRuntime.observe() only (R0036). observe() asks for no geometry when nothing is
// accepted, so the limitation must not be derived from that null. The moonTruth expression is the authored text of
// src/native/index.html, evaluated over the real runtime's observation.
const authored=fs.readFileSync(path.join(__dirname,'../../src/native/index.html'),'utf8');
const truthText=(()=>{const m=/moonTruth:(\(\(\)=>\{[\s\S]*?\n    \}\)\(\))/.exec(authored);assert.ok(m,'moonTruth expression boundary');return m[1];})();
function moonTruth(b,{alt=20,day=false}={}){
 const o=b.rt().observe(),ready=!!o.current;
 return new Function('moonNow','A','moonSky','window','$','_lastMoonPaint','_pbrReady','return '+truthText)(
  ()=>({frac:b.state.fraction,waxing:b.state.waxing}),{day,moonAltitude:alt,moonGrp:day?0:1,moonDisc:1,moonlightIntensity:alt>-.5?.4:0,moonBeam:alt>-.5?.3:0,moonObservation:null},{alt},
  {SalahMoonRuntime:b.rt(),SalahMoonConstructionError:b.r.w.SalahMoonConstructionError},()=>({classList:{contains:()=>ready}}),null,false);
}
const report=b=>{const before=b.counts.publishes,o=b.rt().observe();assert.equal(b.counts.publishes,before,'observe() publishes nothing');return {slot:o.state.slot,limitation:o.state.limitation,current:o.current};};

test('R41-PD-REPORT: on the observe() path the limitation is reported only when information is absent or a fault occurred; withheld and awaiting states report none',()=>{
 const ABSENT=/no accepted native lunar scene/,AWAIT='awaiting current terrain; no legacy substitution';
 // Awaiting: a night scene before the first presentation (nothing accepted yet).
 let b=boot({decodeFails:true});assert.deepEqual(report(b),{slot:'awaiting',limitation:null,current:false});
 let t=moonTruth(b);assert.equal(t.limitation,null);assert.equal(t.slotState,'awaiting');assert.equal(t.reason,AWAIT);assert.equal(t.displayMode,'surface-unavailable');
 // Day: withheld, not a limitation.
 b=boot({decodeFails:true,night:false});b.rt().request();assert.deepEqual(report(b),{slot:'withheld-day',limitation:null,current:false});
 t=moonTruth(b,{day:true});assert.equal(t.limitation,null);assert.equal(t.slotState,'withheld-day');assert.match(t.reason,/daytime suppression/);
 // Scene pending: withheld.
 b=boot({decodeFails:true});b.state.presentationReady=false;b.rt().request();assert.deepEqual(report(b),{slot:'withheld-scene-pending',limitation:null,current:false});
 assert.equal(moonTruth(b).limitation,null);
 // Presented phase disc, above the horizon: disclosed as the untextured renderer-failure fallback (owner decision
 // 2026-11-22, G2), with its cause; a distinct slot state, display mode and label. Never reported as absent information.
 b=boot({decodeFails:true});b.rt().request();{const r0=report(b);assert.equal(r0.slot,'presented-fault-fallback');assert.equal(r0.current,true);assert.match(r0.limitation,FALLBACK);assert.match(r0.limitation,/receiver-decode-failed/);assert.doesNotMatch(r0.limitation,ABSENT);}
 t=moonTruth(b);assert.match(t.limitation,FALLBACK);assert.equal(t.slotState,'presented-fault-fallback');assert.equal(t.surface.status,'phase-disc');assert.equal(t.surface.visibleSource,'phase-disc');
 assert.equal(t.displayMode,'phase-disc-fault-fallback');assert.equal(t.degraded,'phase-disc fault fallback, untextured');assert.equal(t.reason,t.limitation);assert.equal(t.physicalMoonVisible,true);
 // The healthy V5 tier in the same state reports no degradation at all.
 {const h=boot();h.rt().request();assert.deepEqual(report(h),{slot:'presented',limitation:null,current:true});const th=moonTruth(h);assert.equal(th.displayMode,'physical');assert.equal(th.degraded,null);assert.equal(th.limitation,null);assert.equal(th.reason,null);assert.equal(th.surface.status,'v5-initial');}
 assert.match(t.surface.texture,/uniform sphere.*no lunar terrain or albedo.*receiver-decode-failed/);assert.match(t.earthshine,/uniform material/);
 // The same disc below the horizon: a phase-disc calendar presentation, never called refined.
 b.state.up=0;b.rt().request();t=moonTruth(b,{alt:-10});assert.equal(t.displayMode,'phase-disc-calendar');assert.equal(t.degraded,'phase-disc fault fallback, untextured');assert.match(t.limitation,FALLBACK);assert.match(t.reason,/phase-disc calendar phase/);assert.doesNotMatch(t.reason,/refined/);assert.equal(t.physicalMoonVisible,false);
 // Hidden at night: withheld; the wording is the one main used, not a limitation.
 b.state.up=1;b.setHidden(true);assert.deepEqual(report(b),{slot:'withheld-hidden-or-paused',limitation:null,current:false});
 t=moonTruth(b);assert.equal(t.limitation,null);assert.equal(t.reason,AWAIT);
 assert.equal(t.degraded,null,'nothing presented: nothing degraded to disclose');
 b.setHidden(false);assert.equal(report(b).slot,'presented-fault-fallback');
 // Paused by the native host: withheld.
 b.state.paused=true;b.rt().request();assert.deepEqual(report(b),{slot:'withheld-hidden-or-paused',limitation:null,current:false});b.state.paused=false;
 // Publication fault on the phase-disc path: the fault text, not the absent-information text.
 b=boot({decodeFails:true});b.counts.publishThrows=true;b.rt().request();let r=report(b);
 assert.equal(r.slot,'fault');assert.match(r.limitation,/^phase-disc producer or presenter fault: texture publication failure$/);assert.doesNotMatch(r.limitation,ABSENT);
 t=moonTruth(b);assert.equal(t.slotState,'fault');assert.match(t.reason,/no truthful Moon can be constructed: phase-disc producer or presenter fault: texture publication failure/);
 // Publication fault on the receiver path (healthy receiver): also a fault, named as the presenter's.
 b=boot();b.counts.publishThrows=true;b.rt().request();r=report(b);assert.equal(r.slot,'fault');assert.equal(r.limitation,'presenter fault: texture publication failure');
 // Absent information: no scene identity, and a non-finite phase.
 b=boot({decodeFails:true});b.state.sceneIdentity=null;b.rt().request();r=report(b);assert.equal(r.slot,'information-absent');assert.match(r.limitation,ABSENT);
 t=moonTruth(b);assert.match(t.limitation,ABSENT);assert.match(t.reason,/no truthful Moon can be constructed: no accepted native lunar scene/);
 b=boot({decodeFails:true});b.state.fraction=NaN;b.rt().request();r=report(b);assert.equal(r.slot,'information-absent');assert.match(r.limitation,ABSENT);
 // A reference view.
 b=boot({decodeFails:true});b.rt().setProfile('reference');b.rt().request();r=report(b);assert.equal(r.slot,'reference-view');assert.match(r.limitation,/reference view/);
 // The adopting state getter agrees with the observation in every case above (one report, two readers).
 for(const make of [()=>boot({decodeFails:true,night:false}),()=>{const x=boot({decodeFails:true});x.state.fraction=NaN;return x;},()=>boot({decodeFails:true})]){
  const x=make();x.rt().request();const o=x.rt().observe().state,s=x.rt().state;assert.equal(o.slot,s.slot);assert.equal(o.limitation,s.limitation);}
});

// ---- Owner decisions of 2026-11-22 (G1, G2, G8) and review 3 advisories (R3-1, R3-2) ----------------------------
// The native light chain is the AUTHORED text of src/native/index.html (nativeLunarPresentation, lunarPresentation,
// moonSurfacePresentable), evaluated over the real runtime of the shipped bundle.
const lightText=(()=>{const a=authored.indexOf('function nativeLunarPresentation('),z=authored.indexOf('// Presentability also changes outside render()',a);assert.ok(a>0&&z>a,'native light boundary');return authored.slice(a,z);})();
const clamp=(x,a=0,b=1)=>Math.max(a,Math.min(b,x));
function nativeLight(runtime,{frac=.6,alt=30,solar=-30}={}){
 const lunarPresentation=new Function('clamp','moonSky','window','$','_skySceneKey',lightText+';return lunarPresentation;')(clamp,{frac,alt},{SalahMoonRuntime:runtime},()=>({getAttribute:()=>'data:published'}),'scene');
 return lunarPresentation(solar);
}
// moonTruth with the light the native chain grants for this runtime state (A.moonBeam is 0.6 x moonlight natively).
function truthWithLight(b,scene){
 const L=nativeLight(b.rt(),scene),o=b.rt().observe(),ready=!!o.current,{frac=.6,alt=30,solar=-30}=scene??{};
 const t=new Function('moonNow','A','moonSky','window','$','_lastMoonPaint','_pbrReady','return '+truthText)(
  ()=>({frac,waxing:true}),{day:solar>-3,moonAltitude:alt,moonGrp:1,moonDisc:1,moonlightIntensity:L.moonlight,moonBeam:.6*L.moonlight,moonObservation:null},{alt},
  {SalahMoonRuntime:b.rt()},()=>({classList:{contains:()=>ready}}),null,false);
 return {L,t};
}

test('R41-G1-NOLIGHT: no moonlight when the phase disc is not genuinely presented (hidden, paused, withheld, fault with an empty slot, absent information)',()=>{
 const none=(b,why)=>{const {L,t}=truthWithLight(b);assert.equal(b.rt().presentable,false,why);assert.equal(L.moonlight,0,why);assert.equal(L.moonLightEligible,false,why);assert.equal(L.moonLightReason,'surface-unavailable',why);
  assert.equal(L.moonGlow,0,why);assert.equal(L.moonLocalWash,0,why);assert.equal(t.moonlightOpacity,0,why);assert.equal(t.physicalMoonVisible,false,why);};
 // Control: the same scene with the phase disc presented carries light, so the zeros below are not vacuous.
 let b=boot({decodeFails:true});b.rt().request();presented(b,'phase-disc');assert.ok(truthWithLight(b).L.moonlight>0);assert.ok(truthWithLight(b).t.moonlightOpacity>0);
 b.setHidden(true);none(b,'hidden');b.setHidden(false);presented(b,'phase-disc');
 b.state.paused=true;b.rt().request();none(b,'paused');b.state.paused=false;
 b=boot({decodeFails:true});b.state.presentationReady=false;b.rt().request();none(b,'scene pending');
 b=boot({decodeFails:true,night:false});b.rt().request();none(b,'not warranted');
 b=boot({decodeFails:true});b.counts.publishThrows=true;b.rt().request();assert.equal(b.rt().observe().state.slot,'fault');none(b,'publication fault, empty slot');
 b=boot({decodeFails:true});b.state.fraction=NaN;b.rt().request();none(b,'absent information');
 b=boot({decodeFails:true});none(b,'awaiting: nothing presented yet');
 const r=rig({initial:false,deferWorker:true});r.c.renderPhaseDisc=()=>{throw new Error('injected phase-disc failure');};r.rt().request();
 assert.equal(r.rt().presentable,false);assert.equal(nativeLight(r.rt()).moonlight,0,'producer fault, empty slot');
});

test('R41-G1-RULES: under a presented phase disc the ordinary ephemeris, horizon, phase and darkness rules still decide: new or below-horizon Moon and daylight give moonlightOpacity 0',()=>{
 const b=boot({decodeFails:true});b.rt().request();presented(b,'phase-disc');
 for(const [scene,reason] of [[{frac:.01,alt:30,solar:-30},'near-new'],[{frac:.02,alt:30,solar:-30},'near-new'],[{frac:.6,alt:-10,solar:-30},'below-horizon'],[{frac:.6,alt:-2,solar:-30},'below-horizon'],[{frac:.6,alt:30,solar:10},'daylight'],[{frac:.6,alt:30,solar:-3},'daylight']]){
  const {L,t}=truthWithLight(b,scene);assert.equal(L.moonlight,0,reason);assert.equal(L.moonLightEligible,false,reason);assert.equal(L.moonLightReason,reason);assert.equal(t.moonlightOpacity,0,reason);assert.equal(t.physicalMoonVisible,false,reason);
  assert.notEqual(t.displayMode,'phase-disc-fault-fallback','no physical label without light: '+reason);}
 const {L,t}=truthWithLight(b,{frac:.6,alt:30,solar:-30});assert.equal(L.moonLightReason,'eligible');assert.ok(t.moonlightOpacity>0);
});

test('R41-G1-NEVERMORE: a renderer failure never raises illumination: for the same instant the phase disc grants exactly the light the V5 tiers grant, and an empty slot grants none',()=>{
 const disc=boot({decodeFails:true});disc.rt().request();presented(disc,'phase-disc');
 const v5=boot();v5.rt().request();presented(v5,'initial-v5');
 const refined=boot();refined.r.run(refined.tail);refined.frames();refined.frames();refined.rt().request();
 {const w=refined.r.workers[0];w.onmessage({data:{kind:'ready'}});const job=w.sent.findLast(m=>m.kind==='render'),n=job.scene.size,out=job.scene.outSize;
  w.onmessage({data:{kind:'result',id:job.id,identity:job.identity,scene:structuredClone(job.scene),width:out,height:out,rgba:new Uint8ClampedArray(out*out*4),calendarRgba:new Uint8ClampedArray(out*out*4),surfaceSize:n,surfaceExtent:job.scene.extent,
   surfaceLinear:new Float32Array(n*n*3),calendarLinear:new Float32Array(n*n*3),surfaceCoverage:new Float32Array(n*n),physicalIdentity:'physical',profileIdentity:'profile',diagnostics:{kernel:'metric-radial-terrain-wasm-mb1',quality:{status:'empirical-adaptive'}}}});}
 presented(refined,'refined-terrain');
 const empty=boot({decodeFails:true});empty.counts.publishThrows=true;empty.rt().request();
 let n=0,lit=0;
 for(const frac of [0,.01,.03,.07,.15,.5,.65,.92,1])for(const alt of [-28,-2,-1,0,4,20,60])for(const solar of [-40,-12,-6,-3,0,10]){
  const s={frac,alt,solar},a=nativeLight(disc.rt(),s),b=nativeLight(v5.rt(),s),c=nativeLight(refined.rt(),s),e=nativeLight(empty.rt(),s);n++;if(c.moonlight>0)lit++;
  assert.deepEqual(a,c,'phase disc equals refined: '+JSON.stringify(s));assert.deepEqual(b,c);assert.ok(a.moonlight<=c.moonlight);assert.equal(e.moonlight,0);assert.equal(e.moonGlow,0);}
 assert.ok(n===378&&lit>20,'the grid is not vacuous');
 // Structurally the light chain reads the ephemeris and ONE boolean; it cannot see which producer filled the slot.
 assert.doesNotMatch(lightText,/visibleSource|phaseDisc|phase-disc|limitation|slotState|degraded|initial-v5|observe\(/);
 assert.match(lightText,/function lunarPresentation\(solarElevation\)\{ const presented=moonSurfacePresentable\(\); _moonLightSurface=presented; return nativeLunarPresentation\(moonSky,solarElevation,!presented\); \}/);
 assert.match(lightText,/const moonObject=surfaceFailed\?0:moonUp\*darkness\*phaseVis;/);
});

test('R41-G2-ORDINARY: with V5 material available the phase disc is never rendered or presented: start-up, polling, expiry, invalidation, hide and resume, identity change, below the horizon',()=>{
 const b=boot();b.r.run(b.tail);b.frames();b.frames();
 const never=why=>{const o=b.rt().observe().state;assert.equal(o.phaseDisc.renders,0,why);assert.notEqual(o.visibleSource,'phase-disc',why);assert.notEqual(o.slot,'presented-fault-fallback',why);assert.equal(o.phaseDisc.cause,null,why);};
 b.rt().request();presented(b,'initial-v5');never('start-up');
 b.tick(3000);never('polling');b.expire();b.rt().request();presented(b,'initial-v5');never('expiry');
 b.rt().invalidate('r0041 g2');presented(b,'initial-v5');never('invalidation');
 b.setHidden(true);never('hidden');b.advance(1000);b.setHidden(false);b.rt().request();presented(b,'initial-v5');never('resume');
 b.state.sceneIdentity='B';b.advance(250);b.rt().request();presented(b,'initial-v5');never('identity change');
 b.state.up=0;b.rt().request();presented(b,'initial-v5');never('below the horizon');
 b.tick(61000,1000);never('a minute later');
 const truth=moonTruth(b,{alt:-10});assert.equal(truth.degraded,null);assert.equal(truth.limitation,null);
});

test('R41-G2-V5FIRST: a valid worker record always displaces or pre-empts the phase disc; the phase disc is never an ordinary tier',()=>{
 // Receiver permanently failed, so the phase disc is presented; a validated worker PREVIEW for the current scene
 // replaces it in the message task, and later polls never go back to the phase disc while a V5 record is current.
 const b=boot({decodeFails:true});b.r.run(b.tail);b.frames();b.frames();b.rt().request();presented(b,'phase-disc');
 const w=b.r.workers[0];w.onmessage({data:{kind:'ready'}});const job=w.sent.findLast(m=>m.kind==='render'),n=job.scene.size,out=job.scene.outSize,renders=b.rt().state.phaseDisc.renders;
 const message=kind=>({kind,id:job.id,identity:job.identity,scene:structuredClone(job.scene),width:out,height:out,rgba:new Uint8ClampedArray(out*out*4),calendarRgba:new Uint8ClampedArray(out*out*4),surfaceSize:n,surfaceExtent:job.scene.extent,
  surfaceLinear:new Float32Array(n*n*3),calendarLinear:new Float32Array(n*n*3),surfaceCoverage:new Float32Array(n*n),physicalIdentity:'physical',profileIdentity:'profile',diagnostics:{kernel:'metric-radial-terrain-wasm-mb1',quality:{status:kind==='preview'?'preview':'empirical-adaptive'}}});
 w.onmessage({data:message('preview')});let s=presented(b,'terrain-preview');assert.equal(s.slot,'presented');assert.equal(s.limitation,null);assert.equal(b.counts.clears,0,'in place');
 b.tick(2000);s=presented(b,'terrain-preview');assert.equal(s.phaseDisc.renders,renders,'a current V5 record is never replaced by the phase disc');
 w.onmessage({data:message('result')});presented(b,'refined-terrain');b.tick(2000);s=presented(b,'refined-terrain');assert.equal(s.phaseDisc.renders,renders);assert.equal(s.slot,'presented');
 // Structure: one call site of the producer, reached only with a renderer-failure cause and nothing current; the
 // worker cannot emit a phase disc; a presented phase disc is provisional (initial), so refinement is always requested.
 assert.equal(native.match(/renderPhaseDisc\(/g).length,1);assert.equal(native.match(/phaseDiscPresentation\(/g).length,3,'the definition and two guarded calls');
 assert.match(native,/const cause=initialCause\(capturedAt\);\n  if\(cause\)\{if\(!current\)phaseDiscPresentation\(s,cause\);return;\}/);
 assert.match(native,/if\(!presentation\(s\)\)phaseDiscPresentation\(s,'initial-throw'\);/);
 assert.match(native,/return initialEligible\(now\)\?null:'initial-waiting';/);
 assert.match(native,/if\(!\['preview','result'\]\.includes\(m\.kind\)/);
 assert.match(native,/initial:m\.kind==='initial'\|\|m\.kind==='phase-disc',phaseDisc:m\.kind==='phase-disc'/);
 assert.match(native,/if\(matches\(accepted,s\)&&!\(accepted\.initial&&waitingPreview&&matches\(waitingPreview\.record,s\)\)\)return true;/);
 assert.doesNotMatch(read('moon-worker.mjs'),/phase-disc|renderPhaseDisc/);assert.doesNotMatch(read('moon-first-paint.mjs'),/phase-disc|renderPhaseDisc/);
});

// G8 (owner decision 2026-11-22): on restoration the Moon is composed in the event task that clears the pause, never
// in a later frame callback. setVis is the AUTHORED text of src/native/index.html, composed with the shipped bundle;
// the Moon runtime's own visibilitychange listener runs BEFORE it, as in the page (the native pause is still set).
const setVisText=(()=>{const m=/\n  function setVis\(\)\{[\s\S]*?\n(?=  document\.addEventListener\("visibilitychange",setVis\);)/.exec(authored);assert.ok(m,'setVis boundary');return m[0];})();
function nativePause(b,{requestThrows=false}={}){
 const classes=new Set(),log=[],cEl={classList:{contains:k=>classes.has(k),toggle(k,on){on?classes.add(k):classes.delete(k);},add(k){classes.add(k);}}};
 Object.defineProperty(b.state,'paused',{get:()=>classes.has('paused'),enumerable:true,configurable:true});
 const w=requestThrows?{SalahMoonRuntime:{request(){log.push('request');throw new Error('injected Moon fault');}}}:{get SalahMoonRuntime(){return b.rt();}};
 const env={visible:()=>!b.r.c.document.hidden,rebaseCloudMotion(){},cEl,ADVANCING:false,start(){log.push('start');},stop(){log.push('stop');},window:w,updateSkySurface(){log.push('surface');},recordRenderFault(name,e){log.push('fault:'+name+':'+e.message);}};
 return {log,classes,setVis:new Function(...Object.keys(env),setVisText+';return setVis;')(...Object.values(env))};
}
// The event task of a visibility change: every Moon-runtime listener first, then the native host's.
const visibilityTask=(b,n,hidden)=>{b.setHidden(hidden);n.setVis();};

test('R41-G8-1: back/forward restoration and tab resume end their event task with the Moon adopted, published and presentable (no frame callback, no poll)',()=>{
 for(const [label,options,source] of [['healthy receiver',{},'initial-v5'],['receiver decode failure',{decodeFails:true},'phase-disc']]){
  const b=boot(options),n=nativePause(b);n.setVis();assert.deepEqual(n.log,['start'],'boot: nothing resumed, the Moon is not touched');
  b.rt().request();presented(b,source);
  for(const route of ['back/forward','tab']){
   // Leaving: pagehide (the asset owner disposes the refined sky and starts no preview hand-off), then hidden.
   if(route==='back/forward')b.r.w.SalahRealSky=null;
   visibilityTask(b,n,true);assert.equal(b.rt().observe().current,false,label+': hide withdraws (ISM-MOON-019 unchanged)');assert.equal(b.rt().presentable,false);
   b.advance(1000);const publishes=b.counts.publishes,frames=b.r.frames.size;
   // Restoring: the Moon runtime's listener runs while the native pause is still set, and adopts nothing ...
   b.setHidden(false);assert.equal(b.rt().observe().current,false,label+': nothing adopted while the host still reads paused');
   // ... then the native listener clears the pause. END OF THE EVENT TASK: no animation frame and no timer has run.
   n.setVis();
   const o=b.rt().observe();assert.equal(o.current,true,label+' '+route+': adopted in the event task');assert.equal(o.state.visibleSource,source);assert.equal(o.wouldPresent,true);
   assert.equal(b.rt().presentable,true);assert.ok(b.counts.publishes>publishes,'published in the event task');assert.ok(Math.abs(o.state.phasePrecision.signedPositionDrift)<=BOUND+1e-9,'a current record, never the pre-hide one');
   assert.equal(n.log.at(-1),'surface');assert.ok(n.log.lastIndexOf('start')<n.log.length-1,'the frame loop is scheduled before the Moon is touched');
   // The frame callback that used to do this work now finds nothing to do.
   const before=b.counts.publishes,renders=b.counts.receiver+b.rt().state.phaseDisc.renders;assert.ok(b.r.frames.size>=frames);b.frames();
   assert.equal(b.counts.publishes,before,'the backstop frame callback adopts nothing more');assert.equal(b.counts.receiver+b.rt().state.phaseDisc.renders,renders);
  }
 }
});

test('R41-G8-2: the restoration composition is contained and narrow: a Moon fault cannot escape the task or stop the frame loop; boot, hide and a steady visible state do not touch the Moon',()=>{
 const b=boot(),n=nativePause(b,{requestThrows:true});n.setVis();assert.deepEqual(n.log,['start']);
 visibilityTask(b,n,true);assert.deepEqual(n.log,['start','stop'],'hide: no Moon call');
 b.r.c.document.hidden=false;assert.doesNotThrow(()=>n.setVis());assert.deepEqual(n.log.slice(2),['start','request','fault:moon-resume:injected Moon fault']);
 n.setVis();assert.deepEqual(n.log.slice(5),['start'],'already visible: no Moon call');
 // Static: one guarded call, after the loop is (re)started; no prayer symbol in the function.
 assert.match(setVisText,/if\(on\) start\(\); else stop\(\);\n    if\(resumed\)\{ try\{ window\.SalahMoonRuntime\?\.request\(\); updateSkySurface\(\); \}catch\(e\)\{ recordRenderFault\("moon-resume",e\); \} \} \}/);
 assert.match(setVisText,/resumed=on&&!!cEl&&cEl\.classList\.contains\("paused"\)/);
 assert.doesNotMatch(setVisText.replace(/\/\/[^\n]*/g,''),/prayer|timings|countdown|fetch|aladhan/i);
});

test('R41-R3-1: a recovered presenter fault is not reported again while the slot merely awaits its next record',()=>{
 const b=boot();b.counts.publishThrows=true;b.rt().request();
 assert.deepEqual(report(b),{slot:'fault',limitation:'presenter fault: texture publication failure',current:false});
 b.counts.publishThrows=false;b.advance(250);b.rt().request();assert.deepEqual(report(b),{slot:'presented',limitation:null,current:true});
 // A scene identity change, read before the next poll: awaiting, not the old fault.
 b.state.sceneIdentity='B';assert.deepEqual(report(b),{slot:'awaiting',limitation:null,current:false});
 assert.equal(moonTruth(b).reason,'awaiting current terrain; no legacy substitution');
 b.advance(250);b.rt().request();assert.equal(report(b).slot,'presented');
 // A same-scope expiry, read before the next poll: awaiting as well.
 b.expire();assert.deepEqual(report(b),{slot:'awaiting',limitation:null,current:false});
 b.rt().request();assert.equal(report(b).slot,'presented');
 // A fault that is NOT recovered stays reported in its own epoch and stops being reported in the next one.
 b.counts.publishThrows=true;b.rt().invalidate('r3-1');b.rt().request();assert.equal(report(b).slot,'fault');
 b.rt().invalidate('next epoch');assert.deepEqual(report(b),{slot:'awaiting',limitation:null,current:false},'a fault of an earlier epoch is not current');
});

test('R41-R3-2: a phase-disc fault is reported only in the epoch it occurred in (the slot-report epoch guard)',()=>{
 const r=rig({initial:false,deferWorker:true});r.c.renderPhaseDisc=()=>{throw new Error('injected phase-disc failure');};
 r.rt().request();assert.equal(r.rt().observe().state.slot,'fault');
 // invalidate() starts a new epoch and attempts nothing itself; a read before the next poll must not name the old fault.
 r.rt().invalidate('new epoch');let o=r.rt().observe().state;assert.equal(o.slot,'awaiting');assert.equal(o.limitation,null);assert.equal(o.phaseDisc.state,'failed','the record itself is kept for diagnostics');
 r.rt().request();o=r.rt().observe().state;assert.equal(o.slot,'fault','and the new epoch reports its own fault');assert.match(o.limitation,/injected phase-disc failure/);
});
