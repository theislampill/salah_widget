// One operator list is consumed by both contained VM preparation and the native driver.
(() => {
  const json=v=>JSON.parse(JSON.stringify(v));
  function visibleDelta(a,b){
    if(!a||!b||a.length!==144*232*4||b.length!==a.length)throw new Error('actual 144x232 RGBA required');
    let sum=0,max=0,changed=0,over5=0,alphaMax=0;
    for(let i=0;i<a.length;i+=4){let any=false,gt=false;alphaMax=Math.max(alphaMax,Math.abs(a[i+3]-b[i+3]));
      for(let k=0;k<3;k++){const d=Math.abs(a[i+k]*a[i+3]/255-b[i+k]*b[i+3]/255);sum+=d;max=Math.max(max,d);any ||= d!==0;gt ||= d>5;}
      changed+=any?1:0;over5+=gt?1:0;
    }
    return {changedVisiblePixels:changed,changedOver5:over5,meanAbsolutePremultipliedRGB:sum/(144*232*3),maxPremultipliedRGB:max,maxAlphaDelta:alphaMax,
      definition:'P_RGB = RGB*alpha/255; exact zero for equal-time current position-only operators; >5 is historical diagnostic, not calibrated perceptibility'};
  }
  const equal=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
  const protectedState=s=>Object.fromEntries(Object.entries(s.cloudState).filter(([k])=>!['wx','wy','wspd'].includes(k)));
  const persistent=s=>({population:s.axes.population,phase:s.axes.phase,life:s.axes.life,wander:s.axes.wander,key:s.axes.key});
  const finite=s=>s.axes.phase.length===3&&s.axes.life.length===3&&s.axes.phase.every(v=>Number.isFinite(v)&&v>=0&&v<1.25)
    &&[...s.axes.life,s.axes.wander].every(v=>Number.isFinite(v)&&v>=0&&v<4294967296)&&s.columns.length===144;
  window.__r0025Run=async({mode='preview',nativePixels=false,realElapsed=false,only=null,stopOnFailure=false}={})=>{
    const selected=only===null?null:typeof only==='string'?[only]:only;
    if(selected!==null&&(!Array.isArray(selected)||!selected.length||selected.some(n=>typeof n!=='string')||new Set(selected).size!==selected.length))throw new Error('invalid finite original selection');
    let stopped=false;
    const f=window.__r0025,cases=[],check=(ok,message)=>{if(!ok)throw new Error(message);};
    await f.init();f.traceEnabled(true);const initial=f.paint(),base=f.checkpoint();
    check(initial.trace.length>20&&finite(initial),'actual finite healthy painter bootstrap not reached');
    async function run(name,body){
      if(stopped||selected!==null&&!selected.includes(name))return; // selection only; original body/oracle remains unchanged
      const captures=[],checks=[];let reached=false;
      const capture=(label,value=f.paint())=>{const recorded={label,...value};captures.push(recorded);reached=true;return recorded;};
      const assert=(value,message)=>{checks.push({message,passed:!!value});check(value,message);};
      const pixelEqual=(a,b,message)=>{
        if(nativePixels)assert(visibleDelta(a.rgba,b.rgba).changedVisiblePixels===0,message);
        else checks.push({message,passed:null,status:'READY_FOR_NATIVE'});
      };
      const ready=message=>checks.push({message,passed:null,status:'READY_FOR_NATIVE'});
      try{f.restore(base);await body({capture,assert,pixelEqual,ready});cases.push({name,reached,terminal:true,status:'PASS',checks,captures,pixelOracle:nativePixels?'ACTUAL_NATIVE_RGBA':'NOT_EXECUTED'});}
      catch(error){cases.push({name,reached,terminal:true,status:'FAIL',error:String(error.message??error),checks,captures,pixelOracle:nativePixels?'ACTUAL_NATIVE_RGBA':'NOT_EXECUTED'});if(stopOnFailure)stopped=true;}
    }
    if(mode==='preview'){
      await run('adapter-first-image-parity',({capture,assert,pixelEqual})=>{
        f.traceEnabled(false);const a=capture('unwrapped-original-painter',f.paintUninstrumented());f.traceEnabled(true);const b=capture('traced-original-painter');
        assert(equal(a.axes,b.axes),'instrumentation retains actual axes');assert(equal(a.columns,b.columns),'instrumentation retains actual columns');pixelEqual(a,b,'instrumentation retains exact visible raw cloud color');
      });
      await run('no-op-equal-time',({capture,assert,pixelEqual})=>{const a=capture('before');f.wind({});const b=capture('after');
        assert(equal(a.trace,b.trace)&&equal(a.noise,b.noise)&&equal(a.columns,b.columns),'actual no-op canvas commands/noise/columns exact');
        assert(equal(persistent(a),persistent(b)),'actual no-op population/axes exact');pixelEqual(a,b,'actual no-op visible raw cloud color exact');});
      for(const [name,values] of [['wind-speed-3-to-3.1',{wind:3.1}],['wind-heading-225-to-45',{windDir:45}],
          ['wind-calm-3-to-0',{wind:0}],['wind-reversal-and-gust',{wind:9,windDir:45,gust:18}]]){
        await run(name,({capture,assert,pixelEqual})=>{const a=capture('before');f.wind(values);const b=capture('after');
          assert(!equal([a.cloudState.wx,a.cloudState.wy,a.cloudState.wspd],[b.cloudState.wx,b.cloudState.wy,b.cloudState.wspd]),'actual new admitted wind reaches render/applyCloudState');
          assert(equal(protectedState(a),protectedState(b)),'coverage/tint/light/target held for pure wind operator');
          assert(equal(persistent(a),persistent(b)),'same-monotonic-time wind cannot change captured population/axes');
          assert(equal(a.trace,b.trace)&&equal(a.noise,b.noise)&&equal(a.columns,b.columns),'same-time wind actual painter commands/noise/columns exact');
          pixelEqual(a,b,'same-time wind has zero premultiplied visible-color displacement');});
      }
      for(const [name,values] of [['canonical-preview-calm0-old-wind-500ms',{wind:0}],
          ['canonical-preview-heading45-wind3.1-old-wind-500ms',{wind:3.1,windDir:45}]]){
        await run(name,({capture,assert,pixelEqual,ready})=>{
          const a=capture('before'),cp=f.checkpoint();
          assert(q.get('simTime')==='18:10'&&q.get('timeScale')==='1'&&q.get('motion')==='full'&&!a.followWall&&a.timeScale===1&&!a.axes.paused&&!a.axes.reduced,
            'canonical A06 explicit active 1x preview admitted');
          assert(finite(a)&&a.columns.some(x=>x>0)&&a.trace.length>20,'canonical A06 established nonempty finite painter');
          f.setClock(a.clock.wallMs+500,a.clock.monoMs+500);f.wind(values);const b=capture('after-admission'),after=f.checkpoint();
          const ref=capture('independent-old-velocity-reference',f.referencePaint(a,{wx:a.cloudState.wx,wspd:a.cloudState.wspd}));
          f.restore(after);const negative=capture('independent-new-velocity-negative',f.referencePaint(a,{wx:b.cloudState.wx,wspd:b.cloudState.wspd}));
          f.restore(after);f.setClock(b.clock.wallMs+500,b.clock.monoMs+500);const next=capture('subsequent-new-velocity');
          const wrap=(v,p)=>{const remainder=v%p;return remainder<0?remainder+p:remainder;};
          b.elapsedLightingFields=Object.keys(protectedState(b)).filter(k=>!equal(a.cloudState[k],b.cloudState[k])).map(k=>({field:k,before:a.cloudState[k],after:b.cloudState[k]}));
          assert(b.civilMs-a.civilMs===500&&b.clock.monoMs-a.clock.monoMs===500,'canonical A06 civil and monotonic500ms');
          for(let di=0;di<3;di++){
            const expected=wrap(a.axes.phase[di]-a.cloudState.wx*a.cloudState.wspd*0.5*(0.024+di*0.006),1.25);
            assert(Math.abs(expected-b.axes.phase[di])<1e-10,'canonical A06 old velocity phase deck '+di);
            assert(wrap(a.axes.life[di]+0.5*(0.018+di*0.004),4294967296)===b.axes.life[di],'canonical A06 exact elapsed life deck '+di);
            const subsequent=wrap(b.axes.phase[di]-b.cloudState.wx*b.cloudState.wspd*0.5*(0.024+di*0.006),1.25);
            assert(Math.abs(subsequent-next.axes.phase[di])<1e-10,'canonical A06 subsequent new velocity deck '+di);
            assert(wrap(b.axes.life[di]+0.5*(0.018+di*0.004),4294967296)===next.axes.life[di],'canonical A06 subsequent elapsed life deck '+di);
          }
          assert(wrap(a.axes.wander+0.5*0.011,4294967296)===b.axes.wander&&wrap(b.axes.wander+0.5*0.011,4294967296)===next.axes.wander,'canonical A06 exact elapsed wander and subsequent interval');
          assert(a.axes.key===b.axes.key&&a.axes.population===b.axes.population&&finite(b)&&finite(next),'canonical A06 target/population finite and preserved');
          assert(equal(ref.axes.phase,b.axes.phase)&&equal(ref.columns,b.columns),'independent old-velocity state/column reference agrees');
          assert(!equal(ref.axes.phase,negative.axes.phase),'independent new-velocity negative changes expected motion state; quantized columns recorded separately');
          pixelEqual(b,ref,'canonical A06 actual native RGBA equals independent old-velocity reference at held elapsed lighting');
          if(nativePixels)assert(visibleDelta(ref.rgba,negative.rgba).changedVisiblePixels>0,'canonical A06 independent old/new velocity native RGBA negative discriminates');
          else ready('native old/new velocity negative READY_FOR_NATIVE; VM RGBA doubled and excluded');
        });
      }
    }else if(mode==='wall'){
      await run('old-wind-integrated-before-receipt',({capture,assert})=>{const a=capture('before');f.setClock(a.clock.wallMs+1000,a.clock.monoMs+1000);f.wind({wind:9,windDir:45,gust:18});const b=capture('after');
        const wind=a.cloudState.wx*a.cloudState.wspd;
        for(let i=0;i<3;i++){const expected=((a.axes.phase[i]-wind*(.024+i*.006))%1.25+1.25)%1.25;
          assert(Math.abs(expected-b.axes.phase[i])<1e-10,'receipt integrates old wind for deck '+i);}
        assert(finite(b),'receipt actual state/columns finite');});
      await run('positive-elapsed-30s',async({capture,assert})=>{const a=capture('before'),start=window.__r0025Boundary?.nativeNow?.();
        for(let i=1;i<=30;i++){
          if(realElapsed)await new Promise(resolve=>setTimeout(resolve,1000));
          const elapsed=realElapsed?window.__r0025Boundary.nativeNow()-start:i*1000;
          f.setClock(a.clock.wallMs+elapsed,a.clock.monoMs+elapsed);
          if(i===15)capture('mid-15s');else f.paint(undefined,{readPixels:false});
        }
        const b=capture('after-30s');assert(!equal(persistent(a),persistent(b)),'positive monotonic intervals advance actual cloud axes');
        assert(!equal(a.trace,b.trace),'positive elapsed actual puff geometry/morphology changes');assert(finite(b),'positive elapsed axes/columns finite');
        if(nativePixels)assert(visibleDelta(a.rgba,b.rgba).changedOver5>0,'positive native raw cloud visible-color control changes');
      });
      for(const [kind,stamp] of [['day','2026-09-09T00:00:00Z'],['month','2026-10-01T00:00:00Z'],['year','2027-01-01T00:00:00Z']]){
        await run(kind+'-boundary-vs-ordinary-76ms',({capture,assert,pixelEqual})=>{
          const B=Date.parse(stamp);f.establishWall(B-38);const a=capture('boundary-before'),cp=f.checkpoint();
          f.setClock(B+38,76);const b=capture('boundary-after');
          f.restore(cp);f.setClock(B-1000,0);const c=capture('ordinary-before');f.setClock(B-924,76);const d=capture('ordinary-after');
          assert(a.followWall&&b.followWall&&c.followWall&&d.followWall,'ordinary wall-following seam reached without changing explicit simulation anchor');
          assert(a.axes.population===b.axes.population,'civil '+kind+' boundary cannot reseed captured population');
          assert(equal(persistent(a),persistent(c))&&equal(persistent(b),persistent(d)),'boundary and ordinary axes controls agree');
          assert(equal(a.trace,c.trace)&&equal(b.trace,d.trace)&&equal(a.columns,c.columns)&&equal(b.columns,d.columns),'boundary and ordinary actual painter endpoints agree');
          pixelEqual(a,c,'boundary/ordinary raw visible before endpoints exact');pixelEqual(b,d,'boundary/ordinary raw visible after endpoints exact');
        });
      }
      await run('empty-deck-visible-negative-and-retained-time',({capture,assert,pixelEqual})=>{
        const a=capture('populated-before'),cov=[a.cloudState.covLow,a.cloudState.covMid,a.cloudState.covHigh],cp=f.checkpoint();
        f.clearCoverage();for(let i=1;i<=3;i++){f.setClock(a.clock.wallMs+i*1000,a.clock.monoMs+i*1000);f.paint(undefined,{readPixels:false});}
        const empty=capture('empty');
        f.setCoverage(cov);const b=capture('returned-populated');f.restore(cp);
        for(let i=1;i<=3;i++){f.setClock(a.clock.wallMs+i*1000,a.clock.monoMs+i*1000);f.paint(undefined,{readPixels:false});}
        const c=capture('never-empty-reference');
        assert(empty.trace.length===0&&empty.columns.every(x=>x===0),'empty deck paints no puffs/density');
        if(nativePixels)assert(empty.rgba.every(x=>x===0),'actual clear negative RGBA is empty');
        assert(!equal(persistent(a),persistent(empty)),'empty actual decks retain advancing motion axes');
        assert(equal(persistent(b),persistent(c))&&equal(b.trace,c.trace),'hidden empty deck population/time agrees with always-visible reference');
        pixelEqual(b,c,'restored population visible raw endpoint agrees with reference');
      });
      await run('visible-cell-periodic-wrap-1ms',({capture,assert})=>{
        f.paint();const edge=f.edge(),a=capture('before-wrap');f.setClock(a.clock.wallMs+1,a.clock.monoMs+1);const b=capture('after-wrap');
        const geometry=x=>x.trace.map(g=>g.geometry).sort((p,q)=>p[0]-q[0]||p[1]-q[1]);const aa=geometry(a),bb=geometry(b);
        assert(edge.index>=0&&edge.index<=6,'actual visible low-deck cell edge reached');
        assert(aa.length===bb.length&&aa.length>20,'periodic edge copies retain puff population across wrap');
        for(let i=0;i<aa.length;i++)for(let j=0;j<6;j++)assert(Math.abs(aa[i][j]-bb[i][j])<.01,'wrapped actual gradient geometry is continuous');
        assert(finite(a)&&finite(b),'wrapped state/canvas/columns bounded');
      });
    }else throw new Error('unsupported clock mode');
    f.restore(base);const terminal={schema:'r0025-operator-results/2',mode,nativePixels,realElapsed,cases,
      declared:selected!==null?selected.length:(mode==='preview'?8:7),selection:only,stoppedOnFailure:stopped,fullRecipeCount:15,executed:cases.length,passed:cases.filter(x=>x.status==='PASS').length,failed:cases.filter(x=>x.status!=='PASS').length,
      terminal:true,sourceConsumer:'actual current whole classic script; original paintClouds with transparent command/noise instrumentation',
      limits:nativePixels?'Detached native cloud canvas only. Crops require root visual review; not full physical sky, provider, terrain, default live-widget motion, platform completeness or closure.':'Contained VM commands/state only. RGBA boundary is doubled and receives no raster/motion credit.'};
    if(!stopped&&terminal.declared!==terminal.executed)throw new Error('missing declared operator terminal');return terminal;
  };
  window.__r0025VisibleDelta=visibleDelta;
})();
