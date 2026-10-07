/** Measured angular refinement, not an all-error mathematical certificate.
 * Uses receiver display differences without unstable near-zero ratios. A true
 * terrain/finite-light solution is evaluated at every admitted receiver; this
 * selects angular quadrature effort, not geography, material or source energy.
 */
function sourceRule(n){const pairs={64:[4,16],256:[8,32],1024:[16,64],4096:[32,128],8192:[64,128]};if(!pairs[n])throw new RangeError('source rule');return pairs[n];}
function qualityMask(before,after,{first=false,threshold=.125}={}){
 const a=before.receiverCodes,b=after.receiverCodes,m=after.ambiguous;
 if(!Number.isFinite(threshold)||threshold<=0||!a||!b||a.length!==b.length||b.length%3||m?.length!==b.length/3)throw new RangeError('quality input');
 const mask=new Uint8Array(m.length);let count=0,maxCode=0;
 for(let i=0;i<m.length;i++){
  let d=0;for(let k=0;k<3;k++){const x=a[3*i+k],y=b[3*i+k];if(!Number.isFinite(x)||!Number.isFinite(y))throw new RangeError('quality signal');d=Math.max(d,Math.abs(x-y));}
  maxCode=Math.max(d,maxCode);
  if(d>threshold||(first&&m[i]!==0)){mask[i]=3;count++;}
 }return {mask,count,maxCode,threshold};
}
function projectedDifference(a,b){
 if(!a.qualityImages||!b.qualityImages)return null;
 let result=0;for(let j=0;j<a.qualityImages.length;j++){
  const x=a.qualityImages[j],y=b.qualityImages[j];if(!x||x.length!==y.length)throw new Error('quality projection identity');
  for(let i=0;i<x.length;i++)result=Math.max(result,Math.abs(x[i]-y[i]));
 }return result;
}
async function adaptiveRender(engine,scene,{cancelled=()=>false,onProgress=()=>{},onPreview=()=>{},diagnostic=false,threshold=.125}={}){
 const begin=performance.now(),rules=[64,256,1024,4096,8192],history=[];let last=null,selection=null,result=null,comparison=null,projected=null,projectedStable=false;
 for(let step=0;step<rules.length;step++){
  const n=rules[step],[radial,azimuth]=sourceRule(n);
  result=await engine.render(scene,{radial,azimuth,cancelled,onProgress:p=>onProgress({...p,sourceSamples:n}),qualityFields:true,lightingMask:selection,diagnostic});
  history.push({samples:n,receivers:selection?selection.reduce((a,x)=>a+(x!==0),0):result.ambiguous.length,milliseconds:result.diagnostics.totalMs});
  if(step===0)await onPreview({...result,receiverCodes:undefined,ambiguous:undefined,solar:undefined,earth:undefined,coverage:undefined,pixels:undefined,displayLinear:undefined,diagnostics:{...result.diagnostics,quality:{status:'preview',samples:n}}});
  if(last){
   comparison=qualityMask(last,result,{first:step===1,threshold});projected=projectedDifference(last,result);
   projectedStable=step>=3&&projected!==null&&projected<=.5;
   if(comparison.count===0||projectedStable)break;
   selection=comparison.mask;onProgress({stage:'refinement',sourceSamples:n,selected:comparison.count,maxCode:comparison.maxCode});
  }
  last=result;
 }
 result.diagnostics.quality={status:comparison?.count===0||projectedStable?'empirical-adaptive':'limit-reached',method:'64/256 full + ambiguous-source minimum1024 + selected4096/8192; local display-change criterion',thresholdCode:threshold,unsettled:projectedStable?0:(comparison?.count??0),receiverHeuristicRemaining:comparison?.count??0,projectedMaximumCode:projected,projectedGate:.5,lastMaximumCode:comparison?.maxCode??null,history,totalMs:performance.now()-begin,scope:'angular-rule discriminator; independent dense-reference, spatial, terrain and photometry errors are separate'};
 if(!diagnostic){delete result.receiverCodes;delete result.ambiguous;delete result.qualityImages;}
 return result;
}

