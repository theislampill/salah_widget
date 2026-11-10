#!/usr/bin/env python3
"""One-off C19 icon consumer observation; not a replacement C18 acceptance collector."""
import argparse, base64, functools, hashlib, http.server, json, os, sys, threading, time, traceback, uuid
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlopen
from playwright.sync_api import sync_playwright

def document_url(url):
    return urlparse(url)._replace(fragment="").geturl()

def select_icon_requests(events, icon, consumer):
    rows=[]
    for event in events:
        if event["method"]!="Network.requestWillBeSent" or event["params"]["request"]["url"]!=icon:
            continue
        params=event["params"];rid=params["requestId"]
        relevant=(event["phase"]=="automatic-document" and params.get("frameId")==consumer["frameId"] and params.get("loaderId")==consumer["loaderId"] and document_url(params.get("documentURL",""))==consumer["documentURL"])
        rows.append({"request":event,"relevantConsumer":relevant,
          "responses":[e for e in events if e["method"]=="Network.responseReceived" and e["params"]["requestId"]==rid],
          "terminals":[e for e in events if e["method"] in ["Network.loadingFinished","Network.loadingFailed"] and e["params"]["requestId"]==rid]})
    return rows

def require_icon_consumption(rows, consumer):
    relevant=[row for row in rows if row["relevantConsumer"]]
    assert relevant, "No automatic icon request bound to the intended top-level document/frame/loader"
    ids=[row["request"]["params"]["requestId"] for row in rows]
    assert len(ids)==len(set(ids)), "Repeated icon request ID requires explicit redirect attribution"
    for row in rows:
        assert not row["request"]["params"].get("redirectResponse"), "Unexpected icon redirect"
        assert not any(e["params"]["response"]["status"]>=400 for e in row["responses"]), "Observed icon HTTP failure"
        assert not any(e["method"]=="Network.loadingFailed" for e in row["terminals"]), "Observed icon network failure"
    for row in relevant:
        assert len(row["responses"])==1, "Missing or ambiguous intended-consumer icon response"
        response=row["responses"][0]["params"]
        assert response["response"]["status"]==200 and response["response"]["mimeType"]=="image/svg+xml", "Intended icon response is not HTTP200 SVG"
        for key in ["frameId","loaderId"]:
            assert response.get(key)==consumer[key], "Icon response identity does not match the intended consumer"
        assert len(row["terminals"])==1 and row["terminals"][0]["method"]=="Network.loadingFinished", "Intended icon request lacks one observed successful terminal"
    return relevant

def require_no_icon_errors(events, icon):
    ids={e["params"]["requestId"] for e in events if e["method"]=="Network.requestWillBeSent" and e["params"]["request"]["url"]==icon}
    for event in events:
        if event["method"]=="Network.requestWillBeSent":
            assert urlparse(event["params"]["request"]["url"]).path!="/favicon.ico", "Origin-root fallback was requested"
        if event["method"]=="Log.entryAdded":
            entry=event["params"].get("entry",{})
            assert not (entry.get("level")=="error" and (entry.get("url")==icon or entry.get("networkRequestId") in ids)), "Observed icon-related error log"

