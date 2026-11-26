#!/usr/bin/env python3
"""Emit the initial native command plan. This entry never launches a browser.

Run only after prepare.py. --out must be a new owner-private directory. Its
r0035-plan.json and the JSON on stdout contain private paths and must be retained
inside the encrypted capture. An isolated coordinator executes the declared argv
sequentially, captures both streams, and adjudicates the result files separately
from subprocess exit codes. No shell interpolation is needed.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

from prepare import BASELINE, RESEARCH, digest, validate_prepared, verify_generated, write_json
from r002f_prepare import BASE_INDEX, COMBINED_INDEX, BASE_INVENTORY, COMBINED_INVENTORY, PATCH
from r0040_capture_prepare import load_contract as load_r0040_contract
import r0035_stage_materialize as stage_material

HERE = Path(__file__).resolve().parent
R002F_PROBE_SHA256 = '673c0656d8e2d8e1c343d1258be5070fa9447f3f43878460791ea8570468558f'
WORK_ORDERS = ('R0040', 'R003F', 'R0035', 'R002F')
STAR_DEFAULTS = {'guard': 'default', 'scope': 'all', 'mode': 'both'}
R003F_MATERIALIZATION = 'fab2e2ad49a14eee2ba715fb75365fa4b0abfa48a1d8b60247343ad29b1021e5'
R0040_MANIFEST = HERE.parents[2]/'docs/state-contracts/evidence/R0040/native-capture-preflight.json'
R0040_MANIFEST_SHA256 = '267f2fd8ac130c049430ffdaa0fd50b72457c60084b49360346748cc940f6b73'
R0040_CAPTURE_WRAPPER_SHA256 = 'd252e345225c0d3565c0c2a321324ca206083ba371eb43654193d422f9b2235f'
R0040_PREPARER_SHA256 = '4ba6328ee9fe96aec4a96109c58d0d67e0d3e434756829fbe247816bcd001f68'
R0040_CAPTURE_MODES = ('capture', 'capture-dateonly')
R0040_DATEONLY_WRAPPER_SHA256 = '214d4a3c6cb13dbfa69cf0330444aeb9f71d9816b43129091c93bb3121489c44'
R0040_DATEONLY_ADMITTED = 'ADMITTED_DATE_ONLY_FOR_OFFLINE_VERIFICATION'
R0035_STAGE_WRAPPER_SHA256 = '8c3838b2ba01d6a4114b5de0aa2401134bb0cea3918dcba4fe1237997e53c99b'
R0035_STAGE_MATERIALIZER_SHA256 = '1890dbdeacf3bcd3fc7f9624a8a970770ae4dbb43f6987e43919c7161e17bf4a'


def stage_mode(enabled, selected, stars, retained=False):
    if type(enabled) is not bool:
        raise ValueError('R0035 stage observation must be boolean')
    if enabled and ('R0035' not in selected or stars['mode'] != 'timing' or retained):
        raise ValueError('R0035 stage observation requires selected timing only and no per-event retention wrapper')
    return enabled


def original_star_plan(prepared, guard='default', scope='all'):
    star_controls({'guard': guard, 'scope': scope})
    arms = {'main': {'root': str(Path(prepared['trees']['main']['root'])), 'commit': BASELINE, 'flags': ''}}
    for label, writes in (('unmodified', 'full'), ('mitigated', 'changed')):
        arms[label] = {'root': str(Path(prepared['trees']['r0035']['root'])), 'commit': RESEARCH,
                       'flags': f'&r35arm={writes}&r35scope={scope}&r35amplitude=1&r35glass=0.5&r35margin=4'
                                + ('&r35guard=off' if guard == 'off' else ''),
                       'producerProbe': {'path': 'stars.status', 'equals': 'active'}}
    return {'kind': 'independent-reconstruction', 'arms': arms}


def admit_r0035_stages(prepared, prepared_path, process_path, guard, scope):
    """Failed optional preparation blocks the diagnostic lane without fallback."""
    admission = {'status': 'INCOMPLETE'}
    try:
        process_path = Path(process_path).absolute(); folder = process_path.parent
        plan_path, identity = folder/'plan.json', folder/'identity.json'
        driver_path = Path(prepared['sources']['research']['root'])/'tools/r0035/native_trials.py'
        if (digest(HERE/'observe_r0035_stages.py') != R0035_STAGE_WRAPPER_SHA256
                or digest(HERE/'r0035_stage_materialize.py') != R0035_STAGE_MATERIALIZER_SHA256):
            raise ValueError('stage preparation or observer source differs from review')
        custody = stage_material.preparation_process(process_path, driver_path, plan_path, identity)
        admission['custody'] = custody
        if custody['originalPreparation']['sha256'] != digest(Path(prepared_path)):
            raise ValueError('stage original preparation differs from this campaign')
        plan = json.loads(plan_path.read_bytes())
        driver = stage_material.support().load_driver(driver_path)
        record = stage_material.admit(plan, driver, identity)
        if record['sourcePlan'] != original_star_plan(prepared, guard, scope):
            raise ValueError('stage source plan or current flags differ from this campaign')
        admission.update(status='PASS', root=record['root'], process=str(process_path), identity=str(identity),
                         plan=str(plan_path), custody=custody, wrapperSha256=R0035_STAGE_WRAPPER_SHA256,
                         materializerSha256=R0035_STAGE_MATERIALIZER_SHA256)
    except (OSError, ValueError, KeyError, TypeError, AttributeError, subprocess.SubprocessError) as error:
        admission['reason'] = str(error)
    return admission


def same_json(left, right):
    """Receipt identity must distinguish booleans from integer measurements."""
    return json.dumps(left, sort_keys=True, allow_nan=False) == json.dumps(right, sort_keys=True, allow_nan=False)


def r0040_dateonly_identity():
    return {'protocol': 'r0040-date-only-diagnostic/1', 'kind': 'instrumented native-timer Date-only helper',
            'entrySha256': R0040_DATEONLY_WRAPPER_SHA256, 'retentionSha256': R0040_CAPTURE_WRAPPER_SHA256,
            'helper': {'protocol': 'r0040-date-only-helper/1',
                       'originalSha256': 'a02358979e9aa2f968c5ca9dde4ec7a8e63db869b871f1c24ce65a68e71497e7',
                       'transformedSha256': '95865791b0de11b15c35a4e6ec05d6d7122df6bd31850e49673d32855ef309ec',
                       'installDateOnlySha256': '83146eeba65f7c37ce99d68cd8ec4bdb69d43fc9a86668be0988c327a30f4137',
                       'originalRecoveredExactly': True, 'changedSeams': 1, 'originalBytes': 17990, 'transformedBytes': 19642},
            'originalDriverUnchanged': True, 'originalVerifierUnchanged': True, 'productAndRendererUnchanged': True,
            'admissionScope': 'Separate research diagnostic; original acquisition failure remains unchanged. The unchanged lossless verifier and all owner gates remain required.'}


def rain_mode(value, selected, engine):
    if not isinstance(value, str) or value not in ('options', *R0040_CAPTURE_MODES):
        raise ValueError('unsupported R0040 mode')
    if value in R0040_CAPTURE_MODES and ('R0040' not in selected or engine != 'chromium'):
        raise ValueError('R0040 capture requires selected R0040 and the reviewed Chromium cell')
    return value


def admit_r0040(prepared, work, process_path, entry_path, out, node, module, *, mode='capture'):
    """The actual outer exit and unchanged read-only source guard both gate capture."""
    admission = {'status': 'INCOMPLETE'}
    try:
        if mode not in R0040_CAPTURE_MODES:
            raise ValueError('unsupported R0040 capture admission mode')
        dateonly = mode == 'capture-dateonly'
        work, process_path, entry_path = (Path(p).absolute() for p in (work, process_path, entry_path))
        for path in (process_path, entry_path):
            if any(p.is_symlink() for p in (path, *path.parents)) or not path.is_file():
                raise ValueError('regular R0040 preparation receipts required')
        entry = json.loads(entry_path.read_text())
        admission['entryReceipt'] = {'path': str(entry_path), 'sha256': digest(entry_path)}
        if (entry.get('protocol') != 'r0040-capture-preparation-entry/1'
                or type(entry.get('returncode')) is not int or entry['returncode'] != 0
                or entry.get('timedOut') is not False or entry.get('wrapperSha256') != R0040_PREPARER_SHA256
                or entry.get('retentionError') or dateonly and entry.get('retentionError') is not None):
            raise ValueError('R0040 preparation entry did not complete successfully')
        child = json.loads(process_path.read_text())
        admission['processReceipt'] = {'path': str(process_path), 'sha256': digest(process_path)}
        if (child.get('protocol') != 'r0040-capture-preparation-process/1' or child.get('status') != 'PREPARED'
                or child.get('nativeStatus') != 'NOT_RUN' or type(child.get('returncode')) is not int
                or child['returncode'] != 0 or child.get('timedOut') is not False):
            raise ValueError('R0040 guarded recipe child did not complete successfully')
        research = Path(prepared['sources']['research']['root']).resolve()
        historical = Path(prepared['sources']['historical']['root']).resolve()
        main = Path(prepared['trees']['main']['root']).resolve()
        expected_inputs = {'manifest': str(R0040_MANIFEST), 'research': str(research), 'historical': str(historical),
                           'main': str(main), 'out': str(work)}
        if child.get('inputs') != expected_inputs:
            raise ValueError('R0040 preparation input paths differ from this campaign')
        if (digest(HERE/'r0040_capture_prepare.py') != R0040_PREPARER_SHA256
                or digest(HERE/'retain_r0040_capture.cjs') != R0040_CAPTURE_WRAPPER_SHA256
                or dateonly and digest(HERE/'r0040_dateonly.cjs') != R0040_DATEONLY_WRAPPER_SHA256):
            raise ValueError('R0040 preparation or capture source differs from review')
        manifest, _ = load_r0040_contract(R0040_MANIFEST)
        original = work/'receipts/prepared.json'
        identifier = 'r0040-chromium-'+mode
        options = {'driver': str(research/'tools/qa/r0040/capture.cjs'), 'manifest': str(R0040_MANIFEST),
                   'prepared': str(original), 'preparationProcess': str(process_path),
                   'evidence': str(out/(identifier+'-retention'))}
        argv = list(map(str, (module, work/'historical', main, out/identifier,
                              'chromium', 'bday', 'moderate', 'M1')))
        # This exported guard imports no browser. It rechecks the actual twelve
        # research, six patched historical, 116 generated and 177 runtime files.
        check = ('const m=require(process.argv[1]); '
                 'process.stdout.write(JSON.stringify(m.verifySources(JSON.parse(process.argv[2]),JSON.parse(process.argv[3]))));')
        if dateonly:
            options['preparationEntry'] = str(entry_path)
            check = ('const m=require(process.argv[1]),o=JSON.parse(process.argv[2]),a=JSON.parse(process.argv[3]),'
                     'd=require(process.argv[4]),fs=require("fs"),path=require("path"); '
                     'const checked=m.verifySources(o,a); '
                     'checked.dateOnlyPreparation=d.admitPreparationEntry(o.preparationEntry,o,a); '
                     'checked.dateOnlyDiagnostic=d.diagnosticIdentity(d.transformHelper(fs.readFileSync(path.join(a[1],"tools/qa/precip_eval_lib.cjs"))).identity); '
                     'process.stdout.write(JSON.stringify(checked));')
        env = dict(os.environ, R0040_DISPERSION='common')
        for key in ('R0040_OPTIONS', 'NODE_OPTIONS'): env.pop(key, None)
        try:
            command = [str(node), '-e', check, str(HERE/'retain_r0040_capture.cjs'), json.dumps(options), json.dumps(argv)]
            if dateonly: command.append(str(HERE/'r0040_dateonly.cjs'))
            result = subprocess.run(command, cwd=research, env=env,
                                    capture_output=True, text=True, timeout=90)
        except subprocess.TimeoutExpired as error:
            def retained(value):
                return value.decode('utf-8', errors='replace') if isinstance(value, bytes) else value
            admission['sourceCheck'] = {'returncode': None, 'timedOut': True,
                                        'stdout': retained(error.stdout), 'stderr': retained(error.stderr)}
            raise
        admission['sourceCheck'] = {'returncode': result.returncode, 'timedOut': False}
        if result.returncode != 0:
            admission['sourceCheck'].update(stdout=result.stdout, stderr=result.stderr)
            raise ValueError('R0040 actual source admission failed: '+result.stderr)
        checked = json.loads(result.stdout)
        wanted = {'historical': manifest['stages'][-1]['files'], 'research': manifest['researchInputs'],
                  'main': manifest['main']['runtimeFiles']}
        if (checked.get('sources') != wanted or {k: len(v) for k, v in wanted.items()}
                != {'historical': 6, 'research': 12, 'main': 177}
                or checked.get('custody', {}).get('manifestSha256') != R0040_MANIFEST_SHA256):
            raise ValueError('R0040 actual source admission population or custody is incomplete')
        if dateonly:
            if (not same_json(checked.get('dateOnlyDiagnostic'), r0040_dateonly_identity())
                    or not same_json(checked.get('dateOnlyPreparation'), {**admission['entryReceipt'], 'actualExitCode': 0})):
                raise ValueError('Date-only diagnostic helper or outer-entry identity differs')
            admission.update(dateOnlyDiagnostic=checked['dateOnlyDiagnostic'], dateOnlyPreparation=checked['dateOnlyPreparation'])
        admission.update(status='PASS', work=str(work), manifest=str(R0040_MANIFEST), prepared=str(original),
                         process=str(process_path), wrapperSha256=R0040_CAPTURE_WRAPPER_SHA256,
                         sourceCustody=checked['custody'], verifiedPopulation={k: len(v) for k, v in wanted.items()},
                         expectedCapture=manifest['plannedNativeCell']['expectedCapture'], pins=manifest['pins'])
    except (OSError, ValueError, KeyError, TypeError, AttributeError, subprocess.SubprocessError) as error:
        admission['reason'] = str(error)
    return admission


def moon_harness(value, selected):
    if value not in ('published', 'corrected-b0') or not isinstance(value, str):
        raise ValueError('unsupported R003F harness')
    if value == 'corrected-b0' and 'R003F' not in selected:
        raise ValueError('corrected R003F harness requires selected R003F observations')
    return value


def star_controls(value=None):
    """Existing recipe options only; no admission, time or owner-policy changes."""
    if value is None:
        value = {}
    choices = {'guard': ('default', 'off'), 'scope': ('all', 'preview-members'),
               'mode': ('both', 'timing', 'capture')}
    if (not isinstance(value, dict) or any(key not in choices for key in value)
            or any(not isinstance(v, str) or v not in choices[k] for k, v in value.items())):
        raise ValueError('unsupported R0035 diagnostic controls')
    return {**STAR_DEFAULTS, **value}


def selected_work_orders(value, include_r002f):
    """An absent selection retains the existing CLI population; empty is invalid."""
    if type(include_r002f) is not bool:
        raise ValueError('R002F enabled must be boolean')
    if value is None:
        value = [order for order in WORK_ORDERS if order != 'R002F' or include_r002f]
    if (not isinstance(value, list) or not value
            or any(not isinstance(order, str) or order not in WORK_ORDERS for order in value)
            or len(set(value)) != len(value)):
        raise ValueError('work-order selection must be a nonempty list of distinct known identifiers')
    if ('R002F' in value) != include_r002f:
        raise ValueError('R002F enabled and work-order selection disagree')
    # Selection does not reorder dependencies or change the reviewed lane order.
    return [order for order in WORK_ORDERS if order in value]


def admit_r002f(path, process_path=None):
    """A failed optional build remains a blocked lane, not a failed common plan."""
    admission = {'status': 'INCOMPLETE'}
    try:
        if process_path is not None:
            process_path = Path(process_path).resolve()
            process = json.loads(process_path.read_text())
            admission['processReceipt'] = {'path': str(process_path), 'sha256': digest(process_path)}
            if (not isinstance(process, dict) or type(process.get('returncode')) is not int
                    or process['returncode'] != 0 or process.get('timedOut') is not False):
                raise ValueError('R002F preparation process did not complete successfully')
        path = Path(path).resolve()
        body = json.loads(path.read_text())
        admission['receipt'] = {'path': str(path), 'sha256': digest(path)}
        if (body.get('protocol') != 'r002f-hosted-build/1' or body.get('status') != 'PASS'
                or body.get('baseProvenance') != BASELINE or body.get('researchProvenance') != RESEARCH
                or body.get('wrapperSha256') != digest(HERE/'r002f_prepare.py')
                or body.get('patch', {}).get('patch') != PATCH):
            raise ValueError('R002F build receipt is absent, incomplete or has wrong custody')
        trees = {}
        for arm, index, inventory in (('baseline', BASE_INDEX, BASE_INVENTORY),
                                      ('candidate', COMBINED_INDEX, COMBINED_INVENTORY)):
            record = body.get('arms', {}).get(arm, {})
            builds = record.get('builds', [])
            if (record.get('path') != arm or record.get('indexSha256') != index
                    or record.get('inventorySha256') != inventory or len(builds) != 2
                    or any(run.get('indexSha256') != index for run in builds)
                    or any(builds[-1].get(k) != v for k, v in {'written': 0, 'removed': 0, 'unchanged': 117}.items())):
                raise ValueError('R002F generated arm receipt is incomplete: '+arm)
            root = path.parent/arm
            verified = verify_generated(root, {'index.html': index, 'GENERATED.json': inventory})
            trees[arm] = {**verified, 'root': str(root)}
        if digest(HERE/'r002f_probe.cjs') != R002F_PROBE_SHA256:
            raise ValueError('R002F probe differs from the reviewed source')
        admission.update(status='PASS', trees=trees)
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        admission['reason'] = str(error)
    return admission


def admit_r003f(path, process_path):
    """Bind the reviewed corrected helpers to their exact deterministic receipt."""
    admission = {'status': 'INCOMPLETE'}
    try:
        path, process_path = Path(path).absolute(), Path(process_path).absolute()
        if path.is_symlink() or process_path.is_symlink():
            raise ValueError('R003F preparation receipts must be regular files')
        process = json.loads(process_path.read_text())
        admission['processReceipt'] = {'path': str(process_path), 'sha256': digest(process_path)}
        if (type(process.get('returncode')) is not int or process['returncode'] != 0
                or process.get('timedOut') is not False):
            raise ValueError('R003F materialization process did not complete successfully')
        if digest(path) != R003F_MATERIALIZATION:
            raise ValueError('R003F materialization differs from the reviewed receipt')
        body = json.loads(path.read_text()); root = path.parent
        if any(parent.is_symlink() for parent in (root, *root.parents)):
            raise ValueError('R003F materialized source uses a symlinked ancestor')
        if (body.get('protocol') != 'R003F/corrected-harness/1' or body.get('status') != 'PREPARED'
                or body.get('materializerSha256') != digest(HERE/'r003f_materialize.cjs')):
            raise ValueError('R003F materializer identity mismatch')
        outputs = {}
        for member in body['outputFiles']:
            relative = Path(member['path']); source = root/relative
            if relative.is_absolute() or '..' in relative.parts:
                raise ValueError('R003F materialized member escaped its source root')
            if (not source.is_file() or any(item.is_symlink() for item in (source, *source.parents))
                    or source.stat().st_size != member['bytes'] or digest(source) != member['sha256']):
                raise ValueError('R003F materialized helper changed: '+member['path'])
            outputs[member['path']] = member['sha256']
        harness = {'protocol': 'R003F/corrected-harness/1', 'kind': 'corrected MIME and native UI admission',
                   'materializationSha256': R003F_MATERIALIZATION,
                   'driverSha256': outputs['tools/qa/r003f_owner_baseline.cjs'],
                   'captureHelperSha256': outputs['tools/qa/r003f_capture.cjs'],
                   'uiHelperSha256': outputs['tools/qa/hosted-native/r003f_ui.cjs']}
        if harness['uiHelperSha256'] != digest(HERE/'r003f_ui.cjs'):
            raise ValueError('R003F UI helper differs from orchestration')
        admission.update(status='PASS', root=str(root), harness=harness,
                         receipt={'path': str(path), 'sha256': R003F_MATERIALIZATION})
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        admission['reason'] = str(error)
    return admission


def make_plan(prepared, out, *, python_playwright, node, node_modules, pngjs,
              engine='chromium', r003f_dpr=1, include_r002f=False, r002f_preparation=None,
              r002f_dpr=1, r002f_rounds=1, r002f_section='all', work_orders=None, retain_evidence=False,
              r0035_guard='default', r0035_scope='all', r0035_mode='both',
              r0035_stages=False, r0035_stage_preparation=None,
              r003f_harness='published', r003f_preparation=None,
              r0040_mode='options', r0040_preparation=None):
    if engine not in ('chromium', 'firefox', 'webkit') or type(r003f_dpr) is not int or r003f_dpr not in (1, 2):
        raise ValueError('unsupported engine or R003F DPR')
    if (type(include_r002f) is not bool or type(r002f_dpr) is not int or r002f_dpr not in (1, 2, 3)
            or type(r002f_rounds) is not int or not 1 <= r002f_rounds <= 10
            or r002f_section not in ('all', 'prayer', 'preview')):
        raise ValueError('unsupported R002F campaign controls')
    selected = selected_work_orders(work_orders, include_r002f)
    rain_mode(r0040_mode, selected, engine)
    moon_harness(r003f_harness, selected)
    stars = star_controls({'guard': r0035_guard, 'scope': r0035_scope, 'mode': r0035_mode})
    if stars != STAR_DEFAULTS and 'R0035' not in selected:
        raise ValueError('R0035 diagnostic controls require selected R0035 observations')
    if type(retain_evidence) is not bool:
        raise ValueError('evidence retention must be boolean')
    stage_mode(r0035_stages, selected, stars, retain_evidence)
    research = Path(prepared['sources']['research']['root'])
    historical = Path(prepared['sources']['historical']['root'])
    roots = {key: Path(value['root']) for key, value in prepared['trees'].items()}
    module = node_modules / 'playwright'
    star_plan_path = out / 'r0035-plan.json'
    star_plan = original_star_plan(prepared, r0035_guard, r0035_scope)
    entries = []

    def lane(identifier, work_order, dpr, timeout, kind, filename, statuses):
        target = out / identifier
        row = {'id': identifier, 'workOrder': work_order, 'engine': engine, 'dpr': dpr,
               'cwd': str(research), 'env': {'NODE_PATH': str(node_modules)},
               'output': str(target), 'stdout': str(out / (identifier + '.stdout')),
               'stderr': str(out / (identifier + '.stderr')), 'timeoutSeconds': timeout,
               'result': {'kind': kind, 'path': str(target / filename)},
               'exitStatuses': statuses, 'dependsOn': [], 'stopScopeOnAndon': work_order}
        entries.append(row)
        return row

    if r0040_mode in R0040_CAPTURE_MODES:
        dateonly = r0040_mode == 'capture-dateonly'
        rain = lane('r0040-chromium-'+r0040_mode, 'R0040', 1, 180, 'r0040-'+r0040_mode, 'capture.json',
                    {'0': R0040_DATEONLY_ADMITTED if dateonly else 'ADMITTED_FOR_OFFLINE_VERIFICATION',
                     '1': 'FAIL', '86': 'EXTERNAL_CONTINUATION_VETOED'})
        admission = r0040_preparation or {'status': 'INCOMPLETE', 'reason': 'R0040 capture preparation is missing'}
        rain['preparation'] = admission
        rain['env']['R0040_DISPERSION'] = 'common'; rain['clearEnv'] = ['R0040_OPTIONS']
        evidence = str(out/(rain['id']+'-retention'))
        rain['stopAllOnExit'] = [86]
        rain['evidenceRetention'] = {'instrumented': True, 'output': evidence, 'timingComparableToOriginal': False,
                                    'overhead': 'Host request/error/cleanup serialization and fsync; PNGs are hashed after capture. No added CDP frame listener or per-frame copies.'}
        rain['result']['finalAdmissionPath'] = str(Path(evidence)/'final-admission.json')
        if dateonly:
            rain['postCaptureCheckSeconds'] = 100
            rain['evidenceRetention']['overhead'] += ' Date reads use native performance time; a bounded startup timer and two rAF callbacks add work before capture. Instrumented timing is not original performance.'
            rain['result'].update(journalPath=str(Path(evidence)/'events.jsonl'),
                                  isolationReceiptPath=str(out.parent/'isolation'/rain['id']/'receipt.json'))
        rain['argv'] = []
        if admission.get('status') == 'PASS':
            original = list(map(str, [node, research/'tools/qa/r0040/capture.cjs', module,
                                      Path(admission['work'])/'historical', roots['main'], rain['output'],
                                      'chromium', 'bday', 'moderate', 'M1']))
            rain['evidenceRetention']['originalArgv'] = original
            rain['argv'] = [str(node), str(HERE/'retain_r0040_capture.cjs'), '--driver', original[1],
                            '--manifest', admission['manifest'], '--prepared', admission['prepared'],
                            '--preparation-process', admission['process'], '--evidence', evidence, '--', *original[2:]]
            rain['result'].update(expectedCapture=admission['expectedCapture'], pins=admission['pins'],
                                  wrapperSha256=R0040_CAPTURE_WRAPPER_SHA256)
            if dateonly:
                rain['argv'][1] = str(HERE/'r0040_dateonly.cjs')
                insert = rain['argv'].index('--evidence')
                rain['argv'][insert:insert] = ['--preparation-entry', admission['entryReceipt']['path']]
                rain['result'].update(wrapperSha256=R0040_DATEONLY_WRAPPER_SHA256,
                                      diagnostic=admission['dateOnlyDiagnostic'])
    else:
        rain = lane(f'r0040-{engine}', 'R0040', 1, 720, 'r0040-options', 'native-options.json',
                    {'0': 'MEASURED', '1': 'FAIL'})
        rain['argv'] = list(map(str, [node, research / 'tools/qa/r0040/native-options.cjs', module,
                                     historical, roots['r0040'], rain['output'], engine]))
        rain['result']['expectedCells'] = ['day-rain', 'day-drizzle', 'day-thunder', 'night', 'twilight',
                                          'reduced-none', 'reduced-still', 'motion-full', 'dry']

    moon = lane(f'r003f-b0-{engine}-dpr{r003f_dpr}', 'R003F', r003f_dpr, 900, 'r003f-b0', 'summary.json',
                {'0': 'MEASURED', '1': 'FAIL', '2': 'INCOMPLETE', '3': 'ISOLATION FAIL', '4': 'ANDON'})
    moon['argv'] = list(map(str, [node, research / 'tools/qa/r003f_owner_baseline.cjs', '--root', roots['r003f'],
                                 '--out', moon['output'], '--engine', engine, '--dpr', r003f_dpr,
                                 '--playwright', module, '--pngjs', pngjs]))
    moon['result']['expectedCaptures'] = ['offset', 'b0', 'b0-repeat', 'reference']
    moon['stopAllOnExit'] = [3]
    if r003f_harness == 'corrected-b0':
        admission = r003f_preparation or {'status': 'INCOMPLETE', 'reason': 'corrected R003F preparation is missing'}
        moon['preparation'] = admission
        if admission.get('status') == 'PASS':
            moon['argv'][1] = str(Path(admission['root'])/'tools/qa/r003f_owner_baseline.cjs')
            moon['result'].update(expectedHarness=admission['harness'], expectedIndexSha256=BASE_INDEX)
        else:
            moon['argv'] = []

    for capture in (False, True):
        label = 'capture' if capture else 'timing'
        if r0035_mode not in ('both', label):
            continue
        star = lane(f'r0035-{engine}-{label}', 'R0035', 1, 480, 'r0035-trials', 'summary.json',
                    {'0': 'INSPECT ADMISSION', '1': 'INCOMPLETE'})
        star['argv'] = list(map(str, [python_playwright, research / 'tools/r0035/native_trials.py',
                                     star_plan_path, star['output'], '--engine', engine, '--rounds', 1,
                                     '--seconds', 15, '--clock', 'ordinary', '--scene', 'dark', '--motion', 'normal']))
        star['result'].update(expectedRows=3, expectedArms=['main', 'unmodified', 'mitigated'],
                              requiresEveryRowAdmitted=True, capture=capture)
        if capture:
            star['argv'].append('--capture')
            if r0035_mode == 'both':
                star['dependsOn'] = [entries[-2]['id']]
                star['dependencyPolicy'] = 'finished; retain failed timing, classify captures independently'
        if r0035_stages:
            admission = r0035_stage_preparation or {'status': 'INCOMPLETE', 'reason': 'R0035 stage preparation is missing'}
            star['preparation'] = admission
            evidence = str(out/(star['id']+'-stages'))
            star['stageObservation'] = {'protocol': 'r0035-stage-diagnostic/1', 'instrumented': True}
            star['evidenceRetention'] = {'instrumented': True, 'output': evidence, 'timingComparableToOriginal': False,
                'overhead': 'In-memory stage marks and small worker replies; one trace extraction after measurement. No added pixel copies or per-frame host writes.'}
            star['stopAllOnExit'] = [86]; star['exitStatuses']['86'] = 'EXTERNAL_CONTINUATION_VETOED'
            star['result'].update(stageDriverPath=str(Path(evidence)/'driver.json'), stageWrapperSha256=R0035_STAGE_WRAPPER_SHA256)
            if admission.get('status') == 'PASS':
                original = star['argv']; original[2] = admission['plan']
                star['evidenceRetention']['originalArgv'] = original
                star['argv'] = [original[0], str(HERE/'observe_r0035_stages.py'), '--driver', original[1],
                                '--identity', admission['identity'], '--preparation-process', admission['process'],
                                '--preparation-sha256', admission['custody']['process']['sha256'],
                                '--evidence', evidence, '--', *original[2:]]
            else:
                star['argv'] = []
    if include_r002f:
        admission = r002f_preparation or {'status': 'INCOMPLETE', 'reason': 'requested R002F preparation is missing'}
        probe = lane(f'r002f-{engine}-dpr{r002f_dpr}', 'R002F', r002f_dpr, 900,
                     'r002f-probe', 'result.json', {'0': 'PASS', '1': 'FAIL', '2': 'INCOMPLETE or INCONCLUSIVE'})
        probe['preparation'] = admission
        probe['result'].update(expectedRounds=r002f_rounds, expectedSection=r002f_section,
                               expectedObserverSha256=R002F_PROBE_SHA256)
        probe['argv'] = []
        if admission.get('status') == 'PASS':
            trees = admission['trees']
            probe['argv'] = list(map(str, [node, HERE/'r002f_probe.cjs', '--playwright', module,
                                          '--baseline', trees['baseline']['root'], '--candidate', trees['candidate']['root'],
                                          '--out', probe['output'], '--engine', engine, '--dpr', r002f_dpr,
                                          '--rounds', r002f_rounds, '--section', r002f_section, '--timeout-ms', 60000]))
    entries = [row for row in entries if row['workOrder'] in selected]
    if retain_evidence:
        for row in entries:
            if row['workOrder'] not in ('R0040', 'R0035'):
                continue
            if row['result']['kind'] in ('r0040-capture', 'r0040-capture-dateonly'):
                continue
            original = row['argv']
            evidence = str(out/(row['id']+'-retention'))
            wrapper = HERE/('retain_r0040.cjs' if row['workOrder'] == 'R0040' else 'retain_r0035.py')
            row['argv'] = [original[0], str(wrapper), '--driver', original[1], '--evidence', evidence,
                           '--', *original[2:]]
            row['evidenceRetention'] = {
                'instrumented': True, 'originalArgv': original, 'output': evidence,
                'timingComparableToOriginal': False,
                'overhead': 'Host serialization, hashing, fsync and evidence copies affect timing/capture; '
                            'these are instrumented observations, not original performance measurements.'}
            row['exitStatuses']['86'] = 'EXTERNAL_CONTINUATION_VETOED'
            row['stopAllOnExit'] = [86]
    return {'schemaVersion': 1, 'protocol': 'salah-hosted-native-lanes/1', 'sequential': True,
            'scope': 'Selected native observations only; no work-order acceptance or owner selection.',
            'workOrders': selected, 'evidenceRetention': retain_evidence,
            'r0035Controls': stars,
            'r0035Stages': r0035_stages,
            'r003fHarness': r003f_harness,
            'r0040Mode': r0040_mode,
            'r0035PlanPath': str(star_plan_path), 'r0035Plan': star_plan, 'lanes': entries,
            'failurePolicy': {'isolation': 'stop all observations', 'R003FAndon': 'stop R003F progression',
                              'externalContinuationVeto': 'stop all observations; prevented continuation is not an actual network escape',
                              'ordinaryLaneFailure': 'retain outputs; independent lanes may continue',
                              'timeout': 'coordinator kills child process group and retains private logs'},
            'followUp': [
                'After inspected admission, obtain Firefox and WebKit counterparts; neither proves Safari or physical-device behavior.',
                'R003F B0 at DPR2 is available with --r003f-dpr 2; its product Andon stops proposal progression.',
                'R0035 nine-round WebKit timing, native reduced/full-motion and phase/glass evidence need separate plans with their actual inactive probes.',
                'The R0040 nine-cell option recipe fixes DPR1. Additional motion, lossless capture and DPR evidence require the owning recipes and fresh admission.',
            ]}


def check_star_plan(prepared, plan):
    """Use the published driver's unchanged clean-source and arm guards."""
    directory = Path(prepared['sources']['research']['root']) / 'tools/r0035'
    sys.path.insert(0, str(directory))
    try:
        spec = importlib.util.spec_from_file_location('hosted_native_existing_trials', directory / 'native_trials.py')
        driver = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(driver)
        driver.check_plan(plan)
        driver.verify_reconstructed_flags(plan['arms'])
    finally:
        sys.path.pop(0)


