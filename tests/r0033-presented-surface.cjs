'use strict';
// R0033 (issue 100, M4/R33-16): a registered Moon runtime stub that presents a current
// surface, for VM suites whose positive lunar-light cases need one (the R001D stub
// pattern). Since R0033, native light eligibility requires a presented surface; the
// generated host is not executed by the native VM harness, so without this stub every
// case would correctly read "surface-unavailable". One priming render establishes the
// sky scene (the predicate's _skySceneKey term). Harmless for sources that predate the
// predicate: they ignore `presentable` and see only a present, non-legacy runtime.
// The priming render consumes no case patch: lunar geometry is re-derived afterwards.
function presentSurface(h){
  h.run(`{ const cv=document.createElement('canvas');
    window.SalahMoonRuntime={presentable:true,surface(){return cv;},request(){return true;},
      get state(){return {status:'ready',visibleSource:'refined-terrain',quality:'empirical-adaptive',accepted:{identity:'r0033-stub'}};},
      detailEnabled:false,invalidate(){},finishInitialDocument(){},presentationUp:1,disposed:false}; }
    document.querySelector('.mphoto').setAttribute('href','data:image/png;base64,R0033_STUB');
    render();
    // Let the case's own scene patch recompute lunar geometry on its first render, as before.
    if(typeof lastMoonMin!=='undefined')lastMoonMin=-1;`);
  return h;
}
module.exports={presentSurface};
