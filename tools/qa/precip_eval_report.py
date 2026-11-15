"""Precipitation-presentation evaluation (research only, 2026-11-15): offline analysis of precip_eval_capture clips.

  python tools/qa/precip_eval_report.py analyze --bulk <bulk dir> --engine chromium [--only <regex>] --out <metrics.json>
  python tools/qa/precip_eval_report.py sheet   --bulk <bulk dir> --engine chromium --ids a,b,c --labels x,y,z --png <out.png> [--crop 0,60,325,300]
  python tools/qa/precip_eval_report.py webp    --bulk <bulk dir> --engine chromium --ids a,b --labels x,y --webp <out.webp> [--frames 60]
  python tools/qa/precip_eval_report.py prune   --bulk <bulk dir> --engine chromium [--keep-every 5]

Stepped clips hold a<k>.png (card) and b<k>.png (same instant with the streak layer hidden): |a-b| isolates the rain.
Metrics per clip: streak count per frame (geometry), rain-pixel density per tile on an 8x12 grid (40.6 x 44.2 px tiles)
and its coefficient of variation across tiles (space) and across frames (time); length/width/opacity distributions;
lean angle; fall speed (px/s, matched by element index between frames); occupied-column count (fixed tracks);
temporal power spectrum of tile density (share of power below 0.5 Hz = sheet/gust band); repeat detection (max
normalised correlation of the rain mask at lags >= 0.4 s); scene statistics of the rain-hidden frame (CIELAB L* of
upper-sky and horizon bands, horizon contrast, sun-region peak) and of the full frame. Never reads qaState hashes.
"""
import argparse, glob, json, os, re, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

GRID_C, GRID_R = 8, 12


def lab_L(rgb):
    c = rgb.astype(np.float64) / 255.0
    lin = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    Y = lin[..., 0] * 0.2126 + lin[..., 1] * 0.7152 + lin[..., 2] * 0.0722
    f = np.where(Y > 216 / 24389, np.cbrt(Y), (24389 / 27 * Y + 16) / 116)
    return 116 * f - 16


def load(p):
    return np.asarray(Image.open(p).convert('RGB'), dtype=np.int16)


