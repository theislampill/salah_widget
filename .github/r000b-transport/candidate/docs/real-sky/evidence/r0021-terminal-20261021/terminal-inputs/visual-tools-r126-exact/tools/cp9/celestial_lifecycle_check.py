"""Targeted real-browser lifecycle controls after the ordinary startup capture."""
import asyncio,json
STATE="""()=>{const m=window.SalahMoonRuntime.state,n=window.SalahNativeSkyHost.capture(false),p=document.querySelector('.mphoto').getBoundingClientRect();return {native:n,moon:{current:m.current,source:m.visibleSource,epoch:m.epoch,generation:m.generation,pending:m.pending,accepted:m.accepted,phasePrecision:m.phasePrecision,cancelled:m.cancelled,rejected:m.rejected,quality:m.quality},surface:!!window.SalahMoonRuntime.surface(),photo:{x:p.x,y:p.y,width:p.width,height:p.height},settings:{open:document.querySelector('.c').classList.contains('settings-open'),display:getComputedStyle(document.querySelector('#settings')).display,role:document.querySelector('#settings').getAttribute('role')}};}"""
async def lifecycle_controls(page,frame,out,mode):
 records=[];failures=[]
 async def take(name):
  state=await frame.evaluate(STATE);state['name']=name
  file=mode+'-lifecycle-'+name+'.png';await page.screenshot(path=str(out/file));state['image']=file;records.append(state);return state
 def check(condition,reason):
  if not condition:failures.append(reason)
 before=await take('before')
 await frame.locator('.buckle.interactive').click()
 await take('settings-open')
 check(await frame.locator('#settings').is_visible(),'settings dialog unavailable')
 original_fields={name:await frame.locator('#set-'+name).input_value() for name in ['lat','lon','label']}
 for name,value in {'lat':'40.7128','lon':'-74.006','label':'B settings fixture'}.items():
  await frame.locator('#set-'+name).fill(value)
 await frame.locator('#setClose').click()
 await frame.wait_for_function('()=>window.SalahNativeSkyHost.capture(false)?.lat===40.7128')
 ui_b=await take('settings-target-b')
 check(not ui_b['settings']['open'],'actual close button did not close settings')
 await frame.locator('.buckle.interactive').click()
 for name,value in original_fields.items():await frame.locator('#set-'+name).fill(value)
 await frame.locator('#setClose').click()
 await frame.wait_for_function('(lat)=>window.SalahNativeSkyHost.capture(false)?.lat===lat',arg=before['native']['lat'])
 ui_a=await take('settings-target-a')
 check(ui_a['native']['generation']>=before['native']['generation']+2,'actual settings round-trip reused target generation')
 check(ui_a['native']['lon']==before['native']['lon'] and not ui_a['settings']['open'],'actual settings did not restore target A')
 await frame.evaluate("()=>{window.__startupConfigA=window.SalahConfig.resolve(location.hash).cfg;}")
 ab=await frame.evaluate("""async()=>{const a=window.__startupConfigA,b={...a,lat:40.7128,lon:-74.006,label:'B fixture'};
 const pb=applyConfig(b,{save:false});const mb=window.SalahMoonRuntime.state,nb=window.SalahNativeSkyHost.capture(false);
 const pa=applyConfig(a,{save:false});await Promise.all([pb,pa]);return {b:{native:nb,current:mb.current,generation:mb.generation,epoch:mb.epoch},a:window.SalahNativeSkyHost.capture(false)};}""")
 after=await take('a-b-a')
 check(ab['b']['native']['lat']==40.7128 and after['native']['lat']==before['native']['lat'],'A-B-A target mismatch')
 check(after['native']['generation']>=before['native']['generation']+2,'A-B-A reused generation')
 check(after['moon']['generation']==after['native']['generation'] and after['moon']['epoch']>before['moon']['epoch'],'A-B-A lunar scope not revoked')
 sought=await frame.evaluate("()=>SalahClock.set({rate:0,utcMs:window.SalahNativeSkyHost.capture(false).utcMs+1800000})")
 seek=await take('seek')
 check(seek['moon']['epoch']>after['moon']['epoch'],'seek failed to revoke lunar epoch')
 check(abs(seek['native']['utcMs']-sought['utcMs'])<1,'seek did not use native accepted UTC')
 await frame.evaluate('()=>SalahClock.set({live:true})')
 live=await take('live-return')
 check(live['moon']['epoch']>seek['moon']['epoch'] and live['native']['timeScale']==1,'live return did not revoke seek')
 unsupported=await frame.evaluate("()=>{SalahMoonRuntime.setProfile('reference');return {surface:!!SalahMoonRuntime.surface(),state:SalahMoonRuntime.state};}")
 check(not unsupported['surface'] and unsupported['state']['visibleSource']=='awaiting-terrain','initial tier leaked into unsupported reference profile')
 await take('reference-withdrawal')
 await frame.evaluate("()=>SalahMoonRuntime.setProfile('calendar')")
 restored=await take('calendar-return')
 check(restored['surface'] and restored['moon']['current'],'calendar return failed')
 reference=await frame.evaluate("""()=>{const m=SalahMoonRuntime.state,s={...m.accepted.scene,mode:'physical-reference'};
 SalahMoonRuntime.setReferenceScene(s);const absent=!SalahMoonRuntime.surface();SalahMoonRuntime.setReferenceScene(null);
 let rejected=false;try{SalahMoonRuntime.setReferenceScene({mode:'physical-reference'})}catch{rejected=true}return {absent,rejected};}""")
 check(reference['absent'] and reference['rejected'],'reference-scene admission fence')
 final=await take('final')
 for row in records:
  bound=(row['moon'].get('phasePrecision') or {}).get('targetPositionErrorBound')
  if bound is not None:check(bound<=.041600001,'phase displacement exceeded unchanged bound in '+row['name'])
  check(abs(row['photo']['width']-before['photo']['width'])<.5,'body footprint changed in '+row['name'])
 return {'status':'PASS' if not failures else 'FAIL','failures':failures,
  'settingsRoute':{'route':'.buckle.interactive -> input events on #set-lat/#set-lon/#set-label -> #setClose click, twice',
   'aGeneration':before['native']['generation'],'bGeneration':ui_b['native']['generation'],'returnedAGeneration':ui_a['native']['generation'],'storageScope':'Disposable test origin/profile only'},
  'aBA':ab,'reference':reference,'records':records,'scope':'Actual settings UI round-trip followed by separately labelled programmatic rapid A-B-A/clock/profile controls after ordinary first fifteen seconds; not passive startup timing evidence.'}
