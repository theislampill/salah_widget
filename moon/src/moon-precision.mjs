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

// Shared calendar geometry; the existing native owner supplies every input.
function nativeCalendarMoonScene(s,profile){
 const nativeAlpha=Math.acos(2*s.fraction-1),moving=(s.timeScale??1)>0;
 const alpha=moving?Math.max(0,Math.min(Math.PI,nativeAlpha+(s.waxing?-1:1)*(2*PHASE_POSITION_BUDGET/s.maximumPhaseDiameter)*(1-1e-9))):Math.acos(2*s.physicalFraction-1);
 const fraction=(1+Math.cos(alpha))/2;
 return {size:540,outSize:300,diameter:288,basis:[0,1,0,0,0,1,1,0,0],sun:[Math.cos(alpha),(s.waxing?1:-1)*Math.sin(alpha),0],earth:[384400,0,0],distance:384400,extent:1.08,profile,mode:'calendar-canonical',fraction,waxing:s.waxing,tilt:0,requestedNativeFraction:s.fraction,phaseQuantumRadians:s.phaseQuantum,phaseDisplayDiameter:s.phaseDiameter,geometryConvention:'native accepted phase; leading-edge bounded display approximation while advancing, nearest while fixed; .0416 device px maximum; no future UTC'};
}
