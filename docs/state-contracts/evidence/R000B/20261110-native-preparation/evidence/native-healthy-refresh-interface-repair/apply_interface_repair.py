"""Prepared HR1/HR2 repair; existing repository files require mutation windows."""
from pathlib import Path
import ast
import hashlib
import json
import sys

base = Path('/workspace/scratch/15b8fb6ac4c2')
work = base / 'r000b-work'
evidence = base / 'evidence/native-healthy-refresh-interface-repair'
proof = json.loads((evidence / 'old-v3-discriminators.json').read_text())
assert proof['oldApiInvocationCompletedWithoutTypeError'] is True
assert proof['HR1']['recordSelected'] is False and proof['HR1']['fullSampleHealthy'] is False
assert proof['HR2']['recordSelected'] is True and proof['HR2']['requestMatched'] is False
kind = sys.argv[1]

def change(old, new, count=1):
    global text
    assert text.count(old) == count, (old[:120], text.count(old), count)
    text = text.replace(old, new)

if kind == 'driver':
    target = work / 'tools/qa/run_r000b_withdrawal.py'
    expected = '9c4931b82f39f559f0e876943c1d0bb1bd0e2c43a25e9501d8fe661aba76420e'
    text = target.read_text()
    helpers_text = (evidence / 'repair-helpers.py').read_text()
    helpers = {node.name: ast.get_source_segment(helpers_text, node) for node in ast.parse(helpers_text).body if isinstance(node, ast.FunctionDef)}
    old_functions = {node.name: ast.get_source_segment(text, node) for node in ast.parse(text).body if isinstance(node, ast.FunctionDef)}
    change('# R000B_F01_HEALTHY_REFRESH_EXTENSION_V1\n', '# R000B_F01_HEALTHY_REFRESH_EXTENSION_V1\n# R000B_HR1_HR2_INTERFACE_REPAIR_V1\n')
    change("          latest:f.latest,ledger:f.ledger.filter(request=>request.kind==='weather')};",
           "          clockOrigin:{started:f.started,startUtc:f.startUtc},\n          latest:f.latest,ledger:f.ledger.filter(request=>request.kind==='weather')};")
    change('\ndef healthy_refresh_record(state):\n', '\n' + helpers['_healthy_refresh_target_projection'] + '\n\n\n' + helpers['_healthy_refresh_clock'] + '\n\n\ndef healthy_refresh_record(state):\n')
    change("    target = state.get('target')\n", "    target = state.get('target')\n    projection = _healthy_refresh_target_projection(target)\n")
    change("            and receipt.get('target') == target == raw.get('target')\n",
           "            and projection is not None and receipt.get('target') == projection\n            and target == raw.get('target')\n")
    change(old_functions['_healthy_refresh_request'], helpers['_healthy_refresh_request'])
    change("                and raw.get('target') == receipts[0]['target']\n",
           "                and raw.get('target') == state.get('target')\n                and _healthy_refresh_target_projection(state.get('target')) == receipts[0]['target']\n                and state.get('runtimeGeneration') == receipts[0]['target']['generation']\n")
    change('def healthy_refresh_pair(before, after, ledger):', 'def healthy_refresh_pair(before, after, ledger, clock=None):')
    change("              'beforeRecord': left, 'afterRecord': right, 'reason': None}",
           "              'beforeRecord': left, 'afterRecord': right, 'clockOrigin': clock, 'reason': None}")
    change('_healthy_refresh_request(left, before, ledger)', '_healthy_refresh_request(left, before, ledger, clock)')
    change('_healthy_refresh_request(right, after, ledger)', '_healthy_refresh_request(right, after, ledger, clock)')
    change('def healthy_refresh_evidence(before, after, passive, full_samples, ledger, mode):',
           'def healthy_refresh_evidence(before, after, passive, full_samples, ledger, mode, clock=None):')
    change('    pair = healthy_refresh_pair(before, after, ledger)\n', '    pair = healthy_refresh_pair(before, after, ledger, clock)\n')
    change("            refresh_progress = page.evaluate(HEALTHY_REFRESH_PROGRESS)\n            if refresh_progress['maxElapsedMs'] != 240000:",
           "            refresh_progress = page.evaluate(HEALTHY_REFRESH_PROGRESS)\n            refresh_clock_origin = refresh_progress.get('clockOrigin')\n            if _healthy_refresh_clock(recovered, refresh_clock_origin) is None:\n                raise ValueError('Observed fixture clock origin is missing or inconsistent with native motion')\n            if refresh_progress['maxElapsedMs'] != 240000:")
    change("healthy_refresh_pair(recovered, final, refresh_progress['ledger'])",
           "healthy_refresh_pair(recovered, final, refresh_progress['ledger'], refresh_clock_origin)", count=2)
    change("                'beforeStage': 'recovered', 'afterStage': refresh_after_stage,\n",
           "                'beforeStage': 'recovered', 'afterStage': refresh_after_stage, 'clockOrigin': refresh_clock_origin,\n")
    change("            while not refresh_pair['ok']:\n                remaining =",
           "            while not refresh_pair['ok']:\n                if refresh_progress.get('clockOrigin') != refresh_clock_origin:\n                    raise ValueError('Observed fixture clock origin changed during healthy refresh acquisition')\n                remaining =")
    change("                    refresh_progress = page.evaluate(HEALTHY_REFRESH_PROGRESS)\n                    refresh_pair =",
           "                    refresh_progress = page.evaluate(HEALTHY_REFRESH_PROGRESS)\n                    if refresh_progress.get('clockOrigin') != refresh_clock_origin:\n                        raise ValueError('Observed fixture clock origin changed at the healthy refresh capture')\n                    refresh_pair =")
    change("        row['fixture'] = fixture\n        if args.expect == 'withdrawal':\n            refresh_observations =",
           "        row['fixture'] = fixture\n        if args.expect == 'withdrawal':\n            if {'started': fixture.get('started'), 'startUtc': fixture.get('startUtc')} != refresh_clock_origin:\n                raise ValueError('Final fixture clock origin differs from the observed acquisition origin')\n            refresh_observations =")
    change("                [observation['state'] for observation in refresh_observations], fixture['ledger'], args.mode)\n",
           "                [observation['state'] for observation in refresh_observations], fixture['ledger'], args.mode, refresh_clock_origin)\n")
