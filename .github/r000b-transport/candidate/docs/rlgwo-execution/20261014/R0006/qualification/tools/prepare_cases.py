"""Prepare only R0006 inputs for the delivered prayer driver; no browser is launched."""
import copy, hashlib, json
from pathlib import Path

ROOT = Path(__file__).parent / 'salah_widget'
if not ROOT.exists(): ROOT = Path(__file__).parent.parent / 'salah_widget'
OUT = Path(__file__).parent
BASE = 'c431733c57f76e2b441ee8f8cd85a1fa6675de55'
ordinary = json.loads((ROOT/'tests/r0002-ordinary.json').read_bytes())
HASH = '#lat=24.47&lon=39.61&label=Madinah&method=4&school=0&time=24&tz=UTC'
KEY = 'salah:24.47|39.61|UTC|4|0'
F = 'window.__prayerFixture'
current = "s.stage==='render-completed'&&s.currentDay==='07-09-2026'&&s.render&&!s.render.unavailable&&!s.flags.prayerStale"
def cp(x): return copy.deepcopy(x)
def wait(pred, timeout=15000): return {'type':'wait','predicate':pred,'timeoutMs':timeout}
def capture(name, first=False):
    a={'type':'capture','name':name,'selector':'.c','readOnly':not first}
    if first: a.update(firstRender=True,firstPredicate=current)
    return a
def count(day='07-09-2026'):
    return f"{F}.requests.filter(r=>r.kind==='prayer'&&r.url.includes('/{day}?')).length"
def payload(data=None): return {'code':200,'status':'OK','data':cp(data or ordinary)}
def healthy(id='healthy', **kw): return {'id':id,'kind':'prayer','payload':payload(),'dateFromRequest':True,**kw}
def expectation(stage, day='07-09-2026', **extra):
    return {'stage':stage,'equals':{'currentDay':day,'timezone':'UTC','dom/.c/geometry/width':325,'dom/.c/geometry/height':530},'noInvalidText':True,**extra}
def case(name, rules, actions, expected, **kw):
    return {'caseId':'R0006-'+name,'entry':'index.html','hash':HASH,'clockPolicy':{'mode':'advancing','epoch':'2026-09-07T12:00:00Z'},'cacheSeeds':[],
      'responseRules':rules+[{'id':'weather-offline','kind':'weather','failure':True},{'id':'radar-offline','kind':'radar','failure':True}],
      'orderedActions':actions,'expected':expected,'reviewRequirements':['Original loading/unavailable/first recovered native pixels, not eventual DOM alone','All six rows, 325x530 card, arc, next output, header and date footer','Operation/attempt/prefetch separation and native elapsed deadlines','Retain every failed capture and original trace'],**kw}

cases=[]
old=cp(ordinary); old['timings']['Fajr']='04:01'; old['meta']['timezone']='Asia/Tokyo'
rules=[{'id':'stalled','kind':'prayer','day':'07-09-2026','times':3,'hold':True,'phase':'body','ignoreAbort':True,'payload':payload(old)},
       healthy('next-current',day='07-09-2026',failure=True),healthy('prefetch',day='08-09-2026')]
actions=[wait(f"{F}.pending().includes('stalled:1')"),capture('loading'),
    wait(f"{count()}===3&&{F}.peekSlots().current===null",45000),capture('unavailable'),
    {'type':'setRule','id':'next-current','patch':{'failure':False}},
    wait(f"{F}.snapshots.some(s=>{current})",45000),capture('first-current',True),
    wait(f"{F}.peekSlots().current===null&&{F}.peekSlots().prefetch===null&&{F}.snapshots.some(s=>s.tomorrowDay==='08-09-2026')"),capture('before-late'),
    *[{'type':'release','id':'stalled','occurrence':i} for i in (1,2,3)],{'type':'sleep','ms':1300},capture('after-late')]
cases.append(case('cold-body',rules,actions,[expectation('unavailable',None),expectation('first-current',retryPolicy={'day':'07-09-2026','recoveryFence':True,'fullBodyTimeouts':True}),expectation('after-late',unchangedFrom={'stage':'before-late','paths':['today','tomorrow','timezone','runtimeGeneration','slots','storageLogLength']})],acceptanceIds=['R0006-A02','R0006-A05']))

prompt_rules=[{'id':'failed','kind':'prayer','day':'07-09-2026','times':3,'failure':True},healthy('next-current',day='07-09-2026',failure=True),healthy('prefetch',day='08-09-2026')]
prompt_actions=[wait(f"{count()}===3&&{F}.peekSlots().current===null"),capture('unavailable'),{'type':'setRule','id':'next-current','patch':{'failure':False}}]
finish=[wait(f"{F}.snapshots.some(s=>{current})",75000),capture('first-current',True),{'type':'sleep','ms':1600},capture('settled')]
hidden=prompt_actions+[
    {'type':'widgetOffscreen','offscreen':True},wait("document.querySelector('.c').classList.contains('paused')"),{'type':'checkpoint','name':'hidden'},
    wait(f"performance.now()-{F}.started>=65000",75000),{'type':'checkpoint','name':'after-fence-hidden'},
    {'type':'widgetOffscreen','offscreen':False},wait("!document.querySelector('.c').classList.contains('paused')"),*finish]
for action in hidden:
    if action['type']=='wait' and ('.classList.contains' in action['predicate'] or '.started>=65000' in action['predicate']):
        action['polling']=100
