#!/usr/bin/env python3
"""Seal CP7 stage snapshots with explicit scientific status and fresh byte/test verification.
Archives contain source and evidence, never toolchains/font files or the parent ZIP itself.
"""
from __future__ import annotations
import argparse,hashlib,json,re,subprocess,sys,tempfile,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def files(root):
    return sorted(p for p in root.rglob('*') if p.is_file() and not any(s in p.parts for s in ['.git','__pycache__','node_modules']) and p.name!='MANIFEST.sha256' and p.name!='hygdata_v40.csv' and p.suffix.lower() not in ['.ttf','.otf','.woff','.woff2'])
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('stage',choices=['7_1','7_2','7_3']);ap.add_argument('--root',type=Path,default=ROOT);ap.add_argument('--out',type=Path,default=Path('/mnt/data'));a=ap.parse_args();root=a.root.resolve()
    progress=a.out/f'Salah_Real_Sky_Checkpoint_{a.stage}_seal-progress.log'
    def note(text):
        with progress.open('a') as f:f.write(text+'\n')
    note('START')
    status=json.loads((root/'checkpoints'/('cp'+a.stage)/'status.json').read_text())
    listed=files(root);(root/'MANIFEST.sha256').write_text(''.join(digest(p)+'  '+p.relative_to(root).as_posix()+'\n' for p in listed));listed.append(root/'MANIFEST.sha256')
    out=a.out/f'Salah_Real_Sky_Checkpoint_{a.stage}.zip';out.parent.mkdir(parents=True,exist_ok=True)
    # Do not overwrite a previously sealed checkpoint. Parent linkage uses immutable ZIP hashes.
    if out.exists():raise FileExistsError(str(out)+' already sealed; inspect/remove only this attempted output explicitly')
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(listed):
            zi=zipfile.ZipInfo('salah-real-sky/'+p.relative_to(root).as_posix(),(2026,10,4,0,0,0));zi.external_attr=0o100644<<16;zi.compress_type=zipfile.ZIP_DEFLATED;z.writestr(zi,p.read_bytes())
    note('ZIP_WRITTEN')
    receipt={'stage':a.stage.replace('_','.'),'stageStatus':status['stageStatus'],'checkpoint7Status':'OPEN','scienceSourceGate':'BLOCKED','archive':out.name,'bytes':out.stat().st_size,'sha256':digest(out),'manifestMembers':len(listed)-1,'githubWrites':0,'tests':{},'verification':{}}
    with tempfile.TemporaryDirectory(prefix='cp7-fresh-') as d:
        with zipfile.ZipFile(out) as z:
            if z.testzip() is not None:raise RuntimeError('CRC mismatch')
            z.extractall(d)
        e=Path(d)/'salah-real-sky';receipt['verification']['zipCRC']='PASS'
        manifest={n:h for h,n in (s.split('  ',1) for s in (e/'MANIFEST.sha256').read_text().splitlines())}
        for n,h in manifest.items():
            if digest(e/n)!=h:raise RuntimeError('Extracted manifest mismatch: '+n)
        receipt['verification']['freshExtractionManifest']='PASS'
        for name,cmd in [('JavaScript',['node','tools/test.mjs']),('Python',[sys.executable,'-m','unittest','discover','-s','tests','-p','*_test.py'])]:
            note('TEST '+' '.join(cmd))
            q=subprocess.run(cmd,cwd=e,capture_output=True,text=True,timeout=90);log=q.stdout+q.stderr
            (a.out/f'Salah_Real_Sky_Checkpoint_{a.stage}_{name}_extracted.log').write_text(log)
            if q.returncode:raise RuntimeError(name+' extracted tests failed:\n'+log[-3000:])
            pattern=r'# tests (\d+)' if name=='JavaScript' else r'Ran (\d+) tests?'
            m=re.search(pattern,log);receipt['tests'][name]={'exitCode':0,'count':int(m.group(1)) if m else None,'log':f'Salah_Real_Sky_Checkpoint_{a.stage}_{name}_extracted.log'}
        cmds=[[sys.executable,'tools/rebuild.py'],[sys.executable,'tools/inspect_diffuse_source.py']]
        if a.stage in ['7_2','7_3']:cmds.append([sys.executable,'tools/build_diffuse_diagnostic.py'])
        if a.stage=='7_3':cmds.append([sys.executable,'tools/build_diffuse_viewer.py'])
        logs=[]
        for cmd in cmds:
            note('TEST '+' '.join(cmd))
            q=subprocess.run(cmd,cwd=e,capture_output=True,text=True,timeout=90);logs.append(' '.join(cmd)+'\n'+q.stdout+q.stderr)
            if q.returncode:raise RuntimeError('Extracted rebuild failed: '+logs[-1][-3000:])
        note('CHECK_REBUILT_MANIFEST')
        changed=[n for n,h in manifest.items() if digest(e/n)!=h]
        if changed:raise RuntimeError('Rebuild changed manifest members: '+repr(changed))
        receipt['verification']['offlineRebuildAllManifestMembers']='PASS';receipt['verification']['membersChangedByRebuild']=changed
        (a.out/f'Salah_Real_Sky_Checkpoint_{a.stage}_rebuild.log').write_text('\n'.join(logs))
    note('VERIFIED')
    receipt['engineeringVerification']='PASS (does not close scientific source gate)'
    out.with_suffix('.receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');out.with_suffix('.sha256').write_text(receipt['sha256']+'  '+out.name+'\n');print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
