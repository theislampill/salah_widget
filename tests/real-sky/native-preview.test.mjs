import test from 'node:test';
import assert from 'node:assert/strict';
import {nativeJob} from '../../real-sky/native-contract.mjs';
import {renderPhysicalSky} from '../../real-sky/core/src/physical-sky-renderer.mjs';
import {encodeNativeFrame} from '../../real-sky/native-encoding.mjs';
import {nativeSkyPresentation,renderNativeBackgroundPreview,nativeSolarRegistration,nativeAtmosphereFields,nativeCloudSolarLighting} from '../../real-sky/native-preview.mjs';
import {luminanceToSurfaceMagnitude} from '../../real-sky/core/src/sky-background.mjs';
import {physicalSkyState} from '../../real-sky/core/src/sky-state.mjs';

const state=(utc='2026-10-07T15:09:00Z')=>({utcMs:Date.parse(utc),lat:28.5383,lon:-81.3792,heightM:0,generation:2,sceneIdentity:'accepted-Orlando',camera:{azDeg:180,altDeg:45,fovYDeg:90,rollDeg:0},weather:{vis:20000,cloud:60,code:2,temp:72},units:'f',lp:0});
test('accepted daytime preview is blue and readable before catalogue/worker readiness',()=>{
 const p=renderNativeBackgroundPreview(state());
 assert.equal(p.utcMs,state().utcMs);assert.equal(p.native.generation,2);
 assert.equal(p.quality,'physical-background-preview');assert.ok(p.raster.physicalState.sun.altDeg>40);
 const i=(205*325+290)*3,c=encodeNativeFrame(p.raster.linear.slice(i,i+3),p.raster.effectiveExposure);
 assert.ok(c[2]>=150&&c[2]-c[0]>=40,JSON.stringify([...c]));
});
test('preview and refined atmosphere share daylight identity within a display-code bound',()=>{
 for(const stamp of ['2026-10-07T15:09:00Z','2026-10-07T23:10:00Z','2026-10-08T03:30:00Z']){
  const s=state(stamp),j=nativeJob(s,true),p=renderNativeBackgroundPreview(s);
  const raw=renderPhysicalSky([],{...j.options,observer:j.observer,diffuse:null,atmosphere:{...j.options.atmosphere,nightZenithVMag:luminanceToSurfaceMagnitude(.00014)}});
  const fields=nativeAtmosphereFields(raw.physicalState,j.options.atmosphere,j.options.view,j.options.diffuse.residualNight);
  raw.solarAerosolLinear=fields.solarAerosolLinear;raw.solarBackgroundLinear=fields.solarBackgroundLinear;raw.twilightDisplay=fields.twilightDisplay;
  const r=nativeSkyPresentation(raw);
  const a=encodeNativeFrame(p.raster.linear,p.raster.effectiveExposure),b=encodeNativeFrame(r.linear,r.effectiveExposure),errors=[];
  for(let y=20;y<480;y++)for(let x=20;x<305;x++)for(let k=0;k<3;k++)errors.push(Math.abs(a[4*(y*325+x)+k]-b[4*(y*325+x)+k]));
  errors.sort((a,b)=>a-b);assert.ok(errors[Math.floor(errors.length*.99)]<=8,stamp+': '+errors[Math.floor(errors.length*.99)]);
 }
});
test('detached physical solar aerosol lobe is registered to visible Sun',()=>{
 const p=renderNativeBackgroundPreview(state()),reg=nativeSolarRegistration(p.raster);
 assert.ok(reg.active);assert.ok(reg.source.y>200);assert.equal(reg.target.y,40);
 assert.ok(reg.gain(reg.target.x,reg.target.y)>1);assert.ok(reg.gain(reg.source.x,reg.source.y)<1);
 for(let i=0;i<=530;i++)assert.ok(Number.isFinite(reg.gain(20,i))&&reg.gain(20,i)>0);
});

test('solar display registration leaves the non-forward atmospheric wing in camera space',()=>{
 // At this morning geometry both the physical Sun and display body are far
 // from the lower-right view. Relocating the complete HG field used to add
 // warm veiling light here, despite it being outside either forward lobe.
 const p=renderNativeBackgroundPreview(state('2026-10-07T12:12:00Z')),r=nativeSolarRegistration(p.raster);
 assert.equal(r.gain(324,529),1,'non-forward air is background, not a relocated solar glow');
});

