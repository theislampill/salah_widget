import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {nativeJob} from '../../real-sky/native-contract.mjs';
import {NativeSkyEngine} from '../../real-sky/native-engine.mjs';
import {angularSeparation} from '../../real-sky/core/src/astronomy.mjs';
import {horizontalVector} from '../../real-sky/core/src/scene.mjs';
import {prepareStars} from './stellar_replay.mjs';
import {replayObserver} from './qualification_scene.mjs';
const read=n=>readFileSync(new URL('../../vendor/real-sky/data/'+n,import.meta.url),'utf8');
const engine=new NativeSkyEngine({catalogueText:read('bright-stars.json'),manifestText:read('registered-starlight/runtime-manifest.json'),
  assetTexts:{128:read('registered-starlight/V-nside128.json')}});
const catalogue=new Map(engine.store.catalogue.stars.map(s=>[s.id,s]));
const centered='2026-12-23T20:00:00Z',id='hyg:27761';
const cam={...replayObserver.camera,azDeg:74.72172746240722,altDeg:74.54675001359269};
const results={scope:'actual physical topocentric Moon, fixed camera, one projected real source before/during/after; no calendar geometry',id,camera:cam,cells:[]};
try {
  for(const offsetMinutes of [-90,0,90,7*1436]){
    const utcMs=Date.parse(centered)+offsetMinutes*60000,job=nativeJob({...replayObserver,camera:cam,utcMs},true);
    const frame=await engine.render(job);assert.equal(frame.status,'ready');
    const star=frame.sources.find(s=>s.id===id);assert.ok(star);
    const d=frame.raster.sourceDiagnostics.find(s=>s.id===id),moon=frame.raster.physicalState.moon;
    const separation=angularSeparation(horizontalVector(star),horizontalVector(moon));
    const eligible=prepareStars(frame,catalogue).some(s=>s.id===id);
    const occulted=separation<=moon.angularRadiusDeg;
    assert.equal(occulted,offsetMinutes===0);assert.equal(!!d,!occulted);
    assert.equal(eligible,!!d?.detectable);
    results.cells.push({utc:new Date(utcMs).toISOString(),vmag:star.vmag,x:star.x,y:star.y,altDeg:star.altDeg,
      moonRadiusDeg:moon.angularRadiusDeg,separationDeg:separation,physicalOccultation:occulted,
      projected:true,transportDiagnostic:!!d,detectable:d?.detectable??null,replayEligible:eligible});
  }
  assert.equal(results.cells.at(-1).replayEligible,true);
  console.log(JSON.stringify(results,null,2));
} finally {engine.dispose();}
