/** Native-only geometry cache precision. All physical/reference evaluators remain
 * continuous. This never changes the native UTC, prayer clock or sky age fence.
 * |delta f| <= quantum/4 implies <=.0416 device pixels at D416. This geometric
 * bound is not a bound on every terrain/photometric sample's temporal error. */
const PHASE_QUANTUM=.0004;
function canonicalFraction(f){
 if(typeof f!=='number'||!Number.isFinite(f)||f<0||f>1)throw new RangeError('native phase');
 if(f===0||f===1)return f;
 const a=Math.acos(2*f-1),q=Math.max(0,Math.min(Math.PI,Math.round(a/PHASE_QUANTUM)*PHASE_QUANTUM));
 return (1+Math.cos(q))/2;
}