cases.append(case('hidden-resume',cp(prompt_rules),hidden,[expectation('unavailable',None),{'stage':'after-fence-hidden','equals':{'currentDay':None,'visibility/paused':True},'requestCountCheckpoint':True,'requestCounts':[{'kind':'prayer','day':'07-09-2026','exact':3}]},expectation('settled',retryPolicy={'day':'07-09-2026','recoveryFence':True})],iframe=True,acceptanceIds=['R0006-A03','R0006-A05']))
for name, suffix, mode in [('frozen-recovery','&simTime=12%3A00','fixed'),('accelerated-recovery','&simTime=12%3A00&timeScale=120','advancing')]:
    cases.append(case(name,cp(prompt_rules),cp(prompt_actions)+cp(finish),[expectation('unavailable',None),expectation('settled',retryPolicy={'day':'07-09-2026','recoveryFence':True})],hash=HASH+suffix,clockPolicy={'mode':mode,'epoch':'2026-09-07T12:00:00Z'},acceptanceIds=['R0006-A03']))

third_rules=[{'id':'failed','kind':'prayer','day':'07-09-2026','times':2,'failure':True},healthy()]
third_actions=[wait(f"{F}.snapshots.some(s=>{current})"),capture('first-current',True),{'type':'sleep','ms':2200},capture('settled')]
third_expected=[expectation('settled',requestCounts=[{'kind':'prayer','day':'07-09-2026','exact':3},{'kind':'prayer','day':'08-09-2026','exact':1}])]
cases.append(case('third-success',third_rules,third_actions,third_expected,acceptanceIds=['R0006-A04']))
offline=case('offline-entry',cp(third_rules),cp(third_actions),cp(third_expected),entry='offline.html',acceptanceIds=['R0006-A04','R0006-A05'])
cases.append(offline)

r2=json.loads((ROOT/'tests/rlgwo/R0002-cases.json').read_bytes())
for origin,name in [('R0002-cache-valid-offline','cache-offline'),('R0002-cache-distinct-denied-write','cache-denied')]:
    c=cp(next(c for c in r2['cases'] if c['caseId']==origin));c['caseId']='R0006-'+name
    c['clockPolicy']={'mode':'advancing','epoch':'2026-09-07T12:00:00Z'}
    c['acceptanceIds']=['R0006-A04'];c['reusedRecipeFrom']=origin
    if name=='cache-offline':c['offline']=True
    for k in ['originalCaseSha256','originalExpectedSha256']:c.pop(k,None)
    cases.append(c)

promotion_actions=[wait(f"{F}.snapshots.some(s=>{current})"),capture('first-current',True),wait(f"{F}.snapshots.some(s=>s.tomorrowDay==='08-09-2026')"),
    wait(f"performance.now()-{F}.started>=65000",75000),capture('matching-tomorrow'),
    {'type':'clock','epoch':'2026-09-08T00:00:01Z'},wait(f"{F}.snapshots.some(s=>s.currentDay==='08-09-2026'&&s.tomorrowDay==='09-09-2026')"),capture('promoted'),{'type':'sleep','ms':1200},capture('settled')]
cases.append(case('tomorrow-promotion',[healthy()],promotion_actions,[expectation('matching-tomorrow',requestCountCheckpoint=True,requestCounts=[{'kind':'prayer','day':'07-09-2026','exact':1},{'kind':'prayer','day':'08-09-2026','exact':1}]),expectation('settled','08-09-2026',requestCounts=[{'kind':'prayer','day':'07-09-2026','exact':1},{'kind':'prayer','day':'08-09-2026','exact':1},{'kind':'prayer','day':'09-09-2026','exact':1}])],acceptanceIds=['R0006-A04']))

gen_rules=[healthy('old-A',day='07-09-2026',match={'latitude':'24.47'},times=1,hold=True,phase='body',ignoreAbort=True),
    healthy('new-B',day='07-09-2026',match={'latitude':'40.71'},times=1,hold=True,phase='body'),healthy()]
gen_actions=[wait(f"{F}.pending().includes('old-A:1')"),capture('loading'),{'type':'settings','fields':{'lat':'40.71','lon':'-74.01','label':'New York B'}},
    wait(f"{F}.pending().includes('new-B:1')"),capture('B-owning'),{'type':'release','id':'old-A'},{'type':'sleep','ms':900},capture('B-after-old'),
    {'type':'release','id':'new-B'},wait(f"{F}.snapshots.some(s=>{current})"),capture('first-current',True),{'type':'sleep','ms':1200},capture('settled')]
cases.append(case('generation-late-cleanup',gen_rules,gen_actions,[expectation('B-owning',None),expectation('B-after-old',None,unchangedFrom={'stage':'B-owning','paths':['slots/current','runtimeGeneration','today','storageLogLength']}),expectation('settled')],hash=HASH+'&preferLocal=1',acceptanceIds=['R0006-A03','R0006-A04']))

next(c for c in cases if c['caseId']=='R0006-accelerated-recovery')['jsonTraceTransport']=True
files=['src/native/index.html','index.html','offline.html','config.js','tools/build_native.py','tools/cp9/browser_runtime.py','tools/cp9/r0007_browser.py','tests/rlgwo/prayer-browser-fixture.cjs']
packet={'schema':'remaining-prayer-cases/v1','issue':6,'sourceCommit':BASE,'specCommit':'21e7a84365fae37a86cae5c7d5e41008c0adc53f','sourceFiles':{f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files},'cases':cases}
(ROOT/'tests/rlgwo/R0006-cases.json').write_text(json.dumps(packet,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
(OUT/'lease.json').write_text(json.dumps({'resource':'heavy-browser','status':'GRANTED','owner':'prayer','sourceCommit':BASE,'scope':'Owner execution order R0006; one isolated browser at a time; no desktop or personal profile access'},indent=2)+'\n')
print('Prepared',len(cases),'R0006 cases for existing driver')
