"""Freeze reviewed wording and verify only scoped portable evidence copies."""
from pathlib import Path
import gzip
import hashlib
import json
import re

HERE=Path(__file__).resolve().parent
REV=Path('C:/Users/theis/.codex/worktrees/pr43-review-revision/salah_widget')
PORTABLE=REV/'docs/real-sky/pr43-review-evidence'
checks=[];inputs={}
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):
    b=p.read_bytes();inputs[str(p)]={'bytes':len(b),'sha256':sha(b)};return json.loads(b)
def check(name,ok,**detail):checks.append({'name':name,'pass':bool(ok),**detail})
evidence=read(HERE/'CHECKS.json')
font=read(HERE/'FONT_READBACK.json')
manifest=read(PORTABLE/'COPY_MANIFEST.json')
docs=[]
for relative,stored in (('docs/real-sky/PR43_REVIEW_REVISION.md','REVIEWED_PR43_REVIEW_REVISION.md'),
                        ('docs/real-sky/pr43-review-evidence/README.md','REVIEWED_PORTABLE_README.md')):
    p=REV/relative;b=p.read_bytes();inputs[str(p)]={'bytes':len(b),'sha256':sha(b)}
    (HERE/stored).write_bytes(b)
    docs.append({'path':str(p),'reviewedCopy':stored,'sha256':sha(b),'bytes':len(b)})
    check('wording binds exact current runtime '+relative,evidence['runtime'] in b.decode() and evidence['index'] in b.decode())
text=(HERE/'REVIEWED_PR43_REVIEW_REVISION.md').read_text()
check('strict failures and reused baseline disclosed','five FAIL and one PASS' in text
      and 'not a fresh matched timing pair' in text and 'coverage remains80ms' in text)
check('compact dependency disclosed','smaller, not absent' in text and '549,170' in text
      and 'do not claim core' in text and 'compact head itself is withheld' in text)
check('appearance/parent/callback gates retained','S10' in text and 'actual extension parent' in text
      and 'spotlight/grey wash remains visible' in text)
check('current18 distinct from old36','all eighteen corrected variants with sealed driver r5' in text
      and 'Original/intermediate RED remains in' in text and 'was not rerun or assigned a new date' in text)
README=(HERE/'REVIEWED_PORTABLE_README.md').read_text()
links=re.findall(r'\]\(([^)]+)\)',README)
for target in links:check('portable README target '+target,(PORTABLE/target).exists())
check('portable omissions and clip limits disclosed','OMITTED_GENERATED_INPUTS.json' in README
      and 'A viewing\nclip is not the timing oracle' in README)
viewed=[i for i in evidence['images'] if i['kind']=='ordinary-first-source-frame'
        or Path(i['path']).name=='while-held.png' or Path(i['path']).name=='final-refinement.png'
        or (Path(i['path']).name=='after-release.png' and any(v in i.get('case','') for v in ('held-core-night','compressed')))]
viewed+=font['images']
check('32 retained images independently viewed',len(viewed)==32)
target_sources=set()
for path in evidence['inputs']:
    p=Path(path)
    if 'R1-entry-final-04' in p.parts or 'R1-complete-scene-02' in p.parts:
        if p.name in ('receipt.json','results.json','ASSESSMENT.json'):target_sources.add(p)
for path in font['inputs']:
    p=Path(path)
    if 'R2-font-final-04' in p.parts:target_sources.add(p)
target_sources.update(Path(i['path']) for i in viewed)
copies=[]
for source in sorted(target_sources):
    found=[(relative,pin) for relative,pin in manifest.items() if Path(pin['source'])==source]
    check('unique scoped portable copy '+str(source),len(found)==1)
    if len(found)!=1:continue
    relative,pin=found[0];original=source.read_bytes();stored=(PORTABLE/relative).read_bytes()
    decoded=gzip.decompress(stored) if pin['encoding']=='gzip-exact-original' else stored
    ok=decoded==original and sha(original)==pin['sourceSha256'] and len(original)==pin['sourceBytes'] and sha(stored)==pin['storedSha256']
    check('portable exact bytes '+relative,ok)
    copies.append({'relative':relative,**pin})
views={'schema':'current04-original-pixel-review/1','count':len(viewed),'images':viewed,
       'judgments':{'ordinaryFirstScenes':'Moon/stars/sky co-captured; early prayer/date readiness not established; L1 wash/spotlight visible',
                    'heldCoreNight':'Moon/catalogue visible before incomplete core; loading placeholders expected',
                    'heldTailAndReleased':'Native prayer/settings consumer recovery with preserved Moon appearance and card footprint',
                    'finalRefinement':'Both native finals show textured Moon, closed settings and persistent L1 wash/spotlight',
                    'fonts':'Ten natural current04 captures preserve relevant rail clearance, label baseline and hero alignment; no whole-renderer verdict'},
       'limits':['Stills do not prove all intermediate frames, motion or every opacity boundary.','Day held-core has no warranted lunar body; do not label a daylight non-visible Moon current.']}
(HERE/'VIEWS.json').write_text(json.dumps(views,indent=2)+'\n',encoding='utf-8')
result={'schema':'current04-publication-binding/1','status':'PASS_SCOPED_COPIES_AND_DOCUMENT_BOUNDARIES' if all(c['pass'] for c in checks) else 'BINDING_FAILURE',
        'checks':checks,'inputs':inputs,'docs':docs,'scopedPortableCopies':copies,'viewedImages':len(viewed),
        'scope':'Fresh exact04 evidence and publication wording only; source unchanged, no browser/build/publication performed'}
(HERE/'PUBLICATION_BINDINGS.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':result['status'],'checks':len(checks),'failures':[c for c in checks if not c['pass']],
                  'docPins':docs,'portableCopies':len(copies),'images':len(viewed)},indent=2))
assert all(c['pass'] for c in checks)
