"""Fixed r52 ROI thresholds, geometry-mapped locators only; whole-card review remains mandatory."""
from pathlib import Path
import hashlib,json,math,statistics
from PIL import Image,ImageStat,ImageDraw
O=Path(__file__).resolve().parent;N=O/'native/absolute-timing-r120'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
result={'schema':'r0021-absolute-timing-observations/v1','executionSha256':sha(N/'EXECUTION.json'),
 'detectorOriginSha256':sha(O/'annotate_direct_source_r52.py'),'derivationSha256':sha(Path(__file__)),
 'status':'HEURISTIC_LOCATORS_REQUIRE_INDEPENDENT_ORIGINAL_PIXEL_AND_CLOCK_REVIEW',
 'limits':['The r52 mean/std/star thresholds are unchanged, with explicit iframe8px translation and recorded image/viewport scaling. This geometry extension is not a new calibrated detector or automatic PASS.',
 'Every original is preserved. No source interval is interpolated; source time and receipt are not hardware presentation timestamps.',
 'First positive from an old document is not counted. Candidate needs an observed preceding negative after navigation and receipt after original accepted capture. Both identities and full scene still require review.',
 'The observer captures the first15s only, does not wait for final refinement, and does not certify late handoff or whole continuous presentation.'], 'cells':[]}
for folder in sorted(p for p in N.iterdir() if p.is_dir() and (p/'results.json').exists()):
 report=json.loads((folder/'results.json').read_bytes());sheet=Image.new('RGB',(1044,1770),'#ddd');draw=ImageDraw.Draw(sheet)
 for ri,run in enumerate(report['runs']):
  video=Path(run['video']);side=Path(str(video)+'.frames.jsonl');frames=Path(str(video)+'.frames');raw=[json.loads(x) for x in side.read_text().splitlines()]
  nav=run['navigationAbsolute'];nextnav=next((r['navigationAbsolute'] for r in report['runs'] if r['navigationAbsolute']>nav),float('inf'))
  part=[r for r in raw if nav<=r['receiptUtcMs']<nextnav]
  initial=run['at15s'].get('moon',{}).get('firstInitial');origin=run['at15s']['timeOrigin']
  accepted=origin+initial.get('headCapturedAt',initial['capturedAt']) if initial else None
  offset=8 if report['entry']=='iframe' else 0;vw=report['viewport']['width'];vh=report['viewport']['height'];rows=[]
  for src in part:
   if src['receiptUtcMs']-nav>2200:break
   p=frames/src['file'];im=Image.open(p).convert('RGB');sx=im.width/vw;sy=im.height/vh
   xy=lambda x,y:(round((x+offset)*sx),round((y+offset)*sy))
   stat=ImageStat.Stat(im.crop((*xy(237,17),*xy(297,82))))
   peak=max(sum(im.getpixel(xy(x,y)))/3 for x in range(89,94) for y in range(129,134))
   back=statistics.median(sum(im.getpixel(xy(x,y)))/3 for x in range(84,99) for y in range(124,139) if x in [84,98] or y in [124,138])
   mean=sum(stat.mean)/3;std=sum(stat.stddev)/3
   rows.append({**src,'sha256':sha(p),'size':[im.width,im.height],'scale':[sx,sy],'iframeOffsetCssPx':offset,
    'moonMean':mean,'moonStd':std,'moon':mean>95 and std>8,'anchorContrast':peak-back,'stars':peak-back>8,
    'receiptUpperFromNavigationMs':src['receiptUtcMs']+1-nav})
  candidate=None;negative=None
  for row in rows:
   if not(row['moon'] and row['stars']):negative=row
   elif negative is not None and accepted is not None and row['receiptUtcMs']>=accepted:
    candidate=row;break
  engine=folder.name.split('-')[0];budgets={'navigationMs':1000 if engine=='chromium' else 1500,'originalAcceptedMs':250 if engine=='chromium' else 400}
  cell={'family':folder.name,'mode':run['mode'],'engine':engine,'runtime':report['runtime']['treeSha256'],
   'resultsSha256':sha(folder/'results.json'),'sidecar':str(side),'sidecarSha256':sha(side),'navigationAbsolute':nav,'timeOrigin':origin,
   'firstInitial':initial,'originalAcceptedAbsolute':accepted,'originalAcceptedFromNavigationMs':accepted-nav if accepted else None,
   'observedPrecedingNegative':negative,'firstCompleteLocator':candidate,'budgets':budgets,
   'receiptUpperAfterOriginalAcceptedMs':candidate['receiptUpperFromNavigationMs']-(accepted-nav) if candidate else None,
   'sourceFrames':len(part),'allGapsOver80ms':[{'from':a['seq'],'to':b['seq'],'ms':(b['sourceTimeSeconds']-a['sourceTimeSeconds'])*1000,'status':'UNOBSERVED'} for a,b in zip(part,part[1:]) if (b['sourceTimeSeconds']-a['sourceTimeSeconds'])*1000>80],
   'firstSecondsRows':rows,'status':'REQUIRES_ORIGINAL_PIXEL_AND_CLOCK_REVIEW'}
  cell['upperBoundsWithinBudget']=bool(candidate and candidate['receiptUpperFromNavigationMs']<=budgets['navigationMs'] and cell['receiptUpperAfterOriginalAcceptedMs']<=budgets['originalAcceptedMs'])
  picks=[negative,candidate,next((x for x in rows if x['receiptUpperFromNavigationMs']>1200),rows[-1] if rows else None)]
  for col,(label,row) in enumerate(zip(['preceding negative','first complete locator','later control'],picks)):
   x=col*348;y=ri*590
   if row:
    im=Image.open(frames/row['file']).convert('RGB');sx=im.width/vw;sy=im.height/vh
    crop=im.crop((0,0,round((338+offset)*sx),round((544+offset)*sy)));crop.thumbnail((348,552));sheet.paste(crop,(x,y+38))
    draw.text((x+3,y+3),f'{run["mode"]} {label} #{row["seq"]}',fill='black');draw.text((x+3,y+18),f'receipt <= {row["receiptUpperFromNavigationMs"]:.2f}ms',fill='black')
  result['cells'].append(cell)
 sheet.save(N/(folder.name+'-boundary-contact.png'))
 print(json.dumps({'family':folder.name,'cells':[{'mode':c['mode'],'candidateSeq':(c['firstCompleteLocator'] or {}).get('seq'),'navMs':(c['firstCompleteLocator'] or {}).get('receiptUpperFromNavigationMs'),'acceptedMs':c['receiptUpperAfterOriginalAcceptedMs'],'within':c['upperBoundsWithinBudget']} for c in result['cells'] if c['family']==folder.name]}),flush=True)
p=N/'SUMMARY.json';assert not p.exists();p.write_bytes((json.dumps(result,indent=2)+'\n').encode())
print(json.dumps({'sha256':sha(p),'candidateUpperBoundsWithin':sum(c['upperBoundsWithinBudget'] for c in result['cells']),'cells':len(result['cells'])}))
