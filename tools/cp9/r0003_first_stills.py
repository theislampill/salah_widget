"""Bind native first-render screenshots by holding only the tomorrow provider body.

No render/clock/state changes: the actual current B renders normally, its native
screenshot is associated before releasing the independent tomorrow input.
"""
import copy, hashlib, json
from pathlib import Path
from r0003_cases import B, rule, release, settled, wait, cap

ROOT=Path(__file__).resolve().parents[2]

def main():
    packet=json.loads((ROOT/'tests/rlgwo/R0003-cases.json').read_text(encoding='utf-8'))
    original=packet['cases'][0];cases=[]
    for name,entry,iframe in [('root','index.html',False),('offline','offline.html',False),('iframe','index.html',True)]:
        case=copy.deepcopy(original)
        case.update(caseId='R0003-first-still-'+name,entry=entry,iframe=iframe,acceptanceIds=['R0003-A01','R0003-A07'])
        case['responseRules'][1]['day']='07-09-2026'
        case['responseRules'].insert(2,rule('B-next',B,hold=True,zone='America/New_York',day='08-09-2026'))
        for action in case['orderedActions']:
            if action.get('firstRender'):action['name']='first-current'
        case['orderedActions'] += [release('B-next'),settled('B-next'),wait("window.__prayerFixture.readSnapshot().tomorrow?.tag==='B-next'"),cap('B-tomorrow')]
        case['expected'].append({'stage':'B-tomorrow','equals':{'tomorrow/tag':'B-next','tomorrowDay':'08-09-2026','slots/prefetch':None},'noInvalidText':True})
        case['firstStillPurpose']='First accepted prayer-presentation state while tomorrow remains held. Preserve actual ordinal mismatches; independent exact presentation equivalence and original PNG review are required. No unique scanout, whole-scene or motion claim.'
        cases.append(case)
    packet['cases']=cases
    packet['sourceFiles']['tools/cp9/r0003_first_stills.py']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    path=ROOT/'tests/rlgwo/R0003-first-stills.json'
    path.write_text(json.dumps(packet,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps({'cases':len(cases),'packetSha256':hashlib.sha256(path.read_bytes()).hexdigest()}))

if __name__=='__main__':main()
