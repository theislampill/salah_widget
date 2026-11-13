#!/usr/bin/env python3
"""R0028 G-14 readback: re-read every comment cited in docs/state-contracts/CLOSURE_INDEX.md.

Read-only GitHub API calls through the authenticated `gh` CLI. For each cited comment the first
line must start with the indexed marker and, where a bound commit is indexed, carry that SHA.
Prints one line per comment and a JSON summary; exit 0 only when every readback agrees.
"""
from pathlib import Path
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
REPO = 'theislampill/salah_widget'


def table(text, heading):
    start = text.index('\n## ' + heading + '\n')
    end = text.find('\n## ', start + 1)
    lines = [line for line in text[start:end if end > 0 else None].split('\n') if line.startswith('| ')]
    header = [cell.strip() for cell in lines[0].split('|')[1:-1]]
    return [dict(zip(header, (cell.strip() for cell in line[2:-2].split(' | ')))) for line in lines[1:]]


def first_line(comment):
    result = subprocess.run(['gh', 'api', 'repos/' + REPO + '/issues/comments/' + comment, '--jq', '.body'],
                            capture_output=True, text=True, encoding='utf-8', timeout=60, check=False)
    if result.returncode != 0:
        return None
    return result.stdout.split('\n', 1)[0]


def main():
    text = (ROOT / 'docs/state-contracts/CLOSURE_INDEX.md').read_text(encoding='utf-8')
    rows = table(text, 'Certificates') + table(text, 'Withdrawals, corrections and reopenings')
    failures = []
    for row in rows:
        marker = row['Marker'].strip('`') if row.get('Marker', '-') != '-' else ''
        bound = row.get('Bound commit', '-')
        line = first_line(row['Comment'])
        ok = line is not None and line.startswith(marker) and (bound in ('-', '') or bound in line)
        print(('OK  ' if ok else 'BAD ') + row['WO'] + ' ' + row['Kind'] + ' ' + row['Comment'] + ' :: ' + (line or '<unreadable>')[:120])
        if not ok:
            failures.append(row['Comment'])
    print(json.dumps({'comments': len(rows), 'failures': failures}))
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
