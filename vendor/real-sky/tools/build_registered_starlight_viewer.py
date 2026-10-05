#!/usr/bin/env python3
"""Bundle the corrected real V-component and its registration viewer, entirely offline."""
from pathlib import Path
import json,re,hashlib
R=Path(__file__).resolve().parents[1]
def build(root=R):
    names=['src/time-scales.mjs','src/astronomy.mjs','src/projection.mjs','src/diffuse-map.mjs','src/registered-starlight.mjs','demo/registered-starlight.mjs'];parts=[]
    for name in names:
        text=(root/name).read_text();text=re.sub(r'^import .*?;\s*$','',text,flags=re.M);text=re.sub(r'\bexport\s+(?=(?:async\s+)?(?:const|function|class)\b)','',text)
        if re.search(r'^\s*(?:import|export)\s',text,re.M):raise ValueError('Unsupported bundler syntax '+name)
        parts.append('// '+name+'\n'+text)
    assets={'catalogue':json.loads((root/'data/bright-stars.json').read_text()),'report':json.loads((root/'checkpoints/cp7_completion/asset-build.json').read_text()),'maps':{tier:json.loads((root/f'data/registered-starlight/V-nside{tier}.json').read_text()) for tier in ['128','64','32']}}
    if any(a.get('dataAdmitted') is not True for a in assets['maps'].values()):raise ValueError('Unadmitted source map')
    js='window.__registeredAssets='+json.dumps(assets,separators=(',',':'),ensure_ascii=False)+';\n'+'\n'.join(parts);js=js.replace('</script','<\\/script')
    html=(root/'demo/registered-starlight.html').read_text();tag='<script type="module" src="./registered-starlight.mjs"></script>'
    if html.count(tag)!=1:raise ValueError('Diagnostic entry tag missing or duplicated')
    html=html.replace(tag,'<script type="module">\n'+js+'\n</script>');out=root/'dist/registered-starlight-viewer.html';out.write_text(html)
    return {'path':'dist/registered-starlight-viewer.html','bytes':out.stat().st_size,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'diagnosticOnly':True,'sourceComponentAdmitted':True,'physicalComposition':False}
if __name__=='__main__':print(json.dumps(build(),indent=2))
