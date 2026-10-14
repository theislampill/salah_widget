"""Bounded native-video crop sheets; streamed ffmpeg decode, never browser use."""
import argparse, hashlib, json, subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):
            h.update(block)
    return h.hexdigest()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('input',type=Path)
    args=parser.parse_args()
    receipts=[]
    for p in sorted(args.input.glob('*/trace.json')):
        case=p.parent;video=next((case/'video').glob('*.webm'))
        probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0',
            '-show_entries','stream=width,height:frame=best_effort_timestamp_time','-of','json',str(video)]))
        times=[float(f['best_effort_timestamp_time']) for f in probe['frames']]
        target=HERE/'batch3-transition'/case.name;target.mkdir(parents=True,exist_ok=True)
        windows=[(0,2),(2.04,4.04)]
        if case.name=='R0006-tomorrow-promotion':windows.append((64,66))
        row={'caseId':case.name,'videoSha256':sha(video),'traceSha256':sha(p),'frameCount':len(times),'windows':[]}
        for j,(start,end) in enumerate(windows):
            ids=[{'ordinal':i,'ptsSeconds':t} for i,t in enumerate(times) if start<=t<=end]
            if not ids:continue
            name=f'window-{j}.png'
            subprocess.check_call(['ffmpeg','-v','error','-y','-i',str(video),'-vf',
                f'select=between(t\\,{start}\\,{end}),crop=95:250:230:280,tile=8x7:padding=2:color=gray',
                '-frames:v','1',str(target/name)])
            row['windows'].append({'png':name,'sha256':sha(target/name),'frames':ids})
        (target/'windows.json').write_text(json.dumps(row,indent=2)+'\n',encoding='utf-8')
        receipts.append(row)
        print(case.name,[(w['frames'][0]['ordinal'],w['frames'][-1]['ordinal']) for w in row['windows']])
    return 0

if __name__=='__main__':raise SystemExit(main())
