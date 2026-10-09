"""Preparation only: primary runs native keyboard checks with existing Playwright."""
import argparse, hashlib, json, pathlib, subprocess, sys, time, traceback
from urllib.parse import parse_qs, urlparse

HERE=pathlib.Path(__file__).resolve().parent
ROOT=pathlib.Path('C:/Users/theis/.codex/worktrees/hotfix-startup-clouds/salah_widget')
NODE='C:/workspace/ai/cp9-integration-20261005/toolchain/node-v22.16.0-win-x64/node.exe'
sys.path.insert(0,str(ROOT/'tools/cp9'))
from browser_runtime import launch_browser, browser_identity
from playwright.sync_api import sync_playwright

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--out',required=True);args=parser.parse_args()
 out=pathlib.Path(args.out).resolve();out.mkdir(parents=True,exist_ok=False)
 result={'target':'18ff14860ff41c084b1db5f396bb62aa9c22b1be','indexSha256':digest(ROOT/'index.html'),
  'sourceBuilderSha256':digest(ROOT/'builder.html'),'driverSha256':digest(pathlib.Path(__file__)),
  'fixtureSha256':digest(HERE/'native-radio-fixture.cjs'),'cases':[],
  'scope':'Actual native keys/default actions and current builder output; per-document private storage/null coarse detection. Sky iframe response is blank; no rendered widget/terrain claim. Remote fonts blocked and their state reported; focus crops use actual native CSS.'}
 assert result['indexSha256']=='ff728552442f4bcce7f213a089bf01d4cf70ea8d74040bdd3323768ca453beee'
 server=subprocess.Popen([NODE,str(HERE/'native-radio-fixture.cjs'),str(out)],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 try:
  binding=json.loads(server.stdout.readline());result['server']=binding
  assert binding['sourceBuilderSha256']==result['sourceBuilderSha256']
  with sync_playwright() as pw:
   browser=launch_browser(pw);result['browser']=browser_identity(browser)
   try:
    for label,width,height in [('mobile',375,800),('desktop',1100,900)]:
     context=browser.new_context(viewport={'width':width,'height':height},device_scale_factor=1)
     context.route('**/*',lambda route:route.continue_() if urlparse(route.request.url).netloc==urlparse(binding['origin']).netloc else route.abort())
     try:
      for mutant in ['', 'arrows','tabindex']:
       page=context.new_page();errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
       case={'name':label+'-'+(mutant or 'healthy'),'viewport':{'width':width,'height':height},'mutant':mutant,'steps':[],'pageErrors':errors,'status':'INCOMPLETE'}
       result['cases'].append(case)
       def snap(step):
        value=page.evaluate('window.__radioFixture.snapshot()');case['steps'].append({'step':step,'observed':value});return value
       def selected(value,mode,focus=False):
        assert value['mode']==mode,'embedMode expected '+mode
        if focus:assert value['focus']=='mode-'+mode,'selected focus expected mode-'+mode
        for b in value['buttons']:
         yes=b['id']=='mode-'+mode
         assert b['checked']==str(yes).lower(),b['id']+' checked state'
         assert b['active']==yes,b['id']+' active state'
         assert b['tabIndex']==(0 if yes else -1),b['id']+' tabIndex must follow selected state'
        expected='1' if mode=='local' else None
        for key in ['iframeHash','codeHash']:assert parse_qs(value[key].lstrip('#')).get('local',[None])[0]==expected,key+' local flag'
        assert value['iframeAllow']==('geolocation' if mode=='local' else ''),'iframe delegation'
        assert ('allow="geolocation"' in value['code'])==(mode=='local'),'snippet delegation'
        assert 'width:325px;height:530px' in value['code'],'preserved current snippet dimensions'
       def change(key,mode):
        before=snap('before '+key);page.keyboard.press(key);after=snap('native '+key)
        selected(after,mode,True);assert after['revision']==before['revision']+1,key+' updates once';return after
       try:
        page.goto(binding['routes'][mutant or 'healthy'],wait_until='domcontentloaded')
        page.wait_for_function('window.__radioFixture && typeof window.__radioFixture.snapshot==="function"',timeout=8000)
        page.evaluate('new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')
        selected(snap('initial'),'portable');assert not errors,'bootstrap cannot count as native proof'
        if mutant:
         page.locator('#mode-portable').focus();before=snap('mutant before Right');page.keyboard.press('ArrowRight');after=snap('mutant native Right')
         caught=None
         try:selected(after,'local',True);assert after['revision']==before['revision']+1,'Right updates once'
         except AssertionError as e:caught=str(e)
         assert caught is not None,'mutant escaped original Right-arrow assertions'
         if mutant=='arrows':assert 'focus expected' in caught or 'embedMode expected' in caught,'wrong arrow discriminator: '+caught
         else:assert 'tabIndex' in caught,'wrong tabindex discriminator: '+caught
         assert not errors,'script/bootstrap error is not mutation detection'
         case.update(status='PASS',negativeControlDetected=True,discriminator=caught)
         continue
        # Native Tab entry from the preceding enabled tab stop in real DOM order.
        preceding=page.evaluate('''()=>{const a=[...document.querySelectorAll('button,input,select,textarea,a[href],iframe,[tabindex]')].filter(e=>e.tabIndex>=0&&!e.disabled&&e.getBoundingClientRect().width&&e.getBoundingClientRect().height);const i=a.findIndex(e=>e.id==='mode-portable');if(i<1)throw Error('No preceding native tab stop');a[i-1].focus();return a[i-1].id;}''')
        page.keyboard.press('Tab');selected(snap('Tab entry from '+preceding),'portable',True)
        for key,mode in [('ArrowRight','local'),('ArrowRight','portable'),('ArrowLeft','local'),('ArrowUp','portable'),('ArrowDown','local')]:change(key,mode)
        before=snap('before Tab exit');page.keyboard.press('Tab');after=snap('Tab exit')
        assert after['focus'] not in ['mode-portable','mode-local'],'Tab must leave the one-stop group';selected(after,'local');assert after['revision']==before['revision']
        page.keyboard.press('Shift+Tab');after=snap('Shift+Tab entry');selected(after,'local',True);assert after['revision']==before['revision']
        # Enter and complete Space press preserve native activation: exactly one update.
        for key in ['Enter','Space']:change(key,'local')
        before=snap('before click');page.locator('#mode-portable').click();after=snap('click portable');selected(after,'portable');assert after['revision']==before['revision']+1
        for mode in ['local','portable']:
         before=snap('before programmatic '+mode);page.evaluate('(mode)=>setMode(mode)',mode);after=snap('programmatic '+mode);selected(after,mode);assert after['revision']==before['revision']+1
        page.evaluate('document.getElementById("mode-portable").disabled=true;setMode("portable")');selected(snap('disabled portable fallback'),'local')
        page.locator('#mode-local').focus();change('ArrowRight','local')
        page.evaluate('document.getElementById("mode-local").disabled=true;setMode("local")');before=snap('none enabled')
        assert all(b['checked']=='false' and not b['active'] and b['tabIndex']==-1 for b in before['buttons']),'none enabled must expose no selected tab stop'
        page.evaluate('document.getElementById("mode-local").dispatchEvent(new KeyboardEvent("keydown",{key:"ArrowRight",bubbles:true,cancelable:true}))')
        after=snap('safe disabled synthetic boundary');assert after['revision']==before['revision']
        page.evaluate('document.getElementById("mode-portable").disabled=false;document.getElementById("mode-local").disabled=false;setMode("local");const s=document.createElement("span");s.id="audit-unrelated";s.tabIndex=0;document.querySelector(".modebtns").appendChild(s);s.focus()')
        before=snap('unrelated target before');page.keyboard.press('ArrowRight');after=snap('unrelated target native Right');assert after['revision']==before['revision'];selected(after,'local')
        page.evaluate('document.getElementById("audit-unrelated").remove();setMode("portable")')
        # Re-enter through native Tab to force :focus-visible and inspect its real crop.
        page.evaluate('''()=>{const a=[...document.querySelectorAll('button,input,select,textarea,a[href],iframe,[tabindex]')].filter(e=>e.tabIndex>=0&&!e.disabled&&e.getBoundingClientRect().width&&e.getBoundingClientRect().height);a[a.findIndex(e=>e.id==='mode-portable')-1].focus();}''')
        page.keyboard.press('Tab');focused=snap('native focus crop');selected(focused,'portable',True)
        focus=next(b for b in focused['buttons'] if b['id']=='mode-portable');assert focus['focusVisible'],'native keyboard focus must be visible';assert '2px' in focus['outline'],'actual 2px focus outline'
        page.locator('.modebtns').scroll_into_view_if_needed();box=page.locator('.modebtns').bounding_box();assert box
        clip={'x':max(0,box['x']-5),'y':max(0,box['y']-5),'width':min(width-max(0,box['x']-5),box['width']+10),'height':box['height']+10}
        page.screenshot(path=str(out/(label+'-focus.png')),clip=clip);page.screenshot(path=str(out/(label+'-builder.png')),full_page=True)
        assert not errors,'all healthy native cases must complete without page error';case['status']='PASS'
       except Exception as e:
        case.update(status='FAIL',error=str(e),traceback=traceback.format_exc());raise
       finally:page.close()
     finally:context.close()
   finally:browser.close()
  assert len(result['cases'])==6 and all(c['status']=='PASS' for c in result['cases'])
  result['status']='PASS'
 except Exception as e:
  result.update(status='FAIL',error=str(e));raise
 finally:
  server.terminate()
  try:server.wait(timeout=5)
  except subprocess.TimeoutExpired:server.kill();server.wait(timeout=5)
  (out/'results.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
  print(json.dumps({'status':result.get('status','INCOMPLETE'),'cases':len(result['cases']),'output':str(out),'browser':result.get('browser'),'scope':result['scope']}),flush=True)
if __name__=='__main__':main()
