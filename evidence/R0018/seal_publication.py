"""R000D's lossless publication pattern, scoped to this issue's evidence branch."""
import argparse,gzip,hashlib,json,subprocess,tempfile
from pathlib import Path

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[1]
MANIFEST=BASE/'publication/payload-manifest.json'
def sha(data):return hashlib.sha256(data).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('--stage',action='store_true');a=p.parse_args()
    branch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()
    if branch!='codex/r0018-closure-evidence-20261015':raise RuntimeError('Wrong evidence branch')
    large=[source.relative_to(BASE).as_posix() for source in sorted(BASE.rglob('*.json')) if source!=MANIFEST and source.stat().st_size>1_000_000 and source.parent!=BASE/'publication']
    (BASE/'.gitignore').write_text('# Exact raw originals remain local; lossless .gz counterparts are published.\n'+''.join('/'+p+'\n' for p in large),encoding='utf-8')
    rows=[];paths=[]
    for source in sorted(BASE.rglob('*')):
        if not source.is_file() or '__pycache__' in source.parts or source==MANIFEST or source.suffix=='.gz':continue
        if source.parent==BASE/'publication' and source.name!='README.md':continue
        data=source.read_bytes();published=source;encoding='identity'
        if source.suffix=='.json' and len(data)>1_000_000:
            published=source.with_name(source.name+'.gz');compressed=gzip.compress(data,compresslevel=9,mtime=0)
            if published.exists() and published.read_bytes()!=compressed:raise RuntimeError('Sealed evidence changed: '+str(source))
            if not published.exists():published.write_bytes(compressed)
            if gzip.decompress(published.read_bytes())!=data:raise RuntimeError('Lossless custody failed')
            encoding='gzip'
        body=published.read_bytes()
        if len(body)>=90_000_000:raise RuntimeError('Oversized publication object')
        rows.append({'original':source.relative_to(BASE).as_posix(),'originalBytes':len(data),'originalSha256':sha(data),'published':published.relative_to(BASE).as_posix(),'publishedBytes':len(body),'publishedSha256':sha(body),'encoding':encoding})
        paths.append(published.relative_to(ROOT).as_posix())
    value={'schema':'r0018-evidence-custody/v1','scope':'Non-deploying issue evidence. Original raw failures and all raw observations retained; compression is lossless.','fileCount':len(rows),'originalBytes':sum(r['originalBytes'] for r in rows),'publishedBytes':sum(r['publishedBytes'] for r in rows),'files':rows}
    MANIFEST.parent.mkdir(parents=True,exist_ok=True);MANIFEST.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8');paths.append(MANIFEST.relative_to(ROOT).as_posix())
    if a.stage:
        with tempfile.NamedTemporaryFile(prefix='r0018-pathspec-',suffix='.bin',delete=False) as f:
            f.write(b'\0'.join(x.encode() for x in paths)+b'\0');pathspec=f.name
        subprocess.run(['git','add','--pathspec-from-file='+pathspec,'--pathspec-file-nul'],cwd=ROOT,check=True)
    print(json.dumps({k:v for k,v in value.items() if k!='files'}))
if __name__=='__main__':main()
