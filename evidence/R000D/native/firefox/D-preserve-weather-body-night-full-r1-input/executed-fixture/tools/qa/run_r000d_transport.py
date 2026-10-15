"""Native HTTP headers/body/Image lifetime and automatic eligible recovery.

Requires root capacity-one lease. Actual 10s application deadlines are never
accelerated. Only radar retry cooldown may use the explicitly selected wall offset.
"""
import argparse
import base64
import json
import os
from pathlib import Path
import runpy
import sys
import time
import traceback
from urllib.request import Request,urlopen

HERE=Path(__file__).resolve().parent
H=runpy.run_path(str(HERE/'weather_native_http.py'));N=H['N']

def control_release(server,row):
    body=json.dumps({'run':server.run,'document':row['document'],'requestId':row['requestId']}).encode()
    request=Request(server.origin+'/control/release',data=body,headers={'Content-Type':'application/json','X-Weather-Test-Token':server.token},method='POST')
    with urlopen(request,timeout=3)as response:
        if response.status!=200 or json.load(response)!={'released':True}:raise AssertionError('Owned control release failed')

GAP_CASES=('D-ignore-abort-weather-body-day','D-superseded-weather-body-day',
           'D-preserve-weather-body-night-reduced','D-preserve-weather-body-night-full')

def validate_gap_spec(spec):
    t=spec.get('transport',{});gap=t.get('gap')
    if spec.get('id')not in GAP_CASES or spec.get('group')!='R000D' or spec.get('clock')!='real1x' or t.get('stage')!='weather-body':
        raise ValueError('Closed real-clock weather-body gap case required')
    if gap not in('ignored-abort','superseded-target','preservation')or t.get('retryClock')!='real1x':
        raise ValueError('Closed gap/real initial retry policy required')
    expected_gap=dict(zip(GAP_CASES,('ignored-abort','superseded-target','preservation','preservation')))
    if expected_gap[spec['id']]!=gap:raise ValueError('Case identity does not match its reviewed gap')
    if gap=='superseded-target' and (spec.get('local')is not True or spec.get('profileB')!={'lat':21.42,'lon':39.83,'label':'Deadline site B','units':'c','tz':'Asia/Riyadh'}):
        raise ValueError('Actual seeded-local settings profile B required')
    if gap=='preservation':
        if not spec.get('night')or spec.get('motion')!='reduce' or t.get('heldNumbers')!=[2,3] or t.get('abortPolicy')!='native-signal':
            raise ValueError('Preservation requires a healthy first acquisition then held second/third and native signal')
        if spec.get('watchMotionSeconds')!=15 or t.get('expiryClock')!='real1x-source-TTL-boundary':
            raise ValueError('Preservation watch/clock disclosure changed')
        if bool(spec.get('motionFull'))!=(spec['id'].endswith('-full')):raise ValueError('Reduced/full case identity mismatch')
    elif t.get('heldNumbers')!=[1,2] or t.get('abortPolicy')!='ignore-old-weather-signal' or spec.get('night'):
        raise ValueError('Late-body gap requires only old A signal omission and held A/B')
    return gap

def gap_no_renewal(before,after):
    return (before['consumer']['raw']==after['consumer']['raw'] and before['cacheRaw']==after['cacheRaw']
            and before['lastWxAt']==after['lastWxAt'] and before['weatherWrites']==after['weatherWrites']
            and before.get('weatherMutations',[])==after.get('weatherMutations',[]))

def old_cannot_touch_active(before,after,kind):
    # Compare the complete captured owner, attempt, failure diagnostic and namespace.
    keys=['requests','slots']
    return (all(before[key][kind]==after[key][kind] for key in keys)
            and before['wxBusy' if kind=='weather' else 'radarBusy']==after['wxBusy' if kind=='weather' else 'radarBusy']
            and temporal_no_renewal(before,after,kind)
            and (kind!='weather' or (before['weatherTrack']==after['weatherTrack'] and before['lastWxTry']==after['lastWxTry'])))

def gap_active_owner(state,operation,generation):
    s=state['temporal'];slot=s['slots']['weather']
    return bool(slot and slot['operationId']==operation and slot['generation']==generation and s['wxBusy'])

def claim_fresh_output(path):
    # Atomically refuse any existing output directory, even if empty; no prior receipts overwritten.
    path=Path(path).resolve();path.mkdir(parents=True,exist_ok=False);return path

