"""Build resumable planning ledgers from exact cold-review and primary receipts."""
from pathlib import Path
import hashlib
import json

ROOT=Path(__file__).resolve().parents[1]


def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,d):p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')


def main():
    graph=load(ROOT/'CLOSURE_DAG.json');reviews={};issues=[]
    for filename in ('A-B','B-A','C-D','D-C','E-F','F-E'):
        path=ROOT/'reviews'/f'{filename}.json'
        if not path.exists():continue
        r=load(path)
        for row in r.get('issues',[]):
            valid=row.get('disposition') in {'PASS','PASS_SPECIFICATION_ONLY'} and not row.get('remainingMaterialFindingIds')
            bindings=row.get('reviewedFiles',[])
            if len(bindings)<3:valid=False
            for f in bindings:
                p=ROOT/f['path']
                if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=f['sha256']:valid=False
            reviews[row['issue']]={'reviewer':filename[0],'author':filename[-1],'disposition':row.get('disposition'),
                'exactFilesVerified':valid,'report':path.relative_to(ROOT).as_posix(),'reviewedFiles':bindings,
                'resolvedFindingIds':row.get('resolvedFindingIds',[]),'remainingMaterialFindingIds':row.get('remainingMaterialFindingIds',[])}
    primary=load(ROOT/'PRIMARY_RECONCILIATION.json') if (ROOT/'PRIMARY_RECONCILIATION.json').exists() else {'approvedIssues':[]}
    for path in sorted((ROOT/'metadata').glob('R*.json')):
        m=load(path);r=reviews.get(m['issue'],{})
        ready=bool(r.get('exactFilesVerified') and m['issue'] in primary['approvedIssues'])
        pubfile=ROOT/'publication'/f'{m["issue"]:02d}-rev{m["revision"]}.json'
        pub=load(pubfile) if pubfile.exists() else {}
        issues.append({'issue':m['issue'],'canonicalId':m['canonicalId'],'revision':m['revision'],'priority':m['priority'],
            'author':m['author'],'coldRead':r,'primaryReconciled':m['issue'] in primary['approvedIssues'],
            'specificationReadiness':'READY_WITH_EXPLICIT_EXECUTION_GATES' if ready else 'PENDING_COLD_OR_PRIMARY_RECONCILIATION',
            'sourceTarget':m['sourceTarget'],'auditEvidenceCommit':m['auditEvidenceCommit'],'specification':m['specPath'],
            'executionStatus':'NOT_STARTED_BY_PLANNING_PROGRAMME','issueState':'open','stateMutationAuthorized':False,
            'commentUrl':pub.get('commentUrl'),'publicationStatus':pub.get('status','NOT_PUBLISHED'),
            'nextAction':'Execute eligible scoped nodes only after owner launch; retain platform/decision/delivery gates.' if ready else 'Finish exact-hash cold read and primary reconciliation before publication.'})
    issues.sort(key=lambda x:x['issue'])
    save(ROOT/'SPECIFICATION_READINESS.json',{'kind':'Specification executability only; not product/native evidence or closure','issues':issues})
    save(ROOT/'ISSUE_LEDGER.json',{'initialOpenCount':26,'acceptedClosedIssues':[1,5,9,10,14,15,18,26,29,30,31],
        'closuresReopenedOrClosedByPlanning':0,'issues':issues})
    nodes=[]
    for n in graph['nodes']:
        nodes.append({'id':n['id'],'parentIssues':n['parentIssues'],'owner':n['owner'],'specification':n['specification'],
            'planningStatus':n['status'],'executionStatus':'NOT_STARTED_BY_THIS_PROGRAMME', 'sourceTarget':graph['identities']['sourceTarget'],
            'inputs':n['inputs'],'resources':n['resources'],'resourceLease':None,'independentReviewer':None,'outputReceipts':[],
            'affectedEvidence':[],'pendingExternalEffects':[],'nextAction':'Satisfy exact inputs and entry criteria; record source/runtime/fixture/platform and resource lease before execution.'})
    save(ROOT/'NODE_LEDGER.json',{'schemaVersion':1,'note':'Seed ledger. Existing active startup work is described in STARTUP_HANDOFF; do not duplicate it or infer completion from a node.', 'nodes':nodes})
    save(ROOT/'PUBLICATION_LEDGER.json',{'schemaVersion':1,'specifications':len(issues),'publishedReadBack':sum(i['publicationStatus']=='PUBLISHED_READBACK_VERIFIED' for i in issues),
        'issueStateChangesByThisProgramme':0,'issues':[{k:i[k] for k in ('issue','canonicalId','revision','commentUrl','publicationStatus','issueState')} for i in issues]})
    print(json.dumps({'specifications':len(issues),'coldReadExactPass':sum(bool(i['coldRead'].get('exactFilesVerified')) for i in issues),
                      'primaryReady':sum(i['primaryReconciled'] for i in issues),'published':sum(bool(i['commentUrl']) for i in issues)}))


if __name__=='__main__':main()
