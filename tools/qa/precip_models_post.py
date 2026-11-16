"""Precipitation MODEL comparison (research only): post-process real-time screencast captures.

  python tools/qa/precip_models_post.py --bulk <models bulk dir> --only <regex> --anim <dir> [--blind <dir> --key <file>] [--keep 1]

Per scene/model: resample the timestamped lossless frames to a constant 25 fps native-size (325x530) animated WebP;
prayer-text contrast (min / mean over the clip) for each text rectangle recorded at capture (rows, big clock, title,
countdown) as a luminance ratio (95th vs 30th percentile relative luminance inside the rectangle, WCAG formula) -
comparative only; per-scene side-by-side comparison WebP (models in capture order, labelled). Blind pack: for day
scenes, a 3 s unlabelled clip per model, written under a random name; the key goes to a separate file.
Frames are deleted afterwards unless --keep 1 (the first frame and three consecutive mid frames are always kept).
"""
import argparse, glob, json, os, random, re
import numpy as np
from PIL import Image, ImageDraw, ImageFont

FPS = 25


def rel_lum(a):
    c = a.astype(np.float64) / 255.0
    lin = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    return lin[..., 0] * 0.2126 + lin[..., 1] * 0.7152 + lin[..., 2] * 0.0722


def resample_idx(ts, t0, dur):
    return [max(0, min(int(np.searchsorted(ts, t0 + k / FPS, side='right') - 1), len(ts) - 1)) for k in range(int(dur * FPS))]


_cache = {}


def load(p):
    if p not in _cache:
        _cache[p] = Image.open(p).convert('RGB')
    return _cache[p]


def font(sz=12):
    try:
        return ImageFont.truetype('arial.ttf', sz)
    except Exception:
        return ImageFont.load_default()


