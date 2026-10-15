"""Representative public settings/prayer/weather consumer with actual deployed assets.

Only external provider ingress is synthetic; no document rewrite, init script,
product mutation. Existing qaState is read only. Independent HTTP byte verification
is retained. Healthy weather inputs are labelled synthetic model data, not provider health.
"""
import argparse, hashlib, json, os, sys, time, urllib.request, subprocess
from pathlib import Path
from urllib.parse import urlsplit, parse_qs
ROOT=Path(__file__).resolve().parents[2]
DRIVER_ROOT=ROOT
sys.path.insert(0,str(ROOT/'tools/cp9'))
from browser_runtime import launch_browser, browser_identity
HASH='#preferLocal=1&lat=24.47&lon=39.61&tz=UTC&label=Madinah&method=4&school=0&units=c&time=24'
def prayer(tag, zone='UTC', fajr='05:00', asr='15:30'):
    data=json.loads((ROOT/'tests/r0002-ordinary.json').read_bytes())
    data['tag']=tag;data['meta']['timezone']=zone
    data['timings'].update(Fajr=fajr,Sunrise='06:00',Dhuhr='12:00',Asr=asr,Sunset='18:00',Maghrib='18:00',Isha='19:30')
    return {'code':200,'status':'OK','data':data}
PUBLIC='https://theislampill.github.io/salah_widget/'
def sha(b):return hashlib.sha256(b).hexdigest()
def dump(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')

def main():
    global ROOT
    p=argparse.ArgumentParser();p.add_argument('--output',required=True,type=Path);p.add_argument('--engine',choices=['chromium','firefox'],required=True);p.add_argument('--root',required=True,type=Path);p.add_argument('--expected-commit',required=True);a=p.parse_args();ROOT=a.root.resolve();a.output.mkdir(parents=True,exist_ok=False)
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==a.expected_commit, 'Merged root identity mismatch'
    paths=['index.html','offline.html','config.js','real-sky/native-sky.js','moon/moon-host.js','moon/asset-manifest.json']
    receipt={'schema':'r000d-public-consumer/v1','origin':PUBLIC,'byteReadback':[],'providerRequests':[],'nativeResponses':[],'errors':[],
             'sourceCommit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
             'driverSha256':sha(Path(__file__).read_bytes()),'leaseSha256':sha((DRIVER_ROOT/'evidence/R000D/delivery/public-consumer-lease.json').read_bytes()),
             'inputPolicy':'Synthetic prayer and healthy Open-Meteo ingress only; actual public application/assets and native fetch/Response.json; no clock override, init script, direct fetchWeather call or accepted-state write. Radar ingress deliberately unavailable. Model input is not observed precipitation or provider health.',
             'providerPayloads':[]}
    def byte_readback():
        for path in paths:
            row={'path':path,'url':PUBLIC+path,'status':None};receipt['byteReadback'].append(row)
            req=urllib.request.Request(PUBLIC+path,headers={'Cache-Control':'no-cache','User-Agent':'R000D-public-readback'})
            with urllib.request.urlopen(req,timeout=60) as r:b=r.read();row.update(status=r.status,url=r.url)
            expected=sha((ROOT/path).read_bytes());actual=sha(b)
            row.update(bytes=len(b),expectedSha256=expected,actualSha256=actual,equal=expected==actual)
            assert row['status']==200 and expected==actual,('public source mismatch',path)
    os.environ['SALAH_BROWSER']=a.engine
    from playwright.sync_api import sync_playwright
    try:
        byte_readback()
        receipt['documentationReadback']=[]
        for ref in (a.expected_commit,'main'):
            for path in ('README.md','DESIGN.md'):
                url='https://raw.githubusercontent.com/theislampill/salah_widget/'+ref+'/'+path
                req=urllib.request.Request(url,headers={'Cache-Control':'no-cache','User-Agent':'R000D-public-readback'})
                with urllib.request.urlopen(req,timeout=60)as response:data=response.read();status=response.status
                row={'ref':ref,'path':path,'url':url,'status':status,'bytes':len(data),'actualSha256':sha(data),'expectedSha256':sha((ROOT/path).read_bytes())}
                row['equal']=row['actualSha256']==row['expectedSha256'];receipt['documentationReadback'].append(row)
                assert status==200 and row['equal'],('delivered documentation mismatch',row)
        with sync_playwright() as pw:
            browser=launch_browser(pw);context=None
            try:
                context=browser.new_context(viewport={'width':390,'height':600},device_scale_factor=1,timezone_id='Asia/Riyadh')
                run_consumer(browser,context,a,receipt,paths)
            finally:
                try:
                    if context:context.close()
                finally:browser.close()
    except Exception as e:
        receipt['status']='FAIL';receipt['failure']=repr(e);raise
    finally:dump(a.output/'public-readback.json',receipt)
    print(json.dumps({'status':receipt['status'],'byteMatches':len(receipt['byteReadback']),'providerRequests':len(receipt['providerRequests'])}))

def run_consumer(browser,context,a,receipt,paths):
            page=context.new_page();page.on('pageerror',lambda e:receipt['errors'].append(str(e)))
            def weather_payload(query):
                zone=query['timezone'][0]
                assert query['temperature_unit']==['celsius'] and query['wind_speed_unit']==['ms']
                clock=page.evaluate("""zone=>{const now=Date.now();const fmt=new Intl.DateTimeFormat('en-CA',{timeZone:zone,year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hourCycle:'h23'});const stamp=ms=>{const p=Object.fromEntries(fmt.formatToParts(new Date(ms)).map(p=>[p.type,p.value]));return `${p.year}-${p.month}-${p.day}T${p.hour}:${p.minute}`};return {now,zone,current:stamp(now),next:stamp(now+3600000)}}""",zone)
                selected=query.get('latitude')==['40.71'];temp=19 if selected else 20
                current={'time':clock['current'],'interval':900,'weather_code':95,'temperature_2m':temp,'apparent_temperature':19,
                         'relative_humidity_2m':90,'dew_point_2m':18,'wind_speed_10m':2,'wind_direction_10m':180,
                         'wind_gusts_10m':4,'cloud_cover':95,'precipitation':2,'is_day':0}
                payload={'timezone':zone,'elevation':100,'latitude':float(query['latitude'][0]),'longitude':float(query['longitude'][0]),
                         'current':current,'current_units':{'temperature_2m':'°C','precipitation':'mm'},
                         'hourly':{'time':[clock['current'],clock['next']],'temperature_2m':[temp,19],'weather_code':[95,3],'wind_direction_10m':[180,180],'precipitation':[2,0]},
                         'hourly_units':{'temperature_2m':'°C','precipitation':'mm'}}
                wire=json.dumps(payload,allow_nan=False).encode()
                receipt['providerPayloads'].append({'kind':'synthetic-current-and-hourly-model','target':'B'if selected else'A','requestQuery':query,'nativeClockRead':clock,'body':payload,'bodySha256':sha(wire),'bytes':len(wire)})
                return wire
            def weather_read():
                return page.evaluate("""()=>{const s=qaState();return {wx:s.wx,wxTruth:s.wxTruth,cache:s.cache,config:s.config,render:s.render,weatherHeader:s.weatherHeader,dom:{temperature:document.querySelector('#wt').textContent,label:document.querySelector('#wi').getAttribute('aria-label')}}}""")
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
                if u.hostname=='api.open-meteo.com':
                    route.fulfill(status=200,body=weather_payload(q),content_type='application/json',headers={'Access-Control-Allow-Origin':'*'});return
                if u.hostname!='api.aladhan.com':route.abort('failed');return
                selected=q.get('latitude')==['40.71'];body=prayer('public-B' if selected else 'public-A','America/New_York' if selected else 'Asia/Riyadh','05:00' if selected else '04:46','15:30' if selected else '15:49')
                day=u.path.split('/')[-1];d,mo,y=map(int,day.split('-'));g=body['data']['date']['gregorian'];g.update(date=day,day=str(d).zfill(2),month={'number':mo},year=str(y))
                route.fulfill(status=200,json=body,headers={'Access-Control-Allow-Origin':'*'})
            page.route('https://api.aladhan.com/**',provider);page.route('https://api.open-meteo.com/**',provider);page.route('https://api.rainviewer.com/**',provider)
            page.goto(PUBLIC+'index.html?evidence=R000D'+HASH,wait_until='domcontentloaded')
            page.locator('.times [data-prayer-key="Asr"] .tm').filter(has_text='15:49').wait_for(timeout=30000)
            page.locator('#wt').filter(has_text='20°').wait_for(timeout=35000)
            receipt['weatherA']=weather_read()
            page.screenshot(path=str(a.output/'public-A.png'))
            page.locator('.buckle').click()
            for k,v in dict(lat='40.71',lon='-74.01',label='New York',method='2',school='0',units='c').items():
                e=page.locator('#set-'+k)
                if k in ('method','school','units'):e.select_option(v)
                else:e.fill(v)
            page.screenshot(path=str(a.output/'public-settings.png'));page.locator('#setClose').click()
            page.locator('.times [data-prayer-key="Asr"] .tm').filter(has_text='15:30').wait_for(timeout=30000)
            page.locator('#wt').filter(has_text='19°').wait_for(timeout=35000)
            receipt['weatherB']=weather_read()
            page.screenshot(path=str(a.output/'public-B.png'))
            receipt['browser']=browser_identity(browser)
            receipt['dom']=page.evaluate("""(()=>({url:location.href,card:(()=>{let r=document.querySelector('.c').getBoundingClientRect();return {width:r.width,height:r.height}})(),
              elements:Object.fromEntries(['.cn','.nt','.left','.times','#ce','#ah','.buckle'].map(s=>[s,document.querySelector(s)?.textContent])),
              storage:Object.keys(localStorage).map(key=>({key,value:localStorage.getItem(key)}))}))()""")
            assert receipt['dom']['card']=={'width':325,'height':530}
            assert '15:30' in receipt['dom']['elements']['.times'] and '05:00' in receipt['dom']['elements']['.times']
            assert any(r['url'].find('latitude=40.71&longitude=-74.01&method=2&school=0')>=0 for r in receipt['providerRequests'])
            assert not receipt['errors']
            for key,temp,lat,lon in (('weatherA',20,24.47,39.61),('weatherB',19,40.71,-74.01)):
                state=receipt[key];truth=state['wxTruth'];header=state['weatherHeader']
                assert state['wx']['temp']==temp and state['dom']['temperature']==str(temp)+'°'
                assert state['cache']['currentEligible'] and state['cache']['forecastTrackLoaded']
                assert truth['requests']['weather']['state']=='received' and truth['observedPresent'] is False
                assert truth['radarPrecipMm']==0 and truth['activeThunder'] is False
                assert truth['target']['lat']==lat and truth['target']['lon']==lon
                assert header['target']=={'lat':lat,'lon':lon} and header['temperature']==temp
                assert 'model estimate' in state['dom']['label'] and 'unobserved' in state['dom']['label']
            assert receipt['weatherB']['weatherHeader']['generation']>receipt['weatherA']['weatherHeader']['generation']
            for path in ('index.html','config.js','real-sky/native-sky.js','moon/moon-host.js'):
                rows=[r for r in receipt['nativeResponses'] if r['path']==path]
                assert rows and all(r.get('equal') and r['status']==200 for r in rows),('browser-consumed source mismatch',path,rows)
            receipt['status']='PASS_REPRESENTATIVE_PUBLIC_CONSUMER_PENDING_INDEPENDENT_REVIEW'
if __name__=='__main__':main()
