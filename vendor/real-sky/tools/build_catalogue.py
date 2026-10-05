#!/usr/bin/env python3
"""Deterministically normalise the retained measured-data excerpt; never synthesise a star."""
import csv, hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def build():
    src=ROOT/'upstream/bright-packed.csv'
    rows=list(csv.DictReader(src.open(newline='',encoding='utf-8')))
    stars=[]; excluded=[]
    tagged=list(enumerate(rows,7))
    endpoint_path=ROOT/'upstream/annotation-endpoints.csv'
    for extra in csv.DictReader(endpoint_path.open(newline='',encoding='utf-8')):
        tagged.append((int(extra.pop('source_line')),extra))
    for lineno,row in tagged:
        r={k:int(v) for k,v in row.items()}
        if r['hip']<=0:
            excluded.append({'sourceLine':lineno,'reason':'Sun' if r['vmag_centi']< -200 else 'no-resolvable-HIP-identity','raw':r});continue
        if r['vmag_centi']>400 and r['hip'] not in (10670,36962):raise ValueError('unexpected excerpt limit')
        stars.append({'hip':r['hip'],'raDeg':r['ra_mdeg']/1000,'decDeg':r['dec_mdeg']/1000,'vmag':r['vmag_centi']/100,
          'bv':None if r['bv_milli']==650 else r['bv_milli']/1000,'epochJyear':2000,
          'pmRaCosDecMasYr':None,'pmDecMasYr':None,'distancePc':None,'radialVelocityKmS':None,
          'sourceLine':lineno,'flags':['proper-motion-unavailable','catalogue-mean-not-current-variable-photometry']+(['colour-unavailable-upstream-default-ambiguous'] if r['bv_milli']==650 else [])})
    if len(stars)!=520 or len({s['hip'] for s in stars})!=520:raise ValueError('retained census mismatch')
    result={'schema':'salah-real-sky/catalogue/1','id':'HYG4.1-M5-pinned-bright518-plus2','frame':'mean equatorial J2000; source positions described by HYG as epoch/equinox 2000',
      'licence':'CC-BY-SA-4.0','attribution':'David Nash / Astronexus; quantized derivative uezo/M5StarScope; further selection and normalisation in this handoff',
      'selection':'518 HIP entries with V<=4.00 plus 2 measured annotation endpoints (HIP10670 V4.03 and HIP36962 V4.06). Not complete to naked-eye limit.',
      'provenance':{'commit':'b89fb6c0ec4077846816ac055d08c066115143f9','path':'lib/StarScopeCore/src/generated_star_data.cpp',
       'reportedGitBlob':'6ba9cfa858177618e088067a1444b4d1a81170f2','sourceLines':[7,530],'additionalSourceLines':[544,564],'endpointCsvSha256':hashlib.sha256(endpoint_path.read_bytes()).hexdigest(),'acquisition':'Numeric transcription from connector-returned source slices; complete raw blob not downloaded',
       'retainedCsvSha256':hashlib.sha256(src.read_bytes()).hexdigest()},'stars':stars}
    (ROOT/'data/bright-stars.json').write_text(json.dumps(result,separators=(',',':'),ensure_ascii=False)+'\n')
    (ROOT/'provenance/catalogue-exclusions.json').write_text(json.dumps(excluded,indent=2)+'\n')
    print(f'{len(tagged)} source rows -> {len(stars)} unique HIP sources; {len(excluded)} excluded')
if __name__=='__main__':build()
