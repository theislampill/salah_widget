"""H2/H8 daytime ownership and star/precipitation isolation.

Settled, matched-input diagnostics complement (never replace) continuous playback.
Reuses the actual entry, provider admission, browser and currentness harness.
"""
import argparse, base64, json, shutil, sys
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw, ImageStat
from playwright.sync_api import sync_playwright
import hotfix_stress_check as h
from browser_runtime import launch_browser, browser_identity
from runtime_identity import runtime_identity

PATCH=(275,190,310,218) # Right open sky, outside solar body, cloud band and text.
def daylight_pixels(path,ordinary=False):
 im=Image.open(path).convert('RGB');rgb=ImageStat.Stat(im.crop(PATCH)).median
 y=sum(a*b for a,b in zip(rgb,[.2126,.7152,.0722]))
 # Reuse the existing B>=100 daylight family; add a luminance floor so a
 # blue-only/night placeholder cannot pass. Chroma applies only to clear sky.
 return {'medianRGB':rgb,'luminance':y,'blueMinusRed':rgb[2]-rgb[0],
         'pass':y>=80 and rgb[2]>=100 and (not ordinary or rgb[2]-rgb[0]>=10)}

ISOLATE=r'''async()=>{
 const {renderNativeBackgroundPreview}=await import('/salah_widget/real-sky/native-preview.mjs'),
 {NativeStarPreview,joinNativeStarPreview}=await import('/salah_widget/real-sky/native-star-preview.mjs'),
 {encodeNativeFrame}=await import('/salah_widget/real-sky/native-encoding.mjs');
 const h=SalahNativeSkyHost.capture(),r=realSkyFrame().raster;
 const image=(a,w=325,ht=530)=>{const c=document.createElement('canvas');c.width=w;c.height=ht;c.getContext('2d').putImageData(new ImageData(a,w,ht),0,0);return c;};
 const catalogueText=await(await fetch('/salah_widget/vendor/real-sky/data/bright-stars.json')).text(),
 manifestText=await(await fetch('/salah_widget/vendor/real-sky/data/registered-starlight/runtime-manifest.json')).text(),stars=new NativeStarPreview({catalogueText,manifestText});
 const cases=[];
 for(const rate of [1,600]){
  const p=renderNativeBackgroundPreview({...h,timeScale:rate}),small=image(encodeNativeFrame(p.raster.linear,p.raster.effectiveExposure),p.raster.width,p.raster.height),full=document.createElement('canvas');full.width=325;full.height=530;
  const cx=full.getContext('2d');cx.drawImage(small,0,0,325,530);const base=cx.getImageData(0,0,325,530).data,s=stars.render(p.job,p.raster.physicalState,{background:base,exposure:p.raster.effectiveExposure}),joined=joinNativeStarPreview(p,base,s);
  let visible=0,maximum=0;for(let i=0;i<base.length;i+=4){let d=0;for(let k=0;k<3;k++)d=Math.max(d,joined.rgba[i+k]-base[i+k]);maximum=Math.max(maximum,d);if(d>=2)visible++;}
  cases.push({rate,utc:p.utcMs,solar:p.raster.physicalState.sun,exposure:p.raster.effectiveExposure,display:p.raster.displayPresentation,stars:s.diagnostics,visibleStarPixels:visible,maximumStarCodeDelta:maximum,atmosphere:full.toDataURL(),joined:image(joined.rgba).toDataURL()});
 }
 return {host:h,refinedSolar:r.physicalState.sun,cases,legacyStars:{opacity:getComputedStyle(document.querySelector('.stars')).opacity,display:getComputedStyle(document.querySelector('.stars')).display}};
}'''

