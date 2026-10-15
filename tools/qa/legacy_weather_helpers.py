"""Closed native weather consumer cases. Requires the root's capacity-one execution lease.

Product source/assets are served read only. Controlled provider Response.json,
owned synthetic/forecast hooks, isolated storage, clock kind and suppressed fonts
are disclosed. Exit zero means executed checks passed, not visual/issue closure.
"""
import argparse
import hashlib
import http.server
import json
import os
from pathlib import Path
import struct
import sys
import threading
import time
import traceback
from urllib.parse import parse_qs, unquote, urlencode, urlsplit
import zlib

BASE=Path(__file__).resolve().parents[2]
ASSETS=BASE/"tests"/"weather-native"
def sha(data):return hashlib.sha256(data).hexdigest()
def write_json(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf-8")
def load_cases():return json.loads((ASSETS/"cases.json").read_text(encoding="utf-8"))
def png(rgba):
    def chunk(kind,data):return struct.pack('!I',len(data))+kind+data+struct.pack('!I',zlib.crc32(kind+data)&0xffffffff)
    raw=(b'\0'+bytes(rgba)*256)*256
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!2I5B',256,256,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b'')
def wait(page,predicate,arg=None,timeout=45000):
    end=time.monotonic()+timeout/1000
    while time.monotonic()<end:
        if page.evaluate(predicate,arg):return
        page.wait_for_timeout(100)
    raise TimeoutError('Owned direct-function predicate exceeded '+str(timeout)+'ms')

class FixtureServer:
    def __init__(self,root):
        self.root=Path(root).resolve();self.ledger=[];self.tile=png([130,123,105,73]);self.cases={x['id']:x for x in load_cases()}
        parent=self
        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_GET(self):
                parts=urlsplit(self.path);path=unquote(parts.path)
                if path=='/fixture.html':data=(ASSETS/'widget-fixture.html').read_bytes();mime='text/html; charset=utf-8'
                elif path=='/actions.js':data=(ASSETS/'actions.js').read_bytes();mime='text/javascript'
                elif path=='/forecast.js':data=(BASE/'tests'/'weather-forecast-fixture.js').read_bytes();mime='text/javascript'
                elif path=='/case.json':
                    name=parse_qs(parts.query).get('case',[''])[0]
                    if name not in parent.cases:self.send_error(404);return
                    data=json.dumps(parent.cases[name],ensure_ascii=False,allow_nan=False).encode();mime='application/json'
                elif path.startswith('/tile/v2/radar/') and path.endswith('/2/1_1.png'):data=parent.tile;mime='image/png'
                elif path.startswith('/product/'):
                    target=(parent.root/path[len('/product/'):]).resolve()
                    if not target.is_relative_to(parent.root) or not target.is_file():self.send_error(404);return
                    data=target.read_bytes();mime={'.js':'text/javascript','.mjs':'text/javascript','.css':'text/css','.wasm':'application/wasm','.html':'text/html; charset=utf-8','.json':'application/json','.png':'image/png','.svg':'image/svg+xml','.jpg':'image/jpeg','.webp':'image/webp'}.get(target.suffix,'application/octet-stream')
                elif path=='/favicon.ico':self.send_response(204);self.end_headers();return
                else:self.send_error(404);return
                parent.ledger.append({'path':path,'bytes':len(data),'sha256':sha(data)})
                self.send_response(200);self.send_header('Content-Type',mime);self.send_header('Content-Length',str(len(data)));self.send_header('Cache-Control','no-store');self.end_headers()
                try:self.wfile.write(data)
                except (BrokenPipeError,ConnectionResetError):parent.ledger.append({'path':path,'clientDisconnected':True})
        self.server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
    def __enter__(self):
        threading.Thread(target=self.server.serve_forever,daemon=True).start();self.origin='http://127.0.0.1:'+str(self.server.server_port);return self
    def __exit__(self,*args):self.server.shutdown();self.server.server_close()

def open_case(browser,server,spec,index_sha,run,attempt,out=None,wait_acquisition=True,failed=None):
    config={'lat':24.47,'lon':39.61,'tz':'Asia/Riyadh','label':'Weather fixture','method':4,'school':0,'units':'c','seed':1}
    if spec.get('preview'):config['timeScale']=1
    if spec.get('local'):config['local']=1
    if spec.get('motionFull'):config['motion']='full'
    if spec.get('night'):config.update(simMoon=0.5,simMoonAlt=20,simMoonH=42)
    context=browser.new_context(viewport={'width':390,'height':600},device_scale_factor=1,reduced_motion=spec.get('motion','no-preference'),timezone_id='Asia/Riyadh',**({'record_video_dir':str(out/'video')} if out and (spec.get('watchMotionSeconds') or spec.get('watchStrike') or spec.get('suspend')) else {}))
    page=context.new_page();errors=[];network=[]
    page.on('pageerror',lambda error:errors.append(str(error)));page.on('request',lambda request:network.append(request.url))
    if failed is not None:
        context.on('requestfailed',lambda r:failed.append({'scope':'Context','url':r.url,'failure':r.failure}))
        page.on('requestfailed',lambda r:failed.append({'scope':'Page','url':r.url,'failure':r.failure}))
    url=server.origin+'/fixture.html?'+urlencode({'case':spec['id'],'attempt':attempt,'run':run,'mode':'healthy','source':index_sha})+'#'+urlencode(config)
    page.goto(url,wait_until='domcontentloaded')
    wait(page,"()=>window.__widgetFixture?.state==='ready'||window.__widgetFixture?.state==='error'")
    if page.evaluate("()=>__widgetFixture.state")!='ready':raise AssertionError(page.evaluate("()=>__widgetFixture.error"))
    if wait_acquisition:wait(page,"()=>{const s=__weatherCases.read(__weatherCases.identity()),d=s.information.decision,h=s.information.header;return s.qa.cache.prayerLoaded&&!s.wxBusy&&!s.radarBusy&&h&&h.generation===d.target.generation&&h.rawCode===(d.record?.code??null)&&h.temperature===(d.record?.temp??null);}")
    return context,page,errors,network,url

def pixel_delta(before,after):
    try:
        from PIL import Image,ImageChops
        with Image.open(before) as a,Image.open(after) as b:
            a=a.convert('RGB');b=b.convert('RGB')
            if a.size!=b.size:return {'available':False,'reason':'geometry mismatch'}
            d=ImageChops.difference(a,b);values=list(d.getdata())
            return {'available':True,'changedChannelsGt2':sum(c>2 for p in values for c in p),'maxChannelDelta':max(c for p in values for c in p),'pixels':len(values),'scope':'actual cloud crop pixels; independent visual inspection still required'}
    except ImportError:return {'available':False,'reason':'Pillow unavailable; actual before/after crops and clip retained'}

def accessibility(page):
    result={}
    for selector in ('#wi','.buckle','#weather-information'):
        try:result[selector]=page.locator(selector).aria_snapshot(timeout=1000) if page.locator(selector).count() else {'unavailable':'Element absent in this source'}
        except Exception as error:result[selector]={'unavailable':str(error)}
    if page.context.browser.browser_type.name=='chromium':
        session=page.context.new_cdp_session(page)
        try:
            root=session.send('DOM.getDocument')['root']['nodeId']
            for selector in ('#wi','.buckle'):
                node=session.send('DOM.querySelector',{'nodeId':root,'selector':selector})['nodeId']
                backend=session.send('DOM.describeNode',{'nodeId':node})['node']['backendNodeId']
                result[selector+'-AX']=session.send('Accessibility.getPartialAXTree',{'backendNodeId':backend,'fetchRelatives':False})
        finally:session.detach()
    return result
