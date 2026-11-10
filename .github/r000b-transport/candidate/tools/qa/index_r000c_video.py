"""Index untouched R000C native video and decode review crops, without browser calls.

Every frame is inventoried. Measurements nominate frames for visual review; they
are not a motion, readability or continuity PASS. The original video is retained.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import numpy as np
from PIL import Image, ImageDraw


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('case', type=Path)
    args = p.parse_args()
    root = args.case
    receipt = json.loads((root / 'receipt.json').read_bytes())
    video = root / receipt['video']['file']
    assert sha(video.read_bytes()) == receipt['video']['sha256']
    probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0',
        '-show_entries', 'stream=width,height:frame=best_effort_timestamp_time', '-of', 'json', str(video)]))
    width, height = probe['streams'][0]['width'], probe['streams'][0]['height']
    times = [float(f['best_effort_timestamp_time']) for f in probe['frames']]
    assert [width, height] == [390, 600]
    out = root / 'pixel-review'
    out.mkdir(exist_ok=False)
    candidates = {0, len(times) - 1}
    candidates.update(min(range(len(times)), key=lambda i: abs(times[i] - sec)) for sec in range(1, int(times[-1]) + 1))
    # All decoded originals remain in video; bounded 1-second native-size samples
    # plus every visually suspect frame are exported losslessly below.
    command = ['ffmpeg', '-v', 'error', '-i', str(video), '-vsync', '0', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-']
    process = subprocess.Popen(command, stdout=subprocess.PIPE)
    rows, samples, previous = [], [], None
    frame_bytes = width * height * 3
    while True:
        data = process.stdout.read(frame_bytes)
        if not data:
            break
        if len(data) != frame_bytes:
            raise ValueError('Truncated decoded original frame')
        i = len(rows)
        arr = np.frombuffer(data, np.uint8).reshape(height, width, 3)
        card = arr[:530, :325]
        regions = {'card': card, 'header': arr[16:43, 60:220], 'footer': arr[500:525, 20:305],
                   'cloud': arr[85:210, 20:305], 'moon': arr[35:125, 220:310]}
        stats = {key: {'std': float(value.std()), 'mean': float(value.mean())} for key, value in regions.items()}
        row = {'ordinal': i, 'ptsSeconds': times[i], 'decodedRgbSha256': sha(data), 'regions': stats,
               'previousCloudMae': None if previous is None else float(np.abs(regions['cloud'].astype(float) - previous).mean())}
        previous = regions['cloud'].astype(float)
        rows.append(row)
        # Retain low-information full/partial frames, even if outside the watch.
        suspect = stats['card']['std'] < 5 or stats['footer']['std'] < 3 or stats['header']['std'] < 3
        if i in candidates or suspect:
            im = Image.frombytes('RGB', (width, height), data)
            name = f'frame-{i:05}.png'
            im.save(out / name)
            samples.append({'ordinal': i, 'ptsSeconds': times[i], 'file': name, 'suspect': suspect})
    if process.wait() or len(rows) != len(times):
        raise ValueError('Decode did not cover every original frame')
    # Native-sized samples permit text/opacity inspection; sheets are navigation.
    for start in range(0, len(samples), 24):
        batch = samples[start:start + 24]
        sheet = Image.new('RGB', (195 * 6, 322 * ((len(batch) + 5) // 6)), (230, 230, 230))
        for j, sample in enumerate(batch):
            im = Image.open(out / sample['file'])
            tile = Image.new('RGB', (195, 322), 'white')
            tile.paste(im.resize((195, 300)), (0, 22))
            ImageDraw.Draw(tile).text((2, 3), f"{sample['ordinal']} / {sample['ptsSeconds']:.2f}s", fill='black')
            sheet.paste(tile, ((j % 6) * 195, (j // 6) * 322))
        sheet.save(out / f'overview-{start // 24:02}.jpg', quality=92)
    last = Image.open(out / f'frame-{len(rows)-1:05}.png')
    for name, box in {'card': (0, 0, 325, 530), 'header': (0, 0, 325, 55),
                      'footer': (10, 493, 315, 530), 'cloud': (0, 65, 325, 245),
                      'moon': (205, 25, 325, 140)}.items():
        last.crop(box).save(out / (name + '.png'))
    index = {'schema': 'r000c-original-video-index/v1', 'videoSha256': receipt['video']['sha256'],
             'receiptSha256': sha((root / 'receipt.json').read_bytes()), 'size': [width, height],
             'durationPts': times[-1], 'frameCount': len(rows), 'samples': samples, 'frames': rows,
             'limitation': __doc__}
    (out / 'index.json').write_text(json.dumps(index, indent=2) + '\n', encoding='utf8')
    print(root.name, len(rows), 'frames;', len(samples), 'exported; suspect', sum(s['suspect'] for s in samples))


if __name__ == '__main__':
    main()
