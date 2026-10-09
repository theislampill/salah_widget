"""Validate the published RLGWO execution graph; does not run product tests.

Python 3 standard library only. This checks structural/contract coverage and
artifact availability, not whether future implementation or qualification passed.
"""
from pathlib import Path
import argparse
import collections
import csv
import hashlib
import json
import re


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def validate(root):
    errors, warnings = [], []
    graph = read_json(root / 'CLOSURE_DAG.json')
    baseline = read_json(root / 'BASELINE_OBLIGATIONS.json')
    inventory = read_json(root / 'INVENTORY.json')
    nodes = graph['nodes']
    ids = [n['id'] for n in nodes]
    if len(ids) != len(set(ids)):
        errors.append('Duplicate node IDs')
    by_id = {n['id']: n for n in nodes}
    resources = {r['id']: r for r in graph['resources']}
    outputs = collections.defaultdict(list)
    for n in nodes:
        for o in n.get('outputs', []):
            outputs[o['id']].append(n['id'])
    for oid, owners in outputs.items():
        if len(owners) != 1:
            errors.append(f'Output interface has multiple producers: {oid}: {owners}')
    outgoing = collections.defaultdict(list)
    incoming = collections.Counter()
    pairs = set()
    edge_set = set()
    for e in graph['edges']:
        a, b = e['from'], e['to']
        if a not in by_id or b not in by_id:
            errors.append(f'Dangling dependency: {a} -> {b}')
            continue
        if e['type'] not in {'hard-interface', 'qualification', 'review', 'integration', 'closure', 'authority'}:
            errors.append(f'Unknown dependency type: {e}')
        if not e.get('reason'):
            errors.append(f'Unexplained dependency: {a} -> {b}')
        key = (a, b, e['type'])
        if key in edge_set:
            errors.append(f'Duplicate typed edge: {key}')
        edge_set.add(key)
        if (a, b) not in pairs:
            outgoing[a].append(b)
            incoming[b] += 1
            pairs.add((a, b))
        if e.get('interface') and e['interface'] not in {o['id'] for o in by_id[a].get('outputs', [])}:
            errors.append(f'Edge names missing produced interface: {e}')
    queue = sorted(n for n in ids if incoming[n] == 0)
    topo = []
    while queue:
        n = queue.pop(0)
        topo.append(n)
        for child in outgoing[n]:
            incoming[child] -= 1
            if incoming[child] == 0:
                queue.append(child)
                queue.sort()
    if len(topo) != len(nodes):
        errors.append('Cycle detected among: ' + ', '.join(sorted(set(ids) - set(topo))))
    if graph.get('topologicalOrder') != topo:
        errors.append('Stored topological order differs from independently computed order')
    externals = {x['id']: x for x in graph.get('externalInputs', [])}
    required = ('id', 'priority', 'kind', 'owner', 'scope', 'specification', 'inputs', 'outputs',
                'entryCriteria', 'exitCriteria', 'tests', 'resources', 'estimate', 'status')
    blocked_inputs = []
    for n in nodes:
        for key in required:
            if key not in n:
                errors.append(f'{n["id"]}: missing {key}')
        if n.get('priority') not in {'P0', 'P1', 'P2'}:
            errors.append(f'{n["id"]}: invalid priority')
        for rid in n.get('resources', []):
            if rid not in resources:
                errors.append(f'{n["id"]}: unknown resource {rid}')
        for item in n.get('inputs', []):
            iid = item['id']
            if iid not in externals and iid not in outputs:
                errors.append(f'{n["id"]}: unbound input interface {iid}')
                continue
            if iid in outputs and outputs[iid][0] != n['id']:
                producer = outputs[iid][0]
                if (producer, n['id']) not in pairs:
                    errors.append(f'{n["id"]}: input {iid} lacks a dependency on {producer}')
            if iid in externals and externals[iid]['status'] not in {'SATISFIED', 'AVAILABLE', 'VERIFIED'}:
                blocked_inputs.append({'node': n['id'], 'input': iid, 'status': externals[iid]['status']})
                if n['status'] == 'READY':
                    errors.append(f'{n["id"]}: READY despite unavailable input {iid}')
        spec = n.get('specification', {})
        if spec.get('path') and not (root / spec['path']).is_file():
            errors.append(f'{n["id"]}: unavailable specification {spec["path"]}')
        if n.get('status') in {'PASS', 'COMPLETE', 'CLOSED'} and n.get('kind') != 'retained-baseline':
            errors.append(f'{n["id"]}: future work incorrectly represented as completed')
    expected = {(r['issue'], r['canonicalId'], r['id']) for r in baseline['remainingMandatory']}
    coverage = graph['coverage']
    original = [c for c in coverage if c['basis'] == 'audit-residual']
    actual = [(c['issue'], c['canonicalId'], c['obligationId']) for c in original]
    if len(actual) != len(set(actual)):
        errors.append('Duplicate audit-residual coverage rows')
    if set(actual) != expected:
        errors.append(f'Original residual coverage mismatch: missing={sorted(expected-set(actual))}; extra={sorted(set(actual)-expected)}')
    expected_issues = set(inventory['actualOpen'])
    if {c['issue'] for c in coverage} != expected_issues:
        errors.append('Issue coverage differs from frozen planning inventory')
    for c in coverage:
        for nid in c['nodeIds'] + [c['closureGate']]:
            if nid not in by_id:
                errors.append(f'Coverage {c["canonicalId"]}:{c["obligationId"]} refers to missing {nid}')
        if not c.get('acceptanceEvidence'):
            errors.append(f'Coverage lacks an acceptance artifact: {c["canonicalId"]}:{c["obligationId"]}')
    with (root / 'OBLIGATION_COVERAGE.csv').open(encoding='utf-8', newline='') as f:
        csv_rows = list(csv.DictReader(f))
    csv_keys = {(int(r['issue']), r['canonicalId'], r['obligationId'], r['basis']) for r in csv_rows}
    graph_keys = {(r['issue'], r['canonicalId'], r['obligationId'], r['basis']) for r in coverage}
    if len(csv_rows) != len(coverage) or csv_keys != graph_keys:
        errors.append('CSV coverage differs from machine graph')
    mmd = (root / 'CLOSURE_DAG.mmd').read_text(encoding='utf-8')
    # IDs are placed in explicit comment annotations, making the complete diagram
    # checkable without depending on a Mermaid renderer or label punctuation.
    diagram_nodes = set(re.findall(r'^%% NODE (\S+)$', mmd, re.M))
    diagram_edges = set(re.findall(r'^%% EDGE (\S+) (\S+) (\S+)$', mmd, re.M))
    if diagram_nodes != set(ids):
        errors.append('Human Mermaid node set differs from graph')
    if diagram_edges != edge_set:
        errors.append('Human Mermaid dependency set differs from graph')
    aliases=dict(re.findall(r'^\s+(n\d+)\["([^"<]+)<br/>[^\n]+$',mmd,re.M))
    rendered_edges=[]
    for a,kind,b in re.findall(r'^\s+(n\d+) -->\|([^|]+)\| (n\d+)$',mmd,re.M):
        rendered_edges.append((aliases.get(a,'ABSENT'),aliases.get(b,'ABSENT'),kind))
    if set(aliases.values()) != set(ids) or len(aliases)!=len(ids):
        errors.append('Rendered Mermaid nodes differ from graph')
    if set(rendered_edges)!=edge_set or len(rendered_edges)!=len(edge_set):
        errors.append('Rendered Mermaid arrows differ from graph')
    for x in graph.get('externalInputs', []):
        if x.get('contractViewsRequireReconciliation'):
            errors.append(f'Unreconciled interface views: {x["id"]}')
        for artifact in x.get('localArtifacts', []):
            if not (root / artifact).is_file():
                errors.append(f'External input {x["id"]}: unavailable artifact {artifact}')
        if x.get('status') in {'SATISFIED', 'AVAILABLE', 'VERIFIED'} and not (x.get('evidence') or x.get('localArtifacts')):
            errors.append(f'External input {x["id"]}: unsupported available status')
    for n in nodes:
        if n['kind']=='closure':
            parents=[by_id[a] for a,b in pairs if b==n['id']]
            if not any(p['kind']=='delivery' for p in parents):
                errors.append(f'{n["id"]}: closure lacks explicit actual delivery/readback gate')
        if n['kind']=='delivery':
            parents=[by_id[a] for a,b in pairs if b==n['id']]
            if not any(p['kind']=='independent-review' for p in parents):
                errors.append(f'{n["id"]}: delivery lacks independent exact-candidate review')
            if n.get('deliveryMode') in {'docs-merge','runtime-merge'} and not any(p['kind']=='authority' for p in parents):
                errors.append(f'{n["id"]}: new merge lacks separate exact-head authority')
    if graph['status'].startswith('FINAL'):
        handoff = read_json(root / 'STARTUP_HANDOFF.json')
        if handoff.get('planningHandoffStatus') != 'DEFINITE_RECEIVED_AND_RECONCILED':
            errors.append('Final graph lacks a definite reconciled startup planning handoff')
        if not handoff.get('explicitGlowDisposition'):
            errors.append('Final graph lacks explicit glow disposition')
    if graph['status'] == 'PROVISIONAL':
        warnings.append('Provisional graph: independent review and definite startup handoff may still be pending')
    return {'schemaVersion': 1, 'validationKind': 'planning structure and coverage, not product qualification',
            'graphSha256': hashlib.sha256((root / 'CLOSURE_DAG.json').read_bytes()).hexdigest(),
            'sourceTarget': graph['identities']['sourceTarget'], 'planStatus': graph['status'],
            'nodes': len(nodes), 'typedEdges': len(graph['edges']), 'originalResidualRows': len(original),
            'amendedRows': len(coverage)-len(original), 'issues': len(expected_issues),
            'topologicalOrder': topo, 'unavailableInputsExplicitlyGated': blocked_inputs,
            'errors': errors, 'warnings': warnings, 'result': 'PASS' if not errors else 'FAIL'}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    ap.add_argument('--output', type=Path)
    args = ap.parse_args()
    result = validate(args.root.resolve())
    output = args.output or args.root / 'DAG_VALIDATION.json'
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps({k: result[k] for k in ('result', 'nodes', 'typedEdges', 'originalResidualRows', 'amendedRows', 'issues', 'errors', 'warnings')}))
    raise SystemExit(0 if result['result'] == 'PASS' else 1)


if __name__ == '__main__':
    main()
