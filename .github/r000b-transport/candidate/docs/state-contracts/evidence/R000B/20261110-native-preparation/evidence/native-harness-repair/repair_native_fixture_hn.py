from pathlib import Path
import hashlib

target = Path('/workspace/scratch/15b8fb6ac4c2/r000b-work/tests/rlgwo/r000b-no-timetable-fixture.html')
assert hashlib.sha256(target.read_bytes()).hexdigest() == '77f5221280705cf9f4a9de760007a6b49ac25c12b8f53412c23661af32b3be09'
text = target.read_text()

def replace(old, new):
    global text
    assert text.count(old) == 1, old[:100]
    text = text.replace(old, new)

replace('// Test-only document and transport wrapper. Every product script body is kept',
        '// R000B_HN1_HN4_READ_ONLY_OBSERVER_V2\n// Test-only document and transport wrapper. Every product script body is kept')
replace('''    const motion=()=>({key:_cloudMotion.key,population:_cloudMotion.population,phase:[..._cloudMotion.phase],life:[..._cloudMotion.life],wander:_cloudMotion.wander,lastRt:_cloudMotion.lastRt,paused:_cloudMotion.paused,reduced:_cloudMotion.reduced,fieldSeed:_cloudFieldSeed});''',
'''    const motion=()=>({key:_cloudMotion.key,population:_cloudMotion.population,phase:[..._cloudMotion.phase],life:[..._cloudMotion.life],wander:_cloudMotion.wander,
      lastRt:_cloudMotion.lastRt,elapsedRtMs:_cloudMotion.lastRt==null?null:_cloudMotion.lastRt-report.started,
      paused:_cloudMotion.paused,reduced:_cloudMotion.reduced,fieldSeed:_cloudFieldSeed,wind:{wx:cloudState.wx,wspd:cloudState.wspd}});
    const actuallyDisplayed=el=>{
      if(!el)return false;const style=getComputedStyle(el),bounds=el.getBoundingClientRect();
      return style.display!=="none"&&style.visibility==="visible"&&Number(style.opacity)>0&&bounds.width>0&&bounds.height>0;
    };''')
replace('''        alphaCentroid:sum?{x:mx/sum,y:my/sum}:null,columnAlpha:columns,rgbNonzero,minRGB,maxRGB,display:style.display,visibility:style.visibility,opacity:Number(style.opacity)};''',
'''        alphaCentroid:sum?{x:mx/sum,y:my/sum}:null,columnAlpha:columns,rgbNonzero,minRGB,maxRGB,
        bounds:rect(cv,document.querySelector(".c")),filter:style.filter,maskImage:style.maskImage||style.webkitMaskImage||"none",
        display:style.display,visibility:style.visibility,opacity:Number(style.opacity)};''')
replace('''        const bounds=rect(el,c),displayed=style.display!=="none"&&style.visibility==="visible"&&Number(style.opacity)>.03&&
          bounds.right>0&&bounds.left<325&&bounds.bottom>0&&bounds.top<530&&c.dataset.precip==="on";
        return {index,kind:el.classList.contains("drop")?"rain":"snow",leftPercent,column:col,density:col==null?null:density[col],
          normalizedDensity:col==null||densityMax===0?null:density[col]/densityMax,inlineDisplay:el.style.display,display:style.display,
          visibility:style.visibility,opacity:Number(style.opacity),displayed,originTop:style.top,rect:bounds,animation:style.animationName,animationPlayState:style.animationPlayState};''',
'''        const bounds=rect(el,c),displayed=style.display!=="none"&&style.visibility==="visible"&&Number(style.opacity)>.03&&
          bounds.right>0&&bounds.left<325&&bounds.bottom>0&&bounds.top<530&&c.dataset.precip==="on";
        // The source column belongs to the untransformed CSS base position.
        // Keep the currently visible segment separately; its opacity/translation
        // must never be mistaken for the invisible start of the fall animation.
        const parent=el.offsetParent,pixels=value=>/^-?[0-9.]+px$/.test(value)?Number.parseFloat(value):null;
        const position={left:pixels(style.left),top:pixels(style.top),width:pixels(style.width),height:pixels(style.height)};
        const parentGeometry=parent?{bounds:rect(parent,c),clientLeft:parent.clientLeft,clientTop:parent.clientTop,
          clientWidth:parent.clientWidth,clientHeight:parent.clientHeight,offsetWidth:parent.offsetWidth,offsetHeight:parent.offsetHeight,classes:String(parent.className)}:null;
        const matrix=new DOMMatrixReadOnly(style.transform==="none"?undefined:style.transform);
        const transform={is2D:matrix.is2D,a:matrix.a,b:matrix.b,c:matrix.c,d:matrix.d,e:matrix.e,f:matrix.f};
        const baseOrigin=parentGeometry&&Object.values(position).every(Number.isFinite)?{
          left:parentGeometry.bounds.left+parentGeometry.clientLeft+position.left,
          top:parentGeometry.bounds.top+parentGeometry.clientTop+position.top,width:position.width,height:position.height}:null;
        return {index,kind:el.classList.contains("drop")?"rain":"snow",leftPercent,column:col,density:col==null?null:density[col],
          normalizedDensity:col==null||densityMax===0?null:density[col]/densityMax,inlineDisplay:el.style.display,display:style.display,
          visibility:style.visibility,opacity:Number(style.opacity),displayed,originTop:style.top,rect:bounds,animation:style.animationName,animationPlayState:style.animationPlayState,
          originGeometry:{position,parent:parentGeometry,transform,baseOrigin,transformText:style.transform,
            contract:"CSS base top19%; assigned untransformed cloud column; visible segment is base plus current translation"}};''')
