/* =============================================================================
 * config.js — the canonical WidgetConfig contract for the Prayer Times widget.
 *
 * SINGLE SOURCE OF TRUTH for config logic, shared by index.html (runtime) and
 * builder.html (snippet generator). Loaded as a classic same-origin <script> BEFORE
 * the inline page script; exposes a plain global `window.SalahConfig`. No build, no
 * modules, no dependencies (consistent with the project's no-build / static-Pages rule).
 *
 * This file deliberately relaxes the former "single self-contained index.html"
 * invariant — by the maintainer's explicit choice — so config logic can NEVER fork
 * between the widget and the builder (the task's "do not fork config logic" rule).
 * index.html keeps a one-line fallback to legacy hash parsing if this file fails to
 * load, so a 404 degrades instead of white-screening.
 *
 * Sources of a resolved config (the `source` field): hash | localStorage | coarse-ip
 * | browser-geolocation | manual | fallback.
 * ========================================================================== */
(function (root) {
  "use strict";

  var KEY = "salah_widget:config:v1";   // versioned persistence key (NOT shared with prayer/weather caches)

  // Widget parse defaults — MUST mirror index.html's historical hash defaults so that
  // existing hardcoded embeds resolve byte-identically (method "2", units "f", 24h, iso
  // date, tz hint America/New_York which the widget overwrites from the API's meta zone).
  var DEFAULTS = {
    v: 1,
    lat: null, lon: null,
    tz: "America/New_York",
    label: "",
    method: "2", school: "0",
    time: "24",
    datefmt: "YYYY-MM-DD",
    units: "f",
    lp: 0, seed: null,
    source: "fallback", savedAt: null
  };

  // Back-compat date-format preset keys (old embeds) → Unicode token strings.
  var DATEFMT_PRESETS = { iso: "YYYY-MM-DD", us: "MM/DD/YYYY", eu: "DD/MM/YYYY", long: "DD MMMM YYYY" };

  // ---- small helpers --------------------------------------------------------
  function numOrNull(x) { if (x == null || x === "") return null; var n = +x; return isNaN(n) ? null : n; }
  function clampN(x, a, b) { return Math.min(b, Math.max(a, x)); }
  function clamp01(x) { return clampN(x, 0, 1); }
  function mapDatefmt(raw) { if (!raw) return DEFAULTS.datefmt; return DATEFMT_PRESETS[String(raw).toLowerCase()] || String(raw); }

  // ---- parse: URL hash → partial config (present keys only) + mode flags -----
  function parseHash(hashStr) {
    var s = hashStr == null ? "" : String(hashStr);
    if (s.charAt(0) === "#") s = s.slice(1);
    var q = new URLSearchParams(s);
    var flags = { local: q.get("local") === "1", preferLocal: q.get("preferLocal") === "1" };
    var c = {};
    if (q.has("lat")) c.lat = numOrNull(q.get("lat"));
    if (q.has("lon")) c.lon = numOrNull(q.get("lon"));
    if (q.has("tz")) c.tz = q.get("tz");
    if (q.has("label")) c.label = q.get("label");
    if (q.has("method")) c.method = q.get("method");
    if (q.has("school")) c.school = q.get("school");
    if (q.has("time")) c.time = q.get("time") === "12" ? "12" : "24";
    if (q.has("datefmt")) c.datefmt = mapDatefmt(q.get("datefmt"));
    if (q.has("units")) c.units = String(q.get("units")).toLowerCase() === "c" ? "c" : "f";
    if (q.has("lp")) c.lp = clamp01(numOrNull(q.get("lp")) || 0);
    if (q.has("seed")) c.seed = numOrNull(q.get("seed"));
    return { cfg: c, flags: flags };
  }

  // ---- normalize: fill defaults, coerce types, clamp ranges -----------------
  function normalize(cfg) {
    var c = Object.assign({}, DEFAULTS, cfg || {});
    c.lat = numOrNull(c.lat); c.lon = numOrNull(c.lon);
    if (c.lat != null) c.lat = clampN(c.lat, -90, 90);
    if (c.lon != null) c.lon = clampN(c.lon, -180, 180);
    c.tz = (typeof c.tz === "string" && c.tz) ? c.tz : DEFAULTS.tz;
    c.label = (c.label == null) ? "" : String(c.label);
    c.method = /^([0-9]|1[0-6])$/.test(String(c.method)) ? String(c.method) : DEFAULTS.method;
    c.school = (String(c.school) === "1") ? "1" : "0";
    c.time = (String(c.time) === "12") ? "12" : "24";
    c.units = (String(c.units).toLowerCase() === "c") ? "c" : "f";
    c.datefmt = (typeof c.datefmt === "string" && c.datefmt) ? c.datefmt : DEFAULTS.datefmt;
    c.lp = clamp01(numOrNull(c.lp) || 0);
    c.seed = numOrNull(c.seed);
    c.source = (typeof c.source === "string" && c.source) ? c.source : "fallback";
    c.savedAt = numOrNull(c.savedAt);
    c.v = 1;
    return c;
  }

  // ---- validate: a config is USABLE only with real coordinates --------------
  function validate(cfg) {
    var c = cfg || {}, e = [];
    if (c.lat == null || isNaN(+c.lat) || +c.lat < -90 || +c.lat > 90) e.push("lat");
    if (c.lon == null || isNaN(+c.lon) || +c.lon < -180 || +c.lon > 180) e.push("lon");
    if (!/^([0-9]|1[0-6])$/.test(String(c.method))) e.push("method");
    if (!(String(c.school) === "0" || String(c.school) === "1")) e.push("school");
    if (!(String(c.time) === "12" || String(c.time) === "24")) e.push("time");
    if (!(String(c.units) === "f" || String(c.units) === "c")) e.push("units");
    if (c.lp != null && (c.lp < 0 || c.lp > 1)) e.push("lp");
    return { ok: e.length === 0, errors: e };
  }

  // ---- serialize: config → URL hash string ----------------------------------
  // opts.mode: "local" → generic "#local=1" (no coordinates); "preferLocal" → adds
  // preferLocal=1 + emits coordinates as defaults. Default (portable/hardcoded) emits
  // location + always method/school — matching builder.html's historical output so
  // existing portable snippets stay byte-identical.
  function serialize(cfg, opts) {
    opts = opts || {};
    var c = normalize(cfg), p = new URLSearchParams(), local = opts.mode === "local";
    if (local) p.set("local", "1");
    else if (opts.mode === "preferLocal") p.set("preferLocal", "1");
    if (!local) {
      if (c.lat != null) p.set("lat", String(c.lat));
      if (c.lon != null) p.set("lon", String(c.lon));
      if (c.label) p.set("label", c.label);
      p.set("method", c.method);
      p.set("school", c.school);
    } else {
      // generic local snippet: only carry non-default *preferences*, never coordinates
      if (c.method !== DEFAULTS.method) p.set("method", c.method);
      if (c.school !== DEFAULTS.school) p.set("school", c.school);
    }
    if (c.time === "12") p.set("time", "12");
    if (c.datefmt && c.datefmt !== DEFAULTS.datefmt) p.set("datefmt", c.datefmt);
    if (c.units === "c") p.set("units", "c");
    if (c.lp > 0) p.set("lp", String(c.lp));
    if (c.seed != null) p.set("seed", String(c.seed));
    return p.toString();
  }

  // ---- localStorage (every access wrapped; never throws to the caller) -------
  function storageAvailable() {
    try {
      var k = "__sw_probe__";
      root.localStorage.setItem(k, "1"); root.localStorage.removeItem(k);
      return { ok: true };
    } catch (e) { return { ok: false, error: (e && e.name) || "error" }; }
  }
  function loadLocal() {
    try {
      var raw = root.localStorage.getItem(KEY);
      if (!raw) return null;
      var j = JSON.parse(raw);
      if (!j || j.v !== 1) return null;            // version gate (future migrations)
      var c = normalize(j);
      if (!validate(c).ok) return null;            // corrupt/partial → ignore (fall through to detect)
      c.origin = c.source;                         // how the coords were obtained (coarse-ip / browser-geolocation / manual) — survives the storage marker
      c.source = "localStorage"; c.savedAt = numOrNull(j.savedAt);
      return c;
    } catch (e) { return null; }
  }
  function saveLocal(cfg) {
    try {
      var c = normalize(cfg); c.v = 1; c.savedAt = Date.now();
      root.localStorage.setItem(KEY, JSON.stringify(c));
      return { ok: true, savedAt: c.savedAt };
    } catch (e) { return { ok: false, error: (e && e.name) || "error" }; }
  }
  function clearLocal() {
    try { root.localStorage.removeItem(KEY); return { ok: true }; }
    catch (e) { return { ok: false, error: (e && e.name) || "error" }; }
  }

  // ---- coarse, permission-free area detection (sends the IP to the provider) -
  // GeoJS primary → ipinfo.io fallback (both live-CORS-verified). IANA timezone is
  // taken from the device (Intl) first — the honest "where the clock is" — falling
  // back to the provider's zone. Returns a normalized coarse-ip config or {ok:false}.
  function detectTz() {
    try { return (Intl.DateTimeFormat().resolvedOptions().timeZone) || ""; } catch (e) { return ""; }
  }
  function methodForCC(cc) { cc = String(cc || "").toUpperCase(); return (cc === "US" || cc === "CA" || cc === "MX") ? "2" : "4"; }
  function unitsForCC(cc) { return String(cc || "").toUpperCase() === "US" ? "f" : "c"; }   // US → imperial (°F); everywhere else → metric (°C)
  function coarseDetect(opts) {
    opts = opts || {};
    var timeoutMs = opts.timeoutMs || 6000, tzIntl = detectTz();
    var providers = [
      { name: "GeoJS", url: "https://get.geojs.io/v1/ip/geo.json", parse: function (j) {
          return { lat: parseFloat(j.latitude), lon: parseFloat(j.longitude),
            label: j.city || j.region || j.country || "",   // concise: the small header shows just the locality
            area: [j.city, j.region, j.country].filter(Boolean).join(", "),
            tz: j.timezone || "", cc: j.country_code, accuracy: j.accuracy != null ? +j.accuracy : null }; } },
      { name: "ipinfo", url: "https://ipinfo.io/json", parse: function (j) {
          var loc = String(j.loc || "").split(",");
          return { lat: parseFloat(loc[0]), lon: parseFloat(loc[1]),
            label: j.city || j.region || j.country || "",
            area: [j.city, j.region, j.country].filter(Boolean).join(", "),
            tz: j.timezone || "", cc: j.country, accuracy: null }; } }
    ];
    return (function next(i) {
      if (i >= providers.length) return Promise.resolve({ ok: false, source: "coarse-ip", status: "failed" });
      var p = providers[i], ac = new AbortController(), to = setTimeout(function () { ac.abort(); }, timeoutMs);
      return fetch(p.url, { signal: ac.signal, mode: "cors", referrerPolicy: "no-referrer", cache: "no-store" })
        .then(function (r) { clearTimeout(to); if (!r.ok) throw new Error("http " + r.status); return r.json(); })
        .then(function (j) {
          var d = p.parse(j);
          if (d.lat == null || d.lon == null || isNaN(d.lat) || isNaN(d.lon)) throw new Error("no coords");
          var cfg = normalize({ lat: d.lat, lon: d.lon, label: d.label || "",
            tz: tzIntl || d.tz || "", method: methodForCC(d.cc), units: unitsForCC(d.cc), source: "coarse-ip" });
          cfg.source = "coarse-ip"; cfg.detectProvider = p.name; cfg.accuracy = d.accuracy; cfg.area = d.area || cfg.label;
          return { ok: true, cfg: cfg, source: "coarse-ip", provider: p.name, status: "ok" };
        })
        .catch(function () { clearTimeout(to); return next(i + 1); });
    })(0);
  }

  // ---- precise geolocation (ONLY call from a user gesture) -------------------
  function geolocate(opts) {
    opts = opts || {};
    return new Promise(function (resolve) {
      if (!root.navigator || !root.navigator.geolocation) { resolve({ ok: false, error: "unsupported" }); return; }
      root.navigator.geolocation.getCurrentPosition(
        function (pos) { resolve({ ok: true, lat: pos.coords.latitude, lon: pos.coords.longitude,
          accuracy: pos.coords.accuracy, source: "browser-geolocation" }); },
        function (err) { resolve({ ok: false, error: (err && err.message) || "denied", code: err && err.code }); },
        { enableHighAccuracy: false, timeout: opts.timeoutMs || 10000, maximumAge: 600000 }
      );
    });
  }
  function permissionState() {
    try {
      if (root.navigator && root.navigator.permissions && root.navigator.permissions.query)
        return root.navigator.permissions.query({ name: "geolocation" }).then(function (s) { return s.state; }, function () { return "unknown"; });
    } catch (e) {}
    return Promise.resolve("unknown");
  }

  // ---- precedence resolver (synchronous part) -------------------------------
  // Returns {mode, cfg|null, needsDetect, hashCfg, flags}. The async coarse-detect
  // path is run by the caller (index.html boot) when needsDetect is true, so hardcoded
  // mode stays fully synchronous at module load (preserving the historical boot timing).
  function resolve(hashStr) {
    var parsed = parseHash(hashStr), hashCfg = parsed.cfg, flags = parsed.flags;
    var mode, cfg = null, needsDetect = false;
    if (flags.local) mode = "local";
    else if (flags.preferLocal) mode = "preferLocal";
    else if (hashCfg.lat != null && hashCfg.lon != null) mode = "hardcoded";
    else mode = "bare";

    if (mode === "hardcoded") {
      cfg = normalize(Object.assign({}, hashCfg, { source: "hash" }));
    } else if (mode === "preferLocal") {
      var savedP = loadLocal();
      if (savedP) cfg = savedP;
      else if (hashCfg.lat != null && hashCfg.lon != null) cfg = normalize(Object.assign({}, hashCfg, { source: "hash" }));
      else needsDetect = true;
    } else if (mode === "local") {
      var savedL = loadLocal();
      if (savedL) cfg = savedL; else needsDetect = true;
    }
    return { mode: mode, cfg: cfg, needsDetect: needsDetect, hashCfg: hashCfg, flags: flags };
  }

  // Overlay explicitly-set hash PREFERENCES (not location) onto a detected/saved base,
  // so e.g. "#local=1&units=c" honours the unit even when the location comes from detect.
  function applyHashPrefs(base, hashCfg) {
    var c = Object.assign({}, base), PK = ["method", "school", "time", "units", "datefmt", "lp", "seed"];
    PK.forEach(function (k) { if (hashCfg && hashCfg[k] !== undefined) c[k] = hashCfg[k]; });
    if (hashCfg && hashCfg.label !== undefined && hashCfg.label !== "") c.label = hashCfg.label;
    return normalize(c);
  }

  // ---- forward geocoding (type a place / postcode → coordinates) ------------
  // Shared by builder.html AND the in-widget settings panel so the search behaviour
  // (Nominatim places/postcodes + Zippopotam Canadian FSA fallback, deduped) is identical
  // and never forks. Returns a Promise of candidates: {lat, lon, name, norm, cc}.
  function _nomCands(arr) {
    if (!Array.isArray(arr)) return [];
    var places = arr.filter(function (r) { return r.class === "place" || r.class === "boundary"; });
    return (places.length ? places : arr).map(function (res) {
      var a = res.address || {};
      var place = a.city || a.town || a.village || a.hamlet || a.municipality || a.suburb || a.county || res.name || "";
      return { lat: parseFloat(res.lat), lon: parseFloat(res.lon), name: place,
        norm: [place, a.state || a.region || a.province || "", a.country || ""].filter(Boolean).join(", "),
        cc: (a.country_code || "").toLowerCase() };
    });
  }
  function _zipCand(j) {
    if (!j || !j.places || !j.places.length) return null;
    var p = j.places[0], place = (p["place name"] || "").split(" (")[0].trim();
    return { lat: +p.latitude, lon: +p.longitude, name: place,
      norm: [place, p.state || "", j.country || ""].filter(Boolean).join(", "),
      cc: (j["country abbreviation"] || "").toLowerCase() };
  }
  function _dedupeCands(cs) {
    var out = [];
    cs.forEach(function (c) {
      if (c.lat == null || isNaN(c.lat) || c.lon == null || isNaN(c.lon)) return;
      if (!out.some(function (o) { return o.norm === c.norm || (Math.abs(o.lat - c.lat) < 0.2 && Math.abs(o.lon - c.lon) < 0.2); })) out.push(c);
    });
    return out;
  }
  function geocodeSearch(query, opts) {
    opts = opts || {};
    var q = String(query == null ? "" : query).trim();
    if (q.length < 2) return Promise.resolve([]);
    var homeCC = opts.homeCC || "";
    var ac = new AbortController(), to = setTimeout(function () { ac.abort(); }, opts.timeoutMs || 8000);
    var bias = (/\d/.test(q) && homeCC) ? ("&countrycodes=" + homeCC) : "";      // a digit ⇒ likely a postcode ⇒ keep it in the viewer's country
    var bare = q.replace(/\s/g, ""), caFSA = /^[A-Za-z]\d[A-Za-z]/.test(bare) ? bare.slice(0, 3).toUpperCase() : null;
    var jobs = [ fetch("https://nominatim.openstreetmap.org/search?format=jsonv2&addressdetails=1&limit=5" + bias + "&q=" + encodeURIComponent(q), { signal: ac.signal })
      .then(function (r) { return r.json(); }).then(_nomCands).catch(function () { return []; }) ];
    if (caFSA) jobs.push( fetch("https://api.zippopotam.us/ca/" + caFSA, { signal: ac.signal })
      .then(function (r) { return r.ok ? r.json() : null; }).then(function (j) { var c = _zipCand(j); return c ? [c] : []; }).catch(function () { return []; }) );
    return Promise.all(jobs).then(function (res) {
      clearTimeout(to);
      return _dedupeCands(res.reduce(function (a, b) { return a.concat(b); }, []));
    }).catch(function () { clearTimeout(to); return []; });
  }

  root.SalahConfig = {
    KEY: KEY, DEFAULTS: DEFAULTS, DATEFMT_PRESETS: DATEFMT_PRESETS,
    geocodeSearch: geocodeSearch,
    parseHash: parseHash, normalize: normalize, validate: validate, serialize: serialize,
    storageAvailable: storageAvailable, loadLocal: loadLocal, saveLocal: saveLocal, clearLocal: clearLocal,
    coarseDetect: coarseDetect, geolocate: geolocate, permissionState: permissionState,
    resolve: resolve, applyHashPrefs: applyHashPrefs
  };
})(typeof window !== "undefined" ? window : this);
