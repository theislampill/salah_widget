"""Owned Chromium lifecycle supplement using the installed driver's noDefaults.

The standard automation driver forces every page focused/visible. The existing
noDefaults CDP option leaves native tab visibility intact in its default context.
Each case gets a fresh private profile and actual product/fixture bytes. Native
events and original before/after pixels are retained; no motion clip is claimed.
"""
import argparse,json,os,subprocess,time,traceback
from pathlib import Path
import run_r0024_native as native

class DefaultContext:
    def __init__(self,context,options):self.context=context;self.options=options
    def __getattr__(self,name):return getattr(self.context,name)
    def new_page(self):
        page=self.context.new_page();page.set_viewport_size({'width':390,'height':600})
        session=self.context.new_cdp_session(page)
        session.send('Emulation.setTimezoneOverride',{'timezoneId':'Asia/Riyadh'})
        page.emulate_media(reduced_motion=self.options['reduced_motion'])
        # These emulations remain owned by the attached session for this page.
        page._r0024_environment_session=session
        return page

class OwnedBrowser:
    def __init__(self,browser):self.browser=browser
    def new_context(self,**options):
        native.require(options['viewport']=={'width':390,'height':600} and options['device_scale_factor']==1 and options['timezone_id']=='Asia/Riyadh','Exact environment required')
        return DefaultContext(self.browser.contexts[0],options)

def connect_without_defaults(pw,endpoint):
    # Python1.57's public signature predates this installed1.60 driver option.
    # Add only the documented driver wire field for this one connection, then
    # restore the channel method. No installed files or browser state are patched.
    channel=pw.chromium._impl_obj._channel;original=channel.send_return_as_dict
    async def send(method,timeout,params=None,*args,**kwargs):
        native.require(method=='connectOverCDP','Unexpected connection operation')
        return await original(method,timeout,{**params,'noDefaults':True},*args,**kwargs)
    channel.send_return_as_dict=send
    try:return pw.chromium.connect_over_cdp(endpoint)
    finally:channel.send_return_as_dict=original

def run_case(args,pw,server,base,oracle,spec,attempt,out):
    profile=out/'private-profile';profile.mkdir();log=(out/'browser.log').open('w',encoding='utf-8')
    command=[str(args.executable),'--headless','--no-first-run','--no-default-browser-check','--remote-debugging-port=0','--user-data-dir='+str(profile),'about:blank']
    process=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
    row={'id':spec['id'],'attempt':attempt,'input':spec,'status':'NOT_RUN','launch':command,'connection':{'noDefaults':True,'context':'fresh private profile default context'},'limitations':['No continuous clip from this lifecycle supplement; no motion qualification'],'checks':{}};browser=None;page=None
    try:
        end=time.monotonic()+20;active=profile/'DevToolsActivePort'
        while not active.exists() and time.monotonic()<end:
            native.require(process.poll() is None,'Owned browser exited during startup');time.sleep(.1)
        lines=active.read_text().splitlines();browser=connect_without_defaults(pw,'ws://127.0.0.1:'+lines[0]+lines[1]);row['browserVersion']=browser.version
        context,page,errors,network,url=base.open_case(OwnedBrowser(browser),server,spec,native.read_json(native.BINDING)['entrySha256'],args.run,attempt,out)
        row['url']=url;row['fixtureIdentity']=page.evaluate('()=>__weatherCases.identity()');row['seedDescriptions']=page.evaluate(native.approved_seed())
        row['environment']=page.evaluate('()=>({width:innerWidth,height:innerHeight,dpr:devicePixelRatio,zone:Intl.DateTimeFormat().resolvedOptions().timeZone,reduced:matchMedia("(prefers-reduced-motion:reduce)").matches})')
        native.require(row['environment']=={'width':390,'height':600,'dpr':1,'zone':'Asia/Riyadh','reduced':False},'Actual environment mismatch')
        row['captureEnvironment']={'driverViewport':page.viewport_size,'nativeLayout':page._r0024_environment_session.send('Page.getLayoutMetrics'),'visualViewport':page.evaluate('()=>({width:visualViewport.width,height:visualViewport.height,scale:visualViewport.scale,offsetLeft:visualViewport.offsetLeft,offsetTop:visualViewport.offsetTop})'),'scope':'Recorded before actions and first suspension capture; independent original-pixel review remains required'}
        row['actionReceipts']=[];row['nativeReceipts']=[]
        for i,action in enumerate(spec.get('actions',[])):
            row['actionReceipts'].append(page.evaluate('i=>__weatherCases.step(__weatherCases.identity(),i)',i));native.publication(page,base,{'wet':True})
        for step in spec.get('nativeSteps',[]):row['nativeReceipts'].append(page.evaluate('k=>__r24NativeControl.run(__r24NativeControl.identity(),k)',step['kind']))
        row['suspension']=native.suspension(page,context,base,spec,'chromium',out)
        expected={**spec['expect'],'group':'R0024'}
        if spec['suspend'].get('recover'):expected.update(wet=True,modelEstimate=True)
        native.publication(page,base,expected);state=page.evaluate('()=>__weatherCases.read(__weatherCases.identity())');ax=native.ax_read(page,base)
        row['checks']={**page.evaluate('e=>__weatherCases.checks(__weatherCases.read(__weatherCases.identity()),e)',expected),**row['suspension']['checks'],'noPageErrors':not errors}
        info=oracle.info_checks(state,ax,spec);row['checks'].update({'INFO:'+k:v for k,v in info.items() if isinstance(v,bool)})
        row.update(state=state,accessibility=ax,INFOOracle=info,nativeObservation=native.observation(page),pageErrors=errors,network=network,providerLedger=page.evaluate('()=>__widgetFixture.ledger'))
        for selector,name in [('.c','card'),('.h','header'),('.d','footer')]:page.locator(selector).screenshot(path=str(out/(name+'.png')))
        row['status']='EXECUTED_PENDING_PIXEL_AND_INDEPENDENT_REVIEW' if all(row['checks'].values()) else 'FAIL'
    except Exception:
        row['status']='FAILED_CONSUMER_OR_HARNESS';row['exception']=traceback.format_exc()
        if page:
            try:row['failureObservation']=native.observation(page);page.locator('.c').screenshot(path=str(out/'failure-card.png'))
            except Exception:row['failureCaptureException']=traceback.format_exc()
    finally:
        if browser:
            try:browser.close()
            except Exception:pass
        try:process.wait(timeout=5)
        except subprocess.TimeoutExpired:process.terminate();process.wait(timeout=5)
        log.close()
    native.write_json(out/'receipt.json',row);return row

