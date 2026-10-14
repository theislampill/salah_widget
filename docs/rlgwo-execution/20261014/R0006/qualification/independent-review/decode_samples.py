"""Decode lossless original native frames for offline inspection only."""
import hashlib, json, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EVIDENCE = HERE.parent
SOURCE = EVIDENCE.parent / 'salah_widget'

def digest(data):
    return hashlib.sha256(data).hexdigest()

def extract(video, target, numbers):
    target.mkdir(parents=True, exist_ok=True)
    probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0',
        '-show_entries', 'stream=width,height:frame=best_effort_timestamp_time', '-of', 'json', str(video)]))
    frames = probe['frames']
    times = [float(f['best_effort_timestamp_time']) for f in frames]
    selected = sorted(set(n if isinstance(n, int) else min(range(len(times)), key=lambda i: abs(times[i]-n)) for n in numbers))
    vf = 'select=' + '+'.join(f'eq(n\\,{n})' for n in selected)
    subprocess.check_call(['ffmpeg', '-v', 'error', '-y', '-i', str(video), '-vf', vf, '-fps_mode', 'passthrough', str(target / 'sample-%03d.png')])
    receipt = {'videoSha256': digest(video.read_bytes()), 'frameCount': len(times),
        'size': probe['streams'][0], 'samples': []}
    for ix, ordinal in enumerate(selected, 1):
        png = target / f'sample-{ix:03d}.png'
        raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(png), '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'])
        receipt['samples'].append({'png': png.name, 'ordinal': ordinal, 'ptsSeconds': times[ordinal],
            'pngSha256': digest(png.read_bytes()), 'decodedRgbSha256': digest(raw)})
    (target/'samples.json').write_text(json.dumps(receipt, indent=2)+'\n', encoding='utf-8')
    print(str(target.relative_to(HERE)), [(x['ordinal'], x['ptsSeconds']) for x in receipt['samples']])

def main():
    for engine, nums in [('chromium', [1505,1506]), ('firefox',[1522,1523])]:
        case = EVIDENCE/'browser'/engine/'R0006-cold-body'
        extract(next((case/'video').glob('*.webm')), HERE/'original-cold'/engine, nums)
    reuse=json.loads((EVIDENCE/'preservation-reuse.json').read_bytes())
    for control in reuse['controls']:
        path=SOURCE/control['path']
        extract(path/'native.webm', HERE/'preservation'/control['engine']/control['case'], [5.0,15.0,30.0])

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