def executable(path):
    # Keep a venv interpreter's symlink path: resolving it would select system
    # Python and silently lose the separately installed Python Playwright.
    if not path.is_absolute() or not path.is_file() or not os.access(path, os.X_OK):
        raise ValueError('explicit executable path required')
    return path


def dependency(path, name, version):
    if not path.is_absolute() or not path.is_dir():
        raise ValueError('explicit module directory required')
    meta = json.loads((path / 'package.json').read_text())
    if (meta.get('name'), meta.get('version')) != (name, version):
        raise ValueError('dependency package identity mismatch')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan-json', action='store_true', required=True)
    for name in ('prepared', 'out', 'python-playwright', 'node', 'node-modules', 'pngjs'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--engine', choices=('chromium', 'firefox', 'webkit'), default='chromium')
    parser.add_argument('--r003f-dpr', type=int, choices=(1, 2), default=1)
    parser.add_argument('--r003f-harness', choices=('published', 'corrected-b0'), default='published')
    parser.add_argument('--r003f-prepared', type=Path)
    parser.add_argument('--r003f-process', type=Path)
    parser.add_argument('--r0040-mode', choices=('options', *R0040_CAPTURE_MODES), default='options')
    parser.add_argument('--r0040-work', type=Path)
    parser.add_argument('--r0040-process', type=Path)
    parser.add_argument('--r0040-entry-process', type=Path)
    parser.add_argument('--work-orders', nargs='+')
    parser.add_argument('--retain-evidence', action='store_true')
    parser.add_argument('--r0035-guard', choices=('default', 'off'), default='default')
    parser.add_argument('--r0035-scope', choices=('all', 'preview-members'), default='all')
    parser.add_argument('--r0035-mode', choices=('both', 'timing', 'capture'), default='both')
    parser.add_argument('--r0035-stages', action='store_true')
    parser.add_argument('--r0035-stage-process', type=Path)
    parser.add_argument('--r002f', action='store_true')
    parser.add_argument('--r002f-prepared', type=Path)
    parser.add_argument('--r002f-process', type=Path)
    parser.add_argument('--r002f-dpr', type=int, choices=(1, 2, 3), default=1)
    parser.add_argument('--r002f-rounds', type=int, choices=range(1, 11), default=1)
    parser.add_argument('--r002f-section', choices=('all', 'prayer', 'preview'), default='all')
    args = parser.parse_args()
    os.umask(0o077)
    admitted_out = None
    try:
        selected_work_orders(args.work_orders, args.r002f)
        if args.out.exists() or args.out.is_symlink():
            raise ValueError('fresh plan output required')
        out = args.out.resolve()
        prepared = validate_prepared(args.prepared.resolve())
        roots = [Path(row['root']).resolve() for group in ('sources', 'trees') for row in prepared[group].values()]
        r002f = (admit_r002f(args.r002f_prepared, args.r002f_process)
                 if args.r002f_prepared and args.r002f_process else None)
        r003f = (admit_r003f(args.r003f_prepared, args.r003f_process)
                 if args.r003f_harness == 'corrected-b0' else None)
        r0040 = (admit_r0040(prepared, args.r0040_work, args.r0040_process, args.r0040_entry_process,
                             out, args.node, args.node_modules/'playwright', mode=args.r0040_mode)
                 if args.r0040_mode in R0040_CAPTURE_MODES else None)
        r0035_stage = (admit_r0035_stages(prepared, args.prepared, args.r0035_stage_process,
                                         args.r0035_guard, args.r0035_scope) if args.r0035_stages else None)
        if r0035_stage and r0035_stage['status'] == 'PASS':
            roots.append(Path(r0035_stage['root']))
        if r0040 and r0040['status'] == 'PASS':
            roots.append(Path(r0040['work']))
        if r003f and r003f['status'] == 'PASS':
            roots.append(Path(r003f['root']))
        if r002f and r002f['status'] == 'PASS':
            roots.extend(Path(row['root']).resolve() for row in r002f['trees'].values())
        if any(root == out or root in out.parents for root in roots):
            raise ValueError('plan output must be outside source trees')
        out.mkdir(parents=True, mode=0o700)
        admitted_out = out
        executable(args.python_playwright)
        executable(args.node)
        dependency(args.node_modules / 'playwright', 'playwright', '1.62.1')
        dependency(args.pngjs, 'pngjs', '7.0.0')
        plan = make_plan(prepared, out, python_playwright=args.python_playwright, node=args.node,
                         node_modules=args.node_modules, pngjs=args.pngjs, engine=args.engine, r003f_dpr=args.r003f_dpr,
                         include_r002f=args.r002f, r002f_preparation=r002f, r002f_dpr=args.r002f_dpr,
                         r002f_rounds=args.r002f_rounds, r002f_section=args.r002f_section,
                         work_orders=args.work_orders, retain_evidence=args.retain_evidence,
                         r0035_guard=args.r0035_guard, r0035_scope=args.r0035_scope, r0035_mode=args.r0035_mode,
                         r0035_stages=args.r0035_stages, r0035_stage_preparation=r0035_stage,
                         r003f_harness=args.r003f_harness, r003f_preparation=r003f,
                         r0040_mode=args.r0040_mode, r0040_preparation=r0040)
        check_star_plan(prepared, plan['r0035Plan'])
        write_json(Path(plan['r0035PlanPath']), plan['r0035Plan'])
        plan['preparedReceipt'] = {'path': str(args.prepared.resolve()), 'sha256': digest(args.prepared)}
        print(json.dumps(plan, indent=2))
    except Exception as error:
        if admitted_out is not None:
            write_json(admitted_out / 'plan-error.json', {'status': 'INCOMPLETE', 'error': str(error)})
        print('LANE PLAN INCOMPLETE; inspect private preparation or plan receipts', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
