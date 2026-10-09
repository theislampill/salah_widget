"""Check every GitHub source/evidence link and line range before publication."""
from pathlib import Path
from urllib.parse import unquote, urlsplit
import argparse, hashlib, json, re, subprocess

R = Path(__file__).resolve().parent
W = Path(r'C:\Users\theis\.codex\worktrees\hotfix-startup-clouds\salah_widget')
PREFIX = 'docs/rlgwo-audit/20261008/'
ap = argparse.ArgumentParser()
ap.add_argument('--staging', type=Path)
ap.add_argument('--comments', type=Path)
args = ap.parse_args()
comments = sorted(args.comments.glob('*.md')) if args.comments else sorted((R/'workers').glob('*/*-comment.md'))
cache, issues, count = {}, [], 0
for comment in comments:
    body = comment.read_text(encoding='utf-8')
    for rawurl in re.findall(r'https://(?:github\.com|raw\.githubusercontent\.com)/theislampill/salah_widget/[^\s)<>`]+', body):
        url = urlsplit(rawurl.rstrip('.,;'))
        bits = unquote(url.path).split('/')
        if bits[3] in ('issues', 'pull', 'actions', 'compare'):
            continue
        if url.netloc == 'raw.githubusercontent.com':
            ref, path, kind = bits[3], '/'.join(bits[4:]), 'blob'
        elif bits[3] in ('blob','tree'):
            kind, ref, path = bits[3], bits[4], '/'.join(bits[5:])
        else:
            continue
        key = (ref, path, kind)
        count += 1
        if key not in cache:
            if ref == 'AUDIT_EVIDENCE_COMMIT':
                assert path.startswith(PREFIX), path
                loc = args.staging/path if args.staging else R/path[len(PREFIX):]
                if not loc.exists():
                    cache[key] = (None, 'MISSING')
                else:
                    cache[key] = (loc.read_bytes() if loc.is_file() else b'', 'blob' if loc.is_file() else 'tree')
            else:
                p = subprocess.run(['git','cat-file','-t',f'{ref}:{path}'], cwd=W, capture_output=True)
                typ = p.stdout.decode().strip() if p.returncode == 0 else 'MISSING'
                q = subprocess.run(['git','show',f'{ref}:{path}'], cwd=W, capture_output=True) if typ == 'blob' else None
                cache[key] = (q.stdout if q else None, typ)
        data, typ = cache[key]
        if typ != kind:
            issues.append({'comment':str(comment.relative_to(R)), 'url':rawurl, 'problem':f'expected {kind}, found {typ}'})
        line = re.fullmatch(r'L(\d+)(?:-L(\d+))?', url.fragment)
        if line and data is not None and typ == 'blob':
            end = int(line.group(2) or line.group(1))
            if not 1 <= int(line.group(1)) <= end <= len(data.splitlines()):
                issues.append({'comment':str(comment.relative_to(R)), 'url':rawurl, 'problem':f'line range beyond {len(data.splitlines())}'})
report = {'comments':len(comments), 'references':count, 'distinctTargets':len(cache), 'problems':issues}
(R/'publication-link-check.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))
raise SystemExit(bool(issues))
