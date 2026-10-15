"""Copy one coherent R0003 raw-evidence package to its non-deploying branch.

Large text is deterministically gzip encoded without altering decoded bytes.
Original videos are retained; decoded frame manifests permit exact reconstruction.
Only specifically reviewed frames are duplicated alongside original full videos.
"""
import argparse, gzip, hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('--runs',type=Path,required=True);a=p.parse_args();source=a.runs.resolve();out=ROOT/'evidence/R0003/browser';out.mkdir(parents=True,exist_ok=True)
    reviewed={'attempt01-chromium/R0003-prayer-late-body':[71,72,73,95,96],
      'attempt02-chromium/R0003-prayer-late-headers':[64,65,66],
      'attempt02-chromium/R0003-no-abort':[43,44,45],
      'attempt02-chromium/R0003-prayer-old-tomorrow':[49,50,51],
      'attempt04-chromium/R0003-entry-offline':[40,41,42],
      'attempt04-chromium/R0003-entry-iframe':[44,45,46],
      'attempt04-chromium/R0003-warm-ashen-below-horizon':[107],
      'attempt05-firefox/R0003-prayer-late-body':[34,67,68,69,70,71,72,75,76,77],
      'attempt06-firefox-video-only/R0003-prayer-late-body':[38,54,55,56,63,64,65,68,69,70,76,77,78,81,82,83]}
    rows=[]
    for path in sorted(source.rglob('*')):
        if not path.is_file() or path.is_symlink():continue
        rel=path.relative_to(source)
        # Abandoned desktop/window experiments stay in local custody only. They
        # are not an R0003 acceptance route or part of this public browser package.
        if not str(rel.parts[0]).startswith(('attempt','preflight','public-')):continue
        if 'frames' in rel.parts and path.name.startswith('frame-') and path.suffix=='.png':
            key='/'.join(rel.parts[:2]);number=int(path.stem.split('-')[-1])
            if number not in reviewed.get(key,[]):continue
        if path.suffix not in ('.json','.html','.png','.webm','.mkv','.jpg','.log','.txt'):continue
        raw=path.read_bytes();compressed=path.suffix in ('.json','.html','.log','.txt') and len(raw)>300000
        blob=gzip.compress(raw,compresslevel=9,mtime=0) if compressed else raw
        target=out/rel;target=target.with_name(target.name+'.gz') if compressed else target;target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists():assert target.read_bytes()==blob,('immutable packaged path changed',target)
        else:target.write_bytes(blob)
        rows.append({'path':str(target.relative_to(ROOT)).replace('\\','/'),'originalRelativePath':str(rel).replace('\\','/'),
                     'encoding':'gzip' if compressed else 'identity','bytes':len(blob),'sha256':sha(blob),'decodedBytes':len(raw),'decodedSha256':sha(raw)})
    manifest={'schema':'r0003-raw-evidence-index/v1','files':rows,'limits':'Raw driver statuses and failed recordings remain unchanged. A separate independent acceptance map controls disposition; this index does not grant PASS.'}
    (ROOT/'evidence/R0003/raw-index.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'files':len(rows),'encodedMiB':round(sum(r['bytes'] for r in rows)/1048576,2),'decodedMiB':round(sum(r['decodedBytes'] for r in rows)/1048576,2)}))
if __name__=='__main__':main()
