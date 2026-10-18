"""Safe complete callback interval projection; no browser requests or unrelated trace data."""
from pathlib import Path
import hashlib,json,re,zipfile
from native_profile_v5 import read_marks
O=Path(__file__).resolve().parents[1];R=Path(r'${REPO_ROOT}')
S=O/'cost/runs/chromium-native-v5-r76';D=R/'docs/real-sky/evidence/r0021-terminal-20261018/r110'
sha=lambda b:hashlib.sha256(b).hexdigest()
record=json.loads((S/'RESULTS.json').read_bytes());manifest={'scope':__doc__,'originalResultsSha256':sha((S/'RESULTS.json').read_bytes()),'slots':[],'removed':'All non-r21 trace events, browser/network/profile data and unused trace arguments. Relevant UserTiming timestamp/thread/document fields and every original CALLS record retained. Full local originals retain their published hashes.'}
with zipfile.ZipFile(D/'r76-native-intervals.zip','w',compression=zipfile.ZIP_DEFLATED,compresslevel=6)as z:
 for slot in record['slots']:
  raw=(S/slot['rawFile']).read_bytes();original=(S/slot['nativeProfileFile']).read_bytes()
  assert sha(raw)==slot['callsSha256']and sha(original)==slot['nativeProfileSha256']
  p=json.loads(original);events=[]
  for e in p['traceEvents']:
   if e.get('ph')=='M'and e.get('name')=='thread_name':
    events.append({k:e[k]for k in ['ph','name','pid','tid']}|{'args':{'name':e['args']['name']}})
   elif e.get('cat')=='blink.user_timing'and e['name'].startswith('r21:'):
    events.append({k:e[k]for k in ['cat','name','ph','ts','pid','tid']}|{'args':{'data':{'navigationId':e.get('args',{}).get('data',{}).get('navigationId')}}})
  projection={'traceEvents':events};assert read_marks(p,'chromium')==read_marks(projection,'chromium')
  body=json.dumps(projection,separators=(',',':')).encode()
  assert not re.search(rb'(?<![A-Za-z])[A-Za-z]:[\\/]',raw+body)
  base=slot['id']+'/';z.writestr(base+'CALLS.json',raw);z.writestr(base+'PROFILE.json',body)
  keys=['id','side','block','order','documentReadback','documentMarkerLabel','warmStart','warmEnd','start','end','overheadBefore','overheadAfter']
  meta={k:slot[k]for k in keys};meta.update(originalCallsSha256=sha(raw),originalProfileSha256=sha(original),projectedProfileSha256=sha(body),nativeMarkers=len(read_marks(projection,'chromium')))
  manifest['slots'].append(meta)
 z.writestr('SLOTS.json',json.dumps(manifest,indent=2)+'\n')
 z.writestr('ANALYSIS.json',(S/'ANALYSIS.json').read_bytes())
result={'schema':'r0021-safe-native-interval-publication/v1','archive':'r76-native-intervals.zip','sha256':sha((D/'r76-native-intervals.zip').read_bytes()),'bytes':(D/'r76-native-intervals.zip').stat().st_size,'slots':len(manifest['slots']),'markerProjectionVerifiedEqual':True,'sourceAnalysisSha256':sha((S/'ANALYSIS.json').read_bytes()),'sourceResultsSha256':manifest['originalResultsSha256'],'limits':manifest['removed']}
(D/'INTERVALS.json').write_bytes((json.dumps(result,indent=2)+'\n').encode());print(json.dumps(result))