replace('''      const solarMask=c.style.getPropertyValue("--native-sun-cloud-mask");''',
'''      const visibleForegrounds=[
        {owner:"refined",canvas:refinedCanvas,status:refined?.status??null,composition:copy(refined?.last?.composition),frameUtcMs:refined?.displayed?.utcMs??refined?.presentationUtcMs??null},
        {owner:"preview",canvas:previewCanvas,status:preview?.status??null,composition:copy(preview?.composition),frameUtcMs:preview?.utcMs??null}
      ].filter(layer=>layer.canvas&&layer.canvas.display!=="none"&&layer.canvas.visibility==="visible"&&layer.canvas.opacity>0&&layer.canvas.bounds.width>0&&layer.canvas.bounds.height>0);
      const photo=document.querySelector(".mphoto"),moonGroup=document.querySelector(".moon");
      const moonDOM={photoHrefPresent:!!photo?.getAttribute("href"),photoBounds:photo?rect(photo,c):null,
        groupBounds:moonGroup?rect(moonGroup,c):null,groupOpacity:moonGroup?Number(getComputedStyle(moonGroup).opacity):null};
      const solarMask=c.style.getPropertyValue("--native-sun-cloud-mask");''')
replace('''          moonGeometry:copy(moonSky),moonRuntime:copy(window.SalahMoonRuntime?.state),solarMask},''',
'''          moonGeometry:copy(moonSky),moonDOM,visibleForegrounds,solarMask,
          diagnosticReadLimit:"Moon runtime state/surface/presentation getters are not read; handled Moon worker diagnostic errors are uninspected"},''')
replace('''        const begin=performance.now();let frames=0;
        const readFrame=()=>{
          if(report.state!=="ready")return;
          try{
            frames++;const first=!report.resumeFirstRaf,c=document.querySelector(".c"),visible=c.classList.contains("real-sky-composed")||c.classList.contains("real-sky-preview-ready");
            const value=first||visible?snapshot():null;
            if(first)report.resumeFirstRaf=value;
            if(value?.celestial?.owner&&value.celestial.status==="ready"&&value.celestial.activeCanvas?.visibility==="visible"){
              report.resumeFirstVisible=value;report.resumeObservation={frames,elapsedMs:performance.now()-begin,kind:"read-only post-event rAF observer"};return;
            }
            if(frames>=120||performance.now()-begin>5000)throw Error("No eligible visible foreground within bounded resume observation");
            requestAnimationFrame(readFrame);
          }catch(error){report.error=String(error.message||error);report.state="error";}
        };
        requestAnimationFrame(readFrame);''',
'''        const begin=performance.now();let frames=0;report.resumeOpportunities=[];
        const readFrame=()=>{
          if(report.state!=="ready")return;
          try{
            frames++;const first=frames===1;
            // CSS visibility, dimensions and opacity determine observation.
            // A pending diagnostic status never suppresses displayed pixels.
            const visible=actuallyDisplayed(document.querySelector(".real-sky-canvas"))||actuallyDisplayed(document.querySelector(".real-sky-preview"));
            const value=first||visible?snapshot():null;
            report.resumeOpportunities.push({frame:frames,elapsedMs:performance.now()-report.started,visible,state:value});
            if(first)report.resumeFirstRaf=value;
            if(visible&&!report.resumeFirstVisible)report.resumeFirstVisible=value;
            // Ready recovery is a separate endpoint after every earlier
            // actually visible opportunity has been retained for checking.
            const ready=value?.celestial?.visibleForegrounds.some(layer=>layer.owner===value.celestial.owner&&layer.status==="ready");
            if(ready){
              report.resumeReady=value;report.resumeObservation={complete:true,frames,elapsedMs:performance.now()-begin,kind:"all visible post-event rAF opportunities retained independently of diagnostic readiness"};return;
            }
            if(frames>=120||performance.now()-begin>5000)throw Error("No ready foreground within bounded resume observation; visible pending frames retained");
            requestAnimationFrame(readFrame);
          }catch(error){report.error=String(error.message||error);report.state="error";}
        };
        requestAnimationFrame(readFrame);''')
replace('''        document.dispatchEvent(new Event("visibilitychange"));
        if(!hidden)window.__withdrawalRead.observeResume(owner);''',
'''        document.dispatchEvent(new Event("visibilitychange"));
        // Passive values after the product's own pause/resume listeners establish
        // exact elapsed boundaries for the no-backlog continuity oracle.
        event.nativeMotionAfter={key:_cloudMotion.key,population:_cloudMotion.population,phase:[..._cloudMotion.phase],life:[..._cloudMotion.life],wander:_cloudMotion.wander,
          lastRt:_cloudMotion.lastRt,elapsedRtMs:_cloudMotion.lastRt==null?null:_cloudMotion.lastRt-started,paused:_cloudMotion.paused,reduced:_cloudMotion.reduced,
          fieldSeed:_cloudFieldSeed,wind:{wx:cloudState.wx,wspd:cloudState.wspd}};
        event.elapsedAfterDispatchMs=elapsed();
        if(!hidden)window.__withdrawalRead.observeResume(owner);''')
target.write_text(text)
print(hashlib.sha256(target.read_bytes()).hexdigest(), target)
