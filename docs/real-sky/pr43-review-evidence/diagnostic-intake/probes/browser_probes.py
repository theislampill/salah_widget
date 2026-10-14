#!/usr/bin/env python3
"""Independent PR43 source-extracted / structural browser checks.
Not a complete widget rerun. No production services, profiles or files are edited.
The delayed font is a local test font under the target family name, not Fraunces.
"""
import argparse, asyncio, json, hashlib, shutil
from datetime import datetime, timezone
from pathlib import Path
from playwright.async_api import async_playwright
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--native-source', type=Path, help='Optional actual authored src/native/index.html for a source-bound rerun')
parser.add_argument('--chromium', default=shutil.which('chromium') or shutil.which('google-chrome'), help='Installed Chromium/Chrome executable')
parser.add_argument('--font-local', default='DejaVu Sans Mono', help='Installed controlled test font; no font files are bundled')
args=parser.parse_args()
if not args.chromium:
 raise SystemExit('Supply --chromium with an installed executable; this probe does not install browsers.')
if args.native_source:
 text=args.native_source.read_text(encoding='utf-8')
 BOOT=text[text.index('async function boot(){'):text.index('// SINGLE rAF render clock')]
 FIT='let _cnFit="";\n'+text[text.index('function fitCn('):text.index('// PROCEDURAL BRANCHING LIGHTNING')]
else:
 BOOT=(ROOT/'source-excerpts/boot.js').read_text()
 FIT=(ROOT/'source-excerpts/fitCn.js').read_text()
STATE_JS='''
window.obs={settings:false,scene:false,weather:0,radar:0,prayer:0,loop:false};
window._runtimeGeneration=0;window._cfgMode='local';window.QA=false;
window.lat=28.54;window.lon=-81.38;
window.enableSettingsAffordance=()=>{obs.settings=true};
window.beginSkyScene=()=>{};window.simulationReady=()=>true;
window.buildSceneOnce=()=>{};window.renderMoon=()=>{};
window.fetchWeather=()=>{obs.weather++};window.fetchRadar=()=>{obs.radar++};
window.startWeather=(defer=false)=>{if(!defer){fetchWeather();fetchRadar()}};
window.render=()=>{obs.scene=true};window.SalahSkyPreview={update(){}};
window.loadPrayerData=async()=>{obs.prayer++};window.startRenderLoop=()=>{obs.loop=true};
'''
BASE_BOOT='''async function boot(){const generation=_runtimeGeneration;
enableSettingsAffordance();beginSkyScene();buildSceneOnce();renderMoon();
startWeather();render();window.SalahSkyPreview?.update();
await loadPrayerData();if(generation!==_runtimeGeneration)return;startRenderLoop();}'''
PREFIX=b'<!doctype html><html><head><style>.card{width:325px;height:530px;background:#273445;color:white}</style><script>window.headSkyPrepared=true;</script></head><body><div class="card">Structural loading-order probe (not the widget)</div>'

