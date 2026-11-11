// Isolated pure source-boundary expressions only. No native page, producer,
// request, timer, listener, browser or product bootstrap is executed.
const fs = require('fs');
const crypto = require('crypto');
const vm = require('vm');
const sourcePath = '/workspace/scratch/15b8fb6ac4c2/r000b-work/src/native/index.html';
const source = fs.readFileSync(sourcePath, 'utf8');
const sha = text => crypto.createHash('sha256').update(text).digest('hex');
if (sha(source) !== 'b17801b33cc99c95710b916016dfd542eddce304145b493c0adecc4c3412e37f') throw Error('Frozen product interface source drift');
const between = (start, end) => {
  if (source.split(start).length !== 2) throw Error('Ambiguous source boundary: ' + start);
  const at = source.indexOf(start), stop = source.indexOf(end, at);
  if (stop < 0) throw Error('Missing source boundary: ' + end);
  return source.slice(at, stop).trim();
};
const number = source.match(/^function wxNumber\([^\n]+$/m)[0];
const target = between('function captureWeatherTarget(', '\nfunction weatherTargetSame(');
const raf = source.match(/^const _RAFNOW = [^\n]+$/m)[0];
const publication = between('function publishCloudAuthority(', '\nfunction rememberWeatherEffects(');
const projection = publication.match(/target:Object\.freeze\((\{generation:target\.generation,lat:target\.lat,lon:target\.lon\})\)/)[1];
const attempt = between('function beginAttempt(', '\nfunction attemptEligible(');
const deadline = attempt.match(/deadlineAt:([^,]+),timer:null/)[1];
const weatherWait = Number(source.match(/const _WX_BODY_WAIT=(\d+),/)[1]);
const observedClock = {started:125.25,startUtc:1788901190000};
const requestElapsedMs = 180000;
const context = {
  CONFIG:{locationEvidence:{intent:'fixed-site',source:'hash',accuracyM:null,acquiredAt:null,provider:null,area:null,bounds:null}},
  performance:{now:()=>observedClock.started+requestElapsedMs},
  Date:{now:()=>observedClock.startUtc+Math.floor(requestElapsedMs)},
  timeoutMs:weatherWait
};
const code = `${number}\n${target}\n${raf}\nconst target = captureWeatherTarget(7,24.7136,46.6753);\n` +
  `JSON.stringify({richTarget:target,receiptTarget:(${projection}),monotonicDeadline:(${deadline})});`;
const result = JSON.parse(new vm.Script(code, {filename:'isolated-pure-interface-expressions'}).runInNewContext(context, {timeout:1000}));
console.log(JSON.stringify({schema:'r000b-observed-source-interface-shapes/v1',
  scope:'Exact source pure constructor/projection/clock expressions under contained declared inputs; no native or producer execution',
  sourcePath,sourceSha256:sha(source),sourceFragments:{wxNumber:sha(number),captureWeatherTarget:sha(target),
    rafNow:sha(raf),receiptProjection:sha(projection),attemptDeadline:sha(deadline)},
  observedClock,requestElapsedMs,requestPerformanceMs:observedClock.started+requestElapsedMs,
  weatherAttemptBudgetMs:weatherWait,...result},null,2));
