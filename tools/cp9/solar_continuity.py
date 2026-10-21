"""Bounded regression oracle for the fixed Orlando sunset solar-mask fixture.

The lower Sun ROI is below the native cloud support (y181). Adjacent source
frames must preserve the separate sky reference while the Sun alternates. This
is a source-frame defect detector, not whole-frame or presentation certification.
Keep originals: uniform or missing ROIs break, never bridge, a triplet. The
colour screen cannot detect every partial acquisition defect; inspect originals.
"""
import argparse, hashlib, json
from pathlib import Path

REGIONS = {'sun': (20, 185, 50, 215), 'reference': (260, 205, 285, 225)}

def fixture_errors(report):
    errors=[]
    expected={'scene':'day','dpr':1,'entry':'direct','viewport':{'width':390,'height':600}}
    for key,value in expected.items():
        if report.get(key)!=value:errors.append('Unsupported '+key)
    if report.get('stamp') not in ['2026-09-25T22:54:00Z','2026-09-25T22:54:15Z']:
        errors.append('Unsupported clock anchor')
    run=(report.get('runs') or [{}])[0]
    if not run.get('video'):errors.append('No original source recording')
    observed=run.get('at30s') or {}
    for name,expected in [('card',{'x':0,'y':0,'width':325,'height':530}),
                          ('native',{'lat':28.5383,'lon':-81.3792,'tz':'America/New_York','timeScale':1})]:
        for key,value in expected.items():
            if (observed.get(name) or {}).get(key)!=value:errors.append('Unsupported '+name+'.'+key)
    return errors

def readable_triplets(rows):
    for a,b,c in zip(rows, rows[1:], rows[2:]):
        if not all(r['roiReadable'] for r in (a,b,c)):continue
        if [b['seq']-a['seq'],c['seq']-b['seq']]!=[1,1]:continue
        if all(0 < right['at']-left['at'] <= .15 for left,right in [(a,b),(b,c)]):yield a,b,c

def result_for(rows,hits):
    if hits:return 'OBSERVED_SOLAR_ALTERNATION'
    return 'NO_ALTERNATION_OBSERVED' if next(readable_triplets(rows),None) else 'INSUFFICIENT_READABLE_TRIPLETS'

def distance(a, b):
    return sum(abs(x-y) for x, y in zip(a, b))/3

def alternations(rows):
    found=[]
    for a,b,c in readable_triplets(rows):
        if max(distance(a['reference'],b['reference']),distance(b['reference'],c['reference'])) > 8: continue
        if min(distance(a['sun'],b['sun']),distance(b['sun'],c['sun'])) > 40 and distance(a['sun'],c['sun']) < 5:
            found.append({'seq':[a['seq'],b['seq'],c['seq']], 'at':[a['at'],b['at'],c['at']],
                          'files':[r.get('file') for r in (a,b,c)], 'sun':[r['sun'] for r in (a,b,c)]})
    return found

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('case',type=Path);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--start',type=float,default=4);p.add_argument('--end',type=float,default=45)
    a=p.parse_args();assert not a.out.exists(),'Preserve prior evidence'
    from PIL import Image, ImageStat
    report=json.loads((a.case/'results.json').read_text(encoding='utf-8'))
    errors=fixture_errors(report)
    if errors:
        value={'result':'UNSUPPORTED_FIXTURE','case':str(a.case),'reasons':errors}
        a.out.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8');print(json.dumps(value));return 2
    # Firefox starts another acquisition on reload. Bind the ordinary run's
    # recorded video identity instead of selecting an unrelated reload stream.
    video=Path(report['runs'][0]['video']).name
    meta=a.case/'video'/(video+'.frames.jsonl');assert meta.is_file()
    frames=json.loads('['+','.join(meta.read_text(encoding='utf-8').splitlines())+']')
    folder=Path(str(meta)[:-6]);absolute=frames[0]['sourceTimeSeconds']>=1e9
    origin=report['runs'][0]['navigationAbsolute']/1000 if absolute else frames[0]['sourceTimeSeconds']
    rows=[]
    for f in frames:
        at=f['sourceTimeSeconds']-origin
        if not a.start<=at<=a.end:continue
        r={'seq':f['seq'],'at':at,'file':f['file'],'roiReadable':False}
        try:
            with Image.open(folder/f['file']) as image:
                image.load();image=image.convert('RGB')
                if image.size!=(390,600):raise ValueError('Source footprint differs from admitted fixture')
                r.update({k:ImageStat.Stat(image.crop(box)).mean for k,box in REGIONS.items()})
                # Fixture-specific colour screen, not an integrity classifier.
                # Partial blank bands can pass it even inside the selected ROIs.
                r['roiReadable']=max(r['reference'])-min(r['reference'])>5
        except Exception as e:r['error']=str(e)
        rows.append(r)
    hits=alternations(rows);unreadable=sum(not r['roiReadable'] for r in rows)
    value={'schema':'r0021-bounded-solar-source-regression/v1','case':str(a.case),'regions':REGIONS,
           'sourceMetadataSha256':hashlib.sha256(meta.read_bytes()).hexdigest(),
           'clock':'source elapsed; no navigation or presentation clock join' if not absolute else 'source UTC minus navigation UTC',
           'scope':'Original adjacent frames of the fixed real-1x sunset fixture; Sun motion over <=150ms negligible. Counts are colour-screen-admitted ROI samples/triplets, not certified readable frames. Manual original inspection remains required. No startup/performance/continuous-presentation PASS.',
           'result':result_for(rows,hits),'readableTriplets':sum(1 for _ in readable_triplets(rows)),
           'frames':len(rows),'unreadableRoiFrames':unreadable,'alternations':hits,'samples':rows}
    a.out.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({**{k:v for k,v in value.items() if k not in ['samples','alternations']},'alternationCount':len(hits)}))
    return 1 if hits else 0 if value['result']=='NO_ALTERNATION_OBSERVED' else 2

if __name__=='__main__':raise SystemExit(main())
