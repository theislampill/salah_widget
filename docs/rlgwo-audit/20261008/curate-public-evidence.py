"""Create a new immutable docs-only evidence staging directory; never edits runtime."""
from pathlib import Path
import argparse, gzip, hashlib, json, re, shutil

ROOT = Path(__file__).resolve().parent
PREFIX = 'docs/rlgwo-audit/20261008'
TARGET = '18ff14860ff41c084b1db5f396bb62aa9c22b1be'

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    out = args.out.resolve()
    if out.exists():
        raise SystemExit('New staging directory required; existing evidence is never overwritten')
    out.mkdir(parents=True)
    records = []
    allowed = {'.json', '.jsonl', '.log', '.tap', '.txt', '.md', '.py', '.cjs', '.mjs', '.html', '.js', '.png', '.gz', '.ps1', '.sh'}
    top = {'release.json', 'initial-inventory.json', 'raw-open-items.json', 'merge-preconditions.json',
           'public-runtime.json', 'public-browser-summary.json', 'public-document-distribution.json',
           'reviewer-model-settings.json', 'pages-poll.json', 'v1-verifier.log', 'WORKER_BRIEF.md',
           'public-smoke.py', 'snapshot.py', 'verify-delivered.py', 'docs-contract-primary.json',
           'primary-reconciliation.json', 'primary-visual-review.json', 'owner-amendments.json',
           'curate-public-evidence.py', 'publish-reviewed-issue.py', 'README.md',
           'assemble-reconciliation.py', 'prepare-final-evidence.py', 'check-publication-links.py',
           'publication-link-check.json'}
    for src in sorted(ROOT.rglob('*')):
        if not src.is_file():
            continue
        rel = src.relative_to(ROOT)
        if any(x in {'__pycache__', '.git', 'node_modules', 'profiles', 'profile', 'public-staging'} or x.startswith('public-evidence-') for x in rel.parts):
            continue
        first = rel.parts[0]
        selected = (len(rel.parts) == 1 and src.name in top) or first in {'issues', 'starting-state', 'workers'} or first.startswith(('public-chromium', 'public-firefox', 'primary-native-'))
        if not selected or src.suffix.lower() not in allowed:
            continue
        # Reconciled matrices accompany their inspectable receipts. Final posted
        # comment copies and effect ledger follow in a second docs-only commit.
        if src.name.endswith('-comment.md'):
            continue
        # Workers' generated fixture pages are explicitly labelled test material.
        # Compress large textual receipts losslessly; PNGs remain actual pixels.
        raw = src.read_bytes()
        destrel = rel.as_posix()
        compression = src.suffix != '.png' and src.suffix != '.gz' and len(raw) > 2_000_000
        public = gzip.compress(raw, mtime=0) if compression else raw
        if compression:
            destrel += '.gz'
        dest = out / PREFIX / destrel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(public)
        records.append({'source': rel.as_posix(), 'published': f'{PREFIX}/{destrel}', 'sourceBytes': len(raw),
                        'sourceSha256': hashlib.sha256(raw).hexdigest(), 'publishedBytes': len(public),
                        'publishedSha256': hashlib.sha256(public).hexdigest(), 'compression': 'gzip' if compression else None})
    manifest = {'target': TARGET, 'purpose': 'Issue-specific audit evidence; no runtime modification or new release',
                'privacy': 'Public city/axis fixtures and isolated test stores; no owner precise coordinates, profiles, credentials or font files.',
                'records': records}
    (out / PREFIX / 'EVIDENCE_MANIFEST.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'out': str(out), 'files': len(records), 'bytes': sum(x['publishedBytes'] for x in records)}))

if __name__ == '__main__':
    main()