test('uniform directional daylight is not vignetted by perspective pixel solid angle',()=>{
 // Independent planar-camera differential solid angle: f/(f²+x²+y²)^1.5.
 // A uniform radiance field must display uniformly; the reference solver's
 // integrated flux remains intact and is not itself a surface-brightness map.
 const w=9,h=9,f=h/2,source=new Float64Array(w*h*3);
 for(let y=0;y<h;y++)for(let x=0;x<w;x++){
  const omega=f/(f*f+(x+.5-w/2)**2+(y+.5-h/2)**2)**1.5;
  for(let k=0;k<3;k++)source[(y*w+x)*3+k]=[.3,.5,1][k]*omega;
 }
 const p=nativeSkyPresentation({width:w,height:h,linear:source,skyBackgroundLinear:source,effectiveExposure:10,nominalExposure:24,physicalState:{sun:{altDeg:45}}},{type:'camera',width:w,height:h,azDeg:180,altDeg:45,fovYDeg:90});
 const a=encodeNativeFrame(p.linear,10),centre=(4*w+4)*4;
 for(let i=0;i<a.length;i+=4)for(let k=0;k<3;k++)assert.ok(Math.abs(a[i+k]-a[centre+k])<=1,`uniform radiance differs at ${i/4}`);
 assert.equal(p.physicalSkyBackgroundLinear,source);
});

test('moving the decorative solar aureole cannot reset the atmospheric exposure meter',()=>{
 const s=state('2026-10-07T12:12:00Z'),j=nativeJob(s,true),p=physicalSkyState(j.observer),f=nativeAtmosphereFields(p,j.options.atmosphere,j.options.view,j.options.diffuse.residualNight),r={width:325,height:530,linear:f.background,skyBackgroundLinear:f.background,solarAerosolLinear:f.solarAerosolLinear,effectiveExposure:24/(1+24*f.mean/.5),nominalExposure:24,physicalState:p};
 const a=nativeSkyPresentation(r,j.options.view,{x:20,y:127}),b=nativeSkyPresentation(r,j.options.view,{x:160,y:260});
 assert.equal(a.displayPresentation.displayExposure,b.displayPresentation.displayExposure,'display-only Sun registration cannot meter the whole sky');
});
test('night display and scientific arrays are preserved; neutral daylight stays neutral',()=>{
 const s=state('2026-10-08T03:30:00Z'),j=nativeJob(s,true),r=renderPhysicalSky([],{...j.options,observer:j.observer,diffuse:null});
 assert.equal(nativeSkyPresentation(r),r);
 const original=new Float64Array([1,1,1]),day={width:1,height:1,linear:original,backgroundLinear:original,stellarLinear:new Float64Array(3),effectiveExposure:1,physicalState:{sun:{altDeg:45}}};
 const shown=nativeSkyPresentation(day);assert.deepEqual(original,new Float64Array([1,1,1]));assert.equal(shown.physicalSkyBackgroundLinear,original);assert.equal(shown.linear[0],shown.linear[1]);assert.equal(shown.linear[1],shown.linear[2]);
});
test('preview refuses missing native identity and invalid accepted geometry',()=>{
 assert.throws(()=>renderNativeBackgroundPreview({...state(),sceneIdentity:null}));
 assert.throws(()=>renderNativeBackgroundPreview({...state(),lat:NaN}));
});

test('twilight atmosphere retains physical direction independently of decorative body presence or placement',()=>{
 const r={width:325,height:530,physicalState:{sun:{altDeg:1,azDeg:180}},atmosphere:{aerosolG:.76}};
 const view={type:'camera',width:325,height:530,azDeg:180,altDeg:45,fovYDeg:90};
 const hidden=nativeSolarRegistration(r,view,{x:20,y:150,presence:0});
 assert.equal(hidden.gain(162.5,520),1,'Physical afterglow must not be gated by decorative body visibility');
 const shown=nativeSolarRegistration(r,view,{x:20,y:150,presence:1});
 assert.equal(shown.gain(20,150),hidden.gain(20,150),'Low-Sun atmospheric afterglow cannot migrate between a decorative corner and physical horizon');
 const twilight=nativeSolarRegistration({...r,physicalState:{sun:{altDeg:-5,azDeg:180}}},view,{x:20,y:150,presence:1});
 assert.equal(twilight.gain(162.5,520),1,'Below-horizon physical twilight is not an attached solar glare layer');
});

