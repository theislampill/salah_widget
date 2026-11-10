#!/usr/bin/env python3
"""Bounded R000B bundle preparation and staging-only Git carrier construction.

No product producer is executed. No REST object upload, canonical ref write,
force push, automatic retry, merge, PR or credential export is implemented.
"""
import argparse
import gzip
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

REPOSITORY = 'theislampill/salah_widget'
BASE_COMMIT = 'eebba178172f96b3ffe5ab3845bc0fffd57c6e1b'
BASE_TREE = '6b94a3933f9d1381b1c2ceaab287c93afb215ecb'
STAGING_REF = 'refs/heads/pro/r000b-recovery-materialization-20261110'
CANONICAL_REF = 'refs/heads/pro/r000b-explicit-weather-withdrawal-20261106'
PREFIX = '.github/r000b-transport/'
MANIFEST = PREFIX + 'manifest.json'
RECEIVER = PREFIX + 'receive.py'
WORKFLOW = '.github/workflows/r000b-recovery-materialization.yml'
CARRIER_PATH = PREFIX + 'candidate'
GENERATED = {'index.html', 'offline.html', 'real-sky/native-sky.js', 'moon/BUILD.json'}
PART_BYTES = 65536
MAX_MANIFEST_BYTES = 262144
MAX_INVENTORY_BYTES = 64 * 1024 * 1024
MAX_PAYLOAD_BYTES = 64 * 1024 * 1024
OID = re.compile(r'[0-9a-f]{40}\Z')
SHA256 = re.compile(r'[0-9a-f]{64}\Z')

WORKFLOW_TEMPLATE = '''name: R000B recovery materialization
on:
  push:
    branches: [pro/r000b-recovery-materialization-20261110]
permissions:
  contents: read
concurrency:
  group: r000b-recovery-materialization
  cancel-in-progress: false
jobs:
  carrier:
    if: github.repository == 'theislampill/salah_widget' && github.ref == 'refs/heads/pro/r000b-recovery-materialization-20261110'
    runs-on: ubuntu-22.04
    timeout-minutes: 15
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1
        with:
          ref: ${{ github.sha }}
          fetch-depth: 2
          sparse-checkout-cone-mode: false
          sparse-checkout: |
            .github/r000b-transport/
            .github/workflows/r000b-recovery-materialization.yml
      - name: Verify complete bundle and publish only the coherent staging carrier
        env:
          R000B_GITHUB_TOKEN: ${{ github.token }}
        run: >-
          python3 .github/r000b-transport/receive.py receive
          --repo "$GITHUB_WORKSPACE"
          --manifest-sha256 __MANIFEST_SHA256__
          --receipt "$RUNNER_TEMP/r000b-transport/receipt.json"
          --publish-staging
      - name: Preserve transport outcome including failure
        if: always()
        uses: actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02
        with:
          name: r000b-transport-${{ github.run_id }}-${{ github.run_attempt }}
          path: ${{ runner.temp }}/r000b-transport
          if-no-files-found: error
'''