def analyze_clip(d):
    meta = json.load(open(os.path.join(d, 'meta.json'), encoding='utf8'))
    fr = meta.get('frames') or []
    fa = sorted(glob.glob(os.path.join(d, 'a*.png')))
    fb = sorted(glob.glob(os.path.join(d, 'b*.png')))
    fps = meta['fps']
    hy = meta.get('horizonY') or 157
    out = {'id': meta['id'], 'cell': meta['cell'], 'engine': meta['engine'], 'variant': meta['variant'], 'frames': len(fr),
           'data': (meta.get('state') or {}).get('data'), 'vars': (meta.get('state') or {}).get('vars', {}).get('--rain-op'),
           'header': (meta.get('state') or {}).get('header'), 'continuedExternal': len(meta.get('continuedExternal') or []),
           'aborted': meta.get('aborted'), 'errors': meta.get('errors'), 'horizonY': hy}
    if meta.get('error'):
        out['error'] = meta['error']
    # ---- geometry ----
    counts, lens, wids, ops, xs, speeds, angles = [], [], [], [], [], [], []
    prev = None
    for f in fr:
        g = f['geom']
        cur = {}
        if g.get('pe'):
            ds = g['pe']['drops'] or []
            counts.append(len(ds))
            k = g['pe'].get('k') or 0
            for x, y, L_, a_, far, i, cyc in ds:
                lens.append(L_ * np.hypot(1, k)); ops.append(a_); cur[(i, cyc)] = y
                if y - L_ <= 160 <= y: xs.append(x - k * (y - 160))
            angles.append(np.degrees(np.arctan(k)))
        else:
            ds = [q for q in g['dom'] if q[5] == 0]
            counts.append(len(ds))
            sl = g['vars'].get('slant') or '0px'
            kk = float(sl.replace('px', '') or 0) / 132.0
            for x, y, w, h, o, cls, i in ds:
                lens.append(float(np.hypot(w - 1.5, h))); wids.append(1.5); ops.append(o); cur[i] = y + h
                if y <= 160 <= y + h:
                    xb = x + 0.75 + (w - 1.5) * (1 if kk >= 0 else 0)
                    xs.append(xb - kk * (y + h - 160))
            angles.append(float(np.degrees(np.arctan(float(sl.replace('px', '') or 0) / 132.0))))
        if prev is not None:
            for key, y in cur.items():
                if key in prev and y > prev[key]:
                    speeds.append((y - prev[key]) * fps)
        prev = cur
    q = lambda v: None if not len(v) else [round(float(np.percentile(v, p)), 3) for p in (5, 25, 50, 75, 95)]
    out['geom'] = {'countMean': round(float(np.mean(counts)), 2) if counts else 0, 'countMin': int(min(counts)) if counts else 0,
                   'countMax': int(max(counts)) if counts else 0, 'lengthPx_p5_25_50_75_95': q(lens), 'opacity_p5_25_50_75_95': q(ops),
                   'fallSpeedPxS_p5_25_50_75_95': q(speeds), 'leanDeg_mean': round(float(np.mean(angles)), 2) if angles else None,
                   'leanDeg_range': [round(float(min(angles)), 2), round(float(max(angles)), 2)] if angles else None,
                   'crossings_y160': len(xs), 'distinctCrossingX_2px': int(len(set(int(x // 2) for x in xs))) if xs else 0}
    if not fa or len(fa) != len(fb):
        return out
    # ---- rain layer from image pairs ----
    H, W = 530, 325
    th, tw = H / GRID_R, W / GRID_C
    tiles = []
    masks = []
    Lb_up, Lb_hz, con_hz, La_hz, sunpk, LA_full = [], [], [], [], [], []
    for pa, pb in zip(fa, fb):
        A, B = load(pa), load(pb)
        dif = np.abs(A - B).sum(axis=2)
        m = (dif > 6).astype(np.float32)
        masks.append(m[::2, ::2])
        t = np.zeros((GRID_R, GRID_C))
        for r in range(GRID_R):
            for c in range(GRID_C):
                t[r, c] = m[int(r * th):int((r + 1) * th), int(c * tw):int((c + 1) * tw)].mean()
        tiles.append(t)
        Lb = lab_L(B); La = lab_L(A)
        Lb_up.append(Lb[50:100].mean()); Lb_hz.append(Lb[int(hy) - 25:int(hy) + 5].mean()); con_hz.append(Lb[int(hy) - 25:int(hy) + 5].std())
        La_hz.append(La[int(hy) - 25:int(hy) + 5].mean()); sunpk.append(float(np.percentile(Lb[0:300], 99.5))); LA_full.append(La[0:300].mean())
    T = np.array(tiles)  # frames x R x C
    active = T.mean(axis=0) > 0.002
    sp = T.mean(axis=0)[active]
    out['tiles'] = {'activeTiles': int(active.sum()), 'meanDensity': round(float(T.mean()), 5),
                    'cvSpace': round(float(sp.std() / sp.mean()), 3) if sp.size and sp.mean() > 0 else None,
                    'cvTime': round(float(np.mean([T[:, r, c].std() / max(T[:, r, c].mean(), 1e-9) for r, c in zip(*np.where(active))])), 3) if active.any() else None,
                    'rowProfile': [round(float(v), 4) for v in T.mean(axis=(0, 2))]}
    if active.any():
        series = np.array([T[:, r, c] - T[:, r, c].mean() for r, c in zip(*np.where(active))])
        P = (np.abs(np.fft.rfft(series, axis=1)) ** 2).mean(axis=0)
        fq = np.fft.rfftfreq(series.shape[1], 1 / fps)
        tot = P[1:].sum()
        out['spectrum'] = {'lowShare_below0p5Hz': round(float(P[(fq > 0) & (fq < 0.5)].sum() / tot), 3) if tot > 0 else None,
                           'peakHz': round(float(fq[1:][np.argmax(P[1:])]), 3)}
        # whole-field density (sum over the active area): slow modulation = sheets/gusts
        tot_series = T[:, active].sum(axis=1)
        out['fieldDensity_cvTime'] = round(float(tot_series.std() / tot_series.mean()), 3) if tot_series.mean() > 0 else None
    Ms = np.array(masks).reshape(len(masks), -1)
    Mz = Ms - Ms.mean(axis=1, keepdims=True)
    nrm = np.linalg.norm(Mz, axis=1) + 1e-9
    best = (0, None)
    for lag in range(int(0.4 * fps), len(masks) // 2):
        cc = float(np.mean([(Mz[i] @ Mz[i + lag]) / (nrm[i] * nrm[i + lag]) for i in range(len(masks) - lag)]))
        if cc > best[0]:
            best = (cc, lag / fps)
    out['repeat'] = {'maxCorr_lag>=0.4s': round(best[0], 3), 'atLagS': best[1]}
    out['scene'] = {'Lstar_upper_rainHidden': round(float(np.mean(Lb_up)), 2), 'Lstar_horizonBand_rainHidden': round(float(np.mean(Lb_hz)), 2),
                    'horizonBandStdL': round(float(np.mean(con_hz)), 2), 'Lstar_horizonBand_full': round(float(np.mean(La_hz)), 2),
                    'skyP99p5_L': round(float(np.mean(sunpk)), 2), 'Lstar_sky0to300_full': round(float(np.mean(LA_full)), 2)}
    return out


def cmd_analyze(a):
    res = {}
    if os.path.exists(a.out):
        res = json.load(open(a.out, encoding='utf8'))
    for d in sorted(glob.glob(os.path.join(a.bulk, a.engine, '*'))):
        name = os.path.basename(d)
        if a.only and not re.search(a.only, name):
            continue
        if not os.path.exists(os.path.join(d, 'meta.json')) or 'realtime' in name:
            continue
        r = analyze_clip(d)
        res[name + '@' + a.engine] = r
        g = r.get('geom', {}); t = r.get('tiles', {})
        print(name, a.engine, 'n', g.get('countMean'), 'cvS', t.get('cvSpace'), 'cvT', t.get('cvTime'), 'low', (r.get('spectrum') or {}).get('lowShare_below0p5Hz'),
              'xings', g.get('crossings_y160'), 'distinctX', g.get('distinctCrossingX_2px'), 'v', g.get('fallSpeedPxS_p5_25_50_75_95'), 'Lhz', (r.get('scene') or {}).get('Lstar_horizonBand_full'))
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(res, open(a.out, 'w', encoding='utf8'), indent=1)


def frames_of(a, i):
    return sorted(glob.glob(os.path.join(a.bulk, a.engine, i, 'a*.png')))


def font():
    try:
        return ImageFont.truetype('arial.ttf', 12)
    except Exception:
        return ImageFont.load_default()


def cmd_sheet(a):
    ids, labels = a.ids.split(','), a.labels.split(',')
    x0, y0, x1, y1 = [int(v) for v in a.crop.split(',')]
    n0 = min(len(frames_of(a, i)) for i in ids)
    picks = [0, n0 // 3, 2 * n0 // 3]
    w, h = x1 - x0, y1 - y0
    S = Image.new('RGB', (w * len(picks) + 4 * (len(picks) - 1) + 110, (h + 4) * len(ids)), (18, 18, 22))
    dr = ImageDraw.Draw(S); F = font()
    for r, (i, lab) in enumerate(zip(ids, labels)):
        fs = frames_of(a, i)
        dr.text((4, r * (h + 4) + 6), lab.replace('|', '\n'), fill=(230, 230, 230), font=F)
        for c, p in enumerate(picks):
            if p < len(fs):
                S.paste(Image.open(fs[p]).convert('RGB').crop((x0, y0, x1, y1)), (110 + c * (w + 4), r * (h + 4)))
    S.save(a.png)
    print('sheet', a.png, S.size)


def cmd_webp(a):
    ids, labels = a.ids.split(','), a.labels.split(',')
    x0, y0, x1, y1 = [int(v) for v in a.crop.split(',')]
    seqs = [frames_of(a, i) for i in ids]
    n = min(int(a.frames), *[len(s) for s in seqs])
    w, h = x1 - x0, y1 - y0
    F = font(); out = []
    for k in range(n):
        S = Image.new('RGB', (w * len(ids) + 4 * (len(ids) - 1), h + 18), (18, 18, 22)); dr = ImageDraw.Draw(S)
        for c, (s, lab) in enumerate(zip(seqs, labels)):
            S.paste(Image.open(s[k]).convert('RGB').crop((x0, y0, x1, y1)), (c * (w + 4), 18))
            dr.text((c * (w + 4) + 3, 2), lab, fill=(235, 235, 235), font=F)
        out.append(S)
    out[0].save(a.webp, save_all=True, append_images=out[1:], duration=int(1000 / 15), loop=0, quality=72, method=4)
    print('webp', a.webp, len(out), os.path.getsize(a.webp))


def cmd_prune(a):
    keep = int(a.keep_every)
    n = 0
    for d in glob.glob(os.path.join(a.bulk, a.engine, '*')):
        if os.path.exists(os.path.join(d, 'KEEP')):
            continue
        for p in glob.glob(os.path.join(d, '[ab]*.png')):
            k = int(re.findall(r'(\d+)', os.path.basename(p))[0])
            if os.path.basename(p).startswith('b') or k % keep:
                os.remove(p); n += 1
    print('pruned', n)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd'); ap.add_argument('--bulk'); ap.add_argument('--engine', default='chromium'); ap.add_argument('--only')
    ap.add_argument('--out'); ap.add_argument('--ids'); ap.add_argument('--labels'); ap.add_argument('--png'); ap.add_argument('--webp')
    ap.add_argument('--crop', default='0,40,325,300'); ap.add_argument('--frames', default='75'); ap.add_argument('--keep-every', default='5')
    a = ap.parse_args()
    {'analyze': cmd_analyze, 'sheet': cmd_sheet, 'webp': cmd_webp, 'prune': cmd_prune}[a.cmd](a)
