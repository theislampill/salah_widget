"""Lossless publication of this issue's evidence; raw local originals are retained."""
import argparse, gzip, hashlib, json, subprocess, tempfile
from pathlib import Path

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[1]
MANIFEST=BASE/'publication/payload-manifest.json'

def sha(data):return hashlib.sha256(data).hexdigest()

def main():
    p=argparse.ArgumentParser();p.add_argument('--stage',action='store_true');args=p.parse_args()
    branch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()
    if branch!='codex/r000d-closure-evidence-20261014':raise RuntimeError('Wrong evidence branch')
    rows=[];paths=[]
    for src in sorted(BASE.rglob('*')):
        if not src.is_file() or '__pycache__' in src.parts or src==MANIFEST or src.suffix=='.gz':continue
        # Readback is a later additive publication receipt, not part of its own payload.
        if src.parent==BASE/'publication' and src.name!='README.md':continue
        data=src.read_bytes();published=src;encoding='identity'
        if src.suffix=='.json' and len(data)>1_000_000:
            published=src.with_name(src.name+'.gz');compressed=gzip.compress(data,compresslevel=9,mtime=0)
            if published.exists() and published.read_bytes()!=compressed:raise RuntimeError('Sealed raw evidence changed: '+str(src))
            if not published.exists():published.write_bytes(compressed)
            if gzip.decompress(published.read_bytes())!=data:raise RuntimeError('Lossless custody failed')
            encoding='gzip'
        delivered=published.read_bytes()
        if len(delivered)>=90_000_000:raise RuntimeError('Unexpected oversized publication object: '+str(published))
        rows.append({'original':src.relative_to(BASE).as_posix(),'originalBytes':len(data),'originalSha256':sha(data),
                     'published':published.relative_to(BASE).as_posix(),'publishedBytes':len(delivered),'publishedSha256':sha(delivered),'encoding':encoding})
        paths.append(published.relative_to(ROOT).as_posix())
    manifest={'schema':'r000d-evidence-custody/v1','scope':'Issue evidence only on a non-deploying branch. Gzip decompresses to exact original bytes; originals remain locally retained.',
              'fileCount':len(rows),'originalBytes':sum(x['originalBytes']for x in rows),'publishedBytes':sum(x['publishedBytes']for x in rows),'files':rows}
    MANIFEST.parent.mkdir(parents=True,exist_ok=True);MANIFEST.write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    paths.append(MANIFEST.relative_to(ROOT).as_posix())
    if args.stage:
        with tempfile.NamedTemporaryFile(prefix='r000d-pathspec-',suffix='.bin',delete=False)as f:
            f.write(b'\0'.join(x.encode()for x in paths)+b'\0');pathspec=f.name
        subprocess.run(['git','add','--pathspec-from-file='+pathspec,'--pathspec-file-nul'],cwd=ROOT,check=True)
    print(json.dumps({k:v for k,v in manifest.items()if k!='files'}))

if __name__=='__main__':main()
