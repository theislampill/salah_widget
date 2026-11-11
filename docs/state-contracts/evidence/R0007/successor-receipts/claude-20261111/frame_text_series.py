"""Per-frame text-presence series for a 370x570 widget recording.

Usage: python -I frame_text_series.py RUN_DIR
Extracts every frame with ffmpeg, then measures 'ink' (count of bright pixels) in
regions: timetable rows and centre name/time (web-font text), the mono countdown
and the header label (non-web-font controls). It also reads the 10x10 marker at
the top-left corner (if the observer painted one) to align frames with page events.

A frame is 'populated' when rows ink is within 60%..150% of the settled value
(median of the last 20 frames); blank white pre-paint frames are thereby excluded.
A loss interval is a span, after the first populated frame, where a region's ink
is below 25% of its settled value.
"""
import json
import pathlib
import subprocess
import sys

import numpy as np
from PIL import Image

run = pathlib.Path(sys.argv[1])
video = next(run.glob('*.webm'))
frames = run / 'frames'
frames.mkdir(exist_ok=True)
if not any(frames.iterdir()):
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', str(video), '-vsync', '0', str(frames / 'f-%05d.png')], check=True)

REGIONS = {'rows': (25, 292, 312, 492), 'centre': (60, 118, 290, 228), 'mono': (70, 258, 135, 282), 'label': (70, 18, 150, 38)}
MARK = {'#000': (0, 0, 0), 'media': (255, 0, 0), 'loading': (0, 255, 0), 'loadingdone': (0, 0, 255), 'rows-populated': (255, 255, 0), 'loadingerror': (255, 0, 255)}


def ink(img, box):
    a = np.asarray(img.crop(box).convert('L'), dtype=np.int16)
    return int((a > 200).sum())


def marker(img):
    r, g, b = [int(x) for x in np.asarray(img.convert('RGB').crop((2, 2, 8, 8))).reshape(-1, 3).mean(axis=0)]
    best = min(MARK, key=lambda k: sum((p - q) ** 2 for p, q in zip(MARK[k], (r, g, b))))
    d = sum((p - q) ** 2 for p, q in zip(MARK[best], (r, g, b)))
    return best if d < 3 * 70 ** 2 else 'none'


series = []
for p in sorted(frames.glob('f-*.png')):
    img = Image.open(p)
    row = {k: ink(img, b) for k, b in REGIONS.items()}
    row['marker'] = marker(img)
    series.append(row)

settled = {k: float(np.median([s[k] for s in series[-20:]])) for k in REGIONS}
first = next((i for i, s in enumerate(series) if settled['rows'] > 0 and 0.6 * settled['rows'] <= s['rows'] <= 1.5 * settled['rows']), None)
out = {'frames': len(series), 'firstPopulatedFrame': None if first is None else first + 1, 'regions': {}}
transitions, prev = [], None
for i, s in enumerate(series):
    if s['marker'] != prev:
        transitions.append([i + 1, s['marker']])
        prev = s['marker']
out['markerTransitions'] = transitions
for k in REGIONS:
    v = [s[k] for s in series]
    losses = []
    i = first if first is not None else len(v)
    while i < len(v):
        if v[i] < 0.25 * settled[k]:
            j = i
            while j < len(v) and v[j] < 0.25 * settled[k]:
                j += 1
            losses.append({'firstFrame': i + 1, 'lastFrame': j, 'encodedSeconds': round((j - i) * 0.04, 3)})
            i = j
        else:
            i += 1
    out['regions'][k] = {'settledInk': settled[k], 'lossIntervals': losses}
(run / 'series.json').write_text(json.dumps({'summary': out, 'series': series}))
print(run.name, json.dumps(out))
