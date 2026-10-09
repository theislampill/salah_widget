"""Render the reasoned issue/sub-obligation triage from reviewed specifications."""
from pathlib import Path
import collections
import json

ROOT=Path(__file__).resolve().parents[1]
TIE_ORDER=[24,33,34,36,2,3,4,6,7,32,8,11,12,13,17,35,19,21,22,23,37,20,16,25,27,28]


def clean(s):
    if isinstance(s,list):s='; '.join(map(str,s))
    return str(s).replace('|','\\|').replace('\n',' ')


def interval(m,key):
    values=[n['estimate'].get(key) for n in m['nodes']]
    if any(not isinstance(x,list) or len(x)!=2 or any(not isinstance(v,(int,float)) for v in x) for x in values):
        return 'unknown; bounded probe in spec'
    total=[sum(x[i] for x in values) for i in (0,1)]
    return f'{total[0]:g}–{total[1]:g}'


def main():
    metas=[json.loads(p.read_text(encoding='utf-8-sig')) for p in (ROOT/'metadata').glob('R*.json')]
    readiness=json.loads((ROOT/'SPECIFICATION_READINESS.json').read_text()) if (ROOT/'SPECIFICATION_READINESS.json').exists() else {'issues':[]}
    ready_by={x['issue']:x['specificationReadiness'] for x in readiness['issues']}
    metas.sort(key=lambda m:(int(m['priority'][1]), TIE_ORDER.index(m['issue']) if m['issue'] in TIE_ORDER else 100+m['issue']))
    counts=collections.Counter(m['priority'] for m in metas)
    lines=['# Remaining RLGWO priorities — revision 1','',
           'This ranks current residual obligations, not historical issue titles. Planning readiness does not mean implementation or closure is complete. Source target: `18ff14860ff41c084b1db5f396bb62aa9c22b1be`; accepted audit evidence: `b879573c298f19189d1f2392108b8b9f3b2cda0b`. No existing priority labels were found at inventory capture, and this programme does not change unrelated labels.','',
           '## Rubric and ordering','',
           '- **P0:** demonstrated critical security/data-integrity/core-correctness failure or severe operational blockage requiring immediate action or containment.',
           '- **P1:** substantial user-facing functionality, reliability or fidelity failure, or a significant release/closure-confidence gap that should be addressed next.',
           '- **P2:** bounded lower-urgency quality, documentation, coverage or maintenance completion that can safely follow higher-impact work.','',
           f'Current authored dispositions: P0 **{counts["P0"]}**, P1 **{counts["P1"]}**, P2 **{counts["P2"]}** across **{len(metas)}** specifications. Final publication additionally requires cold review and primary reconciliation. No P0 is invented to populate the rubric. Missing evidence is not proof of a current vulnerability.','',
           'Within P1, demonstrated ordinary visible failures receive attention before confidence-only gaps; broad core prayer/currentness exposure precedes less frequent edge cases. Platform acquisition starts early because its wait can dominate the schedule. Within P2, small, well-bounded document/coverage packages can finish early. The ordering below is a risk tie-breaker, not a false dependency or a promise to idle an available resource. The single heavy-browser queue, existing startup lease, native-host availability and independent review determine the actual ready waves.','',
           'Estimates below sum each issue’s declared active-work and exclusive-machine node ranges before cross-issue reuse. They are planning envelopes, not elapsed-time promises, and should not be summed across issues as independent campaigns. Confidence/basis and exclusions are in each work order. External platform/owner waits have no fabricated duration.','',
           '| Issue / ID | Residual class | Priority | Specification readiness | Execution owner | Hard prerequisites / gates | Active hours; exclusive minutes | Specification / published comment |',
           '|---|---|---|---|---|---|---|---|']
    for m in metas:
        modes=m.get('deliveryMode',m.get('closure',{}).get('deliveryMode','required proof/delivery per spec'))
        owners=[]
        for n in m['nodes']:
            if n['kind'] not in {'closure','qualification','delivery'} and n['owner'] not in owners:owners.append(n['owner'])
        pending=[]
        outputs={o['id'] for n in m['nodes'] for o in n['outputs']}
        for n in m['nodes']:
            for i in n['inputs']:
                if i['id'] not in outputs and i.get('status') not in {'SATISFIED','AVAILABLE','VERIFIED'} and i['id'] not in pending:pending.append(i['id'])
        gate='; '.join(pending) if pending else 'Accepted interfaces already supplied; own proof/review'
        gate+='; '+str(modes)
        path=ROOT/'publication'/f'{m["issue"]:02d}-rev{m["revision"]}.json'
        pub=json.loads(path.read_text(encoding='utf-8'))['commentUrl'] if path.exists() else None
        link=f'[spec]({m["specPath"]})'+(f' · [comment]({pub})' if pub else ' · publication pending')
        lines.append('| '+ ' | '.join([f'#{m["issue"]} / {m["canonicalId"]}',clean(m['residualClasses']),m['priority'],ready_by.get(m['issue'],m['readiness']),clean(owners),clean(gate),interval(m,'activeHours')+'h; '+interval(m,'exclusiveMachineMinutes')+'min',link])+' |')
    lines+=['','## Individual rationales and material sub-obligations','',
            'The following preserves severity, confidence, exposure and execution cost as different dimensions. Sub-obligations retain their own priority even when the parent’s highest-risk residual sets its issue rank. The detailed acceptance rows and evidence remain in the linked specifications.','']
    for m in metas:
        a=m['priorityAssessment']
        lines += [f'### #{m["issue"]} / {m["canonicalId"]} — {m["priority"]}', '', a['rationale'], '',
                  f'**Impact:** {clean(a["impact"])} **Affected conditions:** {clean(a["conditions"])} **Exposure/recurrence:** {clean(a["exposure"])}', '',
                  f'**Evidence confidence:** {clean(a["confidence"])} **Containment:** {clean(a["containment"])} **Existing priority/label departure:** {clean(a["existingLabelDeparture"])}','',
                  '| Residual obligation | Class | Priority | Reason |', '|---|---|---|---|']
        for r in m['remainingObligations']:
            lines.append(f'| {r["id"]} | {clean(r["class"])} | {r["priority"]} | {clean(r["priorityRationale"])} |')
            for sub in r.get('children',[]):
                if isinstance(sub,dict) and 'priority' in sub:
                    lines.append(f'| {sub.get("id",r["id"]+" child")} | {clean(sub.get("class",r["class"]))} | {sub["priority"]} | {clean(sub.get("priorityRationale",sub.get("rationale","See exact child acceptance row in specification.")))} |')
        lines += ['', 'Evidence: '+', '.join(f'[input {i+1}]({url})' for i,url in enumerate(a['evidence'])), '']
    lines += ['## Startup and glow boundary','',
              'R0021/#33 owns first-scene initialization/availability and its original callback-cost residuals. The separately demonstrated settled lunar atmospheric/display hotspot and broad wash is the named R0022-L1 successor under #34, linked from S10. Its presence in both baseline and candidate does not make it an accepted appearance or a new startup-caused regression. Attribution is completed; the bounded display correction and full-scene acceptance remain explicitly gated. The definite [STARTUP_HANDOFF](STARTUP_HANDOFF.md) records an active uncommitted candidate, no PR at capture, two Chromium timing failures, final Firefox measurement pending, actual extension parent unavailable and original callback cost unverified. It is a completed planning handoff, not a final implementation acceptance. Do not wait for all issue closures to plan these nodes, and do not count a lunar RGB comparison as whole-scene acceptance.','',
              'No change to N001/N002 PARTIAL or N003 BLOCKED is implied. Native Apple requirements remain specific to their installer/filesystem/entry contracts, not a global barrier to unrelated Windows/browser/docs work. New merges/deployments require separate exact-head approval.']
    (ROOT/'PRIORITIES.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({'issues':len(metas),'counts':dict(counts),'status':'GENERATED_FROM_AUTHOR_METADATA_REQUIRES_RECONCILIATION'}))


if __name__=='__main__':main()
