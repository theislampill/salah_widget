#!/usr/bin/env python3
"""Deterministic offline physical diffuse viewer; exact catalogue bytes are embedded."""
from pathlib import Path
import re,json,hashlib
R=Path(__file__).resolve().parents[1]
MODULES=['src/time-scales.mjs','src/astronomy.mjs','src/projection.mjs','src/photometry.mjs','src/spectral-tables.mjs','src/spectral.mjs','src/optics.mjs','src/renderer.mjs','src/atmosphere.mjs','src/sky-state.mjs','src/visibility.mjs','src/sky-background.mjs','src/catalogue.mjs','src/scene.mjs','src/sha256.mjs','src/diffuse-map.mjs','src/registered-starlight.mjs','src/diffuse-binding.mjs','src/diffuse-transport.mjs','src/physical-sky-renderer.mjs','integration/physical-sky-bridge.mjs','demo/physical-diffuse.mjs']
def build(root=R):
 parts=[]
 for name in MODULES:
  text=(root/name).read_text();text=re.sub(r'^import .*?;\s*$','',text,flags=re.M);text=re.sub(r'\bexport\s+(?=(?:async\s+)?(?:const|function|class)\b)','',text)
  if re.search(r'^\s*(?:import|export)\s',text,re.M):raise ValueError('Unsupported module syntax: '+name)
  parts.append('// '+name+'\n'+text)
 raw=(root/'data/bright-stars.json').read_bytes();digest=hashlib.sha256(raw).hexdigest()
 maps={t:json.loads((root/f'data/registered-starlight/V-nside{t}.json').read_text()) for t in ['128','64','32']}
 if any(a['catalogueSha256']!=digest or a['dataAdmitted'] is not True for a in maps.values()):raise ValueError('Unbound or unadmitted map')
 assets={'catalogueText':raw.decode('utf-8'),'scenes':json.loads((root/'data/cp74-scenes.json').read_text()),'maps':maps}
 script=('window.__physicalDiffuseAssets='+json.dumps(assets,separators=(',',':'),ensure_ascii=False)+';\n'+'\n'.join(parts)).replace('</script','<\\/script')
 html=(root/'demo/physical-diffuse.html').read_text();tag='<script type="module" src="./physical-diffuse.mjs"></script>'
 if html.count(tag)!=1:raise ValueError('Entry tag absent or repeated')
 html=html.replace(tag,'<script type="module">\n'+script+'\n</script>');out=root/'dist/physical-diffuse-sky-viewer.html';out.write_text(html)
 return {'path':out.relative_to(root).as_posix(),'bytes':out.stat().st_size,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'catalogueSha256':digest,'physicalComposition':True,'stage':'7.4'}
if __name__=='__main__':print(json.dumps(build(),indent=2))
