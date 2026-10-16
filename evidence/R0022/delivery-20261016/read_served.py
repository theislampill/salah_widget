"""Read every approved runtime body from deployed Pages; no product mutation."""
from pathlib import Path
import concurrent.futures,datetime,hashlib,json,subprocess,urllib.request
D=Path(__file__).resolve().parent;O=D.parent;M='f270792f39ef8bf4cabffbe6746ac0ea0dd9d3de';URL='https://theislampill.github.io/salah_widget/'
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def api(p):return json.loads(subprocess.check_output(['gh','api','repos/theislampill/salah_widget/'+p]))
def main():
 out=D/'served-runtime.json';assert not out.exists()
 expected=json.loads((O/'selected-r7/RUNTIME.json').read_bytes());run=api('actions/runs/38932765174');build=api('pages/builds/latest');pages=api('pages')
 assert run['head_sha']==M and run['status']=='completed'and run['conclusion']=='success'and build['commit']==M and build['status']=='built'
 assert api('git/ref/heads/main')['object']['sha']==M and pages['source']=={'branch':'main','path':'/'}
 report={'startedAtUtc':now(),'merge':M,'expectedRuntime':expected['treeSha256'],'pagesRun':{k:run[k]for k in ['id','head_sha','status','conclusion','html_url','created_at','updated_at']},'pagesBuild':build,'pages':{k:pages[k]for k in ['html_url','status','source','build_type']},'files':[],'errors':[]}
 def get(item):
  path,want=item;url=URL+path+'?r0022_delivery='+M;h=hashlib.sha256();count=0
  with urllib.request.urlopen(urllib.request.Request(url,headers={'Cache-Control':'no-cache','Accept-Encoding':'identity'}),timeout=60)as r:
   assert r.status==200
   while True:
    block=r.read(1024*1024)
    if not block:break
    h.update(block);count+=len(block)
   row={'path':path,'url':url,'bytes':count,'sha256':h.hexdigest(),'status':r.status,'etag':r.headers.get('ETag'),'observedAtUtc':now()}
  row['match']=count==want['bytes']and row['sha256']==want['sha256'];return row
 with concurrent.futures.ThreadPoolExecutor(max_workers=4)as pool:
  for f in concurrent.futures.as_completed([pool.submit(get,item)for item in expected['files'].items()]):
   try:report['files'].append(f.result())
   except Exception as e:report['errors'].append(repr(e))
   if len(report['files'])%25==0:print(json.dumps({'servedFiles':len(report['files'])}),flush=True)
 with urllib.request.urlopen(URL,timeout=60)as response:b=response.read();report['plainEntry']={'url':URL,'status':response.status,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
 report['files'].sort(key=lambda x:x['path']);report['completedAtUtc']=now();report['mainAfter']=api('git/ref/heads/main')['object']['sha']
 report['observedRuntime']=hashlib.sha256(''.join(f"{r['sha256']}  {r['path']}\n"for r in report['files']).encode()).hexdigest()
 report['allMatch']=not report['errors']and len(report['files'])==len(expected['files'])and all(r['match']for r in report['files'])and report['observedRuntime']==expected['treeSha256']and report['plainEntry']['sha256']==expected['files']['index.html']['sha256']and report['mainAfter']==M
 out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({'files':len(report['files']),'allMatch':report['allMatch'],'runtime':report['observedRuntime']}));assert report['allMatch']
if __name__=='__main__':main()
