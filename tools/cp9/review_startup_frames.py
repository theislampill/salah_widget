"""Pixel annotations for the fixed clear-night source-frame capture.
The thresholds are specific to this retained scene, never a universal sky gate.
Inspect emitted 1x frames and source-anchor crops before accepting annotations.
"""
import argparse,json,statistics
from pathlib import Path
from PIL import Image,ImageStat,ImageDraw
p=argparse.ArgumentParser();p.add_argument('directory',type=Path);a=p.parse_args();d=a.directory;r=json.loads((d/'results.json').read_text());out=d/'native-frame-review';out.mkdir(exist_ok=True)
report=[];selected=[]
for run in r['runs']:
 video=Path(run['video']);records=[json.loads(l) for l in Path(str(video)+'.frames.jsonl').read_text().splitlines()];start=run['navigationAbsolute'];end=start+run['elapsedMs'];rows=[]
 for rec in records:
  if not start<=rec['receiptUtcMs']<end:continue
  im=Image.open(Path(str(video)+'.frames')/rec['file']).convert('RGB')
  if im.width<390 or im.height<600:continue
  marker=None;v=im.getpixel((3,576))
  if v[0]>170 and v[2]>170 and v[1]<90:marker=sum((1<<i) if sum(im.getpixel((18+i*20,576)))>400 else 0 for i in range(16))
  if run['mode']=='warm-reload' and (marker is None or marker>rec['receiptUtcMs']-run['topTimeOrigin']+40):continue
  scene=60<min(im.getpixel((170,80)))<210 and max(im.getpixel((360,540)))<65
  m=ImageStat.Stat(im.crop((245,25,305,90)));moon=scene and sum(m.mean)/3>95 and sum(m.stddev)/3>8
  # HYG107315 at x90.8,y131.4 native -> x99,y139 iframe. Its local
  # peak above the surrounding background discriminates absent catalogue.
  values=[sum(im.getpixel((x,y)))/3 for x in range(97,102) for y in range(137,142)]
  back=[sum(im.getpixel((x,y)))/3 for x in range(92,107) for y in range(132,147) if x in [92,106] or y in [132,146]]
  contrast=max(values)-statistics.median(back);stars=scene and contrast>8
  row={**rec,'msUpper':rec['receiptUtcMs']-start,'markerMs':marker,'scene':scene,'moon':moon,'stars':stars,'anchorContrastCode':contrast};rows.append(row)
 for label,predicate in [('scene',lambda x:x['scene']),('moon',lambda x:x['moon']),('stars',lambda x:x['stars'])]:
  row=next((x for x in rows if predicate(x)),None)
  if row:
   im=Image.open(Path(str(video)+'.frames')/row['file']).convert('RGB');im.save(out/(run['mode']+'-'+label+'.png'))
   if label!='stars':selected.append((im,run['mode']+' '+label+' <= '+str(round(row['msUpper'],1))+'ms'))
 initial=(run['at15s'].get('moon') or {}).get('firstInitial')
 named={label:next((x for x in rows if x[label]),None) for label in ['scene','moon','stars']}
 report.append({'mode':run['mode'],'navigationAbsolute':start,'first':named,'acceptedMs':run['at15s']['timeOrigin']+initial['capturedAt']-start if initial else None,'publishedMs':run['at15s']['timeOrigin']+initial['publishedAt']-start if initial else None,'sourceFrames':len(rows),'receiptLagRangeMs':[min(x['receiptUtcMs']-1000*x['sourceTimeSeconds'] for x in rows),max(x['receiptUtcMs']-1000*x['sourceTimeSeconds'] for x in rows)]})
 (out/(run['mode']+'-frames.json')).write_text(json.dumps(rows,indent=2))
sheet=Image.new('RGB',(390*6,635),'#131b26');draw=ImageDraw.Draw(sheet)
for i,(im,label) in enumerate(selected):sheet.paste(im,(390*i,35));draw.text((390*i+3,5),label,fill='white')
sheet.save(out/'contact.png');(out/'timing.json').write_text(json.dumps(report,indent=2))
print(json.dumps([{'mode':x['mode'],'scene':x['first']['scene'] and x['first']['scene']['msUpper'],'moon':x['first']['moon'] and x['first']['moon']['msUpper'],'stars':x['first']['stars'] and x['first']['stars']['msUpper'],'accepted':x['acceptedMs'],'sourceFrames':x['sourceFrames']} for x in report],indent=2))
