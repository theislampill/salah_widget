"""R000F bounded native observation: builder preview publication (issue #15, ES0F increment).

Serves the GENERATED builder.html / config.js / index.html unchanged from --root on 127.0.0.1 and drives the real
builder with real keyboard/mouse input. Every non-local request is intercepted at the browser-context level and
ABORTED (nothing reaches a real provider; the report lists each one with its disposition), so coarse detection and
reverse lookups fail closed. navigator.geolocation and the geolocation permission query are init-script doubles in
every frame (always "denied"; no real position is requested). Preview navigations are counted from the browser's own
frame events (`framenavigated` on the #pv child frame for a `?r=` URL, plus child-frame document requests), never from
the builder's revision counter. A navigation observed here is an ISSUED/committed frame navigation; it says nothing
about the widget inside having loaded or rendered.

Cells: load (one navigation) / equivalentEdit (typed equivalent spelling + commit → none) / changedSelect (one select
change → exactly one, frame fragment = embed snippet) / rapidTyping (navigations only for distinct outputs; final
frame = final draft) / invalidDraft (preview + export kept, aria-invalid + note, Copy/Install/Open refuse with readable
feedback, no popup) / refresh (forced re-issue once, also while invalid, never the invalid draft) / radios (Space,
Enter, arrow, click: one navigation per real mode change, none for the active mode; allow attribute follows) /
localEdits (local-mode location edits → none) / layout (boxes; #pv 325x530). Screenshots per stage.
--root selects the served tree (use a checkout of main for the control run); --out receives all evidence.
"""
import argparse, functools, hashlib, http.server, json, re, subprocess, sys, threading, time
from pathlib import Path
from urllib.parse import urlparse, parse_qs

REPO = Path(__file__).resolve().parents[2]
SERVED = ('builder.html', 'config.js', 'index.html')
GEO_INIT = r"""(()=>{const deny=(ok,bad)=>setTimeout(()=>bad&&bad({code:1,message:'fixture denied'}),10);
 const geo={getCurrentPosition:deny,watchPosition(ok,bad){deny(ok,bad);return 0;},clearWatch(){}};
 try{Object.defineProperty(Navigator.prototype,'geolocation',{get(){return geo;},configurable:true});}catch(e){}
 if(navigator.permissions){const q=navigator.permissions.query.bind(navigator.permissions);
  navigator.permissions.query=d=>d&&d.name==='geolocation'?Promise.resolve({state:'denied',onchange:null}):q(d);}})();"""
STATE = """()=>{const pv=document.getElementById('pv'),code=document.getElementById('code').value,m=code.match(/src="([^"]+)"/);
 const note=document.getElementById('draftnote');
 return {pvSrc:pv.getAttribute('src')||pv.src,pvAllow:pv.getAttribute('allow')||'',codeSrc:m?m[1]:null,codeAllow:/allow="geolocation"/.test(code),
  latInvalid:document.getElementById('lat').getAttribute('aria-invalid'),lonInvalid:document.getElementById('lon').getAttribute('aria-invalid'),
  note:note?{hidden:note.hidden,text:note.textContent}:null,copied:document.getElementById('copied').textContent,
  installtip:document.getElementById('installtip').textContent,
  embedRecoveryHidden:document.getElementById('embed-recovery-wrap').hidden,active:document.activeElement&&document.activeElement.id,
  mode:document.getElementById('mode-local').getAttribute('aria-checked')==='true'?'local':'portable'}}"""
BOXES = """()=>{const r=s=>{const e=document.querySelector(s);if(!e)return null;const b=e.getBoundingClientRect();
 return {x:Math.round(b.x*10)/10,y:Math.round(b.y*10)/10,w:Math.round(b.width*10)/10,h:Math.round(b.height*10)/10};};
 return Object.fromEntries(['#pv','.preview','form.card','.out','#code','#copy','#open','#install','#reload','.modebtns','#lat','#lon','#label']
  .map(s=>[s,r(s)]));}"""


