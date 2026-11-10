import fs from 'node:fs';
import {createHash} from 'node:crypto';
import {observationFrame,radecVector,angularSeparation,DEG} from '../src/astronomy.mjs';
import {observeDiffuseDirection,horizontalToDiffuseJ2000} from '../src/diffuse-map.mjs';
const raw=fs.readFileSync(new URL('../tests/fixtures/cp7-directions.json',import.meta.url)),fixture=JSON.parse(raw);
const frames=fixture.epochs.map(e=>fixture.locations.map(l=>observationFrame({...e,...l,pressureHpa:0})));
const forward=[],inverse=[],closure=[];let worst=null;
for(const [di,li,si,az,alt] of fixture.rows){
 const f=frames[di][li],s=fixture.directions[si],v=radecVector(s.raDeg,s.decDeg),actual=observeDiffuseDirection(v,f);
 const expected=[Math.cos(alt*DEG)*Math.sin(az*DEG),Math.cos(alt*DEG)*Math.cos(az*DEG),Math.sin(alt*DEG)];
 const e=angularSeparation(actual.enu,expected)*3600,i=angularSeparation(horizontalToDiffuseJ2000({altDeg:alt,azDeg:az},f),v)*3600,c=angularSeparation(horizontalToDiffuseJ2000(actual,f),v)*3600;
 forward.push(e);inverse.push(i);closure.push(c);if(!worst||Math.max(e,i)>worst.maxArcsec)worst={maxArcsec:Math.max(e,i),forwardArcsec:e,inverseArcsec:i,direction:s,epoch:fixture.epochs[di],location:fixture.locations[li]};
}
const stats=a=>{a.sort((x,y)=>x-y);return {cases:a.length,max:a.at(-1),p95:a[Math.floor(.95*(a.length-1))],median:a[Math.floor(.5*(a.length-1))]};};
const report={status:'PASS',scope:fixture.scope,sourceGate:'BLOCKED',productionDiffuseSurvey:false,oracle:fixture.oracle,fixtureSha256:createHash('sha256').update(raw).digest('hex'),directions:fixture.directions.length,epochs:fixture.epochs.length,locations:fixture.locations.length,forwardHorizontalArcsec:stats(forward),inverseJ2000Arcsec:stats(inverse),ownRoundTripArcsec:stats(closure),limits:fixture.limitsDeclaredBeforeEvaluation,worst};
for(const [k,limit] of Object.entries(report.limits))if(report[k].max>limit)report.status='FAIL';
fs.writeFileSync(new URL('../checkpoints/cp7_3/registration-validation.json',import.meta.url),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report,null,2));process.exitCode=report.status==='PASS'?0:1;
