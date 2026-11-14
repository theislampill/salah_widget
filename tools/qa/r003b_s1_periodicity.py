"""R003B slice S1 periodicity analysis (extends tools/qa/r0034_periodicity.py, same residual/control method).

Residual = luminance - Gaussian blur (sigma 3), 4 px border trimmed. Reported per crop:
  * residualStd (grey levels);
  * 2-D Hann-windowed FFT strongest peak (pitch px, direction, sinusoid amplitude), periods > 16 px masked;
  * per-axis 1-D spectra: the residual is averaged across the other axis and its Hann-windowed spectrum searched for
    pitches 2..16 px; 'y' = variation along y (horizontal bands, the owner's 90-degree peaks), 'x' = along x;
  * the same for a flat control: a quadratic surface fitted to the crop, rounded to 8 bit (pure quantisation).
Modes:
  capture <capture-root> <out-dir> [--residuals tag1,tag2]   analyse every <run>/capture.json under the root
  degrade <clean-png> <out-dir>                               discriminator 7: rescale/JPEG a clean composite
Coordinates are CSS px of the card (DPR 1); composites are scaled by the run's screenshotScale. Pillow, numpy, scipy.
"""
import io, json, os, sys
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter

# Crops (x0, y0, x1, y1) in CSS px of the 325x530 card / canvas px of the 325x530 backing.
SKY_ONLY = (268, 165, 316, 222)     # composite: sky right of the arc's descending leg, no DOM element above it
GLASS1 = (70, 294, 250, 320)        # composite: interior of the first glass row (Fajr), no glyphs
GLASS2 = (70, 329, 250, 355)        # composite: interior of the second glass row (Sunrise), no glyphs
CANVAS = (100, 380, 300, 500)       # canvas readback: pure sky behind the rows (R0034 CANVAS_BOX)
CANVAS_SKY = (269, 166, 317, 223)     # canvas readback: the canvas pixels displayed at SKY_ONLY (+1 px border offset)


def lum(img):
    a = np.asarray(img.convert('RGB')).astype(float)
    return .2126 * a[..., 0] + .7152 * a[..., 1] + .0722 * a[..., 2]


def quad_control(c):
    h, w = c.shape; y, x = np.mgrid[0:h, 0:w]
    A = np.stack([np.ones_like(x), x, y, x * x, y * y, x * y], -1).reshape(-1, 6).astype(float)
    coef, *_ = np.linalg.lstsq(A, c.reshape(-1), rcond=None)
    return np.round((A @ coef).reshape(h, w))


def axis_peak(profile):
    n = len(profile)
    if n < 16: return None
    win = np.hanning(n); F = np.abs(np.fft.rfft((profile - profile.mean()) * win)); f = np.fft.rfftfreq(n)
    ok = (f >= 1 / 16) & (f <= 0.5)
    if not ok.any(): return None
    k = np.argmax(np.where(ok, F, 0)); med = np.median(F[ok]) + 1e-12
    return {'pitchPx': round(float(1 / f[k]), 2), 'ampGrey': round(float(2 * F[k] / win.sum()), 3), 'peakToMedian': round(float(F[k] / med), 1)}


def analyse(c):
    r = (c - gaussian_filter(c, 3))[4:-4, 4:-4]
    h, w = r.shape
    win = np.outer(np.hanning(h), np.hanning(w))
    M = np.abs(np.fft.fft2((r - r.mean()) * win)); M[0, 0] = 0
    fy = np.fft.fftfreq(h); fx = np.fft.fftfreq(w)
    M[(np.abs(fy)[:, None] < 1 / 16) & (np.abs(fx)[None, :] < 1 / 16)] = 0
    i, j = np.unravel_index(M.argmax(), M.shape); f = np.hypot(fx[j], fy[i])
    peak = {'pitchPx': round(1 / f, 2) if f else None, 'dirDeg': round(float(np.degrees(np.arctan2(fy[i], fx[j]))) % 180, 1),
            'ampGrey': round(float(2 * M[i, j] / win.sum()), 3)}
    return {'residualStd': round(float(r.std()), 3), 'peak2d': peak, 'y': axis_peak(r.mean(1)), 'x': axis_peak(r.mean(0))}, r


def crop(img, box, scale):
    b = tuple(int(round(v * scale)) for v in box)
    return lum(img)[b[1]:b[3], b[0]:b[2]]


def both(c):
    m, r = analyse(c); ctl, _ = analyse(quad_control(c)); return {'measured': m, 'flatControl8bit': ctl}, r


def save_residual(r, path_base, gains=(32, 64)):
    for g in gains:
        v = np.clip(128 + r * g, 0, 255).astype(np.uint8)
        Image.fromarray(v).resize((v.shape[1] * 4, v.shape[0] * 4), Image.NEAREST).save(f'{path_base}-x{g}.png')