def preserve_and_close(report,args,server,context,browser):
    # Save the original observations before teardown can fail. Cleanup errors are
    # distinct evidence and never replace an earlier case exception or verdict.
    report['nativeHttpEvents']=server.state();report['httpLedger']=server.ledger
    report['sourceUnchanged']=N['sha']((args.root/'index.html').read_bytes())==args.expected_index
    if not report['sourceUnchanged']:report['status']='FAIL_SOURCE_DRIFT'
    report['teardown']={'status':'PENDING','operations':[]}
    N['write_json'](args.out/'pre-teardown.json',report)
    for name,owner in (('context.close',context),('browser.close',browser)):
        if owner is None:continue
        try:
            owner.close();report['teardown']['operations'].append({'operation':name,'status':'RETURNED'})
        except Exception:
            report['teardown']['operations'].append({'operation':name,'status':'ERROR','exception':traceback.format_exc()})
    report['teardown']['status']='ERROR'if any(x['status']=='ERROR'for x in report['teardown']['operations'])else'RETURNED'
    N['write_json'](args.out/'post-teardown.json',report)

def gap_prayer_rows(state):
    p=state['preservation'];render=p.get('prayerRender')or{};rows=p.get('prayerRows')or[]
    keys=['Fajr','Sunrise','Dhuhr','Asr','Maghrib','Isha']
    fixture={'Fajr':'05:00','Sunrise':'06:00','Dhuhr':'12:00','Asr':'15:30','Maghrib':'18:00','Isha':'19:30'}
    def formatted(value):
        try:h,m=map(int,value.split(':'))
        except (ValueError,AttributeError):return None
        if not 0<=h<24 or not 0<=m<60:return None
        return f'{h:02}:{m:02}'if p.get('prayer24h')else f'{h%12 or 12}:{m:02} '+('PM'if h>=12 else'AM')
    timetable=render.get('timetable')or{}
    return (p.get('prayerLoaded')is True and [row.get('key')for row in rows]==keys
      and all(timetable.get(key)==fixture[key]for key in keys)
      and all(row.get('time')==formatted(render.get('nextTime')if row.get('next')else timetable.get(row['key']))for row in rows)
      and [row['key']for row in rows if row.get('next')]==[render.get('nextKey')]
      and p.get('prayerChip')==formatted(render.get('nextTime'))
      and render.get('generation')==state['temporal']['generation']
      and render.get('timetableDate')in('07-09-2026','08-09-2026')
      and isinstance(render.get('nextEpoch'),(int,float)) and render['nextEpoch']>render.get('acceptedUtcMs',float('inf'))
      and bool(p.get('prayerCountdown'))and not any(x in p['prayerCountdown']for x in('NaN','undefined','—')))

def temporal_no_renewal(before,after,kind):
    # The stalled operation owns only its own admission namespace; the other provider may succeed normally.
    if kind=='radar':return before['radar']==after['radar']and before['lastRadarAt']==after['lastRadarAt']
    return (before['weather']==after['weather']
      and before['cacheRaw']==after['cacheRaw']and before['lastWxAt']==after['lastWxAt']
      and [x for x in before['storageEvents']if x[0]in('set','remove','clear')and (len(x)<2 or x[1].startswith('salahwx:'))]
        ==[x for x in after['storageEvents']if x[0]in('set','remove','clear')and (len(x)<2 or x[1].startswith('salahwx:'))])

def gap_preservation(state,spec):
    s=state['consumer'];p=state['preservation']
    return {'cardGeometry':s['card']['width']==325 and s['card']['height']==530,
            'footerFits':s['footer']['top']>=0 and s['footer']['bottom']<=530.1,
            'prayerAvailable':p['prayerLoaded']is True and len(p['prayerRows'])==6 and all(row['time']and row['time']!='—'for row in p['prayerRows']),
            'actualPrayerRows':gap_prayer_rows(state),
            'motionPolicy':p['reducedNative']is True and p['reducedEffective']is(not bool(spec.get('motionFull')))
                           and p['fullOverride']is bool(spec.get('motionFull')) and p['fullClass']is bool(spec.get('motionFull')),
            'realTimeScene':p['followsWall']is True and p['timeScale']==1 and p['visibility']=='visible' and p['paused']is False}

def gap_capture(page,out,name,night):
    for selector,suffix in(('.c','card'),('.h','header'),('.d','footer'),('.times','prayers')):
        page.locator(selector).screenshot(path=str(out/(name+'-'+suffix+'.png')))
    if night:page.locator('.moon').screenshot(path=str(out/(name+'-moon.png')))

