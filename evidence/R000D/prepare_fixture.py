"""Copy the prior issue-specific native fixture and pin the current unchanged source."""
import hashlib, json, re, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
OLD = Path(r'C:\Users\theis\Documents\Codex\salah-rlgwo-execution-20261009\workers\persistent-R000D-20261013\native-observation-correction-r1\package')
if (OUT/'package').exists():
    raise RuntimeError('Initial intake only: never overwrite an adapted or executed package')
def sha(b): return hashlib.sha256(b).hexdigest()
source = (ROOT/'index.html').read_bytes()
assert sha(source) == 'd4e3f084aea7d264a5c790268a21aa015b5e565e1feb9ad853d953c1c8a7b26f'
files = ['tools/qa/run_r000d_transport.py','tools/qa/run_weather_native.py','tools/qa/weather_native_http.py',
         'tests/weather-native/widget-fixture.html','tests/weather-native/actions.js','tests/weather-native/transport-bootstrap.js',
         'tests/weather-native/cases.json','tests/weather-forecast-fixture.js']
bindings = {}
for rel in files:
    target=OUT/'package'/rel
    target.parent.mkdir(parents=True, exist_ok=True)
    data=(OLD/rel).read_bytes()
    target.write_bytes(data)
    bindings[rel]={'origin':str(OLD/rel),'originalSha256':sha(data)}
scripts=list(re.finditer(r'<script\b([^>]*)>([\s\S]*?)</script>',source.decode(),re.I))
roles=[dict(ordinal=i,attributes=s[1].strip(),bodySha256=sha(s[2].encode()),bodyBytes=len(s[2].encode())) for i,s in enumerate(scripts)]
main=next(i for i,s in enumerate(scripts) if 'async function fetchTimings(' in s[2])
first=next(i for i,s in enumerate(scripts) if 'id="native-first-paint-code"' in s[1])
p=OUT/'package/tests/weather-native/widget-fixture.html'
s=p.read_text(encoding='utf-8')
s=s.replace('c773af444ed1071f9ba6b62b8e635c8d38b1b7f73de995c781ed23c0d307499a',sha(source))
s=s.replace('ff728552442f4bcce7f213a089bf01d4cf70ea8d74040bdd3323768ca453beee',sha(source))
s,n=re.subn(r'const CURRENT07_SCRIPT_ROLES=\[.*?\];','const CURRENT07_SCRIPT_ROLES='+json.dumps(roles,separators=(',',':'))+';',s)
assert n==1
s=s.replace('mainOrdinal:4,firstPaintSha256:CURRENT07_SCRIPT_ROLES[2]','mainOrdinal:'+str(main)+',firstPaintSha256:CURRENT07_SCRIPT_ROLES['+str(first)+']')
s=s.replace('Exact current07 source/script admission only','Exact 06772824 source/script admission only')
# The same three optional font link anchors remain; original CSP isolation is preserved.
p.write_text(s,encoding='utf-8',newline='\n')
# No Firefox recording system. Chromium uses the installed ordinary context recorder;
# Firefox uses original native PNG checkpoints and real 1x observer intervals.
p=OUT/'package/tools/qa/run_weather_native.py';s=p.read_text(encoding='utf-8')
s=s.replace("if out and spec.get('watchMotionSeconds') else {}", "if out and spec.get('watchMotionSeconds') and browser.browser_type.name=='chromium' else {}")
p.write_text(s,encoding='utf-8',newline='\n')
for rel in files: bindings[rel]['adaptedSha256']=sha((OUT/'package'/rel).read_bytes())
(OUT/'fixture-provenance.json').write_text(json.dumps(dict(sourceCommit='06772824a159cd2bc42a1d9f79a3fb22fa46e49d',sourceSha256=sha(source),scriptRoles=roles,mainOrdinal=main,files=bindings),indent=2)+'\n',encoding='utf-8')
print(json.dumps({'copied':len(files),'scripts':len(roles),'mainOrdinal':main,'index':sha(source)}))
