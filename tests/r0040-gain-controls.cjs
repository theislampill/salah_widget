'use strict';

// Run against the separate precipitation research checkout. The no-op drawing context
// exercises the real model's public set/frame and allocation paths, without taking pixels.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
if (process.argv.length !== 3) throw Error('usage: node tests/r0040-gain-controls.cjs RESEARCH_CHECKOUT');
const qa = path.join(process.argv[2], 'tools/qa');
const source = fs.readFileSync(path.join(qa, 'precip_models.js'), 'utf8');
const profile = JSON.parse(fs.readFileSync(path.join(qa, 'precip_declared_gain.json'), 'utf8'));

function renderer(rate, parameters, options, tileAlphas = [], study = null, config = {}) {
  const noop = () => {};
  const presentedTiles = new Set();
  let frameTime = 0, strokes = 0, textureEnergy=0, nearEnergy=0;
  const drops = [];
  const transforms = [];
  function element() {
    const canvas = {style: {}}, context = Object.create(draw);
    let firstStroke = true;
    context.stroke = () => {
      strokes++;
      if(config.energy && context.tip && context.base && typeof context.strokeStyle==='string'){
        const alpha=Number(context.strokeStyle.match(/,([\d.]+)\)$/)?.[1]||0);
        const energy=alpha*context.lineWidth*Math.hypot(context.tip[0]-context.base[0],context.tip[1]-context.base[1]);
        if(canvas.className==='pm-rain')nearEnergy+=energy;
        else if(canvas.width===352&&canvas.height===320)textureEnergy+=energy;
      }
      if(config.geometry && canvas.className==='pm-rain' && context.tip) drops.push([...context.tip,context.lineWidth,
        Math.hypot(context.tip[0]-context.base[0],context.tip[1]-context.base[1])]);
      if (firstStroke && canvas.width === 352 && canvas.height === 320) {
        firstStroke = false;
        tileAlphas.push(context.strokeStyle);
      }
    };
    context.moveTo=(x,y)=>{context.base=[x,y]};
    context.lineTo=(x,y)=>{context.tip=[x,y]};
    canvas.getContext = () => context;
    return canvas;
  }
  const draw = {clearRect: noop, putImageData: noop, drawImage: source => {
    if (source.width === 352 && source.height === 320) presentedTiles.add(source);
  }, beginPath: noop,
    moveTo: noop, lineTo: noop, stroke: noop, save: noop, restore: noop,
    createImageData: (w,h) => ({data:new Uint8ClampedArray(w*h*4)}),
    fillRect: noop, setTransform: (...v)=>transforms.push(v), createLinearGradient: () => ({addColorStop: noop}),
    getImageData: (_x, _y, w, h) => ({data: new Uint8ClampedArray(w*h*4)})};
  const card = {dataset: {precip: 'on', fx: config.code===53?'drizzle':'rain'}};
  const window = {__PMGEOM:config.geom, __R0040_STUDY:study, __PM_PARAMS: parameters, qaState: () => ({})};
  const document = {querySelector: s => s === '.c' ? card : null, querySelectorAll: () => [],
    getElementById: () => ({querySelector: () => null, insertBefore: noop}),
    createElement: element, head: {appendChild: noop}};
  vm.runInNewContext(config.instrumentedSource || source, {window, document, location: {hash: ''}, URLSearchParams,
    _colDens: config.col || new Array(65).fill(100),
    selectedWeather: () => ({code: config.code || 63, precip: rate/4, wind: config.wind || 0, windDir:90, currentIntervalSec:900, cloud: 85}),
    getComputedStyle: () => ({getPropertyValue: () => '0'}), requestAnimationFrame: noop,
    performance: {now: () => 0}});
  window.__PM.set(config.model || (options.shell ? 'M1' : 'M2'), options.frame || 'flat', options);
  return (nextRate = rate) => {
    rate = nextRate;
    frameTime += config.stepMs || 1000; // refresh the prototype's 500 ms weather input cache
    presentedTiles.clear();
    transforms.length=0;drops.length=0;strokes=0;textureEnergy=0;nearEnergy=0;
    const frame = window.__PM.frame(frameTime);
    return {R: frame.R, tiles: [...presentedTiles],strokes,transforms:[...transforms],near:frame.near,drops,textureEnergy,nearEnergy,params:window.__PM.params};
  };
}

