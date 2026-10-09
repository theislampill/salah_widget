"""Read-only component comparison for narrow old native evidence reuse."""
import hashlib,json,subprocess,re
from pathlib import Path
OUT=Path(__file__).resolve().parent
ROOT=Path('C:/Users/theis/.codex/worktrees/hotfix-startup-clouds/salah_widget')
CURRENT='18ff14860ff41c084b1db5f396bb62aa9c22b1be'
OLD='1977217cc2ac26fcc436b991aff498d306a0cd26'
def blob(ref,path):return subprocess.check_output(['git','-C',str(ROOT),'show',ref+':'+path])
old=blob(OLD,'src/native/index.html').decode('utf-8-sig')
new=blob(CURRENT,'src/native/index.html').decode('utf-8-sig')
def cut(s,a,b):
    i=s.index(a);j=s.index(b,i+len(a));return s[i:j]
def digest(s):return hashlib.sha256(s.encode()).hexdigest()
blocks=[
 ('plain-format-and-escaping','const fmtDate =','// One ephemeral provider selection'),
 ('calendar-selection','function selectCalendarDisplay(M){','function bindDateDisclosure(){'),
 ('native-dialog-handler','function bindDateDisclosure(){','function renderCalendarDates(projection){'),
 ('calendar-sinks-and-full-values','function renderCalendarDates(projection){','// ---- SINGLE TEMPORAL SOURCE OF TRUTH'),
 ('native-arc-full-consumer','function drawArc(M){','// ---- continuous time-of-day sky'),
]
rows=[]
for name,a,b in blocks:
    try:
        x,y=cut(old,a,b),cut(new,a,b)
        row={'component':name,'oldSha256':digest(x),'currentSha256':digest(y),'byteEquivalent':x==y,'oldLines':len(x.splitlines()),'currentLines':len(y.splitlines())}
        if name=='native-arc-full-consumer':
            normalized=y.replace(' data-prayer-key="${p.k}"','')
            row.update({'oldEquivalentAfterSingleDiagnosticAttributeRemoval':normalized==x,
                'normalization':'Remove exactly added data-prayer-key="${p.k}" attribute; preserve all classes, classification, titles, geometry and emitted styles.',
                'addedAttributeOccurrences':y.count(' data-prayer-key="${p.k}"')})
        rows.append(row)
    except ValueError as e:rows.append({'component':name,'byteEquivalent':False,'error':'Boundary not present in both source owners: '+str(e)})
# Complete exact individual date/marker CSS rules; broader next-keyframe region
# can legitimately change for unrelated visual owners.
selectors=['.date-trigger','.date-trigger:hover','.date-trigger:focus-visible','.date-dialog','.date-dialog dd','.date-dialog p','.arc .dot','.arc .dot.adj','.arc .dot.adj.next']
for selector in selectors:
    p=re.compile(r'(?:^|\n)'+re.escape(selector)+r'\{[^}]*\}')
    a,b=p.findall(old),p.findall(new)
    rows.append({'component':'CSS '+selector,'oldRules':a,'currentRules':b,'byteEquivalent':bool(a) and a==b})
data={'schema':'B-native-component-equivalence/1','oldCommit':OLD,'targetCommit':CURRENT,'oldRootIndexSha256':hashlib.sha256(blob(OLD,'index.html')).hexdigest(),'currentRootIndexSha256':hashlib.sha256(blob(CURRENT,'index.html')).hexdigest(),'rows':rows,
 'reuseBoundary':'Exact component equivalence can retain old native click-handler/selection/markup/CSS controls within matching inputs/environments. Changed sky, startup, background, clocks, lifecycle or current render call sites are not automatically qualified. Old ordinary pointer open-close is not full native keyboard/touch or hostile-text execution proof.',
 'receiptIdentityCorrection':'docs/real-sky/evidence/chromium/native-controls/results.json runtimeSha256 hashes real-sky/native-sky.js, not index.html (tools/cp9/cp9_native_controls.py:55). It is not an old root-index binding and is not used to certify old root consumer behavior.',
 'existingExactTargetReceipt':'docs/real-sky/evidence/startup-cloud-20261007/final-v49/runs/joined-v49-final-chromium-native-lifecycle/results.json sourceSha256 equals exact final root ff728552442f4bcce7f213a089bf01d4cf70ea8d74040bdd3323768ca453beee. native-prayer-calendar-clock passed45 assertions, zero page errors. Controls before/at Maghrib, sky-pending countdown, before/after midnight. tools/cp9/native_lifecycle_check.py proof_ui performs native CE click->modal->Close. These exact-target ordinary paths are reused narrowly; not hostile text, unavailable-tomorrow, correction/method or complete keyboard/touch proof. Calendar PNGs remain local under startup-cloud-hotfix-20261007/h8; they are not falsely represented as retained public PNGs.'}
(OUT/'native-component-equivalence.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(data,ensure_ascii=False,indent=2))
