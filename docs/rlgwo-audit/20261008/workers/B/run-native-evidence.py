"""PRIMARY-ONLY serial native date/arc proof; preparation/import does not launch.

Reuses original fixtures prepared by prepare-native-fixtures.cjs. Optional sky
catalogue and terrain transports receive explicit HTTP 503 in the disposable
fixture. Native fail-closed handling, config/prayer/date/model/drawArc/CSS remain.
This does not qualify astronomy, full-renderer startup, sleep or public origin.
"""
import argparse, hashlib, http.server, json, mimetypes, sys, threading, time
from pathlib import Path
from urllib.parse import urlsplit

BASE=Path(__file__).resolve().parent
ROOT=Path('C:/Users/theis/.codex/worktrees/hotfix-startup-clouds/salah_widget')
sys.path.insert(0,str(ROOT/'tools/cp9'))
from browser_runtime import launch_browser, browser_identity

SNAP=r'''() => {
 const el=s=>document.querySelector(s),box=n=>{const r=n.getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height,bottom:r.bottom,right:r.right};};
 const d=_lastDateTruth,fixture=window.__uiFixture||window.__calendarFixture;
 return {ready:!!fixture?.ready,renders:fixture?.renders,canary:window.__sw_sec_probe,
  ce:el('#ce').textContent,ah:el('#ah').textContent,ceHtml:el('#ce').innerHTML,ahHtml:el('#ah').innerHTML,
  ceNodes:el('#ce').querySelectorAll('svg,img,script').length,ahNodes:el('#ah').querySelectorAll('svg,img,script').length,
  preview:el('#ah .mph.pre')?.textContent||null,title:el('#ah').title,dateTruth:d,
  dialog:{gregorian:el('#dateGregorian').textContent,hijri:el('#dateHijri').textContent,preview:el('#datePreview').textContent,reason:el('#dateReason').textContent},
  ceLabel:el('#ceDateButton').getAttribute('aria-label'),ahLabel:el('#ahDateButton').getAttribute('aria-label'),
  prayerStale:_prayerStale,configSource:CONFIG.source,method:CONFIG.method,rows:document.querySelectorAll('.p').length,
  current:el('.cn').textContent,nextTime:el('.nt').textContent,countdown:el('.left').textContent,
  loadedDay:today?.date?.gregorian?.date,nextDay:tomorrow?.date?.gregorian?.date,
  width:innerWidth,height:innerHeight,card:box(el('.c')),footer:box(el('.d')),header:box(el('.h')),
  svg:el('.arc').innerHTML,markers:[...el('.arc').querySelectorAll('circle[data-prayer-key]')].map(n=>({key:n.getAttribute('data-prayer-key'),class:n.getAttribute('class'),status:n.getAttribute('data-adjustment'),title:n.querySelector('title')?.textContent,angle:n.getAttribute('data-angle'),x:n.getAttribute('cx'),y:n.getAttribute('cy'),r:n.getAttribute('r'),box:box(n),fill:getComputedStyle(n).fill,fillOpacity:getComputedStyle(n).fillOpacity,stroke:getComputedStyle(n).stroke,strokeWidth:getComputedStyle(n).strokeWidth,strokeOpacity:getComputedStyle(n).strokeOpacity,strokeDasharray:getComputedStyle(n).strokeDasharray})),
  effects:fixture?.effects?.()||{requests:fixture?.requests||[]},unexpectedFetch:fixture?.unexpectedFetch||[]};
}'''

def check(condition,description,rows):
    rows.append({'check':description,'pass':bool(condition)})
    if not condition: raise AssertionError(description)
def stable(s,c,positive_geometry=True):
    check(s['ready'] and s['renders']>=1 and s['rows']==6,'actual real boot/render completed with six rows',c)
    check(bool(s['current']) and bool(s['nextTime']),'non-empty actual prayer consumer positive',c)
    check(s['width']==325 and s['height']==530,'actual viewport325x530',c)
    check(abs(s['card']['width']-325)<.5 and abs(s['card']['height']-530)<.5,'actual card325x530',c)
    if positive_geometry:check(s['footer']['bottom']<=s['card']['bottom']+.5,'footer within card',c)
    check(s['header']['height']>0,'header remains measurable',c)
