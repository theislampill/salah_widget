"""Bounded, serial actual-consumer driver. --validate-only never launches a browser.

Uses installed Playwright and the repository browser_runtime launcher. The fixture
replaces ingress inputs and observes real renders; it never seeds product state.
Native claims remain PARTIAL pending independent pixels/preservation review.
"""
import argparse, functools, hashlib, http.server, importlib.util, json, os
import subprocess, sys, threading, time, base64, re, math
from pathlib import Path
from urllib.parse import quote

def digest(data):
    return hashlib.sha256(data).hexdigest()

def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")

def validate_cases(packet, root):
    if packet.get("schema") != "remaining-prayer-cases/v1":
        raise ValueError("case schema mismatch")
    if packet["issue"] not in (2,3,4,6,7):
        raise ValueError("issue outside bounded assignment")
    for relative, expected in packet["sourceFiles"].items():
        path=(root/relative).resolve()
        if not path.is_relative_to(root.resolve()) or digest(path.read_bytes()) != expected:
            raise ValueError("bound source bytes drifted: "+relative)
    names=set()
    if not packet['cases']:raise ValueError('native case selection cannot be empty')
    for case in packet["cases"]:
        required={"caseId","entry","hash","clockPolicy","cacheSeeds","responseRules","orderedActions","expected"}
        if not required.issubset(case) or case["caseId"] in names:
            raise ValueError("incomplete or duplicate case")
        names.add(case["caseId"])
        if case["entry"] not in ("index.html","offline.html"):
            raise ValueError("consumer entry not admitted")
        if not case["expected"] or not case["orderedActions"]:
            raise ValueError("case cannot pass by doing nothing")
        if case["clockPolicy"]["mode"] not in ("native","fixed","advancing"):
            raise ValueError("clock policy unsupported")
        for action in case["orderedActions"]:
            if action["type"] not in ("wait","release","reject","setRule","clock","settings","capture","sleep","iframeVisibility","dialog","checkpoint","waitImage","releaseImage"):
                raise ValueError("unsupported action: "+action["type"])
            if action.get('firstRender') and not action.get('firstPredicate'):
                raise ValueError('first-render capture requires an exact observation predicate')
        if "simTime=23%3A30" in case["hash"]:
            if "timeScale" in case["hash"] or case["clockPolicy"]["mode"] != "fixed":
                raise ValueError("frozen overnight must omit timeScale and fix pre-boot epoch")
    return {"status":"PREPARED_NOT_EXECUTED","caseCount":len(names),"sourceFiles":packet["sourceFiles"]}

