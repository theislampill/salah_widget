"""Chromium screenshot/presentation clock reconciliation (diagnostic only).

Join by compositor source/sequence, never substitute expected_display_time for
presentation feedback. Thumbnails cannot qualify real stellar pixel contrast.
Run alongside the retained normal-1x source-frame review, not instead of it.
"""
import argparse, base64, hashlib, io, json
from pathlib import Path
from PIL import Image, ImageStat

def review(directory, mode):
    run = next(r for r in json.loads((directory / 'results.json').read_text())['runs'] if r['mode'] == mode)
    path = directory / (mode + '-filmstrip.json')
    trace = json.loads(path.read_text())
    before, after, mono = trace['clock']
    def bracket(us):
        return [us / 1000 - mono * 1000 + t - run['navigationAbsolute'] for t in (before, after)]
    presentations = {}
    for event in trace['events']:
        if event['name'] == 'AnimationFrame::Presentation':
            frame = event.get('args', {}).get('begin_frame_id', {})
            presentations.setdefault((frame.get('source_id'), frame.get('sequence_number')), []).append(event['ts'])
    out = directory / ('compositor-review-' + mode)
    out.mkdir(exist_ok=True)
    rows = []
    for event in trace['events']:
        if event['name'] != 'Screenshot' or bracket(event['ts'])[0] > 1500:
            continue
        args = event['args']
        image = Image.open(io.BytesIO(base64.b64decode(args['snapshot']))).convert('RGB')
        # Fixed clear-night diagnostic only. Normal 1x source JPEGs retain the
        # actual footprint; this scaled thumbnail proves no stellar detail.
        sx, sy = image.width / 390, image.height / 600
        region = lambda box: tuple(round(n * (sx if i % 2 == 0 else sy)) for i, n in enumerate(box))
        sample = image.getpixel((round(170 * sx), round(80 * sy)))
        scene = 60 < min(sample) < 210
        moon_region = ImageStat.Stat(image.crop(region((245, 25, 305, 90))))
        moon = scene and sum(moon_region.mean) / 3 > 95 and sum(moon_region.stddev) / 3 > 8
        name = f'{len(rows):03}.png'
        image.save(out / name)
        match = presentations.get((args.get('source_id'), args.get('frame_sequence')), [])
        rows.append({'file': name, 'size': image.size, 'scene': scene, 'moon': moon,
                     'stars': 'not qualified by thumbnail', 'captureMs': bracket(event['ts']),
                     'expectedDisplayMsEstimateOnly': bracket(args['expected_display_time']),
                     'presentationFeedbackMs': [bracket(t) for t in sorted(set(match))],
                     'sourceId': args.get('source_id'), 'frameSequence': args.get('frame_sequence')})
    result = {'schema': 'compositor-clock-review/1', 'mode': mode,
              'sourceTraceSha256': hashlib.sha256(path.read_bytes()).hexdigest(),
              'clockBracketWidthMs': after - before, 'navigationAbsolute': run['navigationAbsolute'],
              'limitations': 'Instrumented headless compositor feedback, not physical monitor photons. '
                            'Thumbnail Moon annotation must be visually inspected. Stars require normal-1x source frames. '
                            'Missing or multiple feedback joins do not establish a unique presentation time.',
              'frames': rows}
    (out / 'receipt.json').write_text(json.dumps(result, indent=2) + '\n')
    return result

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('directory', type=Path)
    parser.add_argument('--mode', default='cold')
    args = parser.parse_args()
    result = review(args.directory, args.mode)
    print(json.dumps(next((f for f in result['frames'] if f['moon']), None), indent=2))
