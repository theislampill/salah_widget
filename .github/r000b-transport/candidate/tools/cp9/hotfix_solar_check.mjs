// H8 independent low-order geometry check. NOAA fractional-year equations,
// https://gml.noaa.gov/grad/solcalc/solareqns.PDF, geometric solar centre only.
// No refraction/90.833-degree sunrise adjustment; not a precision ephemeris.
import fs from 'node:fs';
import {physicalSkyState} from '../../real-sky/core/src/sky-state.mjs';
import {projectPerspective} from '../../real-sky/core/src/projection.mjs';
const D=Math.PI/180,clamp=x=>Math.max(-1,Math.min(1,x));
function noaa(ms,lat,lon){
 const date=new Date(ms),year=date.getUTCFullYear(),start=Date.UTC(year,0,1),doy=Math.floor((ms-start)/86400000)+1,h=date.getUTCHours()+date.getUTCMinutes()/60+date.getUTCSeconds()/3600;
 const days=(Date.UTC(year+1,0,1)-start)/86400000,g=2*Math.PI/days*(doy-1+(h-12)/24);
 const eq=229.18*(.000075+.001868*Math.cos(g)-.032077*Math.sin(g)-.014615*Math.cos(2*g)-.040849*Math.sin(2*g));
 const dec=.006918-.399912*Math.cos(g)+.070257*Math.sin(g)-.006758*Math.cos(2*g)+.000907*Math.sin(2*g)-.002697*Math.cos(3*g)+.00148*Math.sin(3*g),ha=(h*60+eq+4*lon)/4*D-Math.PI,p=lat*D;
 // ENU form avoids the azimuth singularity at zenith and 0/360 discontinuity.
 return [-Math.cos(dec)*Math.sin(ha),Math.cos(p)*Math.sin(dec)-Math.sin(p)*Math.cos(dec)*Math.cos(ha),Math.sin(p)*Math.sin(dec)+Math.cos(p)*Math.cos(dec)*Math.cos(ha)];
}
const enu=s=>[Math.cos(s.altDeg*D)*Math.sin(s.azDeg*D),Math.cos(s.altDeg*D)*Math.cos(s.azDeg*D),Math.sin(s.altDeg*D)];
const angle=(a,b)=>Math.acos(clamp(a.reduce((s,v,i)=>s+v*b[i],0)))/D;
const sites=[['Central Florida fixture',28.5383,-81.3792],['Sydney fixture',-33.8688,151.2093],['Equator fixture',0,0],['Arctic fixture',78.2232,15.6469],['Antarctic fixture',-78.2232,15.6469]];
const cases=[];let failed=false;
for(const [label,lat,lon] of sites)for(const date of ['2026-03-20','2026-06-21','2026-09-23','2026-12-21']){
 let previous=null,maxReference=0,maxTenMinuteDirection=0,minAlt=90,maxAlt=-90,crossings=0,wasUp=null,finite=true;
 for(let minute=0;minute<=1440;minute+=10){
  const ms=Date.parse(date+'T00:00:00Z')+minute*60000,s=physicalSkyState({utcMs:ms,latDeg:lat,lonDeg:lon,heightM:0}).sun,v=enu(s),p=projectPerspective(s,{width:325,height:530,azDeg:180,altDeg:45,fovYDeg:90});
  maxReference=Math.max(maxReference,angle(v,noaa(ms,lat,lon)));if(previous)maxTenMinuteDirection=Math.max(maxTenMinuteDirection,angle(previous,v));previous=v;
  minAlt=Math.min(minAlt,s.altDeg);maxAlt=Math.max(maxAlt,s.altDeg);finite&&=[s.altDeg,s.azDeg,...v,...(p?[p.x,p.y]:[])].every(Number.isFinite);
  const up=s.altDeg>=0;if(wasUp!==null&&wasUp!==up)crossings++;wasUp=up;
 }
 // NOAA approximation bound declared 0.6 degrees. Earth's rotation plus solar
 // orbital motion is <2.6 degrees in ten minutes, independent of angle wrap.
 const pass=finite&&maxReference<.6&&maxTenMinuteDirection<2.6&&(minAlt>0||maxAlt<0?crossings===0:true);
 cases.push({label,lat,lon,date,maxReferenceDeg:maxReference,maxTenMinuteDirectionDeg:maxTenMinuteDirection,minAltitudeDeg:minAlt,maxAltitudeDeg:maxAlt,geometricHorizonCrossings:crossings,regime:minAlt>0?'polar-day':maxAlt<0?'polar-night':'rises-and-sets',pass});failed||=!pass;
}
const report={status:failed?'FAIL':'PASS_SCOPED',scope:'Independent NOAA approximation versus CP9 solar direction; geometric no-refraction centre; finite perspective projection, direction continuity, polar horizons. Does not validate prayer calendars or claim a sunrise where none occurs.',reference:'https://gml.noaa.gov/grad/solcalc/solareqns.PDF',samples:20*145,cases};
if(process.argv[2])fs.writeFileSync(process.argv[2],JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({status:report.status,samples:report.samples,maxError:Math.max(...cases.map(x=>x.maxReferenceDeg)),failed:cases.filter(x=>!x.pass)},null,2));process.exitCode=failed?1:0;
