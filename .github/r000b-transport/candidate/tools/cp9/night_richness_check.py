"""Matched retained V38/current richness: runtime fields and complete pixels.

Not an assertion that the owner's unlabelled attachment has this exact receipt.
Uses the closest retained Maghrib scene, explicitly fixed geometry and weather.
"""
from pathlib import Path
import sys,json,hashlib,argparse,shutil,time,math,copy
from PIL import Image,ImageDraw
from playwright.sync_api import sync_playwright
W=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(W/'tools/cp9'))
import hotfix_stress_check as h
from browser_runtime import launch_browser,browser_identity
from runtime_identity import runtime_identity

FIELD=r'''async()=>{
 const f=realSkyFrame(),r=f.raster,h=SalahNativeSkyHost.capture(),p=SalahSkyPreview.frame;
 const {NativeForegroundCapture}=await import('/salah_widget/real-sky/native-composition.mjs');
 const {nativeIdentity}=await import('/salah_widget/real-sky/native-contract.mjs');
 const capture=new NativeForegroundCapture(document.querySelector('.real-sky-canvas')).capture();
 const digest=async a=>{if(!a)return null;const u=new Uint8Array(a.buffer,a.byteOffset,a.byteLength),d=new Uint8Array(await crypto.subtle.digest('SHA-256',u));let sum=0,max=0;for(const v of a){sum+=v;max=Math.max(max,v);}return{length:a.length,sha256:[...d].map(x=>x.toString(16).padStart(2,'0')).join(''),sum,max};};
 const fields={};for(const name of ['stellarLinear','diffuseLinear','physicalSkyBackgroundLinear','skyBackgroundLinear','backgroundLinear','linear'])fields[name]=await digest(r[name]);
 return {native:h,expectedIdentity:nativeIdentity(h),frame:{utcMs:f.utcMs,native:f.native,observer:f.observer},dpr:devicePixelRatio,physical:r.physicalState,atmosphere:r.atmosphere,diffuse:r.diffuseState,catalogue:f.catalogue??realSkyState().last?.catalogue,exposure:r.effectiveExposure,display:r.displayPresentation,fields,cloudBuffer:await digest(capture.cloudRGBA),preview:p&&{quality:p.quality,stars:p.raster.starPreview}};
}'''

FIELDS={'stellarLinear','diffuseLinear','physicalSkyBackgroundLinear','skyBackgroundLinear','backgroundLinear','linear'}
UTC=1791417600000
def admitted(state,audit,field):
 n=field['native'];m=state['moon'];mh=state['moonPresentation']['host']
 assert state['utc']==n['utcMs']==field['frame']['utcMs']==field['physical']['utcMs']==audit['utc']==UTC
 assert field['frame']['native']['identity']==field['expectedIdentity'] and field['frame']['native']['generation']==n['generation']
 assert (n['lat'],n['lon'],n['heightM'],n['tz'])==(28.5383,-81.3792,25,'America/New_York')
 assert n['camera']=={'azDeg':180,'altDeg':45,'fovYDeg':90,'rollDeg':0} and n['lp']==0 and field['dpr']==1
 assert math.isfinite(field['exposure']) and field['exposure']>0
 assert state['displayedOwner']==audit['owner']=='refined' and m['status']=='ready' and m['quality']=='empirical-adaptive' and not m['legacyFallback'] and m['visibleSource']=='refined-terrain'
 assert state['visible']['base']['display']!='none' and state['visible']['base']['visibility']=='visible' and state['visible']['base']['opacity']==1
 assert state['presentedFrame']['owner']=='refined' and state['presentedFrame']['utcMs']==UTC and state['presentedFrame']['ageMs']==0
 assert state['moonPresentation']['geometry']['alt']==25 and state['moonPresentation']['geometry']['H']==42
 assert state['moonPresentation']['detail']['visible'] and mh['utcMs']==UTC and mh['fraction']==.5 and mh['waxing'] is False and mh['up']==1 and mh['dpr']==1
 assert field.get('diffuse',{}).get('enabled') and set(field['fields'])==FIELDS
 assert all(v and v['length']==325*530*3 and math.isfinite(v['sum']) and v['sum']>0 for v in field['fields'].values())
 assert field['cloudBuffer'] and field['cloudBuffer']['length']==325*530*4
 assert audit['counts']['unobscuredActual']>0,'No actual unobscured star contribution'

