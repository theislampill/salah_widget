"""R0029 generator contract: all-or-nothing publication and fail-loud guards (G-02..G-08, G-11).

Every scenario runs the REAL tools/build_native.py inside a disposable copy of the builder
inputs and the committed generated outputs; the repository is never written. Detected
failures (manifest drift, Moon asset drift, anchor drift at every count-checked site) must
leave the copy byte-identical, under `python -O` too. A clean build twice is byte-identical
to the committed outputs; a rebuild removes stale owned files only; an injected I/O fault
during publish reports the replaced paths and a re-run restores parity.
Run: python -m unittest tests/real-sky/generator_atomicity_test.py -v
"""
from pathlib import Path
import ast, hashlib, json, os, re, shutil, subprocess, sys, tempfile, unittest

ROOT = Path(__file__).resolve().parents[2]
ENTRY = 'src/native/index.html'
INVENTORY = 'GENERATED.json'
ROOT_FILES = ['index.html', 'offline.html', 'config.js', 'builder.html', INVENTORY]
VENDOR_FIXED = ['src/reference-worker-client.mjs', 'src/latest-render-queue.mjs', 'src/diffuse-manifest-pin.mjs',
                'data/bright-stars.json', 'data/registered-starlight/runtime-manifest.json',
                'data/registered-starlight/V-nside128.json', 'LICENSE-CODE.txt', 'LICENSE-DATA.md',
                'THIRD_PARTY_NOTICES.md', 'upstream/ASTROPY_LICENSE.rst', 'vendor/spectral/IRAF-LICENSE.txt',
                'vendor/spectral/MITSUBA-LICENSE.txt', 'vendor/spectral/SPECLITE-LICENSE.txt',
                'provenance/cp7/admitted/ASTROGO-LICENSE.txt']
IGNORE = shutil.ignore_patterns('__pycache__', '*.pyc')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def core_list():
    builder = (ROOT / 'tools/build_native.py').read_text(encoding='utf-8')
    return ast.literal_eval(re.search(r'^core=(\[.*?\])$', builder, re.M).group(1))


def copy_inputs(tree):
    """The builder's complete input set plus the committed generated outputs. No git, no network."""
    for directory in ['src/native', 'real-sky', 'moon']:
        shutil.copytree(ROOT / directory, tree / directory, ignore=shutil.ignore_patterns('__pycache__', 'tests'))
    (tree / 'tools').mkdir()
    for p in (ROOT / 'tools').glob('*.py'):
        shutil.copyfile(p, tree / 'tools' / p.name)
    for p in core_list() + VENDOR_FIXED:
        target = tree / 'vendor/real-sky' / p
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / 'vendor/real-sky' / p, target)
    for name in ROOT_FILES:
        if (ROOT / name).is_file():
            shutil.copyfile(ROOT / name, tree / name)


def manifest(tree):
    return {p.relative_to(tree).as_posix(): sha(p.read_bytes()) for p in sorted(tree.rglob('*')) if p.is_file()}


def difference(a, b):
    return {'changed': sorted(k for k in a.keys() & b.keys() if a[k] != b[k]),
            'added': sorted(b.keys() - a.keys()), 'removed': sorted(a.keys() - b.keys())}


NOTHING = {'changed': [], 'added': [], 'removed': []}

# Wrapper that runs the real builder script after optional in-process fault injection.
WRAPPER = r'''
import runpy, sys
tools = sys.argv[1]; mode = sys.argv[2]; sys.path.insert(0, tools)
import generated_outputs, build_moon
if mode == 'publish-fault':
    real, calls = generated_outputs._replace, [0]
    def faulty(staged, target):
        calls[0] += 1
        if calls[0] > 2:
            raise OSError(28, 'injected publish fault (R0029 G-07)')
        return real(staged, target)
    generated_outputs._replace = faulty
elif mode == 'interrupt-before-publish':
    def interrupted(root, entries):
        raise KeyboardInterrupt('injected interruption before publish (R0029)')
    build_moon.plan_moon = interrupted
sys.argv = [tools + '/build_native.py']
runpy.run_path(tools + '/build_native.py', run_name='__main__')
'''


