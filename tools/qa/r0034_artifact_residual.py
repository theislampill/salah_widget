"""R0034 owner-artifact residual: luminance minus a wide Gaussian blur, column profiles at fixed rows.

Used to compare OUR composited renders with the owner's description of soft vertical bars between the
countdown line and the Fajr/Sunrise rows. Coordinates are CARD coordinates (the 325x530 card); pass --ox/--oy
for the card's offset inside the image (the owner's full-card capture has the card about 16 px in).

  python tools/qa/r0034_artifact_residual.py IMG [--ox 0 --oy 0] [--png OUT.png] [--json OUT.json] [--base BASE.png]

With --base, the residual is also taken of (IMG - BASE) so a layer toggle can be measured as a difference.
Metrics (all in 8-bit luminance levels):
  gap_profile : column profile of the residual averaged over card rows 284-290 (between countdown and Fajr row,
                owner image rows ~346-354), card columns 12-317.
  bar_pp      : peak-to-peak of gap_profile over card columns 12-110 (where the owner's bars sit).
  col_median  : per-column median of the residual over card rows 245-430 (robust to text), and its peak-to-peak.
  peak48/dip127: column contrasts of gap_profile at the reproduced artifact's columns (see code).
  --scale     : image pixels per card pixel (the owner's capture is ~1.195: card 388x635 px in a 415x644 image).
"""
import argparse, json, sys
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter

def lum(img):
    a = np.asarray(img.convert('RGB'), dtype=np.float64)
    return .2126 * a[..., 0] + .7152 * a[..., 1] + .0722 * a[..., 2]

def residual(L, radius=25):
    # Gaussian with sigma = radius (the PIL GaussianBlur(radius) convention), reflected edges
    return L - gaussian_filter(L, sigma=radius, mode='reflect')

def measure(path, ox=0, oy=0, base=None, scale=1.0):
    img = Image.open(path)
    L = lum(img)
    if base is not None:
        L = L - lum(Image.open(base))
    S = lambda v: int(round(v * scale))
    # card region x 12..317, y 245..430 (= the integrator's owner crop x 30-395, y 300-520 at scale 1.195, offset 16,6)
    x0, x1, y0, y1 = S(12) + ox, S(317) + ox, S(245) + oy, S(430) + oy
    x1 = min(x1, L.shape[1]); y1 = min(y1, L.shape[0])
    R = residual(L[y0:y1, x0:x1], 25 * scale)
    # gap band between the countdown line and the Fajr row: card rows 284-290 (owner image rows ~346-354)
    gap = R[S(284) - S(245):S(290) - S(245)].mean(axis=0)
    nb = S(110) - S(12)   # card columns 12..110 hold the owner's bars (card x ~24-28 and ~47-51)
    cm = np.median(R, axis=0)
    out = {
        'image': str(path).replace('\\', '/').split('/')[-1], 'ox': ox, 'oy': oy, 'scale': scale, 'base': bool(base),
        'gap_profile_card_x0': 12,
        'gap_profile': [round(float(v), 2) for v in gap],
        'bar_pp_x12_110': round(float(gap[:nb].max() - gap[:nb].min()), 2),
        'gap_pp_all': round(float(gap.max() - gap.min()), 2),
        'col_median_pp_x12_110': round(float(cm[:nb].max() - cm[:nb].min()), 2),
        'col_median_pp_all': round(float(cm.max() - cm.min()), 2),
        'resid_rms': round(float(R.std()), 3),
        # Fingerprint of the 2026-11-14 artifact at 10:26 Central Florida (physical Sun at card ~41,282): a narrow
        # bright column at card x~48 between darker columns at ~39 and ~57, and a dark column at ~126-129.
        'peak48': round(float(gap[S(48) - S(12)] - .5 * (gap[S(39) - S(12)] + gap[S(57) - S(12)])), 2),
        'dip127': round(float(gap[S(127) - S(12)] - .5 * (gap[S(112) - S(12)] + gap[S(142) - S(12)])), 2),
    }
    return out, R

def main():
    p = argparse.ArgumentParser()
    p.add_argument('img'); p.add_argument('--ox', type=int, default=0); p.add_argument('--oy', type=int, default=0)
    p.add_argument('--scale', type=float, default=1.0); p.add_argument('--png'); p.add_argument('--json'); p.add_argument('--base'); p.add_argument('--gain', type=float, default=12)
    a = p.parse_args()
    out, R = measure(a.img, a.ox, a.oy, a.base, a.scale)
    if a.png:
        v = np.clip(128 + a.gain * R, 0, 255).astype(np.uint8)
        Image.fromarray(v).resize((v.shape[1] * 2, v.shape[0] * 2), Image.NEAREST).save(a.png)
    s = json.dumps(out)
    if a.json:
        open(a.json, 'w').write(s)
    short = {k: v for k, v in out.items() if k != 'gap_profile'}
    print(json.dumps(short))

if __name__ == '__main__':
    main()
