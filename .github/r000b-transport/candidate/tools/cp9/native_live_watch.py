"""Twenty-second wall-clock cloud observations with normal and reduced-motion controls.
No simulated time, Date override or qaState cloud hash. Saves actual video/pixels.
"""
import argparse, functools, http.server, json, threading, time
from pathlib import Path
from playwright.sync_api import sync_playwright
from browser_runtime import launch_browser, browser_identity
from native_browser_check import ROOT, Quiet
from runtime_identity import runtime_identity
def run(root,out):
    out.mkdir(parents=True,exist_ok=True);server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(root)))
    threading.Thread(target=server.serve_forever,daemon=True).start();rows=[]
    try:
        with sync_playwright() as p:
            b=launch_browser(p);ident=browser_identity(b)
            for name,reduced,extra in [('default-live','no-preference',''),('os-reduced','reduce',''),('full-override','reduce','&motion=full')]:
                c=b.new_context(viewport={'width':430,'height':640},reduced_motion=reduced,record_video_dir=str(out/'video'),record_video_size={'width':430,'height':640});q=c.new_page();errors=[];q.on('pageerror',lambda e:errors.append(str(e)))
                try:
                    q.goto(f'http://127.0.0.1:{server.server_port}/index.html#lat=24.47&lon=39.61&tz=Asia/Riyadh&label=Madinah&method=4&simWx=2&simCloud=65&simPrecip=0&debugMotion=1&qa=1'+extra,wait_until='domcontentloaded')
                    q.wait_for_function("window.realSkyState?.().status==='ready'",timeout=60000)
                    q.locator('.c').screenshot(path=str(out/(name+'-start.png')))
                    q.evaluate('''()=>{const c=document.querySelector('.cloudcanvas');window.__cloudStart=c.getContext('2d').getImageData(0,0,c.width,c.height).data;window.__watchStart={utc:simNow(),wall:Date.now(),mono:performance.now(),sky:realSkyState(),host:SalahNativeSkyHost.capture()};}''')
                    q.wait_for_timeout(20000)
                    result=q.evaluate('''()=>{const c=document.querySelector('.cloudcanvas'),end=c.getContext('2d').getImageData(0,0,c.width,c.height).data;let changed=0,total=0,max=0;for(let i=0;i<end.length;i++){const d=Math.abs(end[i]-__cloudStart[i]);if(d)changed++;total+=d;max=Math.max(max,d);}return {start:__watchStart,end:{utc:simNow(),wall:Date.now(),mono:performance.now(),sky:realSkyState(),host:SalahNativeSkyHost.capture()},meanAbsoluteCodeDifference:total/end.length,maxCodeDifference:max,changedChannels:changed,totalChannels:end.length,rows:document.querySelectorAll('.p').length,followWallClock:FOLLOW_WALL_CLOCK,debug:document.querySelector('#debugMotion')?.textContent};}''')
                    q.locator('.c').screenshot(path=str(out/(name+'-end.png')));result.update(name=name,seconds=20,pageErrors=errors)
                    result['clockCurrent']=abs((result['end']['utc']-result['start']['utc'])-(result['end']['wall']-result['start']['wall']))<100 and result['followWallClock']
                    result['motionPreferenceCorrect']=result['end']['host']['reducedMotion']==(name=='os-reduced')
                    rows.append(result)
                except Exception as e:rows.append({'name':name,'error':str(e),'pageErrors':errors})
                finally:
                    video=q.video;c.close()
                    if video:video.save_as(str(out/(name+'.webm')))
                (out/'results.json').write_text(json.dumps({'browser':ident,'runtimeTreeSha256':runtime_identity(root)['treeSha256'],'cases':rows,'scope':'Real wall clock, live prayer, explicitly simulated cloudy weather only. Pixel deltas and 20s video; no claim of stellar scintillation or all-day visual qualification.'},indent=2),encoding='utf-8')
            b.close()
    finally:server.shutdown()
    return rows
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--output',type=Path,required=True);a=p.parse_args();run(a.root,a.output)
