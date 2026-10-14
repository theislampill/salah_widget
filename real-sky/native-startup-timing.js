/* Optional capture observer. It records owner admissions; it grants no authority. */
(() => {
  if (window.SalahStartupTiming) return;
  if (!globalThis.crypto?.getRandomValues || !globalThis.performance?.now) return;
  const token = () => Array.from(crypto.getRandomValues(new Uint32Array(4)),
    x => x.toString(16).padStart(8, '0')).join('');
  const documentId = token();
  const clock = Object.freeze({id: `document:${documentId}`, kind: 'window-performance',
    unit: 'ms', documentId, timeOriginMs: performance.timeOrigin});
  const admissions = [], events = [], rejected = [], lookup = new Map();
  let firstValidAdmission = null, presentedMarker = null, overflow = false;
  const limit = 512;
  const freeze = value => {
    if (value && typeof value === 'object') {
      Object.values(value).forEach(freeze); Object.freeze(value);
    }
    return value;
  };
  const finite = value => typeof value === 'number' && Number.isFinite(value);
  const binding = (s, configIdentity) => {
    if (!s || typeof s.sceneIdentity !== 'string' || !s.sceneIdentity ||
      typeof configIdentity !== 'string' || !configIdentity ||
      !Number.isSafeInteger(s.generation) || s.generation < 0 ||
      !finite(s.dpr) || s.dpr <= 0 || !finite(s.utcMs)) return null;
    return freeze({sceneIdentity: s.sceneIdentity, configIdentity,
      generation: s.generation, dpr: s.dpr});
  };
  const key = value => JSON.stringify(value);
  const reject = reason => {
    if (rejected.length < limit) rejected.push(freeze({reason, atMs: performance.now()}));
    else overflow = true;
    return null;
  };
  const admit = (snapshot, source, configIdentity) => {
    try {
      const b = binding(snapshot, configIdentity);
      if (!b || !['head', 'native'].includes(source)) return reject('invalid admission identity');
      const previous = lookup.get(key(b));
      if (previous) return previous.admissionId;
      if (admissions.length >= limit) { overflow = true; return null; }
      const admissionId = `${clock.id}/a${admissions.length + 1}`;
      const markerToken = token();
      if (admissions.some(x => x.markerToken === markerToken)) return reject('marker identity collision');
      const row = freeze({kind: 'valid-shared-scene-admission', eventId: admissionId,
        admissionId, clockId: clock.id, documentId, atMs: performance.now(),
        binding: b, source, utcMs: snapshot.utcMs, markerToken});
      admissions.push(row); lookup.set(key(b), row);
      if (firstValidAdmission === null) firstValidAdmission = row;
      return admissionId;
    } catch { return reject('admission observer error'); }
  };
  const stage = (kind, detail) => {
    try {
      if (!['head-work-start', 'head-work-end', 'native-adoption'].includes(kind))
        return reject('unknown stage');
      const b = binding(detail?.snapshot, detail?.configIdentity);
      const admission = b && lookup.get(key(b));
      if (!admission || admission.admissionId !== detail?.admissionId ||
        !['head', 'native'].includes(detail.source)) return reject('stage identity mismatch');
      if (kind.startsWith('head-') && detail.source !== 'head') return reject('head source mismatch');
      if (kind === 'native-adoption' && detail.source !== 'native') return reject('native source mismatch');
      if (kind === 'head-work-end' && !['published', 'error', 'superseded'].includes(detail.status))
        return reject('missing head outcome');
      if (events.length >= limit) { overflow = true; return null; }
      const eventId = `${clock.id}/e${events.length + 1}`;
      const row = {kind, eventId, admissionId: admission.admissionId,
        clockId: clock.id, documentId, atMs: performance.now(), binding: b,
        source: detail.source, utcMs: detail.snapshot.utcMs};
      if (kind === 'head-work-end') row.status = detail.status;
      if (typeof detail.reason === 'string') row.reason = detail.reason;
      events.push(freeze(row));
      if ((kind === 'head-work-end' && detail.status === 'published') || kind === 'native-adoption') {
        presentedMarker = freeze({token: admission.markerToken, admissionId: admission.admissionId,
          documentId, clockId: clock.id});
        if (window.__SALAH_STARTUP_CAPTURE_MARKER__ === true && window.parent !== window) {
          try { window.parent.postMessage({kind: 'salah-startup-pixel-marker/1', ...presentedMarker}, '*'); }
          catch { /* Marker availability is diagnostic; it cannot change publication. */ }
        }
      }
      return eventId;
    } catch { return reject('stage observer error'); }
  };
  const snapshot = () => freeze({schema: 'salah-startup-timing/1', clock,
    firstValidAdmission, admissions: admissions.slice(), events: events.slice(),
    rejected: rejected.slice(), presentedMarker, overflow});
  Object.defineProperty(window, 'SalahStartupTiming', {
    value: Object.freeze({admit, stage, snapshot, marker: () => presentedMarker}), writable: false, configurable: false
  });
})();
