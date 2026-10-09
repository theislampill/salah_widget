"""Add an explicit coordinator readiness reconciliation; preserve author text."""
import json
import hashlib

PREFIX='https://github.com/theislampill/salah_widget/blob/SPEC_EVIDENCE_COMMIT/docs/rlgwo-execution/20261008/'


def verify_reviewed_source(root, readiness):
    expected={readiness['specification'],f'comments/{readiness["issue"]:02d}.md',f'metadata/{readiness["canonicalId"]}.json'}
    bindings=readiness['coldRead']['reviewedFiles']
    assert {x['path'] for x in bindings}==expected,'Cold-read binding must cover exact issue spec/comment/metadata'
    for item in bindings:
        path=root/item['path']
        assert path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest()==item['sha256'],f'Reviewed source drift: {item["path"]}'


def compact_expanded_schedule(text, metadata):
    """GitHub 65536-char bound: keep substantive core and link full node cards."""
    if metadata['issue'] not in (27,28):return text
    start=text.index('### '+metadata['canonicalId']+'-',text.index('## G.'))
    end=text.index('## H.',start)
    lines=[f'The full independently reviewed node cards (exact entry/exit/checks/shared-file contracts) remain in the [versioned specification appendix]({PREFIX}{metadata["specPath"]}#g-interface-dependencies-resources-and-costs). '
           'This comment retains the full A–F execution/acceptance core and H closure checklist. The following lossless interface/ownership index replaces repeated expanded cards here to respect GitHub’s comment-size limit; it does not remove those binding cards from the work order.','',
           '| Node / owner | Consumed interfaces and prerequisites | Produced interfaces | Resources / effort |',
           '|---|---|---|---|']
    def clean(v):return str(v).replace('|','\\|').replace('\n',' ')
    for n in metadata['nodes']:
        inputs='; '.join(i['id']+' ('+i.get('status','produced; pending')+')' for i in n['inputs'])
        deps='; '.join(d['node']+': '+d['reason'] for d in n.get('dependsOn',[]))
        outputs='; '.join(o['id']+' → '+o.get('artifact','specified case receipt') for o in n['outputs'])
        cost=n['estimate']
        lines.append('| '+ ' | '.join(map(clean,[n['id']+' / '+n['owner'],inputs+(' / '+deps if deps else ''),outputs,
            ', '.join(n['resources'])+'; active '+str(cost.get('activeHours'))+'h; exclusive '+str(cost.get('exclusiveMachineMinutes'))+'min; '+cost.get('confidence','unknown')]))+' |')
    return text[:start]+'\n'.join(lines)+'\n\n'+text[end:]


def annotate(text, metadata, readiness, compact_for_comment=False):
    assert readiness['primaryReconciled'] and readiness['coldRead']['exactFilesVerified']
    assert readiness['specificationReadiness']=='READY_WITH_EXPLICIT_EXECUTION_GATES'
    assert '<!-- COORDINATOR-READINESS:rev1 -->' not in text
    if compact_for_comment:text=compact_expanded_schedule(text,metadata)
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
