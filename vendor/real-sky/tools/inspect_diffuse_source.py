#!/usr/bin/env python3
"""Inspect retained source bytes without promoting a catalogue to a diffuse survey.
Stdlib only. Does not download anything, infer licences, or produce production radiance.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,math,struct,zlib
from collections import Counter
from pathlib import Path
from build_authenticated_catalogue import source_bytes,authenticate,dump
ROOT=Path(__file__).resolve().parents[1]

def read_retained_catalogue(path:Path):
    raw=source_bytes(path); authentication=authenticate(raw)
    rows=list(csv.DictReader(io.StringIO(raw.decode('utf-8'))))
    if len(rows)!=119626:raise ValueError('Wrong retained source row count')
    seen=set()
    for r in rows:
        i=int(r['id'])
        if i in seen:raise ValueError('Duplicate HYG identity')
        seen.add(i)
        ra,dec,mag=float(r['ra']),float(r['dec']),float(r['mag'])
        if not all(math.isfinite(v) for v in [ra,dec,mag]):raise ValueError('Nonfinite source')
        if not(0<=ra<24 and -90<=dec<=90 and -30<=mag<=30):raise ValueError('Source coordinate/magnitude outside declared domain')
    return rows,authentication

def assert_survey_admitted(gate:dict):
    """Fail closed. Tests/builders may inspect a diagnostic while this gate remains shut."""
    if gate.get('productionSourceAdmitted') is not True or not isinstance(gate.get('admittedSurvey'),dict):
        raise ValueError('CP7_SURVEY_SOURCE_BLOCKED: no admitted optical diffuse survey')
    src=gate['admittedSurvey']
    for field in ['path','sha256','licence','frame','units','starTreatment']:
        if not isinstance(src.get(field),str) or not src[field].strip():raise ValueError('Incomplete survey admission: '+field)
    if len(src['sha256'])!=64 or any(c not in '0123456789abcdef' for c in src['sha256']):raise ValueError('Invalid survey hash')
    return src

def write_greyscale_png(path:Path,width:int,height:int,values:list[float]):
    """Source-count thumbnail, logarithmic stretch. This PNG is NOT an input map."""
    high=max(values,default=0)
    pixels=bytes(round(255*math.log1p(v)/math.log1p(high)) if high else 0 for v in values)
    raw=b''.join(b'\0'+pixels[y*width:(y+1)*width] for y in range(height))
    def chunk(name,b):return struct.pack('>I',len(b))+name+b+struct.pack('>I',zlib.crc32(name+b)&0xffffffff)
    path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',width,height,8,0,0,0,0))+chunk(b'IDAT',zlib.compress(raw,9))+chunk(b'IEND',b''))

def inspect(root:Path=ROOT):
    rows,auth=read_retained_catalogue(root/'upstream/hygdata_v40.csv.gz')
    gate=json.loads((root/'provenance/cp7/source-gate.json').read_text())
    cat=json.loads((root/'data/bright-stars.json').read_text())
    retained={int(s['hygId']):s for s in cat['stars']}
    if not set(retained).issubset({int(r['id']) for r in rows}):raise ValueError('Runtime not contained in retained source')
    w,h=128,64; counts=[0]*(w*h)
    for row in rows:
        if row['id']=='0':continue
        x=int(float(row['ra'])/24*w)%w;y=min(h-1,int((90-float(row['dec']))/180*h))
        counts[y*w+x]+=1
    report={'stage':'7.1','stageStatus':'PARTIAL','checkpoint7Status':'OPEN',
        'productionDiffuseSourceAdmitted':False,'surveyArraysAcquired':0,
        'retainedCatalogueAuthentication':auth,'retainedCatalogueRecords':len(rows),
        'solarRowExcluded':1,'retainedNonSolarRecords':len(rows)-1,
        'runtimeCatalogueRecords':len(retained),'runtimeEmittingRecords':sum(s['emission']['enabled'] for s in retained.values()),
        'runtimeWithheldRecords':sum(not s['emission']['enabled'] for s in retained.values()),
        'sourceOnlyRecords':len(rows)-1-len(retained),
        'magnitudeHistogram':dict(sorted(Counter(str(math.floor(float(r['mag']))) for r in rows if r['id']!='0').items(),key=lambda x:int(x[0]))),
        'preview':{'file':'retained-catalogue-counts.png','width':w,'height':h,'projection':'equirectangular, RA increases right, north up','quantity':'integer non-solar HYG row counts','stretch':'log1p(count), normalised to brightest count cell','notRadiance':True,'notDiffuseSurvey':True,'populatedCells':sum(v>0 for v in counts)},
        'candidateDispositions':{c['id']:c['status'] for c in gate['candidates']},
        'sourceGateTest':'EXPECTED_BLOCKED','newScienceInputAcquired':False}
    try:assert_survey_admitted(gate)
    except ValueError:pass
    else:raise ValueError('This partial diagnostic must not silently replace an admitted survey workflow')
    out=root/'checkpoints/cp7_1';out.mkdir(exist_ok=True,parents=True)
    dump(out/'source-inspection.json',report,True)
    write_greyscale_png(out/'retained-catalogue-counts.png',w,h,counts)
    return report
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=ROOT);a=p.parse_args()
    print(json.dumps(inspect(a.root),indent=2))
