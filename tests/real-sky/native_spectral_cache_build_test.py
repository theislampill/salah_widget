"""R0027 generator contract for the authored spectral retention transform.

The transform must apply exactly once to the digest-pinned immutable vendor input, fail
closed (precise diagnostic, nothing written) on digest or anchor drift, refuse a second
application, introduce no identifier that collides inside the concatenated bundles, and be
what the REAL builder (tools/build_native.py) writes to the generated core.

Mutation controls at the bottom load disposable in-memory mutants of the transform or of
the builder and require these same checks to fail with an AssertionError.
Run: python -m unittest tests/real-sky/native_spectral_cache_build_test.py -v
"""
from pathlib import Path
import ast, hashlib, importlib.util, re, shutil, subprocess, sys, tempfile, types, unittest

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / 'tools'
VENDOR = ROOT / 'vendor/real-sky/src/spectral.mjs'
GENERATED = ROOT / 'real-sky/core/src/spectral.mjs'
TRANSFORM_PATH = TOOLS / 'native_core_spectral_cache.py'
JS_WORDS = {'if', 'const', 'let', 'return', 'new', 'Map', 'function'}


def load_transform(text=None):
    text = TRANSFORM_PATH.read_text(encoding='utf-8') if text is None else text
    module = types.ModuleType('native_core_spectral_cache_under_test')
    exec(compile(text, str(TRANSFORM_PATH), 'exec'), module.__dict__)
    return module


def core_list(builder_text):
    match = re.search(r'^core=(\[.*?\])$', builder_text, re.M)
    return ast.literal_eval(match.group(1))


def concat_inputs():
    """Every source text concatenated into one scope by build_native.py."""
    builder = (TOOLS / 'build_native.py').read_text(encoding='utf-8')
    paths = [ROOT / 'vendor/real-sky' / p for p in core_list(builder)]
    paths += sorted((ROOT / 'real-sky').glob('native-*.mjs'))
    paths += [ROOT / 'real-sky/native-host-hooks.js', ROOT / 'src/native/index.html']
    return {str(p.relative_to(ROOT)).replace('\\', '/'): p.read_text(encoding='utf-8') for p in paths}


def free_identifiers(js):
    js = '\n'.join(line for line in js.split('\n') if not line.lstrip().startswith('//'))
    return {m.group(1) for m in re.finditer(r'(?<![.\w$])([A-Za-z_$][\w$]*)', js)
            if not m.group(1).isdigit()} - JS_WORDS


# ---- checks (shared by the ordinary tests and the mutation controls) ---------------------
def check_applies_once(t):
    source = VENDOR.read_bytes()
    t.assertEqual(hashlib.sha256(source).hexdigest(), t.mod.SOURCE_SHA256, 'pinned scientific input')
    out = t.mod.bound_spectral_cache(source)
    t.assertEqual(hashlib.sha256(out).hexdigest(), t.mod.OUTPUT_SHA256, 'pinned output')
    text, result = source.decode('utf-8'), out.decode('utf-8')
    for before, after in t.mod.SPANS:
        t.assertEqual(text.count(before), 1)
        t.assertEqual(result.count(after), 1)
    # The allowed diff: undoing exactly the whitelisted spans restores the vendor bytes.
    undone = result
    for before, after in t.mod.SPANS:
        undone = undone.replace(after, before, 1)
    t.assertEqual(undone, text, 'nothing outside the whitelisted spans changed')
    t.assertEqual(out, t.mod.bound_spectral_cache(source), 'deterministic')
    return out


def check_digest_guard(t):
    source = VENDOR.read_bytes()
    variants = {
        'trailing byte': source + b'\n',
        'new science, anchors intact': source.replace(b'i<48', b'i<47', 1),
        'already transformed': t.mod.bound_spectral_cache(source),
    }
    for name, variant in variants.items():
        with t.assertRaisesRegex(ValueError, 'R0027 spectral source drift', msg=name):
            t.mod.bound_spectral_cache(variant)


def check_anchor_guard(t):
    text = VENDOR.read_text(encoding='utf-8')
    for before, _ in t.mod.SPANS:
        for name, variant in {'absent': text.replace(before, before[:-1] + ' ;', 1),
                              'duplicated': text.replace(before, before + before, 1)}.items():
            with t.assertRaisesRegex(ValueError, 'R0027 spectral anchor', msg=name + ' ' + before[:30]):
                t.mod.apply_spans(variant)


def check_identifiers(t):
    added = set()
    for before, after in t.mod.SPANS:
        added |= free_identifiers(after) - free_identifiers(before)
    t.assertEqual(added, set(t.mod.INTRODUCED_IDENTIFIERS), 'declared new identifiers')
    for name in added:
        for path, text in concat_inputs().items():
            t.assertIsNone(re.search(r'(?<![\w$])' + re.escape(name) + r'(?![\w$])', text),
                           f'{name} collides with {path}')
        t.assertTrue(name.startswith('sf'), 'module-local sf prefix')


def run_builder(tree, builder_text=None, transform_text=None):
    """Run the REAL builder in a disposable tree that carries only tools/ and the core inputs."""
    shutil.copytree(TOOLS, tree / 'tools', ignore=shutil.ignore_patterns('__pycache__', 'cp9', 'qa', 'qualification'))
    if builder_text is not None:
        (tree / 'tools/build_native.py').write_text(builder_text, encoding='utf-8')
    if transform_text is not None:
        (tree / 'tools/native_core_spectral_cache.py').write_text(transform_text, encoding='utf-8')
    builder = (TOOLS / 'build_native.py').read_text(encoding='utf-8')
    for p in core_list(builder) + ['src/reference-worker-client.mjs', 'src/latest-render-queue.mjs']:
        target = tree / 'vendor/real-sky' / p
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / 'vendor/real-sky' / p, target)
    return subprocess.run([sys.executable, str(tree / 'tools/build_native.py')], cwd=tree,
                          capture_output=True, text=True, timeout=120)