def check_expected(trace, expected):
    rows=trace["snapshots"]
    for item in expected:
        if item.get("reviewOnly"):
            continue
        stage=item.get("stage")
        candidates=[s for s in rows if not stage or s.get("checkpoint")==stage]
        if item.get("firstCurrent"):
            candidates=[s for s in rows if s.get("stage")=="render-completed" and s.get("currentDay") and s.get("render")]
            candidates=candidates[:1]
        if item.get("noCurrentDay"):
            if any(s.get("currentDay")==item["noCurrentDay"] and s.get("render") for s in rows):
                raise AssertionError("forbidden current paint "+item["noCurrentDay"])
            continue
        if not candidates:
            raise AssertionError("no actual consumer receipt for "+str(item))
        row=candidates[-1]
        for key, value in item.get("equals",{}).items():
            actual=row
            for part in key.split("/"):
                actual=actual[part]
            if actual != value:
                raise AssertionError(f"{key}: expected {value!r}, observed {actual!r}")
        for key,value in item.get("contains",{}).items():
            actual=row
            for part in key.split("/"):actual=actual[part]
            if value not in actual:raise AssertionError("missing actual consumer text: "+value)
        for key,bounds in item.get("numberRange",{}).items():
            actual=row
            for part in key.split("/"):actual=actual[part]
            if isinstance(actual,bool) or not isinstance(actual,(int,float)) or not math.isfinite(actual) or not bounds[0]<=actual<=bounds[1]:
                raise AssertionError("consumer value outside bounds: "+key)
        for key,pattern in item.get("regex",{}).items():
            actual=row
            for part in key.split("/"):actual=actual[part]
            if not isinstance(actual,str) or re.fullmatch(pattern,actual) is None:raise AssertionError("consumer text mismatch: "+key)
        for constraint in item.get("requestCounts",[]):
            requests=trace["requests"]
            if item.get("requestCountCheckpoint"):requests=[r for r in requests if r['realElapsedMs']<=row['realElapsedMs']]
            count=sum(1 for r in requests if r["kind"]==constraint["kind"] and (not constraint.get("day") or '/'+constraint["day"]+'?' in r["url"]))
            if "exact" in constraint and count!=constraint["exact"]:raise AssertionError("request count: "+str(count))
        policy=item.get('retryPolicy')
        if policy:
            requests=[r for r in trace['requests'] if r['kind']=='prayer' and '/'+policy['day']+'?' in r['url']]
            if len(requests)!=4:raise AssertionError('retry policy needs exactly four current attempts')
            owners=[r['owner']['current'] for r in requests]
            if any(o is None for o in owners):raise AssertionError('current ownership receipt absent')
            if len({o['operationId'] for o in owners[:3]})!=1 or owners[3]['operationId']==owners[0]['operationId']:
                raise AssertionError('three attempts and the next operation are not distinguished')
            if policy.get('recoveryFence'):
                fence=requests[0]['cooldown']['current']['nextTry']
                if trace['startedPerformance']+requests[3]['realElapsedMs']<fence:raise AssertionError('recovery starts before operation-start 60000ms fence')
            owned_timers=[o['attempt']['timer'] for o in owners]
            for timer_id in owned_timers:
                starts=[t for t in trace['timerLog'] if t['operation']=='start' and t['id']==timer_id]
                if len(starts)!=1 or starts[0]['ms']!=10000:raise AssertionError('full prayer-attempt deadline is not 10000ms')
                if timer_id in trace['activeTimers']:raise AssertionError('owned prayer-attempt timer survived settlement')
            if policy.get('fullBodyTimeouts'):
                for timer_id in owned_timers[:3]:
                    if not any(t['operation']=='fire' and t['id']==timer_id for t in trace['timerLog']):raise AssertionError('stalled json did not reach native attempt deadline')
                for i,backoff in enumerate((900,1800)):
                    between=[t for t in trace['timerLog'] if t['operation']=='start' and requests[i]['realElapsedMs']<=t['realElapsedMs']<=requests[i+1]['realElapsedMs'] and t['ms']==backoff]
                    if len(between)!=1:raise AssertionError('native backoff receipt absent or repeated')
        if item.get("unchangedFrom"):
            reference=[s for s in rows if s.get("checkpoint")==item["unchangedFrom"]["stage"]][-1]
            for key in item["unchangedFrom"]["paths"]:
                a=row;b=reference
                for part in key.split("/"):a=a[part];b=b[part]
                if a!=b:raise AssertionError("obsolete effect changed "+key)
        if item.get("noInvalidText"):
            for selector in (".cn",".nt",".left",".times","#ce","#ah",".arc"):
                text=row["dom"][selector].get("text","")+row["dom"][selector].get("html","")
                if any(token in text for token in ("NaN","Infinity","undefined")):
                    raise AssertionError("invalid rendered text "+selector)
        if row.get('render') and isinstance(row['render'],dict) and not row['render'].get('unavailable'):
            html=row['dom']['.times'].get('html','')
            for prayer in ('Fajr','Sunrise','Dhuhr','Asr','Maghrib','Isha'):
                if html.count('data-prayer-key="'+prayer+'"')!=1:raise AssertionError('actual timetable lacks one '+prayer+' row')
            if row['dom']['.arc'].get('tagName')!='svg' or '<path' not in row['dom']['.arc'].get('html',''):raise AssertionError('actual arc SVG is absent')