def comparison(old,new):
 equal={k:old['field']['fields'].get(k)==new['field']['fields'].get(k) for k in sorted(FIELDS)}
 # Predeclared tolerance: <=1 display code at the same unobscured catalogue
 # pixels. No magnitude/count boost is allowed to substitute for the old field.
 a={str(x['id']):x for x in old['audit']['candidates'] if x['cloudAlpha']==0 and x['delta']>=2}
 b={str(x['id']):x for x in new['audit']['candidates'] if x['cloudAlpha']==0 and x['delta']>=2}
 common=sorted(a.keys()&b.keys());bad=[k for k in common if max(a[k]['compositorSamplingError'],b[k]['compositorSamplingError'])>1 or abs(a[k]['actualDelta']-b[k]['actualDelta'])>1]
 ms=[r['state']['moon']['scene'] for r in [old,new]]
 geometry=all(ms[0].get(k)==ms[1].get(k) for k in ['size','outSize','diameter','basis','earth','distance','extent','profile','mode','waxing','tilt'])
 phase_error=max(r['state']['moon']['phasePrecision']['diameterDevicePixels'] for r in [old,new])/2*abs(math.acos(2*ms[0]['fraction']-1)-math.acos(2*ms[1]['fraction']-1))
 rects=[r['state']['moonPresentation']['photoRect'] for r in [old,new]]
 footprint=max(abs(rects[0][k]-rects[1][k]) for k in ['x','y','w','h'])
 checks={'fieldsEqual':set(old['field']['fields'])==set(new['field']['fields'])==FIELDS and all(equal.values()),'exposureEqual':old['field']['exposure']==new['field']['exposure'],'cloudBufferEqual':old['field']['cloudBuffer']==new['field']['cloudBuffer'],
  'actualStarsEqual':bool(common) and not bad and len(common)>=.99*max(len(a),len(b)),'moonGeometryComparable':geometry and phase_error<=.0416 and footprint<.05,'profileEqual':old['state']['moon']['profile']==new['state']['moon']['profile']}
 return {'family':old['family'],'equalFields':equal,'checks':checks,'commonUnobscuredStars':len(common),'actualStarMismatches':bad,'phaseDifferenceDevicePixels':phase_error,'maximumFootprintDifferenceCSSPixels':footprint,'oldCounts':old['audit']['counts'],'newCounts':new['audit']['counts'],'conditions':{'old':old['consumed'],'new':new['consumed']}}

