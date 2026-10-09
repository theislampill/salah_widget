"""Validate D's public-compatible packets and source link bounds, read-only."""
import hashlib
import json
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).parent
ROOT = Path(r'C:\Users\theis\.codex\worktrees\hotfix-startup-clouds\salah_widget')
SHA = '18ff14860ff41c084b1db5f396bb62aa9c22b1be'
counts = {15: 21, 16: 14, 17: 19, 18: 14, 31: 16, 35: 25}
rows = []
for issue, count in counts.items():
    ap, cp = HERE / f'{issue}-assessment.json', HERE / f'{issue}-comment.md'
    packet = json.loads(ap.read_text(encoding='utf-8'))
    text = cp.read_text(encoding='utf-8')
    matrix = packet.get('requirementMatrix', packet.get('matrix'))
    assert matrix is not None and len(matrix) == count, (issue, packet.keys())
    canonical = f'R{issue:04X}'
    assert text.count(f'<!-- RLGWO-AUDIT:{SHA}:{canonical}:2026-10-08 -->') == 1
    assert len(cp.read_bytes()) < 65536
    assert packet['recommendation'] == ('CLOSE — SATISFIED WITH DEMONSTRATED IMPROVEMENTS' if issue in [15, 18, 31] else 'LEAVE OPEN')
    for match in re.finditer(r'https://github.com/theislampill/salah_widget/blob/' + SHA + r'/([^\s]+?)#L(\d+)-L(\d+)', text):
        relative, start, end = match.groups()
        lines = (ROOT / relative).read_text(encoding='utf-8-sig').splitlines()
        assert 1 <= int(start) <= int(end) <= len(lines), (issue, relative, start, end, len(lines))
    definitions = set(re.findall(r'^\[([^\]]+)\]: ', text, re.M))
    references = set(re.findall(r'\[[^\]]+\]\[([^\]]+)\]', text))
    assert references <= definitions, (issue, references - definitions)
    assert 'DELIVERED_VERIFIED' in text and 'gpt-6.1-sol, effort max' in text
    rows.append({'issue': issue, 'obligations': count, 'assessmentSha256': hashlib.sha256(ap.read_bytes()).hexdigest(), 'commentSha256': hashlib.sha256(cp.read_bytes()).hexdigest(), 'commentBytes': len(cp.read_bytes()), 'sourceLinksValid': True, 'markerValid': True})
dirty = subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True)
assert dirty == '', dirty
result = {'status': 'PASS', 'target': SHA, 'obligations': sum(counts.values()), 'outputs': rows, 'productionDirtyPaths': [], 'limits': 'Structural/content/source-boundary validation; native browser/visual checks are separately attributed to primary.'}
(HERE / 'output-validation.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result))
