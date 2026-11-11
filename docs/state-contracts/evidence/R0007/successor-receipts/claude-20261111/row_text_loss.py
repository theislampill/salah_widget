"""Detect web-font row-text loss in 370x570 R0007 native recordings (theme-agnostic).

Usage: python -I row_text_loss.py ROOT OUT_JSON
For each *.webm under ROOT, per frame:
  rowEdges  = horizontal luminance steps > 8 inside the six timetable rows, x 30..305, y 296..490 (Inter text)
  monoEdges = same measure on the countdown/status line, x 40..330, y 258..282 (monospace; not a web font)
A LOSS frame is any frame where rowEdges < 150 while monoEdges >= 800, i.e. the card and its non-web-font
status/countdown text are painted but the row text is not (either text that vanished, or text whose first
paint is being withheld). Consecutive loss frames form an interval.
Calibration: original FF20 run 42834337271 — loss frames measure 2..55 row edges, text frames >= 1200.
"""
import json, pathlib, subprocess, sys
import numpy as np
W, H = 370, 570

def frames(video):
    p = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', str(video), '-vsync', '0', '-f', 'rawvideo', '-pix_fmt', 'gray', '-s', f'{W}x{H}', '-'], capture_output=True, check=True)
    a = np.frombuffer(p.stdout, dtype=np.uint8)
    return a[: (len(a) // (W * H)) * W * H].reshape(-1, H, W).astype(np.int16)

root = pathlib.Path(sys.argv[1]); result = {}
for video in sorted(root.rglob('*.webm')):
    f = frames(video)
    name = next((p for p in video.parts if p.startswith('NE07-')), video.parent.name)
    row = [int((np.abs(x[296:490, 31:305] - x[296:490, 30:304]) > 8).sum()) for x in f]
    mono = [int((np.abs(x[258:282, 41:330] - x[258:282, 40:329]) > 8).sum()) for x in f]
    first = next((i for i, v in enumerate(row) if v >= 600), None)
    intervals = []; i = 0
    while i < len(row):
        if row[i] < 150 and mono[i] >= 800:
            j = i
            while j < len(row) and row[j] < 150 and mono[j] >= 800: j += 1
            intervals.append({'firstFrame': i + 1, 'lastFrame': j, 'frames': j - i, 'ptsFirst': round(i * 0.04, 3), 'minRowEdges': min(row[i:j]), 'beforeFirstRowText': first is None or i < first})
            i = j
        else: i += 1
    result[name] = {'frames': len(f), 'firstRowTextFrame': None if first is None else first + 1, 'lossIntervals': intervals}
    print(f'{name:34s} frames {len(f):4d} firstRowText {str(result[name]["firstRowTextFrame"]):>5s} loss', [(x['firstFrame'], x['lastFrame']) for x in intervals])
pathlib.Path(sys.argv[2]).write_text(json.dumps(result, indent=1))
print('cells', len(result), '| cells with loss', sum(1 for r in result.values() if r['lossIntervals']), '| intervals', sum(len(r['lossIntervals']) for r in result.values()), '| loss frames', sum(x['frames'] for r in result.values() for x in r['lossIntervals']), '| cells never showing row text', sum(1 for r in result.values() if r['firstRowTextFrame'] is None))
