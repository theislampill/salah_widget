// Source-only diagnostic for the exact disposable R0035 reconstruction. This
// module reads no files, installs no route and performs no native observation.
import {createHash} from 'node:crypto';

const referenceSha256='11717de894a630f99b5d661ff35c4200b355f4486c533e0e31dbc39e67a6a02a';
const prefix='// R0035 publish-decision observation derivative; original scientific gates unchanged.\n';
const condition=`      if(source?.raster===r&&source.canvas===canvas&&source.discKey===discKey&&source.boxes===JSON.stringify(glass)
          &&same(source.cloud,capture.cloudRGBA)&&same(source.moon,capture.moonRGBA)&&same(source.mask,mask)){`;
const observedCondition=`      let publishEvaluated=0,publishEqual=0;
      const publishCheck=(bit,value)=>{publishEvaluated|=bit;if(value)publishEqual|=bit;return value;};
      if(publishCheck(1,source?.raster===r)&&publishCheck(2,source.canvas===canvas)&&publishCheck(4,source.discKey===discKey)&&publishCheck(8,source.boxes===JSON.stringify(glass))
          &&publishCheck(16,same(source.cloud,capture.cloudRGBA))&&publishCheck(32,same(source.moon,capture.moonRGBA))&&publishCheck(64,same(source.mask,mask))){`;
const replacement="      epoch++;pending=false;prepared=false;inactive('preparing accepted frame');writer.invalidate();";
// Only primitive local state is retained. No source/canvas/buffer reference,
// repeated equality scan, timestamp, request, callback or extra event is added.
const observedReplacement=`      const publishDecision=trial?{protocol:'r0035-publish-decision/1',previousEpoch:epoch,hadSource:!!source,
        evaluatedMask:publishEvaluated,equalMask:publishEqual,wasPrepared:prepared,samplePending:pending,
        preparingEpoch:preparing,latestQueued:!!latest}:null;
${replacement}`;
const owner="      event('owner');latest=()=>{";
const observedOwner="      event('owner',publishDecision?{r0035Publish:publishDecision}:{});latest=()=>{";
const seams=Object.freeze([[condition,observedCondition],[replacement,observedReplacement],[owner,observedOwner]]);
const terms=Object.freeze(['rasterReference','canvasReference','discKey','glassBounds','cloudPixels','moonPixels','maskPixels']);

function bytes(value){if(!Buffer.isBuffer(value))throw new TypeError('Actual source Buffer bytes required');return value;}
function sha(value){return createHash('sha256').update(bytes(value)).digest('hex');}
function pinned(value){if(sha(value)!==referenceSha256)throw new Error('Original publish source identity mismatch');return value.toString('utf8');}
function once(source,before,after){
  const index=source.indexOf(before);
  if(index<0||source.indexOf(before,index+before.length)>=0)throw new Error('Missing or ambiguous publish observation seam');
  return source.slice(0,index)+after+source.slice(index+before.length);
}

export function derivePublishDiagnostic(reference){
  let source=pinned(reference);
  for(const [before,after] of seams)source=once(source,before,after);
  return Buffer.from(prefix+source);
}
export function restorePublishDiagnostic(derived){
  let source=bytes(derived).toString('utf8');
  if(!source.startsWith(prefix))throw new Error('Publish observation derivative identity missing');
  source=source.slice(prefix.length);
  for(const [before,after] of [...seams].reverse())source=once(source,after,before);
  const restored=Buffer.from(source);pinned(restored);return restored;
}
export function publishDiagnosticIdentity(reference,derived){
  if(!derivePublishDiagnostic(reference).equals(bytes(derived))||!restorePublishDiagnostic(derived).equals(reference))
    throw new Error('Publish observation is not the exact admitted transformation');
  const identity=value=>({bytes:value.length,sha256:sha(value)});
  return {protocol:'r0035-publish-diagnostic-source/1',scope:'original-short-circuit-and-pre-replacement-local-state',
    reference:identity(reference),derived:identity(derived),nativeObservation:'NOT_RUN',
    speed:'NOT_ESTABLISHED',humanAcceptance:'OUTSTANDING'};
}

// A pure decoder of one supplemental record, not a provenance/intake or trial
// admission function. It cannot make an original FAIL into a qualified result.
export function decodePublishDecision(record,ownerEpoch){
  const keys=['protocol','previousEpoch','hadSource','evaluatedMask','equalMask','wasPrepared','samplePending','preparingEpoch','latestQueued'];
  const need=(condition,message)=>{if(!condition)throw new TypeError(message);};
  need(record!==null&&typeof record==='object'&&!Array.isArray(record),'Publish decision record required');
  need(Object.keys(record).length===keys.length&&keys.every(key=>Object.hasOwn(record,key)),
    'Exact publish decision schema required');
  need(record.protocol==='r0035-publish-decision/1','Publish decision protocol mismatch');
  need(Number.isSafeInteger(record.previousEpoch)&&record.previousEpoch>=0&&Number.isSafeInteger(ownerEpoch)
    &&ownerEpoch>0&&ownerEpoch===record.previousEpoch+1,'Publish decision owner epoch mismatch');
  for(const key of ['hadSource','wasPrepared','samplePending','latestQueued'])
    need(typeof record[key]==='boolean','Boolean publish activity required');
  need(record.preparingEpoch===null||(Number.isSafeInteger(record.preparingEpoch)&&record.preparingEpoch>=0
    &&record.preparingEpoch<=record.previousEpoch),'Invalid original preparation epoch');
  need([1,3,7,15,31,63,127].includes(record.evaluatedMask)&&record.equalMask===(record.evaluatedMask>>1),
    'Executed first-false comparison prefix required');
  // hadSource is sampled after the condition. A getter can revoke or replace
  // the owner during evaluation; that later snapshot cannot constrain its prefix.
  const comparisons=terms.map((term,index)=>({term,outcome:!(record.evaluatedMask&(1<<index))?'NOT_EVALUATED'
    :(record.equalMask&(1<<index))?'EQUAL':'DIFFERENT'}));
  return {scope:'SUPPLEMENTAL_IDENTITY_OBSERVATION',
    kind:record.hadSource?'SOURCE_PRESENT_AT_REPLACEMENT':'SOURCE_ABSENT_AT_REPLACEMENT',
    decisiveTerm:comparisons.find(row=>row.outcome==='DIFFERENT').term,terms:comparisons,
    allTermsEvaluated:record.evaluatedMask===127,originalConditionResult:false,
    activity:{wasPrepared:record.wasPrepared,samplePending:record.samplePending,
      preparingEpoch:record.preparingEpoch,latestQueued:record.latestQueued},cpuTiming:'NOT_MEASURED'};
}
