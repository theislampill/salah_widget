from pathlib import Path
import importlib.util,json,hashlib,subprocess,sys,shutil,tempfile
E=Path(__file__).resolve().parent
P=E/'planning-original-21e7a843/docs/rlgwo-execution/20261008'
O=E/'dag-reconciliation-r1';O.mkdir(exist_ok=True)
W=Path(r'C:\Users\theis\.codex\worktrees\celestial-startup-repair\salah_widget')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before={p.relative_to(P).as_posix():sha(p) for p in P.rglob('*') if p.is_file()}
commands=[('manifest',[sys.executable,str(P/'tools/verify_manifest.py'),'--root',str(P)]),
 ('graph',[sys.executable,str(P/'tools/validate_execution_plan.py'),'--root',str(P),'--output',str(O/'DAG_VALIDATION.json')]),
 ('references',[sys.executable,str(P/'tools/verify_references.py'),'--root',str(P),'--repository',str(W),'--output',str(O/'REFERENCE_VALIDATION.json')])]
for name,args in commands:
    r=subprocess.run(args,capture_output=True,cwd=W)
    (O/(name+'.log')).write_bytes(r.stdout+r.stderr)
    assert r.returncode==0,(name,r.stderr.decode(errors='replace'))
    print(name+': '+r.stdout.decode()[:500],flush=True)
# Existing mutation scripts publish into their own ROOT. Use a disposable copy,
# never the historical package. Its temp cleanup is confined to this owned area.
copy=O/'validator-copy';assert not copy.exists()
shutil.copytree(P,copy)
temp=O/'temporary-controls';temp.mkdir(exist_ok=True);assert temp.resolve().is_relative_to(O.resolve())
tempfile.tempdir=str(temp.resolve())
sys.path.insert(0,str(copy/'tools'));sys.dont_write_bytecode=True
for filename,output in [('graph_negative_controls.py','DAG_NEGATIVE_CONTROLS.json'),('publication_guard_controls.py','PUBLICATION_GUARD_CONTROLS.json')]:
    s=importlib.util.spec_from_file_location(filename[:-3],copy/'tools'/filename)
    module=importlib.util.module_from_spec(s);s.loader.exec_module(module);module.main()
    shutil.copyfile(copy/output,O/output)
after={p.relative_to(P).as_posix():sha(p) for p in P.rglob('*') if p.is_file()}
assert before==after,'Historical planning package changed'
(O/'PLANNING_CUSTODY.json').write_text(json.dumps({'specCommit':'21e7a84365fae37a86cae5c7d5e41008c0adc53f','tree':'1ef81e5030e6835649fa780a78dd4ec9acc9e92b','graphSha256':sha(P/'CLOSURE_DAG.json'),'archiveSha256':sha(E/'planning-21e7a843.zip'),'packageUnchanged':True,'files':before},indent=2)+'\n')
print('Historical package untouched; all supplied structural/negative/guard/reference checks passed.',flush=True)
