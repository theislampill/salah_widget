import fs from 'node:fs';
import {physicalSkyState} from '../src/sky-state.mjs';
import {radecVector,angularSeparation} from '../src/astronomy.mjs';
import {horizontalDirection} from '../src/atmosphere.mjs';
const root=new URL('../',import.meta.url),fixture=JSON.parse(fs.readFileSync(new URL('tests/fixtures/cp6-illumination.json',root))),max={sunDirectionDeg:0,moonDirectionDeg:0,lunarPhaseDeg:0,lunarDistanceKm:0},worst={},horizontal={sunDeg:0,moonDeg:0};
for(const r of fixture.rows){const p=physicalSkyState(r.observer);for(const b of ['sun','moon']){const err=angularSeparation(radecVector(p[b].raDeg,p[b].decDeg),radecVector(r[b].raDeg,r[b].decDeg)),key=b+'DirectionDeg';if(err>max[key]){max[key]=err;worst[key]={observer:r.observer,expected:r[b],got:p[b]};}horizontal[b+'Deg']=Math.max(horizontal[b+'Deg'],angularSeparation(horizontalDirection(p[b]),horizontalDirection(r[b])));}
 const phase=Math.abs(p.moon.phaseAngleDeg-r.moonPhaseDeg),dist=Math.abs(p.moon.distanceKm-r.moon.distanceKm);max.lunarPhaseDeg=Math.max(max.lunarPhaseDeg,phase);max.lunarDistanceKm=Math.max(max.lunarDistanceKm,dist);
}
const pass=Object.entries(max).every(([k,v])=>v<=fixture.acceptanceSetBeforeComparison[k]);const result={status:pass?'PASS':'FAIL',observerCases:fixture.rows.length,bodyDirectionCases:fixture.rows.length*2,oracle:fixture.oracle,scope:fixture.scope,acceptance:fixture.acceptanceSetBeforeComparison,maximumErrors:max,horizontalMaximumErrors:horizontal,worst,limits:['Numerical ephemeris comparison, not measured atmospheric conditions','No claim of CP4 stellar angular precision for this separate low-order lunar model','Eclipse attenuation, actual terrain and horizon refraction not applied']};
fs.writeFileSync(new URL('checkpoints/cp6/illumination-validation.json',root),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify({...result,worst:undefined},null,2));if(!pass)process.exitCode=1;
