"""Prepared digest-guarded mutation; run each repository target via its window."""
from pathlib import Path
import ast
import hashlib
import sys

base = Path('/workspace/scratch/15b8fb6ac4c2')
work = base / 'r000b-work'
evidence = base / 'evidence/native-healthy-refresh-extension'
kind = sys.argv[1]

if kind == 'driver':
    target = work / 'tools/qa/run_r000b_withdrawal.py'
    expected = '73afb4d772e32bd21f2697777914f3db8d2d28c3833271ef669037b079fb28bc'
    text = target.read_text()
    replacements = [
        ('# R000B_HN2_HN3_HN4_NATIVE_ORACLES_V2\n', '# R000B_HN2_HN3_HN4_NATIVE_ORACLES_V2\n# R000B_F01_HEALTHY_REFRESH_EXTENSION_V1\n'),
        ('import base64\n', 'import base64\nimport datetime\n'),
        ('EXPECTED_COVERAGE = [0.92, 0.90, 0.60]\n', '''HEALTHY_REFRESH_PROGRESS = """() => {
  const f=window.__withdrawalFixture;
  if(f?.state==='error')throw Error(f.error);
  if(f?.state!=='ready')throw Error('Expected the existing ready fixture');
  return {elapsedMs:performance.now()-f.started,maxElapsedMs:f.maxElapsedMs,
          latest:f.latest,ledger:f.ledger.filter(request=>request.kind==='weather')};
}"""
EXPECTED_COVERAGE = [0.92, 0.90, 0.60]
'''),
        ('\ndef phase_progress(a, b):\n', '\n' + (evidence / 'extension-functions.py').read_text() + '\n\ndef phase_progress(a, b):\n'),
        ("                'fullOverride': args.mode == 'full', 'recoveredWatchSeconds': 30,\n",
         "                'fullOverride': args.mode == 'full', 'recoveredWatchSeconds': 30,\n                'healthyRefresh': 'Required owned ordinary weather replacement after genuine model recovery; reuse recovered watch captures or passively wait within unchanged240 s fixture cap; no forced capture ordering',\n"),
        ('\n        fixture = page.evaluate(FIXTURE)\n', '\n' + (evidence / 'acquisition-snippet.py').read_text() + '        fixture = page.evaluate(FIXTURE)\n'),
        ("        row['fixture'] = fixture\n", "        row['fixture'] = fixture\n" + (evidence / 'evidence-snippet.py').read_text()),
    ]
elif kind == 'tests':
    target = work / 'tests/weather-no-timetable-native-oracles.test.py'
    expected = '3d60eec118064858d2294955a690a80d88dcb5021376e5362b5f2f6be44f0f82'
    text = target.read_text()
    replacements = [
        ('import ast\n', '# R000B_F01_HEALTHY_REFRESH_ORACLE_CONTROLS_V1\nimport ast\nimport datetime\n'),
        ("         'actual_empty', 'effects_off', 'joined_empty', 'independent_celestial', 'healthy_cloud'}",
         "         'actual_empty', 'effects_off', 'joined_empty', 'independent_celestial', 'healthy_cloud',\n         'healthy_refresh_record', '_healthy_refresh_request', '_healthy_refresh_receipt',\n         '_healthy_refresh_sample', 'healthy_refresh_pair', 'healthy_refresh_evidence'}"),
        ("    namespace = {'math': math, 're': re, 'EXPECTED_COVERAGE': [0.92, 0.90, 0.60]}\n",
         "    namespace = {'math': math, 're': re, 'datetime': datetime, 'EXPECTED_COVERAGE': [0.92, 0.90, 0.60],\n                 'INITIAL_SOURCE_UTC': 1788900300000}\n"),
        ("\nif __name__ == '__main__':\n", '\n' + (evidence / 'extension-tests.py').read_text() + "\n\nif __name__ == '__main__':\n"),
    ]
else:
    raise ValueError('Expected driver or tests')

assert hashlib.sha256(target.read_bytes()).hexdigest() == expected, 'Target drift before prepared edit'
for old, new in replacements:
    assert text.count(old) == 1, old[:120]
    text = text.replace(old, new)
ast.parse(text, filename=str(target))
if len(sys.argv) > 2 and sys.argv[2] == '--prepare':
    target = evidence / ('prepared-driver.py' if kind == 'driver' else 'prepared-tests.py')
target.write_text(text)
print(hashlib.sha256(target.read_bytes()).hexdigest(), target)
