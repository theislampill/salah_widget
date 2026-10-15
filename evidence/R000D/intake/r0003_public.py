"""Representative public settings/prayer consumer with actual deployed entry/assets.

Only external provider ingress is synthetic; no document rewrite, init script,
diagnostic call or product mutation. Independent HTTP byte verification is retained.
"""
import argparse, hashlib, json, os, sys, time, urllib.request, subprocess
from pathlib import Path
from urllib.parse import urlsplit, parse_qs
from browser_runtime import launch_browser, browser_identity
from r0003_cases import prayer, HASH

ROOT=Path(__file__).resolve().parents[2]
PUBLIC='https://theislampill.github.io/salah_widget/'
def sha(b):return hashlib.sha256(b).hexdigest()
def dump(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',required=True,type=Path);p.add_argument('--engine',choices=['chromium','firefox'],required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    paths=['index.html','offline.html','config.js','real-sky/native-sky.js','moon/moon-host.js','moon/asset-manifest.json']
    receipt={'schema':'r0003-public-consumer/v1','origin':PUBLIC,'byteReadback':[],'providerRequests':[],'nativeResponses':[],'errors':[],
             'sourceCommit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
             'driverSha256':sha(Path(__file__).read_bytes()),'leaseSha256':sha((ROOT/'evidence/R0003/native-lease.json').read_bytes())}
    def byte_readback():
        for path in paths:
            row={'path':path,'url':PUBLIC+path,'status':None};receipt['byteReadback'].append(row)
            req=urllib.request.Request(PUBLIC+path,headers={'Cache-Control':'no-cache','User-Agent':'R0003-public-readback'})
            with urllib.request.urlopen(req,timeout=60) as r:b=r.read();row.update(status=r.status,url=r.url)
            expected=sha((ROOT/path).read_bytes());actual=sha(b)
            row.update(bytes=len(b),expectedSha256=expected,actualSha256=actual,equal=expected==actual)
            assert row['status']==200 and expected==actual,('public source mismatch',path)
    os.environ['SALAH_BROWSER']=a.engine
    from playwright.sync_api import sync_playwright
    try:
        byte_readback()
        with sync_playwright() as pw:
            browser=launch_browser(pw);context=None
            try:
                context=browser.new_context(viewport={'width':370,'height':570},device_scale_factor=1,record_video_dir=str(a.output/'video'))
                run_consumer(browser,context,a,receipt,paths)
            finally:
                if context:context.close()
                browser.close()
    except Exception as e:
        receipt['status']='FAIL';receipt['failure']=repr(e);raise
    finally:dump(a.output/'public-readback.json',receipt)
    print(json.dumps({'status':receipt['status'],'byteMatches':len(receipt['byteReadback']),'providerRequests':len(receipt['providerRequests'])}))

def run_consumer(browser,context,a,receipt,paths):
            page=context.new_page();page.on('pageerror',lambda e:receipt['errors'].append(str(e)))
            def response(r):
                if not r.url.startswith(PUBLIC):return
                path=urlsplit(r.url).path.removeprefix('/salah_widget/')
                row={'url':r.url,'status':r.status,'type':r.request.resource_type,'path':path};receipt['nativeResponses'].append(row)
                if path in paths:
                    try:
                        data=r.body();row.update(bytes=len(data),sha256=sha(data),expectedSha256=sha((ROOT/path).read_bytes()))
                        row['equal']=row['sha256']==row['expectedSha256']
                    except Exception as e:row['bodyError']=repr(e)
            page.on('response',response)
            def provider(route):
                u=urlsplit(route.request.url);q=parse_qs(u.query);receipt['providerRequests'].append({'url':u.geturl(),'method':route.request.method,'monotonic':time.monotonic()})
                if u.hostname!='api.aladhan.com':route.abort('failed');return
                selected=q.get('latitude')==['40.71'];body=prayer('public-B' if selected else 'public-A','America/New_York' if selected else 'Asia/Riyadh','05:00' if selected else '04:46','15:30' if selected else '15:49')
                day=u.path.split('/')[-1];d,mo,y=map(int,day.split('-'));g=body['data']['date']['gregorian'];g.update(date=day,day=str(d).zfill(2),month={'number':mo},year=str(y))
                route.fulfill(status=200,json=body,headers={'Access-Control-Allow-Origin':'*'})
            page.route('https://api.aladhan.com/**',provider);page.route('https://api.open-meteo.com/**',provider);page.route('https://api.rainviewer.com/**',provider)
            page.goto(PUBLIC+'index.html?evidence=R0003'+HASH,wait_until='domcontentloaded')
            page.locator('.times [data-prayer-key="Asr"] .tm').filter(has_text='15:49').wait_for(timeout=30000)
            page.screenshot(path=str(a.output/'public-A.png'))
            page.locator('.buckle').click()
            for k,v in dict(lat='40.71',lon='-74.01',label='New York',method='2',school='0',units='c').items():
                e=page.locator('#set-'+k)
                if k in ('method','school','units'):e.select_option(v)
                else:e.fill(v)
            page.screenshot(path=str(a.output/'public-settings.png'));page.locator('#setClose').click()
            page.locator('.times [data-prayer-key="Asr"] .tm').filter(has_text='15:30').wait_for(timeout=30000)
            page.screenshot(path=str(a.output/'public-B.png'))
            receipt['browser']=browser_identity(browser)
            receipt['dom']=page.evaluate("""(()=>({url:location.href,card:(()=>{let r=document.querySelector('.c').getBoundingClientRect();return {width:r.width,height:r.height}})(),
              elements:Object.fromEntries(['.cn','.nt','.left','.times','#ce','#ah','.buckle'].map(s=>[s,document.querySelector(s)?.textContent])),
              storage:Object.keys(localStorage).map(key=>({key,value:localStorage.getItem(key)}))}))()""")
            assert receipt['dom']['card']=={'width':325,'height':530}
            assert '15:30' in receipt['dom']['elements']['.times'] and '05:00' in receipt['dom']['elements']['.times']
            assert any(r['url'].find('latitude=40.71&longitude=-74.01&method=2&school=0')>=0 for r in receipt['providerRequests'])
            assert not receipt['errors']
            for path in ('index.html','config.js','real-sky/native-sky.js','moon/moon-host.js'):
                rows=[r for r in receipt['nativeResponses'] if r['path']==path]
                assert rows and all(r.get('equal') and r['status']==200 for r in rows),('browser-consumed source mismatch',path,rows)
            receipt['status']='PASS_REPRESENTATIVE_PUBLIC_CONSUMER_PENDING_INDEPENDENT_REVIEW'
if __name__=='__main__':main()
