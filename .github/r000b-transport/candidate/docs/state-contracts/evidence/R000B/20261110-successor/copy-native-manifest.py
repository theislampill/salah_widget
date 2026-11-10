from pathlib import Path
import hashlib,json,subprocess
r=Path('/workspace/scratch/15b8fb6ac4c2/r000b-work');e=Path('/workspace/scratch/d9a9ea2be931/recovery');a=json.loads((e/'native-manifest-preflight.json').read_text());h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip()==a['head']
assert h(r/a['target'])==a['preimageSha256']
assert h(r/'src/native/index.html')==a['sourceSha256']
s=e/'r000b-native-candidate-f02.json';assert h(s)==a['outputSha256']
(r/a['target']).write_bytes(s.read_bytes());assert h(r/a['target'])==a['outputSha256']
print(json.dumps(a))
