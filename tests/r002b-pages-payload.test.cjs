'use strict';
// R002B Pages payload instrument (tools/pages_payload.py): verdicts, guards and negative controls on
// synthetic _site / TAR / zip fixtures. No network, no build, no deployment. The deployed-artifact
// readback itself (read-only GitHub API) is exercised only through its pure parts here.
const test = require('node:test'), assert = require('node:assert/strict');
const {spawnSync} = require('node:child_process');
const fs = require('node:fs'), os = require('node:os'), path = require('node:path'), crypto = require('node:crypto');

const ROOT = path.join(__dirname, '..');
const TOOL = path.join(ROOT, 'tools', 'pages_payload.py');
const PY = process.env.PYTHON || (process.platform === 'win32' ? 'python' : 'python3');
const EVIDENCE = ['docs/real-sky/evidence', 'docs/rlgwo-execution', 'docs/state-contracts/evidence', 'docs/moon/evidence'];

function run(args, opts = {}) {
  const r = spawnSync(PY, [...(opts.flags || []), TOOL, ...args], {cwd: ROOT, encoding: 'utf8', input: opts.input});
  return {code: r.status, out: r.stdout, err: r.stderr};
}
function py(code, ...argv) {
  const r = spawnSync(PY, ['-c', `import sys;sys.path.insert(0,${JSON.stringify(path.join(ROOT, 'tools'))});import pages_payload as pp\n${code}`, ...argv],
    {cwd: ROOT, encoding: 'utf8'});
  if (r.status !== 0) throw new Error(r.stderr);
  return JSON.parse(r.stdout);
}
function tmp() { return fs.mkdtempSync(path.join(os.tmpdir(), 'r002b-')); }
function site(files) {
  const dir = tmp(), s = path.join(dir, '_site');
  for (const [name, size] of Object.entries(files)) {
    fs.mkdirSync(path.dirname(path.join(s, name)), {recursive: true});
    fs.writeFileSync(path.join(s, name), Buffer.alloc(size, 0x61));
  }
  return {dir, s};
}
function receipt(dir, args, opts) {
  const out = path.join(dir, 'receipt.json');
  const r = run([...args, '--out', out], opts);
  return {...r, json: JSON.parse(fs.readFileSync(out, 'utf8'))};
}
const FILES = {'index.html': 10, 'docs/a/b.png': 20, 'docs/a/c d.json': 7};
const DIGEST = crypto.createHash('sha256').update('20  docs/a/b.png\n7  docs/a/c d.json\n10  index.html\n').digest('hex');

test('site: within at and below the bound, exceeds one byte above (I1)', () => {
  const {dir, s} = site(FILES);
  const at = receipt(dir, ['site', '--site', s, '--bound', '37']);
  assert.equal(at.code, 0); assert.equal(at.json.verdict, 'within');
  assert.equal(at.json.measured.regularFiles, 3); assert.equal(at.json.measured.regularFileBytes, 37);
  assert.equal(at.json.measured.pathSizeManifestSha256, DIGEST);
  const over = receipt(dir, ['site', '--site', s, '--bound', '36']);
  assert.equal(over.code, 1); assert.equal(over.json.verdict, 'exceeds');
});

test('site: python -O reaches the same verdict (no assert-only guard, G-03)', () => {
  const {dir, s} = site(FILES);
  const r = receipt(dir, ['site', '--site', s, '--bound', '36'], {flags: ['-O']});
  assert.equal(r.code, 1); assert.equal(r.json.verdict, 'exceeds');
  const bad = receipt(dir, ['site', '--site', s, '--bound', '0'], {flags: ['-O']});
  assert.equal(bad.code, 3); assert.equal(bad.json.verdict, 'error');
});

test('site: failed or empty build is inconclusive, never within (G-04)', () => {
  const dir = tmp();
  const missing = receipt(dir, ['site', '--site', path.join(dir, 'nope')]);
  assert.equal(missing.code, 2); assert.equal(missing.json.verdict, 'inconclusive');
  fs.mkdirSync(path.join(dir, 'empty'));
  const empty = receipt(dir, ['site', '--site', path.join(dir, 'empty')]);
  assert.equal(empty.code, 2); assert.equal(empty.json.verdict, 'inconclusive');
});

