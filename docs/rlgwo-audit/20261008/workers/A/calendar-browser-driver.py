"""Primary-only serial consumer for the retained/adapted calendar fixture.

Importing/compiling this file does not start a server or browser. It retains
original positive oracles for three source mutations, never raises deadlines
and never waits for terrain refinement. See browser-handoff.md for provenance.
"""
import argparse, hashlib, json, os, subprocess, sys, time, traceback, urllib.request
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=Path('C:/Users/theis/.codex/worktrees/hotfix-startup-clouds/salah_widget')
NODE=Path('C:/workspace/ai/cp9-integration-20261005/toolchain/node-v22.16.0-win-x64/node.exe')
INDEX='ff728552442f4bcce7f213a089bf01d4cf70ea8d74040bdd3323768ca453beee'
F='window.__calendarFixture'

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def dump(path,value):Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
def require(ok,message):
 if not ok:raise AssertionError(message)

def one(browser,case,out,identity,binding):
 name=case['name'];folder=out/name;folder.mkdir(parents=True,exist_ok=True)
 context=browser.new_context(viewport={'width':370,'height':570},timezone_id='UTC',reduced_motion='reduce')
 page=context.new_page();errors=[];shots=[];states=[];requests=[];started=time.monotonic()
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.on('request',lambda r:requests.append(r.url))
 page.route('https://fonts.googleapis.com/**',lambda r:r.abort())
 page.route('https://fonts.gstatic.com/**',lambda r:r.abort())
 def wait(condition):page.wait_for_function(condition,polling=16,timeout=3000)
 def snap(stage):
  value=page.evaluate('()=>({state:'+F+'.snapshot(),cache:'+F+'.cache(),pending:'+F+'.pendingRequests(),paints:'+F+'.paints,settlements:'+F+'.settlements})')
  states.append({'stage':stage,'realElapsedMs':(time.monotonic()-started)*1000,**value});dump(folder/(stage+'.json'),states[-1]);return value
 def shot(stage):
  target=folder/(stage+'.png');page.locator('.c').screenshot(path=str(target),timeout=3000)
  shots.append({'stage':stage,'path':target.name,'sha256':sha(target),'scope':'Actual 325x530 product card including header/prayers/footer; controlled fixture input, no terrain-ready wait'})
 def cache8(value):
  items=[json.loads(v) for k,v in value['cache'].items() if k.startswith('salah:')]
  return len(items)==1 and items[0]['date']=='08-09-2026'
 expected_error={'no-promotion-control':'promotion accepted date','unconditional-next-control':'late callback never puts current into tomorrow','no-dirty-control':'first resumed frame paints current'}
 result={'name':name,'browser':identity,'binding':binding,'status':'RUNNING','expected':expected_error.get(name,'all original positive oracles'), 'instrumentation':'Fixed wall clock, per-document Map storage, controlled fetch/visibility; actual admission/adoption/render/rAF. Transparent prefetch-settlement observer adds one microtask before existing finally, no direct render or admitted-state injection.'}
 try:
  page.goto(case['url'],wait_until='domcontentloaded',timeout=15000)
  wait('!!'+F+'?.snapshot && '+F+'.snapshot().loopStarted && '+F+'.snapshot().today?.date==="07-09-2026" && '+F+'.snapshot().rows===6')
  if name in ['completed-offline','no-promotion-control']:
   wait(F+'.snapshot().tomorrow?.date==="08-09-2026"');before=snap('before');shot('before')
   require('1448-02-20' in before['state']['ah'],'before-midnight AH20')
   page.evaluate('()=>{const f='+F+'; f.setOffline(true);f.setInstant("2026-09-08T00:00:01Z");}')
   wait(F+'.paints.some(p=>p.utcMs===Date.parse("2026-09-08T00:00:01Z"))');after=snap('after');shot('after')
   require(after['state']['today']['date']=='08-09-2026','promotion accepted date')
   require(after['state']['lastDate']=='08-09-2026' and after['state']['stale'] is False and cache8(after),'promotion accepted marker/cache/stale')
   require('2026-09-08' in after['state']['ce'] and '1448-02-20' in after['state']['ah'] and after['state']['rows']==6,'promotion actual dates and six rows')
  else:
   wait(F+'.pendingRequests().length===1');snap('before');shot('before')
   page.evaluate('()=>'+F+'.setInstant("2026-09-08T00:00:01Z")')
   wait(F+'.pendingRequests().length===2 && '+F+'.paints.some(p=>p.utcMs===Date.parse("2026-09-08T00:00:01Z")&&p.stale)')
   stale=snap('midnight-stale')
   if name in ['late-duplicate','unconditional-next-control']:
    page.evaluate('()=>{const f='+F+';f.releasePending(1,Object.assign(structuredClone(f.tomorrow),{tag:"day8-winner"}));}')
    wait(F+'.snapshot().today?.tag==="day8-winner" && '+F+'.paints.at(-1).today?.tag==="day8-winner"')
    winner=snap('winner');shot('winner');count=len(winner['settlements'])
    page.evaluate('()=>'+F+'.releasePending(0)');wait(F+'.settlements.length>'+str(count))
    late=snap('late-release');shot('late-release')
    relevant=late['settlements'][count:]
    require(all(p.get('tomorrow') is None or p['tomorrow']['date']!='08-09-2026' for p in relevant),'late callback never puts current into tomorrow')
    require(late['state']['today']['tag']=='day8-winner' and late['cache']==winner['cache'],'late callback preserves winner/cache')
    wait(F+'.snapshot().tomorrow?.date==="09-09-2026"')
    page.evaluate('()=>'+F+'.setInstant("2026-09-08T18:01:00Z")')
    wait(F+'.snapshot().ah.includes("1448-02-21")');next_day=snap('next-maghrib');shot('next-maghrib')
    require(next_day['state']['dateTruth']['selectedSource']=='tomorrow','next-Maghrib correct day source')
   else:
    page.evaluate('()=>{const f='+F+';f.setVisibility(true);f.setOffline(true);f.failPending(1);f.releasePending(0);}')
    wait(F+'.snapshot().today?.date==="08-09-2026" && !'+F+'.snapshot().stale')
    hidden=snap('hidden-adoption');shot('hidden-adoption')
    require(hidden['state']['dirty'] is True and cache8(hidden),'hidden accepted state marked dirty/cache')
    require(hidden['state']['utcMs']==stale['state']['utcMs'] and hidden['state']['ce']==stale['state']['ce'],'hidden same-second old DOM')
    resumed=page.evaluate('async()=>{const f='+F+';const index=f.paints.length;f.setVisibility(false);await new Promise(requestAnimationFrame);return {index,first:f.paints[index]??null,utcMs:f.snapshot().utcMs};}')
    states.append({'stage':'first-resumed-frame','observation':resumed});dump(folder/'first-resumed-frame.json',resumed);shot('first-resumed-frame')
    first=resumed['first'];require(first is not None and first['today']['date']=='08-09-2026' and first['stale'] is False and '2026-09-08' in first['ce'] and '1448-02-20' in first['ah'],'first resumed frame paints current')
    require(resumed['utcMs']==stale['state']['utcMs'],'first resumed frame keeps fixed second')
    before_count=len(page.evaluate('()=>'+F+'.effects().requests'))
    page.evaluate('async()=>{for(let i=0;i<20;i++)await new Promise(requestAnimationFrame);}')
    final=snap('twenty-more-frames');shot('twenty-more-frames')
    require(final['state']['today']['date']=='08-09-2026' and final['state']['rows']==6 and not final['state']['stale'],'twenty frames preserve adopted consumer')
    require(len(final['state']['effects']['requests'])-before_count<=2,'no per-frame redundant acquisition')
  require(not errors,'unexpected browser runtime errors')
  if name in expected_error:raise AssertionError('Original oracle did not detect designated source mutation')
  result['status']='PASS'
 except AssertionError as e:
  result['error']=str(e)
  if name in expected_error and str(e)==expected_error[name]:result['status']='EXPECTED_FAILURE';result['originalOraclePreserved']=True
  else:result['status']='FAIL'
 except Exception:
  result.update(status='FAIL',error=traceback.format_exc())
 finally:
  try:snap('terminal');shot('terminal')
  except Exception as e:result['terminalCaptureError']=str(e)
  result.update(pageErrors=errors,states=states,captures=shots,requests=requests,realSeconds=time.monotonic()-started)
  if errors:result['status']='FAIL'
  dump(folder/'results.json',result);context.close()
 return result

