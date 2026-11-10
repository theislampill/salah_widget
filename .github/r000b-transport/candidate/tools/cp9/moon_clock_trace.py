"""Actual-entry clock/phase/cancellation trace; no product-source instrumentation.

--hold-phase is an explicit diagnostic control, not normal-clock acceptance.
The real worker's timer waits are measured without changing their scheduling.
"""
import argparse,functools,http.server,json,sys,threading,time,traceback,hashlib
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright
from browser_runtime import launch_browser,browser_identity
from runtime_identity import runtime_identity

TRACE=r'''(()=>{
 window.__lunarTrace={events:[],samples:[],workers:[]};
 const capture=()=>{const s=window.SalahMoonHost?.capture();if(!s)return null;const a=Math.acos(2*s.fraction-1),precision=window.SalahMoonRuntime?.state.phasePrecision,quantum=precision?.quantumRadians??.0004,bucket=Math.round(a/quantum);return {...s,acceptedNativeUTC:window.realSkyState?.().last?.utcMs,angle:a,bucket,quantum,precision,canonicalFraction:s.fraction===0||s.fraction===1?s.fraction:(1+Math.cos(Math.min(Math.PI,bucket*quantum)))/2};};
 const blob=URL.createObjectURL.bind(URL);
 const prefix=`const __realTimeout=setTimeout;let __yieldTrace={count:0,totalMs:0,maxMs:0,over20:0,start:performance.now()};self.addEventListener('message',e=>{if(e.data.kind==='render')__yieldTrace={count:0,totalMs:0,maxMs:0,over20:0,start:performance.now()};});globalThis.setTimeout=(f,delay,...args)=>{const start=performance.now();return __realTimeout(()=>{if(delay===0){const dt=performance.now()-start;__yieldTrace.count++;__yieldTrace.totalMs+=dt;__yieldTrace.maxMs=Math.max(__yieldTrace.maxMs,dt);if(dt>20)__yieldTrace.over20++;}f(...args);},delay);};const __realPost=self.postMessage.bind(self);self.postMessage=(m,t)=>{if(['progress','preview','result'].includes(m.kind))m={...m,__yieldTrace:{...__yieldTrace,elapsedMs:performance.now()-__yieldTrace.start}};return t?__realPost(m,t):__realPost(m);};\n`;
 URL.createObjectURL=b=>blob(b.type==='text/javascript'?new Blob([prefix,b],{type:b.type}):b);
 const W=Worker;window.Worker=class extends W{constructor(u,o){super(u,o);__lunarTrace.workers.push(this);const send=this.postMessage.bind(this);let job=null,lastProgress=null;
 this.postMessage=(m,t)=>{if(m.kind==='boot')this.isMoon='offline' in m;if(this.isMoon&&['render','cancel'].includes(m.kind)){
 const event={kind:m.kind,at:performance.now(),native:capture(),state:window.SalahMoonRuntime?.state,previousJob:job,workerProgress:lastProgress};
 if(m.kind==='render'){job={id:m.id,identity:m.identity,scene:m.scene,at:performance.now()};event.submission=job;}
 else {event.elapsedWorkerMs=job?performance.now()-job.at:null;setTimeout(()=>event.reason=SalahMoonRuntime.state.reason,0);}
 __lunarTrace.events.push(event);
 }return t?send(m,t):send(m);};
 this.addEventListener('message',e=>{if(!this.isMoon)return;const m=e.data;
 if(m.kind==='progress')lastProgress={stage:m.stage,row:m.row,samples:m.sourceSamples,selected:m.selected,yields:m.__yieldTrace};
 if(['ready','preview','result','error','boot-error'].includes(m.kind)){const event={kind:m.kind,at:performance.now(),id:m.id,identity:m.identity,scene:m.scene,diagnostics:m.diagnostics,yields:m.__yieldTrace,native:capture()};__lunarTrace.events.push(event);setTimeout(()=>event.admission=window.SalahMoonRuntime?.state,0);}
 });}};
 setInterval(()=>{const native=capture();if(native)__lunarTrace.samples.push({at:performance.now(),native,status:window.SalahMoonRuntime?.state.status,epoch:window.SalahMoonRuntime?.state.epoch});},1000);
})();'''


