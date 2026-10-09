"""Record the primary's explicit planning approval after exact independent gates."""
from pathlib import Path
import argparse
import datetime
import hashlib
import json

ROOT=Path(__file__).resolve().parents[1]


def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--approve',action='store_true');args=ap.parse_args()
    assert args.approve,'Primary decision required; inspection alone does not authorize publication'
    inventory=load(ROOT/'INVENTORY.json');baseline=load(ROOT/'BASELINE_OBLIGATIONS.json')
    baseline_by={(x['issue'],x['id']):x for x in baseline['remainingMandatory']}
    readiness=load(ROOT/'SPECIFICATION_READINESS.json')['issues']
    assert len(readiness)==26 and {x['issue'] for x in readiness}==set(inventory['actualOpen'])
    from publication_text import verify_reviewed_source
    rows=[]
    for r in readiness:
        assert r['coldRead']['exactFilesVerified'] and not r['coldRead']['remainingMaterialFindingIds']
        assert r['author']!=r['coldRead']['reviewer']
        verify_reviewed_source(ROOT,r)
        m=load(ROOT/'metadata'/f'{r["canonicalId"]}.json')
        for o in m['remainingObligations']:
            b=baseline_by.get((r['issue'],o['id']))
            if b:assert o['parentText']==b['obligation'],'Changed original parent text'
        rows.append({'issue':r['issue'],'canonicalId':r['canonicalId'],'revision':r['revision'],'author':r['author'],
                     'coldReader':r['coldRead']['reviewer'],'coldReport':r['coldRead']['report'],
                     'boundFiles':r['coldRead']['reviewedFiles'],'priority':r['priority'],
                     'residualRows':len(m['remainingObligations']),'disposition':'APPROVE_SPECIFICATION_PUBLICATION_ONLY'})
    graph=load(ROOT/'DAG_VALIDATION.json');negative=load(ROOT/'DAG_NEGATIVE_CONTROLS.json')
    assert graph['result']==negative['result']=='PASS' and graph['graphSha256']==negative['graphSha256']
    assert graph['graphSha256']==hashlib.sha256((ROOT/'CLOSURE_DAG.json').read_bytes()).hexdigest()
    package=load(ROOT/'reviews/PACKAGE-C.json')
    assert package['disposition']=='PASS' and not package.get('remainingMaterialFindingIds')
    for item in package['reviewedFiles']:
        assert hashlib.sha256((ROOT/item['path']).read_bytes()).hexdigest()==item['sha256'],f'Package review drift: {item["path"]}'
    handoff=load(ROOT/'STARTUP_HANDOFF.json')
    assert handoff['planningHandoffStatus']=='DEFINITE_RECEIVED_AND_RECONCILED'
    record={'capturedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'primaryDecision':'APPROVE_BOUNDED_SPECIFICATION_PUBLICATION_AND_EXECUTION_HANDOFF',
        'scope':'Planning executability/coverage/currentness and documentation-only publication; no planned runtime/native acceptance, merge/deployment or issue-state change.',
        'sourceTarget':inventory['sourceTarget'],'auditEvidenceCommit':inventory['auditEvidenceCommit'],
        'approvedIssues':sorted(x['issue'] for x in rows),'issues':rows,'originalResidualRows':111,'acceptedSupersededRows':len(baseline['acceptedOrSuperseded']),
        'graphSha256':graph['graphSha256'],'packageIndependentReviewer':'C, gpt-6.1-sol/max client-confirmed',
        'packageReviewSha256':hashlib.sha256((ROOT/'reviews/PACKAGE-C.json').read_bytes()).hexdigest(),
        'conditions':'Exact source hashes and live issue/currentness gates rechecked by publisher; mechanical transforms disclosed; required source/evidence/platform/decision/delivery gates remain open. No failed control or original obligation waived.'}
    (ROOT/'PRIMARY_RECONCILIATION.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps({'approved':len(rows),'scope':record['scope']}))


if __name__=='__main__':main()