test('site: a symlink in _site is an instrument error', (t) => {
  const {dir, s} = site(FILES);
  try { fs.symlinkSync(path.join(s, 'index.html'), path.join(s, 'link.html')); }
  catch { t.skip('symlink creation not permitted on this host'); return; }
  const r = receipt(dir, ['site', '--site', s]);
  assert.equal(r.code, 3); assert.match(r.json.error, /symlink/);
});

function makeTar(dir, s, format) {
  const tar = path.join(dir, `artifact-${format}.tar`);
  const r = spawnSync(PY, ['-c', `import tarfile,sys
with tarfile.open(sys.argv[1],'w',format=getattr(tarfile,sys.argv[3])) as t: t.add(sys.argv[2],arcname='.')`, tar, s, format]);
  if (r.status !== 0) throw new Error(String(r.stderr));
  return tar;
}

test('tar: GNU long names and PAX headers give the same manifest as the _site walk (G-02 basis)', () => {
  const long = 'docs/' + 'x'.repeat(140) + '/deep.bin';
  const {dir, s} = site({...FILES, [long]: 600});
  const walk = receipt(dir, ['site', '--site', s]).json.measured;
  for (const format of ['GNU_FORMAT', 'PAX_FORMAT']) {
    const tar = makeTar(dir, s, format);
    const r = receipt(dir, ['tar', '--file', tar]);
    assert.equal(r.code, 0, r.out + r.err);
    assert.equal(r.json.measured.pathSizeManifestSha256, walk.pathSizeManifestSha256, format);
    assert.equal(r.json.measured.regularFileBytes, 637);
    assert.equal(r.json.measured.tarContainerBytes, fs.statSync(tar).size);
  }
});

test('tar: truncation is inconclusive; a corrupted header checksum is an error', () => {
  const {dir, s} = site(FILES);
  const tar = makeTar(dir, s, 'GNU_FORMAT'), bytes = fs.readFileSync(tar);
  const cut = path.join(dir, 'cut.tar'); fs.writeFileSync(cut, bytes.subarray(0, 1536 + 100));
  const t1 = receipt(dir, ['tar', '--file', cut]);
  assert.equal(t1.code, 2); assert.equal(t1.json.verdict, 'inconclusive');
  const bad = Buffer.from(bytes); bad[600] ^= 0xff;  // inside the second header's name field
  const corrupt = path.join(dir, 'corrupt.tar'); fs.writeFileSync(corrupt, bad);
  const t2 = receipt(dir, ['tar', '--file', corrupt]);
  assert.equal(t2.code, 3); assert.match(t2.json.error, /checksum/);
});

function makeZip(dir, tar, name, unseekable) {
  const zip = path.join(dir, `${name}${unseekable ? '-dd' : ''}.zip`);
  const r = spawnSync(PY, ['-c', `import zipfile,sys
class W:
    def __init__(s,f): s.f=f
    def write(s,b): return s.f.write(b)
    def flush(s): s.f.flush()
out=open(sys.argv[1],'wb'); target=W(out) if sys.argv[4]=='1' else out
with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z: z.write(sys.argv[2],arcname=sys.argv[3])
out.close()`, zip, tar, name, unseekable ? '1' : '0']);
  if (r.status !== 0) throw new Error(String(r.stderr));
  return zip;
}

test('zip: streamed artifact.tar (with and without data descriptor, file and stdin) matches the TAR', () => {
  const {dir, s} = site(FILES);
  const tar = makeTar(dir, s, 'GNU_FORMAT');
  const direct = receipt(dir, ['tar', '--file', tar]).json.measured;
  for (const dd of [false, true]) {
    const zip = makeZip(dir, tar, 'artifact.tar', dd);
    assert.equal(Boolean(fs.readFileSync(zip).readUInt16LE(6) & 8), dd, 'data-descriptor flag as intended');
    const r = receipt(dir, ['zip', '--file', zip]);
    assert.equal(r.code, 0, r.out + r.err);
    assert.equal(r.json.measured.memberIndexSha256, direct.memberIndexSha256);
    assert.equal(r.json.measured.tarContainerBytes, direct.tarContainerBytes);
    const env = py('e=pp.read_envelope(lambda a,n: open(sys.argv[1],"rb").read()[a:a+n], __import__("os").path.getsize(sys.argv[1]));print(__import__("json").dumps(e))', zip);
    assert.equal(env.entries[0].uncompressedBytes, direct.tarContainerBytes);
    assert.equal(env.entries[0].crc32, r.json.measured.zipMember.crc32);
  }
  const zip = makeZip(dir, tar, 'artifact.tar', false);
  const piped = run(['zip', '--file', '-'], {input: fs.readFileSync(zip)});
  assert.equal(piped.code, 0, piped.err); assert.equal(JSON.parse(piped.out).regularFileBytes, 37);
});

