"""R0026 layout-identity check for the builder tip (title + live-region change).

Serves two generated trees (--before, --after) on 127.0.0.1, loads builder.html in headless Chromium at the same
viewport with every non-local request aborted and the preview iframe's index.html replaced by a blank page (the
live sky animates, so its pixels are not comparable), sets the same tip text through the page's own setTip, and
compares full-page screenshots pixel by pixel (in-browser canvas) plus the #geotip / #pv / form boxes.
Paths in the JSON are relative to --out. No provider request, no position.
"""
import argparse, base64, functools, hashlib, http.server, json, socket, sys, threading
from pathlib import Path
from playwright.sync_api import sync_playwright

TEXT = 'Search unavailable — try again, use the pin, or enter coordinates.'
BOXES = "()=>Object.fromEntries(['geotip','pv','label','lat','lon','geo'].map(id=>{const r=document.getElementById(id).getBoundingClientRect();return [id,[r.x,r.y,r.width,r.height]]}))"
C = "{lat:43.64,lon:-79.39,name:'Toronto',norm:'Toronto, Ontario, Canada',cc:'ca',provider:'Nominatim'}"
C2 = "{lat:51.5,lon:-0.12,name:'London',norm:'London, England, United Kingdom',cc:'gb',provider:'Nominatim'}"
GEO = "p=>Object.defineProperty(navigator,'geolocation',{configurable:true,value:{getCurrentPosition:(ok,bad)=>p?ok({coords:{latitude:p[0],longitude:p[1],accuracy:5},timestamp:Date.now()}):bad({code:1,message:'User denied Geolocation'})}})"
# Every builder tip, produced by the page's own functions (not retyped strings).
MESSAGES = [('default', 'setTip(TIP_DEFAULT)'), ('searching', 'startDots()'),
            ('no-match', 'searchFailed(captureLookup(),"no-match")'), ('unavailable', 'searchFailed(captureLookup(),"unavailable")'),
            ('found', 'foundSingle(%s,false)' % C), ('partial', 'foundSingle(%s,true)' % C),
            ('match-multi', 'multiCands=[%s,%s];multiIdx=0;multiOwner={...captureLookup(),label:$("label").value,partial:false};showMulti()' % (C, C2)),
            ('partial-multi', 'multiCands=[%s,%s];multiIdx=0;multiOwner={...captureLookup(),label:$("label").value,partial:true};showMulti()' % (C, C2)),
            ('requesting', '(%s)([999,10]);navigator.geolocation.getCurrentPosition=()=>{};locate(false)' % GEO),
            ('invalid-position', '(%s)([999,10]);locate(false)' % GEO), ('browser-denied', '(%s)(null);locate(false)' % GEO),
            ('browser-position', '(%s)([43.64,-79.39]);locate(false)' % GEO),
            ('detected', 'SalahConfig.coarseDetect=async()=>({ok:true,cfg:{lat:51.5,lon:-0.12,label:"London",method:"4"}});detectArea()'),
            ('detect-failed', 'SalahConfig.coarseDetect=async()=>({ok:false});detectArea()')]
MEASURE = "()=>{const e=document.getElementById('geotip');return {text:e.textContent,title:e.title,scrollWidth:e.scrollWidth,clientWidth:e.clientWidth,clipped:e.scrollWidth>e.clientWidth}}"
DIFF = """async ([a,b])=>{const load=s=>new Promise(r=>{const i=new Image();i.onload=()=>r(i);i.src='data:image/png;base64,'+s;});
 const [x,y]=await Promise.all([load(a),load(b)]);if(x.width!==y.width||x.height!==y.height)return {sameSize:false};
 const c=document.createElement('canvas');c.width=x.width;c.height=x.height;const g=c.getContext('2d');
 g.drawImage(x,0,0);const p=g.getImageData(0,0,c.width,c.height).data;g.clearRect(0,0,c.width,c.height);g.drawImage(y,0,0);
 const q=g.getImageData(0,0,c.width,c.height).data;let n=0,x0=1e9,y0=1e9,x1=-1,y1=-1;for(let i=0;i<p.length;i+=4)if(p[i]!==q[i]||p[i+1]!==q[i+1]||p[i+2]!==q[i+2]||p[i+3]!==q[i+3]){n++;const k=i/4,px=k%c.width,py=(k-px)/c.width;x0=Math.min(x0,px);y0=Math.min(y0,py);x1=Math.max(x1,px);y1=Math.max(y1,py);}
 return {sameSize:true,width:c.width,height:c.height,differentPixels:n,bbox:n?[x0,y0,x1,y1]:null};}"""


