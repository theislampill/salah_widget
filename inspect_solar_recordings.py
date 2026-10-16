"""Read original existing source JPEGs; rank changes, never declare a flicker pass."""
from pathlib import Path
from PIL import Image, ImageStat, ImageDraw
import datetime, hashlib, io, json

O = Path(__file__).resolve().parent
OUT = O / 'solar-flicker-recordings-r1'
assert not OUT.exists()
OUT.mkdir()
cases = ['chromium-day-dpr1-r3', 'firefox-day-dpr1-r3',
         'chromium-dawn-dpr2-r3', 'firefox-dawn-dpr2-r3']
# Coordinates refer to original source JPEG pixels. They select broad regions,
# not calibrated device-resolution measurements or the exact solar silhouette.
regions = {'solar_core': (12, 55, 60, 90), 'solar_edge': (86, 60, 122, 105),
           'sky_control': (252, 65, 300, 105), 'lower_control': (240, 460, 290, 485)}
sha = lambda b: hashlib.sha256(b).hexdigest()
results = []
for name in cases:
    root = O / 'native' / name
    raw_result = (root / 'results.json').read_bytes()
    result = json.loads(raw_result)
    run = result['runs'][0]
    video = Path(run['video'])
    side = video.with_name(video.name + '.frames.jsonl')
    frames = video.with_name(video.name + '.frames')
    source = [json.loads(line) for line in side.read_text().splitlines() if line.strip()]
    rows = []
    previous = None
    for record in source:
        t = record['receiptUtcMs'] - run['navigationAbsolute']
        if not 0 <= t <= run['elapsedMs']: continue
        path = frames / record['file']
        data = path.read_bytes()
        assert len(data) == record['bytes'], path
        im = Image.open(io.BytesIO(data)).convert('RGB')
        samples = {key: ImageStat.Stat(im.crop(box)).mean for key, box in regions.items()}
        means = {key: sum(value) / 3 for key, value in samples.items()}
        row = {**record, 'relativeReceiptMs': t, 'path': str(path.relative_to(O)),
               'sha256': sha(data), 'dimensions': list(im.size), 'meanCode': means,
               'meanRGB': samples, 'sourceGapMs': None, 'deltas': None}
        if previous:
            row['sourceGapMs'] = 1000 * (record['sourceTimeSeconds'] - previous['sourceTimeSeconds'])
            row['deltas'] = {key: means[key] - previous['meanCode'][key] for key in means}
        rows.append(row); previous = row
    caseout = OUT / name
    caseout.mkdir()
    (caseout / 'frame-observations.jsonl').write_text(''.join(json.dumps(row) + '\n' for row in rows))
    settled = [row for row in rows if row['relativeReceiptMs'] >= 2000 and row['deltas']]
    ranked = sorted(settled, key=lambda row: abs(row['deltas']['solar_core']), reverse=True)[:8]
    # Every selected change is shown with its actual adjacent source frames.
    indices = {rows.index(row) for row in ranked}
    selected = sorted({j for i in indices for j in [max(0, i-1), i, min(len(rows)-1, i+1)]})
    thumbs = []
    for i in selected:
        row = rows[i]
        im = Image.open(O / row['path']).convert('RGB')
        tile = Image.new('RGB', (195, 244), '#ececec')
        tile.paste(im.crop((0, 0, 195, 210)), (0, 34))
        draw = ImageDraw.Draw(tile)
        draw.text((4, 2), f"seq {row['seq']} receipt {row['relativeReceiptMs']/1000:.3f}s", fill='black')
        draw.text((4, 17), f"core={row['meanCode']['solar_core']:.2f}", fill='black')
        thumbs.append(tile)
    sheet = Image.new('RGB', (195*6, 244*((len(thumbs)+5)//6)), 'white')
    for i, tile in enumerate(thumbs): sheet.paste(tile, ((i%6)*195, (i//6)*244))
    sheet.save(caseout / 'ranked-change-context.png')
    summary = {'case': name, 'resultSha256': sha(raw_result), 'sidecarSha256': sha(side.read_bytes()),
               'runtime': result['runtime']['treeSha256'], 'scene': result['scene'],
               'entry': result['entry'], 'stamp': result['stamp'], 'syntheticWeather': result['syntheticWeather'],
               'viewport': result.get('viewport', {'width':390,'height':600}), 'dpr': result['dpr'],
               'durationMs': run['elapsedMs'], 'sourceFramesInspectedNumerically': len(rows),
               'recordedSourceDimensions': sorted({tuple(row['dimensions']) for row in rows}),
               'finalSunEl': run['final']['qa']['sunEl'],
               'finalSky': {key: run['final']['sky'].get(key) for key in
                            ['status','renders','presentationDraws','presentationSkips','presentationRejections','rejections','errors']},
               'settledCoreRange': [min(row['meanCode']['solar_core'] for row in settled), max(row['meanCode']['solar_core'] for row in settled)],
               'settledMaxSourceGapMs': max(row['sourceGapMs'] for row in settled),
               'rankedChanges': [{key: row[key] for key in ['seq','relativeReceiptMs','path','sha256','sourceGapMs','meanCode','deltas']} for row in ranked],
               'selectedOriginals': [rows[i]['path'] for i in selected],
               'contactSheet': str((caseout/'ranked-change-context.png').relative_to(O)),
               'verdict': 'NUMERICAL_SELECTION_ONLY_REQUIRES_ORIGINAL_PIXEL_INSPECTION'}
    (caseout/'RESULT.json').write_text(json.dumps(summary, indent=2)+'\n')
    results.append(summary)
report = {'schema':'r0021-existing-solar-recording-inspection/v1',
          'atUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'purpose':'Investigate owner-observed Sun strobe within existing R0021 temporal continuity. No source or browser mutation; no new acquisition.',
          'regionsOriginalPixels':regions, 'cases':results,
          'limits':'Receipt-relative times are sample-selection labels, not calibrated presentation. JPEG/recording path and source gaps retain original limitations. ROI averages locate candidate changes only; they neither establish cause nor prove absence of intermittent flicker. Dawn may be a Sun-absent negative control, not sunrise. No exact worker publication time stream exists in these uninstrumented runs.'}
(OUT/'RESULTS.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'output':str(OUT),'sha256':sha((OUT/'RESULTS.json').read_bytes()),'cases':[{'case':r['case'],'frames':r['sourceFramesInspectedNumerically'],'sunEl':r['finalSunEl'],'range':r['settledCoreRange'],'maxSourceGapMs':r['settledMaxSourceGapMs'],'top':r['rankedChanges'][:2]} for r in results]}))
