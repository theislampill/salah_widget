#!/usr/bin/env python3
"""Build Moon MB1 from complete local source. No network, npm, or compiler required.

Call from build_native.py after the unmodified CP9 output is generated. The supplied
WASM is source-bound; recompilation is optional and separately qualified.
"""
from pathlib import Path
import base64, hashlib, json, math, re
from compact_receivers import compact_receivers

WORKER_UNITS=['asset-digest.mjs','surface_v5.mjs','moon-detail.mjs','moon-calendar.mjs','moon-engine.mjs','moon-quality.mjs','moon-pool.mjs','moon-worker.mjs']
HOST_UNITS=['asset-digest.mjs','surface_v5.mjs','moon-detail.mjs','moon-calendar.mjs','moon-initial.mjs','moon-initial-compact.mjs','moon-precision.mjs','moon-first-paint.mjs']
PROFILE={'schema':'lunar-presentation/5','profile_id':'calendar-neutral-v5-01','mode':'calendar','exposure':2.9195482731525044,'lift':0.003,'knee':5.388411226362526e-6,'colour_basis':'linear-sRGB','gamut':'luminance-preserving-neutral-axis'}
CHUNK_BYTES=786432  # independently padded base64 chunks, 1 MiB script text

def sha(data):return hashlib.sha256(data).hexdigest()
def write(path,text):
 path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text,encoding='utf-8',newline='\n')
def inline(text):return text.replace('</script','<\\/script')

def native_lunar_owner(root):
 # These are generated copies of the ONE native owner, not another maintained
 # phase model. Guard the source boundaries before any Moon output is written.
 source=(root/'src/native/index.html').read_text(encoding='utf-8')
 def section(start,end):
  if source.count(start)!=1 or source.count(end)!=1:raise ValueError('Native lunar owner boundary')
  return source[source.index(start):source.index(end,source.index(start))]
 clamp=re.findall(r'^const clamp=.*$',source,re.M)
 if len(clamp)!=1:raise ValueError('Native clamp owner boundary')
 return '\n'.join([clamp[0],section('const _RAD=Math.PI/180','// Galactic centre'),
  section('function moonPhase(date){','// ---- PBR MOON:'),
  section('const MOON_SCALE_MIN=','function renderMoon(){'),
  section('function nativeLunarPresentation(','function lunarPresentation(')])
