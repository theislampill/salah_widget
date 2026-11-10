from pathlib import Path
import functools,http.server,threading,json,sys
R=Path(r'C:\Users\theis\.codex\worktrees\cp9-moon-v5-integration\salah_widget')
sys.path.insert(0,str(R/'tools/cp9'))
from native_browser_check import INIT,Quiet
from browser_runtime import launch_browser
from playwright.sync_api import sync_playwright
O=Path(__file__).resolve().parent/'footer-layer-probe';O.mkdir(exist_ok=True)
results=[]
with sync_playwright() as p:
 b=launch_browser(p)
 for label,root in [('parent',Path(r'C:\Users\theis\.codex\worktrees\cp9-real-sky-integration\salah_widget')),('moon',R)]:
  server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(root)));threading.Thread(target=server.serve_forever,daemon=True).start()
  c=b.new_context(viewport={'width':430,'height':640},reduced_motion='reduce');c.add_init_script(INIT);q=c.new_page()
  c.route('https://fonts.googleapis.com/**',lambda r:r.abort());c.route('https://fonts.gstatic.com/**',lambda r:r.abort())
  q.goto(f'http://127.0.0.1:{server.server_port}/index.html#lat=24.47&lon=39.61&tz=Asia/Riyadh&label=Footer&method=4&simTime=12:30&simWx=3&simCloud=100&simTemp=20&units=c&motion=reduced&qa=1')
  q.wait_for_function("document.querySelectorAll('.p').length===6&&window.realSkyState?.().status==='ready'",timeout=60000)
  row=q.evaluate('''()=>{const c=document.querySelector('.real-sky-canvas'),ctx=c.getContext('2d');return {source:location.href,card:document.querySelector('.c').getBoundingClientRect().toJSON(),canvas:c.getBoundingClientRect().toJSON(),pixels:[500,515,522,526,528,529].map(y=>({y,rgba:[...ctx.getImageData(162,y,1,1).data]})),footer:document.querySelector('.d').getBoundingClientRect().toJSON(),shadow:getComputedStyle(document.querySelector('.c')).boxShadow};}''')
  for name,css in [('original',''),('no-card-shadow','.c{box-shadow:none!important}'),('no-physical-canvas','.real-sky-canvas{visibility:hidden!important}'),('no-dates','.d{visibility:hidden!important}'),('no-prayer-glass','.p{box-shadow:none!important;backdrop-filter:none!important;-webkit-backdrop-filter:none!important}'),('no-sky','.sky{visibility:hidden!important}')]:
   s=q.add_style_tag(content=css) if css else None;q.screenshot(path=str(O/(label+'-'+name+'.png')),clip={'x':0,'y':490,'width':325,'height':60})
   if s:s.evaluate('(e)=>e.remove()')
  results.append(dict(label=label,**row));c.close();server.shutdown()
 b.close()
(O/'results.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(results,indent=2))
