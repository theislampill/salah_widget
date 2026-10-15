"""Read-only source/immutable-receipt reanchor; writes issue-scoped evidence only."""
import hashlib, json, subprocess
from pathlib import Path
from runtime_identity import runtime_identity

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'evidence/R0003/qualification'
AUDIT='b879573c298f19189d1f2392108b8b9f3b2cda0b'
OLD='18ff14860ff41c084b1db5f396bb62aa9c22b1be'
SPEC='21e7a84365fae37a86cae5c7d5e41008c0adc53f'
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def blob(commit,path):return git('show',commit+':'+path)
def sha(b):return hashlib.sha256(b).hexdigest()
def text(b):return b.decode().replace('\r\n','\n')
def dump(name,obj):(OUT/name).write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def region(source,start,end):
    assert source.count(start)==1,start
    a=source.index(start);b=source.index(end,a+len(start))
    return source[a:b]

OUT.mkdir(parents=True,exist_ok=True)
paths=['03-assessment.json','source-fixtures.tap','source-equivalence.json','ownership-mutation-equivalence.json','ownership-mutation-equivalence.cjs']
receipts={}
for name in paths:
    p='docs/rlgwo-audit/20261008/workers/A/'+name;b=blob(AUDIT,p)
    receipts[name]={'sha256':sha(b),'bytes':len(b),'url':f'https://github.com/theislampill/salah_widget/blob/{AUDIT}/{p}'}
assessment=json.loads(blob(AUDIT,'docs/rlgwo-audit/20261008/workers/A/03-assessment.json'))
dump('original-accepted-map.json',{'originalAudit':receipts,'requirementMatrix':assessment['requirementMatrix'],'negativeControls':assessment['negativeControls'],'reuseBasis':assessment['reuseBasis'],'crossIssueDependencies':assessment['crossIssueDependencies']})
old=text(blob(OLD,'src/native/index.html'));new=text((ROOT/'src/native/index.html').read_bytes())
anchors=[('request','function cacheKey(){','// Read only the selected legacy'),('cache','function readPrayerCache(','async function fetchTimings('),('transport','async function fetchTimings(','// The committed response carries'),
         ('hourly','function wxUnitsMatch(','function weatherEligibility('),('weather','async function fetchWeather(){','// RainViewer tiles'),
         ('radar','function wxRadarSample(','// linear-interpolate the forecast'),('settings','function _settingsFormToConfig(){','function _populateSettingsForm(){'),('settings-commit','function _commitSettings(){','async function _usePrecise(){')]
comparisons=[]
for name,start,end in anchors:
    try:a=region(old,start,end);b=region(new,start,end)
    except ValueError:
        if name!='transport':raise
        # Exact transport ends at the next actual owner declaration.
        a=region(old,start,'function prayerResultEligible(');b=region(new,start,'function prayerResultEligible(')
    consumers={}
    for entry in ('index.html','offline.html'):
        raw=text((ROOT/entry).read_bytes())
        mapped=region(raw,start,end) if end in raw[raw.index(start):] else region(raw,start,'function prayerResultEligible(')
        expected=b
        if name=='weather':
            line='    if(track&&attemptEligible(op,a)) weatherTrack=track;'
            expected=b.replace(line,line+'\n    // CP9 elevation custody: notify only after this operation\'s eligible native weather adoption.\n    if((current||track)&&elevation!=null&&attemptEligible(op,a)&&selectedWeather()) window.SalahNativeSkyHost?.acceptedElevation(elevation,op.generation,captured.lat,captured.lon);')
        consumers[entry]={'sha256':sha(mapped.encode()),'expectedGeneratedMatch':mapped==expected}
    comparisons.append({'owner':name,'originalSha256':sha(a.encode()),'currentSha256':sha(b.encode()),'unchanged':a==b,'generated':consumers})
specPath='docs/rlgwo-execution/20261008/REMAINING_RLGWOs/R0003.md'
dump('currentness.json',{'baseCommit':git('rev-parse','HEAD').decode().strip(),'baseTree':git('rev-parse','HEAD^{tree}').decode().strip(),'spec':{'commit':SPEC,'path':specPath,'sha256':sha(blob(SPEC,specPath))},'sourceRegions':comparisons,'priorReceipts':receipts,'limits':'Only named slices prove equivalence. Radar guard changed; native A05 and 57 source controls requalify its boundary. Presentation/Moon changes require fresh A07.'})
dump('runtime-identity.json',runtime_identity(ROOT))
print(json.dumps({'owners':[(r['owner'],r['unchanged'],all(v['expectedGeneratedMatch'] for v in r['generated'].values())) for r in comparisons]}))
