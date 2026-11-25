'use strict';
// Intake is independent of the producer's status: re-read pixels and ledgers,
// verify identities against the retained generated HTML, and replay statistics.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {spawnSync}=require('node:child_process');
const {cells,fragment}=require('./r003f_grid.cjs'),{variants,hash}=require('./r003f_variants.cjs');
const {frameRegistration,matchedRegistration,motionEvidence,nativeDb3Disposition}=require('./r003f_motion.cjs');
const {checkPair,aperture,riseBracket}=require('./r003f_capture.cjs');
const {buildMasks,measure,compareCards,lightness}=require('./r003f_p1.cjs');
const {occultation,terrain,terminator,deltaE,compareTransitions,buckleRate}=require('./r003f_diagnostics.cjs');
const pins=require('../../docs/state-contracts/evidence/R003F/publication-paths.json');
const tiers=['initial','refined'],hex=/^[0-9a-f]{64}$/;
function one(xs,p,label){const found=xs.filter(p);assert.equal(found.length,1,'missing/duplicate '+label);return found[0];}
function validate(file,PNG){return replay(file,PNG,false);}
// The test entry can only replay an explicitly injected diagnostic; the
// sheet intake always takes the native provenance path.
function replayFixture(file,PNG){return replay(file,PNG,true);}
function replay(file,PNG,fixtureOnly){
  const r=JSON.parse(fs.readFileSync(file)),dir=fs.realpathSync(path.dirname(file));
  assert.equal(r.protocol,'R003F/P1/native-matrix/2');
  if(fixtureOnly){assert.equal(r.evidenceClass,'injected-diagnostic');assert.equal(r.status,'DIAGNOSTIC');}
  else{
    assert.equal(r.evidenceClass,'native');assert.equal(r.status,'ACQUIRED');
    assert.equal(r.driver?.name,'playwright');assert.equal(r.decoder?.name,'pngjs');
    for(const pkg of [r.driver,r.decoder]){
      assert.ok(/^\d+\.\d+/.test(pkg.version)&&hex.test(pkg.entrySha256));
      const entry=require.resolve(pkg.name);assert.equal(pkg.entrySha256,hash(fs.readFileSync(entry)),'package entry differs from replay host');
      assert.equal(pkg.version,require(pkg.name+'/package.json').version,'package version differs from replay host');
    }
    assert.match(r.version,/^\d+(\.\d+)+/);
  }
  assert.ok(['chromium','firefox','webkit'].includes(r.engine)&&[1,2].includes(r.dpr));
  const c=one(cells(r.engine,r.dpr),x=>x.id===r.cell?.id,'manifest cell');assert.deepEqual(r.cell,c);
  assert.deepEqual(r.names,variants);assert.deepEqual(r.builds,pins.builds);assert.equal(r.archiveIndexSha256,pins.indexSha256);
  const consumes=new Set(),captures=new Set(),pairs=new Set(),metrics=new Set();
  const artifact=n=>{
    assert.ok(typeof n==='string'&&n&&!path.isAbsolute(n)&&!n.split(/[\\/]/).some(s=>s==='..'||s==='.'||!s),'artifact path');
    const p=fs.realpathSync(path.join(dir,n));assert.ok(p.startsWith(dir+path.sep),'artifact escaped');
    const bytes=fs.readFileSync(p);assert.deepEqual(r.artifacts[n],{sha256:hash(bytes),bytes:bytes.length},'unbound '+n);consumes.add(n);return bytes;
  };
  const json=n=>JSON.parse(artifact(n)),lines=n=>artifact(n).toString().split('\n').filter(Boolean).map(JSON.parse);
  const network=lines('network.jsonl');
  assert.ok(network.length>0&&r.network?.ok&&r.network.seen===network.length&&r.network.allowedOffLoopback===0&&r.network.refusedAtProxy===0&&r.network.refusedByNodeGuard===0);
  assert.deepEqual(r.network.escapes,[]);assert.ok(network.some(x=>x.action==='fulfill'&&x.host==='api.aladhan.com'));
  assert.ok(network.some(x=>x.action==='continue'&&x.host==='127.0.0.1'&&x.url.endsWith('/index.html')));
  for(const [i,n] of network.entries()){
    assert.equal(n.n,i);assert.ok(['continue','fulfill','abort'].includes(n.action));
    if(n.action==='continue')assert.ok(n.host==='127.0.0.1'||/^(blob|data|about):/.test(n.url),'foreign request');
    if(n.action==='fulfill')assert.equal(n.host,'api.aladhan.com');
  }
  for(const [action,prop] of [['fulfill','fulfilled'],['continue','continued'],['abort','aborted']])assert.equal(r.network[prop],network.filter(x=>x.action===action).length);
  const census=new Map();
  for(const {pair,...point} of lines('outside.jsonl')){if(!census.has(pair))census.set(pair,[]);census.get(pair).push(point);}
  const readPng=(name,digest)=>{const bytes=artifact(name);assert.equal(hash(bytes),digest);
    const png=PNG.sync.read(bytes);assert.equal(png.width,325*r.dpr);assert.equal(png.height,530*r.dpr);return png.data;};
  const docs=new Map();let fixture=false;
  function doc(m,n,scenario,options){
    const d=m.document;assert.ok(d&&Number.isSafeInteger(d.id)&&d.id>0);assert.equal(d.name,n);assert.equal(d.offset,!!options.offset);
    assert.equal(d.responseSha256,pins.builds.find(b=>b.variant===n).indexSha256);
    const url=new URL(d.url);assert.equal(url.hostname,'127.0.0.1');assert.equal(url.pathname,'/index.html');
    assert.equal(url.searchParams.get('variant'),n);assert.equal(url.hash,fragment(scenario,!!options.offset));
    if(docs.has(d.id))assert.deepEqual(docs.get(d.id),d);else docs.set(d.id,d);
    if(scenario.mode==='away')for(const [x,y] of [['before','after'],['detailBefore','detailAfter']])
      assert.ok(Math.abs(d.translation[y].y-d.translation[x].y-60)<1.1);
    if(m.before?.weatherFixtureReads>0||m.state?.weatherFixtureReads>0)fixture=true;
  }
  function cap(tag,n,options,scenario=c){
    const m=r.captures[tag];assert.ok(m,'missing '+tag);captures.add(tag);
    const expected={tier:options.tier,...(options.hidden?{hidden:true}:{}),...(options.tier==='inhibited'?{}:{offset:!!options.offset,reference:!!options.reference})};
    assert.deepEqual(m.admission,expected);checkPair(m.state,m.after,scenario,expected);doc(m,n,scenario,expected);
    if(m.boxes){
      for(const selector of ['.moccluder','.moon-detail-canvas','.buckle','.h','.e','.wt']){
        const rect=m.boxes[selector];assert.ok(rect&&[rect.x,rect.y,rect.w,rect.h].every(Number.isFinite)&&rect.w>=0&&rect.h>=0,'missing measured '+selector);
      }
      const box=m.boxes['.moccluder'],disc=m.state.disc;
      assert.ok(Math.abs(box.x+box.w/2-disc.cx)<.001&&Math.abs(box.y+box.h/2-disc.cy)<.001&&Math.abs(box.w/2-disc.r)<.001,'occluder box differs from admitted disc');
      if(m.state.detail?.visible)assert.ok(m.boxes['.moon-detail-canvas'].w>0&&m.boxes['.moon-detail-canvas'].h>0,'empty presented footprint');
      if(c.mode==='long-text')assert.ok(Math.abs(m.boxes['.wt'].w-128)<.5);
      if(c.mode==='no-backdrop')assert.ok(['.wt','.e'].every(k=>['none',''].includes(m.boxes[k].filter)));
    }else assert.ok(tag.startsWith('hidden-')||c.group==='ineligible','missing DOM owner boxes');
    if(m.cloud){const raw=artifact(tag+'-cloud.rgba');assert.equal(hash(raw),m.cloud.sha256);assert.equal(raw.length,4*m.cloud.pixels);
      let nonzero=0;for(let i=3;i<raw.length;i+=4)if(raw[i])nonzero++;assert.equal(nonzero,m.cloud.nonzeroAlpha);}
    return {tag,meta:m,pixels:readPng(tag+'.png',m.sha256)};
  }
  function pair(label,b,f){
    const p=one(r.pairs,x=>x.label===label,label);pairs.add(p);
    assert.equal(p.base,b.tag);assert.equal(p.candidate,f.tag);
    for(const k of ['disc','acceptedFraction','nativeFraction','waxing','up','light','weatherFields','source','quality','profile'])assert.deepEqual(b.meta.state[k],f.meta.state[k]);
    const d=compareCards(r.dpr,b.meta.state.disc,b.pixels,f.pixels),obs=census.get(label)||[];
    assert.equal(p.changed,d.changedPixels);assert.equal(p.outside,d.outside.length);assert.equal(obs.length,d.outside.length);
    const rect=f.meta.boxes['.buckle'];let buckle=0,outMax=0,buckleMax=0;
    for(const [i,v] of d.outside.entries()){
      const {stack,...o}=obs[i];assert.deepEqual(o,v);assert.ok(Array.isArray(stack)&&stack.length);
      const x=(v.x+.5)/r.dpr,y=(v.y+.5)/r.dpr,max=Math.max(...v.delta.map(Math.abs));outMax=Math.max(outMax,max);
      if(x>=rect.x&&x<rect.x+rect.w&&y>=rect.y&&y<rect.y+rect.h){buckle++;buckleMax=Math.max(buckleMax,max);}
    }
    assert.deepEqual([p.outMax,p.buckle,p.buckleMax,p.signature51x16],[outMax,buckle,buckleMax,buckle===51&&buckleMax===16]);
    census.delete(label);return p;
  }
  const metric=(n,t)=>{const m=one(r.metrics,x=>x.name===n&&x.tier===t,n+' '+t);metrics.add(m);return m;};
  if(c.group==='ineligible'){
    for(const n of variants)cap(n,n,{tier:'inhibited'});assert.equal(docs.size,variants.length);
  }else if(['strap','buckle'].includes(c.group)){
    const used=new Set();
    for(const n of variants){
      const counts={repeat:{any:0,signature:0,other:0},candidate:{any:0,signature:0,other:0}};
      for(let i=0;i<c.repeats;i++)for(const [position,arm] of (i%2?['candidate','repeat']:['repeat','candidate']).entries()){
        const label=n+'-'+i+'-'+arm,b=cap(label+'-base','B0',{tier:'refined'}),f=cap(label+'-target',arm==='repeat'?'B0':n,{tier:'refined'});
        for(const v of [b,f]){assert.ok(!used.has(v.meta.document.id),'reused arm document');used.add(v.meta.document.id);}
        const p=pair(label,b,f);assert.deepEqual([p.round,p.name,p.arm,p.position],[i,n,arm,position]);
        if(p.buckle){counts[arm].any++;counts[arm][p.signature51x16?'signature':'other']++;}
      }
      const s=metric(n,undefined);assert.deepEqual(s.counts,counts);assert.equal(s.repeats,c.repeats);
      for(const k of ['any','signature','other'])assert.deepEqual(s.tests[k],buckleRate(counts.repeat[k],counts.candidate[k],c.repeats));
    }
    if(c.gpu==='software'){
      if(r.engine==='chromium')assert.match(r.rasterization,/disabled|unavailable_software/);
      if(r.engine==='firefox'){const support=artifact('firefox-support.txt');assert.equal(hash(support),r.rasterization.sha256);assert.match(support.toString(),/WebRender \(Software\)/i);}
      if(r.engine==='webkit')assert.equal(hash(artifact('raster-trace.bin')),r.rasterization.traceSha256);
    }
  }else if(c.group==='motion'){
    assert.equal(r.streams.length,18);const motionPages=new Set();
    const streams=new Map();
    for(const label of ['offset','reference',...variants,...variants.map(n=>'observer-'+n)]){
      const mode=label.startsWith('observer-')?'continuous':'minute-target',name=label.replace(/^observer-/, '');
      const stream=one(r.streams,s=>s.label===label,label);streams.set(label,stream);assert.equal(stream.frames.length,50);
      assert.equal(stream.clip,label+'/clip.mkv');artifact(stream.clip);assert.equal(stream.mode,mode);assert.equal(stream.evidenceClass,motionEvidence[mode]);const rawHash=require('node:crypto').createHash('sha256');
      for(const v of ['hostRoundTripMs','pageSetupMs'])assert.ok(Number.isFinite(r.clockStarts[label][v])&&r.clockStarts[label][v]>=0);
      for(const [i,f] of stream.frames.entries()){
        const options={tier:'refined',offset:label==='offset',reference:label==='reference',minute:Date.parse(c.epoch)/60000+i};
        assert.deepEqual(f.admission,options);checkPair(f.before,f.after,c,options);doc(f,variants.includes(name)?name:'B0',c,options);
        assert.deepEqual(f.registration,frameRegistration(f,options.minute,mode,Date.parse(c.epoch)-30*60000));
        assert.equal(f.file,label+'/'+String(i).padStart(3,'0')+'.png');assert.deepEqual(f.why,[]);
        assert.ok(f.started>=1000*i&&f.ended>=f.started&&f.ended<1000*(i+1));assert.equal(f.minute,options.minute);
        assert.deepEqual([f.up,f.altitude,f.disc],[f.before.up,f.before.geometry.altitudeDeg,f.before.disc]);
        rawHash.update(readPng(f.file,f.sha256));
      }
      const pageIds=new Set(stream.frames.map(f=>f.document.id));assert.equal(pageIds.size,1);
      const [pageId]=pageIds;assert.ok(!motionPages.has(pageId));motionPages.add(pageId);
      const probe=spawnSync('ffprobe',['-v','error','-select_streams','v:0','-show_entries','stream=codec_name,width,height,avg_frame_rate','-of','json',path.join(dir,stream.clip)],{encoding:'utf8'});
      assert.equal(probe.status,0,'invalid motion clip');assert.deepEqual(JSON.parse(probe.stdout).streams,[{codec_name:'ffv1',width:325*r.dpr,height:530*r.dpr,avg_frame_rate:'1/1'}]);
      assert.deepEqual(stream.cadence,{startsMs:stream.frames.map(f=>f.started),durationsMs:stream.frames.map(f=>f.ended-f.started),oneCapturePerSecond:true});
      const playback=spawnSync('ffmpeg',['-v','error','-i',path.join(dir,stream.clip),'-f','hash','-hash','sha256','-pix_fmt','rgba','-'],{encoding:'utf8'});
      assert.equal(playback.status,0,'undecodable motion clip');assert.equal(playback.stdout.trim().toLowerCase(),'sha256='+rawHash.digest('hex'),'clip / frame pixels');
    }
    assert.deepEqual(Object.keys(r.clockStarts).sort(),[...streams.keys()].sort());
    const series=new Map(),refs=streams.get('reference').frames,offsets=streams.get('offset').frames;
    for(const n of variants){
      const s=metric(n,undefined),frames=streams.get(n).frames;assert.equal(s.sequence.length,50);
      assert.deepEqual(s.observerGeometry,streams.get('observer-'+n).frames.map(f=>f.registration));
      const maskCache=new Uint8Array(325*530*r.dpr*r.dpr);
      const seq=frames.map((f,i)=>{
        const ref=refs[i],off=offsets[i],registration=matchedRegistration(off.registration,ref.registration,f.registration,streams.get('B0').frames[i].registration);
        assert.deepEqual([ref.before.acceptedFraction,ref.before.nativeFraction],[f.before.acceptedFraction,f.before.nativeFraction]);
        assert.equal(f.beam,f.before.beam);assert.equal(f.expected,f.minute);
        const m=buildMasks({dpr:r.dpr,fraction:c.fraction,disc:f.disc,offsetDisc:off.disc,newMoon:readPng(off.file,off.sha256),reference:readPng(ref.file,ref.sha256),headerRects:[],topIsSkyOrMoon:maskCache});
        const val=measure(m,readPng(f.file,f.sha256)),q=aperture(val);
        const row={minute:f.minute,registration,litL:q.lit?lightness(val.litMeanY):null,beam:f.beam,up:f.up,altitude:f.altitude,aperture:q,referenceP95:val.referenceP95,maskOverlapPixels:val.maskOverlapPixels};
        assert.deepEqual(row,s.sequence[i]);return row;
      });
      series.set(n,seq);const bracket=riseBracket(seq);assert.ok(bracket);assert.deepEqual(bracket,riseBracket(series.get('B0')));
      assert.deepEqual(s.nativeDB3,nativeDb3Disposition);assert.deepEqual(s.controlledDB3,{...compareTransitions(seq.slice(...bracket),series.get('B0').slice(...bracket)),bracket});
    }
  }else{
    const ref=cap('reference','B0',{tier:'refined',reference:true});
    const pageIds=new Set();
    for(const tag of ['b0','offset','baseline-repeat',...variants]){
      const first=r.captures[tag+'-initial']?.document?.id,last=r.captures[tag+'-refined']?.document?.id;
      assert.ok(first&&first===last&&!pageIds.has(first),'missing/reused still document '+tag);pageIds.add(first);
    }
    assert.equal(ref.meta.document.id,r.captures['b0-refined'].document.id);
    if(c.group==='horizon'&&c.alt>-2&&c.alt<4)for(const n of variants){
      const id=r.captures[n+'-minus2']?.document?.id;assert.ok(id&&!pageIds.has(id),'reused lower endpoint');pageIds.add(id);
    }
    for(const t of tiers){
      const b=cap('b0-'+t,'B0',{tier:t}),rep=cap('baseline-repeat-'+t,'B0',{tier:t}),off=cap('offset-'+t,'B0',{tier:t,offset:true});
      assert.notEqual(b.meta.document.id,rep.meta.document.id);assert.deepEqual(b.meta.state.disc,ref.meta.state.disc);
      assert.deepEqual(off.meta.state.disc,b.meta.state.disc);for(const k of ['acceptedFraction','nativeFraction','waxing','up','light','weatherFields'])assert.deepEqual(b.meta.state[k],ref.meta.state[k]);
      const h=cap('hidden-'+t,'B0',{tier:t,hidden:true}),ui=json('ui-'+t+'.json'),allowed=new Uint8Array(325*530*r.dpr*r.dpr);
      assert.equal(h.meta.document.id,b.meta.document.id);ui.allowed.forEach(i=>{assert.ok(Number.isInteger(i)&&i>=0&&i<allowed.length);allowed[i]=1;});
      const m=buildMasks({dpr:r.dpr,fraction:c.fraction,disc:ref.meta.state.disc,offsetDisc:off.meta.state.disc,newMoon:off.pixels,reference:ref.pixels,headerRects:ui.headerRects,topIsSkyOrMoon:allowed});
      assert.deepEqual(json('masks-'+t+'.json'),{lit:m.lit,dark:m.dark,sky:m.sky.map(p=>p.i),g0:m.g0,p95:m.p95,maskOverlapPixels:m.maskOverlapPixels});
      const env=pair('baseline-envelope-'+t,b,rep),plain={};
      const same=ids=>ids.every(i=>[0,1,2,3].every(k=>b.pixels[4*i+k]===rep.pixels[4*i+k]));
      for(const n of variants){
        const f=cap(n+'-'+t,n,{tier:t}),s=metric(n,t);if(!n.endsWith('-T'))plain[n]=f.pixels;
        const z=pair(n+'-'+t,b,f);
        assert.deepEqual(s.inputs,{candidate:f.tag,reference:'reference',offset:off.tag,base:b.tag,repeat:rep.tag,hidden:h.tag,ui:'ui-'+t+'.json',masks:'masks-'+t+'.json'});
        assert.deepEqual([s.tag,s.pair,s.envelope],[f.tag,z.label,env.label]);
        for(const [k,v] of [['metrics',f],['repeat',rep],['base',b],['reference',ref]])assert.deepEqual(s[k],measure(m,v.pixels));
        assert.deepEqual(s.aperture,aperture(s.metrics));assert.deepEqual(s.repeatStable,{lit:same(m.lit),dark:same(m.dark),sky:same(m.sky.map(p=>p.i))});
        assert.deepEqual(s.terrain,{candidate:terrain(m,f.pixels),physical:terrain(m,ref.pixels),base:terrain(m,b.pixels)});
        assert.deepEqual(s.terminator,c.fraction>=.15&&c.fraction<=.85?terminator(m,f.pixels,ref.pixels,c.waxing):null);
        assert.deepEqual(s.occlusion,{candidate:occultation(m,f.pixels,h.pixels),reference:occultation(m,ref.pixels,h.pixels)});
        assert.deepEqual(s.deltaE76,deltaE(m,f.pixels,plain[n.split('-')[0]]));
        assert.equal(s.cloudRepeatStable,b.meta.cloud?.sha256===rep.meta.cloud?.sha256&&!!b.meta.cloud);assert.ok(b.meta.cloud&&f.meta.cloud);assert.equal(s.cloudMatch,b.meta.cloud.sha256===f.meta.cloud.sha256);
        if(c.alt<=-2&&s.cloudRepeatStable)assert.equal(s.cloudMatch,true,'unresolved cloud Andon');
        if(s.aperture.dark&&s.repeatStable.dark)assert.ok(!s.occlusion.candidate.starCoincidences?.length,'unresolved dark-limb Andon');
        if(c.group==='horizon'&&c.alt>-2&&c.alt<4&&t==='refined'){
          const low=cap(n+'-minus2',n,{tier:t},{...c,alt:-2});
          if(s.aperture.lit&&s.repeatStable.lit){
            const [lo,mid,hi]=[measure(m,low.pixels).litMeanY,s.metrics.litMeanY,s.reference.litMeanY].map(lightness);
            assert.deepEqual(s.db1,{minus2L:lo,litL:mid,referenceL:hi,convex:mid>=Math.min(lo,hi)-.5&&mid<=Math.max(lo,hi)+.5});
          }else assert.equal(s.db1,undefined);
        }
      }
    }
  }
  const origins=new Set([...docs.values()].map(d=>new URL(d.url).origin));
  assert.equal(origins.size,1,'mixed document origins');const [origin]=origins;
  assert.ok(network.filter(n=>n.action==='continue'&&n.url===origin+'/index.html'&&n.type==='document').length>=docs.size,'unobserved document loads');
  for(const n of network)if(n.action==='continue'&&n.host)assert.equal(new URL(n.url).origin,origin);
  assert.ok(fixture,'no fixture read');assert.equal(census.size,0);assert.equal(captures.size,Object.keys(r.captures).length);
  assert.equal(metrics.size,r.metrics.length);assert.equal(pairs.size,r.pairs.length);assert.deepEqual([...consumes].sort(),Object.keys(r.artifacts).sort());
}
module.exports={validate,replayFixture};
if(require.main===module){
  const files=JSON.parse(fs.readFileSync(0));const {PNG}=require(process.argv[2]||'pngjs');
  const results=files.map(file=>{try{validate(file,PNG);return null;}catch(e){return e.message;}});
  process.stdout.write(JSON.stringify(results));
}
