"""Offline association of an original native PNG with unchanged first prayer state.

Does not create/edit pixels. Strict ordinal mismatches stay in original receipts.
Independent visual review remains required; no whole-scene/scanout/motion claim.
"""
import argparse,copy,hashlib,json
from pathlib import Path

FIELDS=['runtimeGeneration','config','timezone','currentDay','tomorrowDay','today','tomorrow','dom','dateTruth','weatherHeader','weatherDecision','weather','weatherTrack','weatherRadar','lastWxAt','lastRadarAt','fonts','assets','storageLogLength','visibility']
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def tuple_of(row):
    result={k:row[k] for k in FIELDS};render=copy.deepcopy(row['render']);render.pop('atMs',None);result['render']=render
    return result
def check(folder):
    case=read(folder/'case-input.json');trace=read(folder/'trace.json');raw=trace.get('rawOnFailure',trace)
    originals=[s for s in raw['snapshots'] if s['stage']=='render-completed' and not s.get('checkpoint')]
    first=next(s for s in originals if (s.get('today') or {}).get('tag')=='B')
    action=next(a for a in case['orderedActions'] if a.get('firstRender'));name=action['name']
    presentation=read(folder/(name+'-presentation.json'));png=folder/(name+'.png')
    assert presentation['receiptOrdinal']==first['renderOrdinal']
    assert presentation['beforeOrdinal']==presentation['afterOrdinal'],'capture crossed a product render'
    between=[s for s in originals if first['renderOrdinal']<=s['renderOrdinal']<=presentation['afterOrdinal']]
    assert between and between[-1]['renderOrdinal']==presentation['afterOrdinal']
    assert all(tuple_of(s)==tuple_of(first) for s in between),'intervening accepted presentation changed'
    assert png.exists() and png.read_bytes().startswith(b'\x89PNG\r\n\x1a\n')
    return {'status':'FIRST_PRAYER_PRESENTATION_ASSOCIATED_PENDING_PIXEL_REVIEW','caseId':case['caseId'],'traceSha256':sha(folder/'trace.json'),
            'originalPng':name+'.png','originalPngSha256':sha(png),'receiptSha256':sha(folder/(name+'-presentation.json')),
            'firstRenderOrdinal':first['renderOrdinal'],'captureOrdinal':presentation['afterOrdinal'],'interveningRenderOrdinals':[s['renderOrdinal'] for s in between],
            'comparedFields':FIELDS+['render except atMs'],'limits':'Original native PNG plus exact unchanged first accepted prayer presentation; not a unique ordinal-2 screenshot, physical scanout, whole-scene pixel identity or motion proof.'}
def main():
    p=argparse.ArgumentParser();p.add_argument('folder',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    try:r=check(a.folder)
    except Exception as e:r={'status':'NOT_ASSOCIATED','failure':repr(e),'traceSha256':sha(a.folder/'trace.json')}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8');print(json.dumps(r));return int(r['status']=='NOT_ASSOCIATED')
if __name__=='__main__':raise SystemExit(main())