def projection(s,c):
    d=s['dateTruth'];check(d is not None,'last-painted decision exists',c)
    check(s['title']==d['explanation']==s['dialog']['reason'],'footer title and full-value reason match painted decision',c)
    check(s['dialog']['gregorian']==(d['gregorianText'] or 'Gregorian date unavailable'),'full Gregorian matches painted decision',c)
    check(s['dialog']['hijri']==(d['hijriText'] or 'Hijri date unavailable'),'full Hijri matches painted decision',c)
    check(s['dialog']['preview']==d['previewText'],'preview matches painted decision',c)
    check(s['ceLabel']==f"Show complete Gregorian date: {d['gregorianText'] or 'Gregorian date unavailable'}",'accessible CE matches painted selection',c)
    check(s['ahLabel']==f"Show complete Hijri date: {d['hijriText'] or 'Hijri date unavailable'}. {d['explanation']}",'accessible AH explanation matches selection',c)

def security(row,s,canary,c):
    mutant=row.get('mutant');name=row['name']
    # An intentionally unescaped SVG has native 300x150 default dimensions.
    # Its expected overflow must not mask the actual negative canary/node check.
    # Every repaired positive retains the original footer geometry requirement.
    stable(s,c,positive_geometry=not bool(mutant))
    if mutant:
        broken='ce' if mutant=='ce' else 'ah'
        check(s[broken+'Nodes']>=1,'own mutated real sink creates an injected node',c)
        check(s['canary']==1,'positive execution control: mutated SVG canary actually fires',c)
        if mutant!='preview':check(s[('ah' if broken=='ce' else 'ce')+'Nodes']==0,'other repaired sink remains node-free',c)
        return
    check(s['ceNodes']==0 and s['ahNodes']==0 and s['canary']==0,'both real sinks node-free and canary inert',c)
    check(not s['unexpectedFetch'],'original fixture rejects no unexpected external provider fetch',c)
    check(s['configSource']==row['expectedConfigSource'],'actual intended config ingress reaches renderer',c)
    if name in ('hash-format','saved-format','provider-month','stale-control'):
        check(canary in s['ce'] and canary in s['ah'],'literal hostile text retained at both real sinks',c)
    if name=='preview-day':check(s['preview'] and canary in s['preview'],'present preview keeps literal hostile day',c)
    if name=='after-maghrib':
        check(canary in s['ce'] and canary in s['ah'],'after-Maghrib hostile month remains literal',c)
        check(s['preview'] is None and s['dateTruth']['hijriText'].startswith('26 '),'actual tomorrow AH selected with preview absent',c)
    if name=='ordinary':
        check(s['ce']=='2026-09-07CE' and s['dateTruth']['hijriText']=='1448-03-25','ordinary exact date/era positive',c)
        check(s['preview'] and s['preview'].endswith('26'),'ordinary tomorrow preview present',c)
    if name=='held-out-tokens':
        check(s['dateTruth']['gregorianText']=='2026 26 September Sep 09 9 07 7','held-out Gregorian token oracle exact',c)
        check(s['dateTruth']['hijriText']=='1448 48 Rabi al-awwal Rab 03 3 25 25','held-out Hijri token oracle exact',c)
    if name=='literal-control':check('التاريخ "\' & < > 2026'==s['dateTruth']['gregorianText'],'Arabic quote ampersand angle literal exact',c)
    if name=='stale-control':check(s['prayerStale'] and 'stale' in s['ahHtml'],'trusted stale markup retained',c)
    check('class="er"' in s['ceHtml'] and 'class="er"' in s['ahHtml'],'trusted era markup survives',c)