test('low-Sun aerosol field cannot be reanchored by moving the decorative disc',()=>{
 for(const altDeg of [-8,-5,-2,0,1,5.5,10]){
  const r={width:325,height:530,physicalState:{sun:{altDeg,azDeg:265}},atmosphere:{aerosolG:.76}};
  const view={type:'camera',width:325,height:530,azDeg:180,altDeg:45,fovYDeg:90};
  const a=nativeSolarRegistration(r,view,{x:20,y:170,presence:1}),b=nativeSolarRegistration(r,view,{x:290,y:170,presence:1});
  for(const [x,y] of [[20,170],[160,520],[300,520]])assert.equal(a.gain(x,y),b.gain(x,y),'Screen anchor changes twilight at '+altDeg);
 }
});

test('cloud lighting follows physical camera direction, including off-camera Sun and azimuth wrap',()=>{
 const s=state('2026-10-07T22:30:00Z'),a=nativeCloudSolarLighting(s);
 assert.ok(a.sun.azDeg>250&&a.sun.azDeg<270);
 assert.ok(a.sample(.9,.2).facing>a.sample(.1,.2).facing,'Sun west of south-facing camera must light the right side');
 assert.ok(a.sample(.5,.2).dx>0,'Rim light must point towards physical Sun, not prayer arc');
 const b=nativeCloudSolarLighting({...s,camera:{...s.camera,azDeg:0}});
 assert.ok(b.sample(.1,.2).facing>b.sample(.9,.2).facing,'Camera rotation must move solar side');
 for(const azDeg of [-.001,.001,179.999,180.001])for(const x of [0,.5,1]){
  const v=nativeCloudSolarLighting({...s,camera:{...s.camera,azDeg}}).sample(x,.2);
  assert.ok(Object.values(v).every(Number.isFinite));
 }
});

test('twilight exposure does not normalize a hundredfold radiance fall into the same bright card',()=>{
 // Independent scene perturbation: same direction/chromaticity, 100x less
 // incoming atmosphere. The reference auto-exposure nearly cancels that fall.
 // The calendar display must retain a visible illumination difference.
 const samples=[100,1].map(level=>{
  const s=new Float64Array([level,level,level]),E=24/(1+24*level/.5);
  const r=nativeSkyPresentation({width:1,height:1,linear:s,skyBackgroundLinear:s,effectiveExposure:E,nominalExposure:24,physicalState:{sun:{altDeg:-5}}});
  return encodeNativeFrame(r.linear,E)[0];
 });
 assert.ok(samples[0]-samples[1]>=40,'Exposure erased falling twilight illumination: '+samples);
});

test('twilight display retains a readable blue component at the published zero B-V civil-twilight reference',()=>{
 // Patat2006 Table1 B=V=11.84 at -5 degrees; this is an existing CP6
 // near-zenith colour reference, not a Florida measurement or horizon colour.
 // The old single-scatter-dominated RGB was brown even when its integrated
 // luminance converged. Assert a directional DISPLAY sample, not a mean frame.
 const p=renderNativeBackgroundPreview(state('2026-10-07T11:03:00Z'));
 const i=(30*325+162)*3,c=encodeNativeFrame(p.raster.linear.slice(i,i+3),p.raster.effectiveExposure);
 assert.ok(c[2]>c[0]+15,'Twilight reference still brown/grey: '+[...c]);
 assert.ok(c[2]>60&&c[2]<180,'Civil twilight either crushed or normalized to daylight: '+[...c]);
});

test('late twilight horizon highlights remain subordinate without darkening open sky',()=>{
 const p=renderNativeBackgroundPreview({...state('2026-10-07T23:40:00Z'),heightM:25,weather:{vis:20000,cloud:0,code:0,temp:24},units:'c'}),r=p.raster;
 const displayY=(x,y)=>{const i=3*(y*325+x);return [0.2126,0.7152,0.0722].reduce((sum,w,k)=>sum+w*(-Math.expm1(-r.effectiveExposure*r.linear[i+k])),0);};
 // Predeclared product-display contrast bound: retain a horizon highlight up
 // to two stops over the adapted field median. It is not a radiance claim.
 // The rejected actual crop is over ten times that median near(280,491).
 const medianDisplay=-Math.expm1(-r.displayPresentation.displayExposure*r.displayPresentation.medianLuminance);
 assert.ok(displayY(280,491)<=4*medianDisplay,'amber pool still dominates the lower sky');
 const i=3*(205*325+30),c=encodeNativeFrame(r.linear.slice(i,i+3),r.effectiveExposure);
 assert.deepEqual([...c],[21,27,46,255],'upper twilight must retain its approved brightness/chroma');
 assert.ok(displayY(280,491)>displayY(30,491),'legitimate directional afterglow is retained');
 assert.ok(r.physicalSkyBackgroundLinear[(491*325+280)*3]>r.skyBackgroundLinear[(491*325+280)*3],'only the display copy is adjusted');
});