def observed_motion(page,out,name,read,seconds=30):
    """Original native PNG checkpoints and raw painted canvas; no scene calls or clock seek."""
    started=time.monotonic();checkpoints=[]
    for offset in (0,10,20,seconds):
        while time.monotonic()-started<offset:page.wait_for_timeout(200)
        state=read();tag=name+'-motion-'+str(offset)
        # Readback is bracketed around genuine browser screenshots. This is sampled
        # Firefox evidence, not a continuous no-blank recording/physical scanout claim.
        page.locator('.c').screenshot(path=str(out/(tag+'-card.png')))
        box=page.locator('.c').bounding_box()
        page.screenshot(path=str(out/(tag+'-sky.png')),clip={'x':box['x']+8,'y':box['y']+42,'width':309,'height':77})
        canvas=page.locator('.cloudcanvas').evaluate('(c)=>c.toDataURL("image/png")')
        (out/(tag+'-cloud-canvas.png')).write_bytes(base64.b64decode(canvas.split(',',1)[1]))
        checkpoints.append({'offset':offset,'elapsedMs':(time.monotonic()-started)*1000,'before':state,'after':read()})
    return {'scope':'natural 1x native PNG sky/card checkpoints and existing raw cloud canvas; no cloud hash; Chromium continuous context video separately retained',
      'elapsedMs':(time.monotonic()-started)*1000,'checkpoints':checkpoints,
      'cloudCanvasDelta':N['pixel_delta'](out/(name+'-motion-0-cloud-canvas.png'),out/(name+'-motion-'+str(seconds)+'-cloud-canvas.png')),
      'visibleSkyDelta':N['pixel_delta'](out/(name+'-motion-0-sky.png'),out/(name+'-motion-'+str(seconds)+'-sky.png')),'pixelReview':'PENDING'}

def gap_watch(page,out,name,read,report,deadline=None):
    # Native monotonic watch; no timer wrapper or accelerated deadline. Pixel disposition stays independent.
    before=read()
    page.locator('.c').screenshot(path=str(out/(name+'-card-before.png')))
    started=time.monotonic();terminal=None;before_deadline=None
    while time.monotonic()-started<15:
        state=read();report['timeline'].append({'phase':name,'state':state})
        s=state['temporal']
        if deadline is not None:
            if s['monotonic']<deadline:before_deadline=state
            if terminal is None and s['slots']['weather']is None and not s['wxBusy'] and s['requests']['weather'] and s['requests']['weather']['reason']=='body timeout':terminal=state
        page.wait_for_timeout(200)
    after=read()
    page.locator('.c').screenshot(path=str(out/(name+'-card-after.png')))
    return {'scope':'actual real-monotonic fifteen-second card crops; Chromium context video when configured, no continuous Firefox-video claim; independent sky/cloud pixel review required',
            'realWatchMs':(time.monotonic()-started)*1000,'before':before,'after':after,
            'motionPixels':N['pixel_delta'](out/(name+'-card-before.png'),out/(name+'-card-after.png')),'motionPixelScope':'whole-card delta; no automatic cloud-motion verdict',
            'firstTerminal':terminal,'lastBeforeDeadline':before_deadline,'visualReview':'PENDING'}

