"""Actual HTTP before/after crops for the inherited CP9 bottom-border defect."""
from pathlib import Path
import argparse,functools,http.server,threading,json
from playwright.sync_api import sync_playwright
from native_browser_check import INIT,Quiet,ROOT
from browser_runtime import launch_browser,browser_identity
from runtime_identity import runtime_identity

def run(root,parent,out):
    out.mkdir(parents=True,exist_ok=True);rows=[]
    report={'scope':'Bottom-border pixels only; short runs do not qualify lunar refinement. Actual HTTP, synthetic provider/time fixtures.','rows':rows}
    with sync_playwright() as p:
        b=launch_browser(p);report['browser']=browser_identity(b)
        for name,folder in [('parent',parent),('fixed',root)]:
            identity=runtime_identity(folder)
            server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(folder)))
            threading.Thread(target=server.serve_forever,daemon=True).start()
            for scene,time,wx,cloud in [('overcast','12:30',3,100),('night','23:30',0,0)]:
                c=b.new_context(viewport={'width':430,'height':640},device_scale_factor=2,reduced_motion='reduce');c.add_init_script(INIT);q=c.new_page()
                c.route('https://fonts.googleapis.com/**',lambda r:r.abort());c.route('https://fonts.gstatic.com/**',lambda r:r.abort())
                errors=[];q.on('pageerror',lambda e:errors.append(str(e)))
                q.goto(f'http://127.0.0.1:{server.server_port}/index.html#lat=24.47&lon=39.61&tz=Asia/Riyadh&label=Footer&method=4&simTime={time}&simWx={wx}&simCloud={cloud}&simTemp=20&units=c&motion=reduced&qa=1')
                q.wait_for_function("document.querySelectorAll('.p').length===6&&window.realSkyState?.().status==='ready'",timeout=60000)
                state=q.evaluate('''()=>{const c=document.querySelector('.real-sky-canvas'),x=c.getContext('2d');return {sky:realSkyState(),moon:window.SalahMoonRuntime?.state??null,card:document.querySelector('.c').getBoundingClientRect().toJSON(),footer:document.querySelector('.d').getBoundingClientRect().toJSON(),pixels:[500,515,522,526,528,529].map(y=>({y,rgba:[...x.getImageData(162,y,1,1).data]}))};}''')
                q.screenshot(path=str(out/f'{name}-{scene}.png'),clip={'x':0,'y':490,'width':325,'height':50})
                assert not errors and state['footer']['bottom']<=state['card']['bottom']
                rows.append({'candidate':name,'scene':scene,'runtimeTreeSha256':identity['treeSha256'],'state':state,'pageErrors':errors});c.close()
            assert runtime_identity(folder)==identity
            server.shutdown()
        b.close()
    for scene in ['overcast','night']:
        a=next(r for r in rows if r['candidate']=='parent' and r['scene']==scene)['state']['pixels']
        z=next(r for r in rows if r['candidate']=='fixed' and r['scene']==scene)['state']['pixels']
        assert a[-1]['rgba'][0]<.6*a[2]['rgba'][0]
        assert z[-1]['rgba'][0]>.8*z[2]['rgba'][0]
    report['status']='PASS_SCOPED';(out/'results.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--parent',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=run(a.root,a.parent,a.output);print(r['status'])
