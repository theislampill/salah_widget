"""Offline original-frame selection and state/mask diagnostics; never a pixel PASS."""
from pathlib import Path
from PIL import Image,ImageStat,ImageDraw
import base64,datetime,hashlib,io,json,re,sys
O=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
for name in sys.argv[1:]:
 root=O/'native'/name;out=O/'solar-analysis-r2'/name;out.mkdir(parents=True,exist_ok=False)
 raw=(root/'results.json').read_bytes();result=json.loads(raw);run=result['runs'][0];video=Path(run['video'])
 side=video.with_name(video.name+'.frames.jsonl');frames=video.with_name(video.name+'.frames')
 sunrise='sunrise' in name
 regions={'solar_core':(12,125,60,165) if sunrise else (12,55,60,90),'solar_edge':(110,125,140,170) if sunrise else (86,60,122,105),'sky_control':(252,65,300,105),'lower_control':(240,460,290,485),'exterior_control':(8,566,328,586)}
 rows=[];previous=None
 for record in map(json.loads,side.read_text().splitlines()):
  t=record['receiptUtcMs']-run['navigationAbsolute']
  if not 0<=t<=run['elapsedMs']:continue
  path=frames/record['file'];data=path.read_bytes();assert len(data)==record['bytes']
  im=Image.open(io.BytesIO(data)).convert('RGB');means={key:sum(ImageStat.Stat(im.crop(box)).mean)/3 for key,box in regions.items()}
  row={**record,'relativeReceiptMs':t,'path':path.relative_to(O).as_posix(),'sha256':sha(data),'dimensions':list(im.size),'meanCode':means,'sourceGapMs':None,'deltas':None}
  if previous:row.update(sourceGapMs=1000*(record['sourceTimeSeconds']-previous['sourceTimeSeconds']),deltas={key:means[key]-previous['meanCode'][key] for key in means})
  rows.append(row);previous=row
 (out/'frame-observations.jsonl').write_text(''.join(json.dumps(row)+'\n' for row in rows))
 phases={}
 selections={min(range(len(rows)),key=lambda i:abs(rows[i]['relativeReceiptMs']-t)) for t in [3000,5000,9000,12000,20000,30000,44000]}
 for label,lo,hi in [('ordinary',5000,30000),('diagnostic',31000,45000)]:
  candidates=[(i,r) for i,r in enumerate(rows) if lo<=r['relativeReceiptMs']<=hi and r['deltas']]
  ranked=sorted(candidates,key=lambda x:abs(x[1]['deltas']['solar_core']),reverse=True)[:6]
  for i,r in ranked:selections.update(j for j in [i-1,i,i+1] if 0<=j<len(rows))
  phases[label]={'frames':len(candidates),'range':[min(r['meanCode']['solar_core'] for i,r in candidates),max(r['meanCode']['solar_core'] for i,r in candidates)],'maxSourceGapMs':max(r['sourceGapMs'] for i,r in candidates),'maxAdjacentCoreChange':max(abs(r['deltas']['solar_core']) for i,r in candidates),'ranked':[r for i,r in ranked]}
 tracePath=root/'cold-solar-trace.json';trace=json.loads(tracePath.read_text());maskRows=[]
 for m in trace['masks']:
  match=re.search(r'data:image/png;base64,([^"\)]+)',m['value'])
  if not match:maskRows.append({'id':m['id'],'value':m['value']});continue
  data=base64.b64decode(match.group(1));im=Image.open(io.BytesIO(data)).convert('RGBA');alpha=im.getchannel('A').crop(regions['solar_core'])
  maskRows.append({'id':m['id'],'firstAt':m['firstAt'],'pngSha256':sha(data),'size':list(im.size),'solarAlphaMean':ImageStat.Stat(alpha).mean[0],'solarAlphaExtrema':alpha.getextrema()})
 (out/'mask-observations.json').write_text(json.dumps(maskRows,indent=2)+'\n')
 keys=['cardClass','bodyOpacity','bodyVisibility','bodyTransform','discOpacity','discVisibility','cornerOpacity','cornerTransform','maskVisibility']
 styles={k:sorted({r[k] for r in trace['frames']}) for k in keys}
 tiles=[]
 for i in sorted(selections):
  row=rows[i];im=Image.open(O/row['path']).convert('RGB');tile=Image.new('RGB',(195,264),'#eeeeee');tile.paste(im.crop((0,0,195,230)),(0,34));draw=ImageDraw.Draw(tile)
  draw.text((4,2),f"{row['seq']} receipt{row['relativeReceiptMs']/1000:.3f}s",fill='black');draw.text((4,17),f"core={row['meanCode']['solar_core']:.2f}",fill='black');tiles.append(tile)
 sheet=Image.new('RGB',(195*6,264*((len(tiles)+5)//6)),'white')
 for i,tile in enumerate(tiles):sheet.paste(tile,((i%6)*195,(i//6)*264))
 sheet.save(out/'selection.png')
 selected=[rows[i] for i in sorted(selections)]
 report={'schema':'r0021-solar-observation/v2','atUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'case':name,'runtime':result['runtime']['treeSha256'],'runtimeUnchanged':result['runtimeUnchanged'],'resultSha256':sha(raw),'traceSha256':sha(tracePath.read_bytes()),'sourceSidecarSha256':sha(side.read_bytes()),'stamp':result['stamp'],'syntheticWeather':result['syntheticWeather'],'regionsOriginalPixels':regions,'frameCount':len(rows),'durationMs':run['elapsedMs'],'sourceDimensions':sorted({tuple(r['dimensions']) for r in rows}),'physicalSolarAltitudeDeg':run['final']['sky']['displayed']['presentation']['solarAltitudeDeg'],'prayerReady':run['final']['native']['prayerReady'],'serverErrors':result['serverErrors'] if 'serverErrors' in result else result.get('errors'), 'skyFinal':{k:run['final']['sky'].get(k) for k in ['status','renders','presentationDraws','presentationSkips','presentationRejections','rejections','errors']},'phases':phases,'trace':{'samples':len(trace['frames']),'states':len(trace['states']),'styles':styles,'solarVectors':len(trace['values']),'masks':len(trace['masks'])},'maxSourceGaps':sorted([r for r in rows if r['sourceGapMs'] is not None],key=lambda r:r['sourceGapMs'],reverse=True)[:5],'selectedOriginals':selected,'status':'NUMERICAL_SELECTION_AND_STATE_ONLY_PIXEL_INSPECTION_REQUIRED','limitations':'Receipt-relative labels are not calibrated presentation times. Means select possible changes, not flicker absence. First30s ordinary capture; after30s state/CSS polling perturbs observer cost. Whole-frame corruptions, source gaps and the25fps resampled video remain separate from actual Sun-only content. No S1/cost/current-frame acceptance is manufactured.'}
 (out/'RESULT.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({'case':name,'resultSha256':sha((out/'RESULT.json').read_bytes()),'frames':len(rows),'solarAltitude':report['physicalSolarAltitudeDeg'],'prayerReady':report['prayerReady'],'phases':{k:{x:v[x] for x in ['frames','range','maxSourceGapMs','maxAdjacentCoreChange']} for k,v in phases.items()},'trace':report['trace']}))