def run(args):
 require(sha(ROOT/'index.html')==INDEX,'Exact root identity before run');args.output.mkdir(parents=True,exist_ok=True)
 server=None;results=[];origin=args.origin
 try:
  if not origin:
   flags=subprocess.CREATE_NO_WINDOW if sys.platform=='win32' else 0
   server=subprocess.Popen([str(NODE),str(HERE/'calendar-browser-adapter.cjs'),'--serve'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,creationflags=flags)
   startup=json.loads(server.stdout.readline());origin=startup['origin'];require(startup['sourceSha256']==INDEX,'Server source identity')
  with urllib.request.urlopen(origin+'/cases.json',timeout=5) as response:cases=json.load(response)
  preparation=json.loads((HERE/'calendar-browser-preparation.json').read_text(encoding='utf-8'));by_name={c['name']:c for c in preparation['cases']}
  os.environ['SALAH_BROWSER']=args.engine;sys.path.insert(0,str(ROOT/'tools/cp9'))
  from browser_runtime import launch_browser,browser_identity
  from playwright.sync_api import sync_playwright
  with sync_playwright() as pw:
   browser=launch_browser(pw);identity=browser_identity(browser)
   for case in cases:
    with urllib.request.urlopen(case['url'],timeout=5) as response:actual=hashlib.sha256(response.read()).hexdigest()
    require(actual==by_name[case['name']]['fixtureSha256'],'Exact served fixture identity')
    results.append(one(browser,case,args.output,identity,by_name[case['name']]));print(case['name'],results[-1]['status'],round(results[-1]['realSeconds'],2),flush=True)
   browser.close()
 finally:
  if server:server.terminate();server.wait(timeout=5)
 result={'schema':'bounded-calendar-browser-results/1','status':'PASS' if len(results)==6 and all(r['status'] in ['PASS','EXPECTED_FAILURE'] for r in results) else 'FAIL','targetCommit':'18ff14860ff41c084b1db5f396bb62aa9c22b1be','sourceSha256':INDEX,'sourceUnchanged':sha(ROOT/'index.html')==INDEX,'driverSha256':sha(__file__),'adapterSha256':sha(HERE/'calendar-browser-adapter.cjs'),'cases':results,'scope':'Primary serial actual-card browser readback. No terrain-ready wait, no live provider or OS visibility proof, no deadline changes; all six exact positive/mutation expectations retained.'}
 if not result['sourceUnchanged']:result['status']='FAIL'
 dump(args.output/'results.json',result);return result['status']=='PASS'

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--engine',choices=['chromium','firefox','webkit'],default='chromium');p.add_argument('--origin');args=p.parse_args();raise SystemExit(0 if run(args) else 1)
