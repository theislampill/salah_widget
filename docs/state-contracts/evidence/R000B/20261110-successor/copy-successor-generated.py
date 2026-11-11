from pathlib import Path
import hashlib,json,os,shutil,subprocess,sys
r=Path('/workspace/scratch/15b8fb6ac4c2/r000b-work')
e=Path('/workspace/scratch/d9a9ea2be931/recovery')
a=json.loads((e/'generated-copy-preflight.json').read_text())
p=sys.argv[1]
assert p in a['writeSet']
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip()==a['expectedHead']
h=lambda q:hashlib.sha256(q.read_bytes()).hexdigest()
assert h(r/'src/native/index.html')==a['sourceSha256']
assert h(r/p)==a['preimages'][p], 'Preimage changed'
s=Path('/tmp/r000b-successor-build-preserved')/p
assert h(s)==a['outputs'][p]['sha256']
t=(r/p).with_name((r/p).name+'.r000b-copy.tmp')
assert not t.exists()
shutil.copyfile(s,t);shutil.copymode(r/p,t)
assert h(t)==a['outputs'][p]['sha256']
os.replace(t,r/p)
assert h(r/p)==a['outputs'][p]['sha256']
print(json.dumps({'path':p,'sha256':h(r/p),'bytes':(r/p).stat().st_size,'status':'complete canonical copy verified'}))
