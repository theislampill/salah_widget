"""R003B slice S1 (CI-02) before/after comparison of r003b_s1_capture.cjs runs.

Usage: python tools/qa/r003b_s1_compare.py <before-root> <after-root> <control-root> <out-dir>
  before = main, after = candidate, control = a second main run (main-vs-main noise). Each root holds one
  directory per run tag (e.g. firefox-owner-dpr1) with capture.json and PNGs.
Writes <out>/compare.json and before/after crops (full card; sky region at 2x and 4x nearest-neighbour; behind
glass) for the preview and refined base captures. Pillow, numpy, scipy.
"""
import json, os, sys
import numpy as np
from PIL import Image
from scipy.ndimage import maximum_filter, sobel

SKY = (240, 60, 316, 160)        # CSS px: upper-right sky (owner: plain blue; night: stars)
GLASS = (20, 292, 305, 360)      # first two glass rows
SKY_ONLY = (268, 165, 316, 222)
GLASS1 = (70, 294, 250, 320)


def rgb(p): return np.asarray(Image.open(p).convert('RGB')).astype(float)


def lum(a): return .2126 * a[..., 0] + .7152 * a[..., 1] + .0722 * a[..., 2]


def diff(a, b, box=None):
    if box: a = a[box[1]:box[3], box[0]:box[2]]; b = b[box[1]:box[3], box[0]:box[2]]
    d = np.abs(a - b)
    return {'meanAbs': round(float(d.mean()), 4), 'p99': round(float(np.percentile(d, 99)), 2), 'max': float(d.max()),
            'changedPct': round(float((d.max(-1) > 0).mean() * 100), 2)}


def ring(a, b):
    """Outermost 2 CSS px of the card (border + first padding pixel), where 1:1 moves canvas content."""
    m = np.zeros(a.shape[:2], bool); m[:2] = m[-2:] = True; m[:, :2] = m[:, -2:] = True
    d = np.abs(a - b)[m]; return {'meanAbs': round(float(d.mean()), 4), 'max': float(d.max())}


def sharp(a, box):
    """Gradient energy (mean squared Sobel magnitude, grey^2/px^2) and star compactness: for the 8 brightest local
    maxima, mean peak excess over the 7x7 median and mean count of pixels above half that excess (smaller = tighter)."""
    L = lum(a)[box[1]:box[3], box[0]:box[2]]
    g = float(np.mean(sobel(L, 0) ** 2 + sobel(L, 1) ** 2) / 16)
    mx = (L == maximum_filter(L, 7)); ys, xs = np.nonzero(mx[3:-3, 3:-3]); ys += 3; xs += 3
    vals = [(L[y, x] - np.median(L[y - 3:y + 4, x - 3:x + 4]), y, x) for y, x in zip(ys, xs)]
    vals = sorted(vals, reverse=True)[:8]; ex, area = [], []
    for e, y, x in vals:
        if e <= 2: continue
        w = L[y - 3:y + 4, x - 3:x + 4]; base = np.median(w); ex.append(e); area.append(int((w - base > e / 2).sum()))
    return {'gradEnergy': round(g, 3), 'starPeakExcess': round(float(np.mean(ex)), 2) if ex else None,
            'starHalfMaxArea': round(float(np.mean(area)), 2) if area else None, 'stars': len(ex)}


def zoom(a, box, f):
    c = Image.fromarray(a[box[1]:box[3], box[0]:box[2]].astype(np.uint8)); return c.resize((c.width * f, c.height * f), Image.NEAREST)


def pair(left, right, gap=6):
    out = Image.new('RGB', (left.width + right.width + gap, max(left.height, right.height)), (255, 0, 255))
    out.paste(left, (0, 0)); out.paste(right, (left.width + gap, 0)); return out


