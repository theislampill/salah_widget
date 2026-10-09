#!/usr/bin/env python3
"""Deterministic offline native integration. No network, package install, or source reconstruction."""
from pathlib import Path
import re,json,shutil,hashlib
from native_core_horizon import correct_horizon
from native_star_bootstrap import star_bootstrap
R=Path(__file__).resolve().parents[1]; S=R/'vendor/real-sky'; W=R; N=W/'real-sky'
physical=(N/'checkpoint.json').exists() and json.loads((N/'checkpoint.json').read_text(encoding='utf-8'))['physical']
# Same dependency ordering as the retained CP7.5 build, plus bounded native interfaces.
core=['src/time-scales.mjs','src/astronomy.mjs','src/projection.mjs','src/photometry.mjs','src/spectral-tables.mjs','src/spectral.mjs','src/optics.mjs','src/renderer.mjs','src/atmosphere.mjs','src/sky-state.mjs','src/visibility.mjs','src/sky-background.mjs','src/catalogue.mjs','src/scene.mjs','src/sha256.mjs','src/diffuse-map.mjs','src/registered-starlight.mjs','src/diffuse-binding.mjs','src/diffuse-transport.mjs','src/physical-sky-renderer.mjs','integration/physical-sky-bridge.mjs','src/diffuse-assets.mjs','src/diffuse-manifest-pin.mjs','integration/resilient-sky-bridge.mjs','src/reference-engine.mjs']
for p in core+['src/reference-worker-client.mjs','src/latest-render-queue.mjs']:
 target=N/'core'/p; target.parent.mkdir(parents=True,exist_ok=True)
 if p=='src/physical-sky-renderer.mjs':target.write_bytes(correct_horizon((S/p).read_bytes()))
 else:shutil.copyfile(S/p,target)
# Preserve the already retained notices beside a separately copied widget too.
for name in ['LICENSE-CODE.txt','LICENSE-DATA.md','THIRD_PARTY_NOTICES.md',
 'upstream/ASTROPY_LICENSE.rst','vendor/spectral/IRAF-LICENSE.txt',
 'vendor/spectral/MITSUBA-LICENSE.txt','vendor/spectral/SPECLITE-LICENSE.txt',
 'provenance/cp7/admitted/ASTROGO-LICENSE.txt']:
 target=N/'notices'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(S/name,target)
def concat(paths):
 out=[]
 for p in paths:
  s=p.read_text(encoding='utf-8');s=re.sub(r'^import .*?;\s*$', '',s,flags=re.M);s=re.sub(r'\bexport (?=(?:const|let|function|class|async function)\b)','',s)
  if re.search(r'^\s*(?:import |export )',s,re.M):raise RuntimeError('Unbundled import/export '+str(p))
  out.append('// '+str(p.relative_to(R)).replace('\\','/')+'\n'+s)
 return '\n'.join(out)
