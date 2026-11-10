import asyncio,json,time
STATE="const w=window,c=document.querySelector('.c'),r=c.getBoundingClientRect(),style=getComputedStyle(c);return JSON.parse(JSON.stringify({url:location.href,ready:document.readyState,card:{width:r.width,height:r.height},weatherHeader:{icon:document.querySelector('#wi')?.textContent,temperature:document.querySelector('#wt')?.textContent},mode:c.dataset.appearance,classes:c.className,background:style.background,opacity:style.opacity,backdropFilter:style.backdropFilter,storage:localStorage.getItem('salah_widget:config:v1'),mainWorldAvailable:!!w?.SalahMoonRuntime,native:w?.SalahNativeSkyHost?.capture(false),moon:w?.SalahMoonRuntime?.state,sky:w?.SalahRealSky?.state,qa:w?.qaState?.(),rows:[...document.querySelectorAll('.times .p')].map(e=>({text:e.innerText,opacity:getComputedStyle(e).opacity,background:getComputedStyle(e).background,rect:e.getBoundingClientRect().toJSON()})),text:c.innerText}));"
async def appearance_controls(page,frame,out,origin):
    result={'scope':'Actual installed extension parent, admitted weather, native settings in both directions and parent reload; endpoints are not continuous evidence','endpoints':{}}
    def save():
        (out/'parent-controls-partial.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    async def endpoint(label,mode):
        state=await frame.evaluate('()=>{'+STATE+'}');result['endpoints'][label]=state
        element=await frame.frame_element()
        wrapper=await element.evaluate('(f)=>({src:f.src,width:f.getBoundingClientRect().width,height:f.getBoundingClientRect().height,style:f.getAttribute("style")})')
        state['parentWrapper']=wrapper
        save()
        assert wrapper['src']==frame.url and wrapper['width']==325 and wrapper['height']==530,'Actual preset iframe geometry/source changed'
        assert state['weatherHeader']['temperature'] and state['weatherHeader']['icon'] not in ['', '—'],'Admitted weather is required'
        assert state['native']['weather']['cloud']==35 and state['mode']==mode and len(state['rows'])==6 and state['card']=={'width':325,'height':530}
        assert state['moon']['current'] and state['moon']['visibleSource']=='refined-terrain' and not state['moon']['pending'] and state['sky']['status']=='ready'
        q=state['moon']['last']['quality'];assert q['status']=='empirical-adaptive' and q['projectedGate']==.5 and q['projectedMaximumCode']<=.5 and q['unsettled']==0
        await page.screenshot(path=str(out/(label+'.png')))
        await frame.locator('.c').screenshot(path=str(out/(label+'-card.png')))
        return state
    first=await endpoint('parent-glass-default','glass')
    for mode in ['contrast','glass']:
        await frame.locator('.buckle').click();await frame.locator('#set-appearance').select_option(mode);await frame.locator('#setClose').click();await asyncio.sleep(.3)
        state=await endpoint('parent-'+mode+'-return',mode)
        assert all(state['native'][k]==first['native'][k] for k in ['lat','lon','tz','generation','weather']),'Appearance changed target/weather/generation'
    await page.reload(wait_until='domcontentloaded');deadline=time.monotonic()+360
    while time.monotonic()<deadline:
        matches=[f for f in page.frames if f.url.startswith(origin+'/salah_widget/')]
        if matches:
            frame=matches[0]
            if await frame.locator('.c').count():
                state=await frame.evaluate('()=>{'+STATE+'}')
                moon,sky=state.get('moon') or {},state.get('sky') or {}
                if moon.get('status')=='unavailable' or sky.get('status')=='unavailable':raise RuntimeError('Unexpected parent product failure')
                if moon.get('current') and moon.get('visibleSource')=='refined-terrain' and not moon.get('pending') and sky.get('status')=='ready' and not (sky.get('lifecycle') or {}).get('pending'):break
        await asyncio.sleep(.5)
    else:raise TimeoutError('Parent reload final not admitted within360s')
    await endpoint('parent-glass-reload','glass')
    return result
