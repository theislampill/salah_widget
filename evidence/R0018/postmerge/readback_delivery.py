"""Read immutable published delivery objects and verify the complete path mapping."""
from pathlib import Path
import concurrent.futures, gzip, hashlib, json, subprocess, sys, urllib.request
sys.path.insert(0,str(Path(__file__).resolve().parent))
from delivery_control import HERE,REPO,api,sha,now,record
COMMIT='86194dc467a27591b6e1d2510da2dff30ade927f'
PREFIX='evidence/R0018/postmerge/'

def main():
    started=now();p=HERE/'publication-manifest.json';data=p.read_bytes();manifest=json.loads(data)
    rows=manifest['files']+[{'original':'publication-manifest.json','published':'publication-manifest.json','originalBytes':len(data),'originalSha256':sha(data),'publishedBytes':len(data),'publishedSha256':sha(data),'encoding':'identity'}]
    commit=api('git/commits/'+COMMIT);tree=api('git/trees/'+commit['tree']['sha']+'?recursive=1')
    assert not tree.get('truncated') and tree['sha']==commit['tree']['sha']
    objects={o['path']:o for o in tree['tree'] if o['type']=='blob' and o['path'].startswith(PREFIX)}
    assert set(objects)=={PREFIX+r['published'] for r in rows}
    groups={}
    for row in rows:
        raw=(HERE/row['published']).read_bytes();obj=objects[PREFIX+row['published']]
        assert obj['sha']==hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
        assert obj['size']==len(raw) and sha(raw)==row['publishedSha256']
        groups.setdefault((row['publishedSha256'],row['encoding'],row['originalSha256']),[]).append(row)
    def fetch(group):
        row=group[0];url='https://raw.githubusercontent.com/'+REPO+'/'+COMMIT+'/'+PREFIX+row['published']
        result={'url':url,'published':row['published'],'sameObjectPaths':[r['published'] for r in group]}
        try:
            request=urllib.request.Request(url,headers={'Accept-Encoding':'identity','User-Agent':'R0018-delivery-evidence-readback'})
            with urllib.request.urlopen(request,timeout=45) as response:status=response.status;wire=response.read()
            raw=gzip.decompress(wire) if row['encoding']=='gzip' else wire
            result.update(httpStatus=status,publishedBytes=len(wire),publishedSha256=sha(wire),originalBytes=len(raw),originalSha256=sha(raw))
            result['passed']=status==200 and all(result[k]==row[k] for k in ('publishedBytes','publishedSha256','originalBytes','originalSha256'))
        except Exception as exc:result.update(passed=False,error=repr(exc))
        return result
    results=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for item in pool.map(fetch,groups.values()):
            results.append(item)
            if len(results)%40==0:print(json.dumps({'read':len(results),'failed':sum(not r['passed'] for r in results)}),flush=True)
    report={'schema':'r0018-public-delivery-evidence-readback/v1','startedUtc':started,'finishedUtc':now(),'commit':COMMIT,'actualTreeSha':commit['tree']['sha'],
            'driverSha256':sha(Path(__file__).read_bytes()),'manifestSha256':sha(data),'pathsVerified':len(rows),'distinctHttpObjects':len(results),
            'scope':'Every published path/blob matches the complete immutable remote tree. Each distinct content/decoding object read once; aliases explicit. Gzip independently decoded and hashed.',
            'passed':all(r['passed'] for r in results),'failures':[r for r in results if not r['passed']],'results':results}
    record('publication-readback.json',report)
    print(json.dumps({k:report[k] for k in ('commit','pathsVerified','distinctHttpObjects','passed')}),flush=True)
    if not report['passed']:raise SystemExit(1)

if __name__=='__main__':main()
