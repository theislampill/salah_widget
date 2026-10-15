"""Identity of the actual served candidate, independent of historical CP9 seals."""
from pathlib import Path
import hashlib,json

ROOT=Path(__file__).resolve().parents[2]
def runtime_identity(root=ROOT):
    root=Path(root).resolve()
    paths=[root/p for p in ['index.html','offline.html','config.js','builder.html']]
    paths+=sorted(p for p in (root/'real-sky').rglob('*') if p.is_file())
    # HTTP/file delivery also consumes the Moon worker, kernel and local assets.
    # Its tests and authored source are inventoried separately from runtime.
    paths+=sorted(p for p in (root/'moon').rglob('*') if p.is_file()
                  and p.relative_to(root/'moon').parts[0] not in {'src','tests'})
    files={p.relative_to(root).as_posix():{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(paths)}
    canonical=''.join(f"{v['sha256']}  {p}\n" for p,v in sorted(files.items()))
    return {'schemaVersion':1,'treeSha256':hashlib.sha256(canonical.encode()).hexdigest(),'algorithm':'SHA256 of sorted <sha256><two spaces><relative POSIX path><LF> records','files':files}

if __name__=='__main__':print(json.dumps(runtime_identity(),indent=2))
