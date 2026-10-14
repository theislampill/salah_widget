"""Fixed clear-night pixel annotations with first-admission monotonic bindings.

Existing RGB/crop/anchor thresholds remain scene-specific. Retain and inspect
the emitted 1x frames/crops. This annotator grants no visual or S1 PASS.
Legacy captures stay diagnosable and UNKNOWN under the new timing contract.
"""
import argparse
import hashlib
import io
import json
import re
import statistics
from pathlib import Path
from startup_timing import clock_bounds, normalize_startup_timing, InvalidTiming, MissingTiming, ReviewArtifactSnapshot
from startup_baseline_bounds import validate_baseline_capture, baseline_clock_bounds, baseline_frame_custody


def identity_marker(image):
    prefix=image.getpixel((361,4))
    if not (prefix[0]>170 and prefix[2]>170 and prefix[1]<90):return None
    words=[]
    for row in range(4):
        word=0
        for bit in range(32):
            index=row*32+bit
            value=image.getpixel((370+(index%2)*13,4+(index//2)*8))
            # Ambiguous JPEG/bar samples are UNKNOWN, not guessed identities.
            total=sum(value)
            if 180<=total<=570:return None
            if total>570:word|=1<<bit
        words.append(format(word,'08x'))
    return ''.join(words)


def elapsed_marker(image):
    value=image.getpixel((3,576))
    if not (value[0]>170 and value[2]>170 and value[1]<90):return None
    return sum((1<<i) if sum(image.getpixel((18+i*20,576)))>400 else 0 for i in range(16))


def pixel_observation(row, first):
    if row.get('identityMarker')!=first['markerToken'] or row.get('msBounds') is None:return None
    source={'kind':'native-source-receipt','eventId':row['sourceEventId'],
        'clockId':row['receiptClock']['id'],'atMs':row['receiptMonotonicMs'],
        'rawProtocolTimeSeconds':row['sourceTimeSeconds'],'artifact':row['pixelArtifact'],
        'receiptArtifact':row['receiptArtifact']}
    presented={'kind':'presented-pixels-receipt-upper-bound','eventId':row['presentedReceiptEventId'],
        'sourceEventId':row['sourceEventId'],'clockId':row['receiptClock']['id'],
        'atMs':row['receiptMonotonicMs'],'artifact':row['pixelArtifact'],
        'receiptArtifact':row['receiptArtifact']}
    return {'admissionId':first['admissionId'],'binding':first['binding'],
        'documentId':first['documentId'],'markerToken':row['identityMarker'],
        'sourceReceipt':source,'presentedReceipt':presented}


def review(directory, output, baseline=False):
    output=Path(output);staging=output.with_name(output.name+'.staging')
    if output.exists() or staging.exists():
        raise ValueError('Require fresh output and staging; preserve previous/raw receipts')
    if output.resolve().parent!=staging.resolve().parent:
        raise ValueError('Output staging must share the resolved parent')
    with ReviewArtifactSnapshot() as snapshot:
        summaries=_review(directory,staging,baseline,snapshot)
    # The raw-byte and parsed-snapshot guards have passed before admission.
    staging.replace(output)
    return summaries


def _review(directory, output, baseline, snapshot):
    from PIL import Image,ImageStat,ImageDraw
    directory=Path(directory);output=Path(output)
    if output.exists():raise ValueError('Require a fresh output; preserve previous/raw receipts')
    results_file=directory/'results.json';raw_results=snapshot.read_bytes(results_file);results=json.loads(raw_results)
    if baseline:validate_baseline_capture(results)
    bound_callback=baseline_clock_bounds if baseline else clock_bounds
    output.mkdir(parents=True,exist_ok=False)
    report=[];selected=[]
    for run in results['runs']:
        mode=run['mode']
        if mode not in ['cold','warm-reload','new-tab']:raise ValueError('Unknown capture mode')
        video=Path(run['video']);record_file=Path(str(video)+'.frames.jsonl');raw_records=snapshot.read_bytes(record_file)
        receipt_artifact={'file':str(record_file),'sha256':hashlib.sha256(raw_records).hexdigest()}
        records=[json.loads(line) for line in raw_records.splitlines()]
        start=run['navigationAbsolute'];end=start+run['elapsedMs'];rows=[]
        capture=run.get('captureTiming')
        first=(capture or {}).get('observer',{}).get('firstValidAdmission') if (capture or {}).get('observer') else None
        comparison=None
        if capture:
            comparison={'schema':'salah-startup-comparison/1',
                'captureClock':capture.get('captureClock'),'navigation':capture.get('navigation'),
                'bridges':capture.get('bridges',[]),'observer':capture.get('observer'),
                'observerArtifact':{'file':str(results_file),'sha256':hashlib.sha256(raw_results).hexdigest()},
                'observations':{}}
        for record in records:
            if not re.fullmatch('[0-9]{6}\.jpeg',record['file']):raise ValueError('Invalid native source-frame name')
            bounds=None;failure=None
            if comparison and isinstance(record.get('receiptClock'),dict):
                try:
                    if record['receiptClock'].get('kind')!='node-hrtime' or record['receiptClock'].get('unit')!='ms':
                        raise InvalidTiming('wrong native receipt domain')
                    event={'clockId':record['receiptClock']['id'],'atMs':record['receiptMonotonicMs']}
                    common=bound_callback(event,comparison,'node-hrtime');nav=comparison['navigation']['atMs']
                    bounds=[x-nav for x in common]
                    if bounds[1]<0 or bounds[0]>=run['elapsedMs']:continue
                except (InvalidTiming,MissingTiming,KeyError,TypeError) as exc:failure=str(exc)
            else:
                failure='legacy native receipt lacks a comparable monotonic binding'
            if bounds is None and not start<=record['receiptUtcMs']<end:continue
            image_file=Path(str(video)+'.frames')/record['file'];raw_pixel=snapshot.read_bytes(image_file)
            image=Image.open(io.BytesIO(raw_pixel)).convert('RGB')
            if image.width<390 or image.height<600:continue
            marker=elapsed_marker(image);identity=identity_marker(image)
            if baseline and bounds is not None:
                baseline_frame_custody(record,{'file':str(image_file),'sha256':hashlib.sha256(raw_pixel).hexdigest()},receipt_artifact,comparison)
            if mode=='warm-reload':
                if comparison:
                    if bounds is None or not capture.get('topClockId'):
                        failure='warm reload lacks comparable top-document marker clock';bounds=None
                    else:
                        try:
                            top_zero=bound_callback({'clockId':capture['topClockId'],'atMs':0},comparison,'window-performance')
                            current_upper=bounds[1]+comparison['navigation']['atMs']-top_zero[0]
                            if marker is None or marker>current_upper+40:continue
                        except (InvalidTiming,MissingTiming) as exc:failure=str(exc);bounds=None
                elif marker is None or marker>record['receiptUtcMs']-run['topTimeOrigin']+40:continue
            scene=60<min(image.getpixel((170,80)))<210 and max(image.getpixel((360,540)))<65
            moon_stats=ImageStat.Stat(image.crop((245,25,305,90)))
            moon=scene and sum(moon_stats.mean)/3>95 and sum(moon_stats.stddev)/3>8
            values=[sum(image.getpixel((x,y)))/3 for x in range(97,102) for y in range(137,142)]
            back=[sum(image.getpixel((x,y)))/3 for x in range(92,107) for y in range(132,147) if x in [92,106] or y in [132,146]]
            contrast=max(values)-statistics.median(back);stars=scene and contrast>8
            rows.append({**record,'msBounds':bounds,'msUpperLegacy':record['receiptUtcMs']-start,
                'timingUnknown':failure,'markerMs':marker,'identityMarker':identity,
                'pixelArtifact':{'file':str(image_file),'sha256':hashlib.sha256(raw_pixel).hexdigest()},
                'receiptArtifact':receipt_artifact,'scene':scene,'moon':moon,'stars':stars,'anchorContrastCode':contrast})
        eligible=[row for row in rows if first and row['identityMarker']==first.get('markerToken') and row['msBounds'] is not None]
        named={name:next((row for row in eligible if row[name]),None) for name in ['scene','moon','stars']}
        legacy_named={name:next((row for row in rows if row[name]),None) for name in ['scene','moon','stars']}
        if comparison and first:
            comparison['observations']={name:pixel_observation(row,first) for name,row in named.items() if row}
        normalized=normalize_startup_timing(comparison,['scene','moon','stars'])
        initial=(run['at15s'].get('moon') or {}).get('firstInitial')
        legacy={'source':'at15s.moon.firstInitial; diagnostic only','raw':initial,
            'acceptedMs':run['at15s']['timeOrigin']+initial['capturedAt']-start if initial else None,
            'publishedMs':run['at15s']['timeOrigin']+initial['publishedAt']-start if initial else None}
        report.append({'mode':mode,'navigationAbsoluteDiagnostic':start,'first':named,
            'legacyFirst':legacy_named,'legacyEndpoints':legacy,'timing':normalized,
            'timingComparison':comparison,'sourceFrames':len(rows),'identityMatchedFrames':len(eligible),
            'scope':'Pixel receipt upper bounds; visual/coverage qualification remains separate'})
        if baseline:
            baseline_scene=next((row for row in rows if row['scene'] and row['msBounds'] is not None),None)
            report[-1]['baselineScene']=baseline_scene
            report[-1]['baselineScope']='Exact original-main scene callback interval only; no first-admission/F2 credit; visual and coverage admission remain external'
            if baseline_scene:
                Image.open(io.BytesIO(snapshot.read_bytes(baseline_scene['pixelArtifact']['file']))).convert('RGB').save(output/(mode+'-baseline-scene.png'))
        for name,row in named.items():
            if row:
                image=Image.open(io.BytesIO(snapshot.read_bytes(row['pixelArtifact']['file']))).convert('RGB');image.save(output/(mode+'-'+name+'.png'))
                if name!='stars':selected.append((image,mode+' '+name+' <= '+str(round(row['msBounds'][1],1))+'ms'))
        (output/(mode+'-frames.json')).write_text(json.dumps(rows,indent=2)+'\n')
    sheet=Image.new('RGB',(390*6,635),'#131b26');draw=ImageDraw.Draw(sheet)
    for i,(image,label) in enumerate(selected):sheet.paste(image,(390*i,35));draw.text((390*i+3,5),label,fill='white')
    sheet.save(output/'contact.png');(output/'timing.json').write_text(json.dumps(report,indent=2)+'\n')
    return [{'mode':row['mode'],'timingStatus':row['timing']['status'],
        'firstAdmissionBoundsMs':row['timing'].get('firstAdmissionBoundsMs'),
        'sourceFrames':row['sourceFrames'],'identityMatchedFrames':row['identityMatchedFrames']} for row in report]


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('directory',type=Path);parser.add_argument('--out',type=Path)
    parser.add_argument('--baseline-original-main',action='store_true',help='Restricted original-main scene comparator; never candidate F2 attribution')
    args=parser.parse_args()
    print(json.dumps(review(args.directory,args.out or args.directory/'native-frame-review-f2',baseline=args.baseline_original_main),indent=2))
