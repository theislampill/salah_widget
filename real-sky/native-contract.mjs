/** CP8 native boundary. All astronomical time comes from the accepted host snapshot. */
function nativeFinite(v,name,min=-Infinity,max=Infinity){if(typeof v!=='number'||!Number.isFinite(v)||v<min||v>max)throw new RangeError('Invalid native '+name);return v;}
export function nativeIdentity(s){
 if(!s||typeof s!=='object')throw new TypeError('Native snapshot required');
 nativeFinite(s.utcMs,'UTC',-8640000000000000,8640000000000000);nativeFinite(s.lat,'latitude',-90,90);nativeFinite(s.lon,'longitude',-180,180);nativeFinite(s.heightM,'height',-500,10000);
 if(typeof s.sceneIdentity!=='string'||!s.sceneIdentity||!Number.isSafeInteger(s.generation)||s.generation<0)throw new TypeError('Accepted native scene/generation required');
 const c=s.camera??{};nativeFinite(c.azDeg,'camera azimuth',-360,360);nativeFinite(c.altDeg,'camera altitude',-90,90);nativeFinite(c.fovYDeg,'camera field of view',10,150);nativeFinite(c.rollDeg,'camera roll',-180,180);
 return JSON.stringify([s.sceneIdentity,s.generation,s.lat,s.lon,s.heightM,s.camera,s.weather,s.lp,s.reducedMotion,s.allowEstimates!==false,s.units,s.tz??null,s.timeScale??1,s.elevationSource??null,s.elevationOwner??null]);
}
export function nativeJob(s,physical=false){
 const identity=nativeIdentity(s),w=s.weather;
 const visibility=typeof w?.vis==='number'&&Number.isFinite(w.vis)?Math.max(0,w.vis):20000;
 // Visibility is not an aerosol optical-depth measurement: this bounded mapping is an explicit scenario assumption.
 const aerosol=physical?.06+.3*Math.max(0,Math.min(1,1-visibility/20000)):.06;
 const temperature=typeof w?.temp==='number'&&Number.isFinite(w.temp)?(s.units==='f'?(w.temp-32)*5/9:w.temp):10;
 const lp=typeof s.lp==='number'&&Number.isFinite(s.lp)?Math.max(0,Math.min(1,s.lp)):0;
 return {observer:{utcMs:s.utcMs,latDeg:s.lat,lonDeg:s.lon,heightM:s.heightM,temperatureC:Math.max(-90,Math.min(70,temperature)),pressureHpa:0},
 native:{identity,generation:s.generation,sceneIdentity:s.sceneIdentity,weatherSource:w?.src??'unavailable',weatherAccepted:!!w,cloudOwner:physical?'native-linear-foreground':'native-interim-overlay',assumptions:{elevation:s.elevationSource??'explicit caller elevation; provenance not supplied',aerosol:'0.06 + 0.30*(1-visibility/20000), clamped; not measured AOD',pressure:'standard atmosphere from accepted elevation; astrometry remains geometric',localLight:'LPOLL × 0.003 cd/m² assumed non-stellar local light',cloud:'native painted total opacity, not measured optical depth'}},
 tier:128,
 options:{sceneIdentity:identity,view:{type:'camera',width:325,height:530,...s.camera},dpr:1,nominalExposure:24,autoExposure:true,backgroundStepCss:8,reducedMotion:!!s.reducedMotion,scintillation:{strength:0},
 atmosphere:{elevationM:s.heightM,aerosolTau550:aerosol,cloudTransmission:1,cloudGlowCdM2:0,lightPollutionCdM2:physical?lp*.003:0},
 diffuse:physical?{enabled:true,allowEstimates:s.allowEstimates!==false,samplesPerAxis:2,residualNight:{kind:'assumed-nonstellar-residual',zenithCdM2:.00014,source:'CP8 explicit non-stellar residual assumption; not measured airglow',includesRegisteredStarlight:false}}:{enabled:false}}};
}
// A numerical frame older than 30 accepted-UTC seconds is unavailable, not a current sky.
export function nativeResultCurrent(job,current){try{return job.native.identity===nativeIdentity(current)&&Number.isFinite(job.observer.utcMs)&&Math.abs(current.utcMs-job.observer.utcMs)<=30000;}catch{return false;}}
/** Native calendar mask removes only direct astronomical light, never atmospheric sky. */
export function nativeCalendarComposite(raster,mask=null){
 const out=new Float64Array(raster.linear.length),sky=raster.skyBackgroundLinear??raster.backgroundLinear,diffuse=raster.diffusePhysicalLinear;
 if(mask&&mask.length!==raster.width*raster.height)throw new RangeError('Calendar mask dimensions');
 for(let i=0;i<out.length;i++){const m=mask?mask[Math.floor(i/3)]:1;out[i]=sky[i]+(raster.stellarLinear[i]+(diffuse?.[i]??0))*m;}return out;
}

/** Map logical physics pixels through actual CSS bounds and the native SVG screen transform. */
export function nativeDiscMask(width,height,rect,m,radius){
 // DOMMatrix coefficients are native getters. Read each exactly once; all
 // arithmetic and the one-pixel antialias ramp are identical to the CP8.3 mask.
 const {a,b,c,d,e,f}=m,det=a*d-b*c;if(!Number.isFinite(det)||Math.abs(det)<1e-12)throw new RangeError('Singular native Moon transform');
 const mask=new Float64Array(width*height),sx=rect.width/width,sy=rect.height/height;
 const aa=Math.max(1e-9,.5*(Math.hypot(d*sx,b*sx)+Math.hypot(c*sy,a*sy))/Math.abs(det));
 for(let y=0;y<height;y++)for(let x=0;x<width;x++){
  const px=rect.left+(x+.5)*sx-e,py=rect.top+(y+.5)*sy-f;
  const xx=(d*px-c*py)/det,yy=(-b*px+a*py)/det;
  mask[y*width+x]=Math.max(0,Math.min(1,(Math.hypot(xx,yy)-radius)/aa+.5));
 }
 return mask;
}
