"""Read only the missing four-phase reference dependency from V5 Part 01."""
from pathlib import Path
from html.parser import HTMLParser
import zipfile,json,hashlib,base64
P=Path(r'C:\Users\theis\Downloads\Salah_Lunar_V5_Part01_Core.zip')
O=Path(__file__).resolve().parent/'v5-phase-references';O.mkdir(exist_ok=True)
PREFIX='Salah_Lunar_Terminator_V5/'
selected=['wax_012','wax_050','wax_075','wax_099'];reads=[]
class Images(HTMLParser):
 def __init__(self):super().__init__();self.images={}
 def handle_starttag(self,tag,attrs):
  d=dict(attrs)
  if tag=='img' and d.get('alt') in selected:self.images[d['alt']]=d['src']
with zipfile.ZipFile(P) as z:
 manifest_bytes=z.read(PREFIX+'MANIFEST.json');reads.append('MANIFEST.json')
 manifest={v['path']:v for v in json.loads(manifest_bytes)['files']}
 def read(n):
  b=z.read(PREFIX+n);v=manifest[n];assert len(b)==v['bytes'] and hashlib.sha256(b).hexdigest()==v['sha256'];reads.append(n);return b
 gallery=read('GALLERY.html');parser=Images();parser.feed(gallery.decode())
 campaign_bytes=read('evidence/v5/FINAL_CAMPAIGN.json');campaign=json.loads(campaign_bytes)
 chosen=[]
 for name in selected:
  b=base64.b64decode(parser.images[name].split(',',1)[1],validate=True);sha=hashlib.sha256(b).hexdigest()
  matches=[n for n,v in manifest.items() if v['sha256']==sha and n.startswith('outputs/'+name+'_q4096/v5/')]
  assert len(matches)==1,(name,matches)
  (O/(name+'-reference.png')).write_bytes(b)
  scene=next(s for s in campaign['scenes'] if s['name']==name)
  chosen.append(dict(name=name,originalPath=matches[0],sha256=sha,bytes=len(b),selectedCampaign=scene))
 report=dict(scope='Specific missing phase-reference dependency requested during receiving visual review. Only Part01 metadata/gallery consulted and four selected reference images extracted. Individual scene payloads are not in Part01; their selected campaign records provide phase/profile/sampling provenance. No other V5 ZIP opened and no research or terrain campaign rerun.',archive=P.name,archiveBytes=P.stat().st_size,archiveSha256=hashlib.sha256(P.read_bytes()).hexdigest(),manifestSha256=hashlib.sha256(manifest_bytes).hexdigest(),gallerySha256=hashlib.sha256(gallery).hexdigest(),membersRead=reads,additionalInspectedMembers=['REPORT.md','SOURCE_IDENTITY.json','evidence/v5/campaign_N540_q4096.json','tools/campaign_v5.py'],profileIdentity=campaign['profile_identity'],selected=chosen)
 (O/'reference-custody.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'selected':[(s['name'],s['originalPath']) for s in chosen],'membersRead':len(reads),'archiveBytes':P.stat().st_size},indent=2))
