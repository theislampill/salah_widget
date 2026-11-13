#!/usr/bin/env python3
"""R002A delivery-identity readback (issue 91 section 4.2, ISM-BLD-004). Read-only; Python stdlib plus `gh`.

Reads the public GitHub Pages bytes back against the blobs of one merged commit and writes a receipt. It
never builds, deploys, changes settings or comments.

States: awaiting-build -> built(commit) | errored -> reading-back -> identical | mismatch | inconclusive.

Guard: `gh api repos/<repo>/pages/builds/latest` must report status `built` for exactly the requested
commit; otherwise the verdict is `inconclusive`, never `identical` (a bounded --wait-build may poll first).

Readback set, derived from the commit's tree (never hard-coded): the root entries (index.html, offline.html,
config.js, builder.html); every file listed by the commit's R0029 inventory GENERATED.json, and the inventory
itself; install.sh and install.ps1; presets/*; v1/*; any --extra-path. Before comparison every path that
Jekyll does not publish is dropped and listed as `not-published` (the commit's own _config.yml `exclude`
string prefixes, Jekyll's default excludes, and any path component starting with '.' or '_', using R002B's
tools/pages_payload.py filter). The README review-first raw URLs (INSTALL_COMMIT / $InstallCommit) are compared
with the blob at their pinned commit; the unpinned `main` raw routes are compared with this commit's blob only
while `main` still points at this commit (otherwise recorded as `skipped`).

Comparison: SHA-256 of the served bytes against the Git blob. Fetches are bounded (file count, per-file and
total bytes, per-request timeout). A failing path is retried inside a bounded CDN window (--retry-window),
with a cache-busting query on retries; every attempt is recorded. HTTP 404 on a published path after the
window is `absent` (a mismatch); other HTTP or network failures are `inconclusive`.

Network: only theislampill.github.io, raw.githubusercontent.com (the project's own paths) and the GitHub API
through `gh`. Never a prayer, weather, radar, geocoding or location provider.

Exit codes: 0 identical, 1 mismatch, 2 inconclusive, 3 instrument error (bad input or repository state).
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pages_payload import config_excludes, jekyll_excluded  # noqa: E402  (R002B owns the published-path filter)

SCHEMA = 'salah-delivery-identity/1'
REPO = 'theislampill/salah_widget'
SITE = 'https://theislampill.github.io/salah_widget/'
RAW = 'https://raw.githubusercontent.com/' + REPO + '/'
ALLOWED_HOSTS = ('theislampill.github.io', 'raw.githubusercontent.com')
ROOT_ENTRIES = ('index.html', 'offline.html', 'config.js', 'builder.html')
INVENTORY = 'GENERATED.json'
INSTALLERS = ('install.sh', 'install.ps1')
TREE_PREFIXES = ('presets/', 'v1/')
# Jekyll's built-in `exclude` defaults (Jekyll 3.10/4.x Configuration DEFAULTS plus add_default_excludes).
# Matching them errs towards `not-published`, which only removes a path from comparison; it never passes one.
JEKYLL_DEFAULT_EXCLUDES = ('.sass-cache', '.jekyll-cache', 'gemfiles', 'Gemfile', 'Gemfile.lock', 'node_modules',
                           'vendor/bundle/', 'vendor/cache/', 'vendor/gems/', 'vendor/ruby/')
RAW_RE = re.compile(r'https://raw\.githubusercontent\.com/theislampill/salah_widget/'
                    r'(\$INSTALL_COMMIT|\$InstallCommit|main|[0-9a-f]{40})/(install\.(?:sh|ps1))')
README_VARS = {'$INSTALL_COMMIT': re.compile(r"INSTALL_COMMIT='([0-9a-f]{40})'"),
               '$InstallCommit': re.compile(r"\$InstallCommit = '([0-9a-f]{40})'")}
EXIT = {'identical': 0, 'mismatch': 1, 'inconclusive': 2, 'error': 3}


class InstrumentError(Exception):
    """Bad input or repository state; no verdict can be drawn (exit 3)."""


def now():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def git(root, *args):
    result = subprocess.run(['git', *args], cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        raise InstrumentError('git ' + ' '.join(args) + ': ' + result.stderr.decode('utf-8', 'replace').strip())
    return result.stdout


def blob_bytes(root, commit, path):
    return git(root, 'cat-file', 'blob', commit + ':' + path)


def tree_paths(root, commit):
    out = git(root, 'ls-tree', '-r', '-z', '--name-only', commit).decode('utf-8', 'replace')
    return [p for p in out.split('\0') if p]


def published(path, excludes):
    """(published?, reason) under the commit's own _config.yml and Jekyll's defaults."""
    if any(part.startswith(('.', '_')) for part in path.split('/')):
        return False, "path component starts with '.' or '_'"
    if jekyll_excluded(path, excludes):
        return False, '_config.yml exclude prefix'
    if jekyll_excluded(path, JEKYLL_DEFAULT_EXCLUDES):
        return False, 'Jekyll default exclude'
    return True, None


def readback_set(root, commit, extra=()):
    """Candidate paths (with their origin) and the commit's own excludes; derived from the tree."""
    paths = set(tree_paths(root, commit))
    config = blob_bytes(root, commit, '_config.yml').decode('utf-8') if '_config.yml' in paths else ''
    excludes = config_excludes(config)
    candidates, notes = {}, []
    for path in ROOT_ENTRIES + INSTALLERS:
        candidates[path] = 'root-entry' if path in ROOT_ENTRIES else 'installer'
    if INVENTORY in paths:
        inventory = json.loads(blob_bytes(root, commit, INVENTORY).decode('utf-8'))
        files = inventory.get('files')
        if not isinstance(files, dict) or not files:
            raise InstrumentError(INVENTORY + ' at ' + commit + ' has no files map')
        candidates[INVENTORY] = 'inventory'
        for path in sorted(files):
            candidates.setdefault(path, 'generated (' + INVENTORY + ')')
    else:
        notes.append(INVENTORY + ' absent at this commit: generated outputs beyond the root entries are not enumerated')
    for path in sorted(paths):
        if path.startswith(TREE_PREFIXES):
            candidates.setdefault(path, 'tree ' + path.split('/')[0] + '/*')
    for path in extra:
        candidates.setdefault(path, 'extra (--extra-path)')
    return candidates, excludes, paths, notes