def run(root,out,seconds,hold_phase,font_dir,hold_wax):
    sys.path.insert(0,str(root/'tests'));from v1_browser import fixture,FONT_CSS,ROOT_KEY,SETTINGS
    out.mkdir(parents=True,exist_ok=True)
    src='/salah_widget/#local=1'+('' if hold_phase is None else '&simMoon='+str(hold_phase)+'&simWax='+str(hold_wax))
    html='<iframe title="Prayer Times" referrerpolicy="no-referrer" allow="geolocation" src="'+src+'" style="width:330px;height:534px;border:0;border-radius:28px;overflow:hidden" scrolling="no"></iframe>'
    class Server(http.server.SimpleHTTPRequestHandler):
        def log_message(self,*a):pass
        def do_GET(self):
            if self.path=='/trace.html':
                data=html.encode();self.send_response(200);self.send_header('Content-Type','text/html');self.end_headers();self.wfile.write(data)
            else:super().do_GET()
        def translate_path(self,path):return str(root/path.split('?',1)[0].removeprefix('/salah_widget/'))
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Server);threading.Thread(target=server.serve_forever,daemon=True).start();origin=f'http://127.0.0.1:{server.server_port}'
    report={'status':'RUNNING','runtime':runtime_identity(root),'holdPhaseDiagnostic':hold_phase,'holdWaxingDiagnostic':hold_wax if hold_phase is not None else None,'errors':[],'scope':'1x native Date anchor; exact iframe; controlled provider/font fixtures; actual worker with additive timer observation only'}
    try:
        with sync_playwright() as pw:
            b=launch_browser(pw);report['browser']=browser_identity(b);c=b.new_context(viewport={'width':390,'height':600},device_scale_factor=1,timezone_id='Asia/Riyadh',locale='en-US',reduced_motion='reduce')
            def route(r):
                u=r.request.url
                if u.startswith(origin):r.continue_();return
                file=font_dir/hashlib.sha256(u.encode()).hexdigest()
                if file.exists():r.fulfill(body=file.read_bytes(),content_type='text/css' if u==FONT_CSS else 'font/woff2',headers={'Access-Control-Allow-Origin':'*'});return
                value=fixture(u,True)
                if urlsplit(u).hostname=='api.aladhan.com':
                    date=urlsplit(u).path.rstrip('/').split('/')[-1];d,m,y=date.split('-');value['data']['date']['gregorian'].update(date=date,day=d,month={'number':int(m)},year=y)
                r.fulfill(json=value,headers={'Access-Control-Allow-Origin':'*'})
            c.route('**/*',route)
            c.add_init_script(TRACE)
            c.add_init_script("(()=>{const D=Date,start=performance.now(),base=D.parse('2026-10-07T20:30:00Z');window.Date=class extends D{constructor(...a){super(...(a.length?a:[base+performance.now()-start]));}static now(){return base+performance.now()-start;}};})();")
            c.add_init_script('if(location.protocol==="http:")localStorage.setItem('+json.dumps(ROOT_KEY)+','+json.dumps(json.dumps(SETTINGS))+');')
            q=c.new_page();q.on('pageerror',lambda e:report['errors'].append(str(e)));q.goto(origin+'/trace.html',wait_until='load');f=q.frames[1];began=time.monotonic()
            while time.monotonic()-began<seconds:
                q.wait_for_timeout(5000)
                state=f.evaluate('({trace:__lunarTrace,moon:window.SalahMoonRuntime?.state,host:window.SalahMoonHost?.capture(),rows:document.querySelectorAll(".p").length,prayer:typeof model==="function"?model():null})')
                report.update(observation=state,elapsedSeconds=time.monotonic()-began)
                (out/'trace.json').write_text(json.dumps(report,indent=2)+'\n')
                m=state.get('moon') or {};print(round(report['elapsedSeconds']),m.get('status'),m.get('quality'),'cancelled',m.get('cancelled'),flush=True)
                if hold_phase is not None and m.get('status')=='ready' and not m.get('pending'):break
            q.locator('iframe').screenshot(path=out/'terminal-state.png');report['status']='TRACE_COMPLETE';c.close();b.close()
    except Exception:report['status']='TRACE_ERROR';report['exception']=traceback.format_exc()
    finally:server.shutdown();(out/'trace.json').write_text(json.dumps(report,indent=2)+'\n')
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True,type=Path);p.add_argument('--output',required=True,type=Path);p.add_argument('--seconds',type=int,default=300);p.add_argument('--hold-phase',type=float);p.add_argument('--hold-wax',type=int,choices=[0,1],default=0);p.add_argument('--fonts',required=True,type=Path);a=p.parse_args()
    r=run(a.root.resolve(),a.output,a.seconds,a.hold_phase,a.fonts,a.hold_wax);raise SystemExit(0 if r['status']=='TRACE_COMPLETE' else 1)
