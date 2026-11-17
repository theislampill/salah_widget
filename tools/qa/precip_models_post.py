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


def scene_metrics(paths):
    # comparative lightness and fine-structure measures of the sky band (8-bit sRGB -> CIE L*):
    # bandL = mean L* rows 20-250; detail = std of 3-px high-passed L* rows 20-180 (deck/streak structure);
    # motionE = RMS of frame-to-frame difference of high-passed L* (changing fine structure, rows 20-250)
    from scipy.ndimage import gaussian_filter
    Ls = []
    for p in paths:
        a = np.asarray(Image.open(p).convert('RGB')).astype(np.float64) / 255.0
        lin = np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4); Y = lin @ np.array([0.2126, 0.7152, 0.0722])
        L = np.where(Y > 216 / 24389, 116 * np.cbrt(Y) - 16, 24389 / 27 * Y); Ls.append(L)
    hp = [L - gaussian_filter(L, 3) for L in Ls]
    E = [float(np.sqrt(np.mean((hp[i][20:250] - hp[i - 1][20:250]) ** 2))) for i in range(1, len(hp))]
    return {'bandL': round(float(np.mean([L[20:250].mean() for L in Ls])), 2), 'detail': round(float(np.mean([h[20:180].std() for h in hp])), 3),
            'motionE': round(float(np.mean(E)), 3) if E else None}


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
    ap.add_argument('--keep', default='0'); ap.add_argument('--blindrx', default=r'^day-(?!dry)'); ap.add_argument('--out', default=None); ap.add_argument('--compare', default='1')
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
            mdir = os.path.join(sdir, re.sub(r'[|:+~^@/.]', '_', spec))
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
                M['scene'] = scene_metrics(paths[::6])
                end = rec.get('wallEnd') / 1000.0 if rec.get('wallEnd') else ts[-1]
                dur = min(max(ts[-1], end) - ts[0], 12.0)          # hold the last frame to the end of capture (static scenes emit few frames)
                _cache.clear()
                idx = resample_idx(ts, ts[0], dur)
                claim = next((x['wall'] / 1000.0 for x in (rec.get('records') or []) if x.get('wall') and x.get('precip') == 'off'), None)                     if any(x.get('precip') == 'on' for x in (rec.get('records') or [])) else None
                rs = []
                for k, i in enumerate(idx):
                    im = load(paths[i])
                    if claim is not None:      # mark the claim-withdrawal frame (+/- one 50 ms poll) in the clip
                        tk = ts[0] + k / FPS
                        im = im.copy(); d = ImageDraw.Draw(im)
                        txt = ('claims withdrawn +%.2f s' % (tk - claim)) if tk >= claim else ('claims valid  %.2f s' % (tk - claim))
                        d.rectangle((4, 506, 200, 524), fill=(0, 0, 0)); d.text((8, 508), txt, fill=(255, 210, 90) if tk >= claim else (200, 230, 200), font=font())
                        M['claimWithdrawnClipS'] = round(claim - ts[0], 3)
                    rs.append(im)
                w = os.path.join(a.anim, f'{sid}--{re.sub(r"[|:+~^@/.]", "_", spec)}.webp')
                rs[0].save(w, save_all=True, append_images=rs[1:], duration=int(1000 / FPS), loop=0, quality=80, method=4)
                M['anim'] = os.path.basename(w); M['animSeconds'] = round(dur, 2)
                seqs.append(rs); labels.append(spec)
                if a.blind and re.search(a.blindrx, sid) and dur >= 3.2:
                    clip = [load(paths[i]) for i in resample_idx(ts, ts[0] + 0.3, 3.0)]
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


def strip(anim_dir, scenes, model, labels, out, crop_h=330):
    """Side-by-side strip of one model across scenes (frames aligned by index from each scene's clip start)."""
    seqs = []
    for sc in scenes:
        im = Image.open(os.path.join(anim_dir, f'{sc}--{model}.webp'))
        fr = []
        for k in range(getattr(im, 'n_frames', 1)):
            im.seek(k); fr.append(im.convert('RGB').crop((0, 0, 325, crop_h)))
        seqs.append(fr)
    n = min(len(s) for s in seqs)
    outf = []
    for k in range(n):
        C = Image.new('RGB', (len(seqs) * 329 - 4, crop_h + 18), (18, 18, 22)); d = ImageDraw.Draw(C)
        for j, (s, lab) in enumerate(zip(seqs, labels)):
            C.paste(s[k], (j * 329, 18)); d.text((j * 329 + 4, 2), lab, fill=(235, 235, 235), font=font())
        outf.append(C)
    outf[0].save(out, save_all=True, append_images=outf[1:], duration=int(1000 / FPS), loop=0, quality=78, method=4)
    return out


