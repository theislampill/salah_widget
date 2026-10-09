"""Manifest a complete staged planning package; no product/GitHub effects."""
from pathlib import Path
import argparse
import hashlib
import json


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);args=ap.parse_args();root=args.root.resolve()
    files=[]
    for p in sorted(root.rglob('*')):
        if not p.is_file() or p.name in {'MANIFEST.json','MANIFEST.sha256'} or '__pycache__' in p.parts:continue
        b=p.read_bytes();files.append({'path':p.relative_to(root).as_posix(),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
    m={'schemaVersion':1,'package':'Salah remaining RLGWO execution specifications','packageRevision':1,
       'sourceTarget':'18ff14860ff41c084b1db5f396bb62aa9c22b1be','auditEvidenceCommit':'b879573c298f19189d1f2392108b8b9f3b2cda0b',
       'runtimeSha256':'f443cf0820e6879dfa7c3ce857d6b2baf554b1fdd2f889433d22e2c532cec260',
       'specificationCommit':'Bind to immutable containing Git commit selected as SPEC_SHA; no recursive self-SHA.',
       'scope':'Documents/planning only. Runtime, original contracts, accepted closures and V1 untouched. Future runtime/test/merge/closure results are not implied.',
       'excludes':['MANIFEST.json','MANIFEST.sha256','__pycache__/'],'files':files}
    data=(json.dumps(m,indent=2)+'\n').encode();(root/'MANIFEST.json').write_bytes(data)
    (root/'MANIFEST.sha256').write_text(hashlib.sha256(data).hexdigest()+'  MANIFEST.json\n')
    print(json.dumps({'files':len(files),'bytes':sum(f['bytes'] for f in files),'manifestSha256':hashlib.sha256(data).hexdigest()}))


if __name__=='__main__':main()
