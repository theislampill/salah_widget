"""Build an opt-in HTTP experimental widget in a NEW directory. Never modify the source tree."""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def replace(root, relative, old, new):
    path=root / relative
    text=path.read_text()
    if text.count(old)!=1:
        raise ValueError(f'{relative}: missing or ambiguous authored seam {old[:60]!r}')
    path.write_text(text.replace(old,new))


def patch_refined(dest,rc):
    replace(dest,rc,"function clear(reason='invalidated'){","function clear(reason='invalidated'){window.R0035Lab?.clear(canvas);")
    replace(dest,rc,'const base=nativeCalendarRegion(frame.raster,geometry.mask(),rows);',
            'const sampledMask=geometry.mask();capture.r35Mask=sampledMask;const base=nativeCalendarRegion(frame.raster,sampledMask,rows);')
    replace(dest,rc,'status.last.composition.lastComposeMs=lastCompose-started;return true;',
            "status.last.composition.lastComposeMs=lastCompose-started;window.R0035Lab?.publish('refined',canvas,acceptedJob,acceptedFrame,capture,capture.r35Mask);return true;")
    replace(dest,rc,'status.presentationSkips++;lastCompose=performance.now();previousPresentation=presentation;',
            'if(!lifecycle.current(job,snapshot())){clear("superseded during detail composition");return;}\n     status.presentationSkips++;lastCompose=performance.now();previousPresentation=presentation;window.R0035Lab?.renew(canvas,job,frame,capture);')


def build(dest):
    dest=dest.resolve()
    if dest == ROOT or ROOT in dest.parents or dest.exists():
        raise ValueError('A new directory outside the source tree is required')
    dest.mkdir(parents=True,exist_ok=False)
    for folder in ['src','real-sky','tools','moon','vendor','v1','tests']:
        shutil.copytree(ROOT/folder,dest/folder,ignore=shutil.ignore_patterns('__pycache__'))
    rc='real-sky/native-host.mjs'
    preview='real-sky/native-preview-host.mjs'
    html='src/native/index.html'
    patch_refined(dest,rc)
    replace(dest,preview,'function clear(reason,all=false){','function clear(reason,all=false){window.R0035Lab?.clear(canvas);')
    replace(dest,preview,'if(disposed)return;disposed=true;retireFirstPaint();','if(disposed)return;disposed=true;window.R0035Lab?.clear(canvas);retireFirstPaint();')
    replace(dest,preview,'status.draws++;lastPaint=performance.now();return true;',
            "status.draws++;lastPaint=performance.now();window.R0035Lab?.publish('preview',canvas,next.job,next,capture,prepared.mask);return true;")
    replace(dest,'real-sky/native-star-preview.mjs','return {...preview,rgba,atmosphereRGBA:source,',
            'return {...preview,replaySources:stars.sources,rgba,atmosphereRGBA:source,')
    replace(dest,html,'</head>','<script type="module" src="tools/r0035/lab_boot.mjs"></script>\n</head>')
    replace(dest,html,'runRenderStage("sky-preview",()=>window.SalahSkyPreview?.present(_RAFNOW()));',
            'runRenderStage("sky-preview",()=>window.SalahSkyPreview?.present(_RAFNOW()));\n      window.R0035Lab?.present();')
    replace(dest,html,'  let starsVis=0; for(const e of _starEls) if(e.style.display!=="none") starsVis++;\n','')
    replace(dest,html,'stars:{op:+(cs.getPropertyValue("--stars").trim()||0), visible:starsVis, blur:cs.getPropertyValue("--starblur").trim(), mw:+(cs.getPropertyValue("--mw").trim()||0)},',
            'stars:window.R0035Lab?.observe()??{status:"experimental producer off",sample:null},')
    start='function _starSampleNow(){'
    path=dest/html
    original=path.read_text()
    old=next(line for line in original.splitlines() if line.startswith(start))
    replace(dest,html,old,'function _starSampleNow(){return window.R0035Lab?.observe()?.sample??null;}')
    old=next(line for line in original.splitlines() if 'const starAnim=' in line)
    replace(dest,html,old,'  const starStatus=window.R0035Lab?.observe()?.status??"off";')
    old=next(line for line in original.splitlines() if '+\x60starΔ 10s' in line)
    new='    +\x60stars ${starStatus} ${cur.s?.id??""} · factor ${cur.s?.factor?.toFixed(4)??"—"} · RGB Δ ${cur.s?.centerDelta??"—"}\\n\x60'
    replace(dest,html,old,new)
    replace(dest,html,new,new+'\n    +`${window.R0035Lab?.debugLine()??"factor Δ 10s — 60s —"}\\n`')
    subprocess.run([sys.executable,'tools/build_native.py'],cwd=dest,check=True)
    subprocess.run([sys.executable,'tools/verify_v1.py'],cwd=dest,check=True)
    tracked=['src/native/index.html',rc,preview,'real-sky/native-star-preview.mjs','index.html',
             'real-sky/native-sky.js','real-sky/native-worker.js','offline.html','GENERATED.json']
    tracked.extend(p.relative_to(dest).as_posix() for p in sorted((dest/'tools/r0035').glob('*.mjs')))
    receipt={'sourceHead':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
             'purpose':'Independent reconstruction. HTTP lab only. Candidate config requires five explicit options.',
             'sha256':{name:hashlib.sha256((dest/name).read_bytes()).hexdigest() for name in tracked}}
    (dest/'r0035-lab-identity.json').write_text(json.dumps(receipt,indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination',type=Path)
    build(parser.parse_args().destination)
