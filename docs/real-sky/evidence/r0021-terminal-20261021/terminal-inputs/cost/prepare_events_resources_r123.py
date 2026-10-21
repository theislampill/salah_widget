"""Prepare reversible observer overlays using the existing v5 AST/marker method."""
from pathlib import Path
import hashlib,json,subprocess
C=Path(__file__).resolve().parent;O=C.parent
old=(C/'instrument-v5-r74.cjs').read_text()
s=old.replace("B:'integrated-r20'","B:'integrated-r30-owner-callbacks'").replace("'instrumented-v5-r74'","'instrumented-r123'")
s=s.replace("const edits=[],roles=[],owners=[];","const edits=[],roles=[],owners=[],fnNames=new WeakMap();")
s=s.replace("const fn=/Function/.test(node.type),name=node.id?.name||'',chain=ancestors.map(a=>a.id?.name||'<anon>');","const fn=/Function/.test(node.type),name=node.id?.name||(parent?.type==='MethodDefinition'?parent.key?.name:'')||'',chain=ancestors.map(a=>a.id?.name||fnNames.get(a)||'<anon>');if(fn)fnNames.set(node,name);")
s=s.replace("fn?[...ancestors,node]:ancestors","(fn||node.type==='ClassDeclaration')?[...ancestors,node]:ancestors")
s=s.replace("['paint','update','present','tick'].includes(name)","['paint','update','present','tick','prepareForeground','publishPreview','rejectPreview','paintFailed'].includes(name)")
s=s.replace("['compose','accept','animate'].includes(name)","['compose','accept','animate','publishComposition','rejectComposition','compositionFailed'].includes(name)")
marker="   if(role){"
addition="""   if(chain.includes('NativeForegroundCapture')&&['capture','prepareSolarMask'].includes(name))role='foreground.'+name;
   if(chain.includes('NativeSolarMaskPublication')&&['publish','finish','cancel','dispose'].includes(name))role='mask.'+name;
   if(chain.includes('NativeSolarMaskPublication')&&chain.includes('publish')&&!name)role=node.params.length?'mask.decodeRejected':'mask.decodeFulfilled';
   if(chain.includes('NativeSolarMaskPublication')&&name==='constructor')insert(node.body.end-1,';window.__r21Resources.register(this);');
   if(chain.includes('NativeSolarMaskPublication')&&chain.includes('publish')&&!name&&node.params.length&&node.body.type==='BlockStatement')insert(bodyStart(node),';window.__r21Resources.reaction(this,revision,"rejected");');
"""
assert marker in s;s=s.replace(marker,addition+marker)
s=s.replace("'foreground','canvas','disposed','animationId'","'foreground','canvas','disposed','animationId','solarPublication'")
s=s.replace("}else if(vars.has('upperBytes')", "}else if(name==='startNativeSkyPreview'){\n    owner='preview';fields=['solarPublication','foreground','canvas','disposed','value','pendingValue','previewFrame','baseBytes','catalogueRevision'];\n   }else if(vars.has('upperBytes')")
p=C/'instrument-r123.cjs';assert not p.exists();p.write_text(s,encoding='utf-8',newline='\n')
probe=(C/'probe-v5.js').read_text();assert 'registerOwner:(name,read)' in probe
probe=probe.replace('registerOwner:(name,read)','readOwner:name=>owners.get(name)?.at(-1)?.read(),registerOwner:(name,read)')
(C/'probe-r123.js').write_text(probe,encoding='utf-8',newline='\n')
node=r'${TOOL_CACHE}\OpenJS.NodeJS.LTS_Microsoft.Winget.Source_8wekyb3d8bbwe\node-v24.15.0-win-x64\node.exe'
result=subprocess.run([node,str(p)],capture_output=True,text=True);(C/'prepare-r123.log').write_text(result.stdout+result.stderr,encoding='utf-8');assert result.returncode==0,result.stderr
for name in ['probe-r123.js','resource-controls-r123.js']:
 result=subprocess.run([node,'--check',str(C/name)],capture_output=True,text=True);assert result.returncode==0,result.stderr
m=json.loads((C/'instrumented-r123/SOURCE-MAP.json').read_bytes())
print(json.dumps({'roundTrip':all(part['roundTrip'] for side in m['sides'].values() for f in side['files'].values() for part in f['parts']),'roles':{side:sorted({r['role'] for f in rec['files'].values() for part in f['parts'] for r in part['roles']}) for side,rec in m['sides'].items()},'owners':{side:[o for f in rec['files'].values() for part in f['parts'] for o in part['owners']] for side,rec in m['sides'].items()}}))