test('reported -8.64 degree off-solar horizon crop has no isolated amber display pool',()=>{
 const p=renderNativeBackgroundPreview({...state('2026-10-07T23:40:00Z'),heightM:25,weather:{vis:20000,cloud:0,code:0,temp:24},units:'c'}),r=p.raster;
 // Product chroma bound for this reported off-solar crop, not a physical
 // radiance oracle: amber R-B excess may not dominate cool evening atmosphere.
 // Its rays are over60deg from the Sun; the solar-side view is tested separately.
 for(const [x,y] of [[280,491],[305,515],[250,500]]){
  const i=3*(y*325+x),c=encodeNativeFrame(r.linear.slice(i,i+3),r.effectiveExposure);
  assert.ok(c[0]-c[2]<=8,`Detached amber at ${x},${y}: ${[...c]}`);
 }
});

test('late dusk night adaptation cannot resurrect the raw solar highlight',()=>{
 // Independent temporal negative control from the actual west-facing widget:
 // incoming solar flux falls throughout this interval. The old whole-field
 // blend nevertheless raised the horizon from35/26/14 to134/115/63. Natural
 // night adaptation may lift neutral sky; it must not relight an amber pool.
 let previous=null;
 for(let minute=55;minute<=95;minute++){
  const s={...state(),utcMs:Date.parse('2026-10-07T23:00:00Z')+minute*60000,heightM:25,camera:{...state().camera,azDeg:270},weather:{vis:20000,cloud:0,code:0,temp:24},units:'c'};
  const r=renderNativeBackgroundPreview(s).raster,i=3*(491*325+162),c=[...encodeNativeFrame(r.skyBackgroundLinear.slice(i,i+3),r.effectiveExposure)].slice(0,3);
  const flux=r.solarBackgroundLinear.slice(i,i+3).reduce((v,x,k)=>v+x*[.2126,.7152,.0722][k],0),warm=Math.max(0,c[0]-c[2]);
  if(previous){assert.ok(flux<=previous.flux,'Fixture must have falling physical solar flux');assert.ok(warm<=previous.warm+3,`Amber relighting at ${r.physicalState.sun.altDeg}: ${previous.c} -> ${c}`);assert.ok(Math.max(...c.map((v,k)=>Math.abs(v-previous.c[k])))<=8,'One-minute adaptation jump: '+c);}
  previous={flux,warm,c};
 }
});

test('reported evening spatial highlight remains within one display stop of neighbouring sky',()=>{
 // Visual acceptance bound, not a photometric assertion: the isolated lower
 // field must be subordinate to its neighbouring atmosphere. Four times the
 // adapted median retained the owner's blue-grey spotlight. Limit this solar
 // highlight to one stop, independently of its hue, while leaving darker sky
 // exact. No prayer-row/UI pixels or whole-frame average enter this check.
 const r=renderNativeBackgroundPreview({...state('2026-10-07T23:40:00Z'),heightM:25,weather:{vis:20000,cloud:0,code:0,temp:24},units:'c'}).raster;
 const medianDisplay=-Math.expm1(-r.displayPresentation.displayExposure*r.displayPresentation.medianLuminance);
 for(let y=390;y<=518;y+=4)for(let x=245;x<=318;x+=4){
  const i=3*(y*325+x),Y=[.2126,.7152,.0722].reduce((v,w,k)=>v+w*(-Math.expm1(-r.effectiveExposure*r.skyBackgroundLinear[i+k])),0);
  assert.ok(Y<=2*medianDisplay,`Concentrated spatial peak at ${x},${y}: ${Y/medianDisplay}x median`);
 }
});

test('twilight shoulder preserves non-solar background and does not affect daylight',()=>{
 const source=new Float64Array([.1,.1,.1, 20,18,10, .1,.1,.1]);
 const base={width:3,height:1,linear:source,skyBackgroundLinear:source,effectiveExposure:2,nominalExposure:24,physicalState:{sun:{altDeg:-8}}};
 const neutral=nativeSkyPresentation({...base,solarBackgroundLinear:new Float64Array(9)}),control=nativeSkyPresentation(base);
 assert.deepEqual(neutral.linear,control.linear,'local or lunar light cannot be reduced as solar twilight');
 const bright={...base,physicalState:{sun:{altDeg:40}}};
 assert.deepEqual(nativeSkyPresentation({...bright,solarBackgroundLinear:source}).linear,nativeSkyPresentation(bright).linear,'approved high-Sun display is unchanged');
 const solar=nativeSkyPresentation({...base,solarBackgroundLinear:Float64Array.from(source,v=>Math.max(0,v-.1))});
 assert.deepEqual([...solar.linear.slice(0,3)],[...control.linear.slice(0,3)],'ordinary darker field remains exact');
 assert.ok(solar.displayPresentation.twilightShoulder.pixels>0);
 assert.deepEqual(base.linear,source,'physical input is never mutated');
});

