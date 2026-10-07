/** Native-only geometry cache precision. All physical/reference evaluators remain
 * continuous. This never changes the native UTC, prayer clock or sky age fence.
 * A rotated spherical terminator moves at most D/2 * |delta alpha| pixels.
 * Nearest angular buckets have |delta alpha| <= quantum/2, so quantum=4*.0416/D
 * preserves the original .0416 DEVICE-pixel bound at the actual displayed size.
 * Cap at the normal 104px footprint's quantum for smaller/hidden presentations.
 * This geometric bound is not a bound on every terrain/photometric sample. */
const PHASE_QUANTUM=.0004;
const PHASE_POSITION_BUDGET=.0416;
function phaseQuantum(diameter=416){
 if(!Number.isFinite(diameter)||diameter<=0)throw new RangeError('native phase footprint');
 return 4*PHASE_POSITION_BUDGET/Math.max(104,diameter);
}
function canonicalFraction(f,diameter=416){
 if(typeof f!=='number'||!Number.isFinite(f)||f<0||f>1)throw new RangeError('native phase');
 if(f===0||f===1)return f;
 const quantum=phaseQuantum(diameter),a=Math.acos(2*f-1),q=Math.max(0,Math.min(Math.PI,Math.round(a/quantum)*quantum));
 return (1+Math.cos(q))/2;
}