test('zip: wrong first member is an error; truncation is inconclusive', () => {
  const {dir, s} = site(FILES);
  const tar = makeTar(dir, s, 'GNU_FORMAT');
  const wrong = receipt(dir, ['zip', '--file', makeZip(dir, tar, 'other.tar', false)]);
  assert.equal(wrong.code, 3); assert.match(wrong.json.error, /not artifact\.tar/);
  const bytes = fs.readFileSync(makeZip(dir, tar, 'artifact.tar', false));
  const cut = path.join(dir, 'cut.zip'); fs.writeFileSync(cut, bytes.subarray(0, 120));
  const r = receipt(dir, ['zip', '--file', cut]);
  assert.equal(r.code, 2); assert.equal(r.json.verdict, 'inconclusive');
});

test('artifact admission and envelope verdict: expired/foreign is inconclusive; only within is envelope-sound', () => {
  const adm = py(`out={}
for m in [None,{"id":1,"name":"github-pages","expired":True,"expires_at":"x"},{"id":2,"name":"other","expired":False}]:
    try: pp.artifact_status(m); out[str(m and m["id"])]="admitted"
    except pp.Inconclusive as e: out[str(m and m["id"])]="inconclusive"
print(__import__("json").dumps(out))`);
  assert.deepEqual(adm, {None: 'inconclusive', 1: 'inconclusive', 2: 'inconclusive'});
  const v = py(`import json
small=pp.envelope_bounds({"entries":[{"name":"artifact.tar","uncompressedBytes":905902080}]},5825)
big=pp.envelope_bounds({"entries":[{"name":"artifact.tar","uncompressedBytes":1933260800}]},19412)
print(json.dumps([pp.envelope_verdict(small,1000000000),pp.envelope_verdict(big,1000000000),pp.envelope_verdict(big,10**10),pp.envelope_verdict(big,1900000000)]))`);
  assert.equal(v[0].verdict, 'within');
  assert.equal(v[1].verdict, 'inconclusive'); assert.equal(v[1].inferredVerdict, 'exceeds');
  assert.equal(v[2].verdict, 'within');
  // lower bound <= bound < upper bound: an inferred lower bound never proves `within`.
  assert.equal(v[3].verdict, 'inconclusive'); assert.equal(v[3].inferredVerdict, 'within');
});

test('projection mirrors Jekyll string-prefix excludes and flags collateral and protected removals', () => {
  const p = py(`import json
rows=[("docs/a/x",5),("docs/ab/y",7),("_hidden/z",3),("v1/index.html",11),("index.html",2)]
print(json.dumps([pp.project_listing(rows,["docs/a"]),pp.project_listing(rows,["v1"]),pp.config_excludes("x: 1\\nexclude:\\n  - a/b # c\\n  - 'd'\\nother: 2\\n")]))`);
  assert.equal(p[0].removedFiles, 2); assert.deepEqual(p[0].removedPathsNotUnderADirectoryPrefix, ['docs/ab/y']);
  assert.equal(p[0].projectedBytes, 13); assert.deepEqual(p[0].protectedPathsRemoved, []);
  assert.deepEqual(p[1].protectedPathsRemoved, ['v1/index.html']);
  assert.deepEqual(p[2], ['a/b', 'd']);
});