def compare_files(paths, labels, out, crop_h=530, max_frames=100):
    """Side-by-side comparison from per-model clip files (first frames aligned)."""
    seqs = []
    for p in paths:
        im = Image.open(p); fr = []
        for k in range(min(getattr(im, 'n_frames', 1), max_frames)):
            im.seek(k); fr.append(im.convert('RGB').crop((0, 0, 325, crop_h)))
        seqs.append(fr)
    n = min(len(s) for s in seqs); outf = []
    for k in range(n):
        C = Image.new('RGB', (len(seqs) * 329 - 4, crop_h + 18), (18, 18, 22)); d = ImageDraw.Draw(C)
        for j, (s, lab) in enumerate(zip(seqs, labels)):
            C.paste(s[k], (j * 329, 18)); d.text((j * 329 + 4, 2), lab, fill=(235, 235, 235), font=font())
        outf.append(C)
    outf[0].save(out, save_all=True, append_images=outf[1:], duration=int(1000 / FPS), loop=0, quality=78, method=4)
    return out


def engine_compare(sdir, out, seconds=3.4):
    """Firefox/WebKit: cut each presentation's segment from the context's recordVideo (25 fps, lossy VP8) and set
    them side by side. Segment times come from the capture's own wall-clock marks relative to context creation."""
    import subprocess, tempfile
    meta = json.load(open(os.path.join(sdir, 'meta.json'), encoding='utf8'))
    vid = os.path.join(sdir, meta.get('video') or 'clip.webm'); seqs, labels = [], []
    tmp = tempfile.mkdtemp(dir=os.path.dirname(out))
    for spec, rec in meta['models'].items():
        st = rec['videoStartMs'] / 1000.0
        pat = os.path.join(tmp, re.sub(r'[|:+~^@/.]', '_', spec) + '_%03d.png')
        subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-ss', '%.3f' % st, '-t', '%.2f' % seconds, '-i', vid, '-vf', 'fps=25', pat], check=True)
        fr = sorted(glob.glob(pat.replace('%03d', '*')))
        seqs.append([Image.open(p).convert('RGB').resize((325, 530)) for p in fr]); labels.append(spec)
        for p in fr:
            os.remove(p)
    os.rmdir(tmp)
    n = min(len(s) for s in seqs); outf = []
    for k in range(n):
        C = Image.new('RGB', (len(seqs) * 329 - 4, 548), (18, 18, 22)); d = ImageDraw.Draw(C)
        for j, (s, lab) in enumerate(zip(seqs, labels)):
            C.paste(s[k], (j * 329, 18)); d.text((j * 329 + 4, 2), ('current product' if lab == 'current' else lab) + ' [' + meta.get('engine', '?') + ']', fill=(235, 235, 235), font=font())
        outf.append(C)
    outf[0].save(out, save_all=True, append_images=outf[1:], duration=40, loop=0, quality=78, method=4)
    return out, n


def blind_from_anims(anim_dir, scene_rx, out_dir, key_file, seed=20261116, start=0.3, seconds=3.0):
    """Build an unlabelled pack from per-presentation clips (single process, fresh names, key written once).
    Clips are cut from the encoded per-presentation WebPs (25 fps), i.e. a second lossy encoding."""
    rnd = random.Random(seed); os.makedirs(out_dir, exist_ok=True)
    key = json.load(open(key_file, encoding='utf8')) if os.path.exists(key_file) else {}   # resumable; written after every clip
    done = {(v['scene'], v['model']) for v in key.values()}
    files = sorted(f for f in os.listdir(anim_dir) if re.search(scene_rx, f) and f.endswith('.webp') and '--compare' not in f)
    names = rnd.sample(range(10 ** 6), len(files))
    os.makedirs(os.path.dirname(os.path.abspath(key_file)), exist_ok=True)
    for f, n in zip(files, names):
        if tuple(f[:-5].split('--')) in done:
            continue
        im = Image.open(os.path.join(anim_dir, f)); a, b = int(start * FPS), int((start + seconds) * FPS); tl = []
        for k in range(getattr(im, 'n_frames', 1)):     # the encoder merges identical frames: expand by duration
            im.seek(k); rep = max(1, round(im.info.get('duration', 1000 / FPS) / (1000 / FPS))); fr0 = im.convert('RGB'); tl += [fr0] * rep
        tl += [tl[-1]] * max(0, b - len(tl))
        fr = tl[a:b]
        name = 'clip-%06d.webp' % n
        fr[0].save(os.path.join(out_dir, name), save_all=True, append_images=fr[1:], duration=int(1000 / FPS), loop=0, quality=85, method=4)
        sc, spec = f[:-5].split('--'); key[name] = {'scene': sc, 'model': spec, 'frames': len(fr)}
        json.dump(key, open(key_file, 'w', encoding='utf8'), indent=1)
    return len(key)