def run(a):
 a.out.mkdir(parents=True,exist_ok=True);sys.path.insert(0,str(a.root/'tests'));from v1_browser import fonts
 shutil.copytree(a.fonts,a.out/'fonts',dirs_exist_ok=True);ff=fonts(a.out);rows=[]
 report={'runtime':runtime_identity(a.root),'scope':'Sanitised Orlando fixture; settled exact UTC with current catalogue/sky. Fast-preview detached renders are layer diagnostics, not600x playback. Complete scene retains snow/clouds/UI.',
         'thresholds':{'starPixelDelta':2,'daylightLuminance':80,'daylightBlue':100,'ordinaryBlueMinusRed':10,'patchCSS':PATCH},'cases':rows}
 if a.negative:
  report['retainedNegative']=daylight_pixels(a.negative);assert not report['retainedNegative']['pass'],'Retained missing-daylight frame must fail'
 with sync_playwright() as pw:
  b=launch_browser(pw);report['browser']=browser_identity(b)
  cases=[('snow','2026-10-08T12:14:01.640Z'),('clear','2026-10-08T12:14:01.640Z'),('partial','2026-10-07T15:09:00Z'),('rain','2026-10-07T15:09:00Z')]
  if a.incident:cases=[('incident-track','2026-10-07T09:00:00Z')]
  for family,stamp in cases:
   incident=family=='incident-track';out=a.out/family;e=h.Entry(b,a.root,out,ff,rate=0,start=stamp,family='clear' if incident else family,steady=not incident)
   try:
    utc=1791461641640 if incident else e.anchor
    e.frame.evaluate('utcMs=>SalahClock.set({utcMs,rate:0})',utc);e.ready();e.page.wait_for_timeout(1500)
    if incident:
     retained=json.loads(a.incident.read_text(encoding='utf-8'));expected=retained['responses'][0]
     assert e.responses[0]['sha256']==expected['sha256'],'Exact retained response must be consumed, not a similar snow fixture'
     consumed=e.frame.evaluate(h.SNAP)['weather']['selected'];assert consumed['code']==73 and consumed['src']=='forecast'
     consumed={**consumed,'responseSha256':expected['sha256'],'replay':'Exact retained simulated hourly track at paired presentation UTC; not live weather'}
    else:consumed=h.require_weather(e.frame.evaluate(h.SNAP),family)
    # Hold only motion for layer subtraction; neither time nor this capture
    # is reported as continuous operation. Real playback has its own receipt.
    e.frame.add_style_tag(content='*,*::before,*::after{animation-play-state:paused!important;transition:none!important}')
    e.frame.evaluate('()=>{const p=paintClouds;paintClouds=()=>{};window.__dayRestoreCloud=p;}')
    state=e.snap('complete');audit=e.frame.evaluate(h.STAR_AUDIT);fields=e.frame.evaluate(ISOLATE)
    css=e.frame.add_style_tag(content='.rain,.snow,.drop,.flake{visibility:hidden!important}')
    e.element.screenshot(path=out/'without-precipitation.png');css.evaluate('(e)=>e.remove()')
    particles=ImageChops.difference(Image.open(out/'complete.png').convert('RGB'),Image.open(out/'without-precipitation.png').convert('RGB'))
    particles.save(out/'precipitation-only-difference.png')
    for p in fields['cases']:
     for field in ['atmosphere','joined']:(out/('preview-'+str(p['rate'])+'-'+field+'.png')).write_bytes(base64.b64decode(p.pop(field).split(',')[1]))
    pixels=daylight_pixels(out/'complete.png',family in ['clear','partial'])
    checks={'currentRefinedSky':state['displayedOwner']=='refined' and state['presentedFrame']['owner']=='refined' and state['presentedFrame']['ageMs']==0,
            'noRefinedDaytimeStars':audit['counts']['all']==0,'noPreviewDaytimeStars':all(p['visibleStarPixels']==0 for p in fields['cases']),
            'daylightPixels':pixels['pass'],'snowIsolation':family not in ['snow','incident-track'] or particles.crop((20,220,310,480)).getbbox() is not None}
    row={'family':family,'consumed':consumed,'state':state,'audit':audit,'fields':fields,'pixels':pixels,'checks':checks};rows.append(row)
    h.dump(out/'receipt.json',row);h.dump(a.out/'results.json',report);print(family,checks,flush=True)
   finally:e.close()
  b.close()
 report['failures']=[{'family':r['family'],'checks':r['checks']} for r in rows if not all(r['checks'].values())];report['status']='FAIL' if report['failures'] else 'PASS';report['runtimeUnchanged']=runtime_identity(a.root)==report['runtime']
 sheet=Image.new('RGB',(len(rows)*330,2*558),'#101828');d=ImageDraw.Draw(sheet)
 for x,r in enumerate(rows):
  for y,kind in enumerate(['complete','without-precipitation']):
   im=Image.open(a.out/r['family']/(kind+'.png'));sheet.paste(im,(x*330,y*558+24));d.text((x*330+3,y*558+4),r['family']+' '+kind,fill='white')
 sheet.save(a.out/'daytime-isolation.png');h.dump(a.out/'results.json',report);return not report['failures'] and report['runtimeUnchanged']

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=h.ROOT);p.add_argument('--out',type=Path,required=True);p.add_argument('--fonts',type=Path,required=True);p.add_argument('--negative',type=Path);p.add_argument('--incident',type=Path)
 raise SystemExit(0 if run(p.parse_args()) else 1)