def check_builder_invokes(t, builder_text=None):
    with tempfile.TemporaryDirectory() as d:
        tree = Path(d)
        r = run_builder(tree, builder_text)
        # The disposable tree stops at the first input it does not carry (licence notices),
        # strictly after the complete core-copy stage that owns both authored transforms.
        t.assertIn('LICENSE-CODE.txt', r.stderr)
        t.assertEqual((tree / 'real-sky/core/src/spectral.mjs').read_bytes(),
                      t.mod.bound_spectral_cache(VENDOR.read_bytes()), 'builder writes transform(vendor)')
        sys.path.insert(0, str(TOOLS))
        try:
            from native_core_horizon import correct_horizon
        finally:
            sys.path.pop(0)
        renderer = 'src/physical-sky-renderer.mjs'
        t.assertEqual((tree / 'real-sky/core' / renderer).read_bytes(),
                      correct_horizon((ROOT / 'vendor/real-sky' / renderer).read_bytes()), 'horizon transform preserved')


def check_builder_fails_closed(t):
    with tempfile.TemporaryDirectory() as d:
        tree = Path(d)
        shutil.copytree(TOOLS, tree / 'tools', ignore=shutil.ignore_patterns('__pycache__', 'cp9', 'qa', 'qualification'))
        builder = (TOOLS / 'build_native.py').read_text(encoding='utf-8')
        for p in core_list(builder):
            target = tree / 'vendor/real-sky' / p
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / 'vendor/real-sky' / p, target)
        spectral = tree / 'vendor/real-sky/src/spectral.mjs'
        spectral.write_bytes(spectral.read_bytes().replace(b'i<48', b'i<47', 1))
        r = subprocess.run([sys.executable, str(tree / 'tools/build_native.py')], cwd=tree,
                           capture_output=True, text=True, timeout=120)
        t.assertNotEqual(r.returncode, 0)
        t.assertIn('R0027 spectral source drift', r.stderr)
        t.assertFalse((tree / 'real-sky/core/src/spectral.mjs').exists(), 'no transformed output written')
        t.assertFalse((tree / 'real-sky/core/src/optics.mjs').exists(), 'build stopped at the drift')
        for bundle in ['real-sky/native-worker.js', 'real-sky/native-sky.js', 'index.html', 'offline.html']:
            t.assertFalse((tree / bundle).exists(), bundle)


class SpectralCacheTransformTest(unittest.TestCase):
    def setUp(self):
        self.mod = load_transform()

    def test_transform_applies_exactly_once_with_whitelisted_diff(self):
        check_applies_once(self)

    def test_generated_core_is_transform_of_vendor(self):
        self.assertEqual(GENERATED.read_bytes(), self.mod.bound_spectral_cache(VENDOR.read_bytes()))

    def test_digest_drift_and_second_application_fail_closed(self):
        check_digest_guard(self)

    def test_anchor_drift_fails_closed(self):
        check_anchor_guard(self)

    def test_introduced_identifier_cannot_collide_in_bundles(self):
        check_identifiers(self)

    def test_real_builder_invokes_transform_and_keeps_horizon(self):
        check_builder_invokes(self)

    def test_real_builder_fails_closed_on_drift(self):
        check_builder_fails_closed(self)


MUTANTS = [
    # (name, file, from, to, check)
    ('m7 transform without digest guard', 'transform',
     "    if hashlib.sha256(source).hexdigest() != SOURCE_SHA256:\n",
     "    if False:\n", check_digest_guard),
    ('m8 anchor drift silently accepted', 'transform',
     "        if text.count(before) != 1:\n", "        if False:\n", check_anchor_guard),
    ('m10 constant collides with a bundle identifier', 'transform',
     'sfFitCacheLimit', 'sfWeights', check_identifiers),
    ('m10b constant collides with another module', 'transform',
     'sfFitCacheLimit', 'clamp', check_identifiers),
    ('bypass generator invocation', 'builder',
     " elif p=='src/spectral.mjs':target.write_bytes(bound_spectral_cache((S/p).read_bytes()))\n", '',
     lambda t: check_builder_invokes(t, t.builder)),
]


class SpectralCacheTransformMutationControls(unittest.TestCase):
    def test_each_mutant_is_detected_by_an_assertion(self):
        transform = TRANSFORM_PATH.read_text(encoding='utf-8')
        builder = (TOOLS / 'build_native.py').read_text(encoding='utf-8')
        for name, kind, old, new, check in MUTANTS:
            with self.subTest(name):
                original = transform if kind == 'transform' else builder
                self.assertEqual(original.count(old) >= 1, True, 'declared mutation location')
                # healthy run passes
                self.mod, self.builder = load_transform(), None
                check(self)
                mutated = original.replace(old, new)
                if kind == 'transform':
                    self.mod = load_transform(mutated)
                else:
                    self.builder = mutated
                with self.assertRaises(AssertionError) as killed:
                    check(self)
                print(f'MUTANT {name}: killed by {check.__name__ if hasattr(check, "__name__") else "check"}: '
                      + str(killed.exception).splitlines()[0][:200], file=sys.stderr)


if __name__ == '__main__':
    unittest.main()
