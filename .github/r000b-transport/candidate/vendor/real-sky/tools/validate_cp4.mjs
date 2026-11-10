/** Independent, matched-time vacuum residuals. Executes real runtime astronomy, not a duplicate. */
import fs from 'node:fs';import {createHash} from 'node:crypto';import {fileURLToPath} from 'node:url';
import * as A from '../src/astronomy.mjs';
export function validateCP4(){
 const input=fs.readFileSync(new URL('../tests/fixtures/cp4-astrometry.json',import.meta.url)),f=JSON.parse(input),data=JSON.parse(fs.readFileSync(new URL('../data/catalogue-v6_5.json',import.meta.url))),byId=new Map(data.stars.map(s=>[s.id,s]));
 const horizon=[],eqs=[],moves=[],whole=[],earthPosition=[],earthVelocity=[];let worst=null;
 const residual=(ra,dec,a,b)=>A.angularSeparation(A.radecVector(ra,dec),A.radecVector(a,b))*3600;
 const frames=f.epochs.map(e=>f.locations.map(l=>A.observationFrame({...e,...l})));
 for(const [di,li,si,ra,dec,az,alt] of f.rows){const s=f.stars[si],h=A.observeStar(s,frames[di][li]),e=residual(h.raOfDateDeg,h.decOfDateDeg,ra,dec),ah=A.angularSeparation(h.enu,[Math.cos(alt*A.DEG)*Math.sin(az*A.DEG),Math.cos(alt*A.DEG)*Math.cos(az*A.DEG),Math.sin(alt*A.DEG)])*3600;eqs.push(e);horizon.push(ah);if(!worst||ah>worst.arcsec)worst={arcsec:ah,starId:s.id,hip:s.hip,epoch:f.epochs[di],location:f.locations[li],runtime:{alt:h.altDeg,az:h.azDeg,ra:h.raOfDateDeg,dec:h.decOfDateDeg},oracle:{alt,az,ra,dec}};}
 for(const [di,si,ra,dec] of f.motionRows){const v=A.propagateJ2000(f.stars[si],A.julianYear(f.epochs[di].jdTt));moves.push(A.angularSeparation(v,A.radecVector(ra,dec))*3600);}
 for(const epoch of f.census){const frame=A.observationFrame(epoch.observer);for(const [id,ra,dec] of epoch.rows){const h=A.observeStar(byId.get(id),frame);whole.push(residual(h.raOfDateDeg,h.decOfDateDeg,ra,dec));}}
 for(const e of f.earth){const r=A.earthState(e.jdTt);earthPosition.push(Math.hypot(...r.positionAu.map((v,i)=>v-e.positionAu[i])));earthVelocity.push(Math.hypot(...r.velocityAuDay.map((v,i)=>v-e.velocityAuDay[i])));}
 const stats=a=>{a.sort((x,y)=>x-y);return {count:a.length,max:a.at(-1),p95:a[Math.floor((a.length-1)*.95)],median:a[Math.floor((a.length-1)*.5)]};};
 const report={status:'PASS',oracle:f.oracle,fixtureSha256:createHash('sha256').update(input).digest('hex'),scope:'Matched suppliedUT1/TT; vacuum; NOGDEFL; all current catalogue records plus multi-location selected-source matrix. NOT independently measured catalogue accuracy or actual-weather visibility.',horizontalArcsec:stats(horizon),equatorialArcsec:stats(eqs),motionOnlyArcsec:stats(moves),wholeCatalogueEquatorialArcsec:stats(whole),earthPositionAu:stats(earthPosition),earthVelocityAuDay:stats(earthVelocity),worstHorizontal:worst,limits:{horizontalArcsec:5,equatorialArcsec:5,motionOnlyArcsec:.1,wholeCatalogueEquatorialArcsec:5,earthPositionAu:.003,earthVelocityAuDay:.00005}};
 for(const [k,limit] of Object.entries(report.limits))if(report[k].max>limit)report.status='FAIL';return report;
}
if(process.argv[1]===fileURLToPath(import.meta.url)){const r=validateCP4();const text=JSON.stringify(r,null,2)+'\n';if(process.argv[2])fs.writeFileSync(process.argv[2],text);console.log(text);process.exitCode=r.status==='PASS'?0:1;}
