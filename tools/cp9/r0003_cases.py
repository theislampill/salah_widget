"""Build bounded synthetic R0003 inputs; never launches or modifies product state."""
import base64
import copy
import hashlib
import json
import struct
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = '06772824a159cd2bc42a1d9f79a3fb22fa46e49d'
EPOCH = '2026-09-07T16:00:00Z'
HASH = '#preferLocal=1&lat=24.47&lon=39.61&tz=UTC&label=Madinah&method=4&school=0&units=c&time=24'
A = dict(lat=24.47, lon=39.61, label='Madinah', method='4', school='0', units='c')
B = dict(lat=40.71, lon=-74.01, label='New York', method='2', school='0', units='c')
LONDON = dict(lat=51.48, lon=-0.001, label='London', method='2', school='0', units='f')

def prayer(tag, zone='UTC', fajr='05:00', asr='15:30'):
    data = json.loads((ROOT/'tests/r0002-ordinary.json').read_bytes())
    data['tag'] = tag
    data['meta']['timezone'] = zone
    data['timings'].update(Fajr=fajr, Sunrise='06:00', Dhuhr='12:00', Asr=asr, Sunset='18:00', Maghrib='18:00', Isha='19:30')
    return {'code':200, 'status':'OK', 'data':data}

def rule(name, cfg, *, hold=False, phase='body', zone='UTC', tag=None, times=None, day=None):
    r = dict(id=name, kind='prayer', match={k:str(cfg[k]) for k in ('method','school')},
             payload=prayer(tag or name,zone, '04:46' if zone=='Asia/Riyadh' else '05:00', '15:49' if zone=='Asia/Riyadh' else '15:30'), dateFromRequest=True)
    r['match'].update(latitude=str(cfg['lat']), longitude=str(cfg['lon']))
    if hold:r.update(hold=True,phase=phase,ignoreAbort=True)
    if times is not None:r['times']=times
    if day:r['day']=day
    return r

def wait(predicate, timeout=15000):return dict(type='wait',predicate=predicate,timeoutMs=timeout)
def pending(name):return wait("window.__prayerFixture.pending().includes('"+name+":1')")
def cap(name):return dict(type='capture',name=name,readOnly=True)
def first(tag):return dict(type='capture',name='first-current',firstRender=True,firstPredicate="s.stage==='render-completed'&&s.today?.tag==='"+tag+"'")
def settings(cfg):return dict(type='settings',fields=cfg,capture='settings-'+cfg['label'].replace(' ','-')+'-'+cfg['method']+'-'+cfg['school']+'-'+cfg['units'])
def release(name):return dict(type='release',id=name)
def settled(name):return wait("window.__prayerFixture.events.some(e=>e.type==='json-settle'&&e.key==='"+name+":1')")
def current(tag):return wait("window.__prayerFixture.snapshots.some(s=>s.stage==='render-completed'&&s.today?.tag==='"+tag+"')")
def expect(stage, equals=None, **rest):return dict(stage=stage,equals=equals or {},noInvalidText=True,**rest)
def same(stage, before, paths):return expect(stage,unchangedFrom=dict(stage=before,paths=paths))
def case(name, actions, rules, expected, **extra):
    return dict(caseId='R0003-'+name,entry='index.html',hash=HASH,clockPolicy=dict(mode='fixed',epoch=EPOCH),cacheSeeds=[],
                responseRules=rules+[dict(id='weather-unavailable',kind='weather',failure=True),dict(id='radar-unavailable',kind='radar',failure=True)],
                orderedActions=actions,expected=expected,observeImages=True,**extra)

WIN_PATHS=['config','timezone','runtimeGeneration','today','tomorrow','flags','storage','weather','weatherTrack','weatherRadar','lastWxAt','dom/.nt/text','dom/.times/html']
WIN = {'config/lat':40.71,'config/lon':-74.01,'config/label':'New York','timezone':'America/New_York','today/timings/Fajr':'05:00','today/timings/Asr':'15:30','dom/.nt/text':'15:30','flags/prayerStale':False}