def calendar_checks(row,s,c):
    stable(s,c)
    name=row['name'];d=s['dateTruth'];projection(s,c)
    if name in ('before','invalid-next','named-missing-name'):
        expected='' if name=='named-missing-name' else '1448-02-19'
        check(d['hijriText']==expected,'before-boundary selected today or named-format unavailable',c)
        if name in ('wrong-zone','invalid-next'):check(not d['previewDay'],'wrong/invalid next payload cannot preview',c)
    elif name in ('boundary','after','different-method','unknown-method'):
        check(d['hijriText']=='1448-02-20' and d['maghribRollApplied'] and s['preview'] is None,'at/after boundary actual tomorrow20 without preview',c)
    elif name in ('missing','late','wrong-day','wrong-zone'):
        check(d['hijriText']=='1448-02-19' and not d['maghribRollApplied'],'missing/wrong tomorrow retains today19',c)
        check(d['unavailableReason']=='Sunset date update unavailable' and 'Sunset date update unavailable' in s['ah'],'visible unavailable cue separate from prayer staleness',c)
        check(s['prayerStale'] is False and 'could not advance' in s['title'],'missing tomorrow not mislabeled advanced/current prayer stale',c)
    elif name=='absent':check(not d['hijriText'] and 'Hijri date unavailable' in s['ah'],'missing AH explicitly unavailable',c)
    if name=='different-method':check(d['hijriMethod']=='UAQ' and 'HJCoSA' not in s['title'] and s['method']=='4','selected tomorrowUAQ; prayer method preserved',c)
    if name=='unknown-method':check(d['hijriMethod'] is None and 'calendar convention unavailable' in s['title'],'unknown selected convention not inherited',c)
    if name in ('wrong-zone','invalid-next'):check(not d['previewDay'],'wrong/invalid next payload cannot preview',c)
    check(d['hijriAnomaly'] is None,'no unsupported anomaly certainty',c)

def arc_checks(row,s,c):
    stable(s,c);check(not any(x in s['svg'] for x in ('NaN','Infinity','undefined')),'finite actual emitted arc',c)
    marks={m['key']:m for m in s['markers']};check(len(marks)==6,'six actual native arc marker consumers',c)
    if row.get('mutant'):
        check(all('adj' not in marks[k]['class'].split() for k in ['Fajr','Isha']),'universal14 negative loses both actual London rings',c);return
    want={'london':('unreachable-angle','unreachable-angle'),'tromso':('unreachable-angle','unreachable-angle'),'madinah':('reachable-angle','unknown')}[row['name']]
    for key,status in zip(['Fajr','Isha'],want):
        m=marks[key];check(m['status']==status and bool(m['title']),key+' actual classification/title',c)
        check(('adj' in m['class'].split())==(status=='unreachable-angle'),key+' actual class agrees',c)
        check(m['box']['width']>0 and m['box']['height']>0,key+' rendered native marker has nonzero box',c)
        if status=='unreachable-angle':check(float(m['fillOpacity'])<1 and m['stroke']!='none' and float(m['strokeWidth'].rstrip('px'))>0 and m['strokeDasharray']!='none',key+' actual adjusted dashed ring and subdued fill styling',c)
    check('ring' in marks['Sunrise']['class'].split(),'Sunrise independent ring retained',c)
    if row['name']=='london':
        check([marks['Fajr'][k] for k in ['x','y','r']]==['19.37','134.93','5'] and [marks['Isha'][k] for k in ['x','y','r']]==['274.41','133.93','5'],'London exact original marker geometry retained',c)
        check(marks['Sunrise']['y']==marks['Maghrib']['y']=='104.00' and marks['Dhuhr']['x']=='149.84','London horizon and post-transit Dhuhr preserved',c)