def contrast(paths, rects):
    names = [r for r in rects if re.match(r'(row\d-(label|time)|bigclock|title|countdown)$', r['name'])]
    res = {r['name']: [] for r in names}
    for p in paths:
        a = np.asarray(Image.open(p).convert('RGB'))
        L = rel_lum(a)
        for r in names:
            x0, y0 = int(r['x']), int(r['y']); x1, y1 = int(r['x'] + r['w']) + 1, int(r['y'] + r['h']) + 1
            blk = L[max(0, y0):y1, max(0, x0):x1]
            if blk.size == 0:
                continue
            lt, lb = np.percentile(blk, 95), np.percentile(blk, 30)
            res[r['name']].append((max(lt, lb) + 0.05) / (min(lt, lb) + 0.05))
    return {k: {'min': round(float(min(v)), 3), 'mean': round(float(np.mean(v)), 3)} for k, v in res.items() if v}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--bulk'); ap.add_argument('--only', default='.'); ap.add_argument('--anim'); ap.add_argument('--blind'); ap.add_argument('--key')
    ap.add_argument('--keep', default='0'); ap.add_argument('--out', default=None); ap.add_argument('--compare', default='1')
    a = ap.parse_args()
    os.makedirs(a.anim, exist_ok=True)
    summary = json.load(open(a.out, encoding='utf8')) if a.out and os.path.exists(a.out) else {}
    key = json.load(open(a.key, encoding='utf8')) if a.key and os.path.exists(a.key) else {}
    rnd = random.Random(20261115 + len(key))
    for sdir in sorted(glob.glob(os.path.join(a.bulk, '*'))):
        sid = os.path.basename(sdir)
        if not re.search(a.only, sid) or not os.path.exists(os.path.join(sdir, 'meta.json')):
            continue
        meta = json.load(open(os.path.join(sdir, 'meta.json'), encoding='utf8'))
        S = {'error': meta.get('error'), 'continuedExternal': len(meta.get('continuedExternal') or []), 'requests': meta.get('requestsSeen'),
             'aborted': meta.get('aborted'), 'geomProduct': meta.get('geomProduct'), 'models': {}}
        seqs, labels = [], []
        for spec, rec in meta.get('models', {}).items():
            mdir = os.path.join(sdir, re.sub(r'[|:+~]', '_', spec))
            paths = sorted(glob.glob(os.path.join(mdir, 'f*.png')))
            M = {'frames': len(rec.get('frames') or []), 'costMs': rec.get('costMs'), 'costMs4x': rec.get('costMs4x'),
                 'geomSame': rec.get('geom', {}).get('card') == meta.get('geomProduct', {}).get('card') and rec.get('geom', {}).get('header') == meta.get('geomProduct', {}).get('header')
                 and rec.get('geom', {}).get('footer') == meta.get('geomProduct', {}).get('footer') and rec.get('geom', {}).get('rows') == meta.get('geomProduct', {}).get('rows')
                 and rec.get('geom', {}).get('glass') == meta.get('geomProduct', {}).get('glass'),
                 'overlayParents': rec.get('geom', {}).get('overlayParents'), 'completionBound': rec.get('completionBound'), 'boundaryUtc': rec.get('boundaryUtc'),
                 'record': (rec.get('records') or [None])[-1]}
            if os.path.exists(os.path.join(mdir, 'still.png')):
                M['still'] = True
            if paths:
                ts = np.array(rec['frames'], dtype=float)
                if len(ts) != len(paths):
                    ts = np.linspace(0, len(paths) / 55.0, len(paths))
                fps_real = (len(ts) - 1) / (ts[-1] - ts[0]) if len(ts) > 1 else 0
                M['captureFps'] = round(float(fps_real), 1)
                M['contrast'] = contrast(paths[::6], meta.get('rects') or [])
                dur = min(ts[-1] - ts[0], 12.0)
                _cache.clear()
                rs = [load(paths[i]) for i in resample_idx(ts, ts[0], dur)]
                w = os.path.join(a.anim, f'{sid}--{re.sub(r"[|:+~]", "_", spec)}.webp')
                rs[0].save(w, save_all=True, append_images=rs[1:], duration=int(1000 / FPS), loop=0, quality=80, method=4)
                M['anim'] = os.path.basename(w); M['animSeconds'] = round(dur, 2)
                seqs.append(rs); labels.append(spec)
                if a.blind and sid.startswith('day-') and not sid.startswith('day-dry') and dur >= 3.4:
                    clip = [load(paths[i]) for i in resample_idx(ts, ts[0] + 0.4, 3.0)]
                    name = 'clip-%06d.webp' % rnd.randrange(10 ** 6)
                    while name in key:
                        name = 'clip-%06d.webp' % rnd.randrange(10 ** 6)
                    os.makedirs(a.blind, exist_ok=True)
                    clip[0].save(os.path.join(a.blind, name), save_all=True, append_images=clip[1:], duration=int(1000 / FPS), loop=0, quality=80, method=4)
                    key[name] = {'scene': sid, 'model': spec}
                if a.keep != '1':
                    mid = len(paths) // 2
                    keep = {paths[0], *paths[mid:mid + 3]}
                    for p in paths:
                        if p not in keep:
                            os.remove(p)
            S['models'][spec] = M
        if seqs and a.compare == '1' and len(seqs) > 1:
            n = min(len(s) for s in seqs); n = min(n, 4 * FPS)
            out = []
            for k in range(n):
                C = Image.new('RGB', (len(seqs) * 329 - 4, 548), (18, 18, 22)); d = ImageDraw.Draw(C)
                for j, (s, lab) in enumerate(zip(seqs, labels)):
                    C.paste(s[k], (j * 329, 18)); d.text((j * 329 + 4, 2), lab.replace('current', 'current product'), fill=(235, 235, 235), font=font())
                out.append(C)
            w = os.path.join(a.anim, f'{sid}--compare.webp')
            out[0].save(w, save_all=True, append_images=out[1:], duration=int(1000 / FPS), loop=0, quality=78, method=4)
            S['compare'] = os.path.basename(w)
        summary[sid] = S
        if a.out:   # incremental: a timeout never orphans clips or loses the scene record
            json.dump(summary, open(a.out, 'w', encoding='utf8'), indent=1)
        if a.key:
            os.makedirs(os.path.dirname(os.path.abspath(a.key)), exist_ok=True)
            json.dump(key, open(a.key, 'w', encoding='utf8'), indent=1)
        print(sid, {k: (v.get('captureFps'), v.get('costMs'), v.get('geomSame')) for k, v in S['models'].items()}, 'ext', S['continuedExternal'])
    if a.out:
        json.dump(summary, open(a.out, 'w', encoding='utf8'), indent=1)
    if a.key:
        os.makedirs(os.path.dirname(os.path.abspath(a.key)), exist_ok=True)
        json.dump(key, open(a.key, 'w', encoding='utf8'), indent=1)


if __name__ == '__main__':
    main()
