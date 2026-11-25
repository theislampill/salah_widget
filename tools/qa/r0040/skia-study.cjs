'use strict';

// Actual prototype Canvas calls on Skia. No browser, CSS, product sky, UI or acceptance input.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const {createCanvas}=require('@napi-rs/canvas'),{createHash}=require('node:crypto');
const [research,out]=process.argv.slice(2);
if(!research||!out)throw Error('usage: skia-study.cjs PATCHED_RESEARCH NEW_OUT');
const dir=path.resolve(research,'tools/qa');
const src=fs.readFileSync(path.join(dir,'precip_models.js'),'utf8'),profile=JSON.parse(fs.readFileSync(path.join(dir,'precip_declared_gain.json')));
const geom=require(path.join(dir,'precip_models_geom.js'));
const hash=d=>createHash('sha256').update(d).digest('hex');
function instrument({rate,kind='day',model='M2',dispersion='diameter',source=src,params=profile,angle='flat',T=1/60,layers=null,code=63,wind=5}){
  const all=[],card={dataset:{precip:rate>0?'on':'off',fx:rate>0?'rain':'overcast'},classList:{contains:()=>false}};
  const canvas=(w,h)=>{const c=createCanvas(w,h);c.style={};all.push(c);return c};
  const sky=canvas(325,530),cloud=canvas(144,232),merged=canvas(325,530);
  const colors={day:['#3278ba','#c5d8de','#465866'],twilight:['#192646','#bc8068','#384054'],
    moonlit:['#0b1626','#435062','#273143'],moonless:['#000','#000','#000']}[kind];
  const sk=sky.getContext('2d'),grad=sk.createLinearGradient(0,0,325,390);
  grad.addColorStop(0,colors[0]);grad.addColorStop(1,colors[1]);sk.fillStyle=grad;sk.fillRect(0,0,325,530);
  const cc=cloud.getContext('2d');
  cc.fillStyle=colors[2];cc.fillRect(10,30,54,24);cc.fillRect(76,41,62,26);
  const col=Array.from({length:65},(_,i)=>((i>=5&&i<=28)||(i>=35&&i<=61))?100:0);
  let now=0,scheduled=null,reduced=false,record={code,precip:rate/4,currentIntervalSec:900,wind,windDir:90,gust:wind,cloud:85,temp:18,dew:15,units:'c'};
  const host={_colDens:col};
  const window={__PM_PARAMS:params,__PMGEOM:geom,__R0040_STUDY:{dispersion},qaState:()=>({sunEl:kind==='day'?40:-14,moonTruth:{moonlightOpacity:0}})};
  const style={getPropertyValue:()=> '0',display:'block'};
  const document={querySelector:s=>s==='.c'?card:s==='.real-sky-canvas'?sky:s==='.wfx .cloudcanvas'?cloud:null,
    querySelectorAll:()=>[],head:{appendChild(){}},getElementById:()=>({querySelector:()=>null,insertBefore(){}}),
    createElement:n=>n==='canvas'?canvas(1,1):{style:{}}};
  vm.runInNewContext(source,Object.assign(host,{window,document,location:{hash:''},URLSearchParams,performance:{now:()=>now},getComputedStyle:()=>style,
    selectedWeather:()=>record,matchMedia:()=>({matches:reduced}),requestAnimationFrame:f=>{scheduled=f}}));
  const pm=window.__PM;
  pm.set(model,angle,{T,policy:'immediate',layers});
  const overlay=all.find(c=>c.className==='pm-rain');
  const ctx=merged.getContext('2d');
  function composite(withRain){
    ctx.drawImage(sky,0,0);ctx.drawImage(cloud,0,0,325,530);
    if(withRain)ctx.drawImage(overlay,0,0);
    return Buffer.from(ctx.getImageData(0,0,325,530).data);
  }
  const dry=composite(false);
  function tick(){const begin=process.hrtime.bigint();now+=1000/60;pm.frame(now);
    return Number(process.hrtime.bigint()-begin)/1e6;}
  function tiles(){return all.filter(c=>c.width===352&&c.height===320).map(c=>hash(c.getContext('2d').getImageData(0,0,352,320).data));}
  return {tick,tiles,dry,merged,overlay,composite,get last(){return pm.last},
    support(value){host._colDens=value==='admitted'?col:value;},
    lighting(on){sk.fillStyle=on?grad:'#000';sk.fillRect(0,0,325,530);cc.clearRect(0,0,144,232);
      if(on){cc.fillStyle=colors[2];cc.fillRect(10,30,54,24);cc.fillRect(76,41,62,26);}},
    reducedFrame(dt=16){now+=dt;scheduled();},
    setReduced(){reduced=true;scheduled()},withdraw(){card.dataset.precip='off';record=null;},get scheduled(){return scheduled}};
}
function difference(a,b){
  let changed=0,energy=0;
  for(let i=0;i<a.length;i+=4){
    const d=Math.abs(a[i]-b[i])+Math.abs(a[i+1]-b[i+1])+Math.abs(a[i+2]-b[i+2]);
    if(d)changed++;energy+=d;
  }
  return {changedPixels:changed,meanAbsoluteRgb:energy/(3*a.length/4)};
}
const quantile=(a,q)=>a.slice().sort((x,y)=>x-y)[Math.ceil(a.length*q)-1];
function evaluate(opts,n=60){
  const m=instrument(opts),cold=m.tick(),ms=[],energy=[],motion=[];
  let last=m.dry;
  for(let i=0;i<n;i++){
    ms.push(m.tick());const rendered=m.composite(true);
    energy.push(difference(rendered,m.dry).meanAbsoluteRgb);motion.push(difference(rendered,last).meanAbsoluteRgb);last=rendered;
  }
  const name=[opts.kind,opts.model,opts.dispersion,opts.rate].join('-');
  fs.writeFileSync(path.join(out,name+'.png'),m.merged.toBuffer('image/png'));
  const wet=difference(last,m.dry);
  m.withdraw();m.tick();const withdrawn=difference(m.composite(true),m.dry);
  assert.equal(withdrawn.changedPixels,0);
  if(!opts.rate||opts.kind==='moonless')assert.equal(wet.changedPixels,0);else assert.ok(wet.changedPixels>0);
  return {name,coldMs:cold,meanMs:ms.reduce((a,b)=>a+b)/n,p95Ms:quantile(ms,.95),frames:n,
    meanAbsRgbVsDry:energy.reduce((a,b)=>a+b)/n,meanAbsRgbVsPrevious:motion.slice(1).reduce((a,b)=>a+b)/(n-1),last:wet,afterWithdrawal:withdrawn};
}
function ablate({rate,dispersion,G,floor,rescale}){
const rw=src.replace('if(P.enforceDeclaredGain && total>cap)','if(false && total>cap)')
  .replace('P.render.lineFloor!==0 || P.sunKernel.amp!==0','P.sunKernel.amp!==0');
assert.notEqual(src,rw);

    const pp={...profile,G,tile:{...profile.tile,cap:rescale?9000:100000},render:{...profile.render,lineFloor:floor}};
    const m=instrument({rate,dispersion,source:rw,params:pp,layers:['tex','near']});
    const energy=[],motion=[];let previous=null;
    for(let i=0;i<12;i++){m.tick();const pixels=m.composite(true);energy.push(difference(pixels,m.dry).meanAbsoluteRgb);
      if(previous)motion.push(difference(pixels,previous).meanAbsoluteRgb);previous=pixels;}
    return {rate,dispersion,G,floor,rescale,n:energy.length,meanAbsRGB:energy.reduce((a,b)=>a+b)/energy.length,
      meanAbsRGBmotion:motion.reduce((a,b)=>a+b)/motion.length};
}
// Skia may retain large display lists. Isolate each scene/cell and release its native allocations on exit.
const mode=process.argv[4];
if(mode==='discriminators'){
  const a2=[];
  for(const angle of ['flat','rigid'])for(const T of [1/60,1/15]){
    const m=instrument({model:'M1',rate:5,angle,T}),save=createHash('sha256'),energies=[],motion=[];
    let prev=null;for(let i=0;i<60;i++){m.tick();const v=m.composite(true);save.update(v);
      energies.push(difference(v,m.dry).meanAbsoluteRgb);if(prev)motion.push(difference(v,prev).meanAbsoluteRgb);prev=v;}
    a2.push({angle,T,rgbaSha256:save.digest('hex'),meanDeltaVsDry:energies.reduce((a,b)=>a+b)/60,
      meanMotion:motion.reduce((a,b)=>a+b)/59});
  }
  assert.equal(new Set(a2.map(x=>x.rgbaSha256)).size,4);
  function support(rate,source=src,opacity=1){
    const m=instrument({rate,source,wind:0,model:'M1'}),seq=createHash('sha256'),cols=new Set();
    let nonzero=0,totalAlpha=0;
    for(let i=0;i<60;i++){m.tick();const px=m.overlay.getContext('2d').getImageData(0,0,325,530).data;
      const shape=Buffer.alloc(325*530);
      for(let j=0;j<shape.length;j++){const alpha=px[4*j+3]*opacity;if(alpha>0){shape[j]=1;cols.add(j%325);nonzero++;totalAlpha+=alpha;}}
      seq.update(shape);
    }
    return {columns:cols.size,occupiedPixels:nonzero,alphaSum:totalAlpha,maskSha256:seq.digest('hex')};
  }
  const light=support(1.2),heavy=support(12);
  const fixed=src.replace('let x0=h1(s,3)*W,','let x0=[45,70,110,210,245][i%5],');assert.notEqual(fixed,src);
  const repeated=support(12,fixed);assert.ok(repeated.columns<30&&heavy.columns>150,JSON.stringify([repeated.columns,heavy.columns]));
  const opaque=support(5),faint=support(5,src,.25);
  assert.ok(heavy.occupiedPixels>light.occupiedPixels&&heavy.maskSha256!==light.maskSha256);
  assert.equal(opaque.maskSha256,faint.maskSha256);assert.equal(opaque.alphaSum,4*faint.alphaSum);
  console.log(JSON.stringify({evidence:'actual standalone M1 raster, 60 frames each; synthetic cloud rectangles; opacity scaling applied to decoded alpha in floating point',a2,
    d1FixedColumns:{ordinary:heavy,fixed:repeated},d2OpacityOnly:{light,heavy,sameGeometry:opaque,quarterAlpha:faint}}));
  process.exit(0);
}
if(mode==='transitions'){
  const shifts={},m3=[];
  for(const support of [null,Array(65).fill(0),Array(65).fill(1.99),'admitted']){
    const m=instrument({rate:3,code:81,model:'M3'});m.support(support);m.tick();
    m3.push({kind:typeof support==='string'?'admitted':support===null?'absent':String(support[0]),veil:m.last.veil??0,
      shafts:m.last.shafts??0,near:m.last.near?.drawn??0,change:difference(m.composite(true),m.composite(false)).changedPixels});
  }
  const m=instrument({rate:5,model:'M1'});m.setReduced();
  const wet=hash(m.composite(true));
  const observe=()=>difference(m.composite(true),m.composite(false)).changedPixels;
  shifts.eligible=observe();m.reducedFrame(1400);shifts.stable=hash(m.composite(true))===wet;
  m.support(null);m.reducedFrame(16);shifts.lostSupport=observe();
  m.support('admitted');m.reducedFrame(16);shifts.regainedSupport=observe();
  m.lighting(false);m.reducedFrame(16);shifts.dark=observe();
  m.lighting(true);m.reducedFrame(16);shifts.relit=observe();shifts.samePose=hash(m.composite(true))===wet;
  m.withdraw();m.reducedFrame(16);shifts.expired=observe();
  console.log(JSON.stringify({m3,shifts}));
  assert.ok(m3.slice(0,3).every(v=>v.change===0&&v.veil===0&&v.shafts===0&&v.near===0));
  assert.ok(m3[3].change>0&&m3[3].shafts>0&&shifts.eligible>0&&shifts.stable&&shifts.samePose);
  assert.equal(shifts.lostSupport,0);assert.equal(shifts.dark,0);assert.equal(shifts.expired,0);
  assert.ok(shifts.regainedSupport>0&&shifts.relit>0);
  process.exit(0);
}
if(mode==='clip'){
  const opts=JSON.parse(process.argv[5]);
  const m=instrument(opts);
  // Synthetic 180-frame sequence. Encode losslessly without resampling, then independently decode and hash it.
  const temp=fs.mkdtempSync(path.join(require('node:os').tmpdir(),'r0040-rgba-'));
  const raw=path.join(temp,'frames.rgba'),log=createHash('sha256');
  const fd=fs.openSync(raw,'wx');
  try{
    try{for(let n=0;n<180;n++){m.tick();const rgba=m.composite(true);fs.writeSync(fd,rgba);log.update(rgba);}}
    finally{fs.closeSync(fd)}
    require('node:child_process').execFileSync('ffmpeg',['-v','error','-n','-f','rawvideo','-pixel_format','rgba','-video_size','325x530','-framerate','60',
      '-i',raw,'-an','-c:v','ffv1','-pix_fmt','bgra','-threads','1',out]);
    const check=path.join(temp,'decoded.rgba');
    require('node:child_process').execFileSync('ffmpeg',['-v','error','-i',out,'-f','rawvideo','-pix_fmt','rgba','-threads','1',check]);
    const digest=log.digest('hex');
    assert.equal(hash(fs.readFileSync(check)),digest);
    console.log(JSON.stringify({evidence:'standalone synthetic Skia fixture',options:opts,frames:180,syntheticHz:60,rgbaSha256:digest}));
  }finally{fs.rmSync(temp,{recursive:true,force:true})}
  process.exit(0);
}
if(mode==='row'||mode==='factor'){
  const item=JSON.parse(process.argv[5]);
  console.log(JSON.stringify(mode==='row'?evaluate(item):ablate(item)));
  process.exit(0);
}
const child=(type,item)=>JSON.parse(require('node:child_process').execFileSync(process.execPath,
  [__filename,research,out,type,JSON.stringify(item)],{encoding:'utf8'}));
