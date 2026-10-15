"""Additive immutable publication; retain raw JSON locally and publish lossless gzip."""
from pathlib import Path
import gzip, hashlib, json, re
ROOT=Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()

def main():
    target=ROOT/'publication-manifest.json'
    assert not target.exists(),'Retain frozen publication; do not reseal'
    files=[p for p in sorted(ROOT.rglob('*')) if p.is_file()]
    originals=[];rows=[];scanned=[]
    for p in files:
        rel=p.relative_to(ROOT).as_posix();raw=p.read_bytes();published=rel;wire=raw;encoding='identity'
        if p.suffix in ('.py','.cjs','.json','.md'):
            text=raw.decode('utf-8')
            assert not re.search(r'gh[pousr]_[A-Za-z0-9]{25,}|github_pat_[A-Za-z0-9_]{25,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',text),rel
            scanned.append(rel)
        if p.suffix=='.json' and len(raw)>1000000:
            published=rel+'.gz';dest=ROOT/published;assert not dest.exists()
            wire=gzip.compress(raw,mtime=0);dest.write_bytes(wire);assert gzip.decompress(wire)==raw
            encoding='gzip';originals.append('/'+rel)
        rows.append({'original':rel,'published':published,'originalBytes':len(raw),'originalSha256':sha(raw),'publishedBytes':len(wire),'publishedSha256':sha(wire),'encoding':encoding})
    ignore=ROOT/'.gitignore';assert not ignore.exists()
    data=('# Exact large raw receipts remain local; their lossless gzip is published.\n'+'\n'.join(originals)+'\n').encode();ignore.write_bytes(data)
    rows.append({'original':'.gitignore','published':'.gitignore','originalBytes':len(data),'originalSha256':sha(data),'publishedBytes':len(data),'publishedSha256':sha(data),'encoding':'identity'})
    result={'schema':'r0018-additive-delivery-publication/v1','coreEvidenceCommit':'698462f7a3ab69a5ac59ee4c1e61016ca56bb569',
            'reviewPublicationCommit':'eb0bbe44334f427ca6f7cf3917d27086356d6a39','mergeCommit':'ae24fec477eba0280ea513ad57b3947a4c66dda0',
            'scope':'Only additive postmerge evidence. Original packet, failures and public review remain immutable. This manifest excludes itself; later certificate and final readback are additive.',
            'credentialPatternScan':{'files':len(scanned),'matches':[],'scope':'Known credential/private-key format scan plus executor review of fixed synthetic request data; not a universal privacy guarantee.'},'files':rows}
    target.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({'files':len(rows),'largeJsonGzip':len(originals),'publishedBytes':sum(r['publishedBytes'] for r in rows),'manifestSha256':sha(target.read_bytes())}))

if __name__=='__main__':main()