def main(root, out):
    if out.exists() and any(out.iterdir()):
        raise RuntimeError("Refusing nonempty evidence directory")
    out.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(root / "tools/cp9"))
    from browser_runtime import browser_options, browser_identity
    sha = lambda b: hashlib.sha256(b).hexdigest()
    paths = ["tests/smoke.html", "tests/widget-fixture.html", "tests/r0017-smoke-icon.svg"]
    expected = json.loads((out.parent / "integrated/SOURCE_IDENTITY.json").read_text())
    for name in paths:
        assert sha((root/name).read_bytes()) == expected["files"][name]["sha256"], name
    result = {"schema":"r0017-icon-consumers/v1", "scope":"Two actual HTTP documents, automatic native icon requests and separate decode; no Windows/public/full-cleanliness/whole-smoke acceptance substitution", "source":expected, "status":"STARTED", "cases":[], "cleanup":{}, "startedUtc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())}
    def save():
        (out/"result.json").write_text(json.dumps(result,indent=2)+"\n")
    lock=threading.Lock()
    def record(file, data):
        with lock:
            with (out/file).open("a") as f:
                f.write(json.dumps({"receivedMonotonic":time.monotonic(),**data})+"\n")
    class Handler(http.server.SimpleHTTPRequestHandler):
        def log_message(self,*args): pass
        def send_response(self, code, message=None):
            record("http-server.jsonl",{"method":self.command,"path":self.path,"status":code})
            super().send_response(code,message)
        def translate_path(self, path):
            resolved=Path(super().translate_path(path)).resolve()
            if not resolved.is_relative_to(root):
                return str(root/"__outside_payload_refused__")
            return str(resolved)
    server=http.server.ThreadingHTTPServer(("127.0.0.1",0),functools.partial(Handler,directory=str(root)))
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    origin=f"http://127.0.0.1:{server.server_port}/"
    result["ownedServer"]={"origin":origin,"root":str(root),"pid":os.getpid(),"scope":"loopback static source; no rewritten responses"}
    save()
    browser=None
    try:
        with sync_playwright() as p:
            family,launch_options=browser_options()
            assert family=="chromium", "The icon CDP observation requires the explicitly selected Chromium engine"
            # Chromium exposes the actual owned command line only in automation mode.
            launch_options["args"]=[*launch_options.get("args",[]),"--enable-automation"]
            browser=getattr(p,family).launch(**launch_options)
            result["browser"]=browser_identity(browser)
            browser_cdp=browser.new_browser_cdp_session()
            result["browserCommandLine"]=browser_cdp.send("Browser.getBrowserCommandLine")
            result["processes"]=browser_cdp.send("SystemInfo.getProcessInfo")
            save()
            run="R0017-C19-icon-"+str(uuid.uuid4())
            docs=[
                ("wrapper","no-preference","tests/widget-fixture.html?mode=healthy&run="+run+"&attempt=1#lat=24.47&lon=39.61&label=Madinah&method=4&simTime=12:30&simWx=0&tz=Asia/Riyadh&qa=1",8000),
                ("smoke","reduce","tests/smoke.html?fixture=healthy",120000)]
            for name, motion, suffix, limit in docs:
                row={"name":name,"preference":motion,"url":origin+suffix,"readinessLimitMs":limit,"status":"STARTED","pageErrors":[],"consoleErrors":[],"automaticIcon":[]}
                result["cases"].append(row);save()
                context=browser.new_context(viewport={"width":1100,"height":900},device_scale_factor=1,reduced_motion=motion)
                page=context.new_page();cdp=context.new_cdp_session(page);events=[];phase={"value":"automatic-document"}
                def receive(method, params):
                    e={"phase":phase["value"],"method":method,"params":params}
                    events.append(e);record(name+"-cdp.jsonl",e)
                for method in ["Network.requestWillBeSent","Network.responseReceived","Network.loadingFinished","Network.loadingFailed","Log.entryAdded","Page.frameNavigated","Page.documentOpened"]:
                    cdp.on(method,lambda params,m=method:receive(m,params))
                page.on("pageerror",lambda e:row["pageErrors"].append(str(e)))
                page.on("console",lambda e:row["consoleErrors"].append(e.text) if e.type=="error" else None)
                for method in ["Page.enable","Network.enable","Log.enable"]:
                    cdp.send(method)
                try:
                    began=time.monotonic()
                    page.goto(row["url"],wait_until="domcontentloaded",timeout=min(limit,15000))
                    remaining=max(1,limit-(time.monotonic()-began)*1000)
                    predicate="window.__widgetFixture && ['ready','error'].includes(window.__widgetFixture.state)" if name=="wrapper" else "!!window.__smoke"
                    page.wait_for_function(predicate,timeout=remaining)
                    row["readyObservedMs"]=(time.monotonic()-began)*1000
                    row["document"]=page.evaluate("""() => ({
                      url:location.href, readyState:document.readyState,
                      icons:[...document.querySelectorAll('link[rel~="icon"]')].map(e=>({href:e.href,type:e.type})),
                      csp:[...document.querySelectorAll('meta[http-equiv="Content-Security-Policy"]')].map(e=>e.content),
                      preference:matchMedia('(prefers-reduced-motion: reduce)').matches,
                      fixture:window.__widgetFixture??null, smoke:window.__smoke??null, qa:window.qaState?.()??null
                    })""")
                    row["frameTree"]=cdp.send("Page.getFrameTree")
                    frame=row["frameTree"]["frameTree"]["frame"]
                    assert frame.get("id") and frame.get("loaderId") and not frame.get("parentId"), "Current top-level consumer identity unavailable"
                    assert document_url(frame["url"])==document_url(row["document"]["url"])==document_url(row["url"]), "Top-level document identity differs"
                    consumer={"frameId":frame["id"],"loaderId":frame["loaderId"],"documentURL":document_url(row["document"]["url"])}
                    row["consumerIdentity"]=consumer
                    if name=="wrapper":
                        assert row["document"]["fixture"]["state"]=="ready", "Wrapper did not reach existing ready state"
                    else:
                        row["automaticSmokeResult"]=row["document"]["smoke"]
                    icon=origin+"tests/r0017-smoke-icon.svg"
                    assert row["document"]["icons"]==[{"href":icon,"type":"image/svg+xml"}], "Actual final document icon differs"
                    assert row["document"]["preference"]==(motion=="reduce")
                    icon_deadline=time.monotonic()+5
                    while time.monotonic()<icon_deadline:
                        row["automaticIcon"]=select_icon_requests(events,icon,consumer)
                        relevant=[v for v in row["automaticIcon"] if v["relevantConsumer"]]
                        if relevant and all(v["terminals"] for v in relevant):break
                        page.wait_for_timeout(50)
                    relevant=require_icon_consumption(row["automaticIcon"],consumer)
                    require_no_icon_errors(events,icon)
                    with urlopen(icon,timeout=5) as response:
                        data=response.read()
                        row["separateHttpReadback"]={"kind":"independent-HTTP-readback-not-browser-body","url":response.url,"status":response.status,"contentType":response.headers.get_content_type(),"bytes":len(data),"sha256":sha(data)}
                    assert row["separateHttpReadback"]["url"]==icon and row["separateHttpReadback"]["status"]==200 and row["separateHttpReadback"]["contentType"]=="image/svg+xml"
                    assert sha(data)==expected["files"]["tests/r0017-smoke-icon.svg"]["sha256"], "Served icon bytes differ from reviewed source"
                    (out/(name+"-http-readback-icon.svg")).write_bytes(data)
                    row["browserIconBodies"]=[]
                    for chosen in relevant:
                        rid=chosen["request"]["params"]["requestId"]
                        receipt={"requestId":rid};row["browserIconBodies"].append(receipt)
                        try:
                            raw=cdp.send("Network.getResponseBody",{"requestId":rid})
                            data=base64.b64decode(raw["body"]) if raw.get("base64Encoded") else raw["body"].encode()
                            receipt.update({"bytes":len(data),"sha256":sha(data)})
                            assert sha(data)==expected["files"]["tests/r0017-smoke-icon.svg"]["sha256"], "Browser icon bytes differ from reviewed source"
                            (out/(name+"-browser-icon-"+str(len(row["browserIconBodies"]))+".svg")).write_bytes(data)
                        except Exception as e:
                            receipt["unavailable"]=str(e)
                            if isinstance(e,AssertionError):raise
                    phase["value"]="separate-decoder-control"
                    row["decode"]=page.evaluate("""async url => {
                      const image=new Image();image.src=url;
                      await Promise.race([image.decode(),new Promise((_,reject)=>setTimeout(()=>reject(Error('Icon decode deadline')),5000))]);
                      const canvas=document.createElement('canvas');canvas.width=32;canvas.height=32;
                      const ctx=canvas.getContext('2d');ctx.drawImage(image,0,0,32,32);
                      const rgba=ctx.getImageData(0,0,32,32).data;
                      return {width:image.naturalWidth,height:image.naturalHeight,opaquePixels:Array.from(rgba).filter((v,i)=>i%4===3&&v>0).length};
                    }""",icon)
                    assert row["decode"]["width"]==32 and row["decode"]["height"]==32 and row["decode"]["opaquePixels"]>0
                    phase["value"]="final-capture"
                    page.screenshot(path=str(out/(name+".png")))
                    row["automaticIcon"]=select_icon_requests(events,icon,consumer)
                    require_icon_consumption(row["automaticIcon"],consumer)
                    require_no_icon_errors(events,icon)
                    row["status"]="ICON_CONSUMER_OBSERVED"
                except Exception as e:
                    row["status"]="ICON_OBSERVATION_FAILED";row["error"]=str(e);row["traceback"]=traceback.format_exc()
                finally:
                    phase["value"]="owned-context-close"
                    try:
                        context.close();row["contextClosed"]=True
                    except Exception as e:
                        row["contextClosed"]=False;row["contextCloseError"]=str(e);row["status"]="ICON_OBSERVATION_FAILED"
                    if row["status"]=="ICON_CONSUMER_OBSERVED":
                        try:
                            row["finalIconRequests"]=select_icon_requests(events,icon,consumer)
                            require_icon_consumption(row["finalIconRequests"],consumer)
                            require_no_icon_errors(events,icon)
                            row["iconFinalizationChecksPassed"]=True
                        except Exception as e:
                            row["statusBeforeFinalizationGate"]=row["status"];row["status"]="ICON_OBSERVATION_FAILED"
                            row["iconFinalizationChecksPassed"]=False;row["iconFinalizationError"]=str(e)
                    row["observedHttpErrors"]=[e for e in events if e["method"]=="Network.responseReceived" and e["params"]["response"]["status"]>=400]
                    row["observedNetworkFailures"]=[e for e in events if e["method"]=="Network.loadingFailed"]
                    row["observedSecurityLogs"]=[e for e in events if e["method"]=="Log.entryAdded" and e["params"].get("entry",{}).get("source")=="security"]
                    row["eventCount"]=len(events);save()
                print(name,row["status"],row.get("error",""),flush=True)
                if row["status"]!="ICON_CONSUMER_OBSERVED":
                    result["stopReason"]="First actual capability/observation failure; no repeated navigation"
                    break
            result["status"]="ICON_COMPONENTS_OBSERVED" if len(result["cases"])==2 and all(x["status"]=="ICON_CONSUMER_OBSERVED" for x in result["cases"]) else "INCOMPLETE"
            result["wholeNativeCleanliness"]="NOT_QUALIFIED_BY_THIS_SCOPED_PROBE"
            browser.close();result["cleanup"]["browserDisconnected"]=not browser.is_connected();browser=None
    except Exception as e:
        result["status"]="CAPABILITY_OR_OBSERVATION_FAILED";result["error"]=str(e);result["traceback"]=traceback.format_exc()
    finally:
        if browser is not None:
            try:browser.close();result["cleanup"]["browserDisconnected"]=not browser.is_connected()
            except Exception as e:result["cleanup"]["browserCloseError"]=str(e)
        try:
            server.shutdown();server.server_close();thread.join(timeout=5)
            result["cleanup"]["serverThreadStopped"]=not thread.is_alive()
        except Exception as e:
            result["cleanup"]["serverThreadStopped"]=False;result["cleanup"]["serverCloseError"]=str(e)
        result["cleanup"]["allContextsClosed"]=bool(result["cases"]) and all(x.get("contextClosed") is True for x in result["cases"])
        result["cleanup"]["verified"]=result["cleanup"].get("browserDisconnected") is True and result["cleanup"]["serverThreadStopped"] is True and result["cleanup"]["allContextsClosed"]
        if not result["cleanup"]["verified"]:
            result["statusBeforeCleanupGate"]=result["status"];result["status"]="CLEANUP_UNVERIFIED"
        result["finishedUtc"]=time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime());save()
    print(json.dumps({"status":result["status"],"cases":[{"name":x["name"],"status":x["status"]} for x in result["cases"]],"cleanup":result["cleanup"]}),flush=True)
    return 0 if result["status"]=="ICON_COMPONENTS_OBSERVED" else 1

if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--root",type=Path,required=True);parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args();raise SystemExit(main(args.root.resolve(),args.out.resolve()))

