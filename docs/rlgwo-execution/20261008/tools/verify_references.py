"""Check immutable repository file references and new-package relative links.

This is an availability/line-range check, not a claim that a linked test passed.
Existing commit objects must be available in the supplied repository. Remote
publication/readback is separately recorded by the primary publisher.
"""
from pathlib import Path, PurePosixPath
import argparse
import hashlib
import json
import re
import subprocess
from urllib.parse import unquote

REPO_PREFIX = 'docs/rlgwo-execution/20261008/'
IMMUTABLE = re.compile(r'https://github\.com/theislampill/salah_widget/(?:blob|tree)/([0-9a-f]{40}|SPEC_EVIDENCE_COMMIT)/([^\s)<>#]+)(?:#L(\d+)(?:-L(\d+))?)?')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    p.add_argument('--repository', type=Path, required=True)
    p.add_argument('--output', type=Path)
    args = p.parse_args()
    root = args.root.resolve()
    cache, checked, errors, relatives = {}, [], [], []
    for file in sorted(root.rglob('*.md')):
        if any(x in file.relative_to(root).parts for x in ('staging', 'publication', 'contracts', 'workers')):
            continue
        text = file.read_text(encoding='utf-8-sig')
        for rel in re.findall(r'\]\(([^\s)]+)\)',text):
            if rel.startswith(('https:','http:','#','mailto:','codex:')):
                continue
            target=(file.parent/unquote(rel.split('#',1)[0])).resolve()
            relatives.append({'file':file.relative_to(root).as_posix(),'target':rel,'available':target.exists()})
            if not target.exists():
                errors.append({'file':file.relative_to(root).as_posix(),'url':rel,'reason':'Relative package target absent'})
        for match in IMMUTABLE.finditer(text):
            commit, path, start, end = match.groups()
            path = unquote(path.rstrip('.,;'))
            key = (commit, path)
            if key not in cache:
                if commit == 'SPEC_EVIDENCE_COMMIT':
                    target = root / path[len(REPO_PREFIX):] if path.startswith(REPO_PREFIX) else None
                    if not target or not target.exists():
                        cache[key] = {'available': False, 'reason': 'New package target absent'}
                    else:
                        raw = target.read_bytes() if target.is_file() else b''
                        cache[key] = {'available': True, 'lines': len(raw.splitlines()), 'sha256': hashlib.sha256(raw).hexdigest() if target.is_file() else None}
                else:
                    cmd = subprocess.run(['git', 'cat-file', '-t', f'{commit}:{path}'], cwd=args.repository, capture_output=True)
                    if cmd.returncode:
                        cache[key] = {'available': False, 'reason': cmd.stderr.decode(errors='replace').strip()}
                    elif cmd.stdout.strip() == b'tree':
                        cache[key] = {'available': True, 'lines': 0, 'tree': True}
                    else:
                        raw = subprocess.check_output(['git', 'show', f'{commit}:{path}'], cwd=args.repository)
                        cache[key] = {'available': True, 'lines': len(raw.splitlines()), 'sha256': hashlib.sha256(raw).hexdigest()}
            result = cache[key]
            if not result['available']:
                errors.append({'file': file.relative_to(root).as_posix(), 'url': match.group(), 'reason': result['reason']})
            elif start and (int(start) < 1 or int(end or start) > result['lines'] or int(end or start) < int(start)):
                errors.append({'file': file.relative_to(root).as_posix(), 'url': match.group(), 'reason': f'Invalid line range in {result["lines"]}-line file'})
            checked.append({'file': file.relative_to(root).as_posix(), 'commit': commit, 'path': path, 'start': start, 'end': end})
    report = {'kind': 'Immutable repository reference availability and line ranges', 'references': len(checked),
              'distinctTargets': len(cache), 'errors': errors, 'result': 'PASS' if not errors else 'FAIL',
              'checked': checked, 'relativeLinks':relatives, 'objects': [{'commit': k[0], 'path': k[1], **v} for k, v in cache.items()],
              'scope': 'Git object availability/new package presence; public branch/head and issue-comment readback checked separately. No runtime evidence is inferred.'}
    out = args.output or root / 'REFERENCE_VALIDATION.json'
    out.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: report[k] for k in ('result', 'references', 'distinctTargets', 'errors')}))
    raise SystemExit(0 if not errors else 1)


if __name__ == '__main__':
    main()
