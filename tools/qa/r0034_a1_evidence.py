"""R0034-A1 before/after evidence sheets, built only from our own renders.

  python tools/qa/r0034_a1_evidence.py --vm <scene_diff out dir> --native <probe out root> --out <evidence dir>

VM sheets (deterministic refined sky raster alone, no clouds/Moon/CSS; from r0034_a1_scene_diff.mjs):
  vm-<scene>.png : main | candidate | difference magnitude (max channel |code delta| x 16, clipped) for each scene.
Native sheets (frozen-instant composites from r0034_artifact_probe.cjs, freeze mode; directories main-<engine>-<scene>
and cand-<engine>-<scene>):
  native-<engine>-<scene>-card.png     : full card main | candidate
  native-<engine>-<scene>-crop2x.png   : card x 0-200, y 230-420 at 2x, main | candidate
  native-<engine>-<scene>-resid12.png  : luminance minus sigma-25 Gaussian, x12, card x 12-317, y 245-430, main | candidate
"""
import argparse, glob, json, os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(__file__))
from r0034_artifact_residual import measure

W, H = 325, 530
GAP = lambda h, c=255: np.full((h, 6, 3) if c is not None else (h, 6), 255, np.uint8)

def rgba(path):
    return np.frombuffer(open(path, 'rb').read(), np.uint8).reshape(H, W, 4)[..., :3]

def hstack(*ims):
    h = max(i.shape[0] for i in ims); out = []
    for k, i in enumerate(ims):
        if i.ndim == 2: i = np.repeat(i[..., None], 3, 2)
        if i.shape[0] < h: i = np.pad(i, ((0, h - i.shape[0]), (0, 0), (0, 0)), constant_values=255)
        out.append(i)
        if k < len(ims) - 1: out.append(np.full((h, 6, 3), 255, np.uint8))
    return np.hstack(out)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--vm'); ap.add_argument('--native'); ap.add_argument('--out'); a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    if a.vm:
        for m in sorted(glob.glob(os.path.join(a.vm, '*.main.rgba'))):
            tag = os.path.basename(m)[:-10]; c = m.replace('.main.rgba', '.cand.rgba')
            A, B = rgba(m), rgba(c); d = np.abs(A.astype(int) - B.astype(int)).max(2)
            mag = np.clip(d * 16, 0, 255).astype(np.uint8)
            Image.fromarray(hstack(A, B, mag)).save(os.path.join(a.out, f'vm-{tag}.png'), optimize=True)
    if a.native:
        for md in sorted(glob.glob(os.path.join(a.native, 'main-*'))):
            tag = os.path.basename(md)[5:]; cd = os.path.join(a.native, 'cand-' + tag)
            mf, cf = os.path.join(md, 's', 'frozen.png'), os.path.join(cd, 's', 'frozen.png')
            if not (os.path.exists(mf) and os.path.exists(cf)): continue
            s = 1.5 if 'dpr15' in tag else 1.0
            A = np.asarray(Image.open(mf).convert('RGB')); B = np.asarray(Image.open(cf).convert('RGB'))
            Image.fromarray(hstack(A, B)).save(os.path.join(a.out, f'native-{tag}-card.png'), optimize=True)
            cr = lambda X: X[int(230 * s):int(420 * s), 0:int(200 * s)]
            x = hstack(cr(A), cr(B)); Image.fromarray(x).resize((x.shape[1] * 2, x.shape[0] * 2), Image.NEAREST).save(os.path.join(a.out, f'native-{tag}-crop2x.png'), optimize=True)
            _, RA = measure(mf, scale=s); _, RB = measure(cf, scale=s)
            v = lambda R: np.clip(128 + 12 * R, 0, 255).astype(np.uint8)
            Image.fromarray(hstack(v(RA), v(RB))).save(os.path.join(a.out, f'native-{tag}-resid12.png'), optimize=True)

if __name__ == '__main__':
    main()