def build_moon(root):
 root=Path(root).resolve(); moon=root/'moon'
 # Validate both entries before writing any output. A direct repeated Moon build
 # must not partially replace index.html before rejecting the offline entry.
 entries={name:(root/name).read_text(encoding='utf-8') for name in ['index.html','offline.html']}
 boundary='\nboot();'
 native_end=boundary+'\n</script>'
 for name,text in entries.items():
  if any(marker in text for marker in ['<script src="moon/moon-host.js"></script>','window.__SALAH_MOON_INLINE__=true','window.__SALAH_MOON_EMBEDDED__=true','id="moon-embedded-0"']):
   raise ValueError('Run tools/build_native.py, not build_moon directly on already-built entries')
  if text.count(boundary)!=1:raise ValueError('Expected native boot boundary in '+name)
  if text.count(native_end)!=1 or text.count('</head>')!=1:raise ValueError('Expected independent native script and head in '+name)
 native_owner=native_lunar_owner(root)
 manifest=json.loads((moon/'asset-manifest.json').read_text(encoding='utf-8'))
 packed={}
 for key,spec in manifest['assets'].items():
  data=(moon/spec['path']).read_bytes()
  if len(data)!=spec['bytes'] or sha(data)!=spec['sha256']:raise ValueError('Moon asset identity: '+key)
  packed[key]=data
 wasm=(moon/'moon_kernel.wasm').read_bytes()
 if len(wasm)!=manifest['wasm']['bytes'] or sha(wasm)!=manifest['wasm']['sha256']:raise ValueError('WASM identity')
 initial_pin=json.loads((moon/'initial-manifest.json').read_text(encoding='utf-8'))
 initial=(moon/'assets/initial-receivers.bin').read_bytes()
 if len(initial)!=initial_pin['bytes'] or sha(initial)!=initial_pin['sha256']:raise ValueError('Initial receiver identity')
 if initial_pin['parent']!={'manifestSha256':sha((moon/'asset-manifest.json').read_bytes()),'wasmSha256':sha(wasm),'demRawSha256':manifest['assets']['dem']['rawSha256'],'colourRawSha256':manifest['assets']['colour']['rawSha256']}:raise ValueError('Initial receiver ancestry')
 for path,digest in initial_pin['source'].items():
  if sha((root/path).read_bytes())!=digest:raise ValueError('Initial receiver source drift: '+path)
 compact,encoding=compact_receivers(initial)
 decoded_pin={key:initial_pin[key] for key in ['schema','size','records','bytes','geometry']}
 decoded_pin.update(sha256=encoding['decodedSha256'],
  parent={'initialReceiverSha256':sha(initial),'initialManifestSha256':sha((moon/'initial-manifest.json').read_bytes())},
  representation={'schema':encoding['schema'],'encodedSha256':sha(compact),'fields':encoding['fields']},
  approximation={'normalEncoding':'octahedral 5+5 bits, normalized then serialized signed16',
   'materialEncoding':'5 bits per linear channel in the recorded source ranges; serialized unorm16',
   'positionEncoding':'8-bit source-range camera depth; reconstructed float32 and rigid rays',
   'additionalHorizonQuantizationHalfStepRadians':math.pi/510,
   'parentApproximation':initial_pin.get('approximation',{}),
   'finiteSourceSamples':16,'offPlaneTerrain':'full worker refinement required','earthTerrain':'observer-facing approximation; full worker refinement required'},
  qualification='Changed initial representation; parent trace probes do not qualify compact fields. Consumer numerical and browser qualification are separate.')
 def concat(names):
  return ''.join('// '+n+'\n'+(moon/'src'/n).read_text(encoding='utf-8').rstrip()+'\n' for n in names)
 worker='const MOON_ASSET_MANIFEST='+json.dumps(manifest,separators=(',',':'))+';\nconst MOON_WASM_BASE64='+json.dumps(base64.b64encode(wasm).decode('ascii'))+';\n'+concat(WORKER_UNITS)
 write(moon/'moon-worker.js',worker)
 chunks=[]; tags=[]; counter=0
 for key,data in packed.items():
  path=manifest['assets'][key]['path']
  for i,offset in enumerate(range(0,len(data),CHUNK_BYTES)):
   code=base64.b64encode(data[offset:offset+CHUNK_BYTES]).decode('ascii');last=offset+CHUNK_BYTES>=len(data);part=f'file-data/{key}-{i:03}.js'
   chunks.append({'name':path,'index':i,'path':part,'last':last})
   write(moon/part, 'window.SalahMoonAssetChunk('+','.join([json.dumps(path),str(i),json.dumps(code),str(last).lower()])+');\n')
   tags.append(f'<script type="application/octet-stream" id="moon-embedded-{counter}">'+code+'</script>');counter+=1
 cloud=(root/'real-sky/native-cloud-transfer.mjs').read_text(encoding='utf-8').replace('export ','')
 initial_boot='\ntry{const text=atob('+json.dumps(base64.b64encode(compact).decode('ascii'))+'),packed=new Uint8Array(text.length);for(let i=0;i<text.length;i++)packed[i]=text.charCodeAt(i);const bytes=decodeCompactReceivers(packed,'+json.dumps(encoding,separators=(',',':'))+');window.SalahMoonInitial=createInitialMoon(bytes,'+json.dumps(decoded_pin,separators=(',',':'))+');}catch(error){window.SalahMoonInitialError=String(error.message??error);}\n'
 worker_pin={'bytes':len(worker.encode()),'sha256':sha(worker.encode())}
 head_owner='''
window.SalahMoonHead={
 compose(preview,snapshot,sim,encode){return composeNativeHeadMoon(preview,snapshot,sim,
  {snapshot:nativeLunarSnapshot,presentation:nativeLunarPresentation,scene:nativeCalendarMoonScene},
  {initial:window.SalahMoonInitial,profile:MOON_DEFAULT_PROFILE,phaseQuantum,canonicalFraction,prefixSurface,boxSurface,sampleField,joinLunarPixel,encode});},
 backgroundRule:nativeHeadMoonBackgroundRule
};
window.SalahPrepareFirstPaint?.();
'''
 host='(function(){\n'+cloud+'\nconst MOON_DEFAULT_PROFILE='+json.dumps(PROFILE,separators=(',',':'))+';\nlet MOON_WORKER_SOURCE=null;\nconst MOON_WORKER_PIN='+json.dumps(worker_pin,separators=(',',':'))+';\nconst MOON_OFFLINE_CHUNKS='+json.dumps(chunks,separators=(',',':'))+';\n'+concat(HOST_UNITS)+'\n'+native_owner+initial_boot+concat(['moon-native.mjs'])+head_owner+'\n})();\n'
 refinement='window.SalahMoonRuntime.installWorkerSource('+json.dumps(worker)+');\n'
 write(moon/'moon-host.js',host+refinement)
 (moon/'assets/initial-compact.bin').write_bytes(compact)
 write(moon/'initial-compact-manifest.json',json.dumps(encoding,indent=2)+'\n')
 # The small current receiver owner precedes card markup. Native declarations
 # and boot keep their own closing script tag; the independent full refinement
 # source follows it. A held HTML tail cannot hold settings/prayer execution or
 # add the first Moon later. No new request, hidden card or loader is involved.
 refinement_tag='\n<script id="moon-refinement-code">'+inline(refinement)+'</script>\n'
 for name,text in entries.items():
  flags='window.__SALAH_MOON_INLINE__=true;if(location.protocol==="file:")window.__SALAH_MOON_OFFLINE__=true;' if name=='index.html' else 'window.__SALAH_MOON_INLINE__=true;window.__SALAH_MOON_OFFLINE__=true;window.__SALAH_MOON_EMBEDDED__=true;'
  initial_tag='\n<script id="moon-initial-code">'+flags+'\n'+inline(host)+'</script>\n'
  text=text.replace('</head>',initial_tag+'</head>',1).replace(native_end,native_end+refinement_tag,1)
  if name=='offline.html':text=text.replace('</body>','\n'.join(tags)+'\n</body>',1)
  write(root/name,text)
 sources={str(p.relative_to(root)).replace('\\','/'):sha(p.read_bytes()) for p in sorted({moon/'src'/n for n in WORKER_UNITS+HOST_UNITS+['moon-native.mjs','moon_kernel.c']})}
 sources['real-sky/native-cloud-transfer.mjs']=sha((root/'real-sky/native-cloud-transfer.mjs').read_bytes())
 sources['tools/compact_receivers.py']=sha((root/'tools/compact_receivers.py').read_bytes())
 sources['src/native/index.html']=sha((root/'src/native/index.html').read_bytes())
 write(moon/'BUILD.json',json.dumps({'schema':'moon-build/1','source':sources,'compilerRequired':False,'kernelSha256':sha(wasm),'workerSha256':sha(worker.encode()),'hostSha256':sha((host+refinement).encode()),'assetManifestSha256':sha((moon/'asset-manifest.json').read_bytes()),'initialReceiverSha256':sha(initial),'initialManifestSha256':sha((moon/'initial-manifest.json').read_bytes()),'initialCompact':encoding,'chunkCount':len(chunks),'profile':PROFILE},indent=2)+'\n')
 return {'moonHostBytes':len((host+refinement).encode()),'moonInitialHostBytes':len(host.encode()),'moonWorkerBytes':len(worker.encode()),'assetBytes':sum(map(len,packed.values())),'chunks':len(chunks)}