def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument("--issue",type=int,required=True)
    p.add_argument("--engine",choices=["chromium","firefox"],required=True)
    p.add_argument("--source-root",type=Path,required=True)
    p.add_argument("--cases",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--validate-only",action="store_true")
    p.add_argument("--video-only",action="store_true",help="Avoid screenshot-induced compositor changes; extract stills from retained native video afterward")
    p.add_argument("--case-id",action="append")
    p.add_argument("--capacity-lease",type=Path)
    args=p.parse_args(argv)
    root=args.source_root.resolve(); output=args.output.resolve()
    if output.is_relative_to(root):
        raise ValueError("evidence output must be outside source checkout")
    packet=json.loads(args.cases.read_text(encoding="utf-8"))
    if packet["issue"]!=args.issue:
        raise ValueError("issue identity mismatch")
    summary=validate_cases(packet,root)
    dump(output/"input-manifest.json",{"caseFile":str(args.cases.resolve()),"caseSha256":digest(args.cases.read_bytes()),"engineRequested":args.engine,"sourceRoot":str(root),**summary})
    if args.validate_only:
        print(json.dumps(summary));return 0
    if not args.capacity_lease:
        raise ValueError("root-issued capacity-one heavy-browser lease required before launch")
    lease=json.loads(args.capacity_lease.read_text(encoding="utf-8"))
    if lease.get("resource")!="heavy-browser" or lease.get("status")!="GRANTED" or lease.get("owner")!="prayer" or lease.get("sourceCommit")!=packet["sourceCommit"]:
        raise ValueError("capacity lease does not bind this prayer candidate")
    selected=[c for c in packet["cases"] if not args.case_id or c["caseId"] in args.case_id]
    if not selected or args.case_id and set(args.case_id)!={c["caseId"] for c in selected}:
        raise ValueError("unknown/empty case selection")
    # Pinned fixture path after proposed files are integrated, or sibling worker proposal.
    fixture=Path(__file__).resolve().parents[2]/"tests/rlgwo/prayer-browser-fixture.cjs"
    module_path=root/"tools/cp9/browser_runtime.py"
    module_spec=importlib.util.spec_from_file_location("prayer_browser_runtime",module_path)
    runtime=importlib.util.module_from_spec(module_spec);module_spec.loader.exec_module(runtime)
    os.environ["SALAH_BROWSER"]=args.engine
    from playwright.sync_api import sync_playwright
    receipts=[]
    for case in selected:
        if case.get("cacheSeedsFromCase"):
            previous=output/case["cacheSeedsFromCase"]/"trace.json"
            prior=json.loads(previous.read_text(encoding="utf-8"))
            if prior.get("status")!="PASS_ASSERTIONS_PENDING_PIXEL_REVIEW":raise ValueError("winning persistence input did not pass source consumer assertions")
            case={**case,"cacheSeeds":[s for s in prior["storage"] if s["key"].startswith(("salah:","salahwx:","salah_widget:config:"))],"cacheSeedsFromTraceSha256":digest(previous.read_bytes())}
        case_output=output/case["caseId"];case_output.mkdir(parents=True,exist_ok=True)
        case_file=case_output/"case-input.json";dump(case_file,case)
        html=subprocess.check_output(["node",str(fixture),str(root/case["entry"]),str(case_file)])
        dump(case_output/"document-hashes.json",{"source":digest((root/case["entry"]).read_bytes()),"observed":digest(html),"fixture":digest(fixture.read_bytes())})
        class Handler(http.server.SimpleHTTPRequestHandler):
            def do_GET(self):
                if self.path.split("?")[0]=="/"+case["entry"]:
                    self.send_response(200);self.send_header("Content-Type","text/html; charset=utf-8");self.send_header("Content-Length",str(len(html)));self.end_headers();self.wfile.write(html)
                elif self.path.split("?")[0]=="/__iframe.html":
                    markup=('<iframe id="actual-consumer" src="/'+case["entry"]+case["hash"]+'" width="330" height="534" style="border:0"></iframe>').encode()
                    self.send_response(200);self.send_header("Content-Type","text/html; charset=utf-8");self.end_headers();self.wfile.write(markup)
                else:super().do_GET()
            def log_message(self,*_args):pass
        server=http.server.ThreadingHTTPServer(("127.0.0.1",0),functools.partial(Handler,directory=str(root)))
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        trace={"caseId":case["caseId"],"status":"FAIL","actions":[],"snapshots":[],"captureMismatches":[],"variant":case.get('variant'),"expectedOracleFailure":case.get('expectedFailure',False)}
        playwright=None;browser=None;context=None;frame=None
        try:
            playwright=sync_playwright().start()
            if playwright:
                browser=runtime.launch_browser(playwright)
                context=browser.new_context(viewport={"width":370,"height":570},device_scale_factor=1,timezone_id="America/New_York",reduced_motion=case.get("motionPreference","no-preference"),record_video_dir=str(case_output/"video"),record_video_size={"width":370,"height":570})
                page=context.new_page();errors=[];page.on("pageerror",lambda error:errors.append(str(error)))
                image_pending={};image_receipts=[]
                def image_route(route):
                    target=next((r for r in case.get("imageRules",[]) if r["pathContains"] in route.request.url),None)
                    if not target:route.continue_();return
                    image_receipts.append({"stage":"native-image-request","url":route.request.url,"rule":target["id"],"at":time.monotonic()})
                    image_pending[target["id"]]=(route,target)
                    if not target.get("hold"):
                        route.fulfill(status=200,body=base64.b64decode(target["pngBase64"]),headers={"Content-Type":"image/png","Access-Control-Allow-Origin":"*"})
                        del image_pending[target["id"]]
                if case.get("imageRules"):page.route("**/fixture-radar-*/**",image_route)
                consumer=None
                if case.get("iframe"):
                    page.goto(f"http://127.0.0.1:{server.server_port}/__iframe.html",wait_until="domcontentloaded")
                    consumer=page.frame_locator("#actual-consumer")
                    frame=next(f for f in page.frames if f!=page.main_frame)
                else:
                    page.goto(f"http://127.0.0.1:{server.server_port}/{case['entry']}?case={quote(case['caseId'])}"+case["hash"],wait_until="domcontentloaded")
                    frame=page.main_frame
                dump(case_output/"browser-identity.json",runtime.browser_identity(browser))
                for action in case["orderedActions"]:
                    trace["actions"].append(action)
                    kind=action["type"]
                    if kind=="waitImage":
                        end=time.monotonic()+action.get("timeoutMs",15000)/1000
                        while action["id"] not in image_pending and time.monotonic()<end:page.wait_for_timeout(25)
                        if action["id"] not in image_pending:raise AssertionError("missing actual Image route "+action["id"])
                    elif kind=="releaseImage":
                        if action["id"] not in image_pending:raise AssertionError("missing held Image "+action["id"])
                        route,target=image_pending.pop(action["id"])
                        route.fulfill(status=200,body=base64.b64decode(target["pngBase64"]),headers={"Content-Type":"image/png","Access-Control-Allow-Origin":"*"})
                        image_receipts.append({"stage":"native-image-release","url":route.request.url,"rule":target["id"],"alpha":target["alpha"],"at":time.monotonic()})
                    elif kind=="wait":frame.wait_for_function(action["predicate"],timeout=action.get("timeoutMs",15000))
                    elif kind=="sleep":time.sleep(action["ms"]/1000)
                    elif kind=="release" or kind=="reject":frame.evaluate("([type,id,n])=>window.__prayerFixture[type](id,n)",[kind,action["id"],action.get("occurrence",1)])
                    elif kind=="setRule":frame.evaluate("([id,patch])=>window.__prayerFixture.setRule(id,patch)",[action["id"],action["patch"]])
                    elif kind=="clock":frame.evaluate("epoch=>window.__prayerFixture.setClock(epoch)",action["epoch"])
                    elif kind=="settings":
                        frame.locator(".buckle").click()
                        for name,value in action["fields"].items():
                            element=frame.locator("#set-"+name)
                            if name in ("method","school","units","time"):element.select_option(str(value))
                            else:element.fill(str(value))
                        frame.locator("#setClose").click()
                    elif kind=="iframeVisibility":
                        if not case.get("iframe"):raise ValueError("visibility control requires actual iframe")
                        page.locator("#actual-consumer").evaluate("(el,visible)=>el.style.display=visible?'block':'none'",action["visible"])
                    elif kind=="dialog":frame.locator(action["selector"]).click()
                    elif kind in ("checkpoint","capture"):
                        if action.get('firstRender'):
                            predicate=action.get('firstPredicate')
                            if not predicate:raise ValueError('first-render assertion requires an explicit observation predicate')
                            row=frame.evaluate("window.__prayerFixture.snapshots.find(s=>"+predicate+")")
                        else:row=frame.evaluate("window.__prayerFixture.readSnapshot()" if kind=="checkpoint" or action.get('readOnly') else "window.__prayerFixture.snapshots.filter(s=>s.stage!=='read-only-checkpoint').at(-1)")
                        if not row:raise AssertionError("no completed original render")
                        row["checkpoint"]=action["name"];trace["snapshots"].append(row)
                        if kind=="capture":
                            before=frame.evaluate("window.__prayerFixture.ordinal")
                            # Even page.screenshot(clip=...) changes recorded compositor
                            # dimensions in these engines. Keep the native viewport intact;
                            # retain the requested bounds for optional offline image crops.
                            bounds=frame.locator(action.get("selector",".c")).bounding_box()
                            if not args.video_only:
                                page.screenshot(path=str(case_output/(action["name"]+".png")))
                            after=frame.evaluate("window.__prayerFixture.ordinal")
                            dump(case_output/(action["name"]+"-presentation.json"),{"beforeOrdinal":before,"afterOrdinal":after,"receiptOrdinal":row["renderOrdinal"],"capture":"native-video-only" if args.video_only else "native-full-viewport","requestedSelector":action.get("selector",".c"),"requestedBounds":bounds,"viewport":page.viewport_size})
                            if action.get("preservation"):
                                # Separate warm-preservation checkpoint, never a first-prayer
                                # observer. The existing lunar diagnostic may admit a pending
                                # preview; retain the pre/post visible surface to expose that.
                                preservation=frame.evaluate("""(()=>{
                                  const photo=document.querySelector('.mphoto'),card=document.querySelector('.c');
                                  const before={href:photo?.getAttribute('href'),classes:card?.className};
                                  const state=window.SalahMoonRuntime?.state;
                                  return {wallUtcMs:Date.now(),realElapsedMs:performance.now()-window.__prayerFixture.started,
                                    native:window.SalahMoonHost?.capture(),state,consumed:prayerCopy(_lastMoonPaint),
                                    location:{lat,lon,tz},dpr:devicePixelRatio,
                                    motion:{preference:matchMedia('(prefers-reduced-motion: reduce)').matches,full:MOTIONFULL,reduced:isMotionReduced()},
                                    presentationCss:Object.fromEntries(['--moongrp','--moonfeat','--moonbeam'].map(k=>[k,getComputedStyle(card).getPropertyValue(k)])),
                                    before,after:{href:photo?.getAttribute('href'),classes:card?.className},
                                    geometry:prayerDom('.mphoto').geometry};
                                })()""")
                                dump(case_output/(action["name"]+"-preservation.json"),preservation)
                            if action.get("firstRender") and not (before==after==row["renderOrdinal"]):
                                # Preserve the failed still association. Continue collecting the
                                # native video and original assertions; this is not a first-frame PASS.
                                trace["captureMismatches"].append({"capture":action["name"],"beforeOrdinal":before,"afterOrdinal":after,"receiptOrdinal":row["renderOrdinal"]})
                                if action["name"]!="first-current":raise AssertionError("first-render crop crossed another product render")
                if args.video_only:
                    # Completed DOM writes can precede the recorder's next frame.
                    # Keep observing through native presentation before closing;
                    # do not advance the fixture clock or call product rendering.
                    page.wait_for_timeout(1000)
                    trace["nativePresentationTailMs"]=1000
                raw=frame.evaluate("(()=>{const f=window.__prayerFixture;return {startedPerformance:f.started,events:f.events,snapshots:f.snapshots,requests:f.requests,storageLog:f.storageLog,timerLog:f.timerLog,activeTimers:f.activeTimers(),storage:f.storage(),pending:f.pending(),unexpected:f.unexpected,assetEvents:f.assets,resourceTiming:f.resourceTiming(),fonts:{status:document.fonts.status,faces:[...document.fonts].map(f=>({family:f.family,status:f.status,style:f.style,weight:f.weight}))}}})()")
                trace["checkpointSnapshots"]=trace["snapshots"];trace["snapshots"]=raw["snapshots"]+trace["checkpointSnapshots"];trace.update({key:value for key,value in raw.items() if key!="snapshots"});trace["pageErrors"]=errors
                trace["nativeImageReceipts"]=image_receipts
                check_expected(trace,case["expected"])
                if raw["unexpected"] or errors:raise AssertionError("unmatched provider or page error")
                trace["status"]="PARTIAL_FIRST_PRESENTATION_REVIEW_REQUIRED" if trace["captureMismatches"] else "PASS_ASSERTIONS_PENDING_PIXEL_REVIEW"
        except Exception as error:
            trace["failure"]=repr(error)
            try:
                trace["rawOnFailure"]=frame.evaluate("(()=>{const f=window.__prayerFixture;return {events:f.events,snapshots:f.snapshots,requests:f.requests,storageLog:f.storageLog,timerLog:f.timerLog,unexpected:f.unexpected}})()")
                if not args.video_only:
                    page.screenshot(path=str(case_output/"failure.png"))
            except Exception as capture_error:trace["failureCapture"]=repr(capture_error)
        finally:
            dump(case_output/"trace.json",trace)
            if context:context.close()
            if browser:browser.close()
            if playwright:playwright.stop()
            server.shutdown();server.server_close();thread.join(timeout=2)
        receipts.append({"caseId":case["caseId"],"status":trace["status"],"trace":str(case_output/"trace.json")})
        print(args.engine,case["caseId"],trace["status"],trace.get("failure",""),flush=True)
    dump(output/"summary.json",{"status":"PARTIAL_NATIVE_REVIEW_REQUIRED","receipts":receipts,"preservation":"NOT_QUALIFIED_BY_DRIVER","leaseSha256":digest(args.capacity_lease.read_bytes())})
    return 1 if any(r["status"]=="FAIL" for r in receipts) else 0

if __name__=="__main__":
    raise SystemExit(main())
