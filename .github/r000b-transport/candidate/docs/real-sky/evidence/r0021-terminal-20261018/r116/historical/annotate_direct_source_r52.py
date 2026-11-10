"""Read original direct clear-night frames; dimension mismatches remain unclassifiable, never repaired or dropped."""
from pathlib import Path
import hashlib,json,statistics,sys
from PIL import Image,ImageStat
O=Path(__file__).resolve().parent;d=O/'native'/sys.argv[1];out=d/'source-annotations-r52.json';assert not out.exists()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((d/'results.json').read_bytes());assert r['entry']=='direct' and r['scene']=='clear'
report={'scope':__doc__,'notQualification':'Heuristics, source timestamps and receipt bounds do not certify presentation or unobserved intervals.','scriptSha256':sha(Path(__file__)),'resultsSha256':sha(d/'results.json'),'browser':r['browser'],'runs':[]}
for run in r['runs']:
 v=Path(run['video']);meta=Path(str(v)+'.frames.jsonl');rows=[];nav=run['navigationAbsolute'];origin=run['at15s']['timeOrigin']
 for row in map(json.loads,meta.read_text().splitlines()):
  t=row['receiptUtcMs']+1-nav
  if not 0<=t<=3000:continue
  path=Path(str(v)+'.frames')/row['file'];im=Image.open(path).convert('RGB')
  item={**row,'sha256':sha(path),'size':list(im.size),'receiptUpperFromNavigationMs':t}
  if im.size!=(390,600):
   rows.append({**item,'classification':'UNCLASSIFIABLE_DIMENSIONS'});continue
  s=ImageStat.Stat(im.crop((237,17,297,82)));rgb=im.getpixel((3,576));marker=None
  if rgb[0]>170 and rgb[2]>170 and rgb[1]<90:marker=sum((1<<i)if sum(im.getpixel((18+i*20,576)))>400 else 0 for i in range(16))
  current=run['mode']!='warm-reload' or marker is not None and marker<row['receiptUtcMs']-origin+40
  peak=max(sum(im.getpixel((x,y)))/3 for x in range(89,94)for y in range(129,134))
  back=statistics.median(sum(im.getpixel((x,y)))/3 for x in range(84,99)for y in range(124,139)if x in[84,98]or y in[124,138])
  rows.append({**item,'classification':'HEURISTIC_ONLY','externalRafMarker':marker,'newDocumentHeuristic':current,'moonMean':sum(s.mean)/3,'moonStd':sum(s.stddev)/3,'moon':sum(s.mean)/3>95 and sum(s.stddev)/3>8,'anchorContrast':peak-back,'stars':peak-back>8})
 first=next((x for x in rows if x.get('newDocumentHeuristic')and x.get('moon')and x.get('stars')),None)
 initial=run['at15s']['moon']['firstInitial'];accepted=origin+initial.get('headCapturedAt',initial['capturedAt'])-nav
 gaps=[{'from':a['file'],'to':b['file'],'sourceGapMs':(b['sourceTimeSeconds']-a['sourceTimeSeconds'])*1000}for a,b in zip(rows,rows[1:])if(b['sourceTimeSeconds']-a['sourceTimeSeconds'])*1000>80]
 rec={'mode':run['mode'],'video':str(v),'metadataSha256':sha(meta),'firstCompleteHeuristic':first,'earliestAcceptedFromNavigationMs':accepted,'gapsOver80':gaps,'rows':rows}
 report['runs'].append(rec)
 print(json.dumps({'mode':run['mode'],'firstCompleteHeuristic':first['file']if first else None,'receiptUpperFromNavigationMs':first['receiptUpperFromNavigationMs']if first else None,'receiptUpperAfterAcceptedMs':first['receiptUpperFromNavigationMs']-accepted if first else None,'gapsOver80':gaps,'unclassifiable':[x['file']for x in rows if x['classification']!='HEURISTIC_ONLY']}))
out.write_text(json.dumps(report,indent=2)+'\n')
