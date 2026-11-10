"use strict";
const assert=require("node:assert/strict");
const {fixture,copy}=require("/workspace/scratch/15b8fb6ac4c2/r000b-work/tests/weather-no-timetable-fixture.cjs");
function admitPresent(h,{leaseMs=1000,state="wet",type="rain"}={}){
 const target=copy(h.run("currentWeatherTarget()")),now=h.clock.wall;
 h.ctx.__probeInput={scope:"simulation-fixture",provider:"Synthetic QA",product:"present/nearby contract",policy:"synthetic-present-v1",
 target:{generation:target.generation,lat:target.lat,lon:target.lon},measurementAt:now,validFrom:now,validUntil:now+leaseMs,retrievedAt:now,frameAt:now,issuedAt:now,units:"categorical",
 footprint:{kind:"point",lat:target.lat,lon:target.lon,coverage:"target"},quality:{status:"qualified",sampling:"direct",localObservationAt:now,operationalHealth:"operational"},
 present:{state,type,lightning:"unavailable",quantity:null}};
 assert(h.run("(weatherSynthetic=admitWeatherFixture(__probeInput,currentWeatherTarget(),Date.now())).ok"));
}
function state(h){return copy(h.run(`({
 model:!!model(),selected:!!selectedWeather(),sameRecord:weather===__probeRecord,code:weatherDecision().renderCode,
 present:weatherDecision().present.available,consumedPresent:_cloudPublication.decision?.present.available,
 consumedCode:_cloudPublication.decision?.renderCode,receipt:cloudPublicationReceipt(),oldReceiptCurrent:cloudPublicationCurrent(__probeReceipt),
 cov:[cloudState.covLow,cloudState.covMid,cloudState.covHigh],targets:[cloudState.tgtLow,cloudState.tgtMid,cloudState.tgtHigh],ready:_cloudReady,
 density:Math.max(..._colDens),fx:document.querySelector('.c').dataset.fx,header:_lastWeatherHeader?.code,
 candidateLayers:model()?(()=>{const a=atmosphere(model());return [a.cloudLayerLow,a.cloudLayerMid,a.cloudLayerHigh]})():null
 })`));}
(async()=>{
 const h=await fixture({hash:"&simWx=0&simCloud=0"});
 h.ctx.__probeRecord=h.run("weather");
 admitPresent(h);h.run("render();paintClouds(simNow()/1000)");h.ctx.__probeReceipt=h.run("cloudPublicationReceipt()");
 const admitted=state(h);assert(admitted.present&&admitted.ready);assert.deepEqual(admitted.cov,[.9,.85,.3]);
 h.at(891000);const expiredBefore=state(h);assert.equal(expiredBefore.present,false);assert.equal(expiredBefore.sameRecord,true);assert.equal(expiredBefore.code,0);assert.deepEqual(expiredBefore.candidateLayers,[0,0,0]);
 h.run("today=null;render();paintClouds(simNow()/1000)");
 const expiredNoModel=state(h);expiredNoModel.retainedRasterFills=h.raster.currentFills;
 assert.equal(expiredNoModel.model,false);assert.equal(expiredNoModel.present,false);assert.equal(expiredNoModel.oldReceiptCurrent,true);
 assert.deepEqual(expiredNoModel.cov,[.9,.85,.3]);assert(expiredNoModel.retainedRasterFills>0);
 const j=await fixture({hash:"&simWx=0&simCloud=0"});j.ctx.__probeRecord=j.run("weather");admitPresent(j);
 j.run("render();paintClouds(simNow()/1000)");j.ctx.__probeReceipt=j.run("cloudPublicationReceipt()");
 j.ctx.__probeEvidence=j.run("weatherDecision().present.evidence");
 admitPresent(j,{leaseMs:60000,state:"dry",type:null});j.run("render();paintClouds(simNow()/1000)");
 const replacedSameRecord=state(j);replacedSameRecord.receiptSame=j.run("cloudPublicationReceipt()===__probeReceipt");replacedSameRecord.consumedEvidenceIsOld=j.run("_cloudPublication.decision.present.evidence===__probeEvidence");
 assert.equal(replacedSameRecord.code,0);assert.equal(replacedSameRecord.consumedCode,63);assert.equal(replacedSameRecord.receiptSame,true);
 console.log(JSON.stringify({sourceSha256:h.sourceSha256,admitted,expiredBefore,expiredNoModel,replacedSameRecord},null,2));
})().catch(e=>{console.error(e);process.exitCode=1;});