fs.mkdirSync(out);
const rows=[];
for(const opts of [
  ...['day','twilight','moonlit','moonless'].map(kind=>({kind,rate:5,model:'M1',dispersion:'common'})),
  ...['common','diameter'].flatMap(dispersion=>[0,5,12].map(rate=>({kind:'day',rate,model:'M2',dispersion}))),
  {kind:'moonless',rate:12,model:'M2',dispersion:'diameter'},
  {kind:'day',rate:3,code:81,model:'M3',dispersion:'common'}])rows.push(child('row',opts));
// Compare all pixels of each cached tile with only the clipping predicate disabled; no scene geometry or gain change.
const predicate='if(study&&(sx<-1||sx>tw+1||sy<0||sy-L>th))continue;';
assert.equal(src.split(predicate).length,2);
const tileArgs={kind:'day',rate:12,model:'M2',dispersion:'diameter'};
const compact=instrument(tileArgs),unculled=instrument({...tileArgs,source:src.replace(predicate,'')});
compact.tick();unculled.tick();assert.deepEqual(compact.tiles(),unculled.tiles());assert.equal(compact.tiles().length,6);
// Every altered contrast/width/cap below is an explicitly labelled, nonqualifying A1 dissection.
const factorial=[];
for(const rate of [5,12])for(const dispersion of ['common','diameter'])for(const G of [25,100])
  for(const floor of [0,.6])for(const rescale of [false,true])factorial.push(child('factor',{rate,dispersion,G,floor,rescale}));
