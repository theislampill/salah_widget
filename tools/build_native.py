#!/usr/bin/env python3
"""Deterministic offline native integration. No network, package install, or source reconstruction.

R0029: every output (Moon expansion included) is computed in memory and every guard runs
before the first in-tree write; `generated_outputs.publish` then replaces changed files,
removes stale owned files and writes GENERATED.json last. A detected failure leaves the
tree unchanged. One build per tree (concurrent builds on one tree are unsupported).
"""
from pathlib import Path
import re,json,hashlib
from native_core_horizon import correct_horizon
from native_core_spectral_cache import bound_spectral_cache
from native_star_bootstrap import star_bootstrap
from generated_outputs import Outputs,publish,replace_exact,require
R=Path(__file__).resolve().parents[1]; S=R/'vendor/real-sky'; W=R; N=W/'real-sky'
physical=(N/'checkpoint.json').exists() and json.loads((N/'checkpoint.json').read_text(encoding='utf-8'))['physical']
G=Outputs()  # planning -> computed: nothing below writes the tree until publish().
def text_of(data):return data.decode('utf-8').replace('\r\n','\n').replace('\r','\n')  # == read_text() newline handling
def rel(p):return str(p.relative_to(R)).replace('\\','/')
# Same dependency ordering as the retained CP7.5 build, plus bounded native interfaces.
core=['src/time-scales.mjs','src/astronomy.mjs','src/projection.mjs','src/photometry.mjs','src/spectral-tables.mjs','src/spectral.mjs','src/optics.mjs','src/renderer.mjs','src/atmosphere.mjs','src/sky-state.mjs','src/visibility.mjs','src/sky-background.mjs','src/catalogue.mjs','src/scene.mjs','src/sha256.mjs','src/diffuse-map.mjs','src/registered-starlight.mjs','src/diffuse-binding.mjs','src/diffuse-transport.mjs','src/physical-sky-renderer.mjs','integration/physical-sky-bridge.mjs','src/diffuse-assets.mjs','src/diffuse-manifest-pin.mjs','integration/resilient-sky-bridge.mjs','src/reference-engine.mjs']
for p in core+['src/reference-worker-client.mjs','src/latest-render-queue.mjs']:
 data=(S/p).read_bytes()
 if p=='src/physical-sky-renderer.mjs':data=correct_horizon(data)
 elif p=='src/spectral.mjs':data=bound_spectral_cache(data)
 G.add(rel(N/'core'/p),data)
# Preserve the already retained notices beside a separately copied widget too.
for name in ['LICENSE-CODE.txt','LICENSE-DATA.md','THIRD_PARTY_NOTICES.md',
 'upstream/ASTROPY_LICENSE.rst','vendor/spectral/IRAF-LICENSE.txt',
 'vendor/spectral/MITSUBA-LICENSE.txt','vendor/spectral/SPECLITE-LICENSE.txt',
 'provenance/cp7/admitted/ASTROGO-LICENSE.txt']:
 G.add(rel(N/'notices'/name),(S/name).read_bytes())
def read(p):
 # Generated inputs (the copied core) come from this run's staged outputs, never the tree.
 return G.text(rel(p)) if rel(p) in G else p.read_text(encoding='utf-8')
def concat(paths):
 out=[]
 for p in paths:
  s=read(p);s=re.sub(r'^import .*?;\s*$', '',s,flags=re.M);s=re.sub(r'\bexport (?=(?:const|let|function|class|async function)\b)','',s)
  if re.search(r'^\s*(?:import |export )',s,re.M):raise RuntimeError('Unbundled import/export '+str(p))
  out.append('// '+rel(p)+'\n'+s)
 return '\n'.join(out)
base=concat([N/'core'/p for p in core]+[N/'native-contract.mjs',N/'native-preview.mjs',N/'native-engine.mjs'])
worker=base+'''\nlet nativeWorkerEngine=null;
self.onmessage=async e=>{const m=e.data;try{if(m.kind==='boot'){nativeWorkerEngine=new NativeSkyEngine(m.pack);self.postMessage({kind:'ready'});}else if(m.kind==='render'){const result=await nativeWorkerEngine.render(m.job);self.postMessage({kind:'result',id:m.id,result},rasterTransferables(result));}}catch(e){self.postMessage({kind:'error',id:m.id,error:String(e.message??e)});}};
self.addEventListener('unhandledrejection',e=>{self.postMessage({kind:'fatal',error:String(e.reason)});});
'''
G.add('real-sky/native-worker.js',worker)
extra=['core/src/reference-worker-client.mjs','core/src/latest-render-queue.mjs','native-encoding.mjs','native-cloud-transfer.mjs']
if (N/'native-composition.mjs').exists():extra.append('native-composition.mjs')
extra.extend(['native-worker-policy.mjs','native-lifecycle.mjs','native-assets.mjs','native-host.mjs'])
boot='''
startNativeSkyAssets(pack=>startNativeSky(pack,WORKER_SOURCE,PHYSICAL_MODE),document.currentScript?.src);
'''
boot=replace_exact(boot,'WORKER_SOURCE',json.dumps(worker),'build_native worker template')
boot=replace_exact(boot,'PHYSICAL_MODE',str(bool(physical)).lower(),'build_native worker template')
G.add('real-sky/native-sky.js','(function(){"use strict";\n'+base+'\n'+concat([N/p for p in extra])+boot+'\n})();\n')
bootstrap_text,bootstrap_pin=star_bootstrap(S)
preview='(function(){"use strict";\n'+base+'\n'+concat([N/p for p in ['native-encoding.mjs','native-cloud-transfer.mjs','native-composition.mjs','native-star-preview.mjs','native-preview-host.mjs','native-first-paint.mjs']])+'\nwindow.SalahStarBootstrap=NativeStarPreview.fromBootstrap('+json.dumps(bootstrap_text)+','+json.dumps(bootstrap_pin,separators=(',',':'))+');\nwindow.SalahNativeCloudLighting=nativeCloudSolarLighting;window.SalahStartSkyPreview=startNativeSkyPreview;window.SalahPrepareFirstPaint=prepareNativeFirstPaint;\n})();\n'
pack={'catalogueText':(S/'data/bright-stars.json').read_text(encoding='utf-8'),'manifestText':(S/'data/registered-starlight/runtime-manifest.json').read_text(encoding='utf-8'),'assetTexts':{'128':(S/'data/registered-starlight/V-nside128.json').read_text(encoding='utf-8')} if physical else {}}
G.add('real-sky/native-data.js','window.__SALAH_REAL_SKY_PACK__='+json.dumps(pack,ensure_ascii=True,separators=(',',':'))+';\n')
# Source is pinned and retained locally. Only this explicit block replacement and hooks change index.
B=R/'src/native'
for authored in ['config.js','builder.html']:G.add(authored,(B/authored).read_bytes())
original=(B/'index.html').read_text(encoding='utf-8')
rng=re.findall(r'^function _mb32.*$',original,re.M)
require(len(rng)==1,'build_native starfield block: expected exactly one "function _mb32" line, found '+str(len(rng)))
rng=rng[0]
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
for marker in ['// PROJECTED STARFIELD:','// Accepted target/explicit anchor']:
 require(original.count(marker)==1,'build_native starfield block: anchor '+repr(marker)+' expected 1 occurrence(s), found '+str(original.count(marker)))
