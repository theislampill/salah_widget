'use strict';
const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {fixture}=require('./helpers/first-paint-fixture.cjs');
// The genuine producer, encoded asset and decoded pin come from this receiver.
// DOM, background radiance and scheduling retain the labelled lifecycle doubles.
const root=path.resolve(process.env.SALAH_TEST_ROOT||path.join(__dirname,'../..'));
const sourceRoot=root,read=n=>fs.readFileSync(path.join(sourceRoot,n),'utf8');
const python=process.env.SALAH_TEST_PYTHON||(process.platform==='win32'?'python':'python3');
const {pin}=JSON.parse(require('node:child_process').execFileSync(python,
 ['-I','-S','-B',path.join(root,'moon/tests/helpers/initial_bootstrap.py'),root],{maxBuffer:2*1024*1024}));
const encoding=JSON.parse(read('moon/initial-compact-manifest.json'));
const packed=new Uint8Array(fs.readFileSync(path.join(sourceRoot,'moon/assets/initial-compact.bin')));
const units=['asset-digest.mjs','surface_v5.mjs','moon-detail.mjs','moon-calendar.mjs','moon-initial.mjs','moon-initial-compact.mjs'];
const create=Function(units.map(n=>read('moon/src/'+n)).join('\n')+'\nreturn createCompactInitialMoon;')();
const hash=x=>crypto.createHash('sha256').update(new Uint8Array(x.buffer,x.byteOffset,x.byteLength)).digest('hex');
const count=h=>h.log.filter(x=>x==='lunar-render').length;
const make=()=>{const producer=create(packed,encoding,pin);assert(Object.isFrozen(producer)&&Object.isFrozen(producer.identity));return fixture(root,{initialProducer:producer,observerSource:true});};
const report={scope:'Source VM with actual qualified receiver/render data and explicit inherited DOM, atmosphere and scheduling doubles; no native pixels/performance.',sourceRoot:root,cases:[]};
function adopted(h){let value;h.context.SalahMoonDetail.adopt=v=>{value=v;};return ()=>value;}

test('qualified same-target head is adopted without a second initial render',()=>{
 const h=make(),first=h.context.SalahStartupTiming.snapshot().firstValidAdmission;
 assert.equal(count(h),1);const surface=adopted(h),head=h.context.SalahFirstPaint.moon.result;
 h.core();h.poll();assert.equal(count(h),1,'Avoid the native duplicate by reusing the owned admitted head result');
 assert(surface());assert.equal(hash(surface().linear),hash(head.surfaceLinear));assert.equal(hash(surface().calendarLinear),hash(head.calendarLinear));assert.equal(hash(surface().coverage),hash(head.surfaceCoverage));
 assert.equal(h.context.SalahMoonRuntime.state.visibleSource,'initial-v5');
 assert.equal(h.context.SalahMoonRuntime.state.firstInitial.renderMs,null,'Do not label old head work as new native renderer duration');
 assert.equal(h.context.SalahMoonRuntime.state.firstInitial.originalHeadRenderMs,head.diagnostics.totalMs);
 assert.equal(h.context.SalahMoonRuntime.state.firstInitial.initialSource,'head-result-reuse');
 const observer=h.context.SalahStartupTiming.snapshot();assert.equal(observer.firstValidAdmission,first);assert.equal(observer.rejected.length,0);
 const event=observer.events.find(x=>x.kind==='native-adoption');assert(event);assert.equal(event.admissionId,first.admissionId);
 assert.equal(h.context.SalahMoonRuntime.state.accepted.scene.fraction,head.scene.fraction,'Retain the original computed phase');
 report.cases.push({case:'healthy-reuse',renderCalls:count(h),linearSha256:hash(surface().linear),calendarSha256:hash(surface().calendarLinear),firstAdmissionId:first.admissionId});
});

test('public diagnostic buffers and scene cannot mutate the owned handoff',()=>{
 const h=make(),surface=adopted(h),original=h.context.SalahFirstPaint.moon.result;
 const expected={linear:hash(original.surfaceLinear),calendar:hash(original.calendarLinear),coverage:hash(original.surfaceCoverage),fraction:original.scene.fraction};
 original.surfaceLinear.fill(0);original.calendarLinear.fill(0);original.surfaceCoverage.fill(0);original.scene.sun[0]=0;original.scene.profile.exposure=123;
 h.context.SalahFirstPaint.moon.scene.fraction=.001;h.context.SalahFirstPaint.moon.capture.generation=99;
 h.core();h.poll();assert.equal(count(h),1);assert(surface());
 assert.equal(hash(surface().linear),expected.linear);assert.equal(hash(surface().calendarLinear),expected.calendar);assert.equal(hash(surface().coverage),expected.coverage);
 assert.equal(h.context.SalahMoonRuntime.state.accepted.scene.fraction,expected.fraction);
});

for(const change of ['weather','generation','DPR','hash','clock','age','profile','reference','renderer'])test(change+' cannot reuse an ineligible original head result',()=>{
 const h=make();h.core();
 if(change==='weather')h.setWeather({src:'current',cloud:30});
 if(change==='generation')h.setGeneration(1);
 if(change==='DPR')h.setDpr(2);
 if(change==='hash')h.hash('#lat=35&lon=20&tz=UTC');
 if(change==='clock')h.jump(5000);
 if(change==='age')h.advance(30001);
 if(change==='profile')h.context.SalahMoonRuntime.setProfile('reference');
 if(change==='reference')h.context.SalahMoonRuntime.setReferenceScene(null);
 if(change==='renderer'){const previous=h.context.SalahMoonInitial;h.context.SalahMoonInitial={...previous,render:s=>previous.render(s)};}
 const before=count(h);h.poll();
 if(change==='profile')assert.equal(count(h),before,'Reference path stays outside initial calendar rendering');
 else assert.equal(count(h),2,'Ineligible head uses the existing native renderer');
 if(change!=='renderer')assert.equal(h.styles.has('native-first-paint'),false);
 report.cases.push({case:'reject-'+change,renderCalls:count(h),epoch:h.context.SalahMoonRuntime.state.epoch});
});

