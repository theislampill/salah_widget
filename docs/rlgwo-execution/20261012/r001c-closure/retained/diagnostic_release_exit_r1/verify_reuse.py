"""Bounded offline custody/equality review; no execution of retained tests."""
import datetime as dt
import difflib
import hashlib
import json
from pathlib import Path
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')
OUT = Path(__file__).resolve().parent
RUN = OUT.parent.parent
REV = Path('C:/Users/theis/.codex/worktrees/pr43-review-revision/salah_widget')

def load(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))

def ref(p):
    p = Path(p); b = p.read_bytes()
    return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}

def write(n,o):
    p=OUT/n; assert not p.exists(),p
    p.write_text(json.dumps(o,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    return ref(p)

checked={}
def bound(v):
    p=Path(v['path']); a=ref(p)
    assert a['sha256']==v['sha256'],(v,a)
    if 'bytes' in v: assert a['bytes']==v['bytes'],(v,a)
    checked[str(p)]=a
    return a

def references(o):
    if isinstance(o,dict):
        if 'path' in o and 'sha256' in o and re.fullmatch(r'[0-9a-fA-F]{64}',str(o['sha256'])):
            bound(o)
        for x in o.values(): references(x)
    elif isinstance(o,list):
        for x in o: references(x)

packets=[]
for name,expected in [('diagnostic_a10_final_adopted_r1','5173787b5f0cb5c7d9b0b30059defa503efb5a3c95bf91f2414730501b7bbb78'),
                       ('diagnostic_a10_final_consumer_r1','c3744624abd6b96d404c9691439261551f05f281669f79f31c5be50f51e2da7b')]:
    root=RUN/'workers'/name
    seal=bound({'path':str(root/'SEAL.json'),'sha256':expected})
    s=load(root/'SEAL.json')
    manifest=bound({'path':str(root/'MANIFEST.json'),'sha256':s['manifestSha256']})
    m=load(root/'MANIFEST.json')
    for path,v in m['files'].items():
        bound({'path':str(root/path),**v})
    packets.append({'root':str(root),'seal':seal,'manifest':manifest,'membersVerified':len(m['files'])})

map_path=RUN/'workers/diagnostic_a10_final_adopted_r1/FINAL_ROW_MAP.json'
rowmap=load(map_path)
references(rowmap)
inherited=load(rowmap['inheritedSealedRowMap']['path'])
references(inherited)
root_result=bound({'path':str(RUN/'evidence/R001C/rendered/results.json'),'sha256':'84f522e004ace04b8db01a15c6918d56698ad153b3816f1bbd66455840eb867a'})
render_join=bound({'path':str(RUN/'integration/r001c-render-exit-join-r1/receipt.json'),'sha256':'269dd7aaeb57f0b666ecee86bcd0f2a9562db52965072e869c03cb7b31d0fb00'})
references(load(root_result['path']))
references(load(render_join['path']))
facts=load(OUT/'inputs/R001C.metadata.json')['documentationFacts']
sources={f:(OUT/'inputs/final'/f).read_text(encoding='utf-8') for f in ('AGENTS.md','DESIGN.md','OPTICS.md')}
required=[]
for i,x in enumerate(facts):
    text=x.get('example',x['fact'])
    if i in (0,1,2,3,4,5):
        for f,s in sources.items():
            matches=[n for n,l in enumerate(s.splitlines(),1) if l==text]
            assert len(matches)==1,(i,f,text,matches)
            required.append({'assertion':'documentationFacts['+str(i)+']','file':f,'line':matches[0],
                             'literal':text,'sha256':hashlib.sha256(text.encode()).hexdigest(),'occurrences':1,'disposition':'PASS_EXACT_LITERAL'})
enum='debugOptic=halo|sundogs|pillar|anticrep|paraselene|lunarhalo'
assert sources['DESIGN.md'].count(enum)==1
required.append({'assertion':'DESIGN-six-name-enum','file':'DESIGN.md','line':sources['DESIGN.md'][:sources['DESIGN.md'].index(enum)].count('\n')+1,'literal':enum,'disposition':'PASS_EXACT_LITERAL'})

inventory=[]
for f,s in sources.items():
    for i,l in enumerate(s.splitlines(),1):
        if any(x in l for x in ('debugMotion','debugOptic','motion=full','?timeScale')):
            if 'index.html?' in l: classification='EXPLICIT_QUERY_NEGATIVE'
            elif 'A query-only' in l: classification='EXPLICIT_QUERY_NOT_READ_CAVEAT'
            elif 'index.html#' in l: classification='COMPLETE_FRAGMENT_POSITIVE'
            elif '?' in l and 'debugDawn' in l: classification='DEPRECATED_NOOP_UNCHANGED_OTHER_OWNER'
            elif '?' in l: classification='REQUIRES_MANUAL_CLASSIFICATION'
            elif '`&' in l: classification='APPEND_INSIDE_FRAGMENT_POSITIVE_OR_PROSE'
            else: classification='ENUM_OR_DIAGNOSTIC_PROSE'
            inventory.append({'file':f,'line':i,'text':l,'classification':classification})
assert not any(x['classification']=='REQUIRES_MANUAL_CLASSIFICATION' for x in inventory)

vm_lines=[json.loads(x) for x in (RUN/'workers/doc_join_review/runs/actual-ROOT-R001C.stdout').read_text(encoding='utf-8-sig').splitlines() if x.strip()]
summary=next(x['summary'] for x in vm_lines if 'summary' in x)
assert (summary['passed'],summary['reused'],summary['failed'])==(37,1,0)
helper=load(RUN/'workers/doc_join_review/runs/helper-binding.stdout')
assert len(helper['contexts'])==16 and helper['heldOut']=={'fraction':-0.2,'firstMatch':-0.2,'widget':0}
vm={'raw':ref(RUN/'workers/doc_join_review/runs/actual-ROOT-R001C.stdout'),'counts':{k:summary[k] for k in ('cases','passed','reused','failed','scope')},
    'selectedLedger':summary['selectedLedger'],'scope':'Historical recorded source/VM only; no replay or whole-runtime qualification.',
    'helper':{'raw':ref(RUN/'workers/doc_join_review/runs/helper-binding.stdout'),'contexts':helper['contexts'],'heldOut':helper['heldOut'],'limits':helper['limits']}}
write('ACCEPTED_VM_READBACK.json',vm)

# Line-level diagnostic changes; peer owner words in mixed hunks remain uncredited.
changes=[]
for f,current in sources.items():
    before=(OUT/'inputs/base'/f).read_text(encoding='utf-8').splitlines()
    after=current.splitlines()
    for op,a,b,c,d in difflib.SequenceMatcher(None,before,after,autojunk=False).get_opcodes():
        if op=='equal':continue
        for pos in range(c,d):
            l=after[pos]
            region=(f=='AGENTS.md' and 144<=pos+1<175) or (f=='DESIGN.md' and 485<=pos+1<517) or (f=='OPTICS.md' and 13<=pos+1<47)
            if not region and not any(k in l.lower() for k in ('debugmotion','debugoptic','motion=full','six supported forces','dedicated diagnostic forcing')):
                continue
            if not l.strip() or l.startswith('```'):continue
            changes.append({'file':f,'line':pos+1,'text':l,'sha256':hashlib.sha256(l.encode()).hexdigest(),
                            'baseInterval':[a+1,b],'ownerScope':'R001C_DIAGNOSTIC_REQUIRED_FACT_OR_LITERAL' if region else 'R001C_DIAGNOSTIC_SUBCLAUSE_IN_CONTEXTUAL_LINE',
                            'contextualPeerWords':'Unrelated cloud/weather/clock prose in the same line is not approved by this review.' if not region else None})
write('SELECTED_DIFF.json',{'baseHead':load(OUT/'GIT_IDENTITY.json')['baseHead'],'fullThreeDocDiff':ref(OUT/'documentation.diff'),
                           'selectedChangedLines':changes,'meaning':'Diagnostic owner line/subclause selection only; full diff retained as context.'})
write('REQUIRED_ASSERTIONS.json',{'literalAssertions':required,'diagnosticInventory':inventory,'noPositiveQueryOnly':True,
                                'queryNegativesCount':sum(x['classification']=='EXPLICIT_QUERY_NEGATIVE' for x in inventory),
                                'sourceExecutionReplayed':False,'lineNumbersAreFinalFrozenSource':True})
write('REUSE_READBACK.json',{'schema':'r001c-release-applicable-evidence-reuse/1','atUtc':dt.datetime.now(dt.timezone.utc).isoformat(),
                           'packets':packets,'canonicalRenderResult':root_result,'canonicalRenderJoin':render_join,
                           'exactReferencesVerified':list(checked.values()),'originalAcceptedBoundaries':inherited['acceptedBoundaries'],
                           'immutableVmRaw':vm['raw'],'helperRaw':vm['helper']['raw'],
                           'currentSourceRelevantExcerptMatch':load(OUT/'SOURCE_FACT_BINDINGS.json')['priorSemanticOwnerReassociation'],
                           'historicalNativeAndDesignFailures':'Retained exact referenced evidence; no failures relabelled.',
                           'newRuntimePixelMotionMediaAssertions':False,'newTestsOrBrowserOrBuilds':0})
print(json.dumps({'packets':[{ 'name':Path(p['root']).name,'members':p['membersVerified']} for p in packets],
                  'exactReferencesVerified':len(checked),'literalAssertions':len(required),'selectedChangedLines':len(changes),
                  'queryNegatives':sum(x['classification']=='EXPLICIT_QUERY_NEGATIVE' for x in inventory),
                  'retainedVm':'37 PASS + 1 REUSED; 16 contexts; -0.2 held-out differs'}))
