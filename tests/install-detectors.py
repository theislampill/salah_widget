#!/usr/bin/env python3
"""Original R0013 detector controls and discriminating, parse-valid mutants.

Uses the actual source prefix and actual detect_targets/producer functions.
Fixture CONFIGS are inputs, never copied detector implementations. Linux cannot
establish the Apple Bash floor; the empty-array mutant requires actual 3.2.
"""
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shlex
import subprocess
import sys
import tempfile


SOURCE = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / 'install.sh').resolve()
SOURCE_BYTES = SOURCE.read_bytes()
TEXT = SOURCE_BYTES.decode('utf-8')
MARKER = "\nprintf '\\nSalah Widget Installer\\n\\n'"
if TEXT.count(MARKER) != 1:
    raise SystemExit('Actual installer entry boundary drifted')
LIBRARY = TEXT.split(MARKER)[0]
BASH = os.environ.get('SALAH_TEST_BASH', '/bin/bash')
ROOT = Path(tempfile.mkdtemp(prefix='salah-detectors-')).resolve()
ROOT.chmod(0o700)
(ROOT / 'home').mkdir(mode=0o700)
(ROOT / 'tmp').mkdir(mode=0o700)
VERSION = subprocess.check_output([BASH, '--version'], text=True).splitlines()[0]
IS_32 = 'version 3.2.' in VERSION
RESULTS = []
OBSERVATIONS = {}
APPLICABILITY = []
ENV = dict(os.environ, HOME=str(ROOT / 'home'), TMPDIR=str(ROOT / 'tmp'), DRY_RUN='1', NO_OPEN='1', SALAH_INSTALL_SOURCE='github', LC_ALL='C')
ENV.pop('BASH_ENV', None)


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def config(family, path, key='fixture', executable=''):
    return '|'.join((key, key, family, str(path), executable, 'new-id', 'old-id', 'fixture:store', 'fixture:manager', 'fixture:newtab'))


def create(name, family, profiles=(), present=True):
    path = ROOT / name
    if present:
        path.mkdir()
    for profile in profiles:
        child = path / profile
        child.mkdir()
        if family == 'firefox':
            (child / 'extensions.json').write_text('{"addons":[]}', encoding='utf-8')
    return path