def weather(temp=20, units='c', zone='UTC', wall='2026-09-07T16:00', elevation=100):
    # Fully specified, admitted synthetic current/hourly inputs. Model evidence only.
    unit='°C' if units=='c' else '°F'
    current=dict(time=wall,interval=900,weather_code=2,temperature_2m=temp,apparent_temperature=temp,
                 relative_humidity_2m=70,dew_point_2m=18 if units=='c' else 64.4,wind_speed_10m=2,
                 wind_direction_10m=180,wind_gusts_10m=4,cloud_cover=50,cloud_cover_low=35,cloud_cover_mid=15,
                 cloud_cover_high=10,precipitation=0,rain=0,showers=0,snowfall=0,visibility=20000,is_day=1)
    units_meta=dict(temperature_2m=unit,apparent_temperature=unit,dew_point_2m=unit,wind_speed_10m='m/s',
                    wind_direction_10m='°',wind_gusts_10m='m/s',precipitation='mm',rain='mm',showers='mm',snowfall='cm',
                    visibility='m',relative_humidity_2m='%',cloud_cover='%',cloud_cover_low='%',cloud_cover_mid='%',cloud_cover_high='%')
    # One exact record is enough to test captured-zone conversion; no interpolation ambiguity.
    hourly={k:[v] for k,v in current.items() if k not in ('time','interval')}
    hourly['time']=[wall]
    return dict(timezone=zone,elevation=elevation,current=current,hourly=hourly,current_units=units_meta,hourly_units=units_meta)

def wxrule(name,cfg,payload,hold=True):
    return dict(id=name,kind='weather',match=dict(latitude=str(cfg['lat']),longitude=str(cfg['lon']),temperature_unit='celsius' if cfg['units']=='c' else 'fahrenheit'),
                payload=payload,hold=hold,phase='body',ignoreAbort=True)

