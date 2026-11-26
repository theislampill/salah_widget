// Diagnostic-only worker aggregates. No retained source, image, cache or I/O.
export const COST_BUCKETS=Object.freeze(['spectralFlux','psfRaster','calendarTransfer','nominalCompose','envelopeBounds',
  'lowerBoundCompose','upperBoundCompose','variableSelection','patchWeights','inputGathers',
  'centerWithdrawal','withdrawalCompose','centerRanking']);
export const COST_COUNTS=Object.freeze(['fullInputSources','previewInputSources','spectralSources','transportSamples',
  'patchCalls','drawnPatches','referencePsfChannels','referenceGaussianCalls','patchPixelsRequested',
  'replayInputSources','replaySelectedSources','envelopePatchPixelsScheduled','variablePixels','variablePatchOffsets',
  'inputGatherValues','withdrawalCenters','fullComposeCalls','centerComposeCalls']);
const own=(object,key)=>Object.prototype.hasOwnProperty.call(object,key);
function clock(cost){
  let value;
  try{value=performance.now();}catch{cost.faults.clock=true;return cost.lastAt;}
  if(!Number.isFinite(value)||value<cost.lastAt){cost.faults.clock=true;return cost.lastAt;}
  cost.lastAt=value;return value;
}
function collecting(cost){
  if(!cost)return false;
  if(cost.status!=='COLLECTING'){cost.faults.lifecycle=true;return false;}
  return true;
}
export function createCosts(epoch){
  const cost={protocol:'r0035-worker-costs/1',clockDomain:'worker-performance-now-ms',epoch,status:'COLLECTING',
    startedAt:null,lastAt:0,endedAt:null,active:null,
    faults:{clock:false,overlap:false,name:false,count:false,lifecycle:false},
    buckets:Object.fromEntries(COST_BUCKETS.map(key=>[key,{calls:0,completed:0,failed:0,ms:0}])),
    counts:Object.fromEntries(COST_COUNTS.map(key=>[key,0]))};
  if(!Number.isSafeInteger(epoch)||epoch<0)cost.faults.lifecycle=true;
  cost.startedAt=clock(cost);return cost;
}
export function costStart(cost,key){
  if(!collecting(cost))return;
  if(!own(cost.buckets,key)){cost.faults.name=true;return;}
  if(cost.active){cost.faults.overlap=true;return;}
  const row=cost.buckets[key];
  if(!Number.isSafeInteger(row.calls+1)){cost.faults.count=true;return;}
  row.calls++;cost.active={bucket:key,at:clock(cost)};
}
function closeActive(cost,failed){
  const active=cost.active,at=clock(cost),row=cost.buckets[active.bucket];
  row.ms+=at-active.at;row[failed?'failed':'completed']++;cost.active=null;
  if(!Number.isFinite(row.ms)||row.ms<0)cost.faults.clock=true;
}
export function costEnd(cost,key){
  if(!collecting(cost))return;
  if(!own(cost.buckets,key)){cost.faults.name=true;return;}
  if(cost.active?.bucket!==key){cost.faults.lifecycle=true;return;}
  closeActive(cost,false);
}
export function countCost(cost,key,amount=1){
  if(!collecting(cost))return;
  if(!own(cost.counts,key)){cost.faults.name=true;return;}
  const value=cost.counts[key]+amount;
  if(!Number.isSafeInteger(amount)||amount<0||!Number.isSafeInteger(value)){cost.faults.count=true;return;}
  cost.counts[key]=value;
}
export function finishCosts(cost,status){
  if(!collecting(cost))return;
  if(!['COMPLETE','FAILED'].includes(status)){cost.faults.lifecycle=true;return;}
  if(cost.active){if(status==='COMPLETE')cost.faults.lifecycle=true;closeActive(cost,true);}
  cost.endedAt=clock(cost);cost.status=status;
}