class TransportError(Exception):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def require(condition, code):
    if not condition:
        raise TransportError(code)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def blob_id(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n').encode()


def utc():
    return datetime.now(timezone.utc).isoformat()


def valid_path(path):
    return (isinstance(path, str) and path and not path.startswith('/')
            and all(ord(c) >= 32 and ord(c) != 127 for c in path)
            and '\\' not in path and str(PurePosixPath(path)) == path
            and not any(p in ('..', '.') or p.casefold() == '.git' for p in path.split('/')))


class Git:
    """Record bounded observations; never retain raw command/source/credential output."""
    def __init__(self, repo, row=None, persist=None):
        self.repo = Path(repo).resolve()
        self.row = row
        self.persist = persist

    def record(self, operation, code, out, err):
        if self.row is not None:
            self.row['operations'].append({'operation': operation, 'exitCode': code,
                'stdoutBytes': len(out), 'stdoutSha256': sha256(out),
                'stderrBytes': len(err), 'stderrSha256': sha256(err), 'observedAt': utc()})
            self.persist()

    def run(self, operation, *args, data=None, env=None, allow_failure=False):
        command_env = dict(os.environ, GIT_OPTIONAL_LOCKS='0', GIT_TERMINAL_PROMPT='0')
        if env:
            command_env.update(env)
        p = subprocess.run(['git', *args], cwd=self.repo, env=command_env, input=data,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.record(operation, p.returncode, p.stdout, p.stderr)
        require(allow_failure or p.returncode == 0, 'git_failed_' + operation)
        return p.stdout

    def oid(self, operation, *args, **kw):
        value = self.run(operation, *args, **kw).decode().strip()
        require(bool(OID.fullmatch(value)), 'invalid_git_identity_' + operation)
        return value

    def hash_blob(self, oid, operation):
        require(bool(OID.fullmatch(oid)), 'invalid_blob_identity')
        p = subprocess.Popen(['git', 'cat-file', 'blob', oid], cwd=self.repo,
            env=dict(os.environ, GIT_OPTIONAL_LOCKS='0', GIT_TERMINAL_PROMPT='0'),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        h = hashlib.sha256()
        size = 0
        for block in iter(lambda: p.stdout.read(1024 * 1024), b''):
            h.update(block)
            size += len(block)
        p.stdout.close()
        err = p.stderr.read()
        p.stderr.close()
        code = p.wait()
        if self.row is not None:
            self.row['operations'].append({'operation': operation, 'exitCode': code,
                'blob': oid, 'bytes': size, 'sha256': h.hexdigest(),
                'stderrBytes': len(err), 'stderrSha256': sha256(err), 'observedAt': utc()})
            self.persist()
        require(code == 0, 'git_failed_' + operation)
        return {'blob': oid, 'bytes': size, 'sha256': h.hexdigest()}


def inventory(git, revision, operation):
    raw = git.run(operation, 'ls-tree', '-rz', revision)
    rows = []
    for entry in raw.split(b'\0'):
        if not entry:
            continue
        meta, path = entry.split(b'\t', 1)
        mode, kind, oid = meta.decode('ascii').split()
        path = path.decode('utf-8')
        require(valid_path(path) and kind == 'blob' and mode in ('100644', '100755', '120000')
                and bool(OID.fullmatch(oid)), 'unsupported_tree_entry')
        rows.append([path, mode, oid])
    require(rows and len(rows) == len({r[0] for r in rows}), 'invalid_tree_inventory')
    return sorted(rows, key=lambda r: r[0].encode())


def parents(git, commit):
    header = git.run('read_commit_parents', 'cat-file', 'commit', commit).split(b'\n\n', 1)[0]
    return [line[7:].decode('ascii') for line in header.splitlines() if line.startswith(b'parent ')]


def bundle_header(data, expected_commit):
    header = data.split(b'\n\n', 1)[0]
    require(len(header) < 8192 and b'\n\n' in data, 'invalid_bundle_header')
    lines = header.decode('utf-8').splitlines()
    require(len(lines) == 3 and lines[0] == '# v2 git bundle', 'unsupported_bundle_shape')
    require(lines[1].split(' ', 1)[0] == '-' + BASE_COMMIT, 'bundle_prerequisite_mismatch')
    tip = lines[2].split(' ', 1)
    require(len(tip) == 2 and tip[0] == expected_commit
            and tip[1] in ('HEAD', CANONICAL_REF), 'bundle_tip_mismatch')
    return tip[1]


def render_workflow(manifest_sha):
    require(bool(SHA256.fullmatch(manifest_sha)), 'invalid_manifest_digest')
    return WORKFLOW_TEMPLATE.replace('__MANIFEST_SHA256__', manifest_sha).encode()


def make_parts(staging, family, data):
    parts = []
    for number, offset in enumerate(range(0, len(data), PART_BYTES)):
        part = data[offset:offset + PART_BYTES]
        path = f'{PREFIX}payload/{family}/part-{number:05d}.bin'
        target = staging / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(part)
        parts.append({'path': path, 'bytes': len(part), 'sha256': sha256(part), 'blob': blob_id(part)})
    return {'bytes': len(data), 'sha256': sha256(data), 'parts': parts}


def prepare(repo, bundle, candidate_commit, candidate_tree, out):
    repo, bundle, out = Path(repo).resolve(), Path(bundle).resolve(), Path(out).resolve()
    require(not out.exists() and not out.is_relative_to(repo), 'unsafe_preparation_output')
    require(bool(OID.fullmatch(candidate_commit)) and bool(OID.fullmatch(candidate_tree)), 'invalid_candidate_identity')
    require(bundle.is_file() and not bundle.is_symlink() and bundle.stat().st_size <= MAX_PAYLOAD_BYTES,
            'invalid_bundle_file')
    payload = bundle.read_bytes()
    tip_ref = bundle_header(payload, candidate_commit)
    git = Git(repo)
    require(git.oid('baseline_tree', 'rev-parse', BASE_COMMIT + '^{tree}') == BASE_TREE, 'baseline_tree_mismatch')
    require(git.oid('candidate_tree', 'rev-parse', candidate_commit + '^{tree}') == candidate_tree,
            'candidate_tree_mismatch')
    entries = inventory(git, candidate_commit, 'candidate_inventory')
    require(not any(r[0].startswith(PREFIX) or r[0] == WORKFLOW for r in entries), 'candidate_contains_transport')
    entry_map = {p: (mode, oid) for p, mode, oid in entries}
    require(GENERATED <= entry_map.keys(), 'generated_inventory_missing')
    generated = {}
    for path in sorted(GENERATED):
        mode, oid = entry_map[path]
        require(mode == '100644', 'generated_mode_mismatch')
        generated[path] = dict(git.hash_blob(oid, 'hash_generated'), mode=mode)
    raw_inventory = json_bytes(entries)
    require(len(raw_inventory) <= MAX_INVENTORY_BYTES, 'inventory_too_large')
    compressed = io.BytesIO()
    with gzip.GzipFile(filename='', mode='wb', fileobj=compressed, mtime=0) as stream:
        stream.write(raw_inventory)
    staging = out / 'staging'
    staging.mkdir(parents=True)
    receiver = Path(__file__).read_bytes()
    (staging / RECEIVER).parent.mkdir(parents=True, exist_ok=True)
    (staging / RECEIVER).write_bytes(receiver)
    manifest = {
        'schema': 'r000b-bundle-carrier/v1', 'repository': REPOSITORY,
        'stagingRef': STAGING_REF, 'canonicalRef': CANONICAL_REF,
        'baseline': {'commit': BASE_COMMIT, 'tree': BASE_TREE},
        'candidate': {'commit': candidate_commit, 'tree': candidate_tree, 'fileCount': len(entries)},
        'bundle': dict(make_parts(staging, 'bundle', payload), advertisedRef=tip_ref),
        'inventory': dict(make_parts(staging, 'inventory', compressed.getvalue()),
                          encoding='gzip-json', uncompressedBytes=len(raw_inventory),
                          uncompressedSha256=sha256(raw_inventory)),
        'generated': generated,
        'receiver': {'path': RECEIVER, 'bytes': len(receiver), 'sha256': sha256(receiver), 'blob': blob_id(receiver)},
    }
    encoded = json_bytes(manifest)
    require(len(encoded) <= MAX_MANIFEST_BYTES, 'manifest_too_large')
    (staging / MANIFEST).write_bytes(encoded)
    workflow = staging / WORKFLOW
    workflow.parent.mkdir(parents=True, exist_ok=True)
    workflow.write_bytes(render_workflow(sha256(encoded)))
    files = {p.relative_to(staging).as_posix(): {'bytes': p.stat().st_size, 'sha256': sha256(p.read_bytes()),
             'blob': blob_id(p.read_bytes()), 'mode': '100644'}
             for p in staging.rglob('*') if p.is_file()}
    receipt = {'schema': 'r000b-transport-preparation/v1', 'status': 'PREPARED_NOT_PUBLISHED',
        'candidate': {'commit': candidate_commit, 'tree': candidate_tree}, 'baseline': manifest['baseline'],
        'bundleSha256': manifest['bundle']['sha256'], 'manifestSha256': sha256(encoded),
        'partBytes': PART_BYTES, 'files': files, 'publicationAuthority': 'ROOT_PROSPECTIVE_CHECK_REQUIRED'}
    (out / 'preparation.json').write_bytes(json_bytes(receipt))
    return receipt


def validate_manifest(manifest):
    require(isinstance(manifest, dict) and set(manifest) == {
        'schema', 'repository', 'stagingRef', 'canonicalRef', 'baseline', 'candidate',
        'bundle', 'inventory', 'generated', 'receiver'}, 'manifest_schema_mismatch')
    require(manifest['schema'] == 'r000b-bundle-carrier/v1' and manifest['repository'] == REPOSITORY
            and manifest['stagingRef'] == STAGING_REF and manifest['canonicalRef'] == CANONICAL_REF,
            'manifest_scope_mismatch')
    require(manifest['baseline'] == {'commit': BASE_COMMIT, 'tree': BASE_TREE}, 'manifest_baseline_mismatch')
    candidate = manifest['candidate']
    require(isinstance(candidate, dict) and set(candidate) == {'commit', 'tree', 'fileCount'}
            and all(isinstance(candidate[k], str) and OID.fullmatch(candidate[k]) for k in ('commit', 'tree'))
            and isinstance(candidate['fileCount'], int) and 0 < candidate['fileCount'] <= 100000,
            'manifest_candidate_mismatch')
    require(set(manifest['generated']) == GENERATED, 'generated_inventory_mismatch')
    for value in manifest['generated'].values():
        require(isinstance(value, dict) and set(value) == {'mode', 'blob', 'bytes', 'sha256'}
                and value['mode'] == '100644' and isinstance(value['bytes'], int) and value['bytes'] > 0
                and isinstance(value['blob'], str) and OID.fullmatch(value['blob'])
                and isinstance(value['sha256'], str) and SHA256.fullmatch(value['sha256']),
                'invalid_generated_binding')
    for family in ('bundle', 'inventory'):
        spec = manifest[family]
        require(isinstance(spec, dict) and isinstance(spec.get('bytes'), int)
                and 0 < spec['bytes'] <= MAX_PAYLOAD_BYTES
                and isinstance(spec.get('sha256'), str) and SHA256.fullmatch(spec['sha256'])
                and isinstance(spec.get('parts'), list) and len(spec['parts']) == (spec['bytes'] + PART_BYTES - 1) // PART_BYTES,
                'invalid_payload_descriptor')
        for i, part in enumerate(spec['parts']):
            remaining = spec['bytes'] - i * PART_BYTES
            require(isinstance(part, dict) and set(part) == {'path', 'bytes', 'sha256', 'blob'}
                    and part['path'] == f'{PREFIX}payload/{family}/part-{i:05d}.bin'
                    and part['bytes'] == min(PART_BYTES, remaining)
                    and isinstance(part['sha256'], str) and SHA256.fullmatch(part['sha256'])
                    and isinstance(part['blob'], str) and OID.fullmatch(part['blob']), 'invalid_part_descriptor')
    require(manifest['bundle'].get('advertisedRef') in ('HEAD', CANONICAL_REF), 'invalid_bundle_ref')
    inv = manifest['inventory']
    require(inv.get('encoding') == 'gzip-json' and isinstance(inv.get('uncompressedBytes'), int)
            and 0 < inv['uncompressedBytes'] <= MAX_INVENTORY_BYTES
            and isinstance(inv.get('uncompressedSha256'), str) and SHA256.fullmatch(inv['uncompressedSha256']),
            'invalid_inventory_descriptor')
    receiver = manifest['receiver']
    require(isinstance(receiver, dict) and set(receiver) == {'path', 'bytes', 'sha256', 'blob'}
            and receiver['path'] == RECEIVER and isinstance(receiver['bytes'], int) and receiver['bytes'] > 0
            and isinstance(receiver['sha256'], str) and SHA256.fullmatch(receiver['sha256'])
            and isinstance(receiver['blob'], str) and OID.fullmatch(receiver['blob']), 'invalid_receiver_descriptor')


def validate_hosted_context(env, head, origin):
    expected = {'GITHUB_ACTIONS': 'true', 'GITHUB_REPOSITORY': REPOSITORY, 'GITHUB_REF': STAGING_REF,
                'GITHUB_EVENT_NAME': 'push', 'GITHUB_SHA': head}
    require(all(env.get(k) == v for k, v in expected.items()), 'hosted_context_mismatch')
    require(origin in ('https://github.com/' + REPOSITORY, 'https://github.com/' + REPOSITORY + '.git'),
            'hosted_origin_mismatch')


def remote_head(git):
    lines = git.run('read_staging_remote', 'ls-remote', '--exit-code', '--heads', 'origin', STAGING_REF).decode().splitlines()
    require(len(lines) == 1, 'remote_staging_absent_or_ambiguous')
    fields = lines[0].split()
    require(len(fields) == 2 and OID.fullmatch(fields[0]) and fields[1] == STAGING_REF,
            'remote_staging_identity_mismatch')
    return fields[0]


def check_staging_protection(token, expected_head, row, persist):
    """Read only the exact staging branch and its effective rules; fail closed."""
    require(isinstance(token, str) and bool(token), 'staging_api_token_missing')
    branch = STAGING_REF.removeprefix('refs/heads/')
    encoded = urllib.parse.quote(branch, safe='')
    base = 'https://api.github.com/repos/' + REPOSITORY
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, request, fp, code, message, headers, newurl):
            return None
    opener = urllib.request.build_opener(NoRedirect())
    def read(suffix, operation):
        url = base + suffix
        request = urllib.request.Request(url, headers={
            'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2026-03-10', 'User-Agent': 'r000b-bounded-carrier'})
        try:
            with opener.open(request, timeout=30) as response:
                status = response.status
                body = response.read(65537)
                exact_url = response.geturl() == url
        except urllib.error.HTTPError as error:
            body = error.read(65537)
            row['operations'].append({'operation': operation, 'url': url,
                'httpStatus': error.code, 'bodyBytes': len(body), 'bodySha256': sha256(body),
                'bodyTruncated': len(body) > 65536, 'observedAt': utc()})
            persist()
            raise TransportError('staging_api_http_' + str(error.code)) from None
        except urllib.error.URLError:
            row['operations'].append({'operation': operation, 'url': url,
                                      'transportFailure': True, 'observedAt': utc()})
            persist()
            raise TransportError('staging_api_transport_failure') from None
        row['operations'].append({'operation': operation, 'url': url, 'httpStatus': status,
            'bodyBytes': len(body), 'bodySha256': sha256(body),
            'bodyTruncated': len(body) > 65536, 'observedAt': utc()})
        persist()
        require(status == 200 and exact_url and len(body) <= 65536, 'staging_api_response_unresolved')
        return json.loads(body)
    observed = read('/branches/' + encoded, 'read_staging_branch_protection')
    require(isinstance(observed, dict) and observed.get('name') == branch
            and observed.get('protected') is False and isinstance(observed.get('commit'), dict)
            and observed['commit'].get('sha') == expected_head, 'staging_branch_not_unprotected_at_expected_head')
    rules = read('/rules/branches/' + encoded, 'read_staging_effective_rules')
    require(isinstance(rules, list) and not rules, 'staging_rules_not_resolved_empty')
    return {'head': expected_head, 'protected': False, 'effectiveRules': 0}


def receive(repo, manifest_sha256, receipt, publish=False):
    repo, receipt = Path(repo).resolve(), Path(receipt).resolve()
    require(not receipt.is_relative_to(repo), 'receipt_must_be_outside_checkout')
    require(not receipt.exists(), 'receipt_already_exists_no_replay')
    receipt.parent.mkdir(parents=True, exist_ok=True)
    row = {'schema': 'r000b-carrier-receipt/v1', 'status': 'STARTED', 'startedAt': utc(),
           'repository': REPOSITORY, 'stagingRef': STAGING_REF, 'publishRequested': bool(publish),
           'pushAttempted': False, 'published': False, 'operations': []}
    def persist():
        temporary = receipt.with_suffix(receipt.suffix + '.pending')
        temporary.write_bytes(json_bytes(row))
        temporary.replace(receipt)
    persist()
    git = Git(repo, row, persist)
    try:
        require(isinstance(manifest_sha256, str) and bool(SHA256.fullmatch(manifest_sha256)), 'invalid_manifest_digest')
        head = git.oid('staging_head', 'rev-parse', 'HEAD')
        row['stagingHead'] = head
        row['stagingTree'] = git.oid('staging_tree', 'rev-parse', head + '^{tree}')
        require(not git.run('clean_checkout', 'status', '--porcelain', '--untracked-files=all'), 'dirty_staging_checkout')
        require(parents(git, head) == [BASE_COMMIT], 'staging_parent_mismatch')
        require(git.oid('baseline_tree', 'rev-parse', BASE_COMMIT + '^{tree}') == BASE_TREE, 'baseline_tree_mismatch')
        if publish:
            origin = git.run('read_origin', 'remote', 'get-url', 'origin').decode().strip()
            validate_hosted_context(os.environ, head, origin)
            require(Path(__file__).resolve() == repo / RECEIVER, 'receiver_execution_path_mismatch')
            observed = remote_head(git)
            row['remoteBefore'] = observed
            require(observed == head, 'staging_predecessor_changed')
        encoded = git.run('read_manifest', 'show', head + ':' + MANIFEST)
        require(len(encoded) <= MAX_MANIFEST_BYTES and sha256(encoded) == manifest_sha256, 'manifest_digest_mismatch')
        manifest = json.loads(encoded)
        validate_manifest(manifest)
        row['manifestSha256'] = manifest_sha256
        row['candidateCommit'] = manifest['candidate']['commit']
        row['candidateTree'] = manifest['candidate']['tree']
        baseline_entries = {p: (m, o) for p, m, o in inventory(git, BASE_COMMIT, 'baseline_inventory')}
        staged_entries = {p: (m, o) for p, m, o in inventory(git, head, 'staging_inventory')}
        expected_added = {MANIFEST, RECEIVER, WORKFLOW}
        expected_added.update(part['path'] for family in ('bundle', 'inventory') for part in manifest[family]['parts'])
        changed = {p for p in baseline_entries.keys() | staged_entries.keys()
                   if baseline_entries.get(p) != staged_entries.get(p)}
        require(changed == expected_added and not (baseline_entries.keys() & expected_added)
                and all(staged_entries[p][0] == '100644' for p in expected_added), 'staging_delta_mismatch')
        receiver = git.run('read_receiver', 'show', head + ':' + RECEIVER)
        require(len(receiver) == manifest['receiver']['bytes'] and sha256(receiver) == manifest['receiver']['sha256']
                and blob_id(receiver) == manifest['receiver']['blob']
                and sha256(Path(__file__).read_bytes()) == manifest['receiver']['sha256'], 'receiver_identity_mismatch')
        require(git.run('read_workflow', 'show', head + ':' + WORKFLOW) == render_workflow(manifest_sha256),
                'bootstrap_workflow_mismatch')
        payloads = {}
        for family in ('bundle', 'inventory'):
            spec = manifest[family]
            output = receipt.parent / ('payload.bundle' if family == 'bundle' else 'inventory.json.gz')
            require(not output.exists(), 'payload_output_already_exists')
            h = hashlib.sha256()
            size = 0
            with output.open('xb') as stream:
                for part in spec['parts']:
                    require(staged_entries[part['path']] == ('100644', part['blob']), 'part_identity_mismatch')
                    data = git.run('read_' + family + '_part', 'cat-file', 'blob', part['blob'])
                    require(len(data) == part['bytes'] and sha256(data) == part['sha256'], 'part_identity_mismatch')
                    stream.write(data)
                    h.update(data)
                    size += len(data)
            require(size == spec['bytes'] and h.hexdigest() == spec['sha256'], 'payload_identity_mismatch')
            payloads[family] = output
            row[family] = {'bytes': size, 'sha256': h.hexdigest(), 'parts': len(spec['parts'])}
            persist()
        with payloads['bundle'].open('rb') as stream:
            advertised = bundle_header(stream.read(8192), manifest['candidate']['commit'])
        require(advertised == manifest['bundle']['advertisedRef'], 'bundle_advertised_ref_mismatch')
        with gzip.open(payloads['inventory'], 'rb') as stream:
            raw_inventory = stream.read(manifest['inventory']['uncompressedBytes'] + 1)
        require(len(raw_inventory) == manifest['inventory']['uncompressedBytes']
                and sha256(raw_inventory) == manifest['inventory']['uncompressedSha256'], 'inventory_payload_mismatch')
        expected_inventory = json.loads(raw_inventory)
        require(isinstance(expected_inventory, list) and len(expected_inventory) == manifest['candidate']['fileCount'],
                'inventory_population_mismatch')
        git.run('verify_bundle_prerequisite', 'bundle', 'verify', str(payloads['bundle']))
        git.run('import_complete_bundle', 'bundle', 'unbundle', str(payloads['bundle']))
        candidate = manifest['candidate']['commit']
        tree = manifest['candidate']['tree']
        require(git.oid('imported_candidate_tree', 'rev-parse', candidate + '^{tree}') == tree,
                'imported_candidate_tree_mismatch')
        actual_inventory = inventory(git, candidate, 'imported_candidate_inventory')
        require(actual_inventory == expected_inventory, 'imported_candidate_inventory_mismatch')
        require(not any(r[0].startswith(PREFIX) or r[0] == WORKFLOW for r in actual_inventory),
                'candidate_contains_transport')
        git.run('verify_object_connectivity', 'fsck', '--connectivity-only', '--no-reflogs', candidate)
        actual_map = {p: (mode, oid) for p, mode, oid in actual_inventory}
        row['generated'] = {}
        for path, expected in manifest['generated'].items():
            require(actual_map.get(path) == ('100644', expected['blob']), 'generated_entry_mismatch')
            observed = dict(git.hash_blob(expected['blob'], 'verify_generated_' + path.replace('/', '_')), mode='100644')
            require(observed == expected, 'generated_complete_hash_mismatch')
            row['generated'][path] = observed
        # A separate index preserves the checkout and its real index exactly.
        index = receipt.parent / 'carrier.index'
        require(not index.exists(), 'carrier_index_already_exists')
        index_env = {'GIT_INDEX_FILE': str(index)}
        git.run('carrier_read_staging_tree', 'read-tree', head, env=index_env)
        git.run('carrier_add_exact_candidate_tree', 'read-tree', '--prefix=' + CARRIER_PATH + '/', tree, env=index_env)
        carrier_tree = git.oid('carrier_write_tree', 'write-tree', env=index_env)
        carrier_entries = inventory(git, carrier_tree, 'carrier_inventory')
        outside = {p: (m, o) for p, m, o in carrier_entries if not p.startswith(CARRIER_PATH + '/')}
        require(outside == staged_entries, 'carrier_root_drift')
        require(git.oid('carrier_subtree', 'rev-parse', carrier_tree + ':' + CARRIER_PATH) == tree,
                'carrier_subtree_mismatch')
        message = ('transport: carry verified R000B Git objects on staging only\n\n'
                   f'Candidate commit: {candidate}\nCandidate tree: {tree}\n'
                   f'Manifest SHA-256: {manifest_sha256}\n'
                   'Root runtime and workflows unchanged; no qualification or final publication claim.\n\n'
                   'Co-Authored-By: ChatGPT <noreply@openai.com>\n').encode()
        author_env = {'GIT_AUTHOR_NAME': 'github-actions[bot]',
            'GIT_AUTHOR_EMAIL': '41898282+github-actions[bot]@users.noreply.github.com',
            'GIT_COMMITTER_NAME': 'github-actions[bot]',
            'GIT_COMMITTER_EMAIL': '41898282+github-actions[bot]@users.noreply.github.com'}
        carrier = git.oid('create_carrier_commit', 'commit-tree', carrier_tree, '-p', head, data=message, env=author_env)
        require(parents(git, carrier) == [head], 'carrier_parent_mismatch')
        require(git.oid('unchanged_checkout_head', 'rev-parse', 'HEAD') == head, 'checkout_head_changed')
        require(not git.run('unchanged_checkout_status', 'status', '--porcelain', '--untracked-files=all'), 'checkout_changed')
        row.update(carrierCommit=carrier, carrierTree=carrier_tree, carrierParent=head,
                   rootFilesUnchanged=True, rootWorkflowsUnchanged=True)
        persist()
        if publish:
            token = os.environ.get('R000B_GITHUB_TOKEN')
            row['stagingProtectionBeforeDryRun'] = check_staging_protection(token, head, row, persist)
            observed = remote_head(git)
            require(observed == head, 'staging_predecessor_changed')
            row['dryRunAttempted'] = True
            persist()
            git.run('dry_run_staging_push', 'push', '--dry-run', '--porcelain', 'origin', carrier + ':' + STAGING_REF)
            row['dryRunPassed'] = True
            # Neither a dry run nor a stale branch read grants write/protection authority.
            row['stagingProtectionImmediatelyBeforePush'] = check_staging_protection(token, head, row, persist)
            observed = remote_head(git)
            row['remoteImmediatelyBeforePush'] = observed
            require(observed == head, 'staging_predecessor_changed')
            row['pushAttempted'] = True
            persist()
            git.run('push_staging_once', 'push', '--porcelain', 'origin', carrier + ':' + STAGING_REF)
            observed = remote_head(git)
            row['remoteAfter'] = observed
            require(observed == carrier, 'staging_push_readback_mismatch')
            row['published'] = True
            row['status'] = 'STAGING_CARRIER_PUBLISHED_PENDING_ROOT_READBACK'
        else:
            row['status'] = 'LOCAL_CARRIER_VERIFIED_NOT_PUBLISHED'
    except Exception as error:
        row['status'] = 'FAILED_EFFECT_UNCERTAIN_READBACK_REQUIRED' if row['pushAttempted'] else 'FAILED_NO_REF_UPDATE'
        row['failure'] = {'code': error.code if isinstance(error, TransportError) else 'unexpected_' + type(error).__name__}
    finally:
        row['finishedAt'] = utc()
        persist()
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    prep = commands.add_parser('prepare')
    prep.add_argument('--repo', type=Path, required=True)
    prep.add_argument('--bundle', type=Path, required=True)
    prep.add_argument('--candidate-commit', required=True)
    prep.add_argument('--candidate-tree', required=True)
    prep.add_argument('--out', type=Path, required=True)
    recv = commands.add_parser('receive')
    recv.add_argument('--repo', type=Path, required=True)
    recv.add_argument('--manifest-sha256', required=True)
    recv.add_argument('--receipt', type=Path, required=True)
    recv.add_argument('--publish-staging', action='store_true')
    args = parser.parse_args()
    if args.command == 'prepare':
        row = prepare(args.repo, args.bundle, args.candidate_commit, args.candidate_tree, args.out)
        print(json.dumps({k: row[k] for k in ('status', 'candidate', 'manifestSha256', 'bundleSha256')}))
        return 0
    row = receive(args.repo, args.manifest_sha256, args.receipt, publish=args.publish_staging)
    print(json.dumps({k: row[k] for k in ('status', 'published', 'pushAttempted')}))
    return int(row['status'].startswith('FAILED'))


if __name__ == '__main__':
    sys.exit(main())