const tex = {layers: ['tex']};
const tileAlphas = [];
assert.equal(renderer(12, profile, tex, tileAlphas)().R, 12, 'largest stratiform condition of the historical pack');
// At G=100 the first seeded strokes are D=0.3/0.6 mm, depth 1.52902/3.04717 m,
// v=1.17/2.46393 m/s. Canvas receives alpha = G*4*f*(D/2000)^2/(z*v*T), rounded to 0.001.
assert.deepEqual(tileAlphas, ['rgba(255,255,255,0.080)', 'rgba(255,255,255,0.076)']);
const overflow = renderer(20, profile, tex);
assert.throws(overflow, /124160 strokes; cap 100000/, 'a stronger, forward-looking control binds the far slab cap');
assert.throws(overflow, /124160 strokes/, 'a failed tile build must never become a cache hit');
const recovery = renderer(12, profile, tex);
const before = recovery().tiles;
assert.equal(before.length, 2);
assert.throws(() => recovery(20), /124160 strokes/);
const after = recovery(12).tiles;
assert.equal(after.length, 2, 'both slabs are drawn after a rejected weather change');
before.forEach((canvas, i) => assert.equal(after[i], canvas, 'recovered image uses its original valid slab'));
const below = 14.72417113166102, above = 14.724191131661026;
assert.equal(below.toFixed(2), above.toFixed(2));
const crossing = renderer(below, profile, tex);
assert.equal(crossing().tiles.length, 2);
assert.throws(() => crossing(above), /100001 strokes; cap 100000/, 'the warm cache must honor the exact new rate');
assert.throws(renderer(above, profile, tex), /100001 strokes; cap 100000/, 'the cold decision must agree');
assert.throws(renderer(12, {...profile, render: {...profile.render, lineFloor: 0.6}}, tex), /additive line width/);
assert.throws(renderer(12, {...profile, sunKernel: {...profile.sunKernel, amp: 0.55}}, tex), /light kernels/);
assert.throws(renderer(12, {...profile, moonKernel: {...profile.moonKernel, amp: 0.35}}, tex), /light kernels/);
assert.throws(renderer(12, profile, {shell: [1, 3]}), /shell cap/);
console.log('PASS: nominal 12 mm/h stroke alphas, overflow, retry, 12→20→12 tile identity, same-rounded-rate cap crossing, width floor, Sun and Moon kernels, shell compensation');

// Optional new study controls require the second (layer-study) research patch.
if (process.env.R0040_LAYER_STUDY === '1') {
  const render = (dispersion, cfg={}) => renderer(12,profile,tex,[],{dispersion},cfg)();
  const previous = renderer(12,profile,tex)();
  const common = render('common',{wind:8}), varied=render('diameter',{wind:8});
  assert.equal(common.tiles.length,2);
  assert.equal(varied.tiles.length,6);
  const shear = result=>result.transforms.filter(m=>m[0]===1&&m[1]===0&&m[2]!==0&&m[3]===1).map(m=>m[2]);
  assert.equal(new Set(shear(common)).size,2);
  assert.equal(new Set(shear(varied)).size,6);
  assert.ok(common.strokes<previous.strokes/5);
  assert.equal(common.strokes,varied.strokes,'changing the motion cohorts must preserve the number of sampled stroke commands');
  const trace=[];
  for(const rate of [1.2,5,12]) {
    const run=renderer(rate,profile,{},[],{dispersion:'common'},{model:'M1',wind:5});
    const samples=Array.from({length:60},()=>run().near);
    trace.push({rate,meanCount:samples.reduce((sum,x)=>sum+x.drawn,0)/samples.length,
      lengthMedianPx:samples.reduce((sum,x)=>sum+(x.lenP50||0),0)/samples.length});
  }
  assert.ok(trace[2].meanCount>trace[0].meanCount);
  assert.ok(trace[2].lengthMedianPx>trace[0].lengthMedianPx);
  const clear=renderer(12,profile,{},[],{dispersion:'common'},{model:'M1',col:new Array(65).fill(.1599)})();
  assert.equal(clear.near.drawn,0);
  for (const [value,expect] of [[15.999,false],[16,false],[16.001,true]]) {
    const col=new Array(65).fill(value);col[64]=100;
    const point=renderer(12,profile,{},[],{dispersion:'common'},{model:'M1',col,geometry:true,wind:0})();
    // x travel is zero at zero wind. Check away from the single high-control column.
    assert.equal(point.drops.some(d=>d[0]<320),expect,'relative column threshold '+value);
  }
  assert.throws(renderer(12,profile,{categoryOnly:true},[],{dispersion:'common'}), /excludes minimum rates/);
  assert.throws(renderer(12,profile,{policy:'complete'},[],{dispersion:'common'}), /excludes minimum rates/);
  console.log(JSON.stringify({historicalStrokeCalls:previous.strokes,clippedStrokeCalls:common.strokes,
    commonShear:shear(common),diameterShear:shear(varied),sixtySampleM1:trace}));
}