def run(name, library, configs, before='', after=''):
    script = library + '\n' + before + '\nCONFIGS=()\n'
    for value in configs:
        script += 'CONFIGS+=(' + shlex.quote(value) + ')\n'
    script += 'TARGETS=(); TARGET_COUNT=0\ndetect_targets\nprintf "COUNT=%s\\n" "$TARGET_COUNT"\n'
    script += '[ "$TARGET_COUNT" -eq 0 ] || printf "%s\\n" "${TARGETS[@]}"\n' + after
    parsed = subprocess.run([BASH, '-n'], input=script, text=True, capture_output=True)
    require(parsed.returncode == 0, 'Invalid test/mutant shell syntax: ' + parsed.stderr)
    actual = subprocess.run([BASH, '--noprofile', '--norc', '-c', script], env=ENV, capture_output=True, text=True, timeout=20)
    lines = actual.stdout.splitlines()
    count = int(lines[0][6:]) if lines and lines[0].startswith('COUNT=') else None
    rows = [line.split('|') for line in lines[1:]] if count is not None else []
    observation = dict(exit=actual.returncode, stdout=actual.stdout, stderr=actual.stderr, count=count, rows=rows,
                       script_sha256=hashlib.sha256(script.encode()).hexdigest(), parse_exit=parsed.returncode)
    OBSERVATIONS[name] = observation
    (ROOT / (name + '.sh')).write_text(script, encoding='utf-8')
    (ROOT / (name + '.json')).write_text(json.dumps(observation, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    return observation


def exact(result, expected):
    """Only actual path/key/cardinality observations determine detector health."""
    return (result['exit'] == 0 and result['count'] == len(expected) and
            [(row[1], row[5]) for row in result['rows'] if len(row) >= 13] == expected and
            len(result['rows']) == len(expected))


def check(name, action):
    try:
        detail = action()
        RESULTS.append(dict(case=name, pass_=True, detail=detail))
    except Exception as error:
        RESULTS.append(dict(case=name, pass_=False, error=str(error)))


def controls(family):
    prefix = family + '-controls'
    absent = create(prefix + '-absent', family, present=False)
    empty = create(prefix + '-empty', family)
    one_name = 'Default' if family == 'chromium' else 'Only Profile'
    one = create(prefix + '-one', family, [one_name])
    names = ['Default', 'Profile One مدينة', 'Profile Back\\Slash'] if family == 'chromium' else ['One Profile', 'مدينة', 'Back\\Slash']
    many = create(prefix + '-many', family, names)
    executable = ROOT / (prefix + '-browser')
    executable.write_text('#!/bin/sh\nexit 99\n')
    executable.chmod(0o700)
    cases = [
        ('absent', [config(family, absent)], []),
        ('empty-data-fallback', [config(family, empty)], [('fixture', '')]),
        ('executable-fallback', [config(family, absent, executable=str(executable))], [('fixture', '')]),
        ('one', [config(family, one)], [('fixture', str(one / one_name))]),
        ('multiple-unicode-backslash', [config(family, many)], [('fixture', str(many / name)) for name in sorted(names)]),
        ('per-config-reset', [config(family, many, 'first'), config(family, empty, 'second'), config(family, absent, 'third')],
         [('first', str(many / name)) for name in sorted(names)] + [('second', '')]),
    ]
    for suffix, configs, expected in cases:
        actual = run(prefix + '-' + suffix, LIBRARY, configs)
        require(exact(actual, expected), suffix + ': ' + repr(actual))
    return dict(cases=[x[0] for x in cases], actual_paths=[str(many / n) for n in sorted(names)])


def final_line(family):
    name = 'Profile Last\\مدينة' if family == 'chromium' else 'Last\\مدينة'
    path = create(family + '-final-line', family, [name])
    # This one producer boundary deliberately emits a final non-newline line;
    # the consumer under test remains the exact actual detector loop.
    producer = family + '_profiles(){ printf "%s" ' + shlex.quote(str(path / name)) + '; }\n'
    actual = run(family + '-unterminated', LIBRARY, [config(family, path)], producer)
    require(exact(actual, [('fixture', str(path / name))]), repr(actual))
    return dict(producer_override='final line framing only', path=str(path / name))


def loop_for(family):
    expression = r'while IFS= read -r p \|\| \[ -n "\$p" \]; do profiles\+=\("\$p"\); profile_count=\$\(\(profile_count \+ 1\)\); done < <\(' + family + r'_profiles "\$user_data"\)'
    matches = re.findall(expression, LIBRARY)
    require(len(matches) == 1, 'Actual profile loop changed: ' + family)
    return matches[0]


def mutant(kind, family):
    names = ['Profile Back\\مدينة'] if family == 'chromium' else ['Back\\مدينة']
    path = create(kind + '-' + family, family, names)
    empty = create(kind + '-' + family + '-empty', family)
    configs = [config(family, path, 'first'), config(family, empty, 'second')]
    expected = [('first', str(path / names[0])), ('second', '')]
    old = loop_for(family)
    before = ''
    if kind == 'mapfile':
        replacement = 'mapfile -t profiles < <(' + family + '_profiles "$user_data"); profile_count=${#profiles[@]}'
        if not IS_32:
            before = 'enable -n mapfile\n'
        boundary = 'actual Apple-era builtin absence' if IS_32 else 'modern shell with only mapfile builtin disabled; supplemental, not Apple proof'
    elif kind == 'subshell':
        replacement = family + '_profiles "$user_data" | ' + old.split(' < <(')[0]
        boundary = 'actual pipeline loses current-shell array/count'
    elif kind == 'read-r':
        replacement = old.replace('read -r p', 'read p', 1)
        boundary = 'actual read loses literal backslash in profile path'
    else:
        raise AssertionError(kind)
    changed = LIBRARY.replace(old, replacement, 1)
    healthy = run(kind + '-' + family + '-healthy', LIBRARY, configs, before)
    broken = run(kind + '-' + family + '-mutant', changed, configs, before)
    require(exact(healthy, expected), 'Healthy paired control failed: ' + repr(healthy))
    require(not exact(broken, expected), 'Parse-valid mutant survived actual detector oracle: ' + repr(broken))
    return dict(boundary=boundary, healthy_exit=healthy['exit'], mutant_exit=broken['exit'], actual_mutant_rows=broken['rows'])


def empty_array_mutant(family):
    empty = create('empty-array-' + family, family)
    guard = '      [ "$profile_count" -gt 0 ] || continue\n'
    require(LIBRARY.count(guard) == 2, 'Actual empty-array guards changed')
    # Remove only the selected family's guard inside its actual detector branch.
    fn = LIBRARY.index('detect_targets() {')
    at = LIBRARY.index(guard, fn)
    if family == 'firefox':
        at = LIBRARY.index(guard, at + len(guard))
    changed = LIBRARY[:at] + LIBRARY[at + len(guard):]
    configs = [config(family, empty)]
    expected = [('fixture', '')]
    healthy = run('empty-array-' + family + '-healthy', LIBRARY, configs)
    broken = run('empty-array-' + family + '-mutant', changed, configs)
    require(exact(healthy, expected), 'Healthy native empty-array guard failed: ' + repr(healthy))
    require(broken['exit'] != 0 and 'unbound variable' in broken['stderr'], 'Native Bash3.2 nounset mutant survived: ' + repr(broken))
    return dict(actual_bash=VERSION, healthy_exit=healthy['exit'], mutant_exit=broken['exit'], stderr=broken['stderr'])


for family in ('chromium', 'firefox'):
    check(family + ' actual producer/detector native cardinality and exact bytes', lambda f=family: controls(f))
    check(family + ' unterminated final producer line', lambda f=family: final_line(f))
    for mutation in ('mapfile', 'subshell', 'read-r'):
        check(family + ' parse-valid ' + mutation + ' mutant and healthy pair', lambda k=mutation, f=family: mutant(k, f))
    if IS_32:
        check(family + ' native Bash3.2 empty-array nounset mutant', lambda f=family: empty_array_mutant(f))
    else:
        APPLICABILITY.append(dict(case=family + ' empty-array nounset mutant', executed=False,
                                  disposition='Requires actual Apple /bin/bash 3.2; modern Bash accepts the empty expansion. Not counted as a PASS here.'))

print(json.dumps(dict(source=str(SOURCE), source_sha256=hashlib.sha256(SOURCE_BYTES).hexdigest(),
                      test_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                      host=dict(system=platform.system(), platform=platform.platform(), bash=BASH, version=VERSION),
                      fixture=str(ROOT), results=RESULTS, applicability=APPLICABILITY), indent=2, ensure_ascii=False))
sys.exit(0 if RESULTS and all(row['pass_'] for row in RESULTS) else 1)