# ---- pure helpers (unit-tested without a browser: tests/test_r000f_native_helpers.py) --------------------------
def is_preview_nav(url):
    """A preview navigation is a child-frame URL carrying the builder's ?r= cachebuster."""
    try:
        return 'r' in parse_qs(urlparse(url).query)
    except ValueError:
        return False


def fragment(url):
    return urlparse(url).fragment if url else None


def hash_params(url):
    return {k: v[0] for k, v in parse_qs(fragment(url) or '', keep_blank_values=True).items()}


def nav_delta(log, start):
    """Preview navigations recorded after index `start` (frame-event log of URLs)."""
    return [u for u in log[start:] if is_preview_nav(u)]


def distinct_outputs(values):
    """Expected issued sequence for a typed value sequence: consecutive duplicates collapse."""
    out = []
    for v in values:
        if not out or out[-1] != v:
            out.append(v)
    return out


def compare_boxes(a, b, tol=0.5):
    """Element boxes that differ by more than tol px between two layout readings (None = missing on one side)."""
    diff = {}
    for key in sorted(set(a) | set(b)):
        x, y = a.get(key), b.get(key)
        if x is None or y is None:
            if x != y:
                diff[key] = [x, y]
            continue
        if any(abs(x[k] - y[k]) > tol for k in ('x', 'y', 'w', 'h')):
            diff[key] = [x, y]
    return diff


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def tree_identity(root):
    try:
        return subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=root, capture_output=True, text=True, timeout=10).stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