base=concat([N/'core'/p for p in core]+[N/'native-contract.mjs',N/'native-engine.mjs'])
worker=base+'''\nlet nativeWorkerEngine=null;
self.onmessage=async e=>{const m=e.data;try{if(m.kind==='boot'){nativeWorkerEngine=new NativeSkyEngine(m.pack);self.postMessage({kind:'ready'});}else if(m.kind==='render'){const result=await nativeWorkerEngine.render(m.job);self.postMessage({kind:'result',id:m.id,result},rasterTransferables(result));}}catch(e){self.postMessage({kind:'error',id:m.id,error:String(e.message??e)});}};
self.addEventListener('unhandledrejection',e=>{self.postMessage({kind:'fatal',error:String(e.reason)});});
'''
(N/'native-worker.js').write_text(worker,encoding='utf-8',newline='\n')
extra=['core/src/reference-worker-client.mjs','core/src/latest-render-queue.mjs','native-encoding.mjs','native-cloud-transfer.mjs']
if (N/'native-composition.mjs').exists():extra.append('native-composition.mjs')
extra.extend(['native-preview.mjs','native-worker-policy.mjs','native-lifecycle.mjs','native-assets.mjs','native-host.mjs'])
boot='''
startNativeSkyAssets(pack=>startNativeSky(pack,WORKER_SOURCE,PHYSICAL_MODE),document.currentScript?.src);
'''.replace('WORKER_SOURCE',json.dumps(worker)).replace('PHYSICAL_MODE',str(bool(physical)).lower())
(N/'native-sky.js').write_text('(function(){"use strict";\n'+base+'\n'+concat([N/p for p in extra])+boot+'\n})();\n',encoding='utf-8',newline='\n')
bootstrap_text,bootstrap_pin=star_bootstrap(S)
preview='(function(){"use strict";\n'+base+'\n'+concat([N/p for p in ['native-encoding.mjs','native-cloud-transfer.mjs','native-composition.mjs','native-preview.mjs','native-star-preview.mjs','native-preview-host.mjs','native-first-paint.mjs']])+'\nwindow.SalahStarBootstrap=NativeStarPreview.fromBootstrap('+json.dumps(bootstrap_text)+','+json.dumps(bootstrap_pin,separators=(',',':'))+');\nwindow.SalahNativeCloudLighting=nativeCloudSolarLighting;window.SalahStartSkyPreview=startNativeSkyPreview;prepareNativeFirstPaint();\n})();\n'
pack={'catalogueText':(S/'data/bright-stars.json').read_text(encoding='utf-8'),'manifestText':(S/'data/registered-starlight/runtime-manifest.json').read_text(encoding='utf-8'),'assetTexts':{'128':(S/'data/registered-starlight/V-nside128.json').read_text(encoding='utf-8')} if physical else {}}
(N/'native-data.js').write_text('window.__SALAH_REAL_SKY_PACK__='+json.dumps(pack,ensure_ascii=True,separators=(',',':'))+';\n',encoding='utf-8',newline='\n')
# Source is pinned and retained locally. Only this explicit block replacement and hooks change index.
B=R/'src/native'
for authored in ['config.js','builder.html']:shutil.copyfile(B/authored,W/authored)
original=(B/'index.html').read_text(encoding='utf-8')
rng=re.search(r'^function _mb32.*$',original,re.M).group(0)
replacement='''// REAL CATALOGUE: optional worker projection; accepted native inputs own the scene.
'''+rng+'''
let _starEls=[],_starsProjected=false,_starProjectionKey=null;
function projectStars(date){
 const key=skySceneIdentity();_starProjectionKey=key;_starsProjected=key!==null&&Number.isFinite(date.getTime());
 if(!_starsProjected)window.SalahRealSky?.invalidate('invalid native projection input');
}
function refreshStarAppearance(A){ /* Physical lunar sky wash belongs to Real-Sky, not a second per-star dimmer. */ }
function buildStars(){
 for(const selector of ['.stars','.starglints','.milkyway']){const el=document.querySelector(selector);if(el)el.replaceChildren();}
 projectStars(simDate());
}

'''
start=original.index('// PROJECTED STARFIELD:');end=original.index('// Accepted target/explicit anchor',start)
s=original[:start]+replacement+original[end:]
# Narrow additive handoff after native weather admission, guarded by original operation eligibility.
elevation_line='    if(track&&attemptEligible(op,a)) weatherTrack=track;'
assert s.count(elevation_line)==1
s=s.replace(elevation_line,elevation_line+"\n    // CP9 elevation custody: notify only after this operation's eligible native weather adoption.\n    if((current||track)&&elevation!=null&&attemptEligible(op,a)&&selectedWeather()) window.SalahNativeSkyHost?.acceptedElevation(elevation,op.generation,captured.lat,captured.lon);",1)
s=s.replace('function beginSkyScene(){','function beginSkyScene(){\n  window.SalahSkyPreview?.clear("native beginSkyScene");\n  window.SalahRealSky?.invalidate("native beginSkyScene");',1)
s=s.replace('  commitSkyScene(A);\n}','  commitSkyScene(A);\n  window.SalahNativeSkyHost?.notify();\n}',1)
s=s.replace('\nboot();','\n'+(N/'native-host-hooks.js').read_text(encoding='utf-8')+'\nboot();',1)
# The shared resolver and bounded atmosphere must run before static card markup
# can paint. No visibility gate: the first card already has its accepted sky.
s=s.replace('<script src="config.js"></script>','',1)
s=s.replace('</head>','<link rel="stylesheet" href="real-sky/native-sky.css">\n<script src="config.js"></script>\n<script id="native-first-paint-code" data-sha256="'+hashlib.sha256(preview.encode()).hexdigest()+'">'+preview+'</script>\n</head>',1)
s=s.replace('</body>','<script src="real-sky/native-sky.js"></script>\n</body>',1)
(W/'index.html').write_text(s,encoding='utf-8',newline='\n')
css='''.real-sky-canvas{position:absolute;inset:0;width:100%;height:100%;z-index:0;pointer-events:none;border-radius:inherit;visibility:hidden}.real-sky-status{position:absolute;bottom:3px;left:0;width:100%;text-align:center;font:8px sans-serif;color:#aaa;z-index:3;pointer-events:none}.milkyway,.stars,.starglints{display:none!important}
/* A valid accepted atmosphere owns the first visible sky. No timer or worker
   readiness can turn an accepted daytime target into a dark placeholder. */
.c{background:#273445}
.real-sky-preview{position:absolute;inset:0;width:100%;height:100%;z-index:0;pointer-events:none;border-radius:inherit;visibility:hidden}
.c.real-sky-composed .real-sky-preview{display:none}
.c.real-sky-preview-ready .sky .mphoto,.c.real-sky-preview-ready .sky .moccluder,.c.real-sky-preview-ready .sky .mbeam,.c.real-sky-preview-ready .sky .mglow{visibility:hidden!important}
.wfx .cloudcanvas{visibility:hidden!important}
.wfx .fog,.wfx .veil,.wfx .sunhaze,.c>.grain,.c>.climate{display:none!important}
/* Broad sky radiance is now physical. Native discs and discrete optical presentations stay native. */
.atmo .airglow,.atmo .aurora,.atmo .scatter,.atmo .belt,.atmo .anticrep,.atmo>.sun{display:none!important}
'''
if physical:css+='''/* Painter remains live for transfer and rain; bounded display colour is composed exactly once. */
.c.real-sky-composed .wfx .cloudcanvas{visibility:hidden!important}
.c.real-sky-composed .sky .mphoto,.c.real-sky-composed .sky .moccluder,.c.real-sky-composed .sky .mbeam,.c.real-sky-composed .sky .mglow{visibility:hidden!important}
/* Discrete native solar/lunar optics remain condition-gated presentation layers, not diffuse/background meters. */
.c.real-sky-composed .wfx .fog,.c.real-sky-composed .wfx .veil,.c.real-sky-composed .wfx .sunhaze,.c.real-sky-composed>.grain,.c.real-sky-composed>.climate{display:none!important}
'''
(N/'native-sky.css').write_text(css,encoding='utf-8',newline='\n')
print(json.dumps({'physical':bool(physical),'nativeBundleBytes':(N/'native-sky.js').stat().st_size,'dataBundleBytes':(N/'native-data.js').stat().st_size,'indexSha256':hashlib.sha256((W/'index.html').read_bytes()).hexdigest()},indent=2))

# Exact same native app expanded into one file, not the CP7 reference viewer.
def inline_js(text):return text.replace('</script','<\\/script')
standalone=s.replace('<script src="config.js"></script>','<script>'+inline_js((W/'config.js').read_text(encoding='utf-8'))+'</script>')
standalone=standalone.replace('<link rel="stylesheet" href="real-sky/native-sky.css">','<style>'+css+'</style>')
standalone=standalone.replace('<script src="real-sky/native-sky.js"></script>','<script>'+inline_js((N/'native-data.js').read_text(encoding='utf-8'))+'</script><script>'+inline_js((N/'native-sky.js').read_text(encoding='utf-8'))+'</script>')
(W/'offline.html').write_text(standalone,encoding='utf-8',newline='\n')

# Moon MB1: authored Moon sources/assets; deterministic generated entries.
from build_moon import build_moon
build_moon(R)
