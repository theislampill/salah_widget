"""R0034 periodicity analysis of flat-sky crops (canvas readback and composited capture).
Residual = luminance - Gaussian blur (sigma 3). Reports residual std (grey levels), the strongest 2-D FFT peaks
(Hann-windowed residual; pitch in px, direction, sinusoid amplitude estimate in grey levels) and the same for a
synthetic flat control (quadratic surface fitted to the crop in float, rounded to 8 bit). Writes amplified residual
PNGs (x16/x32/x64, nearest x4) for human inspection."""
import json, os, sys
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter

H = sys.argv[1]; OUT = sys.argv[2]; os.makedirs(OUT, exist_ok=True)

def lum(path):
    a = np.asarray(Image.open(path).convert('RGB')).astype(float)
    return .2126 * a[..., 0] + .7152 * a[..., 1] + .0722 * a[..., 2]

def quad_control(c):
    h, w = c.shape; y, x = np.mgrid[0:h, 0:w]
    A = np.stack([np.ones_like(x), x, y, x * x, y * y, x * y], -1).reshape(-1, 6).astype(float)
    coef, *_ = np.linalg.lstsq(A, c.reshape(-1), rcond=None)
    return np.round((A @ coef).reshape(h, w))

def analyse(c):
    r = c - gaussian_filter(c, 3)
    r = r[4:-4, 4:-4]
    h, w = r.shape
    win = np.outer(np.hanning(h), np.hanning(w))
    F = np.fft.fft2((r - r.mean()) * win)
    M = np.abs(F); M[0, 0] = 0
    fy = np.fft.fftfreq(h); fx = np.fft.fftfreq(w)
    # Ignore frequencies with a period > 16 px (blur-residual leakage) in both axes.
    mask = (np.abs(fy)[:, None] < 1 / 16) & (np.abs(fx)[None, :] < 1 / 16); M2 = M.copy(); M2[mask] = 0
    peaks = []
    for _ in range(3):
        i, j = np.unravel_index(M2.argmax(), M2.shape)
        f = np.hypot(fx[j], fy[i]); amp = 2 * M2[i, j] / win.sum()
        peaks.append({'pitchPx': round(1 / f, 2) if f else None, 'dirDeg': round(float(np.degrees(np.arctan2(fy[i], fx[j]))) % 180, 1),
                      'ampGrey': round(float(amp), 3), 'peakToMedian': round(float(M2[i, j] / (np.median(M2[M2 > 0]) + 1e-12)), 1)})
        # suppress this peak and its mirror
        for (a, b) in [(i, j), ((-i) % h, (-j) % w)]:
            M2[max(0, a - 1):a + 2, max(0, b - 1):b + 2] = 0
    return {'residualStd': round(float(r.std()), 3), 'peaks': peaks}, r

def save_residual(r, name):
    for g in (16, 32, 64):
        v = np.clip(128 + r * g, 0, 255).astype(np.uint8)
        Image.fromarray(v).resize((v.shape[1] * 4, v.shape[0] * 4), Image.NEAREST).save(f'{OUT}/{name}-x{g}.png')

# Crops: canvas readback (pure sky, no DOM) and composited capture (inside the Fajr glass row, behind backdrop-filter).
CANVAS_BOX = (100, 380, 300, 500)      # x0,y0,x1,y1 in canvas px
COMPOSITE_BOX = (70, 298, 230, 320)    # inside the first glass row, CSS px at DPR 1
res = {}
for tree in ('main', 'branch'):
    for eng in ('firefox', 'chromium'):
        for state in ('preview', 'refined'):
            for kind, suffix, box in (('canvas', '-canvas', CANVAS_BOX), ('composite', '', COMPOSITE_BOX)):
                p = f'{H}/{tree}/{eng}-{state}{suffix}.png'
                if not os.path.exists(p): continue
                c = lum(p)[box[1]:box[3], box[0]:box[2]]
                a, r = analyse(c); ctl, _ = analyse(quad_control(c))
                res[f'{tree}/{eng}/{state}/{kind}'] = {'measured': a, 'flatControl8bit': ctl}
                if eng == 'firefox': save_residual(r, f'{tree}-{eng}-{state}-{kind}')
# Owner crops (not committed): residual periodicity of a flat band in each crop.
owner = {}
for n in ('5', '6', '7'):
    p = os.path.join(sys.argv[3], f'{n}.png')
    c = lum(p); h, w = c.shape
    band = c[int(h * .55):int(h * .9), 2:int(w * .85)]
    a, r = analyse(band); owner[n] = {'size': [w, h], **a}
    save_residual(r, f'owner-{n}')
json.dump({'crops': {'canvas': CANVAS_BOX, 'composite': COMPOSITE_BOX}, 'results': res, 'ownerCrops': owner}, open(f'{OUT}/periodicity.json', 'w'), indent=1)
for k, v in res.items():
    m, c = v['measured'], v['flatControl8bit']
    print(k, 'std', m['residualStd'], 'peak', m['peaks'][0], '| control std', c['residualStd'], 'peak', c['peaks'][0])
for k, v in owner.items(): print('owner', k, v['size'], 'std', v['residualStd'], 'peaks', v['peaks'][:2])
