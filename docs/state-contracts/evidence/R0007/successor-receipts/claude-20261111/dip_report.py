"""Summarise centre/rows web-font text dips per run. Usage: python -I dip_report.py DIR [prefix]"""
import glob, json, os, sys
rows = []
for d in sorted(glob.glob(os.path.join(sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else '') + '*'))):
    if not os.path.exists(d + '/series.json'): continue
    s = json.load(open(d + '/series.json'))['series']; t = json.load(open(d + '/trace.json'))
    c = [x['centre'] for x in s]; base = sorted(c[-20:])[10]
    f = next((i for i, x in enumerate(c) if 0.6 * base <= x <= 1.5 * base), None)
    if f is None: print(os.path.basename(d), 'INVALID (never populated)'); continue
    dips = [i + 1 for i in range(f, len(c)) if c[i] < 0.5 * base]
    ev = {e['kind']: e['t'] for e in t['fontLog'] if 'kind' in e}
    mono = [x['mono'] for x in s]; mb = sorted(mono[-20:])[10]
    monodips = [i + 1 for i in range(f, len(c)) if mono[i] < 0.5 * mb]
    print(os.path.basename(d), '| firstPopulated', f + 1, '| webfontDipFrames', (f'{dips[0]}-{dips[-1]} n={len(dips)}' if dips else 'none'), '| monoDips', len(monodips),
          '| loading@', ev.get('fonts.loading'), 'done@', ev.get('fonts.loadingdone'), 'applied@', ev.get('webfonts.applied'), '| faces loaded', sum('|loaded|' in x for x in t['faces']), '| final .cn', t['used'][0][4:14])