// Optional 60 s command-mask acquisition. Quantised centre of each emitted stroke, never browser pixels.
if (process.env.R0040_MASK_DIR) {
  const dir=process.env.R0040_MASK_DIR;
  fs.mkdirSync(dir);
  const summary=[];
  for(const rate of [.32,1.2,5,12]){
    const tick=renderer(rate,profile,{},[],{dispersion:'common'},{model:'M1',wind:5,geometry:true,stepMs:1000/60,
      code:rate===.32?53:63});
    const fd=fs.openSync(path.join(dir,rate+'.bin'),'wx');
    const columns=new Uint32Array(325),widths=new Map(),lengths=new Map();
    let commands=0;
    try {
      for(let frame=0;frame<3600;frame++){
        const mask=Buffer.alloc(65*59);
        for(const [x,y,width,length] of tick().drops){
          if(x<0||x>=325||y<8||y>=300)continue;
          columns[Math.floor(x)]++;commands++;
          const w=width.toFixed(2),l=length.toFixed(0);
          widths.set(w,(widths.get(w)||0)+1);lengths.set(l,(lengths.get(l)||0)+1);
          mask[Math.floor((y-8)/5)*65+Math.floor(x/5)]=1;
        }
        fs.writeSync(fd,mask);
      }
    }finally{fs.closeSync(fd)}
    summary.push({rate,commands,occupiedScreenColumns:columns.filter(n=>n>0).length,
      widthPx:Object.fromEntries(widths),lengthPx:Object.fromEntries(lengths)});
  }
  fs.writeFileSync(path.join(dir,'distribution.json'),JSON.stringify(summary));
}

if(process.env.R0040_INSPECT_PARAMETERS){
  const {auditNamed,auditSource}=require('../tools/qa/r0040/parameter-audit.cjs');
  const geometry=fs.readFileSync(path.join(qa,'precip_models_geom.js'),'utf8');
  const stage=renderer(12,profile,tex)();
  const design=process.env.R0040_PARAMETER_DESIGN||'revised';
  const result={...auditNamed(stage.params),...auditSource(source,geometry,design)};
  assert.throws(()=>auditNamed({...stage.params,rateFactor:8}),/rateFactor/);
  assert.throws(()=>auditNamed({...stage.params,sunKernel:{...stage.params.sunKernel,amp:.55}}),/sunKernel/);
  assert.throws(()=>auditNamed({...stage.params,undocumentedLift:2}),/undocumentedLift/);
  console.log(JSON.stringify(result));
}

// Non-qualifying ablation only. These deliberate mutants cannot produce strict-profile captures.
if (process.env.R0040_ABLATION) {
  const cells=[];
  function change(text,old,next){assert.equal(text.split(old).length,2,old);return text.replace(old,next);}
  for(const rate of [5,12])for(const dispersion of ['common','diameter'])for(const gain of [25,100])
    for(const floor of [0,.6])for(const rescale of [false,true]){
      const cap=rescale?9000:100000;
      let fixture=change(source,'if(P.enforceDeclaredGain && total>cap)','if(false && total>cap)');
      fixture=change(fixture,'P.render.lineFloor!==0 || P.sunKernel.amp!==0','P.sunKernel.amp!==0');
      const pp={...profile,G:gain,tile:{...profile.tile,cap},render:{...profile.render,lineFloor:floor}};
      const v=renderer(rate,pp,{layers:['tex','near']},[],{dispersion},{wind:5,energy:true,instrumentedSource:fixture})();
      cells.push({rate,dispersion,gain,nearAdditiveWidthPx:floor,historicalTileRescale:rescale,cap,
        rawTextureAlphaWidthLength:v.textureEnergy,rawNearAlphaWidthLength:v.nearEnergy,strokes:v.strokes});
    }
  assert.equal(cells.length,32);
  assert.ok(cells.every(c=>c.rawTextureAlphaWidthLength>0&&c.rawNearAlphaWidthLength>0));
  fs.writeFileSync(process.env.R0040_ABLATION,JSON.stringify({nonQualifying:true,
    metric:'sum of command alpha × width × length including edge copies, before raster/composition; no judgment',cells}));
}
if(process.env.R0040_EXPOSURE){
  const geometry=require(path.resolve(qa,'precip_models_geom.js'));
  const k=.8, wind=5, rate=5;
  const d=3.67/(4.1*Math.pow(rate,-.21)),v=9.65-10.3*Math.exp(-.6*d);
  const cam={az:180,alt:45,fov:90,W:325,H:530};
  const projected=geometry.screenLean(cam,162.5,265,90,k*wind,v).deg;
  const flat=Math.atan2(k*wind,v)*180/Math.PI;
  assert.ok(projected-flat>9);
  const output=[];
  for(const frame of ['flat','rigid'])for(const T of [1/60,1/15]){
    const r=renderer(rate,profile,{T,frame},[],{dispersion:'common'},{wind,model:'M1',geometry:true,geom:geometry})();
    output.push({frame,T,drawn:r.near.drawn,medianLengthPx:r.near.lenP50,meanAngle:r.near.angleMean,meanAlpha:r.near.meanAlpha});
  }
  assert.ok(output[1].medianLengthPx>2*output[0].medianLengthPx);
  assert.ok(output[3].medianLengthPx>2*output[2].medianLengthPx);
  assert.notEqual(output[0].meanAngle,output[2].meanAngle);
  fs.writeFileSync(process.env.R0040_EXPOSURE,JSON.stringify({declaredPhysicalLean:flat,rectilinearCenter45Deg:projected,output}));
}
