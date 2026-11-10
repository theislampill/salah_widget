from pathlib import Path
import subprocess,hashlib,json,time

repo=Path('/workspace/scratch/15b8fb6ac4c2/r000b-work')
build=Path('/workspace/scratch/d9a9ea2be931/r000b-build-successor')
out=Path('/workspace/scratch/d9a9ea2be931/recovery/build-successor')
out.mkdir(exist_ok=False)
sha=lambda b:hashlib.sha256(b).hexdigest()
source=repo/'src/native/index.html'
assert sha(source.read_bytes())=='fe0ec24a6f26839ec6439c172a3b098bebd03388b3f7b0385cead0febecf4327'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=build,text=True).strip()=='d124f050ec68fa8608022b1ed5fead426d42dcb9'
assert sha((build/'src/native/index.html').read_bytes())=='b17801b33cc99c95710b916016dfd542eddce304145b493c0adecc4c3412e37f'
(build/'src/native/index.html').write_bytes(source.read_bytes())
rows=[]
for name,cmd in [('canonical-build',['python','tools/build_native.py']),('frozen-v1',['python','tools/verify_v1.py']),('protected',['git','diff','--exit-code','--','v1','vendor'])]:
 start=time.time()
 with (out/(name+'.log')).open('wb') as f:r=subprocess.run(cmd,cwd=build,stdout=f,stderr=subprocess.STDOUT)
 rows.append({'name':name,'command':cmd,'exit':r.returncode,'seconds':time.time()-start,'log_sha256':sha((out/(name+'.log')).read_bytes())})
 (out/'commands.json').write_text(json.dumps(rows,indent=2)+'\n')
 print(json.dumps(rows[-1]),flush=True)
 if r.returncode:raise SystemExit(r.returncode)
names=['index.html','offline.html','real-sky/native-sky.js','moon/BUILD.json']
outputs={n:{'bytes':(build/n).stat().st_size,'sha256':sha((build/n).read_bytes()),'gitBlob':subprocess.check_output(['git','hash-object',n],cwd=build,text=True).strip()} for n in names}
(out/'outputs.json').write_text(json.dumps(outputs,indent=2)+'\n')
status=subprocess.check_output(['git','status','--porcelain=v1'],cwd=build,text=True)
(out/'status.txt').write_text(status)
assert set(l[3:] for l in status.splitlines())=={'src/native/index.html','index.html','offline.html','moon/BUILD.json'}
print(json.dumps({'generated':outputs,'only_expected_paths':True}),flush=True)
