"""Create a fresh r5 fork; add only exact final-source/runtime admission."""
from pathlib import Path
import hashlib,json
HERE=Path(__file__).resolve().parent
BASE=HERE.parent/'font-driver-r4'
binding=json.loads((HERE/'SOURCE_BINDING.json').read_text(encoding='utf-8'))
seal=json.loads((BASE/'SEAL.json').read_text(encoding='utf-8'))
def sha(data):return hashlib.sha256(data).hexdigest()
for name,identity in seal['files'].items():assert sha((BASE/name).read_bytes())==identity['sha256']
source=binding['sources']['04']
profile={'sourceSha256':source['indexSha256'],'runtimeTreeSha256':source['runtimeTreeSha256'],'nativeOrdinal':source['nativeOrdinal'],
    'scripts':[[r['attrs'],r['sha256'],r['bootCount']] for r in source['scripts']]}
target_names=list(seal['files']);assert all(not (HERE/name).exists() for name in target_names),'Fresh r5 only; preserve any prior outcome'
original=(BASE/'rlgwo-clock-date-fixture.cjs').read_text(encoding='utf-8')
anchor='\n};\nfunction strictNativeRuntime(source){';assert original.count(anchor)==1
updated=original.replace(anchor,',\n  combined_r1r2_04:'+json.dumps(profile,separators=(',',':'))+anchor)
line=next(line for line in original.splitlines() if line.startswith('  const layoutId=split?'))
updated=updated.replace(line,"  const final04=all[2]&&all[2][1]===SCRIPT_LAYOUTS.combined_r1r2_04.scripts[2][0]&&sha(all[2][2])===SCRIPT_LAYOUTS.combined_r1r2_04.scripts[2][1];\n"+line.replace('const layoutId=split?','const layoutId=final04?\'combined_r1r2_04\':split?'))
runtime_anchor='    p.runtimePaths=Object.keys(runtimeIdentity.files).sort();p.runtimeTreeSha256=runtimeIdentity.treeSha256;';assert updated.count(runtime_anchor)==1
guard="""    if(admission.layoutId==='combined_r1r2_04'){
      const expected=SCRIPT_LAYOUTS.combined_r1r2_04.runtimeTreeSha256,files=runtimeIdentity.files;
      const canonical=Object.keys(files).sort().map(name=>files[name].sha256+'  '+name+'\\n').join('');
      if(runtimeIdentity.treeSha256!==expected||sha(canonical)!==expected)throw Error('Final04 exact runtime tree admission drift');
    }
"""
updated=updated.replace(runtime_anchor,guard+runtime_anchor)
for name in target_names:
    if name=='rlgwo-clock-date-fixture.cjs':(HERE/name).write_text(updated,encoding='utf-8',newline='\n')
    else:(HERE/name).write_bytes((BASE/name).read_bytes())
changes={'schema':'font-driver-r5-fork/1','base':str(BASE),'baseSealSha256':sha((BASE/'SEAL.json').read_bytes()),
    'changes':['Add exact final04 whole generated entry and all six ordered script identities.','Select final04 by its known Moon initial role/body digest, then retain every count/role/body/boot/whole-source guard.','For final04 font admission, bind expected canonical runtime tree; reject changed inventory claims.'],
    'unchanged':['All four Python driver/wrapper bytes','plan/record/pre-script clock/storage/providers/observer hooks','Actual font policies, CSS parsing, byte releases, natural repeated fit calls, screenshots and explicit control boundaries'],
    'files':{name:{'bytes':(HERE/name).stat().st_size,'sha256':sha((HERE/name).read_bytes()),'baseSha256':seal['files'][name]['sha256']} for name in target_names}}
(HERE/'CHANGES.json').write_text(json.dumps(changes,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':'FORKED_NOT_EXECUTED','sourceSha256':source['indexSha256'],'runtimeTreeSha256':source['runtimeTreeSha256'],'changes':changes['changes']}))