test('compare-sites: only evidence may disappear; a removed or resized protected path fails (G-07)', () => {
  const base = '10  index.html\n5  docs/rlgwo-execution/x.png\n3  docs/notes.md\n';
  const ok = py('import json;print(json.dumps(pp.compare_manifests(sys.argv[1],sys.argv[2],sys.argv[3:])))',
    base, '10  index.html\n3  docs/notes.md\n', ...EVIDENCE);
  assert.equal(ok.onlyEvidenceRemoved, true); assert.equal(ok.removedBytes, 5);
  const lost = py('import json;print(json.dumps(pp.compare_manifests(sys.argv[1],sys.argv[2],sys.argv[3:])))',
    base, '10  index.html\n', ...EVIDENCE);
  assert.equal(lost.onlyEvidenceRemoved, false); assert.deepEqual(lost.removedOutsideExcludes, ['docs/notes.md']);
  const resized = py('import json;print(json.dumps(pp.compare_manifests(sys.argv[1],sys.argv[2],sys.argv[3:])))',
    base, '11  index.html\n3  docs/notes.md\n', ...EVIDENCE);
  assert.equal(resized.onlyEvidenceRemoved, false); assert.deepEqual(resized.protectedResized, ['index.html']);
});

test('census: github.io and main-ref links into the prefixes break; commit-pinned links do not', () => {
  const c = py(`import json
texts=[("i1","see https://theislampill.github.io/salah_widget/docs/moon/evidence/a.png and https://theislampill.github.io/salah_widget/README.md"),
("i2","https://github.com/theislampill/salah_widget/blob/0123abcd/docs/moon/evidence/a.png https://github.com/theislampill/salah_widget/blob/main/docs/moon/evidence/b.png https://raw.githubusercontent.com/theislampill/salah_widget/feature-x/docs/moon/evidence/c.png")]
print(json.dumps(pp.census_text(texts,["docs/moon/evidence"])))`);
  assert.equal(c.githubIoUrls, 2); assert.equal(c.githubIoUrlsIntoPrefixes, 1);
  assert.equal(c.githubComUrlsIntoPrefixesPinnedToCommit, 1); assert.equal(c.githubComUrlsIntoPrefixesOnMain, 1);
  assert.deepEqual(c.urlsIntoPrefixesOnOtherRefs, {'feature-x': 1});
});

test('this tree: _config.yml excludes exactly the evidence trees and no protected path (DG-2(a))', () => {
  const cfg = py('import json;print(json.dumps(pp.config_excludes(open("_config.yml").read())))');
  for (const prefix of EVIDENCE) assert.ok(cfg.includes(prefix), prefix);
  assert.ok(cfg.includes('docs/rlgwo-execution/20261014/R000C/native'));
  const listing = py(`import json,subprocess
names=[n for n in subprocess.check_output(["git","ls-files","-z"]).decode().split("\\0") if n]
import os
rows=[(n,os.path.getsize(n)) for n in names if os.path.isfile(n)]
r=pp.project_listing(rows,pp.config_excludes(open("_config.yml").read()))
print(json.dumps({k:r[k] for k in ("projectedBytes","protectedPathsRemoved","removedPathsNotUnderADirectoryPrefix")}))`);
  assert.deepEqual(listing.protectedPathsRemoved, []);
  assert.ok(listing.projectedBytes <= 1_000_000_000, String(listing.projectedBytes));
  for (const p of listing.removedPathsNotUnderADirectoryPrefix)  // only the R000C native-* siblings R0017 measured
    assert.match(p, /^docs\/rlgwo-execution\//);
});

test('no assert-based guard remains in either payload verifier (R0029 class)', () => {
  for (const file of ['tools/pages_payload.py', 'tools/verify_r0017_pages_payload.py']) {
    const text = fs.readFileSync(path.join(ROOT, file), 'utf8');
    assert.doesNotMatch(text, /^\s*assert\b/m, file);
  }
});

test('the committed Stage-1 receipt states only what the envelope proves', () => {
  const r = JSON.parse(fs.readFileSync(path.join(ROOT, 'docs/state-contracts/evidence/R002B/stage1-deployed-envelope.json'), 'utf8'));
  assert.equal(r.source, 'deployed-artifact');
  assert.equal(r.sourceCommit, '5b84647686c28a3ce557fba2c2e6a801d0c0cb73');
  assert.equal(r.verdict, 'inconclusive'); assert.equal(r.inferredVerdict, 'exceeds');
  assert.ok(r.bounds.tarContainerBytes > r.bound);
  assert.equal(r.bounds.tarContainerBytes, r.envelope.entries[0].uncompressedBytes);
  assert.equal(r.envelope.archiveBytes, r.artifact.size_in_bytes);
  assert.equal(r.measured, undefined);
});