def run(a):
 a.out.mkdir(parents=True,exist_ok=True);sys.path.insert(0,str(W/'tests'));from v1_browser import fonts
 shutil.copytree(a.fonts,a.out/'fonts',dirs_exist_ok=True);ff=fonts(a.out);rows=[]
 if a.surface_replay:h.MONITOR+=h.surface_replay_script(a.surface_replay)
 with sync_playwright() as p:
  b=launch_browser(p);identity=browser_identity(b)
  for label,root in [('reference',a.reference),('candidate',a.root)]:
   for family in ['clear','partial','overcast']:
    out=a.out/(label+'-'+family);e=h.Entry(b,root,out,ff,rate=0,start='2026-10-08T00:00:00Z',family=family,steady=True,overrides='simMoon=0.5&simWax=0&simMoonAlt=25&simMoonH=42')
    try:
     e.frame.evaluate('utcMs=>SalahClock.set({utcMs,rate:0})',e.anchor)
     e.frame.wait_for_function("SalahMoonRuntime.state.status==='ready'&&SalahMoonDetail.state.visible&&realSkyState().status==='ready'",timeout=600000,polling=1000)
     e.page.wait_for_timeout(2000);state=e.snap('complete');consumed=h.require_weather(state,family);audit=e.frame.evaluate(h.STAR_AUDIT);field=e.frame.evaluate(FIELD)
     admitted(state,audit,field)
     # Only this diagnostic freezes cloud capture after the complete capture.
     # It does not qualify real motion or refinement timing.
     isolated=e.frame.evaluate(r'''async()=>{const {encodeNativeFrame}=await import('/salah_widget/real-sky/native-encoding.mjs');const r=realSkyFrame().raster,cv=document.createElement('canvas');cv.width=325;cv.height=530;const make=a=>{cv.getContext('2d').putImageData(new ImageData(encodeNativeFrame(a,r.effectiveExposure),325,530),0,0);return cv.toDataURL();};const out={};for(const n of ['stellarLinear','diffuseLinear','skyBackgroundLinear','linear'])if(r[n])out[n]=make(r[n]);return out;}''')
     import base64
     for name,url in isolated.items():(out/(name+'.png')).write_bytes(base64.b64decode(url.split(',')[1]))
     reuse=e.frame.evaluate('window.__surfaceReplay??null')
     entry={'label':label,'family':family,'runtime':runtime_identity(root),'state':state,'consumed':consumed,'audit':audit,'field':field,'surfaceReplay':reuse,'errors':e.errors,'failedLocal':e.failures}
     h.dump(out/'receipt.json',entry);rows.append(entry);print(label,family,audit['counts'],flush=True)
    finally:e.close()
  b.close()
 comparisons=[]
 for family in ['clear','partial','overcast']:
  old=next(r for r in rows if r['label']=='reference' and r['family']==family);new=next(r for r in rows if r['label']=='candidate' and r['family']==family)
  comparisons.append(comparison(old,new))
 sheet=Image.new('RGB',(990,1120),'#101828');d=ImageDraw.Draw(sheet)
 for y,label in enumerate(['reference','candidate']):
  for x,family in enumerate(['clear','partial','overcast']):
   im=Image.open(a.out/(label+'-'+family)/'complete.png');assert im.size==(330,534);sheet.paste(im,(330*x,560*y+24));d.text((330*x+3,560*y+5),label+' '+family+' complete/refined',fill='white')
 sheet.save(a.out/'matched-complete.png')
 # Negative controls retain the real receipt's raw fields, but withdraw actual
 # stars or alter the cloud input. Neither may be passed by raw-field equality.
 old=rows[0];new=next(r for r in rows if r['label']=='candidate' and r['family']==old['family'])
 absent=copy.deepcopy(new)
 for s in absent['audit']['candidates']:s['actualDelta']=0
 changed=copy.deepcopy(new);changed['field']['cloudBuffer']['sha256']='changed-control'
 negative={'missingDisplayedStarsRejected':not comparison(old,absent)['checks']['actualStarsEqual'],'changedCloudBufferRejected':not comparison(old,changed)['checks']['cloudBufferEqual']}
 h.dump(a.out/'negative-controls.json',negative);assert all(negative.values())
 h.dump(a.out/'results.json',{'scope':'Matched retained scene at 2026-10-08T00:00Z, sanitized Orlando, south45/FOV90, native half-waning+25/H42 overrides, DPR1. Complete current refined Moon and sky. Fixed provider preview lane for geometry comparison, not live weather or motion. Owner attachment identity remains unverified; similar retained scene is explicitly the reference.', 'surfaceReplay':None if not a.surface_replay else {'path':str(a.surface_replay),'sha256':hashlib.sha256(a.surface_replay.read_bytes()).hexdigest(),'scope':'Reuse of the unchanged V5 numerical surface only after exact geometry/profile key equality. Not a worker performance, availability or fresh-solve claim. Per-context match/rejection counts are in receipts.'},'browser':identity,'comparisons':comparisons,'failures':[c for c in comparisons if not all(c['checks'].values())],'errors':[r['errors'] for r in rows if r['errors']]})
 return all(all(c['checks'].values()) for c in comparisons) and not any(r['errors'] or r['failedLocal'] for r in rows)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=W);p.add_argument('--reference',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--fonts',type=Path,required=True);p.add_argument('--surface-replay',type=Path);raise SystemExit(0 if run(p.parse_args()) else 1)
