"""Derive structural paths and resource demand; not a wall-clock ETA."""
from pathlib import Path
import collections
import json

ROOT=Path(__file__).resolve().parents[1]


def main():
    g=json.loads((ROOT/'CLOSURE_DAG.json').read_text())
    by={n['id']:n for n in g['nodes']};parents=collections.defaultdict(set)
    for e in g['edges']:parents[e['to']].add(e['from'])
    best={};paths={};resource=collections.defaultdict(lambda:[0,0])
    def hours(n):
        a=n['estimate'].get('activeHours')
        return a if isinstance(a,list) and len(a)==2 and all(isinstance(x,(int,float)) for x in a) else [0,0]
    for nid in g['topologicalOrder']:
        n=by[nid];h=hours(n)
        best[nid]=[];paths[nid]=[]
        for side in (0,1):
            p=max(parents[nid],key=lambda x:best[x][side]) if parents[nid] else None
            best[nid].append(h[side]+(best[p][side] if p else 0))
            paths[nid].append((paths[p][side] if p else [])+[nid])
        for r in n['resources']:
            a=n['estimate'].get('exclusiveMachineMinutes',[0,0]) if r=='heavy-browser' else h
            if isinstance(a,list) and len(a)==2 and all(isinstance(x,(int,float)) for x in a):
                resource[r]=[resource[r][i]+a[i] for i in (0,1)]
    critical=[]
    for side in (0,1):
        last=max(by,key=lambda x:best[x][side])
        critical.append({'estimateBound':'lower' if side==0 else 'upper','activeHours':best[last][side],'nodes':paths[last][side]})
    first=[n['id'] for n in g['nodes'] if n['id']!='INTAKE-DRIFT' and parents[n['id']] <= {'INTAKE-DRIFT'}]
    output={'scope':'Structural active-work paths only. Owner/platform waiting is unknown; shared proof can reduce demand, failures can increase it. Not a mathematically optimal or elapsed-time promise.',
            'criticalStructuralPaths':critical,'resourceDemand':{r:{'range':v,'unit':'exclusive minutes' if r=='heavy-browser' else 'active hours; shared node may hold multiple resources'} for r,v in resource.items()},
            'firstGraphReadyAfterIntake':first,'externalGates':[{'id':x['id'],'status':x['status']} for x in g['externalInputs'] if x['status'] not in {'SATISFIED','AVAILABLE','VERIFIED'}],
            'serialQueueRule':'Startup lease first; then risk-ranked actual ready nodes. Do not start costly browser/terrain/performance work without exclusive release/lease.'}
    (ROOT/'SCHEDULE.json').write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps({'critical':critical,'firstWaveNodes':len(first),'heavyDemand':output['resourceDemand'].get('heavy-browser')}))


if __name__=='__main__':main()
