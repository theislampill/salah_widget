// Precipitation MODEL prototypes M1-M5 (research only; injected by tools/qa/precip_models_capture.cjs into a served
// copy of the generated widget; NOT product code, NOT a merge candidate). Implements the candidate models of the
// precipitation model advisory (2026-11-15) from one shared pure regime() table so that models differ in MODEL,
// not in tuning.
//
// DECLARED DEPICTION CONVENTION (regime-independent; the only licence taken):
//   f   = 265 px      focal length of the card camera (530/2 / tan 45 deg; 13 arcmin per px)
//   T   = 1/60 s      exposure = display frame interval (streaks abut, no strobe)
//   G   = 100         one global contrast gain on the physical streak contrast dI = 4 f a^2/(z v T) (L_env - L_b)
//   ZN  = [0.5,1.0] m near shell in which discrete streaks are drawn (M1, M3, M4 accent)
//   ZM  = [0.7,1.5] m near shell for the large-drop tail (M2/M5, D >= 1.5 mm)
//   mid texture: 1.5 m .. z_res(D) = f v(D) T / 3 (streak still >= 3 px long), D >= 0.3 mm (M2/M5 sheets)
//   veil: alpha = 1 - exp(-sigma(R) L(y)), L(y) = H / sin(e(y)) through rain below the cloud base, no gain
//   rain is drawn only inside #wxfx, rows y < 300 (fade 255-300) so the prayer-list backdrop is not veiled.
// Everything that differs between regimes comes from the physical relations in regime(): drop-size distribution,
// terminal velocity, number density, extinction, cloud-base height, lean tan(phi) = u_r / v_t(D).
// Lean sign: cross-view wind u_r = S sin(a - theta) with camera azimuth a = 180 deg, i.e. the SAME screen direction as
// the product's cloud drift (west wind -> screen-left). Gust: sigma_u = (gust - wind)/3, coherent across the view,
// seeded value noise with an 8 s scale; each drop lags by its relaxation time v/g. Colour of every element is the
// drop's environment: a heavily blurred copy of the composed sky + deck (+ Sun / eligible Moon kernels) drawn
// source-over, so contrast sign and magnitude follow L_env - L_b and nothing glows without a lit source.
// Truth: draws nothing unless the widget published data-precip="on"; the rate comes from the admitted amount.
(function(){
  if(window.__PM)return;
  // ===== ALL MODEL-DEPENDENT NUMBERS (provisional until the independent verifier establishes them) =====
  // Override any of them by setting window.__PM_PARAMS before injection.
  const P=Object.assign({
    T:1/60,            // exposure (s) = display frame interval
    G:100,             // global contrast gain (depiction licence)
    nearShell:[0.5,1.0], nearDmin:0.3,          // M1/M3/M4 discrete streak shell (m) and minimum D (mm)
    tailShell:[0.7,1.5], tailDmin:1.5,          // M2/M5 large-drop tail shell
    midSlabs:[[1.5,3],[3,10]], midDmin:0.3, resolvablePx:3,   // M2/M5 texture slabs, cut where streaks < 3 px
    frustumK:0.355,    // band frustum volume factor: V = K (z2^3 - z1^3) m^3 for rows YTOP..YBOT
    dsd:{mp:[8000,4.1],drizzle:[30000,5.7],convective:[1400,3.0],exp:-0.21},   // N0 (m^-3 mm^-1), Lambda = a R^exp
    vt:'atlas+GK', // v = 9.65 - 10.3 e^(-0.6 D) for D >= 0.5 mm (Atlas); Gunn-Kinzer table (recalled) below
    baseMPerC:125, baseMin:100, baseMax:2000,   // cloud-base height from dew-point spread
    eyeLevel:0.8,      // 10 m wind -> drop-height wind factor (1/7 law)
    gustPeak:3, gustScaleS:8,                   // sigma_u = (gust - wind)/gustPeak, realisation time scale
    shaftPathKm:1.5, shaftTrail:0.21,           // shaft path through rain, trail slope against drift (~12 deg)
    fibrePathKm:0.6, minRateMmH:0.1,            // edge-on rain under the base; category-only minimum-rate depiction
    rateFactor:4,      // live current amount (mm per 900 s interval) -> mm/h, as the product's own label does
    // ---- regime-dependent or non-physical parameters, each labelled [physics] / [convention] / [visibility aid] ----
    drizzleSigmaZero:true,     // [convention] drizzle veil left to the product's own visibility->aerosol path (no double count); not a derivation
    struct:{drizzle:[0.05,8],light:[0.1,8],moderate:[0.2,8],heavy:[0.45,3.5],heavySheets:[0.35,2.5],rModerate:2.5,rHeavy:7.6},   // [convention] M3/M5 field amplitude, time scale (s); NOT derived from the DSD
    showersVeil:'field-only',  // [physics] a cell-mean rate is not local: showers veil only where the M3/M5 field localises it; none in M1/M2/M4
    m4StreakFrac:0.15,         // [visibility aid] M4 keeps 15 % of the M1 streak population
    fibre:{count:70,lenBasePx:10,lenGainPx:60,widthPx:[2,5],colour:0.8},   // [visibility aid] M4/M5 base fibres; strength = 1 - e^(-sigma*fibrePathKm), rate enters only via sigma
    sunKernel:{amp:0.55,sigmaPx:120},     // [convention] area-fraction rule approximated by a gaussian around the visible Sun, x (1 - cloud^2)
    moonKernel:{amp:0,sigmaPx:120},       // [visibility aid if > 0] REMOVED by default (review F-5: magnitude not derived)
    tile:{w:352,h:320,cap:9000},          // [convention] M2/M5 texture tile larger than the band in both axes (no in-frame repeat)
    render:{alphaCap:0.92,lineMin:1,lineFloor:0.6,lineMax:2.2,ytop:8,ybot:300,yfade:255,sunDimMinDeg:3},   // [convention] rendering licences
  },window.__PM_PARAMS||{});
  let T=P.T,G=P.G;const DEG=Math.PI/180,W=325,H=530,YTOP=8,YBOT=300,YFADE=255;
  // camera: the refined-sky camera from the fragment (skyAz/skyAlt), defaults 180/45
  const hq=new URLSearchParams(location.hash.slice(1)),CAM={az:+(hq.get('skyAz')||180),alt:+(hq.get('skyAlt')||45),fov:+(hq.get('skyFov')||90)};
  const F=265/Math.tan(CAM.fov/2*Math.PI/180);
  const c=document.querySelector('.c'),fx=document.getElementById('wxfx');
  const css=document.createElement('style');css.id='pm-style';document.head.appendChild(css);
  const mk=(cls,z)=>{const e=document.createElement('canvas');e.className=cls;e.width=W;e.height=H;e.style.cssText='position:absolute;inset:0;width:100%;height:100%;pointer-events:none';return e;};
  const cv=mk('pm-rain'),g=cv.getContext('2d');
  const anchor=fx.querySelector('.drop')||fx.querySelector('.bolt');fx.insertBefore(cv,anchor);
  const envS=document.createElement('canvas');envS.width=41;envS.height=67;const es=envS.getContext('2d',{willReadFrequently:true});
  const envT=document.createElement('canvas');envT.width=41;envT.height=67;const et=envT.getContext('2d',{willReadFrequently:true});
  const envF=mk('pm-envf');const ef=envF.getContext('2d');           // full-size env (for source-in fills)
  const lay=mk('pm-lay');const lg=lay.getContext('2d');              // scratch layer
  // ---------- deterministic noise ----------
  const h1=(a,b)=>{let n=Math.imul(a|0,374761393)+Math.imul(b|0,668265263)+1013904223;n=Math.imul(n^(n>>>13),1274126177);return ((n^(n>>>16))>>>0)/4294967295;};
  const vn=(x,s)=>{const i=Math.floor(x),f=x-i,u=f*f*(3-2*f);return h1(i,s)+(h1(i+1,s)-h1(i,s))*u;};
  const clamp=(v,a=0,b=1)=>v<a?a:v>b?b:v;
  // ---------- physics ----------
  const GK=[[0.1,0.27],[0.2,0.72],[0.3,1.17],[0.4,1.62],[0.5,2.06]];   // Gunn-Kinzer below 0.5 mm (recalled values; Atlas fit is poor there)
  const vT=D=>{if(D>=0.5)return 9.65-10.3*Math.exp(-0.6*D);if(D<=0.1)return 0.27*D/0.1;for(let i=1;i<GK.length;i++)if(D<=GK[i][0]){const [d0,v0]=GK[i-1],[d1,v1]=GK[i];return v0+(v1-v0)*(D-d0)/(d1-d0);}return 2.06;};   // m/s, D mm
  function regime(I){
    const code=I.code,cls=I.fx,R=Math.max(0,I.R),shower=code>=80&&code<=82,drizzle=cls==='drizzle';
    // DSD families: stratiform Marshall-Palmer; drizzle and convective (Joss-Waldvogel-type, RECALLED, unverified)
    const mkF=(k,name)=>({N0:P.dsd[k][0],L:P.dsd[k][1]*Math.pow(Math.max(R,0.05),P.dsd.exp),name});
    const fam=drizzle?mkF('drizzle','drizzle (JW, recalled)'):shower?mkF('convective','convective (JW, recalled)'):mkF('mp','Marshall-Palmer');
    const Nabove=Dc=>fam.N0/fam.L*Math.exp(-fam.L*Dc);                        // per m^3
    // extinction sigma = (pi/2) int D^2 N dD = pi N0 / L^3 (mm^2/m^3 -> km^-1 x1e-3)
    const sigma=(drizzle&&P.drizzleSigmaZero)?0:Math.PI*fam.N0/Math.pow(fam.L,3)*1e-3;              // km^-1 (drizzle: existing product vis path only)
    const sampleD=(u,Dc)=>Dc-Math.log(1-u*0.999)/fam.L;                      // truncated exponential above Dc
    // cloud-base height from the dew-point spread (125 m per degC, recalled approximation), bounded
    const Hm=clamp(P.baseMPerC*Math.max(0.5,I.spreadC),P.baseMin,P.baseMax);
    return {R,shower,drizzle,fam,Nabove,sigma,sampleD,Hm,vis:I.vis};
  }
  // ---------- inputs ----------
  let I=null,lastIn=-1e9,envAt=-1e9,envData=null,drift={px:0,prev:null,at:0,vx:0};
  function readInputs(t){
    if(I&&t-lastIn<500){I.perm=c.dataset.precip==='on';I.fx=c.dataset.fx||'';return I;}lastIn=t;   // authority read every frame (no cache lag)
    let w=null;try{w=selectedWeather();}catch(e){}
    const ds=c.dataset,cs=getComputedStyle(c),num=k=>parseFloat(cs.getPropertyValue(k));
    let col=null;try{col=_colDens?Array.from(_colDens):null;}catch(e){}
    let q=null;try{q=window.qaState();}catch(e){}
    const toC=v=>v==null?null:((w&&w.units||'f')==='f'?(v-32)*5/9:v);
    const tC=w?toC(w.temp):null,dC=w?toC(w.dew):null;
    const mm=w&&w.precip!=null?+w.precip:null,isSim=w&&w.src==='sim';
    const mt=q&&q.moonTruth||{};
    I={perm:ds.precip==='on',fx:ds.fx||'',code:w?+w.code:null,mm,R:mm==null?0:mm*(isSim?1:P.rateFactor),
      wind:w&&w.wind!=null?+w.wind:0,dir:w&&w.windDir!=null?+w.windDir:225,gust:w&&w.gust!=null?+w.gust:null,
      spreadC:tC!=null&&dC!=null?tC-dC:3,vis:w&&w.vis!=null?+w.vis:20000,cloud:w&&w.cloud!=null?w.cloud/100:1,col,
      sunvx:num('--sunvx'),sunvy:num('--sunvy'),sunamt:num('--sunamt')||0,sunEl:q?q.sunEl:null,
      moonLit:+(mt.moonlightOpacity||0),moonAlt:mt.moonAltitudeDeg};
    const mEl=document.querySelector('.moon');I.moon=null;
    if(mEl&&I.moonLit>0.02){const r=mEl.getBoundingClientRect(),cr=c.getBoundingClientRect();I.moon={x:r.x-cr.x+r.width/2,y:r.y-cr.y+r.height/2};}
    return I;
  }
  // environment = drop's ~30 deg neighbourhood: blurred composed sky + deck, plus Sun and eligible-Moon kernels
  function updateEnv(t,I){
    if(t-envAt<1000&&envData)return;envAt=t;
    const sky=document.querySelector('.real-sky-canvas'),cc=document.querySelector('.wfx .cloudcanvas');
    et.clearRect(0,0,41,67);
    try{if(sky)et.drawImage(sky,0,0,41,67);}catch(e){}
    try{if(cc&&getComputedStyle(cc).display!=='none')et.drawImage(cc,0,0,41,67);}catch(e){}
    const d=et.getImageData(0,0,41,67);
    // light kernels (area-fraction rule ~ gaussian, 120 px), Sun only through the direct-beam fraction 1 - cloud^2
    const add=(x,y,col,amt,sg)=>{for(let j=0;j<67;j++)for(let i=0;i<41;i++){const dx=(i*8+4-x),dy=(j*8+4-y),k=Math.exp(-(dx*dx+dy*dy)/(2*sg*sg))*amt,o=(j*41+i)*4;
      for(let m=0;m<3;m++)d.data[o+m]=Math.min(255,d.data[o+m]+col[m]*k);}};
    if(I.sunamt>0.02&&I.sunEl!=null&&I.sunEl>-1)add(I.sunvx/100*W,I.sunvy/100*H,[255,240,215],P.sunKernel.amp*I.sunamt*(1-I.cloud*I.cloud),P.sunKernel.sigmaPx);
    if(I.moon&&P.moonKernel.amp>0)add(I.moon.x,I.moon.y,[205,215,235],P.moonKernel.amp*I.moonLit,P.moonKernel.sigmaPx);
    et.putImageData(d,0,0);
    es.clearRect(0,0,41,67);es.filter='blur(12px)';
    for(let k=0;k<3;k++)es.drawImage(envT,0,0);es.filter='none';                       // repeated for edge fill
    envData=es.getImageData(0,0,41,67).data;
    ef.clearRect(0,0,W,H);ef.imageSmoothingEnabled=true;ef.drawImage(envS,0,0,W,H);
  }
  const envAtPx=(x,y)=>{const i=clamp(Math.floor(x/8),0,40),j=clamp(Math.floor(y/8),0,66),o=(j*41+i)*4;return [envData[o],envData[o+1],envData[o+2]];};
  // cloud drift in px/s measured from the deck's own column profile (shares the cloud motion owner)
  function updateDrift(t,I){
    if(!I.col||t-drift.at<1000)return;const dt=(t-drift.at)/1000;drift.at=t;const cur=I.col;
    if(drift.prev&&dt<3){let best=0,bs=-1e9;for(let s=-8;s<=8;s++){let a=0;for(let i=8;i<cur.length-8;i++)a+=cur[i]*drift.prev[i-s];if(a>bs){bs=a;best=s;}}
      drift.vx=0.7*drift.vx+0.3*(best*W/cur.length/dt);}
    drift.prev=cur.slice();
  }
  const elev=y=>CAM.alt+Math.atan((265-y)/F)/DEG;                    // refined-sky camera rows -> elevation (deg)
  // ---------- wind ----------
  function windAt(I,t,D){
    // cross-view u_r = S sin(a - theta) (+ = screen-right), along-view u_f = -S cos(theta - a) (+ = away from viewer)
    // default a = 180: west wind (theta 270) -> u_r = -S -> screen-LEFT, the product's cloud-drift direction
    const S=P.eyeLevel*I.wind,ur=S*Math.sin((CAM.az-I.dir)*DEG),uf=-S*Math.cos((I.dir-CAM.az)*DEG);
    const sg=I.gust!=null&&I.gust>I.wind?P.eyeLevel*(I.gust-I.wind)/P.gustPeak:0;
    const lag=(vT(D)/9.81)*1000;
    const n=sg?(vn((t-lag)/(P.gustScaleS*1000),7)*2-1)*1.7:0;               // ~unit-variance seeded realisation
    return {ur:ur+sg*n*Math.sign(ur||1),uf};
  }
  // ---------- structure field (M3/M5) ----------
  function field(I,Rg,t){
    const N=65,rho=new Float32Array(N);
    const smooth=[];if(I.col){const n=I.col.length;for(let k=0;k<N;k++){const x=(k+0.5)/N*n;let s=0,ws=0;for(let i=0;i<n;i++){const w=Math.exp(-((i-x)*(i-x))/(2*36));s+=w*I.col[i];ws+=w;}smooth.push(s/ws);}}
    const mx=Math.max(1e-6,...(smooth.length?smooth:[1]));
    const sh=drift.px;
    if(Rg.shower&&smooth.length){                                          // shafts bound to deck clusters (peaks of the column profile)
      const pk=[];for(let k=1;k<N-1;k++)if(smooth[k]>=smooth[k-1]&&smooth[k]>smooth[k+1]&&smooth[k]>0.55*mx)pk.push(k);
      for(let k=0;k<N;k++){let s=0;for(const p of pk){const w=3.2;s+=(smooth[p]/mx)*Math.exp(-((k-p)*(k-p))/(2*w*w));}rho[k]=s;}
    } else {
      const S=P.struct,heavy=Rg.R>=S.rHeavy&&!Rg.drizzle,k0=Rg.drizzle?S.drizzle:heavy?S.heavy:Rg.R>=S.rModerate?S.moderate:S.light,amp=k0[0],scale=k0[1];
      for(let k=0;k<N;k++){const x=k*5-sh;rho[k]=1+amp*(vn(x/90+t/1000/scale,31)*2-1)+(heavy?S.heavySheets[0]*(vn(x/45-t/1000/S.heavySheets[1],57)*2-1):0);}
      if(smooth.length)for(let k=0;k<N;k++)rho[k]*=clamp((smooth[k]/mx-0.12)/0.3);   // no rain without cloud above (gate H)
    }
    let mean=0;for(let k=0;k<N;k++){rho[k]=Math.max(0,rho[k]);mean+=rho[k]/N;}
    if(mean>0)for(let k=0;k<N;k++)rho[k]/=mean;                            // mean rate conserved
    return {rho,at:x=>rho[clamp(Math.floor(x/5),0,N-1)]};
  }
  // soft elements (shafts, base fibres) are drawn on a quarter-resolution canvas and upscaled with smoothing:
  // the same softness as a blur filter at a fraction of the cost (a ctx.filter blur dropped real-time fps to 7-13)
  const low=document.createElement('canvas');low.width=82;low.height=133;const lw=low.getContext('2d');
  function softBegin(){lw.setTransform(1,0,0,1,0,0);lw.clearRect(0,0,82,133);lw.setTransform(82/W,0,0,133/H,0,0);return lw;}
  function softEnd(){g.save();g.imageSmoothingEnabled=true;g.imageSmoothingQuality='high';g.drawImage(low,0,0,W,H);g.restore();}
  // ---------- layers ----------
  const mask=mk('pm-mask'),mg=mask.getContext('2d'),colC=document.createElement('canvas');colC.width=65;colC.height=1;const cg=colC.getContext('2d');
  function buildMask(grd,fld,scale){mg.globalCompositeOperation='source-over';mg.clearRect(0,0,W,H);mg.fillStyle=grd;mg.fillRect(0,YTOP,W,YBOT-YTOP);
    if(fld){const id=cg.createImageData(65,1);for(let k=0;k<65;k++){id.data[k*4+3]=Math.round(255*clamp(fld.rho[k]*(scale||1)));}cg.putImageData(id,0,0);
      mg.globalCompositeOperation='destination-in';mg.imageSmoothingEnabled=true;mg.drawImage(colC,0,YTOP,W,YBOT-YTOP);mg.globalCompositeOperation='source-over';}
    return mask;}
  function veilLayer(I,Rg,fld,strength){
    const sig=Rg.sigma;if(!(sig>0))return 0;
    if(Rg.shower&&P.showersVeil==='field-only'&&!fld)return 0;            // a cell mean is not a local rate
    lg.clearRect(0,0,W,H);lg.globalCompositeOperation='source-over';lg.drawImage(envF,0,0);
    lg.globalCompositeOperation='destination-in';
    const grd=lg.createLinearGradient(0,YTOP,0,YBOT);let maxA=0;
    for(let y=YTOP;y<=YBOT;y+=12){const e=elev(y),L=Rg.Hm/Math.sin(e*DEG)/1000;let a=(1-Math.exp(-sig*L))*strength*(y>YFADE?clamp((YBOT-y)/(YBOT-YFADE)):1);
      maxA=Math.max(maxA,a);grd.addColorStop((y-YTOP)/(YBOT-YTOP),`rgba(0,0,0,${a.toFixed(4)})`);}
    lg.drawImage(buildMask(grd,fld,1),0,0);
    lg.globalCompositeOperation='source-over';g.drawImage(lay,0,0);return maxA;
  }
  function shafts(I,Rg,fld,t){
    if(!Rg.shower||!fld)return 0;let n=0;
    const cb=colBases(),b0=deckBase(I);const g=softBegin();
    for(let k=0;k<65;k++){const r=fld.rho[k];if(r<0.6)continue;n++;const bb=cb?cb[Math.min(cb.length-1,Math.floor((k*5+2)/W*cb.length))]:-1,base=bb>20?bb:b0;
      const Rl=Rg.R*r,lam=P.dsd.convective[1]*Math.pow(Math.max(Rl,0.05),P.dsd.exp),sl=Math.PI*P.dsd.convective[0]/Math.pow(lam,3)*1e-3;   // local convective sigma
      const a=(1-Math.exp(-sl*P.shaftPathKm))*clamp((r-0.6)/0.6);                  // 1.5 km shaft path (declared typical shaft width)
      const x=k*5,col=envAtPx(x,base+10).map(v=>Math.round(v*0.86)),trail=-Math.sign(drift.vx||0)*P.shaftTrail;   // ~12 deg trail against drift
      const grd=g.createLinearGradient(0,base,0,YBOT);grd.addColorStop(0,`rgba(${col},0)`);grd.addColorStop(0.15,`rgba(${col},${a.toFixed(3)})`);
      grd.addColorStop(0.75,`rgba(${col},${(a*0.8).toFixed(3)})`);grd.addColorStop(1,`rgba(${col},0)`);
      g.fillStyle=grd;g.beginPath();g.moveTo(x-1,base);g.lineTo(x+6,base);g.lineTo(x+6+trail*(YBOT-base),YBOT);g.lineTo(x-1+trail*(YBOT-base),YBOT);g.closePath();g.fill();}
    softEnd();return n;
  }
  function deckBase(I){                                                  // lowest row with appreciable deck alpha (cloud canvas 144x232)
    const cc=document.querySelector('.wfx .cloudcanvas');if(!cc)return 120;
    if(deckBase.at&&performance.now()-deckBase.at<2000)return deckBase.v;
    try{const d=cc.getContext('2d').getImageData(0,0,cc.width,cc.height).data;let yb=0;
      for(let y=0;y<cc.height;y++){let s=0;for(let x=0;x<cc.width;x++)s+=d[(y*cc.width+x)*4+3];if(s/cc.width>40)yb=y;}
      deckBase.v=Math.max(60,Math.min(200,yb/cc.height*H*0.95));}catch(e){deckBase.v=120;}
    deckBase.at=performance.now();return deckBase.v;
  }
  const yband=(y)=>y<YTOP?0:y>YBOT?0:y>YFADE?(YBOT-y)/(YBOT-YFADE):1;
  // discrete streaks: count = N(>Dc) x shell volume (band frustum 0.355 (z2^3 - z1^3) m^3), z uniform in volume,
  // D from the number distribution; length f |V| T / z, alpha = G 4 f a^2 / (z |V| T), colour = environment
  function streaks(I,Rg,t,opt){
    const z1=opt.z1,z2=opt.z2,Dc=opt.Dc,vol=P.frustumK*(z2*z2*z2-z1*z1*z1);
    let count=Rg.Nabove(Dc)*vol*(opt.frac||1);const cap=opt.cap||600,drawn=Math.min(cap,Math.round(count));
    if(COMP&&count>drawn)opt.comp=count/drawn;                                // shell study: keep the summed contrast when the drawn sample is capped
    const CY=180;let n=0,sumA=0;const angs=[],lens=[];
    const rig=opt.frame==='rigid';
    for(let i=0;i<drawn;i++){
      const ph=h1(i,11)*CY,u=(t+ph)/CY,k=Math.floor(u),fr=u-k,s=i*7919+k*104729;
      const D=Rg.sampleD(h1(s,1),Dc),zz=Math.cbrt(z1*z1*z1+h1(s,2)*(z2*z2*z2-z1*z1*z1)),v=vT(D);
      const wnd=windAt(I,t,D);
      let x0=h1(s,3)*W,y0=YTOP+h1(s,4)*(YBOT-YTOP);
      if(opt.fld){let tries=0;while(tries<5&&h1(s,30+tries)>opt.fld.at(x0)/2.5){tries++;x0=h1(s,40+tries)*W;}if(tries>=5)continue;}
      // image velocity (px/s)
      let vx,vy;
      if(!rig){const e=elev(y0)*DEG;vx=F*wnd.ur/zz;vy=F*(v*Math.cos(e)+wnd.uf*Math.sin(e))/zz;}   // parallel layout, foreshortened per row
      else{const Vw=window.__PMGEOM.dropVelocity(I.dir,P.eyeLevel*I.wind,v);                     // rectilinear camera: fan from the radiant
        const gw=wnd.ur-P.eyeLevel*I.wind*Math.sin((CAM.az-I.dir)*DEG);const br=window.__PMGEOM.basis(CAM.az,0).rt;   // gust along the cross-view axis
        const V=[Vw[0]+gw*br[0],Vw[1]+gw*br[1],Vw[2]];[vx,vy]=window.__PMGEOM.imageVelocity({az:CAM.az,alt:CAM.alt,fov:CAM.fov,W,H},x0,y0,zz,V);}
      if(vy<=1)continue;
      const sp=Math.hypot(vx,vy),Lp=sp*T,ux=vx/sp,uy=vy/sp;
      const x=x0+vx*(fr-0.5)*CY/1000,y=y0+vy*(fr-0.5)*CY/1000;
      if(opt.front!=null){if((t-(k*CY-ph))<opt.front*1000)continue;const fy=YTOP+vy*opt.front;if(y-Lp<fy)continue;}   // emitted after expiry: never drawn   // nothing emitted after expiry enters from above
      const a=D/2/1000,alpha=Math.min(P.render.alphaCap,G*4*F*a*a/(zz*Math.hypot(wnd.ur,v)*T)*(opt.comp||1))*yband(y);
      if(alpha<0.01||x<-60||x>W+60)continue;
      const e=envAtPx(x,y);g.strokeStyle=`rgba(${e[0]},${e[1]},${e[2]},${alpha.toFixed(3)})`;
      g.lineWidth=Math.max(P.render.lineMin,Math.min(P.render.lineMax,F*D/1000/zz+P.render.lineFloor));g.beginPath();g.moveTo(x-ux*Lp,y-uy*Lp);g.lineTo(x,y);g.stroke();
      n++;sumA+=alpha;angs.push(Math.atan2(ux,uy)/DEG);lens.push(Lp);
    }
    const q=(a,p)=>{if(!a.length)return null;const b=a.slice().sort((x,y)=>x-y);return +b[Math.min(b.length-1,Math.floor(p*b.length))].toFixed(2);};
    const mA=angs.length?angs.reduce((x,y)=>x+y,0)/angs.length:0,sdA=angs.length?Math.sqrt(angs.reduce((x,y)=>x+(y-mA)*(y-mA),0)/angs.length):null;
    return {count:Math.round(count),drawn:n,meanAlpha:n?sumA/n:0,angleMean:+mA.toFixed(2),angleSd:sdA==null?null:+sdA.toFixed(2),lenP10:q(lens,0.1),lenP50:q(lens,0.5),lenP90:q(lens,0.9)};
  }
  // mid-depth texture sheets (M2/M5): DSD-derived alpha masks generated once per regime, scrolled with parallax
  let tiles=null,tileKey='';
  function buildTiles(I,Rg){
    const key=[Rg.fam.name,Rg.R.toFixed(2)].join('|');if(key===tileKey)return;tileKey=key;tiles=[];
    for(const [zA,zB] of P.midSlabs){
      const tw=P.tile.w,th=P.tile.h,cvT=document.createElement('canvas');cvT.width=tw;cvT.height=th;const tg=cvT.getContext('2d');
      // count per tile: sum over D bins of N(D) dD x volume(zA, min(zB, z_res(D))) x tile area / band area
      let total=0;const bins=[];
      for(let D=P.midDmin;D<6;D+=0.1){const N=Rg.fam.N0*Math.exp(-Rg.fam.L*D)*0.1,zr=Math.min(zB,F*vT(D)*T/P.resolvablePx);if(zr<=zA)continue;
        const vol=P.frustumK*(zr*zr*zr-zA*zA*zA),cnt=N*vol*(tw*th)/(W*(YBOT-YTOP));bins.push([D,cnt,zr]);total+=cnt;}
      const cap=P.tile.cap,scale=total>cap?total/cap:1;let made=0;
      tg.lineCap='butt';
      for(const [D,cnt,zr] of bins){const m=Math.round(cnt/scale);for(let i=0;i<m;i++){const s=made++;
        const zz=Math.cbrt(zA*zA*zA+h1(s,5+zA*10|0)*(zr*zr*zr-zA*zA*zA)),v=vT(D),L=F*v*T/zz,a=D/2000;
        const al=Math.min(0.9,G*4*F*a*a/(zz*v*T)*scale);
        const x=h1(s,6)*tw,y=h1(s,7)*th;tg.strokeStyle=`rgba(255,255,255,${al.toFixed(3)})`;tg.lineWidth=1;
        for(const oy of [0,-th,th])for(const ox of [0,-tw,tw]){tg.beginPath();tg.moveTo(x+ox+0.5,y+oy-L);tg.lineTo(x+ox+0.5,y+oy);tg.stroke();}}}
      tiles.push({cv:cvT,zMean:(zA+zB)/2*0.8,vMean:vT(Math.max(0.6,3.67/Rg.fam.L)),total,scale});
    }
  }
  function sheets(I,Rg,t,fld,front){
    buildTiles(I,Rg);lg.clearRect(0,0,W,H);lg.globalCompositeOperation='source-over';
    const wnd=windAt(I,t,1.5);
    for(const tl of tiles){const vy=F*tl.vMean/tl.zMean,vx=F*wnd.ur/tl.zMean,tan=wnd.ur/tl.vMean;
      const TW=tl.cv.width,TH=tl.cv.height,oy=((t/1000*vy)%TH+TH)%TH,ox=((t/1000*vx)%TW+TW)%TW;
      lg.save();lg.setTransform(1,0,tan,1,-tan*H/2,0);
      for(let yy=-TH+oy;yy<H;yy+=TH)for(let xx=-TW+ox-TW;xx<W+TW;xx+=TW)lg.drawImage(tl.cv,xx,yy);   // tile larger than the band: no in-frame repeat
      lg.restore();}
    // mask: band rows, structure field; colourise with the environment
    lg.globalCompositeOperation='destination-in';
    const grd=lg.createLinearGradient(0,YTOP,0,YBOT);grd.addColorStop(0,'rgba(0,0,0,1)');grd.addColorStop((YFADE-YTOP)/(YBOT-YTOP),'rgba(0,0,0,1)');grd.addColorStop(1,'rgba(0,0,0,0)');
    lg.drawImage(buildMask(grd,fld,1/1.5),0,0);
    if(front!=null){const vmin=Math.min(...tiles.map(tl=>F*tl.vMean/tl.zMean)),fy=YTOP+vmin*front;sheets.visible=fy<YBOT;lg.clearRect(0,0,W,Math.max(0,fy));}else sheets.visible=true;
    lg.globalCompositeOperation='source-in';lg.drawImage(envF,0,0);lg.globalCompositeOperation='source-over';
    g.drawImage(lay,0,0);
  }
  // cloud-base fall streaks (M4/M5): soft fibres hanging under dense columns, deck-lit, length from the rate
  function colBases(){                                                   // per-column lowest deck row (px), refreshed every 2 s
    const cc=document.querySelector('.wfx .cloudcanvas');if(!cc)return null;
    if(colBases.at&&performance.now()-colBases.at<2000&&colBases.v)return colBases.v;
    try{const w=cc.width,h=cc.height,d=cc.getContext('2d').getImageData(0,0,w,h).data,out=new Float32Array(w);
      for(let x=0;x<w;x++){let yb=-1;for(let y=0;y<h;y++)if(d[(y*w+x)*4+3]>60)yb=y;out[x]=yb<0?-1:yb/h*H;}colBases.v=out;}catch(e){colBases.v=null;}
    colBases.at=performance.now();return colBases.v;
  }
  // fall streaks under the deck: irregular, soft, deck-lit fibres hanging from each column's own base; their
  // strength is the edge-on rain path (P.fibrePathKm) through the local rate, length grows with the rate
  function baseFibres(I,Rg,fld,t){
    const cb=colBases();if(!cb||!I.col)return 0;const mx=Math.max(...I.col),len=clamp(Math.log10(1+Rg.R)/1.7)*P.fibre.lenGainPx+P.fibre.lenBasePx;let n=0;
    const g=softBegin();
    for(let k=0;k<P.fibre.count;k++){const x=h1(k,77)*W,ci=Math.min(cb.length-1,Math.floor(x/W*cb.length)),base=cb[ci];if(base<20)continue;
      const dn=I.col[Math.min(I.col.length-1,Math.floor(x/W*I.col.length))]/mx*(fld?clamp(fld.at(x)):1);if(dn<0.3)continue;
      const col=envAtPx(x,base-6).map(v=>Math.round(v*P.fibre.colour)),a=(1-Math.exp(-Rg.sigma*P.fibrePathKm))*dn*(0.6+0.4*h1(k,78));
      const L=len*(0.6+0.8*h1(k,79)),sway=(vn(t/7000+k*0.37,91)-0.5)*6,wid=P.fibre.widthPx[0]+(P.fibre.widthPx[1]-P.fibre.widthPx[0])*h1(k,80);
      const grd=g.createLinearGradient(0,base-4,0,base+L);grd.addColorStop(0,`rgba(${col},${a.toFixed(3)})`);grd.addColorStop(1,`rgba(${col},0)`);
      g.strokeStyle=grd;g.lineWidth=wid;g.beginPath();g.moveTo(x,base-4);g.quadraticCurveTo(x+sway*0.3,base+L*0.5,x+sway,base+L);g.stroke();n++;}
    softEnd();return n;
  }
  function sunDim(I,Rg,on){
    const els=document.querySelectorAll('.atmo .suncorner,.atmo .sunbody,.wfx .sunhaze');
    if(!on||!(Rg.sigma>0)||I.sunEl==null||I.sunEl<=0){els.forEach(e=>e.style.filter='');return 1;}
    const Tm=Math.exp(-Rg.sigma*Rg.Hm/1000/Math.sin(Math.max(3,I.sunEl)*DEG));els.forEach(e=>e.style.filter=`opacity(${Tm.toFixed(3)})`);return Tm;
  }
  // ---------- models ----------
  // Expiry policies (research only): 'immediate' = overlay drawing stops on the frame data-precip goes off;
  // 'complete' = no drop is emitted after that frame; drops already emitted finish their trajectories with the inputs
  // frozen at the last eligible frame (nothing renewed), via an emission front moving down at each layer's screen
  // speed; state-bearing overlay layers (veil, shafts, base fibres) follow the product and stop at once.
  // Category-only presentation (evidence-semantics prototype T-C): draws at P.minRateMmH when the product shows a
  // precipitation class with data-precip off (amount unavailable) - itself an unsupported rate, shown for judgement.
  let MODEL='off',FRAME='flat',POLICY='immediate',CATONLY=false,t0=0,exp=null,lastGood=null;
  let SHELL=null,LAYERS=null,COMP=false;
  const has=k=>!LAYERS||LAYERS.includes(k);
  const NEAR=()=>({z1:(SHELL||P.nearShell)[0],z2:(SHELL||P.nearShell)[1],Dc:P.nearDmin}),TAIL=()=>({z1:P.tailShell[0],z2:P.tailShell[1],Dc:P.tailDmin,cap:300});
  function frame(tAbs){
    const t=tAbs-t0;let In=readInputs(tAbs);g.clearRect(0,0,W,H);
    const rec={t,model:MODEL,frame:FRAME,policy:POLICY,T,G,shell:SHELL,layers:LAYERS,perm:In.perm,cam:CAM};
    const precipClass=/^(rain|drizzle|thunder)$/.test(In.fx);
    let front=null;
    if(MODEL!=='off'&&!In.perm){
      if(CATONLY&&precipClass&&In.mm==null){In=Object.assign({},In,{perm:true,R:P.minRateMmH});rec.categoryOnly=true;}
      else if(POLICY==='complete'&&lastGood){if(!exp)exp={t:tAbs};In=lastGood;front=(tAbs-exp.t)/1000;rec.sinceExpiryS=front;}
    } else if(In.perm){exp=null;lastGood=In;}
    if(MODEL==='off'||!In.perm||In.fx==='snow'){css.textContent=MODEL==='off'?'':'.wfx .drop{visibility:hidden!important}';sunDim(In,{},false);window.__PM_LAST=rec;return rec;}
    css.textContent='.wfx .drop{visibility:hidden!important}';
    const Rg=regime(In);updateEnv(tAbs,In);updateDrift(tAbs,In);
    rec.R=Rg.R;rec.sigma=Rg.sigma;rec.Hm=Rg.Hm;rec.dsd=Rg.fam.name;
    const wnd=windAt(In,t,1.5);rec.ur=wnd.ur;rec.uf=wnd.uf;rec.leanDeg2mm=Math.atan(wnd.ur/vT(2))/DEG;rec.cloudDriftPxS=drift.vx;
    const st=front===null;                                   // state-bearing layers only while authority holds
    const needF=MODEL==='M3'||MODEL==='M5';const fld=needF?field(In,Rg,t):null;
    const o=x=>Object.assign(x,{frame:FRAME,front});
    if(MODEL==='M1'){rec.near=streaks(In,Rg,t,o(NEAR()));}
    else if(MODEL==='M2'){if(st&&has('veil'))rec.veil=veilLayer(In,Rg,null,1);if(has('tex'))sheets(In,Rg,t,null,front);if(has('near'))rec.near=streaks(In,Rg,t,o(TAIL()));rec.sunT=sunDim(In,Rg,st&&has('veil'));}
    else if(MODEL==='M3'){if(st){rec.veil=veilLayer(In,Rg,fld,1);rec.shafts=shafts(In,Rg,fld,t);}rec.near=streaks(In,Rg,t,o(Object.assign(NEAR(),{fld})));}
    else if(MODEL==='M4'){if(st){rec.veil=veilLayer(In,Rg,null,1);rec.fibres=baseFibres(In,Rg,null,t);}rec.near=streaks(In,Rg,t,o(Object.assign(NEAR(),{frac:P.m4StreakFrac})));rec.sunT=sunDim(In,Rg,st);}
    else if(MODEL==='M5'){if(st){rec.veil=veilLayer(In,Rg,fld,1);rec.shafts=shafts(In,Rg,fld,t);rec.fibres=baseFibres(In,Rg,fld,t);}sheets(In,Rg,t,fld,front);
      rec.near=streaks(In,Rg,t,o(Object.assign(TAIL(),{fld})));rec.sunT=sunDim(In,Rg,st);}
    if(front!==null){rec.sheetsVisible=(MODEL==='M2'||MODEL==='M5')?!!sheets.visible:false;rec.completed=(!rec.near||rec.near.drawn===0)&&!rec.sheetsVisible;}
    window.__PM_LAST=rec;return rec;
  }
  let FC=0;const RING=[];
  const reduced=()=>matchMedia('(prefers-reduced-motion: reduce)').matches&&!c.classList.contains('motionfull');
  let frozenAt=null;
  function loop(){const now=performance.now();
    if(reduced()){if(frozenAt===null){frozenAt=now;frame(now);} }   // reduced motion: one frozen frame, alpha-bounded
    else{frozenAt=null;const r=frame(now);FC++;RING.push({fc:FC,pt:now,perm:r.perm,drawn:r.near?r.near.drawn:null,exp:r.sinceExpiryS??null,sheets:r.sheetsVisible??null,done:r.completed??null,precip:c.dataset.precip});if(RING.length>2000)RING.shift();}
    requestAnimationFrame(loop);}
  // maximum post-expiry visibility per layer (s): band height / slowest screen speed of that layer
  function completionBound(){const In=lastGood||readInputs(performance.now());if(!In)return null;const Rg=regime(In),band=YBOT-YTOP,out={};
    out.near=band/(F*vT(P.nearDmin)/P.nearShell[1]);out.tail=band/(F*vT(P.tailDmin)/P.tailShell[1]);
    buildTiles(In,Rg);out.sheets=tiles?Math.max(...tiles.map(tl=>band/(F*tl.vMean/tl.zMean))):null;return out;}
  window.__PM={set(model,frm,opts){MODEL=model;SHELL=(opts&&opts.shell)||null;COMP=!!(opts&&opts.shell);LAYERS=(opts&&opts.layers)||null;T=(opts&&opts.T)||P.T;G=(opts&&opts.G)||P.G;tileKey='';FRAME=frm||'flat';POLICY=(opts&&opts.policy)||'immediate';CATONLY=!!(opts&&opts.categoryOnly);exp=null;t0=performance.now();tileKey='';envAt=-1e9;lastIn=-1e9;frozenAt=null;
      document.querySelectorAll('.atmo .suncorner,.atmo .sunbody,.wfx .sunhaze').forEach(e=>e.style.filter='');g.clearRect(0,0,W,H);},
    frame,completionBound,params:P,cam:CAM,get fc(){return FC;},ring:RING,cost(n){const a=performance.now();for(let i=0;i<n;i++)frame(a+i*16.7);return (performance.now()-a)/n;},
    get last(){return window.__PM_LAST;}};
  requestAnimationFrame(loop);
})();