def capture_mode(root, out, residual_tags):
    os.makedirs(out, exist_ok=True); res = {}
    for tag in sorted(os.listdir(root)):
        cj = os.path.join(root, tag, 'capture.json')
        if not os.path.exists(cj): continue
        d = json.load(open(cj)); sc = d['summary']['screenshotScale']; run = {}
        for cap in d['captures']:
            st, va = cap['state'], cap['variant']
            img = Image.open(os.path.join(root, tag, f'{st}-{va}-composite.png'))
            for name, box in (('skyOnly', SKY_ONLY), ('glass1', GLASS1), ('glass2', GLASS2)):
                k = f'{st}/{va}/composite/{name}'; run[k], r = both(crop(img, box, sc))
                if tag in residual_tags and name in ('glass1', 'skyOnly') and va in ('base', 'onetoone', 'nobackdrop', 'nopreview'):
                    save_residual(r, os.path.join(out, f'{tag}-{st}-{va}-{name}'))
            if va == 'base':
                which = 'preview' if st == 'preview' else 'refined'
                p = os.path.join(root, tag, f'{st}-{which}-canvas.png')
                if os.path.exists(p):
                    cimg = Image.open(p)
                    for name, box in (('canvas', CANVAS), ('canvasSky', CANVAS_SKY)):
                        k = f'{st}/raw-{which}/{name}'; run[k], r = both(crop(cimg, box, 1))
                        if tag in residual_tags and name == 'canvas': save_residual(r, os.path.join(out, f'{tag}-{st}-raw-{which}'))
        # Handoff discontinuity: last preview sample vs first composed sample, sky and whole card, grey levels.
        shots = sorted(f for f in os.listdir(os.path.join(root, tag)) if f.startswith('handoff-'))
        pre = [f for f in shots if f.endswith('preview.png')]; post = [f for f in shots if f.endswith('composed.png')]
        if pre and post:
            A = lum(Image.open(os.path.join(root, tag, pre[-1]))); B = lum(Image.open(os.path.join(root, tag, post[0])))
            D = np.abs(A - B); s = int(round(sc))
            run['handoff'] = {'from': pre[-1], 'to': post[0], 'meanAbsCard': round(float(D.mean()), 3), 'p99AbsCard': round(float(np.percentile(D, 99)), 2),
                              'meanAbsSkyOnly': round(float(D[int(SKY_ONLY[1] * sc):int(SKY_ONLY[3] * sc), int(SKY_ONLY[0] * sc):int(SKY_ONLY[2] * sc)].mean()), 3)}
        res[tag] = run
    json.dump(res, open(os.path.join(out, 'periodicity.json'), 'w'), indent=1)
    return res


def degrade_mode(clean, out):
    """Discriminator 7: does rescaling and/or JPEG of a whole clean composite create owner-band (4.1-4.5 / 8-9 px)
    peaks in the flat crops? The whole frame is transformed (JPEG blocks align to the frame), then GLASS1/GLASS2/
    SKY_ONLY are cropped at the transformed scale and analysed; the reported value is the strongest axis peak."""
    os.makedirs(out, exist_ok=True); base = Image.open(clean).convert('RGB'); res = {}
    def run(name, img, f):
        row = {}
        for cname, box in (('glass1', GLASS1), ('glass2', GLASS2), ('skyOnly', SKY_ONLY)):
            m, r = analyse(crop(img, box, f)); row[cname] = m
            if name in ('clean', 'jpeg60', 'scale1.25-bicubic+jpeg75') and cname == 'glass1': save_residual(r, os.path.join(out, f'degrade-{name}-{cname}'))
        res[name] = row
    def jpeg(img, q):
        buf = io.BytesIO(); img.save(buf, 'JPEG', quality=q); return Image.open(io.BytesIO(buf.getvalue())).convert('RGB')
    run('clean', base, 1)
    for f in (0.8, 0.9, 1.067, 1.1, 1.25, 1.5, 2.0):
        for rs_name, rs in (('bilinear', Image.BILINEAR), ('bicubic', Image.BICUBIC), ('lanczos', Image.LANCZOS)):
            run(f'scale{f}-{rs_name}', base.resize((round(base.width * f), round(base.height * f)), rs), f)
    for q in (95, 85, 75, 60, 40):
        run(f'jpeg{q}', jpeg(base, q), 1)
        for f in (1.067, 1.25, 1.5):
            up = base.resize((round(base.width * f), round(base.height * f)), Image.BICUBIC)
            run(f'scale{f}-bicubic+jpeg{q}', jpeg(up, q), f)
            run(f'jpeg{q}+scale{f}-bicubic', jpeg(base, q).resize(up.size, Image.BICUBIC), f)
    json.dump(res, open(os.path.join(out, 'degrade.json'), 'w'), indent=1)
    return res


if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'capture':
        tags = sys.argv[sys.argv.index('--residuals') + 1].split(',') if '--residuals' in sys.argv else []
        r = capture_mode(sys.argv[2], sys.argv[3], tags)
        for tag, run in r.items():
            for k, v in run.items():
                if k == 'handoff': print(tag, 'handoff', v); continue
                m, c = v['measured'], v['flatControl8bit']
                print(tag, k, 'std', m['residualStd'], 'y', m['y'], 'x', m['x'], '| ctl std', c['residualStd'])
    elif mode == 'degrade':
        for k, row in degrade_mode(sys.argv[2], sys.argv[3]).items():
            print(k, ' | '.join(f"{c} std {v['residualStd']} y {v['y'] and (v['y']['pitchPx'], v['y']['ampGrey'])} x {v['x'] and (v['x']['pitchPx'], v['x']['ampGrey'])}" for c, v in row.items()))
