"""Verify package bytes, without changing source, storage or GitHub state."""
from pathlib import Path
import argparse
import hashlib
import json


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    args=ap.parse_args(); root=args.root.resolve()
    manifest=json.loads((root/'MANIFEST.json').read_text(encoding='utf-8'))
    failures=[]
    for row in manifest['files']:
        path=(root/row['path']).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            failures.append({'path':row['path'],'error':'missing or outside package'});continue
        data=path.read_bytes()
        if len(data)!=row['bytes'] or hashlib.sha256(data).hexdigest()!=row['sha256']:
            failures.append({'path':row['path'],'error':'byte identity mismatch'})
    print(json.dumps({'result':'FAIL' if failures else 'PASS','files':len(manifest['files']),'failures':failures}))
    raise SystemExit(bool(failures))


if __name__=='__main__':main()
