from pathlib import Path
import hashlib,importlib.util,json,shutil,sys,tempfile,zipfile
E=Path(__file__).resolve().parent;P=E/'planning-original-21e7a843/docs/rlgwo-execution/20261008'
O=E/'dag-reconciliation-r1';copy=O/'validator-copy'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sys.flags.utf8_mode,'Existing scripts require explicit UTF-8 mode on this Windows host'
(O/'REJECTED_VALIDATOR_INVOCATION.json').write_text(json.dumps({'classification':'Harness invocation, not graph failure','command':'python validate-planning.py','result':'UnicodeDecodeError: Windows cp1252 cannot decode graph UTF-8 byte 0x8f','completedChecks':['430 manifest files','213 nodes / 409 edges / 26 issues','2186 references / 219 targets'],'repair':'Run unchanged existing negative/guard scripts with Python -X utf8; retained prior output untouched.'},indent=2)+'\n',encoding='utf-8')
temp=O/'temporary-controls';assert temp.resolve().is_relative_to(O.resolve());tempfile.tempdir=str(temp)
sys.path.insert(0,str(copy/'tools'));sys.dont_write_bytecode=True
for filename,output in [('graph_negative_controls.py','DAG_NEGATIVE_CONTROLS.json'),('publication_guard_controls.py','PUBLICATION_GUARD_CONTROLS.json')]:
    s=importlib.util.spec_from_file_location(filename[:-3],copy/'tools'/filename)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);m.main()
    shutil.copyfile(copy/output,O/output)
with zipfile.ZipFile(E/'planning-21e7a843.zip') as z:
    paths={n[len('docs/rlgwo-execution/20261008/'):]:hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist() if not n.endswith('/')}
actual={p.relative_to(P).as_posix():sha(p) for p in P.rglob('*') if p.is_file()}
assert actual==paths,'Historical package differs from immutable Git archive'
(O/'PLANNING_CUSTODY.json').write_text(json.dumps({'specCommit':'21e7a84365fae37a86cae5c7d5e41008c0adc53f','tree':'1ef81e5030e6835649fa780a78dd4ec9acc9e92b','graphSha256':sha(P/'CLOSURE_DAG.json'),'archiveSha256':sha(E/'planning-21e7a843.zip'),'packageUnchanged':True,'files':actual},indent=2)+'\n',encoding='utf-8')
print('Historical package matches immutable archive; controls passed under explicit UTF-8.')