test('the requested profile still receives ordinary renderer admission instead of old cached data',()=>{
 const h=make();h.core();h.context.MOON_DEFAULT_PROFILE={...h.context.MOON_DEFAULT_PROFILE,exposure:0};
 h.poll();assert.equal(count(h),2);assert(h.context.SalahMoonRuntime.state.initialError);
 assert.equal(h.context.SalahMoonRuntime.state.current,false);
});

test('a later public render cannot mutate the private constructor-coverage copy',()=>{
 const h=make(),surface=adopted(h),head=h.context.SalahFirstPaint.moon.result,expected=hash(head.surfaceCoverage);
 const other=h.context.SalahMoonInitial.render(h.context.SalahFirstPaint.moon.scene);other.surfaceCoverage.fill(0);
 const before=count(h);h.core();h.poll();assert.equal(count(h),before);assert.equal(hash(surface().coverage),expected);
});

test('a changed requested backing-image shape uses the ordinary renderer',()=>{
 const h=make();h.core();const scene=h.context.nativeCalendarMoonScene;
 h.context.nativeCalendarMoonScene=(...args)=>({...scene(...args),outSize:301});
 h.poll();assert.equal(count(h),2);assert.equal(h.context.SalahMoonRuntime.state.accepted.scene.outSize,301);
});

test('a larger measured native phase footprint falls back in the same initial turn',()=>{
 const h=make(),query=h.context.document.querySelector;
 h.context.document.querySelector=sel=>sel==='.mphoto'?{getBoundingClientRect:()=>({width:600,height:600})}:query(sel);
 h.core();h.poll();assert.equal(count(h),2);
 assert.equal(h.context.SalahMoonRuntime.state.current,true);
 assert.equal(h.context.SalahMoonRuntime.state.firstInitial.initialSource||'native-render','native-render');
 assert(h.context.SalahMoonRuntime.state.phasePrecision.targetPositionErrorBound<=.0416);
});

test('same-target native initialization transfers numerical data into its checked current epoch',()=>{
 const h=make();h.core();const cap=h.context.SalahMoonHost.capture;
 h.context.SalahMoonHost.capture=()=>({...cap(),presentationReady:false});
 h.context.SalahMoonRuntime.invalidate('native beginSkyScene');assert(h.styles.has('native-first-paint'));
 const epoch=h.context.SalahMoonRuntime.state.epoch;assert(epoch>0);
 h.context.SalahMoonHost.capture=cap;h.poll();assert.equal(count(h),1);
 assert.equal(h.context.SalahMoonRuntime.state.epoch,epoch);assert.equal(h.context.SalahMoonRuntime.state.current,true);
});

test('epoch revocation after transfer prevents publication of that original result',()=>{
 const h=make();h.core();const owner=h.context.SalahFirstPaintLifecycle;
 if(!owner.takeInitial){h.poll();assert.equal(count(h),2);return;}
 const original=owner.takeInitial;owner.takeInitial=(...args)=>{const result=original(...args);h.context.SalahMoonRuntime.invalidate('control revoked during transfer');return result;};
 h.poll();assert.equal(h.context.SalahMoonRuntime.state.current,false);assert.equal(h.context.SalahMoonRuntime.state.accepted,null);
 owner.takeInitial=original;h.poll();assert.equal(count(h),2);assert.equal(h.context.SalahMoonRuntime.state.current,true);
});

test('preview retirement and repeated reads cannot resurrect or repeatedly reuse transferred data',()=>{
 const h=make();h.core();h.poll();const before=count(h);
 h.preview();assert.equal(h.styles.has('native-first-paint'),false);
 h.context.SalahMoonRuntime.invalidate('explicit later withdrawal');h.poll();assert.equal(count(h),before+1);
 assert.equal(h.context.SalahFirstPaintLifecycle.state.active,false);
});

test('expiry during private ownership copy withdraws head work with its original admission',t=>{
 const h=make();
 // This additional boundary exists only in the proposed ownership path. The
 // old source has no ownership copy, so its already-tested age fence applies.
 if(!h.context.SalahFirstPaintLifecycle.takeInitial){t.skip('Private ownership-copy path is absent from the original source.');return;}
 const before=h.context.SalahStartupTiming.snapshot().firstValidAdmission;
 const clone=h.context.structuredClone;let expired=false;
 h.context.structuredClone=value=>{
  if(value?.visible===true&&value.rgba&&!('result' in value)&&!expired){expired=true;h.advance(30001);}
  return clone(value);
 };
 h.context.prepareNativeFirstPaint();assert(expired);
 assert.equal(h.styles.has('native-first-paint'),false);
 const observer=h.context.SalahStartupTiming.snapshot(),end=observer.events.at(-1);
 assert.equal(observer.firstValidAdmission,before);
 assert.equal(end.kind,'head-work-end');assert.equal(end.admissionId,before.admissionId);
 assert.equal(end.status,'superseded');
 assert.equal(h.context.SalahFirstPaintLifecycle.state.status,'superseded');
});

test.after(()=>{if(process.env.SALAH_REUSE_REPORT)fs.writeFileSync(process.env.SALAH_REUSE_REPORT,JSON.stringify(report,null,2)+'\n');});