def main(before, after, control, out):
    os.makedirs(out, exist_ok=True); res = {}
    for tag in sorted(os.listdir(before)):
        if not os.path.exists(os.path.join(after, tag, 'capture.json')): continue
        B = json.load(open(os.path.join(before, tag, 'capture.json'))); A = json.load(open(os.path.join(after, tag, 'capture.json')))
        C = json.load(open(os.path.join(control, tag, 'capture.json'))) if os.path.exists(os.path.join(control, tag, 'capture.json')) else None
        row = {'perf': {'before': B['summary'].get('perf'), 'after': A['summary'].get('perf'), 'control': C and C['summary'].get('perf')},
               'releaseToComposedMs': {'before': B['summary'].get('releaseToComposedMs'), 'after': A['summary'].get('releaseToComposedMs'), 'control': C and C['summary'].get('releaseToComposedMs')},
               'staleSamples': {'before': B['summary']['previewLayerCompositedWhileComposed'], 'after': A['summary']['previewLayerCompositedWhileComposed']}}
        for st in ('preview', 'refined'):
            cb = next(c for c in B['captures'] if c['state'] == st and c['variant'] == 'base')
            ca = next(c for c in A['captures'] if c['state'] == st and c['variant'] == 'base')
            row[st] = {'layers': {'before': cb['layers'], 'after': ca['layers']},
                       'elementBoxesIdentical': cb['geom'] == ca['geom'],
                       'elementBoxDiffs': [k for k in cb['geom'] if cb['geom'][k] != ca['geom'].get(k)],
                       'sync': {'before': cb['sync'], 'after': ca['sync']}}
            pb, pa = rgb(os.path.join(before, tag, f'{st}-base-composite.png')), rgb(os.path.join(after, tag, f'{st}-base-composite.png'))
            row[st]['diffAfterVsBefore'] = {'card': diff(pa, pb), 'sky': diff(pa, pb, SKY), 'glass': diff(pa, pb, GLASS), 'outerRing': ring(pa, pb)}
            if C:
                pc = rgb(os.path.join(control, tag, f'{st}-base-composite.png'))
                row[st]['diffControlVsBefore'] = {'card': diff(pc, pb), 'sky': diff(pc, pb, SKY), 'glass': diff(pc, pb, GLASS), 'outerRing': ring(pc, pb)}
            row[st]['sharpness'] = {'before': sharp(pb, SKY), 'after': sharp(pa, SKY), 'control': C and sharp(pc, SKY)}
            nb = rgb(os.path.join(before, tag, f'{st}-nobackdrop-composite.png')); na = rgb(os.path.join(after, tag, f'{st}-nobackdrop-composite.png'))
            row[st]['glassFilterEffect'] = {'before': diff(pb, nb, GLASS), 'after': diff(pa, na, GLASS)}
            if tag.endswith('dpr1') and ('owner' in tag or 'night' in tag):
                name = f'{tag}-{st}'
                pair(Image.fromarray(pb.astype(np.uint8)), Image.fromarray(pa.astype(np.uint8))).save(os.path.join(out, f'{name}-card-before-after.png'))
                pair(zoom(pb, SKY, 4), zoom(pa, SKY, 4)).save(os.path.join(out, f'{name}-sky4x-before-after.png'))
                pair(zoom(pb, GLASS, 2), zoom(pa, GLASS, 2)).save(os.path.join(out, f'{name}-glass2x-before-after.png'))
        res[tag] = row
    json.dump(res, open(os.path.join(out, 'compare.json'), 'w'), indent=1)
    return res


if __name__ == '__main__':
    r = main(*sys.argv[1:5])
    for tag, row in r.items():
        for st in ('preview', 'refined'):
            s = row[st]; L = s['layers']
            print(tag, st, 'ratio', L['before']['preview' if st == 'preview' else 'refined']['ratio'], '->', L['after']['preview' if st == 'preview' else 'refined']['ratio'],
                  'boxesSame', s['elementBoxesIdentical'], 'diff card', s['diffAfterVsBefore']['card'], 'ctl', s.get('diffControlVsBefore', {}).get('card'),
                  'sharp', s['sharpness']['before'], '->', s['sharpness']['after'])
        print(tag, 'perf', row['perf'], 'r2c', row['releaseToComposedMs'])