def capture(browser, root, out, name, port, measure=False):
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass
    class Server(http.server.ThreadingHTTPServer):
        def handle_error(self, *args):
            pass
    server = Server(('127.0.0.1', port), functools.partial(Quiet, directory=str(root)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f'http://127.0.0.1:{server.server_address[1]}'
    ctx = browser.new_context(viewport={'width': 1100, 'height': 900}, reduced_motion='reduce')
    ctx.route(lambda u: not u.startswith(base), lambda r: r.abort())
    ctx.route(lambda u: u.startswith(base) and u[len(base):].split('?')[0].split('#')[0] in ('/', '/index.html'), lambda r: r.fulfill(status=200, content_type='text/html', body='<!doctype html><body style="margin:0;background:#123"></body>'))
    page = ctx.new_page(); page.goto(base + '/builder.html')
    page.wait_for_function("()=>/^Couldn/.test(document.getElementById('geotip').textContent)")
    page.add_style_tag(content='*{transition:none!important;animation:none!important;caret-color:transparent!important}')
    page.evaluate('t=>{document.activeElement&&document.activeElement.blur();setTip(t);}', TEXT); page.wait_for_timeout(1500)
    png = page.screenshot(full_page=True); (out / f'{name}.png').write_bytes(png)
    tip = page.evaluate("()=>{const e=document.getElementById('geotip');return {text:e.textContent,title:e.title,role:e.getAttribute('role'),ariaLive:e.getAttribute('aria-live'),ellipsised:e.scrollWidth>e.clientWidth}}")
    info = {'png': f'{name}.png', 'sha256': hashlib.sha256(png).hexdigest(), 'builderSha256': hashlib.sha256((root / 'builder.html').read_bytes()).hexdigest(),
            'boxes': page.evaluate(BOXES), 'tip': tip}
    if measure:
        rows, boxes0 = [], {k: v for k, v in info['boxes'].items() if k != 'geotip'}
        for key, js in MESSAGES:
            page.evaluate('js=>{(0,eval)(js)}', js); page.wait_for_timeout(250)
            m = page.evaluate(MEASURE); page.locator('#geotip').screenshot(path=str(out / f'tip-{key}.png'))
            b = page.evaluate(BOXES); m.update(key=key, crop=f'tip-{key}.png', tipHeight=b['geotip'][3], otherBoxesUnchanged={k: v for k, v in b.items() if k != 'geotip'} == boxes0)
            rows.append(m)
        info['messages'] = rows
    ctx.close(); server.shutdown(); server.server_close()
    return png, info


if __name__ == '__main__':
    a = argparse.ArgumentParser(); a.add_argument('--before', required=True); a.add_argument('--after', required=True); a.add_argument('--out', required=True)
    o = a.parse_args(); out = Path(o.out); out.mkdir(parents=True, exist_ok=True); sys.stdout.reconfigure(encoding="utf-8")
    with sync_playwright() as p:
        b = p.chromium.launch()
        probe = socket.socket(); probe.bind(('127.0.0.1', 0)); port = probe.getsockname()[1]; probe.close()   # same origin for both trees
        pb, before = capture(b, Path(o.before), out, 'tip-before', port); pa, after = capture(b, Path(o.after), out, 'tip-after', port, measure=True)
        page = b.new_page(); diff = page.evaluate(DIFF, [base64.b64encode(pb).decode(), base64.b64encode(pa).decode()])
        report = {'browser': 'chromium ' + b.version, 'viewport': [1100, 900], 'text': TEXT, 'before': before, 'after': after, 'pixelDiff': diff,
                  'boxesEqual': before['boxes'] == after['boxes'], 'identical': diff.get('differentPixels') == 0 and before['boxes'] == after['boxes']}
        b.close()
    (out / 'tip-layout.json').write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps({k: report[k] for k in ('pixelDiff', 'boxesEqual', 'identical')}))
    for m in after['messages']:
        print(f"{m['key']:16} clipped={m['clipped']!s:5} {m['scrollWidth']:>4}/{m['clientWidth']:<4} h={m['tipHeight']} same-geometry={m['otherBoxesUnchanged']} | {m['text']}")
    sys.exit(0 if report['identical'] else 1)