start=original.index('// PROJECTED STARFIELD:');end=original.index('// Accepted target/explicit anchor',start)
s=original[:start]+replacement+original[end:]
# Narrow additive handoff after native weather admission, guarded by original operation eligibility.
# Every anchor below is count-checked: a drifted anchor in src/native/index.html fails the build.
elevation_line='    if(track&&attemptEligible(op,a)){ weatherTrack=track; _renderDirty=true; }'
s=replace_exact(s,elevation_line,elevation_line+"\n    // CP9 elevation custody: notify only after this operation's eligible native weather adoption.\n    if((current||track)&&elevation!=null&&attemptEligible(op,a)&&selectedWeather()) window.SalahNativeSkyHost?.acceptedElevation(elevation,op.generation,captured.lat,captured.lon);",'build_native elevation hook')
s=replace_exact(s,'function beginSkyScene(initialDocument=false){','function beginSkyScene(initialDocument=false){\n  window.SalahSkyPreview?.clear("native beginSkyScene");\n  window.SalahRealSky?.invalidate("native beginSkyScene");','build_native beginSkyScene hooks')
s=replace_exact(s,'  commitSkyScene(A);\n}','  commitSkyScene(A);\n  window.SalahNativeSkyHost?.notify();\n}','build_native commitSkyScene notify hook')
s=replace_exact(s,'\nboot();','\n'+(N/'native-host-hooks.js').read_text(encoding='utf-8')+'\nboot();','build_native boot() hook insertion')
# Keep the complete initial-producer group after the native neutral markup,
# before boot. Parsing that markup can overlap its raster work with the bounded
# synchronous preparation; no timer, readiness gate or new clock is introduced.
config_tag='<script src="config.js"></script>'
if s.count(config_tag)!=1:raise ValueError('Expected native config script boundary')
s=replace_exact(s,'</head>','<link rel="stylesheet" href="real-sky/native-sky.css">\n</head>','build_native </head> stylesheet link')
s=replace_exact(s,config_tag,config_tag+'\n<script id="native-first-paint-code" data-sha256="'+hashlib.sha256(preview.encode()).hexdigest()+'">'+preview+'</script>','build_native config tag + first-paint script')
s=replace_exact(s,'</body>','<script src="real-sky/native-sky.js"></script>\n</body>','build_native </body> native-sky script')
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
G.add('real-sky/native-sky.css',css)

# Exact same native app expanded into one file, not the CP7 reference viewer.
def inline_js(text):return text.replace('</script','<\\/script')
standalone=replace_exact(s,'<script src="config.js"></script>','<script>'+inline_js(G.text('config.js'))+'</script>','build_native offline inline config.js')
standalone=replace_exact(standalone,'<link rel="stylesheet" href="real-sky/native-sky.css">','<style>'+css+'</style>','build_native offline inline stylesheet')
standalone=replace_exact(standalone,'<script src="real-sky/native-sky.js"></script>','<script>'+inline_js(G.text('real-sky/native-data.js'))+'</script><script>'+inline_js(G.text('real-sky/native-sky.js'))+'</script>','build_native offline inline data + native-sky scripts')

# Moon MB1: authored Moon sources/assets; deterministic generated entries. The Moon
# preflight runs against these staged entries; both expanded entries come back in memory.
from build_moon import plan_moon
moon_outputs,moon_summary=plan_moon(R,{'index.html':text_of(s.encode('utf-8')),'offline.html':text_of(standalone.encode('utf-8'))})
for path,data in moon_outputs.items():G.add(path,data)
# validated -> publishing -> published. Only now does the tree change.
result=publish(R,G)
print(json.dumps({'physical':bool(physical),'nativeBundleBytes':len(G['real-sky/native-sky.js']),'dataBundleBytes':len(G['real-sky/native-data.js']),'indexSha256':hashlib.sha256(G['index.html']).hexdigest(),'stage':'complete-native-and-moon',**result},indent=2))
