"""Add an explicit coordinator readiness reconciliation; preserve author text."""
import json

PREFIX='https://github.com/theislampill/salah_widget/blob/SPEC_EVIDENCE_COMMIT/docs/rlgwo-execution/20261008/'


def annotate(text, metadata, readiness):
    assert readiness['primaryReconciled'] and readiness['coldRead']['exactFilesVerified']
    assert readiness['specificationReadiness']=='READY_WITH_EXPLICIT_EXECUTION_GATES'
    assert '<!-- COORDINATOR-READINESS:rev1 -->' not in text
    review=readiness['coldRead']
    report=review['report']
    stamp=(
        '<!-- COORDINATOR-READINESS:rev1 -->\n\n'
        '## Coordinator reconciliation — ready specification, open execution gates\n\n'
        f'**READY_WITH_EXPLICIT_EXECUTION_GATES.** Author {metadata["author"]}; independent cold reader {review["reviewer"]}; primary coordinator reconciled this exact revision. '
        f'[Cold-read report]({PREFIX}{report}), [readiness and source hashes]({PREFIX}SPECIFICATION_READINESS.json), '
        f'[consolidated execution graph]({PREFIX}CLOSURE_DAG.md). '
        'This qualifies the work order as executable. It does not claim that its future tests, platform proofs, repairs, merges or closure have happened. '
        'The AWAITING_COLD_REVIEW / READY_PENDING_REVIEW labels retained in the author text below record its pre-review drafting stage; '
        'this paragraph supersedes those labels only for specification cold-read readiness. Actual input, owner-decision, implementation, platform, qualification, delivery and closure gates remain binding. '
        'The issue remains open.\n\n'
        'The consolidated graph separates exact candidate review, required effect authority, actual delivery and final closure. '
        'For documentation-only work, accurate DOC/DOCS output can receive its own review and authorized delivery before unrelated native proof completes. '
        'Where the authored stage combined both, DELIVERY-CONFIRM preserves all original output interfaces and proof requirements; CLOSE still consumes every mandatory row and delivered document. '
        'This refines ordering only, waiving no acceptance obligation. One actual approval/delivery receipt may satisfy several nodes for the same exact head/base/effects; duplicate approvals or merges are not required. '
        'Runtime delivery still requires its full affected qualification and separate exact-head release authority.\n\n'
        '### Retained author specification\n\n')
    lines=text.splitlines(keepends=True)
    assert len(lines)>2 and 'Priority:' in lines[1]
    return ''.join(lines[:3])+stamp+''.join(lines[3:])


def metadata_for(root, path):
    if path.parent.name=='REMAINING_RLGWOs':
        return json.loads((root/'metadata'/f'{path.stem}.json').read_text(encoding='utf-8-sig'))
    if path.parent.name=='comments':
        issue=int(path.stem)
        for p in (root/'metadata').glob('R*.json'):
            m=json.loads(p.read_text(encoding='utf-8-sig'))
            if m['issue']==issue:return m
    return None
