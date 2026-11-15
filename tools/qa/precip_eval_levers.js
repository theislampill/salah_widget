// Precipitation-presentation EVALUATION overlay (research only; injected by tools/qa/precip_eval_capture.cjs into a
// served copy of the generated widget; NOT product code, NOT a merge candidate). It replaces the 32 DOM .drop streaks
// with one canvas layer inside #wxfx so that five independent levers can be switched on alone or in combination:
//   L1 intensity  — rate-driven drop size / streak length / fall speed / width / alpha (Marshall-Palmer D0 + Atlas v(D))
//   L2 slant      — streak lean = across-view wind / fall speed, per intensity; sign 'map' (current) or 'cloud'
//   L3 structure  — deterministic seeded advecting density field (sheets/bands), gust intermittency from wind_gusts_10m,
//                   per-cycle re-seeded drop positions (no fixed tracks), shower shafts sampled from the cloud columns
//   L4 atmosphere — rate-dependent horizon veil (rain extinction), sun corona/body glare attenuation, deck darkening,
//                   soft rain curtains under dense columns (all presentation CSS/canvas; copied sky core untouched)
//   L5 depth      — near/far streak populations (far: shorter, slower, fainter, thinner)
// With every lever off the overlay reproduces the current mapping (32 fixed columns, 12-21 px, 0.60-0.92 s, 1.5 px,
// --rain-op envelope, rainSlant = windX*wind01*120 px) so a lever is measured against the same renderer.
// Truth: draws nothing unless the widget itself published data-precip="on"; intensity only from the admitted
// selectedWeather().precip of the record the widget is showing. Inputs read: .c dataset, selectedWeather(), _colDens,
// cloudState tints, CSS --g3/--sunvx/--sunvy. Deterministic: frame(tMs) is a pure function of tMs and those inputs.
(function(){
  const CFG=Object.assign({levers:[],sign:'map',budget:32,rateFactor:4},window.__PE_CFG||{});
  const on=k=>CFG.levers.includes(k);
  const c=document.querySelector('.c'),fx=document.getElementById('wxfx');
  const st=document.createElement('style');
  st.textContent='.wfx .drop{visibility:hidden!important}'+
    '.c .pe-veil{position:absolute;inset:0;pointer-events:none;opacity:0}';
  document.head.appendChild(st);
  const cv=document.createElement('canvas');cv.className='pe-rain';cv.width=325;cv.height=530;
  cv.style.cssText='position:absolute;inset:0;width:100%;height:100%;pointer-events:none';
  const veil=document.createElement('div');veil.className='pe-veil';
  const firstDrop=fx.querySelector('.drop')||fx.querySelector('.bolt');
  fx.insertBefore(veil,firstDrop);fx.insertBefore(cv,firstDrop);
  const g=cv.getContext('2d');
  // curtains live on their own canvas (atmosphere, like the veil) so the measured streak layer is streaks only
  const cv2=document.createElement('canvas');cv2.className='pe-curtain';cv2.width=325;cv2.height=530;
  cv2.style.cssText='position:absolute;inset:0;width:100%;height:100%;pointer-events:none;filter:blur(5px)';fx.insertBefore(cv2,cv);
  const g2=cv2.getContext('2d');
  // ---- deterministic hashing / value noise ----
  const h1=(a,b)=>{let n=Math.imul(a|0,374761393)+Math.imul(b|0,668265263)+1013904223;n=Math.imul(n^(n>>>13),1274126177);return ((n^(n>>>16))>>>0)/4294967295;};
  const vn=(x,s)=>{const i=Math.floor(x),f=x-i,u=f*f*(3-2*f);return h1(i,s)+(h1(i+1,s)-h1(i,s))*u;};
  const vn2=(x,y,s)=>{const i=Math.floor(y),f=y-i,u=f*f*(3-2*f);return vn(x,s+i*7919)+(vn(x,s+(i+1)*7919)-vn(x,s+i*7919))*u;};
  const fbm2=(x,y,s)=>(vn2(x,y,s)*0.57+vn2(x*2.03,y*1.7,s+17)*0.29+vn2(x*4.1,y*2.9,s+31)*0.14);
  const clamp=(v,a=0,b=1)=>v<a?a:v>b?b:v;
  const ss=(a,b,x)=>{x=clamp((x-a)/(b-a));return x*x*(3-2*x);};
  // ---- physical relations (sources: README Part B) ----
  const lam=R=>4.1*Math.pow(Math.max(R,0.05),-0.21);            // Marshall-Palmer slope (mm^-1), R mm/h
  const vT=D=>Math.max(0.3,9.65-10.3*Math.exp(-0.6*D));          // Atlas et al. 1973 terminal velocity (m/s), D mm
  const sigma=R=>1.1394*Math.pow(Math.max(R,0),0.7057)/4.343;    // optical rain extinction (km^-1): Korai, Luini, Nebuloni 2018 Table 1, mu=1, dB/km -> km^-1
  let inputs=null,lastIn=-1e9;
  function read(t){
    if(inputs&&t-lastIn<500)return inputs; lastIn=t;
    let w=null;try{w=selectedWeather();}catch(e){}
    const ds=c.dataset,perm=ds.precip==='on',fxc=ds.fx||'';
    const cs=getComputedStyle(c),num=k=>parseFloat(cs.getPropertyValue(k))||0;
    let col=null;try{col=_colDens?Array.from(_colDens):null;}catch(e){}
    let tint=[90,98,112];try{tint=cloudState.tLow||tint;}catch(e){}
    const isSim=w&&w.src==='sim';
    const mm=w&&w.precip!=null?+w.precip:null;
    const R=mm==null?2:mm*(isSim?1:CFG.rateFactor);                // mm/h (live current = 15-min amount; see README)
    const wind=w&&w.wind!=null?+w.wind:0,dir=w&&w.windDir!=null?+w.windDir:225,gust=w&&w.gust!=null?+w.gust:wind;
    const windX=-Math.sin(dir*Math.PI/180);
    inputs={perm,fx:fxc,code:w?w.code:null,R,mm,wind,dir,gust,windX,col,tint,g3:cs.getPropertyValue('--g3').trim(),
      sunvx:num('--sunvx'),sunvy:num('--sunvy'),sunamt:num('--sunamt'),snow:fxc==='snow'};
    return inputs;
  }
  const Y0=0.19*530-10,TRAVEL=132;
  function params(I){
    const drizzle=I.fx==='drizzle',R=I.R,shower=I.code>=80&&I.code<=82;
    if(!on('L1')){ // current mapping
      const op=c.style.getPropertyValue('--rain-op')?parseFloat(c.style.getPropertyValue('--rain-op')):0.6;
      return {n:drizzle?11:32,len:i=>12+(i%4)*3,dur:i=>(0.6+(i%5)*0.08),width:1.5,alpha:op,vFall:null,drizzle,shower,R};
    }
    const D0=drizzle?0.32:3.67/lam(R),v=vT(D0);
    const pxps=42*v,len=Math.max(3,3.6*v),width=0.75+0.33*Math.min(D0,2.2);
    const n=drizzle?CFG.budget:Math.round(8+(CFG.budget-8)*clamp(Math.log10(R/0.5)/Math.log10(64)));
    const alpha=drizzle?0.40:0.62+0.38*clamp(Math.log10(R/0.5)/Math.log10(64));
    return {n,len:i=>len*(0.8+0.4*h1(i,5)),dur:i=>TRAVEL/(pxps*(0.9+0.2*h1(i,9))),width,alpha,vFall:v,D0,drizzle,shower,R};
  }
  function slantPerPx(I,P,gustF){ // horizontal px per vertical px
    if(!on('L2')){const w01=clamp((I.wind-0.5)/13.5);return I.windX*w01*120/TRAVEL;}
    const sgn=CFG.sign==='cloud'?-1:1,v=P.vFall||vT(3.67/lam(P.R));
    return clamp(sgn*I.windX*I.wind*gustF/v,-1.2,1.2);   // legibility cap: 50 deg from vertical
  }
  function colAt(I,x){ if(!I.col||!I.col.length)return 1;let mx=0;for(const v of I.col)if(v>mx)mx=v;if(mx<2)return 1;
    const k=Math.min(I.col.length-1,Math.max(0,Math.floor(x/325*I.col.length)));return I.col[k]/mx; }
  let lastT=0;
  function frame(t){
    lastT=t;const I=read(t);g.clearRect(0,0,325,530);g2.clearRect(0,0,325,530);
    const rec={t,drops:[],veil:0,perm:I.perm};
    if(!I.perm||I.snow){veil.style.opacity='0';window.__PE_LAST=rec;return rec;}
    const P=params(I),ts=t/1000;
    // gust intermittency (L3): slow deterministic gust envelope; amplitude from (gust - wind)
    const G=clamp((I.gust-I.wind-2)/14),gEnv=on('L3')?vn(ts/4.5,77):0.5;
    const gustF=on('L3')?1+0.6*G*(gEnv-0.5)*2:1;
    const k=slantPerPx(I,P,gustF);
    const adv=(CFG.sign==='cloud'?-1:1)*I.windX*Math.max(I.wind,0.5)*5;   // sheet advection px/s (screen)
    const field=x=>on('L3')?0.22+0.78*ss(0.34-0.16*G,0.70,fbm2((x-adv*ts)/95,ts/11,13)):1;
    const sigmaK=sigma(P.R),ext=1-Math.exp(-sigmaK*3);
    // L4: horizon veil + glare + deck darkening + curtains
    if(on('L4')){
      const a=(P.drizzle?0.30:0.48)*ext;rec.veil=a;
      veil.style.opacity=a.toFixed(3);
      veil.style.background=`linear-gradient(180deg,transparent 14%,rgba(${I.tint.map(v=>Math.round(v*0.78)).join(',')},0.55) 26%,rgba(${I.tint.map(v=>Math.round(v*0.86)).join(',')},0.9) 36%,rgba(${I.tint.map(v=>Math.round(v*0.86)).join(',')},0.55) 44%,transparent 56%)`;
      const T=Math.exp(-sigmaK*1.6);rec.glareT=T;
      document.querySelectorAll('.atmo .suncorner,.atmo .sunbody,.wfx .sunhaze').forEach(e=>e.style.filter=`opacity(${T.toFixed(3)})`);
      const b=1-0.32*clamp(Math.log10(P.R/0.5)/Math.log10(64));rec.deckB=b;
      const cc=document.querySelector('.wfx .cloudcanvas');if(cc)cc.style.filter=`blur(.55px) brightness(${b.toFixed(3)})`;
      // curtains: soft vertical shafts below the deck, weighted by column density and the advecting field
      const tc=I.tint.map(v=>Math.round(v*0.7));
      for(let x=0;x<325;x+=13){const d=colAt(I,x+6)*(on('L3')?0.35+0.65*field(x+6):1);if(d<0.25)continue;
        const lean=k*70,grd=g2.createLinearGradient(0,Y0+8,0,Y0+150);
        grd.addColorStop(0,`rgba(${tc},0)`);grd.addColorStop(0.25,`rgba(${tc},${(0.16*ext*d).toFixed(3)})`);grd.addColorStop(1,`rgba(${tc},0)`);
        g2.fillStyle=grd;g2.beginPath();g2.moveTo(x,Y0+8);g2.lineTo(x+13,Y0+8);g2.lineTo(x+13+lean,Y0+150);g2.lineTo(x+lean,Y0+150);g2.closePath();g2.fill();}
    } else veil.style.opacity='0';
    // streaks: drops are seen by refracted background + forward scatter; against a bright sky they read as
    // darker neutral streaks, against a dark sky as lit streaks (L1 only; off = the current pale blue)
    let sc=[185,220,245];
    if(on('L1')){const m=(I.g3.match(/[\d.]+/g)||[60,60,60]).map(Number),lum=0.2126*m[0]+0.7152*m[1]+0.0722*m[2],u=clamp((lum-110)/60);
      sc=[185+(92-185)*u,220+(106-220)*u,245+(124-245)*u].map(Math.round);}
    // streaks
    for(let i=0;i<P.n;i++){
      const dur=P.dur(i),ph=on('L3')||on('L1')?h1(i,3)*dur:-(-i*0.09),u=((ts+ph)/dur),cyc=Math.floor(u),f=u-cyc;
      let x0;
      if(on('L3')){ // re-seeded each cycle; showers importance-sample the dense columns
        const span=325+Math.abs(k)*TRAVEL*0.6,off=k>0?-Math.abs(k)*TRAVEL*0.6:0;   // upstream spawn so leaning drops cover the card
        const mid=xx=>xx+k*TRAVEL*0.45;                                             // density judged where the streak is mostly seen
        x0=off+h1(i*131+cyc,21)*span;
        for(let tries=0;tries<4&&colAt(I,mid(x0))<0.35;tries++)x0=off+h1(i*131+cyc,23+tries)*span;
      } else x0=((i*7.3+2)%100)/100*325;
      const far=on('L5')&&h1(i,41)<0.55;
      const cd=colAt(I,on('L3')?x0+k*TRAVEL*0.45:x0);
      let gate=on('L3')?ss(0.12,0.4,cd):(cd>0.16?1:0);
      if(!on('L3')&&I.col){let mx=0;for(const v of I.col)if(v>mx)mx=v;if(mx<2)gate=1;}
      if(gate<=0)continue;
      const env=f<0.22?f/0.22:f<0.6?1:(1-f)/0.4;               // the current keyframe envelope
      const yTop=Y0+(on('L5')&&far?14:0),travel=TRAVEL*(far?0.62:1);
      const y=yTop+f*(travel+10),x=x0+k*(y-yTop);
      const L=P.len(i)*(far?0.55:1),wdt=P.width*(far?0.7:1);
      const a=P.alpha*env*gate*(far?0.45:1)*(on('L3')?field(x):1);
      if(a<0.01)continue;
      const dx=k*L,grd=g.createLinearGradient(x-dx,y-L,x,y);
      grd.addColorStop(0,`rgba(${sc},0)`);grd.addColorStop(1,`rgba(${sc},${Math.min(1,a).toFixed(3)})`);
      g.strokeStyle=grd;g.lineWidth=wdt;g.lineCap='round';g.beginPath();g.moveTo(x-dx,y-L);g.lineTo(x,y);g.stroke();
      rec.drops.push([+x.toFixed(1),+y.toFixed(1),+L.toFixed(1),+a.toFixed(3),far?1:0,i,cyc]);
    }
    rec.colProfile=Array.from({length:13},(_,j)=>+colAt(I,j*25+12).toFixed(2));rec.field=Array.from({length:13},(_,j)=>+field(j*25+12).toFixed(2));
    rec.sc=sc;rec.g3=I.g3;
    rec.k=k;rec.R=P.R;rec.n=P.n;rec.vFall=P.vFall;rec.D0=P.D0;rec.ext=ext;
    window.__PE_LAST=rec;return rec;
  }
  window.__peFrame=frame;
  window.__peCfg=CFG;
  if(!CFG.manual){let t0=performance.now();const loop=()=>{frame(performance.now()-t0);requestAnimationFrame(loop);};requestAnimationFrame(loop);}
})();