def png(alpha):
    def chunk(kind,body):return struct.pack('>I',len(body))+kind+body+struct.pack('>I',zlib.crc32(kind+body)&0xffffffff)
    raw=(b'\x00'+bytes([40,90,160,alpha])*256)*256
    return base64.b64encode(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',256,256,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b'')).decode()

def build():
    cases=[]
    for phase in ('body','headers'):
        cases.append(case('prayer-late-'+phase,
            [pending('A'),cap('loading'),settings(B),current('B'),first('B'),cap('B-before-A'),release('A'),settled('A'),cap('B-after-A')],
            [rule('A',A,hold=True,phase=phase,zone='Asia/Riyadh',times=1),rule('B',B,zone='America/New_York')],
            [expect('B-before-A',WIN),same('B-after-A','B-before-A',WIN_PATHS)],acceptanceIds=['R0003-A01']))
    cases.append(case('prayer-old-rejection',
        [pending('A'),settings(B),pending('B'),cap('B-pending'),dict(type='reject',id='A'),cap('after-rejection'),release('B'),current('B'),cap('B-winner')],
        [rule('A',A,hold=True,zone='Asia/Riyadh',times=1),rule('B',B,hold=True,zone='America/New_York',times=1),rule('B-next',B,zone='America/New_York',tag='B-next')],
        [same('after-rejection','B-pending',['config','timezone','today','tomorrow','slots/current','storage','flags']),expect('B-winner',WIN)],acceptanceIds=['R0003-A01']))
    cases.append(case('prayer-early-A',
        [current('A'),cap('A-current'),settings(B),current('B'),cap('B-winner')],
        [rule('A',A,zone='Asia/Riyadh'),rule('B',B,zone='America/New_York')],
        [expect('A-current',{'today/tag':'A','today/timings/Asr':'15:49'}),expect('B-winner',WIN)],acceptanceIds=['R0003-A01']))
    cases.append(case('prayer-old-tomorrow',
        [pending('A-next'),cap('A-tomorrow-held'),settings(B),current('B'),first('B'),pending('B-next'),cap('B-before-A'),release('A-next'),settled('A-next'),cap('B-after-A'),release('B-next'),current('B'),wait("window.__prayerFixture.readSnapshot().tomorrow?.tag==='B-next'"),cap('B-tomorrow')],
        [rule('A',A,zone='Asia/Riyadh',day='07-09-2026'),rule('A-next',A,hold=True,zone='Asia/Riyadh',day='08-09-2026'),rule('B',B,zone='America/New_York',day='07-09-2026'),rule('B-next',B,hold=True,zone='America/New_York',day='08-09-2026')],
        [expect('A-tomorrow-held',{'slots/prefetch/requestedDay':'08-09-2026'}),expect('B-before-A',{**WIN,'slots/prefetch/requestedDay':'08-09-2026'}),same('B-after-A','B-before-A',WIN_PATHS+['slots/prefetch']),expect('B-tomorrow',{'tomorrow/tag':'B-next','tomorrowDay':'08-09-2026','slots/prefetch':None})],acceptanceIds=['R0003-A01']))
    cases.append(case('prayer-ABA',
        [pending('A1'),cap('A1-pending'),settings(B),pending('B'),cap('B-pending'),settings(A),current('A2'),cap('A2-before-old'),release('B'),release('A1'),settled('A1'),cap('A2-after-old')],
        [rule('A1',A,hold=True,times=1,zone='Asia/Riyadh'),rule('B',B,hold=True,times=1,zone='America/New_York'),rule('A2',A,zone='Asia/Riyadh')],
        [expect('A1-pending',{'runtimeGeneration':0}),expect('B-pending',{'runtimeGeneration':1}),expect('A2-before-old',{'runtimeGeneration':2,'today/tag':'A2','config/lat':24.47}),same('A2-after-old','A2-before-old',WIN_PATHS)],acceptanceIds=['R0003-A02']))
    b3={**B,'method':'3'};b31={**b3,'school':'1'};b31f={**b31,'units':'f'}
    cases.append(case('method-school-units',
        [pending('A'),settings(B),pending('M2'),cap('method2'),settings(b3),pending('M3'),cap('method3'),settings(b31),pending('S1'),cap('school1'),settings(b31f),current('F'),cap('F-before-old'),release('S1'),release('M3'),release('M2'),release('A'),settled('A'),cap('F-after-old')],
        [rule('A',A,hold=True,times=1),rule('M2',B,hold=True,times=1),rule('M3',b3,hold=True,times=1),rule('S1',b31,hold=True,times=1),rule('F',b31f)],
        [expect('method2',{'config/method':'2','runtimeGeneration':1}),expect('method3',{'config/method':'3','runtimeGeneration':2}),expect('school1',{'config/school':'1','runtimeGeneration':3}),expect('F-before-old',{'runtimeGeneration':4,'today/tag':'F','config/units':'f','config/method':'3','config/school':'1'}),same('F-after-old','F-before-old',WIN_PATHS)],acceptanceIds=['R0003-A02']))
    c=copy.deepcopy(cases[0]);c.update(caseId='R0003-no-abort',variant='no-abort',acceptanceIds=['R0003-A02']);cases.append(c)
    cases.append(case('unconditional-finally',
        [pending('A'),settings(B),pending('B'),cap('successor-slot'),release('A'),settled('A'),cap('after-old'),release('B'),settled('B'),cap('after-B')],
        [rule('A',A,hold=True,times=1),rule('B',B,hold=True,times=1),rule('B-next',B)],
        [expect('successor-slot',{'flags/currentOwnerLat':40.71})],variant='unconditional-finally',expectedFailure=True,acceptanceIds=['R0003-A02']))
    control=copy.deepcopy(cases[-1]);control['caseId']='R0003-finally-control';control.pop('variant');control.pop('expectedFailure');cases.append(control)
    for reject in (False,True):
        acts=[pending('WA'),cap('A-body-held'),settings(LONDON),pending('WB'),pending('PB'),cap('B-body-held'),dict(type='reject' if reject else 'release',id='WA'),cap('B-after-A'),release('WB'),wait("window.__prayerFixture.readSnapshot().weather?.temp===68"),release('PB'),current('PB'),release('PA'),settled('PA'),cap('B-weather')]
        cases.append(case('weather-old-'+('reject' if reject else 'body'),acts,
            [rule('PA',A,hold=True,times=1),rule('PB',LONDON,hold=True,times=1),rule('PB-next',LONDON),wxrule('WA',A,weather()),wxrule('WB',LONDON,weather(68,'f',elevation=135))],
            [same('B-after-A','B-body-held',['config','weather','weatherTrack','lastWxAt','flags','slots/weather','storage']),expect('B-weather',{'weather/temp':68,'weather/units':'f','weatherTrack/units':'f','flags/siteElev':135,'flags/wxBusy':False,'config/label':'London','elevationCustody/heightM':135,'elevationCustody/lat':51.48,'elevationCustody/lon':-0.001,'dom/#wt/text':'68°','weatherHeader/temperature':68})],acceptanceIds=['R0003-A03']))
    for mode in ('captured','obsolete','contradictory'):
        h='#preferLocal=1&lat=40.71&lon=-74.01&tz=America%2FNew_York&label=New%20York&method=2&school=0&units=c&time=24'
        payload=weather(zone='America/New_York',wall='2026-03-08T03:30')
        if mode=='contradictory':payload['timezone']='Asia/Riyadh'
        acts=[pending('W'),pending('P'),cap('captured-zone'),release('P'),current('P'),pending('P-next'),cap('prayer-zone-discovery')]
        rules=[rule('P',B,hold=True,times=1,zone='Asia/Riyadh'),rule('P-next',B,hold=True,times=1,zone='Asia/Riyadh'),wxrule('W',B,payload)]
        expected=[expect('captured-zone',{'slots/weather/requestZone':'America/New_York'}),expect('prayer-zone-discovery',{'timezone':'Asia/Riyadh','runtimeGeneration':0})]
        if mode=='obsolete':
            acts += [settings(LONDON),current('London'),cap('successor-before-W')]
            rules += [rule('London',LONDON),wxrule('WB',LONDON,weather(68,'f','America/New_York','2026-03-08T03:30'),False)]
        acts += [release('W'),settled('W'),release('P-next'),settled('P-next'),cap('after-weather')]
        if mode=='captured':expected += [expect('after-weather',{'weatherTrack/ep/0':1772955000000,'weatherTrack/zone':'America/New_York','weather/currentValidAt':1772955000000,'weather/currentZone':'America/New_York'})]
        elif mode=='contradictory':expected += [expect('after-weather',{'weather':None,'weatherTrack':None,'flags/wxBusy':False})]
        else:expected += [same('after-weather','successor-before-W',['config','timezone','weather','weatherTrack','storage','lastWxAt','flags'])]
        c=case('hourly-'+mode,acts,rules,expected,acceptanceIds=['R0003-A04']);c['hash']=h;c['clockPolicy']['epoch']='2026-03-08T07:30:00Z';cases.append(c)
    for hold_manifest in (False,True):
        rA={**A,'lat':0,'lon':30,'label':'Radar A'};rB={**B,'lat':30,'lon':0,'label':'Radar B'}
        manifest=lambda p:dict(host='__ORIGIN__',generated=1788796800,radar=dict(past=[dict(path='/fixture-radar-'+p,time=1788796800)]))
        # Manifests do not encode coordinates; request owner traces bind the ordered instances.
        mA=dict(id='RA',kind='radar',times=1,payload=manifest('A'),hold=hold_manifest,phase='body',ignoreAbort=True)
        mB=dict(id='RB',kind='radar',times=1,payload=manifest('B'))
        first_boundary=pending('RA') if hold_manifest else dict(type='waitImage',id='IA')
        acts=[first_boundary,cap('A-radar-held'),settings(rB),dict(type='waitImage',id='IB'),cap('B-image-held'),release('RA') if hold_manifest else dict(type='releaseImage',id='IA')]
        acts += [settled('RA')] if hold_manifest else [wait("window.__prayerFixture.imageEvents.some(e=>e.event==='load'&&e.src.includes('fixture-radar-A'))")]
        acts += [cap('B-after-A'),dict(type='releaseImage',id='IB'),wait("window.__prayerFixture.readSnapshot().weatherRadar?.target.lat===30"),cap('B-radar')]
        c=case('radar-'+('manifest' if hold_manifest else 'image'),acts,[rule('PA',rA),rule('PB',rB),mA,mB],
            [same('B-after-A','B-image-held',['config','weatherRadar','flags/radarBusy','slots/radar','storage']),expect('B-radar',{'weatherRadar/target/lat':30,'weatherRadar/target/lon':0,'weatherRadar/precipMm':0,'weatherRadar/sample/meanAlpha':0,'flags/radarBusy':False})],acceptanceIds=['R0003-A05'])
        c['hash']=HASH.replace('lat=24.47&lon=39.61','lat=0&lon=30').replace('label=Madinah','label=Radar%20A')
        c['imageRules']=[dict(id='IA',pathContains='fixture-radar-A',hold=True,pngBase64=png(255),alpha=255),dict(id='IB',pathContains='fixture-radar-B',hold=True,pngBase64=png(0),alpha=0)]
        cases.append(c)
    for expired in (False,True):
        c=case('reload-'+('expired' if expired else 'winner'),[wait("window.__prayerFixture.snapshots.some(s=>s.stage==='render-completed'&&s.currentDay)"),cap('reloaded')],
            [dict(id='prayer-offline',kind='prayer',failure=True)],
            [expect('reloaded',{'config/lat':51.48,'config/lon':-0.001,'config/units':'f','today/tag':'PB','dom/#wt/text':'' if expired else '68°','weatherHeader/temperature':None if expired else 68})],
            offline=True,cacheSeedsFromCase='R0003-weather-old-body',cacheSeedKeys=['salah_widget:config:v1','salah:51.48|-0.001|UTC|2|0','salahwx:51.48|-0.001|f'],acceptanceIds=['R0003-A06'])
        c['hash']='#preferLocal=1';c['clockPolicy']['epoch']='2026-09-07T17:00:00Z' if expired else EPOCH;cases.append(c)
    for entry,iframe in [('offline.html',False),('index.html',True)]:
        c=copy.deepcopy(cases[0]);c.update(caseId='R0003-entry-'+('iframe' if iframe else 'offline'),entry=entry,iframe=iframe,acceptanceIds=['R0003-A07']);cases.append(c)
    cases.append(case('error-recovery',
        [wait("window.__prayerFixture.events.some(e=>e.type==='error-output')"),cap('error'),settings(B),current('B'),cap('recovered')],
        [dict(id='PA-error',kind='prayer',match=dict(latitude='24.47'),failure=True),rule('B',B,zone='America/New_York')],
        [expect('error',{'today':None}),expect('recovered',WIN)],acceptanceIds=['R0003-A07']))
    # Same retained control recipe; current source and fresh native pixels must qualify it again.
    preservation=json.loads((ROOT/'tests/rlgwo/R0007-preservation-cases.json').read_bytes())['cases']
    for c in preservation:
        c=copy.deepcopy(c);c['caseId']='R0003-'+c['caseId'].replace('R0007-','');c['acceptanceIds']=['R0003-A07'];c['observeImages']=True
        cases.append(c)
    return cases

def main():
    paths=['index.html','offline.html','config.js','src/native/index.html','src/native/config.js','tools/build_native.py',
           'tools/cp9/browser_runtime.py','tools/cp9/r0007_browser.py','tests/rlgwo/prayer-browser-fixture.cjs','tools/cp9/r0003_cases.py',
           'tests/r0002-ordinary.json','tests/rlgwo/R0007-preservation-cases.json']
    packet=dict(schema='remaining-prayer-cases/v1',issue=3,sourceCommit=BASE,specCommit='21e7a84365fae37a86cae5c7d5e41008c0adc53f',
                sourceFiles={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths},cases=build())
    (ROOT/'tests/rlgwo/R0003-cases.json').write_text(json.dumps(packet,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps({'caseCount':len(packet['cases']),'sourceFiles':packet['sourceFiles']}))

if __name__=='__main__':main()