def readme_raw_routes(root, commit, paths):
    """README raw installer URLs: [(url, blob commit, path, kind)] with variables resolved from README."""
    if 'README.md' not in paths:
        return []
    text = blob_bytes(root, commit, 'README.md').decode('utf-8', 'replace')
    values = {}
    for name, pattern in README_VARS.items():
        found = sorted(set(pattern.findall(text)))
        if len(found) > 1:
            raise InstrumentError('README.md at ' + commit + ' assigns ' + name + ' more than once: ' + repr(found))
        if found:
            values[name] = found[0]
    routes = []
    for ref, path in sorted(set(RAW_RE.findall(text))):
        if ref.startswith('$'):
            if ref not in values:
                raise InstrumentError('README.md uses ' + ref + ' without assigning it')
            routes.append((RAW + values[ref] + '/' + path, values[ref], path, 'raw-pinned'))
        elif ref == 'main':
            routes.append((RAW + 'main/' + path, commit, path, 'raw-main'))
        else:
            routes.append((RAW + ref + '/' + path, ref, path, 'raw-pinned'))
    return routes


# --- network (injectable for tests) ---------------------------------------------------------------

def gh_api(path):
    """Read-only GitHub API call through `gh` (uses GH_TOKEN/GITHUB_TOKEN or the gh login)."""
    try:
        result = subprocess.run(['gh', 'api', path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as error:
        return None, 'gh api unavailable: ' + str(error)
    if result.returncode != 0:
        return None, 'gh api ' + path + ' failed: ' + result.stderr.decode('utf-8', 'replace').strip()[:300]
    try:
        return json.loads(result.stdout), None
    except ValueError:
        return None, 'gh api ' + path + ' returned non-JSON'


def http_get(url, timeout, max_bytes):
    """(status, bytes or None, error). Bounded: refuses hosts outside the project and oversize bodies."""
    host = urllib.parse.urlsplit(url).hostname
    if host not in ALLOWED_HOSTS:
        raise InstrumentError('refusing to fetch outside the project hosts: ' + url)
    request = urllib.request.Request(url, headers={'User-Agent': 'salah-widget-delivery-identity'})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            chunks, total = [], 0
            while True:
                chunk = response.read(1 << 20)
                if not chunk:
                    break
                total += len(chunk)
                if total > max_bytes:
                    return response.status, None, 'body exceeds the ' + str(max_bytes) + '-byte bound'
                chunks.append(chunk)
            return response.status, b''.join(chunks), None
    except urllib.error.HTTPError as error:
        return error.code, None, 'HTTP ' + str(error.code)
    except (urllib.error.URLError, OSError, TimeoutError) as error:
        return None, None, 'network: ' + str(error)[:200]


# --- machine --------------------------------------------------------------------------------------

def await_build(commit, wait, api, sleep, clock):
    """awaiting-build -> built(commit) | errored | (inconclusive). Returns (state, build record, reason)."""
    deadline = clock() + max(0.0, wait)
    observations = []
    while True:
        build, error = api('repos/' + REPO + '/pages/builds/latest')
        record = None if build is None else {k: build.get(k) for k in ('status', 'commit', 'created_at', 'updated_at',
                                                                      'duration', 'error')}
        observations.append({'at': now(), 'build': record, 'error': error})
        if record and record.get('commit') == commit and record.get('status') == 'built':
            return 'built', record, None, observations
        if record and record.get('commit') == commit and record.get('status') == 'errored':
            return 'errored', record, 'Pages build for ' + commit + ' errored', observations
        if clock() >= deadline:
            if error:
                reason = error
            elif record is None:
                reason = 'no Pages build record'
            elif record.get('commit') != commit:
                reason = ('latest Pages build is for ' + str(record.get('commit')) + ' (' + str(record.get('status'))
                          + '), not ' + commit)
            else:
                reason = 'Pages build for ' + commit + ' is ' + str(record.get('status')) + ', not built'
            return 'awaiting-build', record, reason, observations
        sleep(min(30.0, max(1.0, deadline - clock())))


def compare_rows(rows, retry_window, fetch, sleep, clock, limits):
    """Fetch every row; retry failing ones inside the bounded CDN window. Mutates rows in place."""
    total = [0]

    def attempt(row, bust):
        url = row['url'] + (('?delivery-identity=' + row['expectedSha256'][:12] + '-' + str(len(row['attempts'])))
                            if bust else '')
        status, data, error = fetch(url, limits['timeout'], limits['maxFileBytes'])
        entry = {'at': now(), 'url': url, 'http': status, 'error': error}
        if data is not None:
            total[0] += len(data)
            entry.update(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
            if total[0] > limits['maxTotalBytes']:
                raise InstrumentError('total fetched bytes exceed the ' + str(limits['maxTotalBytes']) + '-byte bound')
        row['attempts'].append(entry)
        if data is not None and status == 200:
            row['served'] = {'bytes': len(data), 'sha256': entry['sha256']}
            row['state'] = 'identical' if entry['sha256'] == row['expectedSha256'] else 'mismatch'
        elif status == 404:
            row['state'] = 'absent'
        else:
            row['state'] = 'http-error'

    for row in rows:
        attempt(row, False)
    deadline = clock() + max(0.0, retry_window)
    while any(row['state'] != 'identical' for row in rows) and clock() < deadline:
        sleep(min(20.0, max(1.0, deadline - clock())))
        for row in rows:
            if row['state'] != 'identical':
                attempt(row, True)
    return rows


def run(root, commit, *, extra=(), wait_build=0.0, retry_window=0.0, site=SITE, api=gh_api, fetch=http_get,
        sleep=time.sleep, clock=time.monotonic, limits=None):
    limits = dict({'maxFiles': 400, 'maxFileBytes': 200_000_000, 'maxTotalBytes': 800_000_000, 'timeout': 60},
                  **(limits or {}))
    if urllib.parse.urlsplit(site).hostname not in ALLOWED_HOSTS or not site.endswith('/'):
        raise InstrumentError('site must be the project Pages root ending in /: ' + site)
    if not re.fullmatch(r'[0-9a-f]{40}', commit or ''):
        raise InstrumentError('--commit must be a full 40-hex commit SHA')
    resolved = git(root, 'rev-parse', '--verify', '--quiet', commit + '^{commit}').decode().strip()
    tree = git(root, 'rev-parse', commit + '^{tree}').decode().strip()
    receipt = {'schema': SCHEMA, 'repository': REPO, 'site': site, 'commit': resolved, 'tree': tree,
               'startedAt': now(), 'limits': limits, 'retryWindowSeconds': retry_window,
               'waitBuildSeconds': wait_build, 'states': ['awaiting-build'],
               'identity': {'githubSha': os.environ.get('GITHUB_SHA'), 'event': os.environ.get('GITHUB_EVENT_NAME'),
                            'runId': os.environ.get('GITHUB_RUN_ID'), 'runAttempt': os.environ.get('GITHUB_RUN_ATTEMPT')}}
    candidates, excludes, paths, notes = readback_set(root, resolved, extra)
    receipt['derivation'] = {'configExcludes': excludes, 'jekyllDefaultExcludes': list(JEKYLL_DEFAULT_EXCLUDES),
                             'skip': "any path component starting with '.' or '_'", 'notes': notes,
                             'filter': 'tools/pages_payload.py config_excludes/jekyll_excluded (R002B)'}
    rows, not_published = [], []
    for path, origin in sorted(candidates.items()):
        ok, reason = published(path, excludes)
        if not ok:
            not_published.append({'path': path, 'origin': origin, 'state': 'not-published', 'reason': reason})
            continue
        if path not in paths:
            rows.append({'path': path, 'origin': origin, 'kind': 'pages', 'url': site + path, 'state': 'missing-from-tree',
                         'attempts': []})
            continue
        rows.append({'path': path, 'origin': origin, 'kind': 'pages', 'url': site + urllib.parse.quote(path),
                     'blobCommit': resolved, 'state': 'pending', 'attempts': []})
    main_head, main_error = api('repos/' + REPO + '/commits/main')
    main_sha = (main_head or {}).get('sha')
    receipt['mainHead'] = {'sha': main_sha, 'error': main_error}
    for url, blob_commit, path, kind in readme_raw_routes(root, resolved, paths):
        row = {'path': path, 'origin': 'README raw route', 'kind': kind, 'url': url, 'blobCommit': blob_commit,
               'state': 'pending', 'attempts': []}
        if kind == 'raw-main' and main_sha != resolved:
            row['state'] = 'skipped'
            row['reason'] = 'main is ' + str(main_sha) + ', not this commit; the unpinned route follows main'
        rows.append(row)
    if len(rows) > limits['maxFiles']:
        raise InstrumentError(str(len(rows)) + ' readback rows exceed the ' + str(limits['maxFiles']) + '-file bound')
    receipt['notPublished'] = not_published

    state, build, reason, observations = await_build(resolved, wait_build, api, sleep, clock)
    receipt['pagesBuild'] = {'final': build, 'observations': observations}
    receipt['states'].append('built' if state == 'built' else state)
    if state != 'built':
        receipt.update(verdict='inconclusive', reason=reason, rows=rows, finishedAt=now())
        for row in rows:
            if row['state'] == 'pending':
                row['state'] = 'not-read'
        receipt['counts'] = counts(rows, not_published)
        return receipt
    receipt['states'].append('reading-back')
    live = [row for row in rows if row['state'] == 'pending']
    # Expected bytes are read only once the guard holds (no blob reads for an inconclusive guard).
    for row in live:
        data = blob_bytes(root, row['blobCommit'], row['path'])
        row.update(expectedBytes=len(data), expectedSha256=hashlib.sha256(data).hexdigest())
    compare_rows(live, retry_window, fetch, sleep, clock, limits)
    receipt['rows'] = rows
    receipt['counts'] = counts(rows, not_published)
    mismatched = [row['path'] + ' (' + row['kind'] + ', ' + row['state'] + ')' for row in rows
                  if row['state'] in ('mismatch', 'absent', 'missing-from-tree')]
    errors = [row['path'] + ' (' + row['kind'] + ')' for row in rows if row['state'] == 'http-error']
    # Re-check the build after reading: a newer deployment during the readback makes the result inconclusive.
    after, after_error = api('repos/' + REPO + '/pages/builds/latest')
    receipt['pagesBuild']['afterReadback'] = None if after is None else {k: after.get(k) for k in ('status', 'commit', 'updated_at')}
    if mismatched:
        receipt['verdict'] = 'mismatch'
        receipt['reason'] = 'served bytes differ from ' + resolved + ': ' + ', '.join(mismatched)
    elif errors or not live:
        receipt['verdict'] = 'inconclusive'
        receipt['reason'] = ('HTTP/network failure after the retry window: ' + ', '.join(errors)) if errors else 'nothing read back'
    elif after is None or after.get('commit') != resolved or after.get('status') != 'built':
        receipt['verdict'] = 'inconclusive'
        receipt['reason'] = 'Pages build changed during the readback: ' + json.dumps(receipt['pagesBuild']['afterReadback']) + (after_error or '')
    else:
        receipt['verdict'] = 'identical'
        receipt['reason'] = str(receipt['counts']['identical']) + ' served files byte-identical to ' + resolved
    receipt['states'].append(receipt['verdict'])
    receipt['finishedAt'] = now()
    return receipt


def counts(rows, not_published):
    found = {}
    for row in rows:
        found[row['state']] = found.get(row['state'], 0) + 1
    found['not-published'] = len(not_published)
    found.setdefault('identical', 0)
    return found


def summary(receipt):
    lines = ['### delivery identity: `' + receipt['verdict'] + '` for `' + receipt['commit'] + '`', '',
             '- ' + receipt.get('reason', ''), '- states: ' + ' -> '.join(receipt['states']),
             '- counts: `' + json.dumps(receipt.get('counts', {})) + '`',
             '- not-published (dropped before comparison): ' + str(len(receipt.get('notPublished', [])))]
    for row in receipt.get('rows', []):
        if row['state'] not in ('identical',):
            lines.append('  - `' + row['path'] + '` ' + row['kind'] + ': ' + row['state'] + (' - ' + row['reason'] if row.get('reason') else ''))
    for row in receipt.get('notPublished', [])[:20]:
        lines.append('  - not-published `' + row['path'] + '`: ' + row['reason'])
    return '\n'.join(lines) + '\n'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--commit', required=True, help='full SHA of the merged commit to read back')
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2],
                        help='a Git repository holding the commit (objects are read with git cat-file)')
    parser.add_argument('--out', type=Path, required=True, help='new receipt directory; an existing one is refused')
    parser.add_argument('--extra-path', action='append', default=[], help='add a candidate path (G-09 controls)')
    parser.add_argument('--wait-build', type=float, default=0.0, help='seconds to poll for the Pages build (default 0)')
    parser.add_argument('--retry-window', type=float, default=0.0, help='bounded CDN retry window in seconds (default 0)')
    parser.add_argument('--site', default=SITE)
    args = parser.parse_args(argv)
    try:
        args.out.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        parser.error('receipt directory exists: ' + str(args.out))
    try:
        receipt = run(args.root.resolve(), args.commit, extra=args.extra_path, wait_build=args.wait_build,
                      retry_window=args.retry_window, site=args.site)
    except (InstrumentError, ValueError, UnicodeError) as error:
        receipt = {'schema': SCHEMA, 'commit': args.commit, 'verdict': 'error', 'reason': str(error), 'states': ['error']}
    (args.out / 'delivery-identity.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    text = summary(receipt) if receipt['verdict'] != 'error' else '### delivery identity: `error`\n\n- ' + receipt['reason'] + '\n'
    (args.out / 'summary.md').write_text(text, encoding='utf-8')
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a', encoding='utf-8') as stream:
            stream.write(text + '\n')
    print('VERDICT', receipt['verdict'], receipt.get('reason', ''), flush=True)
    return EXIT[receipt['verdict']]


if __name__ == '__main__':
    sys.exit(main())