class Tree:
    def __init__(self, path, scratch):
        self.path, self.scratch = path, scratch

    def run(self, optimize=False, mode=None):
        tmp = Path(tempfile.mkdtemp(dir=self.scratch, prefix='tmp-'))
        env = dict(os.environ, TMP=str(tmp), TEMP=str(tmp), TMPDIR=str(tmp), PYTHONDONTWRITEBYTECODE='1',
                   PYTHONUTF8='1')
        flags = ['-O'] if optimize else []
        if mode:
            argv = [sys.executable, *flags, '-c', WRAPPER, str(self.path / 'tools'), mode]
        else:
            argv = [sys.executable, *flags, str(self.path / 'tools/build_native.py')]
        r = subprocess.run(argv, cwd=self.path, env=env, capture_output=True, text=True, timeout=900)
        leftovers = list(tmp.iterdir())
        shutil.rmtree(tmp)
        r.staging_leftovers = leftovers
        return r

    def edit(self, relative, old, new, count=1):
        path = self.path / relative
        raw = path.read_bytes()
        text = raw.decode('utf-8')
        if text.count(old) != count:
            raise RuntimeError(f'injection anchor {old[:60]!r} in {relative}: expected {count}, found {text.count(old)}')
        path.write_bytes(text.replace(old, new).encode('utf-8'))
        return raw


