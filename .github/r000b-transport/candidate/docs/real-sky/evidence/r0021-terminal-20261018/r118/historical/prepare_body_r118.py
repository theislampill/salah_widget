"""One fixture-only change: close an actual successful DEM response mid-body."""
from pathlib import Path
import ast,hashlib,json
O=Path(__file__).resolve().parent
R=Path(r'${REPO_ROOT}')
H=O/'body-tools-r118';assert not H.exists()
prior=json.loads((O/'native/chromium-arc-samples-r105/EXECUTION.json').read_bytes())['harnessInputSha256']
old="    elif self.path=='/favicon.ico':self.send(b'',status=204)\n"
new=old+'''    elif os.environ.get('SALAH_R118_BODY_INTERRUPT')=='1' and not server_recovered and urlsplit(self.path).path=='/salah_widget/moon/assets/dem.bin.gz':
     # Real HTTP200/full declared length, then TCP EOF after the first4096 bytes.
     # The unchanged worker fetch/body reader must discover the truncation.
     target=a.root/'moon/assets/dem.bin.gz';length=target.stat().st_size
     with target.open('rb') as f:prefix=f.read(4096)
     self.send_response(200);self.send_header('Content-Type','application/octet-stream');self.send_header('Content-Length',str(length));self.end_headers()
     self.wfile.write(prefix);self.wfile.flush()
     requests.append({'kind':'controlled-response-body-interruption','url':self.path,'httpStatus':200,'declaredBytes':length,'sentBytes':len(prefix),'absolute':time.time()*1000})
     self.close_connection=True;self.connection.shutdown(1)
'''
entries={}
for rel,pin in prior.items():
    data=(R/rel).read_bytes();assert hashlib.sha256(data).hexdigest()==pin
    if rel=='tools/cp9/celestial_startup_check.py':
        source=data.decode();assert source.count(old)==1
        data=source.replace(old,new).encode();ast.parse(data)
    target=H/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    entries[rel]={'beforeSha256':pin,'afterSha256':hashlib.sha256(data).hexdigest()}
record={'schema':'r0021-s5-body-fixture/v1','purpose':__doc__,'changes':entries,'productRuntimeUnchanged':True,'kind':'test fixture only; no timing or decoder claim','intervention':'HTTP200 correct full Content-Length then EOF after4096bytes until existing --recover-at event; original bytes served on retry','stop':'One Chromium and one Firefox clear/direct/DPR1 functional case; stop at admitted final or120s; no repeat; not a startup timing or submillisecond comparison'}
(O/'intake/body-r118-preparation.json').write_bytes((json.dumps(record,indent=2)+'\n').encode())
print(json.dumps(record))
