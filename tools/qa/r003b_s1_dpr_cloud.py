"""R003B S1 follow-up: (a) card-edge and corner changes at DPR != 1, before vs after, from r003b_s1_capture.cjs runs
(owner scene, `base`); (b) baked-cloud registration against the hidden DOM cloud canvas (`--cloud 50` runs with the
`domclouds` variant): sub-pixel shift of the baked clouds relative to the DOM clouds in the left and right halves and
upper/lower bands of the cloud band, by normalised cross-correlation of high-passed luminance with a parabolic peak.
Usage: python tools/qa/r003b_s1_dpr_cloud.py dpr <before root> <after root> <out.json>
       python tools/qa/r003b_s1_dpr_cloud.py cloud <before root> <after root> <out.json>"""
import json, os, sys
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter


def L(p):
    a = np.asarray(Image.open(p).convert('RGB')).astype(float); return a, .2126 * a[..., 0] + .7152 * a[..., 1] + .0722 * a[..., 2]


def card_mask(h, w, s, r=28):
    """True inside the card's rounded outer outline (325x530 CSS, radius 28) at scale s."""
    y, x = np.mgrid[0:h, 0:w] + .5; R = r * s
    cx = np.clip(x, R, w - R); cy = np.clip(y, R, h - R)
    return (x - cx) ** 2 + (y - cy) ** 2 <= R * R


def dpr_mode(before, after, out):
    res = {}
    for tag in sorted(os.listdir(before)):
        if not os.path.exists(os.path.join(after, tag, 'capture.json')): continue
        B = json.load(open(os.path.join(before, tag, 'capture.json'))); A = json.load(open(os.path.join(after, tag, 'capture.json')))
        s = A['summary']['screenshotScale']; row = {'dpr': s}
        for st in ('preview', 'refined'):
            cb = next(c for c in B['captures'] if c['state'] == st); ca = next(c for c in A['captures'] if c['state'] == st)
            lay = 'preview' if st == 'preview' else 'refined'
            dev = lambda c: [round(c['layers'][lay]['backing'][0] / (c['layers'][lay]['rect'][2] * s), 5), round(c['layers'][lay]['backing'][1] / (c['layers'][lay]['rect'][3] * s), 5)]
            ab, _ = L(os.path.join(before, tag, f'{st}-base-composite.png')); aa, _ = L(os.path.join(after, tag, f'{st}-base-composite.png'))
            D = np.abs(aa - ab).max(-1); h, w = D.shape; inside = card_mask(h, w, s); c = int(round(30 * s)); e = int(np.ceil(2 * s))
            corner = np.zeros_like(inside); corner[:c, :c] = corner[:c, -c:] = corner[-c:, :c] = corner[-c:, -c:] = True
            band = np.zeros_like(inside); band[:e] = band[-e:] = True; band[:, :e] = band[:, -e:] = True; band &= ~corner
            interior = inside & ~corner & ~band
            row[st] = {'cssRatioBefore': cb['layers'][lay]['ratio'], 'cssRatioAfter': ca['layers'][lay]['ratio'],
                       'backingPerDevicePxBefore': dev(cb), 'backingPerDevicePxAfter': dev(ca),
                       'elementBoxesIdentical': cb['geom'] == ca['geom'],
                       'edgeBand': {'devicePx': e, 'meanAbs': round(float(D[band].mean()), 2), 'max': float(D[band].max()), 'changedPx': int((D[band] > 0).sum())},
                       'corners': {'changedPxOver8': int((D[corner & inside] > 8).sum()), 'max': float(D[corner & inside].max())},
                       'interior': {'max': float(D[interior].max()), 'p999': round(float(np.percentile(D[interior], 99.9)), 1)},
                       'outsideOutline': {'changedPx': int((D[~inside] > 0).sum()), 'max': float(D[~inside].max())}}
        res[tag] = row
    json.dump(res, open(out, 'w'), indent=1); return res


def shift(a, b, maxs=4):
    """Sub-pixel (dy, dx) such that b ~ a shifted by (dy, dx)."""
    a = a - gaussian_filter(a, 6); b = b - gaussian_filter(b, 6); best = None
    sc = np.zeros((2 * maxs + 1, 2 * maxs + 1))
    for i, dy in enumerate(range(-maxs, maxs + 1)):
        for j, dx in enumerate(range(-maxs, maxs + 1)):
            A = a[maxs:-maxs, maxs:-maxs]; Bs = b[maxs + dy:b.shape[0] - maxs + dy, maxs + dx:b.shape[1] - maxs + dx]
            sc[i, j] = (A * Bs).sum() / np.sqrt((A * A).sum() * (Bs * Bs).sum())
    i, j = np.unravel_index(sc.argmax(), sc.shape)
    def para(m, c, p): d = m - 2 * c + p; return 0 if d == 0 else .5 * (m - p) / d
    fy = para(sc[i - 1, j], sc[i, j], sc[i + 1, j]) if 0 < i < sc.shape[0] - 1 else 0
    fx = para(sc[i, j - 1], sc[i, j], sc[i, j + 1]) if 0 < j < sc.shape[1] - 1 else 0
    return round(i - maxs + fy, 3), round(j - maxs + fx, 3), round(float(sc.max()), 3)


def cloud_mode(before, after, out):
    res = {}
    for root, name in ((before, 'before'), (after, 'after')):
        for tag in sorted(os.listdir(root)):
            if 'cloud' not in tag: continue
            _, base = L(os.path.join(root, tag, 'refined-base-composite.png')); _, dom = L(os.path.join(root, tag, 'refined-domclouds-composite.png'))
            boxes = {'left': (10, 30, 150, 150), 'right': (175, 30, 315, 150), 'upper': (40, 20, 285, 85), 'lower': (40, 85, 285, 160)}
            res.setdefault(tag, {})[name] = {k: dict(zip(('dy', 'dx', 'ncc'), shift(dom[b[1]:b[3], b[0]:b[2]], base[b[1]:b[3], b[0]:b[2]]))) for k, b in boxes.items()}
    json.dump(res, open(out, 'w'), indent=1); return res


if __name__ == '__main__':
    r = (dpr_mode if sys.argv[1] == 'dpr' else cloud_mode)(*sys.argv[2:5]); print(json.dumps(r, indent=1)[:6000])
