"""Read every approved runtime body from Pages; retain exact bytes for native file consumers."""
from pathlib import Path
import concurrent.futures, datetime, hashlib, json, subprocess, urllib.request
D=Path(__file__).resolve().parent
R=Path(r'${REPO_ROOT}')
M='f71fef6ccf7e4efcb57b5a26688d2360461a3253'
H='ec53e1a3778f2f73054253a2a28795873f48364c'
B='f270792f39ef8bf4cabffbe6746ac0ea0dd9d3de'
T='79aedcac840d624b5ea423922314f0832dc3f750'
URL='https://theislampill.github.io/salah_widget/'
RUN=39670161254
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def api(p):return json.loads(subprocess.check_output([r'${GITHUB_CLI}\gh.exe','api','repos/theislampill/salah_widget/'+p]))
def main():
 out=D/'served-runtime.json';assert not out.exists()
 expected=json.loads((R/'docs/real-sky/evidence/r0021-terminal-20261021/r127/builds/integrated-r31-file-transport/RUNTIME.json').read_bytes())
 run=api('actions/runs/'+str(RUN));build=api('pages/builds/latest');pages=api('pages');commit=api('git/commits/'+M)
 assert run['head_sha']==M and run['status']=='completed' and run['conclusion']=='success' and build['commit']==M and build['status']=='built'
 assert api('git/ref/heads/main')['object']['sha']==M and pages['source']=={'branch':'main','path':'/'}
 assert [p['sha'] for p in commit['parents']]==[B,H] and commit['tree']['sha']==T
 report={'schema':'r0021-delivered-pages-runtime/v1','startedAtUtc':now(),'merge':M,'approvedHead':H,'approvedBase':B,'tree':T,'expectedRuntime':expected['treeSha256'],'expectedFileCount':len(expected['files']),'pagesRun':{k:run[k] for k in ['id','head_sha','status','conclusion','html_url','created_at','updated_at']},'pagesBuild':{k:build[k] for k in ['commit','status','duration','created_at','updated_at','error']},'pages':{k:pages[k] for k in ['html_url','status','source','build_type']},'files':[],'errors':[]}
 served=D/'served';assert not served.exists();served.mkdir()
 def get(item):
  path,want=item;url=URL+path+'?r0021_delivery='+M;h=hashlib.sha256();count=0
  target=served/path;target.parent.mkdir(parents=True,exist_ok=True)
  with urllib.request.urlopen(urllib.request.Request(url,headers={'Cache-Control':'no-cache','Accept-Encoding':'identity'}),timeout=90) as response, target.open('xb') as file:
   assert response.status==200
   while True:
    block=response.read(1024*1024)
    if not block:break
    file.write(block);h.update(block);count+=len(block)
   row={'path':path,'url':url,'bytes':count,'sha256':h.hexdigest(),'status':response.status,'etag':response.headers.get('ETag'),'observedAtUtc':now()}
  row['match']=count==want['bytes'] and row['sha256']==want['sha256'];return row
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
  futures={pool.submit(get,item):item[0] for item in expected['files'].items()}
  for future in concurrent.futures.as_completed(futures):
   try:report['files'].append(future.result())
   except Exception as e:report['errors'].append({'path':futures[future],'error':repr(e)})
   if len(report['files'])%25==0:print(json.dumps({'servedFiles':len(report['files'])}),flush=True)
 # Preserve the completed runtime sweep even if a later protected read fails.
 out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 try:
  with urllib.request.urlopen(URL,timeout=60) as response:
   body=response.read();report['plainEntry']={'url':URL,'status':response.status,'bytes':len(body),'sha256':hashlib.sha256(body).hexdigest()}
 except Exception as e:report['errors'].append({'path':'plain entry','error':repr(e)})
 report['protectedPublicEntries']=[]
 for path in ['presets/salah-widget.tablissng.json','v1/index.html','v1/config.js','v1/builder.html']:
  try:
   want=(R/path).read_bytes();row=get((path,{'bytes':len(want),'sha256':hashlib.sha256(want).hexdigest()}));report['protectedPublicEntries'].append(row)
  except Exception as e:report['errors'].append({'path':path,'error':repr(e)})
 report['files'].sort(key=lambda x:x['path']);report['completedAtUtc']=now()
 try:report['mainAfter']=api('git/ref/heads/main')['object']['sha']
 except Exception as e:report['errors'].append({'path':'main after','error':repr(e)})
 report['observedRuntime']=hashlib.sha256(''.join(f"{r['sha256']}  {r['path']}\n" for r in report['files']).encode()).hexdigest()
 report['allMatch']=not report['errors'] and len(report['files'])==142 and len(report['protectedPublicEntries'])==4 and all(r['match'] for r in report['files']+report['protectedPublicEntries']) and report['observedRuntime']==expected['treeSha256'] and report.get('plainEntry',{}).get('sha256')==expected['files']['index.html']['sha256'] and report.get('mainAfter')==M
 out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'files':len(report['files']),'allMatch':report['allMatch'],'runtime':report['observedRuntime'],'errors':report['errors']}));assert report['allMatch']
if __name__=='__main__':main()