# ---- native run ----------------------------------------------------------------------------------------------
def run(engine, root, out, headed, tag, compare=None):
    from importlib import metadata
    from playwright.sync_api import sync_playwright

    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=str(root)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f'http://127.0.0.1:{server.server_address[1]}/'
    report = {'argv': sys.argv, 'engine': engine, 'headed': headed, 'tag': tag,
              'playwright': metadata.version('playwright'), 'root': 'repository' if root.resolve() == REPO else root.name,
              'tree': tree_identity(root), 'served': {f: sha(root / f) for f in SERVED},
              'external': [], 'console': [], 'cells': {}, 'framesLog': [], 'documentRequests': [], 'popups': 0,
              'limits': 'frame navigations observed = issued/committed navigations; no widget load/render claim'}
    navs, docs = report['framesLog'], report['documentRequests']
    with sync_playwright() as p:
        browser = getattr(p, engine).launch(headless=not headed)
        report['browserVersion'] = browser.version
        ctx = browser.new_context(viewport={'width': 1280, 'height': 1000})
        ctx.add_init_script(GEO_INIT)

        def external(route):
            u = urlparse(route.request.url)
            report['external'].append([u.hostname, u.path, 'aborted'])
            route.abort()
        ctx.route(lambda url: not url.startswith(base), external)
        page = ctx.new_page()
        page.on('console', lambda m: report['console'].append([m.type, m.text]) if m.type == 'error' else None)
        page.on('pageerror', lambda e: report['console'].append(['pageerror', str(e)]))
        page.on('popup', lambda pop: (report.__setitem__('popups', report['popups'] + 1), pop.close()))

        def framenav(frame):
            if frame.parent_frame is not None and frame.name in ('', 'pv') and is_preview_nav(frame.url):
                navs.append(frame.url)
        page.on('framenavigated', framenav)
        page.on('request', lambda r: docs.append(r.url) if r.resource_type == 'document' and r.frame.parent_frame is not None and is_preview_nav(r.url) else None)

        def settle(quiet=1200, limit=15000):          # navigation count unchanged for `quiet` ms (covers the 700 ms reverse timer)
            end, n, t = time.monotonic() + limit / 1000, len(navs), time.monotonic()
            while time.monotonic() < end:
                page.wait_for_timeout(100)
                if len(navs) != n:
                    n, t = len(navs), time.monotonic()
                elif (time.monotonic() - t) * 1000 >= quiet:
                    return True
            return False
        state = lambda: page.evaluate(STATE)
        shot = lambda name: page.screenshot(path=str(out / f'{tag}-{name}.png'), full_page=True)
        cells = report['cells']

        def coherent(s):
            return bool(navs) and fragment(navs[-1]) == fragment(s['codeSrc']) and s['pvSrc'] == navs[-1] \
                and s['pvAllow'] == ('geolocation' if s['mode'] == 'local' else '') and s['codeAllow'] == (s['mode'] == 'local')

        page.goto(base + 'builder.html'); settle(2000)
        s = state(); boxes = page.evaluate(BOXES)
        cells['load'] = {'pass': len(navs) == 1 and coherent(s), 'navs': len(navs), 'state': s}
        cells['layout'] = {'pass': boxes['#pv'] is not None and boxes['#pv']['w'] == 325 and boxes['#pv']['h'] == 530, 'boxes': boxes}
        shot('1-load')

        # Equivalent spelling typed for real, then committed (Tab → change): no navigation.
        n0 = len(navs); page.click('#lat'); page.keyboard.press('End'); page.keyboard.type('0'); page.keyboard.type(' ')
        page.keyboard.press('Tab'); settle()
        cells['equivalentEdit'] = {'pass': len(navs) == n0, 'navs': len(nav_delta(navs, n0)), 'lat': page.input_value('#lat')}
        page.fill('#lat', '24.4672'); settle()

        # One real select change (Playwright dispatches input + change): exactly one, coherent outputs.
        n0 = len(navs); page.select_option('#method', '2'); settle(); s = state()
        d = nav_delta(navs, n0)
        cells['changedSelect'] = {'pass': len(d) == 1 and hash_params(d[0]).get('method') == '2' and coherent(s), 'navs': len(d), 'urls': d}
        # Keyboard on the select: one ArrowDown, then commit; navigations must equal real value changes (0 or 1).
        before = page.input_value('#method'); n0 = len(navs); page.focus('#method'); page.keyboard.press('ArrowDown'); page.keyboard.press('Tab'); settle()
        after = page.input_value('#method'); d = nav_delta(navs, n0)
        cells['selectArrowKey'] = {'pass': len(d) == (1 if after != before else 0) and coherent(state()), 'navs': len(d), 'before': before, 'after': after}

        # Rapid typing: select-all then type 21.5 key by key, then commit.
        n0 = len(navs); page.click('#lat', click_count=3); page.keyboard.type('21.5', delay=40); page.keyboard.press('Tab'); settle(); s = state()
        d = [hash_params(u).get('lat') for u in nav_delta(navs, n0)]
        cells['rapidTyping'] = {'pass': d == distinct_outputs(['2', '21', '21', '21.5']) and coherent(s) and hash_params(s['pvSrc']).get('lat') == '21.5',
                                'issuedLat': d}

        # Invalid draft (D1): cleared latitude.
        good = state(); n0 = len(navs); page.fill('#lat', ''); settle(); s = state(); shot('2-invalid')
        page.click('#copy'); page.wait_for_timeout(300); copy = state()
        page.click('#install'); page.wait_for_timeout(300); install = state()
        pops = report['popups']; page.click('#open'); page.wait_for_timeout(500)
        cells['invalidDraft'] = {'pass': bool(len(navs) == n0 and s['pvSrc'] == good['pvSrc'] and s['codeSrc'] == good['codeSrc'] and s['latInvalid'] == 'true'
                                 and s['note'] and not s['note']['hidden'] and bool(s['note']['text']) and 'valid' in copy['copied']
                                 and 'valid' in install['installtip'] and report['popups'] == pops and copy['embedRecoveryHidden']),
                                 'navs': len(nav_delta(navs, n0)), 'state': s, 'copyFeedback': copy['copied'], 'installFeedback': install['installtip'],
                                 'popupsDuringOpen': report['popups'] - pops}
        # Refresh (D3) while invalid: one forced re-issue of the last valid output, never the invalid draft.
        n0 = len(navs); page.click('#reload'); settle(); d = nav_delta(navs, n0)
        refresh_invalid = len(d) == 1 and hash_params(d[0]).get('lat') == '21.5'
        page.fill('#lat', '21.5'); settle(); back = len(nav_delta(navs, n0)) == 1
        n0 = len(navs); page.click('#reload'); settle(); d2 = nav_delta(navs, n0)
        cells['refresh'] = {'pass': refresh_invalid and back and len(d2) == 1 and fragment(d2[0]) == fragment(good['pvSrc']) and coherent(state()),
                            'invalidReissue': d, 'validReissue': d2, 'returnToIssuedAddedNone': back}

        # Radios: real Space / Enter / arrows / click.
        r = {}
        def radio(label, action, expect):
            n = len(navs); action(); settle(); r[label] = {'navs': len(nav_delta(navs, n)), 'expect': expect, 'mode': state()['mode']}
        radio('spaceLocal', lambda: (page.focus('#mode-local'), page.keyboard.press('Space')), 1)
        radio('enterActiveLocal', lambda: page.keyboard.press('Enter'), 0)
        radio('clickActiveLocal', lambda: page.click('#mode-local'), 0)
        shot('3-local')
        radio('enterPortable', lambda: (page.focus('#mode-portable'), page.keyboard.press('Enter')), 1)
        radio('arrowRight', lambda: (page.focus('#mode-portable'), page.keyboard.press('ArrowRight')), 1)
        radio('clickPortable', lambda: page.click('#mode-portable'), 1)
        cells['radios'] = {'pass': all(v['navs'] == v['expect'] for v in r.values()) and coherent(state()), 'steps': r}

        # Local mode omits location fields: their edits issue nothing; switching back publishes once.
        page.click('#mode-local'); settle(); n0 = len(navs)
        page.fill('#label', 'Cairo'); page.fill('#lat', '30.04'); page.fill('#lon', '31.24'); settle()
        quiet = len(navs) == n0
        page.click('#mode-portable'); settle(); d = nav_delta(navs, n0)
        cells['localEdits'] = {'pass': quiet and len(d) == 1 and hash_params(d[0]).get('lat') == '30.04' and coherent(state()), 'urls': d}
        shot('4-final')
        boxes2 = page.evaluate(BOXES)
        cells['layout']['afterRun'] = boxes2
        cells['layout']['pass'] = cells['layout']['pass'] and boxes2['#pv']['w'] == 325 and boxes2['#pv']['h'] == 530
        browser.close()
    server.shutdown()
    report['docRequestsMatchFrameNavs'] = len(docs) == len(navs)
    if compare:
        other = json.loads(Path(compare).read_text(encoding='utf-8'))
        report['layoutDiffVsCompare'] = compare_boxes(report['cells']['layout']['boxes'], other['cells']['layout']['boxes'])
        report['compare'] = {'tag': other.get('tag'), 'tree': other.get('tree'), 'served': other.get('served')}
    report['noProviderReached'] = all(e[2] == 'aborted' for e in report['external'])
    # Console 'error' lines from the deliberately aborted provider requests are recorded, not judged; page errors fail.
    report['pageErrors'] = [c for c in report['console'] if c[0] == 'pageerror']
    report['pass'] = all(v['pass'] for v in report['cells'].values()) and report['noProviderReached'] and not report['pageErrors']
    (out / f'{tag}-report.json').write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps({'engine': engine, 'tag': tag, 'version': report['browserVersion'], 'pass': report['pass'],
                      'cells': {k: v['pass'] for k, v in report['cells'].items()}, 'pageErrors': len(report['pageErrors']),
                      'external': len(report['external'])}))
    return report['pass']


if __name__ == '__main__':
    a = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    a.add_argument('--engine', choices=['chromium', 'firefox'], required=True)
    a.add_argument('--root', default=str(REPO), help='served tree (a checkout of main for the control run)')
    a.add_argument('--out', required=True, help='evidence directory (report JSON + screenshots)')
    a.add_argument('--tag', default=None, help='file prefix, default <engine>-candidate')
    a.add_argument('--compare', default=None, help='another report JSON whose layout boxes are diffed against this run')
    a.add_argument('--headed', action='store_true')
    o = a.parse_args(); out = Path(o.out); out.mkdir(parents=True, exist_ok=True)
    sys.exit(0 if run(o.engine, Path(o.root), out, o.headed, o.tag or f'{o.engine}-candidate', o.compare) else 1)