class GeneratorAtomicity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scratch_dir = tempfile.TemporaryDirectory(prefix='salah-r0029-')
        cls.scratch = Path(cls.scratch_dir.name)
        cls.pristine = Tree(cls.scratch / 'pristine', cls.scratch)
        copy_inputs(cls.pristine.path)
        cls.committed = manifest(cls.pristine.path)

    @classmethod
    def tearDownClass(cls):
        cls.scratch_dir.cleanup()

    def fresh(self, name):
        path = self.scratch / name
        shutil.copytree(self.pristine.path, path)
        return Tree(path, self.scratch)

    def expect_no_write(self, tree, relative, old, new, message, optimize=False, count=1):
        """Inject a fault, require a loud failure naming `message`, and zero in-tree writes."""
        raw = tree.edit(relative, old, new, count)
        try:
            before = manifest(tree.path)
            r = tree.run(optimize=optimize)
            self.assertNotEqual(r.returncode, 0, f'{message}: build reported success')
            self.assertIn(message, r.stderr)
            self.assertEqual(difference(before, manifest(tree.path)), NOTHING, f'{message}: tree changed')
            self.assertEqual(r.staging_leftovers, [], 'staging removed')
            return r
        finally:
            (tree.path / relative).write_bytes(raw)

    # G-08 (in a disposable copy): byte-identical to committed outputs, second build identical.
    def test_clean_build_twice_is_byte_identical_except_inventory(self):
        tree = self.fresh('clean')
        first = tree.run()
        self.assertEqual(first.returncode, 0, first.stderr[-2000:])
        built = manifest(tree.path)
        delta = difference(self.committed, built)
        self.assertEqual(delta['removed'], [])
        self.assertLessEqual(set(delta['changed'] + delta['added']), {INVENTORY}, delta)
        self.assertNotIn('moon/BUILD.json', delta['changed'])
        report = json.loads(first.stdout)
        self.assertEqual(report['phase'], 'published')
        self.assertEqual(report['inventorySha256'], built[INVENTORY])
        second = tree.run()
        self.assertEqual(second.returncode, 0, second.stderr[-2000:])
        self.assertEqual(difference(built, manifest(tree.path)), NOTHING, 'second build identical')
        self.assertEqual(json.loads(second.stdout)['written'], 0)
        inventory = json.loads((tree.path / INVENTORY).read_bytes())
        for path, row in inventory['files'].items():
            data = (tree.path / path).read_bytes()
            self.assertEqual((len(data), sha(data)), (row['bytes'], row['sha256']), path)
        self.assertEqual(inventory['fileCount'], len(inventory['files']))
        self.assertNotIn(INVENTORY, inventory['files'])
        self.assertEqual(second.staging_leftovers, [])

    # G-02 / G-03: manifest-pin drift fails with a named message and writes nothing, also under -O.
    def test_manifest_drift_writes_nothing_normal_and_optimized(self):
        tree = self.pristine
        pin = 'vendor/real-sky/src/diffuse-manifest-pin.mjs'
        digest = sha((tree.path / 'vendor/real-sky/data/registered-starlight/runtime-manifest.json').read_bytes())
        for optimize in (False, True):
            with self.subTest(optimize=optimize):
                self.expect_no_write(tree, pin, digest, '0' * 64, 'manifest drift', optimize=optimize)

    # G-04: a Moon preflight failure leaves the (Moon-expanded) root entries untouched.
    def test_moon_asset_drift_writes_nothing(self):
        tree = self.pristine
        spec = json.loads((tree.path / 'moon/asset-manifest.json').read_bytes())
        relative = 'moon/' + next(iter(spec['assets'].values()))['path']
        path = tree.path / relative
        raw = path.read_bytes()
        try:
            path.write_bytes(raw[:-1] + bytes([raw[-1] ^ 1]))
            before = manifest(tree.path)
            for optimize in (False, True):
                with self.subTest(optimize=optimize):
                    r = tree.run(optimize=optimize)
                    self.assertNotEqual(r.returncode, 0)
                    self.assertIn('Moon asset identity', r.stderr)
                    self.assertEqual(difference(before, manifest(tree.path)), NOTHING)
            for entry in ['index.html', 'offline.html']:
                self.assertIn('id="moon-initial-code"', (tree.path / entry).read_text(encoding='utf-8'))
        finally:
            path.write_bytes(raw)

    # G-05: an injected drift at EVERY count-checked substitution fails, naming the anchor, writing nothing.
    def test_anchor_drift_at_every_count_site_writes_nothing(self):
        native = 'tools/build_native.py'
        first_line = (self.pristine.path / 'moon/src/moon-native.mjs').read_text(encoding='utf-8').split('\n', 1)[0] + '\n'
        sites = [
            # (site, file, injected old, injected new, expected message)
            ('starfield block start', ENTRY, '// PROJECTED STARFIELD:', '// PROJECTED STARFIELD:\n// PROJECTED STARFIELD:',
             'build_native starfield block'),
            ('elevation hook', ENTRY, '    if(track&&attemptEligible(op,a)){ weatherTrack=track; _renderDirty=true; }',
             '    if(track&&attemptEligible(op,a)){ weatherTrack=track;  _renderDirty=true; }', 'build_native elevation hook'),
            ('beginSkyScene hooks', ENTRY, 'function beginSkyScene(initialDocument=false){',
             'function beginSkyScene(initialDocument = false){', 'build_native beginSkyScene hooks'),
            ('commitSkyScene notify hook', ENTRY, '  commitSkyScene(A);\n}', '  commitSkyScene(A); \n}',
             'build_native commitSkyScene notify hook'),
            ('boot() hook insertion', ENTRY, '\nboot();', '\n boot();', 'build_native boot() hook insertion'),
            ('</head> stylesheet link', ENTRY, '</head>', '<!-- </head> -->\n</head>', 'build_native </head> stylesheet link'),
            ('config tag', ENTRY, '<script src="config.js"></script>',
             '<script src="config.js"></script><!-- <script src="config.js"></script> -->', 'native config script boundary'),
            ('</body> native-sky script', ENTRY, '</body>', '<!-- </body> -->\n</body>', 'build_native </body> native-sky script'),
            ('worker template WORKER_SOURCE', native, 'startNativeSky(pack,WORKER_SOURCE,PHYSICAL_MODE)',
             'startNativeSky(pack,WORKER_SRC,PHYSICAL_MODE)', 'build_native worker template'),
            ('worker template PHYSICAL_MODE', native, 'startNativeSky(pack,WORKER_SOURCE,PHYSICAL_MODE)',
             'startNativeSky(pack,WORKER_SOURCE,PHYSICAL_MODE,PHYSICAL_MODE)', 'build_native worker template'),
            ('offline inline config.js', native, "standalone=replace_exact(s,'<script src=\"config.js\"></script>'",
             "standalone=replace_exact(s,'<script src=\"./config.js\"></script>'", 'build_native offline inline config.js'),
            ('offline inline stylesheet', native, '\'<link rel="stylesheet" href="real-sky/native-sky.css">\\n</head>\'',
             '\'<link rel="stylesheet" href="./real-sky/native-sky.css">\\n</head>\'', 'build_native offline inline stylesheet'),
            ('offline inline scripts', native, '\'<script src="real-sky/native-sky.js"></script>\\n</body>\'',
             '\'<script defer src="real-sky/native-sky.js"></script>\\n</body>\'',
             'build_native offline inline data + native-sky scripts'),
            ('moon export strip', 'real-sky/native-cloud-transfer.mjs', 'export function nativeDisplayCode(',
             '// export notes are not declarations\nexport function nativeDisplayCode(', 'build_moon native-cloud-transfer export strip'),
            # A host unit that carries `</body>` would receive the offline chunk tags inside its script.
            ('moon offline chunk tags', 'moon/src/moon-native.mjs', first_line, first_line + '// </body>\n',
             'build_moon offline </body> chunk tags'),
        ]
        for site, relative, old, new, message in sites:
            with self.subTest(site=site):
                self.expect_no_write(self.pristine, relative, old, new, message)

    # G-05 census: every .replace( / re.sub( in the two builders is count-checked or exempt with a reason.
    def test_substitution_census_has_no_unclassified_site(self):
        # Exempt sites: whole-text by design. Each entry is the exact source line (stripped) and its reason.
        exempt = {
            'tools/build_native.py': {
                r"def text_of(data):return data.decode('utf-8').replace('\r\n','\n').replace('\r','\n')  # == read_text() newline handling":
                    'universal-newline decoding of staged bytes',
                r"def rel(p):return str(p.relative_to(R)).replace('\\','/')": 'path separators',
                r"s=read(p);s=re.sub(r'^import .*?;\s*$', '',s,flags=re.M);s=re.sub(r'\bexport (?=(?:const|let|function|class|async function)\b)','',s)":
                    'import/export stripping; any leftover import/export raises Unbundled import/export',
                r"def inline_js(text):return text.replace('</script','<\\/script')": '</script escaping',
            },
            'tools/build_moon.py': {
                r"def inline(text):return text.replace('</script','<\\/script')": '</script escaping',
                r"sources={str(p.relative_to(root)).replace('\\','/'):sha(p.read_bytes()) for p in sorted({moon/'src'/n for n in WORKER_UNITS+HOST_UNITS+['moon-native.mjs','moon_kernel.c']})}":
                    'path separators',
            },
        }
        for relative, rules in exempt.items():
            lines = (ROOT / relative).read_text(encoding='utf-8').split('\n')
            sites = [(n + 1, line.strip()) for n, line in enumerate(lines) if '.replace(' in line or 're.sub(' in line]
            for number, line in sites:
                with self.subTest(file=relative, line=number):
                    self.assertIn(line, rules, f'unclassified substitution site {relative}:{number}: {line[:160]}')
            for line, reason in rules.items():
                self.assertIn(line, [s for _, s in sites], f'stale exemption ({reason}): {line[:80]}')
        for relative in ['tools/build_native.py', 'tools/build_moon.py', 'tools/native_star_bootstrap.py',
                         'tools/generated_outputs.py']:
            tree = ast.parse((ROOT / relative).read_text(encoding='utf-8'))
            self.assertEqual([n.lineno for n in ast.walk(tree) if isinstance(n, ast.Assert)], [],
                             relative + ' must not guard with assert (removed by python -O)')

    # G-06: stale owned outputs are removed; nothing outside the declared owned set is touched.
    def test_rebuild_removes_stale_owned_files_only(self):
        tree = self.fresh('stale')
        outside = {'moon/README-local.txt': 'local\n', 'moon/file-data/notes.txt': 'local\n',
                   'real-sky/native-local.mjs': '// local\n', 'real-sky/notices/LOCAL.txt': 'local\n'}
        stale = {'moon/file-data/stale-999.js': '/* stale */\n', 'real-sky/core/src/retired.mjs': '// stale\n'}
        for relative, text in {**outside, **stale}.items():
            (tree.path / relative).write_text(text, encoding='utf-8')
        # A forged previous inventory naming paths outside the owned set must not widen deletion.
        inventory = json.loads((tree.path / INVENTORY).read_bytes()) if (tree.path / INVENTORY).is_file() else \
            {'schema': 'salah-generated-inventory/1', 'files': {}}
        for relative in [ENTRY, 'moon/README-local.txt', 'README.md', '../outside.txt']:
            inventory['files'][relative] = {'bytes': 0, 'sha256': '0' * 64}
        (tree.path / INVENTORY).write_text(json.dumps(inventory), encoding='utf-8')
        r = tree.run()
        self.assertEqual(r.returncode, 0, r.stderr[-2000:])
        report = json.loads(r.stdout)
        self.assertEqual(sorted(report['removedPaths']), sorted(stale))
        for relative in stale:
            self.assertFalse((tree.path / relative).exists(), relative)
        for relative in [*outside, ENTRY]:
            self.assertTrue((tree.path / relative).is_file(), relative)
        # The tree is the committed tree plus the untouched outside files; the inventory is rewritten exactly.
        self.assertEqual(difference(self.committed, manifest(tree.path)),
                         {'changed': [], 'added': sorted(outside), 'removed': []})
        self.assertEqual(report['ignoredInventoryPaths'], sorted(['../outside.txt', 'README.md', ENTRY,
                                                                   'moon/README-local.txt']))

    def test_unreadable_inventory_fails_before_publish(self):
        tree = self.pristine
        if not (tree.path / INVENTORY).is_file():
            self.skipTest('no committed inventory to corrupt')
        self.expect_no_write(tree, INVENTORY, '"files"', '"filez"', 'Unreadable generated inventory')

    # G-07: an I/O fault during publish is reported with the replaced paths; a re-run restores parity.
    def test_publish_fault_reports_replaced_paths_and_rerun_restores_parity(self):
        tree = self.fresh('fault')
        for relative in ['real-sky/native-sky.js', 'moon/moon-host.js', 'index.html', 'moon/file-data/dem-000.js']:
            (tree.path / relative).write_text('/* damaged */\n', encoding='utf-8')
        r = tree.run(mode='publish-fault')
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('failed-during-publish', r.stderr)
        report = json.loads(r.stderr[r.stderr.index('{'):r.stderr.index('\n}') + 2])
        self.assertEqual(report['phase'], 'failed-during-publish')
        self.assertEqual(len(report['replaced']), 2, report)
        self.assertEqual(r.staging_leftovers, [], 'staging removed in finally')
        again = tree.run()
        self.assertEqual(again.returncode, 0, again.stderr[-2000:])
        clean = self.fresh('fault-control')
        self.assertEqual(clean.run().returncode, 0)
        self.assertEqual(difference(manifest(clean.path), manifest(tree.path)), NOTHING, 're-run restores parity')

    # Interruption before publish leaves the tree unchanged.
    def test_interruption_before_publish_writes_nothing(self):
        tree = self.pristine
        before = manifest(tree.path)
        r = tree.run(mode='interrupt-before-publish')
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('KeyboardInterrupt', r.stderr)
        self.assertEqual(difference(before, manifest(tree.path)), NOTHING)
        self.assertEqual(r.staging_leftovers, [])


if __name__ == '__main__':
    unittest.main()
