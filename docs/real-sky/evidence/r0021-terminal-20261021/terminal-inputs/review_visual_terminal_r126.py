"""Offline locators only: original source frames remain the evidence; no detector or PASS."""
from pathlib import Path
import hashlib,json,statistics
from PIL import Image,ImageDraw
O=Path(__file__).resolve().parent
B=O/'native/visual-parent-r125-r126/chromium-twilight'
OUT=O/'native/visual-parent-r125-r126/offline-review'
OUT.mkdir(exist_ok=True)
d=json.loads((B/'results.json').read_bytes());r=d['runs'][0];f=r['final']
sidecar=next((B/'video').glob('*.frames.jsonl'))
rows=[json.loads(s) for s in sidecar.read_text().splitlines()]
origin=r['topTimeOrigin'];folder=Path(str(sidecar)[:-6])
gaps=[(b['sourceTimeSeconds']-a['sourceTimeSeconds'])*1000 for a,b in zip(rows,rows[1:])]
targets=[220,300,500,650,1000,2000,3000,5000,7000,10000,13000,13700,13800,13850,14000,15000]
chosen=[]
sheet=Image.new('RGB',(390*4,625*4),'#eeeeee');draw=ImageDraw.Draw(sheet)
for i,target in enumerate(targets):
 row=min(rows,key=lambda a:abs(a['sourceTimeSeconds']*1000-origin-target))
 p=folder/row['file'];im=Image.open(p).convert('RGB')
 x=(i%4)*390;y=(i//4)*625;sheet.paste(im,(x,y+25))
 at=row['sourceTimeSeconds']*1000-origin
 draw.text((x+4,y+4),f"{row['file']} source+{at:.2f}ms",fill='black')
 chosen.append({'targetMs':target,'row':row,'sourceAfterOriginMs':at,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'width':im.width,'height':im.height})
sheet.save(OUT/'chromium-twilight-locator.png')
def scalar(v):return {k:x for k,x in (v or {}).items() if not isinstance(x,(dict,list))}
summary={'schema':'r0021-offline-frame-locators/v1','claim':'Locators and state only; no continuous or physical-display qualification. Contact sheet is derived; original JPEGs and gaps control.',
 'sourceResultsSha256':hashlib.sha256((B/'results.json').read_bytes()).hexdigest(),'sidecarSha256':hashlib.sha256(sidecar.read_bytes()).hexdigest(),
 'rows':len(rows),'firstSourceAfterOriginMs':rows[0]['sourceTimeSeconds']*1000-origin,'lastSourceAfterOriginMs':rows[-1]['sourceTimeSeconds']*1000-origin,
 'maxGapMs':max(gaps),'gapsOver80ms':[{'before':a['file'],'after':b['file'],'gapMs':gap,'disposition':'UNOBSERVED'} for a,b,gap in zip(rows,rows[1:],gaps) if gap>80],
 'selected':chosen,'final':{'at':f['at'],'moon':scalar(f['moon']),'quality':f['moon']['last']['quality'],'lastAdoption':f['moon']['lastAdoption'],'sky':scalar(f['sky']),
 'preview':scalar(f['preview']),'moonTruth':scalar(f['qa']['moonTruth']),'native':scalar(f['native'])}}
(OUT/'chromium-twilight-locators.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:summary[k] for k in ['rows','firstSourceAfterOriginMs','lastSourceAfterOriginMs','maxGapMs','gapsOver80ms']}))
