"""Offline original-frame accounting using unchanged r52 clear-night ROI thresholds."""
from pathlib import Path
import hashlib,json,statistics
from PIL import Image,ImageStat
O=Path(__file__).resolve().parent
N=O/'native/first-boundary-r117'
out=N/'SUMMARY.json';assert not out.exists()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
result={'schema':'r0021-first-boundary-observations/v1','scope':__doc__,'status':'OBSERVATIONS_REQUIRING_INDEPENDENT_PIXEL_AND_CLOCK_REVIEW','executionSha256':sha(N/'EXECUTION.json'),'detectorOriginSha256':sha(O/'annotate_direct_source_r52.py'),'derivationSha256':sha(Path(__file__)),'arms':{},'limits':['Fixed clear-night390x600 detector only; threshold equality does not confer visual or timing qualification.','Each source interval remains unobserved; source timestamps and receipt bounds are not hardware presentation timestamps.','Earliest accepted clock is retained when present; no baseline clock is synthesized.','No source-gap bridge, repeated acquisition, callback-cost inference or blanket S1 claim.']}
for name in ['baseline','candidate']:
    folder=N/name;r=json.loads((folder/'results.json').read_bytes());run=r['runs'][0]
    v=Path(run['video']);side=Path(str(v)+'.frames.jsonl');frames=Path(str(v)+'.frames')
    nav=run['navigationAbsolute'];origin=run['at15s']['timeOrigin'];rows=[]
    for src in map(json.loads,side.read_text().splitlines()):
        p=frames/src['file'];raw=p.read_bytes();assert len(raw)==src['bytes']
        im=Image.open(p).convert('RGB');row={**src,'sha256':hashlib.sha256(raw).hexdigest(),'size':list(im.size),'receiptUpperFromNavigationMs':src['receiptUtcMs']+1-nav}
        if im.size!=(390,600):
            row['classification']='UNCLASSIFIABLE_DIMENSIONS'
        else:
            s=ImageStat.Stat(im.crop((237,17,297,82)))
            peak=max(sum(im.getpixel((x,y)))/3 for x in range(89,94) for y in range(129,134))
            back=statistics.median(sum(im.getpixel((x,y)))/3 for x in range(84,99) for y in range(124,139) if x in [84,98] or y in [124,138])
            row.update(classification='HEURISTIC_ONLY',moonMean=sum(s.mean)/3,moonStd=sum(s.stddev)/3,moon=sum(s.mean)/3>95 and sum(s.stddev)/3>8,anchorContrast=peak-back,stars=peak-back>8)
        rows.append(row)
    first=next((x for x in rows if x.get('moon') and x.get('stars')),None)
    idx=rows.index(first) if first else None;previous=rows[idx-1] if idx else None
    initial=run['at15s'].get('moon',{}).get('firstInitial')
    accepted=origin+initial.get('headCapturedAt',initial['capturedAt'])-nav if initial else None
    gaps=[{'from':a['seq'],'to':b['seq'],'sourceGapMs':(b['sourceTimeSeconds']-a['sourceTimeSeconds'])*1000,'status':'UNOBSERVED'} for a,b in zip(rows,rows[1:]) if (b['sourceTimeSeconds']-a['sourceTimeSeconds'])*1000>80]
    result['arms'][name]={'resultsSha256':sha(folder/'results.json'),'sidecarSha256':sha(side),'runtime':r['runtime']['treeSha256'],'navigationAbsolute':nav,'timeOrigin':origin,'earliestAcceptedFromNavigationMs':accepted,'firstCompleteHeuristic':first,'precedingSource':previous,'firstBoundarySourceIntervalMs':(first['sourceTimeSeconds']-previous['sourceTimeSeconds'])*1000 if previous else None,'receiptUpperAfterAcceptedMs':first['receiptUpperFromNavigationMs']-accepted if first and accepted is not None else None,'postFirstMissingHeuristic':[x['seq'] for x in rows[idx:] if not(x.get('moon') and x.get('stars'))] if idx is not None else None,'gapsOver80':gaps,'frameCount':len(rows),'sourceSpanMs':(rows[-1]['sourceTimeSeconds']-rows[0]['sourceTimeSeconds'])*1000,'rows':rows}
b=result['arms']['baseline'];c=result['arms']['candidate']
if b['precedingSource'] and c['firstCompleteHeuristic']:
    lower=b['precedingSource']['sourceTimeSeconds']*1000-b['navigationAbsolute']
    result['sourceClockDependentComparison']={'baselinePrecedingSourceLowerFromNavigationMs':lower,'candidateReceiptUpperFromNavigationMs':c['firstCompleteHeuristic']['receiptUpperFromNavigationMs'],'addedLatencyUpperMs':c['firstCompleteHeuristic']['receiptUpperFromNavigationMs']-lower,'allowanceMs':250,'requiresIndependentClockAndOriginalPixelReview':True}
out.write_bytes((json.dumps(result,indent=2)+'\n').encode())
print(json.dumps({'sha256':sha(out),'comparison':result.get('sourceClockDependentComparison'),'arms':{n:{k:v[k] for k in ['frameCount','firstBoundarySourceIntervalMs','receiptUpperAfterAcceptedMs','postFirstMissingHeuristic','gapsOver80']} for n,v in result['arms'].items()}}))
