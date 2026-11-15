"""R0034 owner-artifact: score a layer-isolation run written by r0034_artifact_probe.cjs.

For every iso-*.png in RUN_DIR (one layer hidden, or one test-only toggle applied) against iso-base-a.png:
  bars_before / bars_after : peak-to-peak (8-bit luminance levels) of the per-column MEDIAN of the high-pass residual
                             (luminance minus a sigma-25 Gaussian) over card rows 245-400, columns 12-150 -- the
                             countdown-to-rows region where the owner's soft vertical bars sit. Column medians reject
                             text and row edges, so this measures vertical structure.
  diff_mean_abs            : mean |toggle - base| over the same region (how much the layer contributes at all).
  diff_p99_abs/diff_max_abs: 99th percentile / maximum |difference| in the region (levels).
  diff_bars                : the same column-median peak-to-peak taken of the high-passed DIFFERENCE image, i.e. the
                             vertical-bar structure that the hidden layer carried.
Noise floor: iso-base-b and iso-base-c (no toggle, later captures) scored the same way.

  python tools/qa/r0034_artifact_isolate.py RUN_DIR [--json OUT.json] [--scale 1]
"""
import argparse, glob, json, os
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter

def lum(p):
    a = np.asarray(Image.open(p).convert('RGB'), dtype=np.float64)
    return .2126 * a[..., 0] + .7152 * a[..., 1] + .0722 * a[..., 2]

def colbars(L, s):
    R = L - gaussian_filter(L, sigma=25 * s, mode='reflect')
    y0, y1, x0, x1 = int(245 * s), int(400 * s), int(12 * s), int(150 * s)
    cm = np.median(R[y0:y1, x0:x1], axis=0)
    return float(cm.max() - cm.min()), cm

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('run'); ap.add_argument('--json'); ap.add_argument('--scale', type=float, default=1.0)
    a = ap.parse_args(); s = a.scale
    meta = {}
    rj = os.path.join(a.run, 'run.json')
    if os.path.exists(rj):
        for e in json.load(open(rj)).get('elements', []):
            meta[e['id']] = f"{e['tag']}.{e['cls'].strip().replace(' ', '.')}"
    base = lum(os.path.join(a.run, 'iso-base-a.png'))
    b_bars, _ = colbars(base, s)
    y0, y1, x0, x1 = int(245 * s), int(400 * s), int(12 * s), int(150 * s)
    rows = []
    for p in sorted(glob.glob(os.path.join(a.run, 'iso-*.png'))):
        n = os.path.basename(p)
        if n == 'iso-base-a.png':
            continue
        L = lum(p); D = L - base
        after, _ = colbars(L, s); dbars, _ = colbars(D, s)
        key = n[4:-4]
        label = key
        if key.startswith('e-'):
            label = key + ' ' + meta.get(key[2:], '')
        rows.append({'capture': n, 'label': label, 'bars_before': round(b_bars, 2), 'bars_after': round(after, 2),
                     'diff_mean_abs': round(float(np.abs(D[y0:y1, x0:x1]).mean()), 3), 'diff_bars': round(dbars, 2),
                     'diff_p99_abs': round(float(np.percentile(np.abs(D[y0:y1, x0:x1]), 99)), 2),
                     'diff_max_abs': round(float(np.abs(D[y0:y1, x0:x1]).max()), 2)})
    for r in rows:
        print(f"{r['label']:48s} bars {r['bars_before']:6.2f} -> {r['bars_after']:6.2f}   |diff| {r['diff_mean_abs']:6.3f}   diff-bars {r['diff_bars']:6.2f}   p99 {r['diff_p99_abs']:6.2f} max {r['diff_max_abs']:6.2f}")
    if a.json:
        json.dump(rows, open(a.json, 'w'), indent=1)

if __name__ == '__main__':
    main()
