#!/usr/bin/env python3
"""Build Moon MB1 from complete local source. No network, npm, or compiler required.

Call from build_native.py after the unmodified CP9 output is generated. The supplied
WASM is source-bound; recompilation is optional and separately qualified.
"""
from pathlib import Path
import base64, hashlib, json, re

WORKER_UNITS=['asset-digest.mjs','surface_v5.mjs','moon-detail.mjs','moon-calendar.mjs','moon-engine.mjs','moon-quality.mjs','moon-worker.mjs']
HOST_UNITS=['moon-detail.mjs','moon-calendar.mjs','moon-precision.mjs','moon-native.mjs']
PROFILE={'schema':'lunar-presentation/5','profile_id':'calendar-neutral-v5-01','mode':'calendar','exposure':2.9195482731525044,'lift':0.003,'knee':5.388411226362526e-6,'colour_basis':'linear-sRGB','gamut':'luminance-preserving-neutral-axis'}
CHUNK_BYTES=786432  # independently padded base64 chunks, 1 MiB script text

def sha(data):return hashlib.sha256(data).hexdigest()
def write(path,text):
 path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text,encoding='utf-8',newline='\n')
def inline(text):return text.replace('</script','<\\/script')
def build_moon(root):
 root=Path(root).resolve(); moon=root/'moon'; manifest=json.loads((moon/'asset-manifest.json').read_text(encoding='utf-8'))
 packed={}
 for key,spec in manifest['assets'].items():
  data=(moon/spec['path']).read_bytes()
  if len(data)!=spec['bytes'] or sha(data)!=spec['sha256']:raise ValueError('Moon asset identity: '+key)
  packed[key]=data
 wasm=(moon/'moon_kernel.wasm').read_bytes()
 if len(wasm)!=manifest['wasm']['bytes'] or sha(wasm)!=manifest['wasm']['sha256']:raise ValueError('WASM identity')
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
 host='(function(){\nconst MOON_DEFAULT_PROFILE='+json.dumps(PROFILE,separators=(',',':'))+';\nconst MOON_WORKER_SOURCE='+json.dumps(worker)+';\nconst MOON_OFFLINE_CHUNKS='+json.dumps(chunks,separators=(',',':'))+';\n'+concat(HOST_UNITS)+'\n})();\n'
 write(moon/'moon-host.js',host)
 # CP9 has already regenerated each entry; refuse stacking repeated Moon injections.
 entry=root/'index.html';text=entry.read_text(encoding='utf-8')
 if '<script src="moon/moon-host.js"></script>' in text:raise ValueError('Run tools/build_native.py, not build_moon directly on already-built entries')
 multi='<script>if(location.protocol==="file:")window.__SALAH_MOON_OFFLINE__=true;</script>\n<script src="moon/moon-host.js"></script>\n'
 if text.count('</body>')!=1:raise ValueError('Expected native body boundary')
 write(entry,text.replace('</body>',multi+'</body>',1))
 entry=root/'offline.html';text=entry.read_text(encoding='utf-8')
 if 'id="moon-embedded-0"' in text:raise ValueError('Duplicate embedded Moon source')
 single='\n'.join(tags)+'\n<script>window.__SALAH_MOON_OFFLINE__=true;window.__SALAH_MOON_EMBEDDED__=true;</script>\n<script>'+inline(host)+'</script>\n'
 write(entry,text.replace('</body>',single+'</body>',1))
 sources={str(p.relative_to(root)).replace('\\','/'):sha(p.read_bytes()) for p in sorted([moon/'src'/n for n in WORKER_UNITS+['moon-precision.mjs','moon-native.mjs','moon_kernel.c']])}
 write(moon/'BUILD.json',json.dumps({'schema':'moon-build/1','source':sources,'compilerRequired':False,'kernelSha256':sha(wasm),'workerSha256':sha(worker.encode()),'hostSha256':sha(host.encode()),'assetManifestSha256':sha((moon/'asset-manifest.json').read_bytes()),'chunkCount':len(chunks),'profile':PROFILE},indent=2)+'\n')
 return {'moonHostBytes':len(host.encode()),'moonWorkerBytes':len(worker.encode()),'assetBytes':sum(map(len,packed.values())),'chunks':len(chunks)}