def main():
    p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);p.add_argument('--input-sha',dest='admission_sha',required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--executable',type=Path,required=True);p.add_argument('--driver-cli',type=Path,required=True);p.add_argument('--driver-node',type=Path,required=True);p.add_argument('--run',required=True);a=p.parse_args();a.root=native.PROPOSED;a.browser='chromium';native.BINDING=a.input
    lease,cap,pre=native.lease_preflight(a);native.require(not a.out.exists(),'New immutable output required')
    from playwright.sync_api import sync_playwright
    base=native.helper_module();oracle=native.load('r0024_info_resume',a.root/'tools/qa/info_contract.py');lock=a.out.parent.parent/'native-resource.lock'
    with lock.open('x',encoding='utf-8') as f:json.dump({'pid':os.getpid(),'kind':'serial owned Chromium native lifecycle','out':str(a.out)},f)
    report={'schema':'r0024-native-resume/v1','preflight':pre,'admissionSha256':a.admission_sha,'capability':cap,'lease':lease,'cases':[],'status':'STARTED'}
    try:
        a.out.mkdir();specs=[s for s in native.cases() if s.get('suspend')]
        with base.FixtureServer(a.root) as server,sync_playwright() as pw:
            for attempt,spec in enumerate(specs,1):
                out=a.out/spec['id'];out.mkdir();row=run_case(a,pw,server,base,oracle,spec,attempt,out);report['cases'].append(row);native.write_json(a.out/'results.json',report);print(json.dumps({'case':row['id'],'status':row['status']}),flush=True)
                if row['status']!='EXECUTED_PENDING_PIXEL_AND_INDEPENDENT_REVIEW':break
            report['httpLedger']=server.ledger
        report['sourcePostflight']=native.source_preflight(a.root);report['status']='EXECUTED_PENDING_PIXEL_AND_INDEPENDENT_REVIEW' if len(report['cases'])==4 and all(r['status']=='EXECUTED_PENDING_PIXEL_AND_INDEPENDENT_REVIEW' for r in report['cases']) else 'FAIL';native.write_json(a.out/'results.json',report);print(report['status']);return 0 if report['status'].startswith('EXECUTED') else 1
    finally:lock.unlink()
if __name__=='__main__':raise SystemExit(main())
