"""Read-only final decoder candidate binding, after root's PASS build receipt."""
from pathlib import Path
import hashlib,importlib.util,json,re
HERE=Path(__file__).resolve().parent
RUN=HERE.parents[2]
ROOTS={name:RUN/'candidates'/('pr43-r1r2-'+name) for name in ['02','03','04']}
RECEIPT=RUN/'evidence/PR43-review/pr43-r1r2-04/build/receipt.json'
def sha(data):return hashlib.sha256(data).hexdigest()
def write(name,value):(HERE/name).write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
receipt=json.loads(RECEIPT.read_text(encoding='utf-8'))
assert receipt['status']=='PASS_DETERMINISTIC_BUILD_AND_V1' and receipt['sourceUnchanged'] is True
assert Path(receipt['candidate']).resolve()==ROOTS['04'].resolve()
tool=ROOTS['04']/'tools/cp9/runtime_identity.py'
spec=importlib.util.spec_from_file_location('font04_identity',tool);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
rows={};inventories={};native={};styles={};font_owners={}
for name,root in ROOTS.items():
    data=(root/'index.html').read_bytes();text=data.decode('utf-8');scripts=list(re.finditer(r'<script\b([^>]*)>([\s\S]*?)</script>',text))
    scripts_meta=[{'ordinal':i,'attrs':m[1],'bytes':len(m[2].encode()),'sha256':sha(m[2].encode()),'bootCount':m[2].count('\nboot();')} for i,m in enumerate(scripts)]
    owners=[r['ordinal'] for r in scripts_meta if r['bootCount']];assert len(owners)==1 and scripts_meta[owners[0]]['bootCount']==1
    native[name]=scripts[owners[0]][2]
    css=[{'ordinal':i,'attrs':m[1],'sha256':sha(m[2].encode()),'bytes':len(m[2].encode())} for i,m in enumerate(re.finditer(r'<style\b([^>]*)>([\s\S]*?)</style>',text))]
    styles[name]=css
    start=re.search(r'\blet _cnFit\s*=',native[name]);assert start
    end=native[name].find('\nlet _lastBolt',start.start());assert end>start.start()
    font_owners[name]=native[name][start.start():end]
    inventory=module.runtime_identity(root);inventories[name]=inventory
    rows[name]={'root':str(root),'indexSha256':sha(data),'indexBytes':len(data),'runtimeTreeSha256':inventory['treeSha256'],'scripts':scripts_meta,'nativeOrdinal':owners[0],'nativeSourceSha256':sha((root/'src/native/index.html').read_bytes()),'nativeCoreSha256':sha(native[name].encode()),'css':css,'fontOwnerBoundary':'let _cnFit through before let _lastBolt (including actual font watchers/fitCn; no source substitution)','fontOwnerSha256':sha(font_owners[name].encode()),'fontOwnerBytes':len(font_owners[name].encode())}
assert rows['04']['indexSha256']==receipt['indexSha256'] and inventories['04']['treeSha256']==receipt['runtimeSha256']
assert native['03']==native['04'],'Native core changed beyond declared decoder follow-up'
assert rows['03']['nativeSourceSha256']==rows['04']['nativeSourceSha256']=='a81b32b46d1153c2cc41f57f6e615f1237a4491774ad383820a18a903013bfcf'
assert styles['03']==styles['04'],'CSS changed beyond declared decoder follow-up'
assert font_owners['03']==font_owners['04'],'Font owner changed'
assert font_owners['02']==font_owners['04'],'Font owner differs from candidate02 font matrix'
binary={}
for name in ['03','04']:
    root=ROOTS[name];binary[name]={p:{'bytes':(root/p).stat().st_size,'sha256':sha((root/p).read_bytes())} for p in ['moon/assets/initial-compact.bin','moon/assets/initial-receivers.bin','moon/initial-compact-manifest.json','moon/initial-manifest.json']}
assert binary['03']==binary['04'],'Encoded/parent receiver or manifest bytes changed'
decoder={name:{'path':str(ROOTS[name]/'moon/src/moon-initial-compact.mjs'),'sha256':sha((ROOTS[name]/'moon/src/moon-initial-compact.mjs').read_bytes())} for name in ['03','04']}
assert decoder['03']['sha256']!=decoder['04']['sha256']
integration_path=RUN/'evidence/PR43-review/R1-decoder-integration-01/receipt.json'
integration=json.loads(integration_path.read_text(encoding='utf-8'))
assert integration['status']=='INTEGRATED_EXACT_DECODER_11_TESTS_PASS' and integration['exit']==0
assert integration['beforeSha256']==decoder['03']['sha256'] and integration['afterSha256']==decoder['04']['sha256']
compact_manifest=json.loads((ROOTS['04']/'moon/initial-compact-manifest.json').read_text(encoding='utf-8'))
assert compact_manifest['sha256']==binary['04']['moon/assets/initial-compact.bin']['sha256']
assert compact_manifest['decodedSha256']=='25755b217ec6da7401740b3d4df06d23c917e4bfc447d5667938b7b960a69331'
changed=[p for p in sorted(set(inventories['03']['files'])|set(inventories['04']['files'])) if inventories['03']['files'].get(p)!=inventories['04']['files'].get(p)]
script_changes=[i for i,(old,new) in enumerate(zip(rows['03']['scripts'],rows['04']['scripts'])) if old!=new]
assert len(rows['03']['scripts'])==len(rows['04']['scripts'])==6
assert script_changes==[2],'Unexpected ordered script changes beyond Moon initial decoder'
binding={'schema':'clock-date-font04-source-binding/1','status':'ACQUIRED_AFTER_ROOT_PASS_BUILD','workerNativeLaunches':0,'rootBuildReceipt':str(RECEIPT),'rootBuildReceiptSha256':sha(RECEIPT.read_bytes()),'rootBuildStatus':receipt['status'],'runtimeIdentityTool':str(tool),'runtimeIdentityToolSha256':sha(tool.read_bytes()),'sources':rows,'unchanged':{'nativeSource03to04':True,'nativeCore03to04':True,'css03to04':True,'fontOwner03to04':True,'fontOwner02to04':True,'receiverAndManifestBytes03to04':True},'decoder':decoder,'receiverBytes':binary,'compactManifest':compact_manifest,'rootDecoderIntegration':{'path':str(integration_path),'sha256':sha(integration_path.read_bytes()),'status':integration['status'],'decodedScope':'Encoded/manifest bytes read equal here; decoded byte identity supported by root retained eleven codec controls at exact after-decoder identity, not a new worker decoder execution.'},'changedRuntimeFiles03to04':changed,'changedOrderedScriptOrdinals03to04':script_changes,'limits':['Candidate03 current source/runtime bytes equal candidate02; exact reference acquired here rather than inferred from folder names.','Actual font/native qualification remains root-owned; no browser or timing measurement here.']}
write('SOURCE_BINDING.json',binding);write('runtime-identity.json',inventories['04'])
print(json.dumps({'status':binding['status'],'sources':rows,'decoder':decoder,'changedRuntimeFiles03to04':changed,'changedOrderedScriptOrdinals03to04':script_changes,'unchanged':binding['unchanged']},indent=2))
