"""Stage authorized planning documents only; no Git/network/product effects.

Source author/reviewer files are preserved. Mechanical package-relative links
are recorded separately, allowing an immutable Git commit without a self-SHA.
"""
from pathlib import Path
import argparse
import hashlib
import json
import posixpath
import re
from publication_text import annotate, metadata_for, verify_reviewed_source

ROOT=Path(__file__).resolve().parents[1]
PREFIX='docs/rlgwo-execution/20261008'
SELF='https://github.com/theislampill/salah_widget/blob/SPEC_EVIDENCE_COMMIT/'+PREFIX+'/'


def digest(b):return hashlib.sha256(b).hexdigest()


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--staging',required=True,type=Path)
    args=ap.parse_args();base=args.staging.resolve();dest=base/PREFIX
    assert not dest.exists(), 'Use a new staging namespace; preserve prior package'
    dest.mkdir(parents=True)
    directories=('REMAINING_RLGWOs','metadata','comments','reviews','inputs','issues','publication','publication-inputs')
    readiness=json.loads((ROOT/'SPECIFICATION_READINESS.json').read_text())
    ready_by={x['issue']:x for x in readiness['issues']}
    assert len(ready_by)==26 and all(x['primaryReconciled'] and x['coldRead']['exactFilesVerified'] for x in ready_by.values())
    for row in ready_by.values():verify_reviewed_source(ROOT,row)
    paths=[p for p in ROOT.iterdir() if p.is_file() and p.suffix in ('.md','.json','.csv','.mmd') and p.name not in
           {'all-items.json','REFERENCE_PREFLIGHT.json','STARTUP_HANDOFF_PROGRESS.json','MANIFEST.json','PUBLICATION_TRANSFORMS.json'}]
    for directory in directories:paths+=list((ROOT/directory).rglob('*'))
    public_tools=('assemble_execution_dag.py','assemble_ledgers.py','assemble_priorities.py','validate_execution_plan.py','verify_manifest.py',
                  'graph_negative_controls.py','summarize_schedule.py','verify_references.py','publish_specification.py','publication_text.py',
                  'publication_guard_controls.py','commit_specification.py','prepare_publication.py')
    paths += [ROOT/'tools'/name for name in public_tools]
    # Freeze receipts preserve authors' exact custody hashes without publishing
    # their editable generators, incidental local working logs or browser data.
    for worker in 'ABCDEF':
        paths += [p for p in (ROOT/'workers'/worker).glob('*') if p.is_file() and 'freeze' in p.name.lower()]
    transforms=[]
    for path in sorted(set(paths)):
        if not path.is_file():continue
        rel=path.relative_to(ROOT).as_posix();data=path.read_bytes();out=data
        if path.suffix in ('.md','.json','.csv','.mmd'):
            text=data.decode('utf-8-sig')
            metadata=metadata_for(ROOT,path) if path.suffix=='.md' else None
            if metadata:text=annotate(text,metadata,ready_by[metadata['issue']],compact_for_comment=path.parent.name=='comments')
            def bind(match):
                target=match.group(1)
                return posixpath.relpath(target,posixpath.dirname(rel) or '.')
            text=re.sub(re.escape(SELF)+r'([^\s)<>"#]+)',bind,text)
            out=text.encode('utf-8')
        target=dest/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(out)
        if data!=out:transforms.append({'path':rel,'sourceSha256':digest(data),'publishedSha256':digest(out),'operation':'Resolve package self-links relative to containing file; remove UTF8 BOM if present; prepend explicit primary readiness/stage-order reconciliation. Only comments27/28 replace expanded G node cards with a metadata-derived interface/resource index and link to their complete unchanged binding cards in the full specification to meet GitHub size limit. All A-F/H and full-spec requirements preserved; no weakening or execution/release authority granted.'})
    record={'kind':'Mechanical publication transforms, distinct from author/reviewer acceptance','sourceTarget':'18ff14860ff41c084b1db5f396bb62aa9c22b1be','selfLinks':'Relative to containing file at the chosen immutable SPEC_SHA. Actual issue comments bind these to the first published specification commit.','files':transforms}
    (dest/'PUBLICATION_TRANSFORMS.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps({'stagedAt':str(dest),'files':len([p for p in dest.rglob('*') if p.is_file()]),'transformed':len(transforms)}))


if __name__=='__main__':main()