def native_access(page,c,observations):
    # Native event/focus smoke for R0009's explanation consumer, not the full
    # long-value/fallback-font/accessibility matrix of R0019.
    for trigger,key in [('#ceDateButton','Enter'),('#ahDateButton','Space')]:
        page.locator(trigger).focus();page.locator(trigger).press(key)
        check(page.locator('#dateDialog').evaluate('(n)=>n.open'),'native keyboard opens selected disclosure',c)
        check(page.locator('#dateDialog').evaluate('(n)=>n.contains(document.activeElement)'),'native initial modal focus within dialog',c)
        focus=lambda:page.evaluate('''()=>{const n=document.querySelector('#dateDialog'),a=document.activeElement;return {open:n.open,modal:n.matches(':modal'),active:{tag:a?.tagName,id:a?.id},within:n.contains(a),documentHasFocus:document.hasFocus()};}''')
        before_tab=focus();page.keyboard.press('Tab');after_tab=focus();blocked=[]
        # Native browser UI is outside this document's focus ownership. With
        # one Close control, Tab may leave activeElement at BODY while the
        # native modal keeps all underlying widget controls inert. The original
        # contract asks for native containment, not an added circular JS trap.
        for background in ['#ceDateButton','#ahDateButton']:
            result=page.evaluate('''s=>{const n=document.querySelector(s);n.focus();const a=document.activeElement,d=document.querySelector('#dateDialog');return {target:s,reached:a===n,active:{tag:a?.tagName,id:a?.id},modal:d.matches(':modal'),open:d.open};}''',background)
            blocked.append(result)
        observations.append({'trigger':trigger,'key':key,'beforeTab':before_tab,'afterTab':after_tab,'backgroundFocusAttempts':blocked,'interpretation':'Native modal background containment tested; BODY/browser UI focus is recorded, no circular custom trap required.'})
        check(after_tab['open'] and after_tab['modal'] and all(not x['reached'] and x['modal'] and x['open'] for x in blocked),'native modal keeps underlying date triggers inert after Tab',c)
        page.keyboard.press('Escape');page.wait_for_function('!document.querySelector("#dateDialog").open')
        check(page.locator(trigger).evaluate('(n)=>document.activeElement===n'),'native Escape restores actual initiator',c)
    box=page.locator('#ahDateButton').bounding_box();page.touchscreen.tap(box['x']+box['width']/2,box['y']+box['height']/2)
    check(page.locator('#dateDialog').evaluate('(n)=>n.open'),'native touch opens explanation',c)
    page.locator('#dateClose').click();check(page.locator('#ahDateButton').evaluate('(n)=>document.activeElement===n'),'native Close restores touched initiator',c)

def settled_fonts(page,c):
    # Google CSS/font requests are explicitly aborted. A pending dynamic asset
    # script can hold FontFaceSet.ready even when there are zero font faces.
    # Settle astronomy transports and observe the actual browser font lifecycle
    # before the ordinary Playwright screenshot wait; never forge fonts.ready.
    receipt=page.evaluate('''async () => {
      let ready=false;
      await Promise.race([document.fonts.ready.then(()=>{ready=true;}),new Promise(r=>setTimeout(r,2000))]);
      const styles={};for(const s of ['#ce','#ah','.cn','#dateDialog']){
        const n=document.querySelector(s),v=getComputedStyle(n);
        styles[s]={family:v.fontFamily,size:v.fontSize,weight:v.fontWeight};
      }
      return {ready,documentState:document.readyState,status:document.fonts.status,
        faces:[...document.fonts].map(f=>({family:f.family,status:f.status})),styles,
        policy:'External Google font CSS/binaries aborted; actual system fallback. No FontFaceSet or screenshot-ready override.'};
    }''')
    check(receipt['ready'] and receipt['status']=='loaded' and all(f['status']=='loaded' for f in receipt['faces']),'actual font lifecycle settled before native screenshot; system fallback disclosed',c)
    return receipt

