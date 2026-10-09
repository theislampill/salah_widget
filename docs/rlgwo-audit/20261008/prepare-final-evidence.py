"""Preserve externally retained receipts and primary rendered-pixel review."""
from pathlib import Path
import hashlib, json

ROOT = Path(__file__).resolve().parent
def dump(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

manifest = json.loads((ROOT/'workers/E/publication-ready.json').read_text(encoding='utf-8'))
copies = []
for item in manifest['receiptSourcesForPrimaryPublication']:
    if 'name' not in item:
        continue
    src = Path(item['path'])
    raw = src.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == item['sha256']
    dst = ROOT/'workers/E/retained-install'/item['name']
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        assert dst.read_bytes() == raw
    else:
        dst.write_bytes(raw)
    copies.append({'source': str(src), 'publishedRelativePath': dst.relative_to(ROOT).as_posix(),
                   'sha256': item['sha256'], 'provenance': item['provenance']})
dump(ROOT/'workers/E/retained-install/CUSTODY.json', {'receipts': copies, 'note': 'Exact historical bytes copied, not newly executed.'})

review = json.loads((ROOT/'primary-visual-review.json').read_text(encoding='utf-8'))
new = [
    {'evidence': 'workers/D/native-rest-primary/31-widget-native-fail.png',
     'finding': 'After both transport attempts fail, the current manual target has usable prayer rows and an intact footer. Actual native stream abort/fallback counts and socket-close evidence are separate in results.json.',
     'disposition': 'satisfies bounded manual recovery/layout readback'},
    {'evidence': 'workers/D/native-three-primary/18-denied-copy-responsive-Windows-payload.png',
     'finding': 'At390px viewport, denied clipboard action exposes the selected, readonly Windows payload with honest failure instructions and no horizontal overflow. Browser selection is real; clipboard and Win32 platform are controlled doubles, not actual owner clipboard or installer execution.',
     'disposition': 'satisfies actual-button/manual-selection responsive readback'},
    {'evidence': 'workers/D/native-three-primary/15-settings-display-close-session.png',
     'finding': 'The325x530 settings panel keeps its inputs and status within the card; the idless footer heart has visible focus. Receipt verifies stale held search/GPS callbacks did not change the current edited/closed-reopened session.',
     'disposition': 'satisfies native settings/session visual bridge'}
]
seen = {x['evidence'] for x in review['observations']}
for item in new:
    assert (ROOT/item['evidence']).is_file()
    if item['evidence'] not in seen:
        review['observations'].append(item)
dump(ROOT/'primary-visual-review.json', review)
print(json.dumps({'retainedReceipts':len(copies),'primaryVisualObservations':len(review['observations'])}))
