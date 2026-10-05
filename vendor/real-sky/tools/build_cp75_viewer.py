#!/usr/bin/env python3
"""Offline worker viewer. Embed exact source texts once; no network/runtime packages."""
from pathlib import Path
import json,re,hashlib
from build_cp74_viewer import MODULES as CP74
from build_cp75_manifest import build as build_manifest
R=Path(__file__).resolve().parents[1]
CORE=CP74[:-1]+['src/diffuse-assets.mjs','src/diffuse-manifest-pin.mjs','integration/resilient-sky-bridge.mjs','src/reference-engine.mjs']
def concat(root,names):
 parts=[]
 for name in names:
  text=(root/name).read_text();text=re.sub(r'^import .*?;\s*$','',text,flags=re.M);text=re.sub(r'\bexport\s+(?=(?:async\s+)?(?:const|function|class)\b)','',text)
  if re.search(r'^\s*(?:import|export)\s',text,re.M):raise ValueError('Unsupported module syntax '+name)
  parts.append('// '+name+'\n'+text)
 return '\n'.join(parts)
def build(root=R):
 build_manifest(root)
 pack={'catalogueText':(root/'data/bright-stars.json').read_text(),'manifestText':(root/'data/registered-starlight/runtime-manifest.json').read_text(),'assetTexts':{t:(root/f'data/registered-starlight/V-nside{t}.json').read_text() for t in ['32','64','128']},'scenes':json.loads((root/'data/cp74-scenes.json').read_text())}
 worker=concat(root,CORE+['demo/reference-worker.mjs'])
 main=concat(root,CORE+['src/latest-render-queue.mjs','src/reference-worker-client.mjs','demo/accepted-sky.mjs'])
 script=('window.__cp75Assets='+json.dumps(pack,separators=(',',':'),ensure_ascii=False)+';\nwindow.__cp75WorkerSource='+json.dumps(worker,separators=(',',':'),ensure_ascii=False)+';\n'+main).replace('</script','<\\/script')
 html=(root/'demo/accepted-sky.html').read_text();tag='<script type="module" src="./accepted-sky.mjs"></script>'
 if html.count(tag)!=1:raise ValueError('Missing viewer entry')
 html=html.replace(tag,'<script type="module">\n'+script+'\n</script>');out=root/'dist/accepted-physical-sky-viewer.html';out.write_text(html)
 return {'path':str(out.relative_to(root)),'bytes':out.stat().st_size,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'worker':True,'networkRequired':False}
if __name__=='__main__':print(json.dumps(build(),indent=2))