elif kind == 'tests':
    target = work / 'tests/weather-no-timetable-native-oracles.test.py'
    expected = '36b1d515b8e101365065695ab3a92540f58e73ae60c0ecc450df5410332f0209'
    text = target.read_text()
    change('# R000B_F01_HEALTHY_REFRESH_ORACLE_CONTROLS_V1\n', '# R000B_F01_HEALTHY_REFRESH_ORACLE_CONTROLS_V1\n# R000B_HR1_HR2_INTERFACE_CONTROLS_V1\n')
    change("         'healthy_refresh_record', '_healthy_refresh_request', '_healthy_refresh_receipt',\n",
           "         '_healthy_refresh_target_projection', '_healthy_refresh_clock',\n         'healthy_refresh_record', '_healthy_refresh_request', '_healthy_refresh_receipt',\n")
    change("def healthy_refresh_case(refresh_ms=180000, end_ms=None, mode='default'):",
           "def healthy_refresh_case(refresh_ms=180000, end_ms=None, mode='default', performance_origin=125.25):")
    change("    target = {'generation': 7, 'lat': 24.7136, 'lon': 46.6753}\n",
           "    clock = {'started': performance_origin, 'startUtc': REFRESH_START_UTC}\n    target = {'generation': 7, 'lat': 24.7136, 'lon': 46.6753, 'intent': 'fixed-site', 'source': 'hash',\n              'accuracyM': None, 'acquiredAt': None, 'provider': None, 'area': None, 'bounds': None}\n")
    change("                'target': target.copy(), 'lane': 'live',\n",
           "                'target': {'generation': 7, 'lat': 24.7136, 'lon': 46.6753}, 'lane': 'live',\n")
    change("        moved = advance(seed, at, seconds=0 if mode == 'reduced' else (at - start_ms) / 1000)['motion']\n",
           "        moved = advance(seed, at, seconds=0 if mode == 'reduced' else (at - start_ms) / 1000)['motion']\n        moved['lastRt'] = clock['started'] + moved['elapsedRtMs']\n")
    change("                                'deadlineAt': REFRESH_START_UTC + at + 12000},\n",
           "                                'deadlineAt': clock['started'] + at + 10000},\n")
    change("            'old': old, 'new': new, 'refreshMs': refresh_ms}\n",
           "            'old': old, 'new': new, 'refreshMs': refresh_ms, 'clock': clock}\n")
    change("                                         case['full'], case['ledger'], case['mode'])\n",
           "                                         case['full'], case['ledger'], case['mode'], case.get('clock'))\n")
    change("ORACLE.healthy_refresh_pair(case['before'], case['after'], case['ledger'])",
           "ORACLE.healthy_refresh_pair(case['before'], case['after'], case['ledger'], case.get('clock'))", count=5)
    change("                    case['ledger'][-1]['nativeOwner']['deadlineAt'] = case['new']['retrievedAt']\n",
           "                    case['ledger'][-1]['nativeOwner']['deadlineAt'] = case['clock']['started'] + (case['new']['retrievedAt'] - case['clock']['startUtc'])\n")
    change("\nif __name__ == '__main__':\n", '\n' + (evidence / 'interface-tests.py').read_text() + "\n\nif __name__ == '__main__':\n")
else:
    raise ValueError('Expected driver or tests')

assert hashlib.sha256(target.read_bytes()).hexdigest() == expected, 'Repository target drift before mutation'
ast.parse(text, filename=str(target))
if len(sys.argv) > 2 and sys.argv[2] == '--prepare':
    target = evidence / ('prepared-driver.py' if kind == 'driver' else 'prepared-tests.py')
target.write_text(text)
print(hashlib.sha256(target.read_bytes()).hexdigest(), target)