def run(a):
    from playwright.sync_api import sync_playwright
    manifest=json.loads((a.fixtures/'manifest.json').read_text(encoding='utf-8'))
    assert hashlib.sha256((a.root/'index.html').read_bytes()).hexdigest()==manifest['sourceSha256']
    assert hashlib.sha256((a.root/'config.js').read_bytes()).hexdigest()==manifest['configSha256']
    a.output.mkdir(parents=True,exist_ok=True);rows=[]
    selected=set(a.issues.split(','));cal_names=set('before boundary after missing late different-method unknown-method wrong-day wrong-zone invalid-next absent named-missing-name title-mutant hold-mutant'.split())
    fixtures=[r for r in manifest['rows'] if str(r['issue']) in selected and (r['issue']!=9 or r['name'] in cal_names)]
    if a.cases:
        selected_cases=set(a.cases.split(','));fixtures=[r for r in fixtures if r['id'] in selected_cases]
        assert {r['id'] for r in fixtures}==selected_cases,'Every requested minimal rerun case must exist and match --issues'
    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self,*args): pass
        def do_GET(self):
            u=urlsplit(self.path);parts=u.path.strip('/').split('/');data=None;mime=None
            if len(parts)>=3 and parts[0]=='fixture' and any(r['id']==parts[1] for r in manifest['rows']):
                relative='/'.join(parts[2:]);base=a.root
                if relative=='index.html':base=a.fixtures;relative=parts[1]+'.html'
                file=(base/relative).resolve()
                if file.is_file() and base.resolve() in file.parents:data=file.read_bytes();mime=mimetypes.guess_type(str(file))[0] or 'application/octet-stream'
            if data is None:self.send_response(404);self.end_headers();return
            self.send_response(200);self.send_header('Content-Type',mime+('; charset=utf-8' if mime.startswith('text/') else ''));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(data)
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler);threading.Thread(target=server.serve_forever,daemon=True).start()
    report={'schema':'B-primary-native-evidence/1','target':manifest['auditTarget'],'sourceSha256':manifest['sourceSha256'],'fixtureManifestSha256':hashlib.sha256((a.fixtures/'manifest.json').read_bytes()).hexdigest(),'driverSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'scope':'Actual HTTP native config/prayer/date/model/drawArc/CSS; deterministic original fixtures; optional catalogue/Moon asset transports receive explicit HTTP 503 and actual product unavailable handling; no whole-renderer astronomy/startup or public-origin claim','rows':rows,'primaryPixelReviewRequired':True,'preparedBy':'reviewerB','executedBy':'primary'}
    dump=lambda:(a.output/'results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    try:
      with sync_playwright() as p:
        browser=launch_browser(p);report['browser']=browser_identity(browser)
        for row in fixtures:
          started=time.monotonic();checks=[];errors=[];deferred=[];transport=[];font_requests=[];fonts=None;state=None;transitions=[];interactions=[]
          context=browser.new_context(viewport={'width':325,'height':530},device_scale_factor=1,has_touch=True,reduced_motion='reduce')
          def route(r):
              u=urlsplit(r.request.url)
              if u.path.endswith(('/real-sky/native-data.js','/moon/moon-worker.js','/moon/moon_kernel.wasm','/moon/assets/dem.bin.gz','/moon/assets/colour.bin.gz')) or '/moon/file-data/' in u.path:
                  deferred.append(r.request.url);transport.append({'url':r.request.url,'status':503,'policy':'explicit optional astronomy unavailability; no terrain solve'})
                  r.fulfill(status=503,content_type='text/plain',body='Controlled optional astronomy unavailability for date-only audit');return
              if u.hostname in ['fonts.googleapis.com','fonts.gstatic.com']:font_requests.append(r.request.url);r.abort();return
              r.continue_()
          context.route('**/*',route);page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
          error=None
          try:
            url=f'http://127.0.0.1:{server.server_port}/fixture/{row["id"]}/index.html?case={row["id"]}'+row['hash']
            page.goto(url,wait_until='domcontentloaded',timeout=20000)
            page.wait_for_function('!!(window.__uiFixture||window.__calendarFixture)?.ready',timeout=20000)
            if row.get('mutant') in ['ce','ah','preview']:page.wait_for_function('window.__sw_sec_probe===1',timeout=3000)
            # The original frozen scene may still await its actual admitted tomorrow.
            if row['kind']=='security':page.wait_for_function('!!tomorrow',timeout=4000)
            elif row['name'] not in ['missing','late','title-mutant','wrong-day','wrong-zone']:page.wait_for_function('!!tomorrow',timeout=4000)
            if row['name'] in ['wrong-day','wrong-zone']:
                # Actual maintainPrayerDay rejects these injected contexts and
                # legitimately clears tomorrow. Observe the rendered rejection,
                # never require a retained invalid bundle to declare readiness.
                page.wait_for_function('_lastDateTruth?.unavailableReason==="Sunset date update unavailable"',timeout=4000)
            page.evaluate('()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')
            state=page.evaluate(SNAP)
            if row['kind']=='security':security(row,state,manifest['canary'],checks)
            elif row['kind']=='markers':arc_checks(row,state,checks)
            elif row['name']=='title-mutant':
                stable(state,checks);check('already advanced' in state['title'] and 'could not advance' in state['dateTruth']['explanation'],'after-only title negative disagrees with actual missing-tomorrow decision',checks)
            else:
                calendar_checks(row,state,checks)
                if row['name']=='invalid-next':
                    page.evaluate('()=>{__calendarFixture.setInstant("2026-09-07T18:01:00Z");__calendarFixture.render();}')
                    invalid_after=page.evaluate(SNAP);projection(invalid_after,checks)
                    check(invalid_after['dateTruth']['hijriText']=='1448-02-19' and invalid_after['dateTruth']['maghribRollApplied'] is False and invalid_after['dateTruth']['unavailableReason']=='Sunset date update unavailable' and invalid_after['prayerStale'] is False,'native invalid next AH cannot advance after Maghrib and exposes independent unavailable cue',checks)
                    transitions.append({'name':'invalid-next-after-maghrib','state':invalid_after})
                if row['name']=='late':
                    page.evaluate('()=>__calendarFixture.releaseTomorrow()');page.wait_for_function('_lastDateTruth?.maghribRollApplied===true',timeout=5000)
                    first=page.evaluate(SNAP);page.evaluate('()=>__calendarFixture.render()');second=page.evaluate(SNAP)
                    projection(first,checks);check(first['dateTruth']['hijriText']=='1448-02-20' and first['dateTruth']==second['dateTruth'] and first['dateTruth']['unavailableReason'] is None,'native late arrival clears only calendar cue and repeats idempotently',checks)
                    transitions.append({'name':'released-tomorrow','state':second})
                if row['name'] in ['before','hold-mutant']:
                    for step in manifest['transitions']:
                        page.evaluate('(x)=>{__calendarFixture.setInstant(x.clock);__calendarFixture.admittedState(x.today,x.tomorrow);}',step)
                        snap=page.evaluate(SNAP);transitions.append({'name':step['name'],'state':snap})
                        if row['name']=='hold-mutant' and step['name']=='same-day-09':
                            check(snap['dateTruth']['hijriText']!='1448-02-09','backwards-hold negative retains future10 after accepted09 correction',checks);break
                        check(snap['dateTruth']['hijriText']==step['want'],'native '+step['name']+' selects exact admitted provider value',checks);projection(snap,checks)
                    if row['name']=='before':
                        spec=row['spec'];page.evaluate('(x)=>{__calendarFixture.setInstant(x.clock);__calendarFixture.admittedState(x.today,x.tomorrow);}',spec);native_access(page,checks,interactions)
                if row['name']=='missing':native_access(page,checks,interactions)
            check(not errors,'no native page script errors; optional unavailability is separately disclosed',checks)
            fonts=settled_fonts(page,checks)
            page.locator('.c').screenshot(path=str(a.output/(row['id']+'--card.png')),timeout=5000)
            page.locator('.d').screenshot(path=str(a.output/(row['id']+'--footer.png')),timeout=5000)
            if row['kind']=='markers':page.locator('.arc').screenshot(path=str(a.output/(row['id']+'--arc.png')),timeout=5000)
            if row['kind']=='calendar' and row['name'] in ['before','missing','different-method','unknown-method']:
                page.locator('#ahDateButton').click();page.locator('#dateDialog').screenshot(path=str(a.output/(row['id']+'--disclosure.png')),timeout=5000)
            check(not errors,'no native page script errors through final captures',checks)
          except Exception as e:error=repr(e)
          finally:
            rows.append({'id':row['id'],'issue':row['issue'],'sourceSha256':row['sourceSha256'],'fixtureSha256':row['fixtureSha256'],'checks':checks,'checkStatus':'FAIL' if error else 'PASS_SCOPED_NATIVE_CONSUMER','error':error,'pageErrors':errors,'optionalDeferred':deferred,'optionalTransport':transport,'blockedFontRequests':font_requests,'fonts':fonts,'fontPolicy':'Google web fonts blocked; actual system fallback CSS retained','state':state,'transitions':transitions,'interactionObservations':interactions,'negativeGeometryBoundary':'Security encoding mutants may expand footer through actual SVG default dimensions; positive cases retain unchanged geometry gate.' if row['kind']=='security' and row.get('mutant') else None,'seconds':time.monotonic()-started});dump();print(row['id'],rows[-1]['checkStatus'],error,flush=True);context.close()
        browser.close()
    finally:server.shutdown()
    report['status']='FAIL' if any(r['error'] for r in rows) else 'CAPTURED_PENDING_PRIMARY_PIXEL_REVIEW';dump();return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--fixtures',type=Path,default=BASE/'browser-fixtures');p.add_argument('--output',type=Path,required=True);p.add_argument('--issues',default='1,9,10');p.add_argument('--cases',help='Comma-separated exact prepared fixture IDs for a minimal rerun');a=p.parse_args();r=run(a);raise SystemExit(1 if r['status']=='FAIL' else 0)