test('solar aerosol presentation stays continuous when the physical Sun crosses the camera edge',()=>{
 // Actual-widget H8 control: 15:08 -> 15:09Z previously switched registration
 // on at physical x=0 and changed a central open-sky channel by 22 codes.
 const frames=['2026-10-07T15:07:00Z','2026-10-07T15:08:00Z','2026-10-07T15:09:00Z','2026-10-07T15:10:00Z'].map(t=>renderNativeBackgroundPreview(state(t)));
 for(const f of frames)assert.equal(f.raster.displayPresentation.solarRegistration.active,true,'Visible native Sun owns its aerosol term even when the physical direction is just outside the camera');
 const bytes=frames.map(f=>encodeNativeFrame(f.raster.linear,f.raster.effectiveExposure));
 let largest=0;
 for(let n=1;n<bytes.length;n++)for(let y=185;y<400;y+=3)for(let x=35;x<310;x+=3)for(let k=0;k<3;k++)largest=Math.max(largest,Math.abs(bytes[n][4*(y*325+x)+k]-bytes[n-1][4*(y*325+x)+k]));
 assert.ok(largest<=8,'One-minute ordinary-solar-motion display jump: '+largest);
});
test('fast-clock atmospheric preview stays within 8 codes at p99 and 20 maximum of higher spatial sampling',()=>{
 // Reference: 96x160 independent spatial integration nodes versus 12x20, then
 // the shared declared display policy. Bilinear display resampling is measured
 // explicitly. This qualifies atmospheric presentation, not terrain/science.
 // Tolerance fixed before full browser acceptance; interior excludes the
 // rounded card edge, and is still region-wide (not a whole-frame average).
 for(const hour of [9,11,12,13,15,17,19,21,23]){
  const s={...state(`2026-10-07T${String(hour).padStart(2,'0')}:00:00Z`),timeScale:600,weather:{vis:20000,cloud:0,code:0,temp:24},units:'c'};
  const p=renderNativeBackgroundPreview(s),j=nativeJob(s,true),physical=physicalSkyState(j.observer),f=nativeAtmosphereFields(physical,j.options.atmosphere,j.options.view,j.options.diffuse.residualNight,96,160),E=24/(1+24*f.mean/.5);
  const r=nativeSkyPresentation({width:325,height:530,linear:f.background,skyBackgroundLinear:f.background,solarAerosolLinear:f.solarAerosolLinear,solarBackgroundLinear:f.solarBackgroundLinear,twilightDisplay:f.twilightDisplay,effectiveExposure:E,nominalExposure:24,physicalState:physical,atmosphere:j.options.atmosphere},j.options.view);
  const a=encodeNativeFrame(p.raster.linear,p.raster.effectiveExposure),b=encodeNativeFrame(r.linear,r.effectiveExposure),errors=[];
  for(let y=20;y<480;y++)for(let x=20;x<305;x++)for(let k=0;k<3;k++){
   const u=(x+.5)/5-.5,v=(y+.5)/5-.5,ix=Math.floor(u),iy=Math.floor(v),tx=u-ix,ty=v-iy;
   const z=(a[(iy*65+ix)*4+k]*(1-tx)+a[(iy*65+ix+1)*4+k]*tx)*(1-ty)+(a[((iy+1)*65+ix)*4+k]*(1-tx)+a[((iy+1)*65+ix+1)*4+k]*tx)*ty;
   errors.push(Math.abs(z-b[(y*325+x)*4+k]));
  }
  errors.sort((a,b)=>a-b);assert.ok(errors[Math.floor(errors.length*.99)]<=8,`${hour}Z p99 ${errors[Math.floor(errors.length*.99)]}; max ${errors.at(-1)}`);assert.ok(errors.at(-1)<=20,`${hour}Z max ${errors.at(-1)}`);
  assert.equal(p.quality,'physical-background-preview');assert.equal(p.job.tier,128);assert.equal(p.utcMs,s.utcMs);
 }
});