def run_gap(args,spec,launch_browser,browser_identity,sync_playwright):
    gap=validate_gap_spec(spec);report={'status':'PREPARED_TO_RUN','sourceSha256':args.expected_index,'case':spec,'gap':gap,
      'timeline':[],'checks':{},'visualReview':'PENDING','nativeTimers':'Unmodified setTimeout/performance.now',
      'clockScope':'real1x; preservation starts at2026-09-07T18:43:28Z with synthetic first source21:30 Riyadh, crossing source TTL naturally during body2. No Date offset or real fifteen-minute receipt-age proof.',
      'savedImageCallbackScope':'Not executed here; retain separately bound contained callback proof; no physical Image cancellation or memory claim'}
    context=None
    with H['TransportServer'](args.root,spec,args.run)as server,sync_playwright()as pw:
        browser=launch_browser(pw);report['browser']=browser_identity(browser)
        try:
            context,page,errors,network,url=N['open_case'](browser,server,spec,args.expected_index,args.run,1,args.out,wait_acquisition=False)
            report['url']=url;read=lambda:page.evaluate('()=>__weatherCases.deadlineGapRead(__weatherCases.identity())')
            if gap=='preservation':
                N['wait'](page,'()=>{const s=__weatherCases.deadlineGapRead(__weatherCases.identity());return s.temporal.prayerLoaded&&!s.temporal.wxBusy&&s.consumer.modelEligible&&s.consumer.temperature==="20°"&&s.consumer.precip==="on"&&s.consumer.visibleParticles>0;}',timeout=30000)
                admitted=read();report['admitted']=admitted
                report['checks']['admittedOriginal']=admitted['consumer']['raw']is not None and admitted['consumer']['raw']['temp']==20 and admitted['consumer']['modelEligible']is True and admitted['cacheRaw']is not None
                gap_capture(page,args.out,'admitted',True)
            old_number=2 if gap=='preservation'else 1
            N['wait'](page,'()=>{const s=__weatherCases.deadlineGapRead(__weatherCases.identity());return s.temporal.prayerLoaded&&s.temporal.slots.weather!==null&&s.temporal.requests.weather?.state==="body"&&s.transportRows.filter(x=>x.transport.kind==="weather").length===OLD_NUMBER;}'.replace('OLD_NUMBER',str(old_number)),timeout=110000 if gap=='preservation'else 10000)
            initial=read();report['held']=initial;slot=initial['temporal']['slots']['weather'];deadline=slot['deadlineAt'];operation=slot['operationId'];generation=slot['generation']
            old=next(x for x in server.state()if x['kind']=='weather'and x['number']==old_number)
            report['checks']['actualHeldBody']=bool(old['held']and old['headersFlushedAt']is not None and old['prefixBytes']>0 and old['finishedAt']is None)
            report['checks']['nativeResponseBody']=any(x['transport']['kind']=='weather'and x['transport']['number']==old_number and x.get('nativeResponse')is True and x['jsonReads']==1 for x in initial['transportRows'])
            gap_capture(page,args.out,'held',bool(spec.get('night')))
            if gap=='superseded-target':
                profile=spec['profileB']
                page.locator('.buckle').focus();page.keyboard.press('Enter')
                N['wait'](page,"()=>document.querySelector('.c').classList.contains('settings-open')&&document.activeElement.id==='set-label'",timeout=3000)
                page.locator('#set-lat').fill(str(profile['lat']));page.locator('#set-lon').fill(str(profile['lon']))
                page.locator('#set-label').fill(profile['label']);page.locator('#set-units').select_option(profile['units'])
                page.keyboard.press('Escape')
                N['wait'](page,"()=>!document.querySelector('.c').classList.contains('settings-open')&&document.activeElement===document.querySelector('.buckle')",timeout=3000)
                report['transition']={'cause':'actual Enter/open, coordinate/label input and Escape/close settings controls; native commitSettings save:true','profileB':profile,'state':read()}
                N['wait'](page,'old=>{const s=__weatherCases.deadlineGapRead(__weatherCases.identity());return s.temporal.slots.weather!==null&&s.temporal.slots.weather.operationId!==old&&s.temporal.requests.weather?.state==="body";}',operation,timeout=10000)
                active=read();report['activeSuccessor']=active
                report['checks']['supersededGeneration']=active['target']['generation']==generation+1 and active['target']['lat']==profile['lat'] and active['target']['lon']==profile['lon'] and active['cacheKey']!=initial['cacheKey']
                report['checks']['cancelDoesNotCommit']=gap_no_renewal(initial,active)
                report['checks']['capturedActualProfile']=active['temporal']['slots']['weather']['captured']=={'lat':profile['lat'],'lon':profile['lon'],'units':profile['units'],'requestZone':profile['tz'],'weatherCacheKey':active['cacheKey']}
                saved=json.loads(active['preservation']['localConfigRaw']or'null')
                report['checks']['actualSettingsPersistence']=bool(saved and all(saved.get(key)==profile[key]for key in profile))
            else:
                if gap=='preservation':
                    # Await weather source expiry under the unmodified 1x clock.
                    # No Moon/readiness predicate or later-frame substitution.
                    report['expiryBefore']=read()
                    N['wait'](page,'()=>{const s=__weatherCases.deadlineGapRead(__weatherCases.identity());return !s.consumer.modelEligible&&s.consumer.temperature===""&&s.consumer.precip==="off"&&s.consumer.visibleParticles===0;}',timeout=3000)
                    expired=read();report['expiredCurrent']=expired;gap_capture(page,args.out,'expired-current',True)
                    before_expiry=report['expiryBefore'];ew=expired['temporal']['wall'];bw=before_expiry['temporal']['wall']
                    em=expired['temporal']['monotonic'];bm=before_expiry['temporal']['monotonic']
                    report['sourceAgeExpiry']={'kind':'real1x-source-TTL-boundary','sourceUtcMs':initial['consumer']['raw']['currentValidAt'],
                      'beforeWall':bw,'expiredWall':ew,'beforeMonotonic':bm,'expiredMonotonic':em,
                      'wallVsMonotonicDeltaMs':(ew-bw)-(em-bm),'deadlineAt':deadline,'DateOffsetUsed':False,
                      'limitation':'Initially aged synthetic source; no real fifteen-minute receipt/cache-age qualification'}
                    report['checks']['sourceExpiryInHeldBody']=gap_active_owner(expired,operation,generation) and em<deadline and ew-initial['consumer']['raw']['currentValidAt']>900000
                    report['checks']['noAstronomyClockSeek']=abs((ew-bw)-(em-bm))<1000 and not any(x.get('action')=='clock-advance' for x in expired['fixture']['weatherEvents'])
                    report['checks']['expiryNoRenewal']=gap_no_renewal(initial,expired)
                    report['checks']['rawRetainedButIneligible']=expired['consumer']['raw']==initial['consumer']['raw'] and expired['consumer']['modelEligible']is False and expired['consumer']['temperature']=='' and expired['consumer']['precip']=='off'
                    report['preservationHeld']=gap_preservation(initial,spec);report['preservationExpired']=gap_preservation(expired,spec)
                    report['heldToTerminalWatch']=gap_watch(page,args.out,'held-to-terminal',read,report,deadline)
                    terminal=report['heldToTerminalWatch']['firstTerminal'];before=report['heldToTerminalWatch']['lastBeforeDeadline']
                else:
                    before=None;terminal=None;limit=time.monotonic()+15
                    while time.monotonic()<limit:
                        state=read();report['timeline'].append({'phase':'deadline','state':state});s=state['temporal']
                        if s['monotonic']<deadline and gap_active_owner(state,operation,generation):before=state
                        if s['slots']['weather']is None and not s['wxBusy'] and s['requests']['weather']and s['requests']['weather']['reason']=='body timeout':terminal=state;break
                        page.wait_for_timeout(100)
                if terminal is None:raise AssertionError('Actual native body deadline did not release A')
                gap_capture(page,args.out,'terminal',bool(spec.get('night')))
                if gap=='preservation':report['preservationTerminal']=gap_preservation(terminal,spec)
                report['beforeDeadline']=before;report['terminal']=terminal;report['deadlineDeliveryLatenessMs']=terminal['temporal']['monotonic']-deadline
                report['checks'].update(applicationTimeout=terminal['temporal']['monotonic']>=deadline,
                  nativeBusyBefore=before is not None and before['temporal']['monotonic']<deadline and gap_active_owner(before,operation,generation),
                  timeoutNoRenewal=gap_no_renewal(initial,terminal))
                next_number=old_number+1;limit=time.monotonic()+110
                active=None
                while time.monotonic()<limit:
                    state=read();report['timeline'].append({'phase':'successor-wait','state':state});s=state['temporal'];rows=server.state()
                    held=next((x for x in rows if x['kind']=='weather'and x['number']==next_number and x['held']and x['prefixBytes']>0),None)
                    if held and s['slots']['weather']is not None and s['slots']['weather']['operationId']!=operation and s['requests']['weather']['state']=='body':active=state;break
                    page.wait_for_timeout(200)
                if active is None:raise AssertionError('Existing native poll did not acquire held B')
                report['activeSuccessor']=active
                report['checks']['eligibleRetryWall']=active['lastWxTry']-initial['lastWxTry']>=60000
                if gap=='ignored-abort':
                    a_native=next(x for x in initial['transportRows']if x['transport']['kind']=='weather'and x['transport']['number']==old_number)
                    b_native=next(x for x in active['transportRows']if x['transport']['kind']=='weather'and x['transport']['number']==next_number)
                    report['checks']['actualRealSixtySecondRetry']=b_native['transport']['realDispatchAt']-a_native['transport']['realTryAt']>=60000
                else:report['retryLimitation']='A04 uses an initially aged synthetic source and natural 1x expiry; this is not a real fifteen-minute receipt/cache-age watch'
            new_slot=active['temporal']['slots']['weather'];held=next(x for x in server.state()if x['kind']=='weather'and x['number']==old_number+1)
            control_release(server,old)
            if gap in('ignored-abort','superseded-target'):
                N['wait'](page,'n=>__weatherCases.deadlineGapRead(__weatherCases.identity()).transportRows.some(x=>x.transport.kind==="weather"&&x.transport.number===n&&x.bodyOutcome==="fulfilled")',old_number,timeout=3000)
            page.wait_for_timeout(200);after_old=read();report['afterOldRelease']=after_old
            report['checks']['oldCannotReleaseB']=gap_active_owner(after_old,new_slot['operationId'],new_slot['generation'])
            report['checks']['oldCannotTouchFullSuccessor']=old_cannot_touch_active(active['temporal'],after_old['temporal'],'weather')
            report['checks']['oldCannotCommitOrPersist']=gap_no_renewal(active,after_old)
            if gap=='preservation':report['preservationAfterOld']=gap_preservation(after_old,spec)
            if gap in('ignored-abort','superseded-target'):
                old_native=next(x for x in after_old['transportRows']if x['transport']['kind']=='weather'and x['transport']['number']==old_number)
                report['oldNativeBody']=old_native
                report['checks']['ignoredSignalActuallyAborted']=old_native['transport']['signalCaptured']is True and old_native['transport']['signalPassed']is False and bool(old_native['signalEvents'])
                report['checks']['lateNativeJsonFulfilled']=old_native.get('nativeResponse')is True and old_native.get('bodyOutcome')=='fulfilled' and old_native['jsonReads']==1
                if gap=='ignored-abort':report['checks']['lateBodyAfterDeadline']=old_native['bodySettledAt']>=deadline
            control_release(server,held)
            N['wait'](page,'()=>{const s=__weatherCases.deadlineGapRead(__weatherCases.identity());return s.temporal.slots.weather===null&&!s.temporal.wxBusy&&s.temporal.requests.weather?.state==="received"&&s.consumer.temperature==="20°"&&s.consumer.precip==="on"&&s.consumer.visibleParticles>0;}',timeout=10000)
            recovered=read();report['recovered']=recovered
            report['checks']['actualHealthyConsumer']=recovered['consumer']['raw']['temp']==20 and recovered['consumer']['modelEligible']is True and recovered['consumer']['qa']['wxTruth']['activePrecip']is True and recovered['consumer']['qa']['wxTruth']['observedPresent']is False and recovered['consumer']['qa']['wxTruth']['activeThunder']is False and recovered['consumer']['lightning']=='off'
            information=recovered['consumer']['information']
            report['checks']['modelQualifiedPresentation']=('CURRENT MODEL ESTIMATE'in(information['description']or'') or (
                args.expected_index=='d4e3f084aea7d264a5c790268a21aa015b5e565e1feb9ad853d953c1c8a7b26f'
                and information['description']is None and recovered['consumer']['modelEligible']is True
                and information['name']==information['title']==information['header']['label']
                and 'Open-Meteo current model estimate'in information['title']
                and 'direct local observation unavailable (unobserved)'in information['title']))
            report['checks']['newTargetAdmitted']=recovered['consumer']['raw']['target']['generation']==new_slot['generation'] and recovered['cacheRaw']is not None and recovered['lastWxAt']>active['lastWxAt']
            gap_capture(page,args.out,'recovered',bool(spec.get('night')))
            report['recoveredWatch']=gap_watch(page,args.out,'recovered',read,report)
            if gap=='preservation':report['originalMotionObservation']=observed_motion(page,args.out,'recovered',read)
            if gap=='preservation':
                report['preservationRecovered']=gap_preservation(recovered,spec)
                report['checks']['preservationGuards']=all(report['preservationHeld'].values())and all(report['preservationExpired'].values())and all(report['preservationRecovered'].values())and all(report['preservationTerminal'].values())and all(report['preservationAfterOld'].values())
                report['checks']['headerStackStable']=initial['preservation']['header']==recovered['preservation']['header'] and initial['preservation']['footer']==recovered['preservation']['footer']
                report['checks']['nativeMotionWatchDuration']=report['heldToTerminalWatch']['realWatchMs']>=15000 and report['recoveredWatch']['realWatchMs']>=15000
                report['moonOpacityReview']='PENDING independent native moon/card crops and clip; no stars-through/opaque proof from metrics alone'
            report['accessibility']=N['accessibility'](page);report['pageErrors']=errors;report['network']=network;report['final']=read()
            report['checks']['noUnhandledOrPageErrors']=not errors and not report['final']['fixture']['consoleErrors']
            report['checks']['isolatedExactConsumer']=report['final']['fixture']['storageIsolated']is True and report['final']['fixture']['sourceSha256']==args.expected_index
            report['status']='EXECUTED_PENDING_NATIVE_PIXEL_REVIEW'if all(value is True for value in report['checks'].values())else'FAIL_OR_UNVERIFIED'
        except Exception:report.update(status='FAILED_HARNESS_OR_CONSUMER',exception=traceback.format_exc())
        finally:
            preserve_and_close(report,args,server,context,browser)
        report['nativeHttpEvents']=server.state();report['httpLedger']=server.ledger
        report['writeErrorClassification']='Retain actual abort/broken-pipe events; normal-signal cancellation is not delivered late-body evidence'
    report['sourceUnchanged']=N['sha']((args.root/'index.html').read_bytes())==args.expected_index
    if not report['sourceUnchanged']:report['status']='FAIL_SOURCE_DRIFT'
    N['write_json'](args.out/'receipt.json',report);print(json.dumps({'status':report['status'],'out':str(args.out)}))
    return 0 if report['status']=='EXECUTED_PENDING_NATIVE_PIXEL_REVIEW'else 1


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path);p.add_argument('--out',type=Path);p.add_argument('--expected-index')
    p.add_argument('--browser',choices=['chromium','firefox'],default='chromium');p.add_argument('--stage',choices=['weather-headers','weather-body','manifest-headers','manifest-body','image'],default='weather-body')
    p.add_argument('--retry-clock',choices=['wall-offset','real1x'],default='real1x');p.add_argument('--scene',choices=['day','night'],default='day')
    p.add_argument('--case',choices=GAP_CASES);p.add_argument('--run',default='r000d-owned-native');p.add_argument('--list',action='store_true');args=p.parse_args()
    spec=next(x for x in N['load_cases']()if x['id']==(args.case or 'D-'+args.stage+'-'+args.scene))
    if args.case:validate_gap_spec(spec);args.stage=spec['transport']['stage'];args.scene='night'if spec.get('night')else'day'
    if args.list:print(json.dumps(spec,indent=2));return 0
    if not args.root or not args.out or not args.expected_index:p.error('--root --out --expected-index are required')
    if args.stage.startswith('weather-')and args.retry_clock!='real1x':p.error('Weather retry requires actual60s and the existing render opportunity')
    spec['transport']['retryClock']=args.retry_clock;args.root=args.root.resolve();args.out=claim_fresh_output(args.out)
    if N['sha']((args.root/'index.html').read_bytes())!=args.expected_index:raise ValueError('Exact source identity precondition failed')
    os.environ['SALAH_BROWSER']=args.browser;sys.path.insert(0,str(args.root/'tools'/'cp9'))
    from browser_runtime import launch_browser,browser_identity
    from playwright.sync_api import sync_playwright
    if args.case:return run_gap(args,spec,launch_browser,browser_identity,sync_playwright)
    report={'status':'PREPARED_TO_RUN','sourceSha256':args.expected_index,'case':spec,'stage':args.stage,'retryClock':args.retry_clock,'timeline':[],'checks':{},'visualReview':'PENDING'}
    context=None
    with H['TransportServer'](args.root,spec,args.run)as server,sync_playwright()as pw:
        browser=launch_browser(pw);report['browser']=browser_identity(browser)
        try:
            context,page,errors,network,url=N['open_case'](browser,server,spec,args.expected_index,args.run,1,args.out,wait_acquisition=False)
            read=lambda:page.evaluate('()=>__weatherCases.temporalRead(__weatherCases.identity())')
            image_read=lambda:page.evaluate('()=>__weatherCases.transportImages(__weatherCases.identity())')
            kind='weather'if args.stage.startswith('weather-')else'radar';target=server.target_kind()
            expected='image'if target=='image'else'fetch'if args.stage.endswith('-headers')else'body'
            N['wait'](page,'kind=>__weatherCases.temporalRead(__weatherCases.identity()).prayerLoaded&&__weatherCases.temporalRead(__weatherCases.identity()).slots[kind]!==null',kind,timeout=10000)
            N['wait'](page,'v=>__weatherCases.temporalRead(__weatherCases.identity()).requests[v.kind]?.state===v.stage',{'kind':kind,'stage':expected},timeout=10000)
            first=read();report['initial']=first;report['url']=url;deadline=first['slots'][kind]['deadlineAt'];operation=first['slots'][kind]['operationId']
            for selector,name in(('.c','held-card'),('.h','held-header'),('.d','held-footer')):page.locator(selector).screenshot(path=str(args.out/(name+'.png')))
            before=None;terminal=None;end=time.monotonic()+15
            while time.monotonic()<end:
                state=read();report['timeline'].append(state);slot=state['slots'][kind]
                if state['monotonic']<deadline and slot and slot['operationId']==operation and slot['generation']==first['slots'][kind]['generation'] and state['wxBusy'if kind=='weather'else'radarBusy']:before=state
                if state['slots'][kind]is None and not state['wxBusy'if kind=='weather'else'radarBusy'] and 'timeout'in(state['requests'][kind]or{}).get('reason',''):
                    terminal=state;break
                page.wait_for_timeout(100)
            report['beforeDeadline']=before
            if terminal is None:raise AssertionError('Actual native application timeout did not release its owner')
            report['terminal']=terminal;report['deadlineDeliveryLatenessMs']=terminal['monotonic']-deadline;report['imagesAtTimeout']=image_read()
            page.locator('.c').screenshot(path=str(args.out/'expired-card.png'))
            report['checks'].update(applicationTimeout=terminal['monotonic']>=deadline,ownerReleased=terminal['slots'][kind]is None,
              reasonMatches=(terminal['requests'][kind]['reason']==expected+' timeout'),nativeBusyBefore=before is not None and before['monotonic']<deadline and bool(before['slots'][kind]) and before['slots'][kind]['operationId']==operation and before['slots'][kind]['generation']==first['slots'][kind]['generation'] and before['wxBusy'if kind=='weather'else'radarBusy'])
            report['checks']['timeoutNoRenewal']=temporal_no_renewal(first,terminal,kind)
            old=next(x for x in server.state()if x['kind']==target and x['number']==1)
            if kind=='radar'and args.retry_clock=='wall-offset':
                report['clockOffset']=page.evaluate('()=>__weatherCases.retryWallOffset(__weatherCases.identity(),600001)')
            successor=None;limit=time.monotonic()+(100 if kind=='weather'or args.retry_clock=='wall-offset'else 660)
            while time.monotonic()<limit:
                state=read();report['timeline'].append(state)
                rows=server.state();held=next((x for x in rows if x['kind']==target and x['number']==2),None)
                if held and state['slots'][kind]is not None and state['slots'][kind]['operationId']!=operation:
                    successor=(held,state);break
                page.wait_for_timeout(200)
            if successor is None:raise AssertionError('Existing native retry opportunity did not acquire replacement B')
            held,active=successor;report['activeSuccessor']=active;new_operation=active['slots'][kind]['operationId']
            control_release(server,old);page.wait_for_timeout(200)
            after_old=read();report['afterOldRelease']=after_old;report['imagesAfterOldRelease']=image_read()
            report['checks']['oldCannotReleaseB']=after_old['slots'][kind]is not None and after_old['slots'][kind]['operationId']==new_operation and after_old['wxBusy'if kind=='weather'else'radarBusy']
            report['checks']['oldCannotTouchFullSuccessor']=old_cannot_touch_active(active,after_old,kind)
            report['checks']['oldCannotCommitOrPersist']=temporal_no_renewal(active,after_old,kind)
            report['checks']['eligibleRetryWall']=(active['lastWxTry']-first['lastWxTry']>=60000)if kind=='weather'else(active['lastRadarAt']-first['lastRadarAt']>=600000)
            control_release(server,held)
            N['wait'](page,'kind=>{const s=__weatherCases.temporalRead(__weatherCases.identity());return s.slots[kind]===null&&!s[kind==="weather"?"wxBusy":"radarBusy"]&&s.requests[kind]?.state==="received";}',kind,timeout=10000)
            N['wait'](page,'()=>{const s=__weatherCases.deadlineGapRead(__weatherCases.identity()).consumer;return s.temperature==="20°"&&s.precip==="on"&&s.visibleParticles>0;}',timeout=10000)
            recovered=read();report['recovered']=recovered;report['imagesAtRecovery']=image_read()
            report['checks']['actualHealthyConsumer']=recovered['weather']['temp']==20 and recovered['wxTruth']['activePrecip']and not recovered['wxTruth']['observedPresent']and not recovered['wxTruth']['activeThunder']
            report['checks']['radarRecovery']=kind!='radar'or(recovered['radar']is not None and recovered['wxTruth']['radarAvailable']and recovered['wxTruth']['radarMm']==0)
            if target=='image':
                images=report['imagesAfterOldRelease'];report['checks']['imageHandlersDetached']=bool(images and images[0]['handlersDetached']and images[0]['nativeImage'])
                report['nativeLateImageEvent']='Inspect retained actual native load/error event; physical cancellation is not asserted'
            for selector,name in(('.c','recovered-card'),('.h','recovered-header'),('.d','recovered-footer')):page.locator(selector).screenshot(path=str(args.out/(name+'.png')))
            page.locator('.c').screenshot(path=str(args.out/'motion-card-before.png'));page.wait_for_timeout(15000);page.locator('.c').screenshot(path=str(args.out/'motion-card-after.png'))
            report['motionPixels']=N['pixel_delta'](args.out/'motion-card-before.png',args.out/'motion-card-after.png');report['motionPixelScope']='whole-card delta; no automatic cloud-motion verdict';report['accessibility']=N['accessibility'](page)
            report['finalTemporal']=read();report['imagesAtEnd']=image_read()
            geometry=page.evaluate('()=>__weatherCases.deadlineGapRead(__weatherCases.identity()).consumer')
            report['checks']['cardGeometry']=geometry['card']['width']==325 and geometry['card']['height']==530 and geometry['footer']['bottom']<=530.1
            report['checks']['noPageErrors']=not errors;report['pageErrors']=errors;report['network']=network
            report['status']='EXECUTED_PENDING_NATIVE_PIXEL_REVIEW'if all(v is True for v in report['checks'].values())else'FAIL_OR_UNVERIFIED'
        except Exception:report.update(status='FAILED_HARNESS_OR_CONSUMER',exception=traceback.format_exc())
        finally:
            preserve_and_close(report,args,server,context,browser)
        report['nativeHttpEvents']=server.state();report['httpLedger']=server.ledger
        report['writeErrorClassification']='Retained abort/broken-pipe events require the joined application-timeout/old-owner receipts; errors are not discarded'
    report['sourceUnchanged']=N['sha']((args.root/'index.html').read_bytes())==args.expected_index
    if not report['sourceUnchanged']:report['status']='FAIL_SOURCE_DRIFT'
    N['write_json'](args.out/'receipt.json',report);print(json.dumps({'status':report['status'],'out':str(args.out)}));return 0 if report['status']=='EXECUTED_PENDING_NATIVE_PIXEL_REVIEW'else 1

if __name__=='__main__':raise SystemExit(main())
