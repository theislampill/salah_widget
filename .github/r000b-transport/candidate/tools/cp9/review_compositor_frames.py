"""Chromium screenshot/presentation clock reconciliation (diagnostic only).

Join by compositor source/sequence, never substitute expected_display_time for
presentation feedback. Thumbnails cannot qualify real stellar pixel contrast.
Run alongside the retained normal-1x source-frame review, not instead of it.
"""
import argparse, base64, hashlib, io, json
from pathlib import Path
from PIL import Image

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
        # Clock reconciliation has no automatic pixel authority. Inherited
        # iframe-coordinate/brightness heuristics mislabel direct H1 frames.
        # Retain thumbnails for explicit visual inspection and raw originals
        # for material/star qualification, with every missing join preserved.
        name = f'{len(rows):03}.png'
        image.save(out / name)
        match = presentations.get((args.get('source_id'), args.get('frame_sequence')), [])
        rows.append({'file': name, 'size': image.size, 'scene': None, 'moon': None,
                     'pixelReview': 'REQUIRES_EXPLICIT_VISUAL_REVIEW',
                     'stars': 'not qualified by thumbnail', 'captureMs': bracket(event['ts']),
                     'expectedDisplayMsEstimateOnly': bracket(args['expected_display_time']),
                     'presentationFeedbackMs': [bracket(t) for t in sorted(set(match))],
                     'sourceId': args.get('source_id'), 'frameSequence': args.get('frame_sequence')})
    result = {'schema': 'compositor-clock-review/1', 'mode': mode,
              'sourceTraceSha256': hashlib.sha256(path.read_bytes()).hexdigest(),
              'clockBracketWidthMs': after - before, 'navigationAbsolute': run['navigationAbsolute'],
              'limitations': 'Instrumented headless compositor feedback, not physical monitor photons. '
                            'Thumbnail scene/Moon annotations require explicit visual inspection. Stars require normal-1x source frames. '
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
