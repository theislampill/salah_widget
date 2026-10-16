(() => {
  // Diagnostic phase only, installed after 30 seconds of ordinary capture.
  // Observe existing presentation; do not set application styles or request work.
  const card = document.querySelector('.c');
  const body = document.querySelector('.sunbody');
  const disc = document.querySelector('.sunbody .disc');
  const corner = document.querySelector('.suncorner');
  const mask = document.querySelector('.sun-cloud-mask');
  if (![card, body, disc, corner, mask].every(Boolean)) throw Error('Solar observation target missing');
  const startedAt = performance.now(), frames = [], states = [], masks = [], values = [];
  const maskIds = new Map(), valueIds = new Map();
  let raf = 0, lastState = -Infinity, stopped = false;
  function id(value, map, list, now) {
    if (!map.has(value)) { map.set(value, list.length); list.push({id:list.length, firstAt:now, value}); }
    return map.get(value);
  }
  function sample(now) {
    if (stopped) return;
    const c = getComputedStyle(card), b = getComputedStyle(body), d = getComputedStyle(disc);
    const g = getComputedStyle(corner), m = getComputedStyle(mask);
    const css = ['--sunamt','--sunbodyamt','--suncore','--sunmid','--sunprofile',
      '--sundisc','--sunflat','--sunpulse','--sunray','--sunx2','--sunlift'].map(k=>c.getPropertyValue(k));
    frames.push({at:now, mask:id(m.maskImage,maskIds,masks,now),
      solarStyle:id(JSON.stringify(css),valueIds,values,now),
      cardClass:card.className, bodyOpacity:b.opacity, bodyVisibility:b.visibility,
      bodyTransform:b.transform, discOpacity:d.opacity, discVisibility:d.visibility,
      cornerOpacity:g.opacity, cornerTransform:g.transform, maskVisibility:m.visibility});
    if (now-lastState>=250) {
      lastState=now;
      const sky=window.realSkyState?.(), native=window.SalahNativeSkyHost?.capture(false);
      states.push({at:now, sky:sky?{status:sky.status,renders:sky.renders,
        presentationDraws:sky.presentationDraws,presentationSkips:sky.presentationSkips,
        presentationRejections:sky.presentationRejections,rejections:sky.rejections,
        errors:sky.errors,reason:sky.reason,displayed:sky.displayed,lifecycle:sky.lifecycle}:null,
        native:native?{utcMs:native.utcMs,generation:native.generation,sceneIdentity:native.sceneIdentity,
          timeScale:native.timeScale,paused:native.paused,weather:native.weather}:null});
    }
    if (frames.length>=12000) { stopped=true; return; }
    raf=requestAnimationFrame(sample);
  }
  raf=requestAnimationFrame(sample);
  window.__SolarStrobeTrace={stop(){stopped=true;cancelAnimationFrame(raf);return {
    schema:'r0021-solar-css-observation/v1',startedAt,endedAt:performance.now(),timeOrigin:performance.timeOrigin,
    limitation:'Read-only CSS/layout and state sampling changes observer cost. Not ordinary startup or callback-cost evidence; no pixel/presentation verdict.',
    cssPropertyOrder:['--sunamt','--sunbodyamt','--suncore','--sunmid','--sunprofile',
      '--sundisc','--sunflat','--sunpulse','--sunray','--sunx2','--sunlift'],frames,states,masks,values};}};
  return {startedAt,timeOrigin:performance.timeOrigin,phase:'DIAGNOSTIC_AFTER_30S_ORDINARY'};
})()