async def main():
 results={'capturedUtc':datetime.now(timezone.utc).isoformat(),'reviewedPRHead':'f0647b44e10c9ce4f80895b52861893c347512fd','reviewedHead':'e3b042f17048fce8577cd08140f306cbce2d7f3c','scope':'source-extracted and structural probes, NOT full runtime tests; document.write models streamed parser ordering; no network throughput measurement','sourceNativeBlob':'767798bacee5c38641bac691a29a60cc399c2c62','sourceMethod':'actual authored file slices' if args.native_source else 'manually transcribed function excerpts, comments omitted; connected head source inspected','fullSourceSha256':hashlib.sha256(args.native_source.read_bytes()).hexdigest() if args.native_source else None,'probeSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'sources':{n:hashlib.sha256((ROOT/'source-excerpts'/n).read_bytes()).hexdigest() for n in ['boot.js','fitCn.js']}}
 async with async_playwright() as p:
  browser=await p.chromium.launch(executable_path=args.chromium,headless=True)
  results['browser']=browser.version
  ctx=await browser.new_context(viewport={'width':500,'height':650})
  # Structural delivery-order comparison: hold the trailing Moon bytes, NOT
  # a fake sleep in product JavaScript. Inspect from the parent/session.
  streams=[]
  for mode in ('baseline','candidate'):
   page=await ctx.new_page()
   if mode=='candidate':
    prefix=PREFIX.decode()+'<script>'+STATE_JS+BOOT+'\nconst inlineInitial="'+'A'*32768
    suffix='A'*200000+'";window.inlineInitialReady=true;boot();</script></body></html>'
   else:
    prefix=PREFIX.decode()+'<script>'+STATE_JS+BASE_BOOT+'\nboot();</script>'
    suffix='<script>window.externalMoonReady=true;</script></body></html>'
   await page.evaluate('(html)=>{document.open();document.write(html)}',prefix)
   await page.wait_for_timeout(250)
   before=await page.evaluate('({sky:headSkyPrepared,cardVisible:document.querySelector(".card").getBoundingClientRect().height>0,mainExecuted:!!window.obs,obs:window.obs??null})')
   await page.evaluate('(html)=>{document.write(html);document.close()}',suffix)
   await page.wait_for_function('window.obs?.loop===true')
   after=await page.evaluate('obs');streams.append({'mode':mode,'whileMoonTailWithheld':before,'afterRelease':after})
   await page.close()
  results['streamingOrder']=streams
  assert streams[0]['whileMoonTailWithheld']['obs']['prayer']==1
  assert streams[1]['whileMoonTailWithheld']['mainExecuted'] is False
  # Real hidden iframe behaviour with extracted boot and deterministic stubs.
  hidden=[]
  for mode in ('baseline','candidate'):
   page=await ctx.new_page();await page.set_content('<html><body>Hidden iframe source probe</body></html>')
   source=BOOT if mode=='candidate' else BASE_BOOT
   await page.evaluate('(html)=>{const f=document.createElement("iframe");f.id="probe";f.style.display="none";f.srcdoc=html;document.body.append(f)}','<html><body><script>'+STATE_JS+source+'\nboot();</script></body></html>')
   await page.wait_for_function('document.querySelector("iframe").contentWindow.obs?.settings===true')
   await page.wait_for_timeout(500)
   before=await page.evaluate('({...document.querySelector("iframe").contentWindow.obs})')
   await page.evaluate('document.querySelector("iframe").style.display="block"')
   await page.wait_for_function('document.querySelector("iframe").contentWindow.obs.loop===true')
   after=await page.evaluate('({...document.querySelector("iframe").contentWindow.obs})')
   hidden.append({'mode':mode,'whileHidden':before,'afterReveal':after});await page.close()
  results['hiddenIframe']=hidden
  # Delayed stylesheet: the family is not known when the first fit is cached.
  page=await ctx.new_page()
  html='''<html><head>
<style>body{margin:0}.c{position:relative;width:325px;height:530px}.arc{position:absolute;width:325px;height:300px}.cn{position:absolute;left:162.5px;transform:translateX(-50%);top:150px;font-family:"Fraunces",serif;font-size:30px;font-weight:600;white-space:nowrap}.nt{position:absolute;top:215px;left:100px;font-size:40px}.bar{position:absolute;top:285px}</style></head><body><div class="c"><svg class="arc" viewBox="0 0 325 300"><path class="rail" d="M20 260 C110 260 103 45 162 45 C221 45 215 260 307 260"/><line class="horizon" x1="20" x2="305" y1="190" y2="190"/></svg><div class="cn">Forenoon</div><div class="nt">13:17</div><div class="bar"></div></div><script>const $=s=>document.querySelector(s);const M={currentKey:'Forenoon',sunrise:446,sunset:1148};'''+FIT+'''
window.fitNow=()=>fitCn(M);window.forceFit=()=>{_cnFit='';fitCn(M)};window.snap=()=>({fontCheck:document.fonts.check('600 24px "Fraunces"'),knownFaces:[...document.fonts].map(f=>({family:f.family,status:f.status})),cachedKey:_cnFit,size:$('.cn').style.fontSize,top:$('.cn').style.top,width:$('.cn').getBoundingClientRect().width,cssApplied:!!window.cssApplied});fitCn(M);</script></body></html>'''
  await page.set_content(html,wait_until='domcontentloaded');before=await page.evaluate('snap()')
  await page.evaluate('''async(localFont)=>{const style=document.createElement('style');style.textContent='@font-face{font-family:"Fraunces";src:local('+JSON.stringify(localFont)+');font-weight:600;}';document.head.append(style);window.cssApplied=true;await document.fonts.load('600 24px "Fraunces"');}''',args.font_local)
  await page.evaluate('fitNow()');after=await page.evaluate('snap()');await page.evaluate('forceFit()');forced=await page.evaluate('snap()')
  results['fontCache']={'initialMissingFace':before,'afterFaceArrivalOrdinaryFit':after,'afterExplicitCacheInvalidationControl':forced,'fontIsControlledLocalSubstitute':True,'controlledLocalFont':args.font_local}
  assert before['fontCheck'] is True and before['knownFaces']==[]
  assert before['cachedKey']==after['cachedKey'] and before['size']==after['size']
  assert abs(float(after['width'])-float(forced['width']))>1 or after['top']!=forced['top']
  await browser.close()
 results['status']='PROBES_COMPLETED'
 out=ROOT/'probe-results.json';out.write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2))
if __name__=='__main__':asyncio.run(main())
