"""Planning validator mutation controls; never execute product or alter originals."""
from pathlib import Path
import copy
import importlib.util
import json
import tempfile
import re

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('validator',ROOT/'tools/validate_execution_plan.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)


def main():
    healthy=mod.validate(ROOT)
    assert healthy['result']=='PASS',healthy['errors']
    graph=json.loads((ROOT/'CLOSURE_DAG.json').read_text())
    results=[]
    cases={
        'cycle':lambda g:g['edges'].append({'from':g['topologicalOrder'][-1],'to':'INTAKE-DRIFT','type':'hard-interface','reason':'Intentional negative control'}),
        'dangling':lambda g:g['edges'].append({'from':'ABSENT','to':'INTAKE-DRIFT','type':'hard-interface','reason':'Intentional negative control'}),
        'duplicate-id':lambda g:g['nodes'].append(copy.deepcopy(g['nodes'][0])),
        'missing-obligation':lambda g:g['coverage'].pop(0),
        'unknown-interface':lambda g:g['nodes'][0]['inputs'].append({'id':'ABSENT/v1','contract':'Intentional negative control'}),
        'unavailable-ready':lambda g:g['nodes'][0].update(status='READY'),
        'missing-specification':lambda g:g['nodes'][0]['specification'].update(path='ABSENT.md'),
        'unreconciled-interface':lambda g:g['externalInputs'][0].update(contractViewsRequireReconciliation=True),
        'missing-merge-authority':lambda g:g['edges'].__setitem__(slice(None),[e for e in g['edges'] if e['type']!='authority']),
    }
    signatures={'cycle':'Cycle detected', 'dangling':'Dangling dependency', 'duplicate-id':'Duplicate node IDs',
                'missing-obligation':'Original residual coverage mismatch', 'unknown-interface':'unbound input interface',
                'unavailable-ready':'READY despite unavailable input', 'missing-specification':'unavailable specification',
                'unreconciled-interface':'Unreconciled interface views', 'missing-merge-authority':'new merge lacks separate exact-head authority'}
    with tempfile.TemporaryDirectory(prefix='rlgwo-graph-controls-') as tmp:
        root=Path(tmp)
        for filename in ('BASELINE_OBLIGATIONS.json','INVENTORY.json','OBLIGATION_COVERAGE.csv','CLOSURE_DAG.mmd','STARTUP_HANDOFF.json'):
            if (ROOT/filename).exists(): (root/filename).write_bytes((ROOT/filename).read_bytes())
        required={n['specification']['path'] for n in graph['nodes']}
        required.update(p for x in graph['externalInputs'] for p in x.get('localArtifacts',[]))
        for rel in required:
            path=root/rel;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes((ROOT/rel).read_bytes())
        for name,mutate in cases.items():
            g=copy.deepcopy(graph);mutate(g)
            (root/'CLOSURE_DAG.json').write_text(json.dumps(g))
            r=mod.validate(root)
            results.append({'control':name,'expected':'FAIL','observed':r['result'],'discriminators':r['errors']})
            assert r['result']=='FAIL',name
            assert any(signatures[name] in error for error in r['errors']), (name,r['errors'])
        (root/'CLOSURE_DAG.json').write_text(json.dumps(graph))
        original=(ROOT/'CLOSURE_DAG.mmd').read_text()
        altered=re.sub(r'(?m)^(\s+n\d+ -->\|[^|]+\| )n\d+$',r'\g<1>n999999',original,count=1)
        (root/'CLOSURE_DAG.mmd').write_text(altered)
        r=mod.validate(root)
        assert any('Rendered Mermaid arrows differ' in e for e in r['errors'])
        results.append({'control':'rendered-arrow-mismatch-with-valid-annotations','expected':'FAIL','observed':r['result'],'discriminators':r['errors']})
        (root/'CLOSURE_DAG.mmd').write_text('flowchart TD\n')
        r=mod.validate(root);assert r['result']=='FAIL'
        results.append({'control':'diagram-mismatch','expected':'FAIL','observed':r['result'],'discriminators':r['errors']})
    output={'kind':'Fresh planning-validator tests only; not product qualification','healthyResult':healthy['result'],'graphSha256':healthy['graphSha256'],'controls':results,'result':'PASS'}
    (ROOT/'DAG_NEGATIVE_CONTROLS.json').write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps({'result':'PASS','controls':len(results),'healthyGraph':healthy['graphSha256']}))


if __name__=='__main__':main()
