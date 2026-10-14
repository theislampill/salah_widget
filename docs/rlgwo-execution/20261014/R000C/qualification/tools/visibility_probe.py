"""Twenty-second passive diagnostic of the existing headed fixture, not qualification.

Reuse its original driver, input, readiness, server, binary and recorder. End
before either acceptance watch. Never call product render, fetch or lunar APIs.
"""
import hashlib
import importlib.util
from pathlib import Path
import sys
import time

driver = Path.cwd() / 'tools/qa/run_r000c_native.py'
assert hashlib.sha256(driver.read_bytes()).hexdigest() == '76cdd0cc607a4c1df85d69a492c7d4994dfeda26d9cf55b2ce0b278914f9ffce'
out = Path(sys.argv[sys.argv.index('--out') + 1]).resolve()
spec = importlib.util.spec_from_file_location('r000c_bound_driver', driver)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
original_wait = module.wait
samples = []
READ = """() => {
  const c=document.querySelector('.c'), r=c.getBoundingClientRect();
  const owner=window.__smokeWeather.identity();
  window.__fixtureClock.assertOwned(owner);
  return {nativeElapsedMs:performance.now(),wallUtcMs:Date.now(),
    visibility:document.visibilityState,hidden:document.hidden,
    visibilityEvents:window.__r000cVisibilityHistory.slice(),
    paused:c.classList.contains('paused'),loopStarted:_loopStarted,
    rect:{x:r.x,y:r.y,width:r.width,height:r.height},
    viewport:{width:innerWidth,height:innerHeight},
    lastRenderAtMs:_lastRender?.atMs,precip:weather?.precip,wxBusy,
    lastWxAt,lastWxTry,
    requests:window.__widgetFixture.ledger.map(x=>({url:x.url,elapsedMs:x.elapsedMs,jsonReads:x.jsonReads,jsonSettled:x.jsonSettled}))};
}"""


def diagnostic_wait(page, predicate, timeout=45000):
    original_wait(page, predicate, timeout)
    if predicate != module.READY:
        return
    page.evaluate("""() => {
      window.__r000cVisibilityHistory=[];
      document.addEventListener('visibilitychange',()=>window.__r000cVisibilityHistory.push({
        atMs:performance.now(),visibility:document.visibilityState,hidden:document.hidden}));
    }""")
    started = time.monotonic()
    for i in range(21):
        samples.append({'hostMonotonic': time.monotonic(), 'state': page.evaluate(READ)})
        module.dump(out / 'passive-visibility.json', {'diagnosticOnly': True, 'samples': samples})
        if i < 20:
            time.sleep(max(0, started + i + 1 - time.monotonic()))
    raise RuntimeError('DIAGNOSTIC_COMPLETE: deliberately ended before acceptance watches; no qualification credit')


module.wait = diagnostic_wait
status = module.main()
module.dump(out / 'diagnostic-binding.json', {
    'schema': 'r000c-passive-visibility-probe/v1', 'diagnosticOnly': True,
    'status': 'DIAGNOSTIC_COMPLETE' if len(samples) == 21 else 'DIAGNOSTIC_INCOMPLETE',
    'driverExitCode': status, 'driverSha256': module.sha(driver.read_bytes()),
    'probeSha256': module.sha(Path(__file__).read_bytes()),
    'override': 'Original READY wait succeeds, then21 passive reads over20 native host seconds; deliberately stop before acceptance watches.',
    'unavailable': '_onScreen and _raf are private closure variables; no value is fabricated. Read the product-owned paused class and document visibility instead.',
    'limitations': __doc__})
print('PASSIVE_DIAGNOSTIC_ONLY', len(samples), 'samples; acceptance status remains FAIL')
