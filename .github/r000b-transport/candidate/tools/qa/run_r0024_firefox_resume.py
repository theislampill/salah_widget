"""One owned Firefox tab-resume case using its existing native Marionette API.

The installed Juggler agent forces every top-level docshell active/focused.
Clear only those two automation overrides on the exact fixture document, then
observe natural native tab events. Product scripts and native recording remain
unchanged. No privileged host APIs, window enumeration, or installed-file edits.
"""
import json,os,socket,time
import run_r0024_native as native

RESET="const d=window.docShell; const before={force:d.forceActiveState,focus:d.overrideHasFocus}; d.forceActiveState=false; d.overrideHasFocus=false; return {before,after:{force:d.forceActiveState,focus:d.overrideHasFocus},visibility:document.visibilityState};"

class Marionette:
    def __init__(self,sock):self.sock=sock;self.serial=0;self.commands=[];self.hello=self.receive()
    def receive(self):
        length=b''
        while not length.endswith(b':'):
            part=self.sock.recv(1)
            if not part:raise EOFError('Owned native socket closed')
            length+=part
        size=int(length[:-1]);data=b''
        while len(data)<size:
            part=self.sock.recv(size-len(data))
            if not part:raise EOFError('Owned native socket closed')
            data+=part
        return json.loads(data)
    def call(self,name,params):
        self.serial+=1;wire=json.dumps([0,self.serial,name,params]).encode();start=time.monotonic();self.sock.sendall(str(len(wire)).encode()+b':'+wire);response=self.receive()
        self.commands.append({'name':name,'params':params,'response':response,'elapsedMs':(time.monotonic()-start)*1000})
        native.require(response[0]==1 and response[1]==self.serial and response[2] is None,'Native command failed: '+str(response))
        return response[3]

PORT=None
def suspension(page,context,base,spec,engine,out):
    native.require(engine=='firefox' and spec['suspend']['kind']=='tab','Only declared Firefox tab case')
    before=native.observation(page);native.require(before['state']['precip']=='on','Actual wet before suspension required')
    particles="()=>[...document.querySelectorAll('.drop,.flake')].map(e=>({class:e.className,left:e.style.left,delay:e.style.animationDelay}))"
    history=page.evaluate(particles);page.locator('.c').screenshot(path=str(out/'before-suspension.png'))
    sock=socket.create_connection(('127.0.0.1',PORT),timeout=10);sock.settimeout(20);client=Marionette(sock)
    physical={'requested':'tab','kind':'tab','protocol':'Installed native Marionette with scoped docshell override reset','seconds':spec['suspend']['seconds'],'startedMonotonic':time.monotonic(),'commands':client.commands,'launchOverrides':{'args':['--marionette','--remote-allow-system-access'],'startupEnvironment':{'MOZ_MARIONETTE_PREF_STATE_ACROSS_RESTARTS':json.dumps({'marionette.port':PORT})}}}
    try:
        physical['session']=client.call('WebDriver:NewSession',{'capabilities':{'alwaysMatch':{}}})
        subject=client.call('WebDriver:GetWindowHandle',{})['value'];url=client.call('WebDriver:GetCurrentURL',{})['value']
        native.require(url==page.url and 'source='+native.read_json(native.BINDING)['entrySha256'] in url,'Native selected document must be the exact owned fixture URL')
        physical['subject']=subject;physical['url']=url
        reset=client.call('WebDriver:ExecuteScript',{'script':RESET,'args':[],'newSandbox':True,'sandbox':'system'})['value'];physical['reset']=reset
        native.require(reset['before']=={'force':True,'focus':True} and reset['after']=={'force':False,'focus':False},'Exact automation override reset required')
        physical['helper']=client.call('WebDriver:NewWindow',{'type':'tab','focus':True})
        base.wait(page,"()=>document.visibilityState==='hidden'&&document.querySelector('.c').classList.contains('paused')",timeout=3000);physical['hidden']=native.observation(page)
        time.sleep(spec['suspend']['seconds'])
        client.call('WebDriver:SwitchToWindow',{'handle':subject,'focus':True})
        base.wait(page,"()=>document.visibilityState==='visible'&&!document.querySelector('.c').classList.contains('paused')",timeout=3000)
    finally:
        native.write_json(out/'native-protocol.json',physical);sock.close()
    native.publication(page,base,{'wet':False});after=native.observation(page);page.locator('.c').screenshot(path=str(out/'expired-after-resume.png'))
    checks={'actualTrustedLifecycleObserved':any(e['type']=='visibilitychange' and e['trusted'] is True for e in after['nativeEvents']),
        'actualTrustedHiddenAndVisible':all(any(e['type']=='visibilitychange' and e['trusted'] is True and e['visibility']==v for e in after['nativeEvents']) for v in ['hidden','visible']),
        'expiredWetWithdrawn':after['state']['precip']=='off' and after['state']['visibleParticles']==0 and after['state']['lightning']=='off',
        'cloudPopulationRetained':before['cloud']['motion']['key']==after['cloud']['motion']['key'] and before['cloud']['motion']['population']==after['cloud']['motion']['population'] and before['cloud']['fieldSeed']==after['cloud']['fieldSeed'],
        'particleHistoryRetained':history==page.evaluate(particles)}
    result={'before':before,'after':after,'physicalOperation':physical,'checks':checks,'pixelContinuity':'PENDING independent original evidence review'}
    if spec['suspend'].get('recover'):
        result['recoveryKick']=page.evaluate('()=>__r24NativeControl.recovery(__r24NativeControl.identity())')
        base.wait(page,'()=>{const r=__r24NativeControl.read(__r24NativeControl.identity());return !r.state.wxBusy&&r.eligibility.eligible;}',timeout=12000);native.publication(page,base,{'wet':True})
        fresh=native.observation(page);result['recovered']=fresh;checks['freshAcquisitionRestoresModelOnly']=fresh['state']['raw']['retrievedAt']>before['state']['raw']['retrievedAt'] and fresh['state']['qa']['wxTruth']['observedPresent'] is False and fresh['state']['lightning']=='off';page.locator('.c').screenshot(path=str(out/'fresh-model-restored.png'))
    return result

def main():
    global PORT
    probe=socket.socket();probe.bind(('127.0.0.1',0));PORT=probe.getsockname()[1];probe.close()
    from playwright.sync_api import BrowserType
    original=BrowserType.launch
    def launch(self,**kwargs):
        native.require(self.name=='firefox','This entry owns only Firefox')
        # Juggler userPrefs are applied after process startup. Marionette reads
        # this supported scoped startup environment before opening its listener.
        env={**os.environ,'MOZ_MARIONETTE_PREF_STATE_ACROSS_RESTARTS':json.dumps({'marionette.port':PORT})}
        return original(self,**{**kwargs,'args':['--marionette','--remote-allow-system-access'],'env':env})
    select=native.select_cases
    def one_case(engine,matrix,ordered=None):
        complete,selected=select(engine,matrix,ordered);native.require(len(selected)==1 and selected[0].get('suspend',{}).get('kind')=='tab','Exactly one declared tab-resume case required');return complete,selected
    BrowserType.launch=launch;native.suspension=suspension;native.select_cases=one_case
    try:return native.main()
    finally:BrowserType.launch=original
if __name__=='__main__':raise SystemExit(main())
