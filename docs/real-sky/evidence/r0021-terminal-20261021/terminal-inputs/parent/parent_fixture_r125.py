"""Reuse the accepted native harness provider fixture in the actual Firefox parent.

Only clock/provider transport is inserted before the original application.
The insertion is removable byte-for-byte; no product style or state is replaced.
"""
from pathlib import Path
import ast,datetime,hashlib,json,sys,time,types
from urllib.parse import parse_qs,urlsplit
R=Path(r'${REPO_ROOT}')
sys.path.insert(0,str(R/'tests'));sys.path.insert(0,str(R/'tools/cp9'))
from v1_browser import fixture
from runtime_identity import runtime_identity
STAMP='2026-09-24T14:00:00Z'
SOURCE=R/'tools/cp9/celestial_startup_check.py'
tree=ast.parse(SOURCE.read_text(encoding='utf-8'))
run=next(n for n in tree.body if isinstance(n,ast.AsyncFunctionDef) and n.name=='run')
node=next(n for n in run.body if isinstance(n,ast.FunctionDef) and n.name=='provider')
scope={'fixture':fixture,'a':types.SimpleNamespace(scene='partial',prayer_delay=0,acquiring=False),'stamp':STAMP,'wx':2,'cloud':35,'time':time,'urlsplit':urlsplit,'parse_qs':parse_qs,'datetime':datetime.datetime,'timezone':datetime.timezone,'timedelta':datetime.timedelta}
exec(compile(ast.Module(body=[node],type_ignores=[]),str(SOURCE),'exec'),scope)
provider=scope['provider']
def sha(raw):return hashlib.sha256(raw).hexdigest()
def insertion(origin):
    clock="(()=>{const D=Date,t=D.parse("+json.dumps(STAMP)+"),s=D.now();window.Date=class extends D{constructor(...a){super(...(a.length?a:[t+D.now()-s]));}static now(){return t+D.now()-s;}};})();"
    fetch="(()=>{const f=window.fetch.bind(window),hosts=new Set(['api.aladhan.com','api.open-meteo.com','api.rainviewer.com','get.geojs.io','ipinfo.io']);window.fetch=(input,init)=>{const u=new URL(typeof input==='string'?input:input.url,location.href);return f(hosts.has(u.hostname)?"+json.dumps(origin)+"+'/fixture?url='+encodeURIComponent(u.href):input,init);};})();"
    return ('<script data-r0021-observer="parent-r125">'+clock+fetch+'</script>').encode()
def handler_class(base,build,report):
    class Handler(base):
        def log_message(self,*args):pass
        def do_GET(self):
            parts=urlsplit(self.path)
            try:
                if parts.path=='/fixture':
                    url=parse_qs(parts.query)['url'][0];value=provider(url);raw=json.dumps(value).encode();kind='application/json'
                    report.setdefault('providerResponses',[]).append({'url':url,'sha256':sha(raw),'body':value})
                elif parts.path in ['/'+build.name+'/', '/'+build.name+'/index.html']:
                    original=(build/'index.html').read_bytes();added=insertion('http://127.0.0.1:'+str(self.server.server_port));assert original.count(b'<head>')==1
                    raw=original.replace(b'<head>',b'<head>'+added,1);assert raw.replace(added,b'',1)==original;kind='text/html'
                    report['fixtureInsertion']={'applicationSha256':sha(original),'servedSha256':sha(raw),'insertedSha256':sha(added),'roundTrip':True,'stamp':STAMP,'scope':'Clock/provider transport only; original application bytes unchanged'}
                else:return super().do_GET()
                self.send_response(200);self.send_header('Content-Type',kind);self.send_header('Access-Control-Allow-Origin','*');self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(raw)
            except (BrokenPipeError,ConnectionResetError):pass
    return Handler