const reduced=instrument({rate:5,kind:'day',model:'M1'});reduced.setReduced();
assert.ok(difference(reduced.composite(true),reduced.dry).changedPixels>0);
reduced.withdraw();reduced.scheduled();assert.equal(difference(reduced.composite(true),reduced.dry).changedPixels,0);
// Isolate M3 shaft raster only and remove the deck sample to exercise the boundary on the very same geometry.
function shafts(noColumns){
  let q=src.replace('rec.veil=veilLayer(In,Rg,fld,1);rec.shafts=shafts','rec.veil=0;rec.shafts=shafts')
    .replace('rec.near=streaks(In,Rg,t,o(Object.assign(NEAR(),{fld})));','rec.near=null;');
  if(noColumns)q=q.replace('const columns=study&&peak>=2?','const columns=false?');
  const m=instrument({rate:3,code:81,model:'M3',source:q});m.tick();
  return {count:m.last.shafts,pixels:difference(m.composite(true),m.dry).changedPixels};
}
const measuredShafts=shafts(false),withheldShafts=shafts(true);
assert.ok(measuredShafts.count>0&&measuredShafts.pixels>0);
assert.deepEqual(withheldShafts,{count:0,pixels:0});
const receipt={factorial,reducedWithdrawal:'zero RGB delta from dry on first reduced callback after authority off',
  isolatedShafts:{admitted:measuredShafts,withoutCloudProfile:withheldShafts},evidence:'Standalone Skia raster using synthetic gradient and two opaque cloud rectangles; no native widget or human assessment',
  sourceSha256:hash(src),syntheticFramesPerSecond:60,hardware:'environment CPU only; timing includes warmed renderer frame, excludes CPU readback and comparison',
  identicalCulledAndUnculledTileDigests:compact.tiles(),rows};
fs.writeFileSync(path.join(out,'skia-study.json'),JSON.stringify(receipt,null,2));
console.log(JSON.stringify(rows.map(r=>[r.name,r.last.changedPixels,r.meanMs])));
