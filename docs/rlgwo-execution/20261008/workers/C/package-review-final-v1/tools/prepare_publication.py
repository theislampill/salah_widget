"""Bind primary-approved issue specifications to the published docs commit."""
from pathlib import Path
import argparse
import hashlib
import json
from publication_text import annotate

ROOT=Path(__file__).resolve().parents[1]


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--commit',required=True);args=ap.parse_args()
    assert len(args.commit)==40 and all(c in '0123456789abcdef' for c in args.commit)
    records=json.loads((ROOT/'SPECIFICATION_READINESS.json').read_text())['issues']
    assert len(records)==26 and all(x['primaryReconciled'] and x['coldRead']['exactFilesVerified'] for x in records)
    dest=ROOT/'publication-inputs';dest.mkdir(exist_ok=True)
    output={'sourceTarget':'18ff14860ff41c084b1db5f396bb62aa9c22b1be','specificationCommit':args.commit,
            'authority':'Owner explicitly authorizes versioned remaining-work issue comments; no close/reopen/labels/body edits or production effects.',
            'issues':[]}
    for r in records:
        m=json.loads((ROOT/'metadata'/f'{r["canonicalId"]}.json').read_text(encoding='utf-8-sig'))
        source=ROOT/'comments'/f'{r["issue"]:02d}.md'
        text=annotate(source.read_text(encoding='utf-8-sig'),m,r).replace('SPEC_EVIDENCE_COMMIT',args.commit)
        assert len(text)<65536 and 'SPEC_EVIDENCE_COMMIT' not in text
        path=dest/source.name;data=text.encode()
        if path.exists():assert path.read_bytes()==data,'Do not overwrite different prepared effect'
        else:path.write_bytes(data)
        packet=json.loads((ROOT/'issues'/f'{r["issue"]:02d}.json').read_text())
        output['issues'].append({'number':r['issue'],'canonicalId':r['canonicalId'],'revision':r['revision'],
            'primaryApproved':True,'coldReadDisposition':'PASS','author':r['author'],'coldReviewer':r['coldRead']['reviewer'],
            'commentPath':path.relative_to(ROOT).as_posix(),'commentSha256':hashlib.sha256(data).hexdigest(),
            'reviewedSourceCommentSha256':hashlib.sha256(source.read_bytes()).hexdigest(),
            'bodySha256':hashlib.sha256(packet['issue']['body'].encode()).hexdigest(),
            'chars':len(text),'transforms':'Coordinator readiness/stage-order reconciliation and immutable package-link binding only.'})
    path=ROOT/'PUBLICATION_APPROVAL.json';data=(json.dumps(output,indent=2)+'\n').encode()
    if path.exists():assert path.read_bytes()==data,'Preserve existing effect approval; reconcile before replacement'
    else:path.write_bytes(data)
    print(json.dumps({'prepared':len(output['issues']),'largestChars':max(x['chars'] for x in output['issues']),'commit':args.commit}))


if __name__=='__main__':main()
