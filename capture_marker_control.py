"""Acquisition-only busy-main-thread discriminator; no widget is loaded."""
from pathlib import Path
import asyncio, hashlib, json, os
from urllib.parse import quote
from playwright.async_api import async_playwright
import playwright._impl._transport as transport

O=Path(__file__).resolve().parent
NODE=Path(r'<runtime-install>\OpenJS.NodeJS.LTS_Microsoft.Winget.Source_8wekyb3d8bbwe\node-v24.15.0-win-x64\node.exe')
transport.compute_driver_executable=lambda:(str(NODE),str(O/'capture-driver/cli.js'))
os.environ['SALAH_CAPTURE_NATIVE_FRAMES']='1'
HTML='''<!doctype html><style>
body{margin:0}#panel{width:325px;height:530px;background:#134fca}
#marker{position:fixed;left:0;top:566px;width:24px;height:20px;background:#ff00cc;will-change:transform;ANIMATION}
@keyframes travel{from{transform:translateX(0)}to{transform:translateX(320px)}}
</style><div id="panel"></div><div id="marker"></div><script>
window.events=[];const record=stage=>events.push({stage,at:performance.now(),utc:performance.timeOrigin+performance.now()});
JS_MARKER
requestAnimationFrame(()=>requestAnimationFrame(()=>setTimeout(()=>{
 record('busy-start');const until=performance.now()+480;while(performance.now()<until){};
 record('busy-end');document.querySelector('#panel').style.background='#ba1c2d';
 setTimeout(()=>{record('done');window.done=true;},240);
},240)));
</script>'''

async def main():
    out=O/'capture-control-r1';out.mkdir()
    lock=O/'native-resource.lock'
    with lock.open('x') as f:f.write(out.name)
    report={'scope':'Synthetic capture mechanism control only. Original widget gaps remain unchanged.','cases':[]}
    try:
        async with async_playwright() as p:
            browser=await p.chromium.launch(executable_path=r'<browser-install>\chromium-1223\chrome-win64\chrome.exe',headless=True,chromium_sandbox=True)
            try:
                report['browserVersion']=browser.version
                for arm in ['main-thread-marker','compositor-marker']:
                    folder=out/arm;folder.mkdir()
                    ctx=await browser.new_context(viewport={'width':390,'height':600},record_video_dir=str(folder/'video'),record_video_size={'width':390,'height':600})
                    try:
                        html=HTML.replace('ANIMATION','animation:travel 1s linear infinite;' if arm=='compositor-marker' else '').replace('JS_MARKER','' if arm=='compositor-marker' else "function tick(t){document.querySelector('#marker').style.transform='translateX('+((t%1000)*.32)+'px)';requestAnimationFrame(tick)}requestAnimationFrame(tick);")
                        (folder/'fixture.html').write_text(html)
                        page=await ctx.new_page();await page.goto('data:text/html,'+quote(html),wait_until='commit')
                        await page.wait_for_function('window.done===true')
                        events=await page.evaluate('window.events')
                        await page.screenshot(path=str(folder/'final.png'))
                    finally:await ctx.close()
                    files=list((folder/'video').glob('*.frames.jsonl'));assert len(files)==1
                    frames=[json.loads(line) for line in files[0].read_text().splitlines()]
                    lo,hi=events[0]['utc'],events[1]['utc']
                    relevant=[f for f in frames if lo-80<=f['sourceTimeSeconds']*1000<=hi+80]
                    report['cases'].append({'arm':arm,'events':events,'fixtureSha256':hashlib.sha256(html.encode()).hexdigest(),
                        'framesPath':str(files[0].relative_to(out)),'framesDuringBusy':sum(lo<=f['sourceTimeSeconds']*1000<=hi for f in frames),
                        'maximumSourceGapMs':max((1000*(b['sourceTimeSeconds']-a['sourceTimeSeconds']) for a,b in zip(relevant,relevant[1:])),default=None),
                        'sourceTimesAroundBusy':[{'file':f['file'],'fromBusyMs':1000*f['sourceTimeSeconds']-lo} for f in relevant],
                        'status':'OBSERVATIONS_REQUIRE_ORIGINAL_PIXEL_REVIEW'})
            finally:await browser.close();report['ownedBrowserClosed']=True
    finally:
        (out/'RESULT.json').write_text(json.dumps(report,indent=2)+'\n')
        assert lock.read_text()==out.name;lock.unlink()
    print(json.dumps(report,indent=2))
asyncio.run(main())
