"""Run admitted recipes sequentially in fresh Linux network/PID namespaces.

This wrapper qualifies observation isolation, not product acceptance. Every
recipe stream and all result detail remain beneath the private capture root.
"""
import argparse
import errno
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import signal
import shutil
import socket
import subprocess
import sys
import tempfile
import time

from lanes import (selected_work_orders, star_controls, STAR_DEFAULTS, moon_harness, BASE_INDEX, R003F_MATERIALIZATION,
                   rain_mode, R0040_MANIFEST, R0040_MANIFEST_SHA256, R0040_CAPTURE_WRAPPER_SHA256, digest, stage_mode, original_star_plan,
                   R0035_STAGE_WRAPPER_SHA256, R0035_STAGE_MATERIALIZER_SHA256,
                   R0040_CAPTURE_MODES, R0040_DATEONLY_WRAPPER_SHA256, R0040_DATEONLY_ADMITTED,
                   r0040_dateonly_identity, same_json,
                   r002f_route_mode, tabhide_manifest, admit_r002f_tabhide, R002F_TABHIDE_MANIFEST_SHA256,
                   R002F_TABHIDE_TIMEOUT_SECONDS, R002F_PROBE_SHA256, matrix, MATRIX_PINS, cost_mode,
                   R0035_COST_WRAPPER_SHA256, R0035_COST_MATERIALIZER_SHA256,
                   admit_r0035_stages, matrix_preparation_runtime, make_plan)
from prepare import validate_prepared
import r0035_stage_materialize as stage_material
import r0035_cost_materialize as cost_material
import r0040_passive_central as passive
import r0035_psf as psf
from observe_r0035_stages import inspect as inspect_stage_trace
from observe_r0035_costs import inspect as inspect_cost_trace, BASE_WRAPPER_SHA256 as COST_BASE_WRAPPER_SHA256
import r003f_diagnostics as diagnostics

CAP_FIELDS = ('CapInh', 'CapPrm', 'CapEff', 'CapBnd', 'CapAmb')
RAIN_CELLS = ('day-rain', 'day-drizzle', 'day-thunder', 'night', 'twilight',
              'reduced-none', 'reduced-still', 'motion-full', 'dry')
HERE = Path(__file__).resolve().parent
ISOLATION_EXIT = 86
VETO_STATUS = 'EXTERNAL_CONTINUATION_VETOED'
CAPTURE_ADMITTED = 'ADMITTED_FOR_OFFLINE_VERIFICATION'
STAGES_OBSERVED = 'OBSERVED_STAGE_DIAGNOSTIC'
TABHIDE_OBSERVED = 'OBSERVED_TABHIDE_DIAGNOSTIC'
COSTS_OBSERVED = 'OBSERVED_PREPARATION_COSTS'
VETO_REASON = ('retention wrapper prevented external continuation before the real continue action; '
               'not evidence of an actual network escape')


def read_campaign(path):
    value = json.loads(Path(path).read_text())
    if (not isinstance(value, dict) or value.get('schemaVersion') != 1
            or value.get('engine') not in ('chromium', 'firefox', 'webkit')
            or type(value.get('r003fDpr')) is not int or value['r003fDpr'] not in (1, 2)):
        raise ValueError('unsupported hosted campaign')
    r002f = value.get('r002f')
    if (not isinstance(r002f, dict) or type(r002f.get('enabled')) is not bool
            or type(r002f.get('dpr')) is not int or r002f['dpr'] not in (1, 2, 3)
            or type(r002f.get('rounds')) is not int or not 1 <= r002f['rounds'] <= 10
            or r002f.get('section') not in ('all', 'prayer', 'preview')):
        raise ValueError('unsupported R002F campaign controls')
    if 'workOrders' in value and not isinstance(value['workOrders'], list):
        raise ValueError('work-order selection must be a list')
    selected = selected_work_orders(value.get('workOrders'), r002f['enabled'])
    r002f_route_mode(value.get('r002fRoute','offscreen'), selected, value['engine'], r002f['dpr'], r002f['rounds'], r002f['section'])
    moon_harness(value.get('r003fHarness', 'published'), selected)
    rain_mode(value.get('r0040Mode', 'options'), selected, value['engine'])
    if 'r0035' in value and (not isinstance(value['r0035'], dict) or 'R0035' not in selected):
        raise ValueError('explicit R0035 controls require a dictionary and selected R0035')
    stars = star_controls(value.get('r0035'))
    if type(value.get('evidenceRetention', False)) is not bool:
        raise ValueError('evidence retention must be boolean')
    diagnostics.controls(value.get('r003fHarness','published'),selected,value['engine'],value['r003fDpr'],value.get('evidenceRetention',False))
    stage_mode(value.get('r0035Stages', False), selected, stars, value.get('evidenceRetention', False))
    matrix.matrix_controls(value.get('r003fMatrix'), value.get('r003fHarness','published'), selected, value['engine'], value['r003fDpr'])
    campaign_budget(value)
    cost_mode(value.get('r0035Costs', False), value.get('r0035Stages', False), selected, stars,
              value['engine'], value.get('evidenceRetention', False), r002f['enabled'])
    return value


def campaign_selection(args):
    if type(getattr(args, 'retain_evidence', False)) is not bool:
        raise ValueError('evidence retention must be boolean')
    return selected_work_orders(getattr(args, 'work_orders', None), getattr(args, 'r002f', False))


def star_campaign(args):
    controls = star_controls({key: getattr(args, 'r0035_'+key, default) for key, default in STAR_DEFAULTS.items()})
    if controls != STAR_DEFAULTS and 'R0035' not in campaign_selection(args):
        raise ValueError('R0035 diagnostic controls require selected R0035 observations')
    return controls


def star_arguments(args):
    return [part for key, value in star_campaign(args).items() for part in ('--r0035-'+key, value)]


def stage_campaign(args):
    return stage_mode(getattr(args, 'r0035_stages', False), campaign_selection(args),
                      star_campaign(args), getattr(args, 'retain_evidence', False))


def cost_campaign(args):
    return cost_mode(getattr(args,'r0035_costs',False),stage_campaign(args),campaign_selection(args),
                     star_campaign(args),args.engine,getattr(args,'retain_evidence',False),getattr(args,'r002f',False))


def psf_campaign(args):
    return psf.mode(getattr(args,'r0035_psf',False),campaign_selection(args),star_campaign(args),args.engine,
                    stages=getattr(args,'r0035_stages',False),costs=getattr(args,'r0035_costs',False),
                    retained=getattr(args,'retain_evidence',False),r002f=getattr(args,'r002f',False),
                    moon=getattr(args,'r003f_harness','published'),rain=getattr(args,'r0040_mode','options'),
                    matrix=getattr(args,'r003f_matrix',None))


def psf_lane(lane):
    return isinstance(lane.get('psfObservation'),dict) and lane['psfObservation'].get('protocol')=='r0035-psf-paired-diagnostic/1'


def cost_lane(lane):
    return lane.get('stageObservation',{}).get('protocol')=='r0035-cost-diagnostic/1'


def moon_campaign(args):
    return moon_harness(getattr(args, 'r003f_harness', 'published'), campaign_selection(args))


def matrix_campaign(args):
    return matrix.matrix_controls(getattr(args,'r003f_matrix',None),moon_campaign(args),campaign_selection(args),args.engine,getattr(args,'r003f_dpr',1))


def diagnostic_campaign(args):
    return diagnostics.controls(moon_campaign(args),campaign_selection(args),args.engine,
                                getattr(args,'r003f_dpr',1),getattr(args,'retain_evidence',False))





def rain_campaign(args):
    return rain_mode(getattr(args, 'r0040_mode', 'options'), campaign_selection(args), args.engine)


def tabhide_campaign(args):
    return r002f_route_mode(getattr(args, 'r002f_route', 'offscreen'), campaign_selection(args), args.engine,
                           getattr(args, 'r002f_dpr', 1), getattr(args, 'r002f_rounds', 1), getattr(args, 'r002f_section', 'all'))






def campaign_budget(campaign):
    """Keep independent route envelopes; unreviewed combinations never use max()."""
    if not isinstance(campaign, dict) or campaign.get('r002fRoute', 'offscreen') not in ('offscreen', 'tabhide'):
        raise ValueError('unsupported campaign budget selector')
    headed = campaign.get('r002fRoute', 'offscreen') == 'tabhide'
    matrix_selected = campaign.get('r003fHarness', 'published') == 'corrected-matrix'
    costs = campaign.get('r0035Costs', False)
    passive_selected = campaign.get('r0040Mode', 'options') == passive.MODE
    diagnostic_selected=campaign.get('r003fHarness') in diagnostics.ROUTES
    psf_selected=psf.mode(campaign.get('r0035Psf',False),campaign.get('workOrders',['R0040','R003F','R0035','R002F']),
                           star_controls(campaign.get('r0035')),campaign.get('engine','chromium'),
                           stages=campaign.get('r0035Stages',False),costs=costs,
                           retained=campaign.get('evidenceRetention',False),r002f=campaign.get('r002f',{}).get('enabled',False),
                           moon=campaign.get('r003fHarness','published'),rain=campaign.get('r0040Mode','options'),
                           matrix=campaign.get('r003fMatrix'))
    if psf_selected:
        if headed:raise ValueError('PSF cannot combine supplemental route budgets')
        return {'coordinatorSeconds':3540,'workflowObservationMinutes':60}
    if type(costs) is not bool or sum((headed, matrix_selected, costs, passive_selected, diagnostic_selected)) > 1:
        raise ValueError('simultaneous supplemental route populations and budgets are not admitted')
    selected = campaign.get('workOrders', ['R0040', 'R003F', 'R0035', 'R002F'])
    if passive_selected:
        rain_mode(passive.MODE, selected, campaign.get('engine', 'chromium'))
        if campaign.get('r0035Stages', False) or campaign.get('r003fHarness', 'published') != 'published' or campaign.get('r002f', {}).get('enabled', False):
            raise ValueError('passive aggregate budget supports only its single capture route')
        # 1350 preparation + 120 outer readmission + (120 current admission +
        # 240 child + 130 final replay + 75 namespace) = 2035. The original
        # 2640/2700 envelope leaves 605 coordinator and 60 step seconds.
        return {'coordinatorSeconds': 2640, 'workflowObservationMinutes': 45}
    diagnostic=diagnostics.controls(campaign.get('r003fHarness','published'),selected,campaign.get('engine','chromium'),
                                    campaign.get('r003fDpr',1),campaign.get('evidenceRetention',False))
    control = matrix.matrix_controls(campaign.get('r003fMatrix'), campaign.get('r003fHarness', 'published'),
                                     selected, campaign.get('engine', 'chromium'), campaign.get('r003fDpr', 1))
    if control:
        return {key: control['budget'][key] for key in ('coordinatorSeconds', 'workflowObservationMinutes')}
    if diagnostic:
        return {key:diagnostic['budget'][key] for key in ('coordinatorSeconds','workflowObservationMinutes')}
    if headed:
        if selected != ['R002F']:
            raise ValueError('headed aggregate budget supports only the selected R002F population')
        # 1920 preparation + (1800 child + 75 namespace/intake) = 3795;
        # 105 coordinator seconds and 60 further step seconds remain bounded.
        return {'coordinatorSeconds': 3900, 'workflowObservationMinutes': 66}
    if costs:
        cost_mode(costs, campaign.get('r0035Stages', False), selected, star_controls(campaign.get('r0035')),
                  campaign.get('engine', 'chromium'), campaign.get('evidenceRetention', False),
                  campaign.get('r002f', {}).get('enabled', False))
    return {'coordinatorSeconds': 2640, 'workflowObservationMinutes': 45}


def observation_budget(args):
    return campaign_budget({'r002fRoute': tabhide_campaign(args), 'r003fHarness': moon_campaign(args),
                            'r003fMatrix': getattr(args, 'r003f_matrix', None),
                            'r0035Costs': getattr(args, 'r0035_costs', False), 'r0035Stages': stage_campaign(args),
                            'r0035Psf':getattr(args,'r0035_psf',False),'r0040Mode':rain_campaign(args),
                            'r0035': star_campaign(args), 'r002f': {'enabled': getattr(args, 'r002f', False)},
                            'evidenceRetention': getattr(args, 'retain_evidence', False),
                            'engine': args.engine, 'r003fDpr': getattr(args, 'r003f_dpr', 1),
                            'workOrders': campaign_selection(args)})


def retained_lane(lane):
    evidence = lane.get('evidenceRetention')
    return isinstance(evidence, dict) and evidence.get('instrumented') is True and 86 in lane.get('stopAllOnExit', [])


def admit_lane_runtime(lane, runtime):
    """Acquisition is executable authority; copied plan/receipt fields are not."""
    if not isinstance(lane, dict):
        raise ValueError('executable lane must be a dictionary')
    if diagnostics.mode_for_lane(lane):
        diagnostics.admit_runtime(lane,runtime)
        return
    argv = lane.get('argv')
    if isinstance(lane.get('preparation'), dict) and lane['preparation'].get('status') == 'INCOMPLETE':
        if argv != []:
            raise ValueError('incomplete preparation cannot execute a substitute recipe')
        return
    role = {'R0040': 'node', 'R003F': 'node', 'R0035': 'python', 'R002F': 'node'}.get(lane.get('workOrder'))
    executable = runtime.get(role) if isinstance(runtime, dict) else None
    if (not isinstance(executable, str) or not Path(executable).is_absolute()
            or not isinstance(argv, list) or len(argv) < 2
            or not all(isinstance(part, str) for part in argv) or argv[0] != executable):
        raise ValueError('lane executable differs from acquired runtime')
    commands = [argv]
    for name in ('evidenceRetention', 'matrixObservation'):
        retained = lane.get(name)
        if isinstance(retained, dict) and 'originalArgv' in retained:
            original = retained['originalArgv']
            if (not isinstance(original, list) or len(original) < 2
                    or not all(isinstance(part, str) for part in original) or original[0] != executable):
                raise ValueError('original executable differs from acquired runtime')
            commands.append(original)
    def dependency(name):
        value = runtime.get(name)
        if not isinstance(value, str) or not Path(value).is_absolute():
            raise ValueError('absolute dependency path required from acquired runtime')
        return value
    environment = lane.get('env', {})
    if not isinstance(environment, dict) or environment.get('NODE_PATH') != dependency('modules'):
        raise ValueError('lane dependency environment differs from acquired runtime')
    for command in commands:
        if lane['workOrder'] == 'R0040':
            index = command.index('--')+1 if command is argv and '--' in command else 2
            if len(command) <= index or command[index] != dependency('playwright'):
                raise ValueError('positional Playwright dependency differs from acquired runtime')
        for name in ('playwright', 'pngjs'):
            option = '--'+name
            matches = [i for i, part in enumerate(command) if part == option or part.startswith(option+'=')]
            required = lane['workOrder'] in ('R003F', 'R002F') if name == 'playwright' else lane['workOrder'] == 'R003F'
            if not matches and not required: continue
            if len(matches) != 1:
                raise ValueError('dependency argument population differs from acquired runtime')
            index = matches[0]
            value = command[index].split('=', 1)[1] if command[index].startswith(option+'=') else (
                command[index+1] if index+1 < len(command) else None)
            if value != dependency(name):
                raise ValueError('explicit dependency path differs from acquired runtime')


class ReturnedCurrentnessRefusal(ValueError):
    """A retained, waited refusal after one complete canonical lane was admitted.

    This is not authority for an interrupted/unknown outer producer, a malformed
    plan, or a failed source check that never returned an observed process.
    """
    def __init__(self, lane, process, receipt, reason):
        super().__init__(reason)
        self.lane = lane
        self.process = process
        self.receipt = receipt


def retain_currentness(args, lane, process, argv, seconds):
    """Save actual byte streams before any success predicate can discard them.

    Old text-only records remain text-only; re-encoding their decoded text would
    not recover original bytes and cannot authorize the new refusal path.
    """
    if type(process) is not dict:
        raise ValueError('currentness process record required')
    clean = {k: v for k, v in process.items() if k not in ('stdoutBytes', 'stderrBytes')}
    parent = args.task/'capture/currentness'
    parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    if any(p.is_symlink() for p in (parent, *parent.parents)):
        raise ValueError('regular private currentness ancestry required')
    phase = 'inner' if getattr(args, 'inside', False) else 'outer'
    folder = Path(tempfile.mkdtemp(prefix=phase+'-'+lane['id']+'-', dir=parent))
    streams = {}
    for label in ('stdout', 'stderr'):
        raw = process.get(label+'Bytes')
        if type(raw) is bytes:
            path = folder/label
            with path.open('xb') as file:
                file.write(raw); file.flush(); os.fsync(file.fileno())
            path.chmod(0o600)
            streams[label] = {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
    complete = (set(streams) == {'stdout', 'stderr'}
                and type(clean.get('returncode')) is int and type(clean.get('timedOut')) is bool
                and same_json(clean.get('argv'), argv) and clean.get('cwd') == str(HERE)
                and type(clean.get('timeoutSeconds')) is int and clean['timeoutSeconds'] == seconds
                and clean.get('error') is None and clean.get('retentionError') is None
                and clean.get('interrupted', False) is False and clean.get('forced', False) is False)
    refused = complete and (clean['timedOut'] or 0 < clean['returncode'] < 126)
    path = folder/'process.json'
    write_json(path, {'protocol': 'salah-returned-currentness/1', 'phase': phase,
                     'lane': lane['id'], 'workOrder': lane['workOrder'], 'process': clean,
                     'streams': streams, 'knownReturnedRefusal': refused,
                     'scope': 'Returned read-only child evidence; no native dispatch or product acceptance.'})
    return clean, {'path': str(path), 'sha256': digest(path)}, refused


def admit_plan(plan, args, runtime):
    if psf_campaign(args):
        phase=getattr(args,'phase',None);identifier=getattr(args,'lane',None)
        native=True
        if getattr(args,'inside',False) and phase=='lane':
            role=next((role for role in psf.ROLES if identifier=='r0035-chromium-psf-'+role),None)
            if role is None:raise ValueError('unknown paired PSF lane')
            retained=args.task/'capture'/('r0035-psf-preadmission-'+role+'.json')
        else:retained=args.task/'capture/r0035-psf-outer-admission.json'
        return psf.admit_plan(plan,args.task,runtime,native=native,retain=retained)
    if plan.get('r0035Psf',False) is not False:
        raise ValueError('PSF plan requires explicit paired campaign')
    """Require the selected identities; preserve missing observations as blocked rows."""
    selected = campaign_selection(args)
    stars = star_campaign(args)
    retention = getattr(args, 'retain_evidence', False)
    stages = stage_campaign(args)
    tabhide = tabhide_campaign(args) == 'tabhide'
    matrix_control = matrix_campaign(args)
    costs = cost_campaign(args)
    if (plan.get('protocol') != 'salah-hosted-native-lanes/1' or plan.get('sequential') is not True
            or plan.get('workOrders') != selected or plan.get('evidenceRetention') is not retention
            or plan.get('r0035Controls', STAR_DEFAULTS) != stars
            or plan.get('r0035Stages', False) is not stages
            or plan.get('r0035Costs', False) is not costs
            or plan.get('r003fHarness', 'published') != moon_campaign(args)
            or plan.get('r0040Mode', 'options') != rain_campaign(args)
            or plan.get('r002fRoute', 'offscreen') != tabhide_campaign(args)
            or plan.get('r003fMatrix') != getattr(args,'r003f_matrix',None)
            or not isinstance(plan.get('lanes'), list)):
        raise ValueError('unadmitted lane plan or campaign controls')
    # Validate the entire population before any optional current-source verifier.
    # Callers pass their acquired runtime, never a value copied from this plan.
    for lane in plan['lanes']:
        admit_lane_runtime(lane, runtime)
    diagnostic=diagnostic_campaign(args)
    if diagnostic:
        if len(plan['lanes'])!=1:raise ValueError('one complete diagnostic lane required')
        lane=plan['lanes'][0];mode=diagnostic['mode'];prepared=lane.get('preparation',{})
        if prepared.get('status') not in ('PASS','INCOMPLETE'):
            raise ValueError('diagnostic preparation status is absent')
        canonical=diagnostics.make_lane(mode,prepared,args.task,runtime)
        if not same_json(lane,canonical):raise ValueError('diagnostic canonical command, source, scope or budget differs')
        if prepared['status']=='PASS':
            common=args.task/'work/prepared/receipts/prepared.json'
            if not same_json(plan.get('preparedReceipt'),diagnostics.record(common)):
                raise ValueError('current diagnostic common preparation differs from copied plan')
            # Bind actual parent/child Python/Node and literal task paths before
            # any optional source verifier can execute.
            prefix=diagnostics.custody_prefix(mode,args.task,runtime)
            expected_sources={k:str(getattr(args,k)) for k in ('research','baseline','historical')}
            if any(prefix['prepared']['sources'][k]['root']!=v for k,v in expected_sources.items()):
                raise ValueError('diagnostic current source roots differ from actual coordinator inputs')
            check=diagnostics.readmit(mode,args.task,runtime)
            check,retained,refused=retain_currentness(args,lane,check,
                [runtime['python'],'-B',str(HERE/'r003f_diagnostics.py'),'readmit'],120)
            if refused:
                raise ReturnedCurrentnessRefusal(lane,check,retained,'actual diagnostic current readmission failed')
            diagnostics.actual_success(check,'actual diagnostic current readmission')
            current=json.loads(check['stdout'])
            if current.get('status')!='PASS' or not same_json(current,prepared):
                raise ValueError('diagnostic current complete preparation differs from copied plan')
        else:current=prepared;check=None
        canonical=diagnostics.make_lane(mode,current,args.task,runtime)
        if not same_json(lane,canonical):raise ValueError('diagnostic canonical command, source, scope or budget differs')
        return [{**lane,**({'preExecutionCurrentness':check} if check is not None else {})}]
    engine = args.engine
    rain_capture = rain_campaign(args) in R0040_CAPTURE_MODES
    observed = rain_campaign(args) == passive.MODE
    dateonly = rain_campaign(args) in ('capture-dateonly', passive.MODE)
    population = [(f'r0040-{engine}-{rain_campaign(args)}' if rain_capture else f'r0040-{engine}', 'R0040', passive.CHILD_SECONDS if observed else 180 if rain_capture else 720),
                  (f'r003f-b0-{engine}-dpr{getattr(args, "r003f_dpr", 1)}', 'R003F', 900),
                  (f'r0035-{engine}-timing', 'R0035', 480), (f'r0035-{engine}-capture', 'R0035', 480),
                  (f'r002f-tabhide-{engine}-dpr{getattr(args, "r002f_dpr", 1)}' if tabhide
                   else f'r002f-{engine}-dpr{getattr(args, "r002f_dpr", 1)}', 'R002F', R002F_TABHIDE_TIMEOUT_SECONDS if tabhide else 900)]
    if matrix_control:population=[(f'r003f-matrix-{engine}-dpr{getattr(args,"r003f_dpr",1)}','R003F',matrix_control['budget']['laneSeconds'])]
    population = [row for row in population if row[1] != 'R0035'
                  or stars['mode'] == 'both' or row[0].endswith('-'+stars['mode'])]
    if costs: population=[(identifier+'-costs' if order=='R0035' else identifier,order,timeout) for identifier,order,timeout in population]
    expected = {identifier: (order, timeout) for identifier, order, timeout in population if order in selected}
    if (tabhide or observed) and [row.get('id') for row in plan['lanes']] != list(expected):
        raise ValueError('complete ordered currentness lane population required')
    actual = {}
    for lane in plan['lanes']:
        if (not isinstance(lane, dict) or not isinstance(lane.get('id'), str) or lane['id'] not in expected
                or lane['id'] in actual or lane.get('workOrder') != expected[lane['id']][0]):
            raise ValueError('duplicate, unknown or unselected lane identity')
        evidence = lane.get('evidenceRetention')
        instrumented = isinstance(evidence, dict) and evidence.get('instrumented') is True
        if (('evidenceRetention' in lane and not instrumented)
                or instrumented != (rain_capture and lane['workOrder'] == 'R0040'
                                    or tabhide and lane['workOrder'] == 'R002F'
                                    or stages and lane['workOrder'] == 'R0035'
                                    or retention and lane['workOrder'] in ('R0040', 'R0035'))
                or instrumented and not retained_lane(lane)):
            raise ValueError('lane retention mode differs from the selected campaign')
        if lane['workOrder'] == 'R002F' and tabhide:
            preparation = lane.get('preparation'); report = lane.get('result', {})
            target = args.task/'capture/lanes'/lane['id']
            if (not isinstance(preparation,dict) or preparation.get('status') not in ('PASS','INCOMPLETE')
                    or lane.get('engine') != 'chromium' or type(lane.get('dpr')) is not int or lane['dpr'] != 1
                    or lane.get('timeoutSeconds') != R002F_TABHIDE_TIMEOUT_SECONDS or lane.get('output') != str(target)
                    or report.get('kind') != 'r002f-tabhide' or report.get('path') != str(target/'result.json')
                    or report.get('expectedRounds') != 1 or report.get('expectedSection') != 'all'
                    or report.get('expectedObserverSha256') != R002F_PROBE_SHA256
                    or report.get('expectedSourceManifestSha256') != R002F_TABHIDE_MANIFEST_SHA256
                    or report.get('expectedRows') != ['baseline/no-hide','baseline/tabhide','candidate/no-hide','candidate/tabhide']
                    or evidence.get('output') != str(target) or evidence.get('timingComparableToOriginal') is not False
                    or lane.get('stopAllOnExit') != [86]):
                raise ValueError('R002F tab-hide source, deadline, private output or population differs')
            tabhide_manifest()
            if preparation['status'] == 'INCOMPLETE':
                if lane.get('argv') != []: raise ValueError('unprepared tab-hide cannot execute a substitute route')
            else:
                argv = lane.get('argv', []); trees = preparation.get('trees', {})
                if (not isinstance(argv,list) or len(argv) != 20 or argv[1] != str(HERE/'r002f_tabhide.cjs')
                        or argv[2:] != ['--playwright', runtime['playwright'],
                            '--baseline', trees['baseline']['root'], '--candidate', trees['candidate']['root'],
                            '--out', str(target), '--engine', 'chromium', '--dpr', '1', '--rounds', '1', '--section', 'all', '--timeout-ms', '180000']
                        or report.get('expectedSources') != preparation.get('generated')
                        or preparation.get('sourceManifestSha256') != R002F_TABHIDE_MANIFEST_SHA256):
                    raise ValueError('R002F tab-hide argv or source admission differs')
                common = Path(plan['preparedReceipt']['path'])
                if (common != args.task/'work/prepared/receipts/prepared.json'
                        or preparation['receipt']['path'] != str(args.task/'work/r002f-prepared/build-result.json')
                        or preparation['processReceipt']['path'] != str(args.task/'capture/r002f-preparation-process.json')
                        or any(trees[arm]['root'] != str(args.task/'work/r002f-prepared'/arm) for arm in ('baseline','candidate'))
                        or digest(common) != plan['preparedReceipt']['sha256']):
                    raise ValueError('R002F common preparation receipt changed')
                common_prepared = validate_prepared(common)
                canonical = make_plan(common_prepared,args.task/'capture/lanes',python_playwright=Path(runtime['python']),
                    node=Path(runtime['node']),node_modules=Path(runtime['modules']),pngjs=Path(runtime['pngjs']),
                    include_r002f=True,work_orders=['R002F'],r002f_route='tabhide',r002f_preparation=preparation,
                    retain_evidence=retention)['lanes']
                if not same_json(plan['lanes'],canonical):
                    raise ValueError('R002F canonical command, source, budget or evidence path differs')
                returned = []
                def retain_generated(check):
                    result = retain_currentness(args,lane,check,[runtime['node'],str(HERE/'r002f_tabhide.cjs'),
                        '--admit-generated',trees['baseline']['root'],trees['candidate']['root']],30)
                    returned.append(result)  # only after every retention write succeeds
                current = admit_r002f_tabhide(Path(preparation['receipt']['path']),Path(preparation['processReceipt']['path']),
                                             common_prepared,common,Path(runtime['node']),retain_generated)
                if returned and returned[0][2]:
                    raise ReturnedCurrentnessRefusal(lane,returned[0][0],returned[0][1],'R002F current generated source readmission failed')
                if current != preparation:
                    raise ValueError('R002F preparation process or current source population changed')
        if ('stageObservation' in lane) != (stages and lane['workOrder'] == 'R0035'):
            raise ValueError('stage observation differs from selected campaign')
        if lane['workOrder'] == 'R0035' and stages:
            preparation = lane.get('preparation'); report = lane.get('result', {})
            wrapper_sha=R0035_COST_WRAPPER_SHA256 if costs else R0035_STAGE_WRAPPER_SHA256
            materializer_sha=R0035_COST_MATERIALIZER_SHA256 if costs else R0035_STAGE_MATERIALIZER_SHA256
            target = args.task/'capture/lanes'/lane['id']; evidence_path = target.with_name(target.name+('-observations' if costs else '-stages'))
            if (not isinstance(preparation, dict) or preparation.get('status') not in ('PASS','INCOMPLETE')
                    or lane.get('stageObservation') != {'protocol': 'r0035-cost-diagnostic/1' if costs else 'r0035-stage-diagnostic/1', 'instrumented': True}
                    or lane.get('engine') != engine or lane.get('dpr') != 1 or lane.get('timeoutSeconds') != 480
                    or lane.get('output') != str(target) or report.get('kind') != 'r0035-trials'
                    or report.get('path') != str(target/'summary.json') or report.get('expectedRows') != 3
                    or report.get('expectedArms') != ['main','unmodified','mitigated'] or report.get('capture') is not False
                    or report.get('requiresEveryRowAdmitted') is not True
                    or report.get('stageWrapperSha256') != wrapper_sha
                    or report.get('stageDriverPath') != str(evidence_path/'driver.json')
                    or evidence.get('output') != str(evidence_path) or evidence.get('timingComparableToOriginal') is not False
                    or costs and (type(lane.get('postObservationCheckSeconds')) is not int or lane['postObservationCheckSeconds']!=90)):
                raise ValueError('stage lane source, private paths or population differs')
            if preparation['status'] == 'INCOMPLETE':
                if lane.get('argv') != []:
                    raise ValueError('unprepared stage lane cannot execute a substitute recipe')
            else:
                original = evidence.get('originalArgv', [])
                if (not isinstance(original, list) or len(original) != 16
                        or original[1] != str(Path(lane['cwd'])/'tools/r0035/native_trials.py')
                        or original[2:] != [preparation['plan'], str(target), '--engine', engine, '--rounds', '1',
                                            '--seconds', '15', '--clock', 'ordinary', '--scene', 'dark', '--motion', 'normal']
                        or preparation.get('wrapperSha256') != wrapper_sha
                        or preparation.get('materializerSha256') != materializer_sha
                        or costs and (preparation.get('collectorSha256')!=cost_material.HELPER_SHA256
                                      or preparation.get('stageMaterializerSha256')!=cost_material.STAGE_MATERIALIZER_SHA256)
                        or not isinstance(preparation.get('custody'), dict)
                        or lane.get('argv') != [original[0], str(HERE/('observe_r0035_costs.py' if costs else 'observe_r0035_stages.py')), '--driver', original[1],
                            '--identity', preparation['identity'], '--preparation-process', preparation['process'],
                            '--preparation-sha256', preparation['custody']['process']['sha256'],
                            '--evidence', str(evidence_path), '--', *original[2:]]):
                    raise ValueError('stage lane does not bind original argv and preparation custody')
                folder = args.task/'capture'/('r0035-cost-preparation' if costs else 'r0035-stage-preparation')
                if any(preparation[key] != str(folder/name) for key, name in
                       (('process','process.json'),('identity','identity.json'),('plan','plan.json'))):
                    raise ValueError('stage lane preparation path differs from this campaign')
                process_path = folder/'process.json'
                process = matrix.load(process_path)
                process_argv = process.get('argv', [])
                if (not isinstance(process_argv, list) or not process_argv
                        or process_argv[0] != runtime['python']):
                    raise ValueError('stage preparation executable differs from acquired runtime')
                process_record = matrix.record(process_path)
                common = plan.get('preparedReceipt', {})
                common_path = Path(common.get('path', ''))
                if not same_json(common, matrix.record(common_path)):
                    raise ValueError('stage common preparation receipt changed')
                current = admit_r0035_stages(validate_prepared(common_path), common_path, process_path,
                                            stars['guard'], stars['scope'], costs=costs)
                if (current.get('status') != 'PASS' or not same_json(current, preparation)
                        or not same_json(current.get('custody', {}).get('process'), process_record)):
                    raise ValueError('stage current preparation or source population differs from plan')
                source_row = preparation['custody']['originalSourcePlan']
                source_path = Path(source_row['path']); source = json.loads(source_path.read_text())
                expected_source = original_star_plan({'trees': {
                    'main': {'root': source['arms']['main']['root']},
                    'r0035': {'root': source['arms']['unmodified']['root']}}}, stars['guard'], stars['scope'])
                if (digest(source_path) != source_row['sha256'] or source != expected_source
                        or source != plan.get('r0035Plan')):
                    raise ValueError('stage lane current source flags differ from this campaign')
        if lane['workOrder'] == 'R0040' and rain_capture:
            preparation = lane.get('preparation'); report = lane.get('result', {})
            target = args.task/'capture/lanes'/lane['id']; evidence_path = target.with_name(target.name+'-retention')
            if (not isinstance(preparation, dict) or preparation.get('status') not in ('PASS', 'INCOMPLETE')
                    or lane.get('engine') != 'chromium' or type(lane.get('dpr')) is not int or lane['dpr'] != 1
                    or lane.get('timeoutSeconds') != (passive.CHILD_SECONDS if observed else 180) or report.get('kind') != 'r0040-'+rain_campaign(args)
                    or lane.get('clearEnv') != ['R0040_OPTIONS']
                    or set(lane.get('env', {})) != {'NODE_PATH', 'R0040_DISPERSION'}
                    or lane['env']['R0040_DISPERSION'] != 'common'
                    or lane.get('output') != str(target) or report.get('path') != str(target/'capture.json')
                    or evidence.get('output') != str(evidence_path)
                    or report.get('finalAdmissionPath') != str(evidence_path/'final-admission.json')
                    or dateonly and (type(lane.get('postCaptureCheckSeconds')) is not int
                                     or lane['postCaptureCheckSeconds'] != (passive.POST_CAPTURE_SECONDS if observed else 100))
                    or observed and (type(lane.get('preCaptureCheckSeconds')) is not int
                                     or lane['preCaptureCheckSeconds'] != passive.READMISSION_SECONDS
                                     or report.get('passiveAdmissionPath') != str(evidence_path/'passive-observation.json'))):
                raise ValueError('R0040 capture mode, private paths or preparation admission differs')
            if preparation['status'] == 'INCOMPLETE':
                if lane.get('argv') != []:
                    raise ValueError('unprepared R0040 capture cannot execute a substitute recipe')
            else:
                original = evidence.get('originalArgv', [])
                expected_argv = [original[0] if original else None,
                    str(HERE/('r0040_passive.cjs' if observed else 'r0040_dateonly.cjs' if dateonly else 'retain_r0040_capture.cjs')),
                    '--driver', original[1] if len(original)>1 else None, '--manifest', preparation['manifest'],
                    '--prepared', preparation['prepared'], '--preparation-process', preparation['process']]
                if dateonly:
                    work = args.task/'work/r0040-capture'
                    entry = args.task/'capture/r0040-preparation-entry.json'
                    if (preparation.get('work') != str(work) or preparation.get('manifest') != str(R0040_MANIFEST)
                            or preparation.get('prepared') != str(work/'receipts/prepared.json')
                            or preparation.get('process') != str(args.task/'capture/r0040-preparation/process.json')
                            or preparation.get('entryReceipt', {}).get('path') != str(entry)
                            or not same_json(preparation.get('dateOnlyPreparation'), {**preparation.get('entryReceipt', {}), 'actualExitCode': 0})
                            or not same_json(preparation.get('dateOnlyDiagnostic'), r0040_dateonly_identity())
                            or not same_json(report.get('diagnostic'), r0040_dateonly_identity())
                            or report.get('journalPath') != str(evidence_path/'events.jsonl')
                            or report.get('isolationReceiptPath') != str(args.task/'capture/isolation'/lane['id']/'receipt.json')):
                        raise ValueError('Date-only capture preparation, helper identity or current namespace path differs')
                    expected_argv += ['--preparation-entry', str(entry)]
                expected_argv += ['--evidence', str(evidence_path), '--', *original[2:]]
                if (not isinstance(original, list) or len(original) != 10
                        or original[1] != str(Path(lane['cwd'])/'tools/qa/r0040/capture.cjs')
                        or original[2] != runtime['playwright']
                        or original[3] != str(Path(preparation['work'])/'historical')
                        or original[5:] != [str(target), 'chromium', 'bday', 'moderate', 'M1']
                        or preparation.get('wrapperSha256') != R0040_CAPTURE_WRAPPER_SHA256
                        or report.get('wrapperSha256') != (passive.ENTRY_SHA256 if observed else R0040_DATEONLY_WRAPPER_SHA256 if dateonly else R0040_CAPTURE_WRAPPER_SHA256)
                        or report.get('expectedCapture') != preparation.get('expectedCapture')
                        or report.get('pins') != preparation.get('pins')
                        or lane.get('argv') != expected_argv):
                    raise ValueError('R0040 capture does not bind its unchanged driver arguments and source receipt')
                if observed:
                    common = args.task/'work/prepared/receipts/prepared.json'
                    common_bytes = passive.regular(common)
                    if not same_json(plan.get('preparedReceipt'), {'path': str(common), 'sha256': hashlib.sha256(common_bytes).hexdigest()}):
                        raise ValueError('passive current common preparation identity differs')
                    prepared = json.loads(common_bytes)
                    custody = passive.preparation_runtime(entry, preparation['process'], common, prepared, runtime, args.task)
                    if (not same_json(custody, preparation.get('passiveRuntime'))
                            or not same_json(passive.verify_sources(), preparation.get('passiveSources'))):
                        raise ValueError('passive current runtime, process or source custody differs')
                    canonical = make_plan(prepared, args.task/'capture/lanes', python_playwright=Path(runtime['python']),
                        node=Path(runtime['node']), node_modules=Path(runtime['modules']), pngjs=Path(runtime['pngjs']),
                        work_orders=['R0040'], r0040_mode=passive.MODE, r0040_preparation=preparation,
                        retain_evidence=retention)['lanes']
                    if not same_json(plan['lanes'], canonical):
                        raise ValueError('passive canonical command, source, budget or evidence path differs')
                    check = passive.readmit(common, runtime, args.task)
                    check,retained,refused=retain_currentness(args,lane,check,
                        [runtime['python'],'-B',str(HERE/'r0040_passive_central.py'),'--readmit'],passive.READMISSION_SECONDS)
                    if refused:
                        raise ReturnedCurrentnessRefusal(lane,check,retained,'passive current source readmission failed')
                    if type(check.get('returncode')) is not int or check['returncode'] != 0 or check.get('timedOut') is not False:
                        raise ValueError('passive current source readmission failed: '+json.dumps(check, allow_nan=False))
                    current = json.loads(check['stdout'])
                    if current.get('status') != 'PASS' or not same_json(current, preparation):
                        raise ValueError('passive current complete preparation differs from copied plan')
                    canonical = make_plan(prepared, args.task/'capture/lanes', python_playwright=Path(runtime['python']),
                        node=Path(runtime['node']), node_modules=Path(runtime['modules']), pngjs=Path(runtime['pngjs']),
                        work_orders=['R0040'], r0040_mode=passive.MODE, r0040_preparation=current,
                        retain_evidence=retention)['lanes'][0]
                    if not same_json(lane, canonical):
                        raise ValueError('passive canonical command, source, budget or evidence path differs')
                    lane = {**lane, 'preExecutionCurrentness': check}
        if lane['workOrder'] == 'R003F' and moon_campaign(args) == 'corrected-b0':
            preparation = lane.get('preparation'); report = lane.get('result', {})
            if not isinstance(preparation, dict) or preparation.get('status') not in ('PASS', 'INCOMPLETE'):
                raise ValueError('corrected R003F lane lacks preparation admission')
            if preparation['status'] == 'INCOMPLETE':
                if lane.get('argv') != []:
                    raise ValueError('unprepared corrected R003F lane cannot execute a substitute recipe')
            else:
                harness = preparation.get('harness'); argv = lane.get('argv', [])
                if (not isinstance(harness, dict) or harness.get('protocol') != 'R003F/corrected-harness/1'
                        or harness.get('materializationSha256') != R003F_MATERIALIZATION
                        or report.get('expectedHarness') != harness or report.get('kind') != 'r003f-b0'
                        or report.get('expectedIndexSha256') != BASE_INDEX
                        or report.get('expectedCaptures') != ['offset', 'b0', 'b0-repeat', 'reference']
                        or lane.get('engine') != engine or lane.get('dpr') != getattr(args, 'r003f_dpr', 1)
                        or len(argv) < 2 or not isinstance(preparation.get('root'), str)
                        or argv[1] != str(Path(preparation['root'])/'tools/qa/r003f_owner_baseline.cjs')):
                    raise ValueError('corrected R003F lane does not bind its admitted helpers and result')
        if matrix_control:
            preparation=lane.get('preparation',{});env=lane.get('env',{})
            if preparation.get('status') not in ('PASS','INCOMPLETE') or set(env)!= {'NODE_PATH'}:
                raise ValueError('matrix preparation or dependency binding is absent')
            if preparation['status']=='PASS':
                if (preparation.get('entry',{}).get('path')!=str(args.task/'capture/r003f-matrix-preparation-entry.json')
                        or preparation.get('root')!=str(args.task/'work/r003f-matrix')
                        or preparation.get('central',{}).get('sha256')!=MATRIX_PINS
                        or preparation.get('harness',{}).get('materializationSha256')!=matrix.MATERIALIZATION
                        or len(preparation.get('harness',{}).get('outputFiles',[]))!=16):
                    raise ValueError('matrix current source/preparation path or closure differs')
                entry = args.task/'capture/r003f-matrix-preparation-entry.json'
                process_runtime = matrix_preparation_runtime(entry, runtime['node'], runtime['python'])
                current = matrix.admit(entry, MATRIX_PINS)
                if (not same_json(current, preparation)
                        or not same_json(current.get('common', {}).get('prepared'), plan.get('preparedReceipt'))
                        or any(not same_json(current.get(key), row) for key, row in process_runtime.items())
                        or current.get('node') != runtime['node'] or current.get('python') != runtime['python']):
                    raise ValueError('matrix current preparation or source population differs from plan')
                preparation = current
            original=lane.get('matrixObservation',{}).get('originalArgv',[])
            node=preparation.get('node','') if preparation['status']=='PASS' else ''
            if preparation['status']=='PASS' and (not isinstance(node,str) or not node or not original or original[0]!=node):
                raise ValueError('matrix executable differs from admitted preparation node')
            canonical=matrix.make_lane(matrix_control,preparation,args.task/'capture/lanes',engine,getattr(args,'r003f_dpr',1),node,
                Path(runtime['modules']) if preparation['status']=='PASS' else Path(env['NODE_PATH']),
                Path(runtime['pngjs']) if preparation['status']=='PASS' else Path(env['NODE_PATH'])/'pngjs',MATRIX_PINS)
            if not same_json(lane,canonical):raise ValueError('matrix canonical argv, selected population, timeout or evidence custody differs')
        actual[lane['id']] = lane
    return [actual.get(identifier, {'id': identifier, 'workOrder': order, 'timeoutSeconds': timeout,
                                   'preparation': {'status': 'INCOMPLETE',
                                                   'reason': f'requested {order} lane {identifier} is missing from the plan'}})
            for identifier, (order, timeout) in expected.items()]


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')
    path.chmod(0o600)


def validate_snapshot(snapshot, outer_netns):
    if len(snapshot['uids']) != 3 or min(snapshot['uids']) <= 0 or len(set(snapshot['uids'])) != 1:
        raise ValueError('nonroot real/effective/saved UID required')
    if len(snapshot['gids']) != 3 or min(snapshot['gids']) <= 0 or len(set(snapshot['gids'])) != 1:
        raise ValueError('nonroot real/effective/saved GID required')
    if snapshot['groups']:
        raise ValueError('supplementary groups retained')
    if not outer_netns or snapshot['netns'] == outer_netns:
        raise ValueError('fresh network namespace required')
    links = snapshot['links']
    if len(links) != 1 or links[0]['ifname'] != 'lo' or not {'LOOPBACK', 'UP'} <= set(links[0]['flags']):
        raise ValueError('only an active loopback interface is allowed')
    for route in snapshot['routes4'] + snapshot['routes6']:
        dst = route.get('dst')
        if route.get('dev') != 'lo' or route.get('gateway') or dst in (None, 'default'):
            raise ValueError('non-loopback route')
        network = ipaddress.ip_network(dst, strict=False)
        if not network.is_loopback and str(network) != 'ff00::/8':
            raise ValueError('external destination route')
    for name in CAP_FIELDS:
        if int(snapshot['status'][name], 16) != 0:
            raise ValueError('retained capability ' + name)
    if snapshot['status'].get('NoNewPrivs') != '1':
        raise ValueError('no-new-privileges missing')
    if snapshot['externalSocketErrno'] not in (errno.ENETUNREACH, errno.EHOSTUNREACH):
        raise ValueError('external socket was not refused by routing boundary')


def kernel_snapshot():
    status = dict(line.split(':', 1) for line in Path('/proc/self/status').read_text().splitlines() if ':' in line)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(2)
        try:
            sock.connect(('192.0.2.1', 443)); result = 0
        except OSError as exc:
            result = exc.errno
    ip = '/usr/sbin/ip' if Path('/usr/sbin/ip').exists() else '/sbin/ip'
    read_ip = lambda *args: json.loads(subprocess.check_output([ip, '-j', *args], text=True))
    return {'uids': list(os.getresuid()), 'gids': list(os.getresgid()), 'groups': os.getgroups(),
            'netns': os.readlink('/proc/self/ns/net'), 'links': read_ip('link', 'show'),
            'routes4': read_ip('-4', 'route', 'show', 'table', 'all'),
            'routes6': read_ip('-6', 'route', 'show', 'table', 'all'),
            'status': {k: status[k].strip() for k in (*CAP_FIELDS, 'NoNewPrivs')},
            'externalSocketErrno': result}


def clean_environment(node, python, task, browsers, modules, baseline, research):
    task = Path(task)
    return {'PATH': ':'.join((str(Path(node).parent), str(Path(python).parent), '/usr/local/bin',
                             '/usr/bin', '/bin', '/usr/sbin', '/sbin')),
            'LANG': 'C.UTF-8', 'LC_ALL': 'C.UTF-8', 'TZ': 'UTC',
            'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONNOUSERSITE': '1',
            'PLAYWRIGHT_BROWSERS_PATH': str(browsers), 'NODE_PATH': str(modules),
            'TMPDIR': str(task/'temporary'), 'XDG_CACHE_HOME': str(task/'cache'),
            'XDG_CONFIG_HOME': str(task/'config'), 'XDG_RUNTIME_DIR': str(task/'runtime'),
            'GIT_CONFIG_COUNT': '2', 'GIT_CONFIG_KEY_0': 'safe.directory',
            'GIT_CONFIG_VALUE_0': str(baseline), 'GIT_CONFIG_KEY_1': 'safe.directory',
            'GIT_CONFIG_VALUE_1': str(research)}


def run_bounded(argv, cwd, env, stdout, stderr, timeout):
    stdout, stderr = Path(stdout), Path(stderr)
    stdout.parent.mkdir(parents=True, exist_ok=True); stderr.parent.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    timed_out = False
    with stdout.open('wb') as out, stderr.open('wb') as err:
        proc = subprocess.Popen(argv, cwd=cwd, env=env, stdout=out, stderr=err, start_new_session=True)
        try:
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(proc.pid, signal.SIGTERM)
            try: proc.wait(timeout=2)
            except subprocess.TimeoutExpired: pass
            # The leader can exit before its descendants. Kill the process group
            # even when wait() already returned; namespace teardown is a second fence.
            try: os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError: pass
            proc.wait()
        except BaseException:
            try: os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError: pass
            proc.wait()
            raise
    return {'returncode': proc.returncode, 'timedOut': timed_out,
            'elapsedSeconds': time.monotonic() - started}


def r002f_report_status(body, lane, returncode, timed_out):
    """A complete selected population is necessary for PASS, never a status word."""
    if not isinstance(body, dict) or body.get('protocol') != 'r002f-hosted-native/1':
        return 'FAIL' if returncode == 1 else 'INCOMPLETE'
    pairs, preview = body.get('prayerPairs'), body.get('preview')
    def verdict(row):
        value = row.get('verdict') if isinstance(row, dict) else None
        return value.get('status') if isinstance(value, dict) else None
    recorded = [verdict(row) for group in (pairs, preview) if isinstance(group, list) for row in group]
    if body.get('status') == 'FAIL' or 'FAIL' in recorded:
        return 'FAIL'
    if body.get('status') in ('INCOMPLETE', 'INCONCLUSIVE'):
        return body['status']
    if timed_out or not isinstance(pairs, list) or not isinstance(preview, list):
        return 'INCOMPLETE'
    expected = lane['result']
    rounds, section = expected.get('expectedRounds'), expected.get('expectedSection')
    if (type(rounds) is not int or not 1 <= rounds <= 10 or section not in ('all', 'prayer', 'preview')
            or type(body.get('dpr')) is not int or type(body.get('rounds')) is not int
            or body.get('engine') != lane.get('engine') or body.get('dpr') != lane.get('dpr')
            or body.get('rounds') != rounds or body.get('section') != section
            or not expected.get('expectedObserverSha256')
            or body.get('observerSha256') != expected['expectedObserverSha256']):
        return 'INCOMPLETE'
    sources = body.get('sources')
    for arm, index in (('baseline', '88411488017ea590e6b4c5a21adc143977c0907089eabb80b0cbe8f0ba18a8a1'),
                       ('candidate', '55a8bdbc7b7ab5cb53ede3b58c0ef1e4101c7c89bc6936860bd4bc5f3acb8fe2')):
        source = sources.get(arm) if isinstance(sources, dict) else None
        if not isinstance(source, dict) or source.get('indexSha256') != index:
            return 'INCOMPLETE'
    wanted_pairs = {(scenario, round_) for round_ in range(1, rounds + 1)
                    for scenario in ('fajr', 'maghrib', 'midnight')} if section != 'preview' else set()
    actual_pairs = []
    for row in pairs:
        if not isinstance(row, dict) or type(row.get('round')) is not int or not isinstance(row.get('scenario'), str):
            return 'INCOMPLETE'
        actual_pairs.append((row['scenario'], row['round']))
        if any(row.get(arm) != f'{arm}-{row["scenario"]}-{row["round"]}.json' for arm in ('baseline', 'candidate')):
            return 'INCOMPLETE'
    wanted_preview = {'baseline', 'candidate'} if section != 'prayer' else set()
    actual_preview = []
    for row in preview:
        if not isinstance(row, dict) or not isinstance(row.get('arm'), str) or row.get('file') != row['arm']+'-preview.json':
            return 'INCOMPLETE'
        actual_preview.append(row['arm'])
    if (len(actual_pairs) != len(wanted_pairs) or set(actual_pairs) != wanted_pairs
            or len(actual_preview) != len(wanted_preview) or set(actual_preview) != wanted_preview):
        return 'INCOMPLETE'
    statuses = [verdict(row) for row in pairs]
    for row in preview:
        if row['arm'] == 'baseline' and verdict(row) != 'OBSERVED':
            return 'INCOMPLETE'
        statuses.append('PASS' if row['arm'] == 'baseline' and verdict(row) == 'OBSERVED' else verdict(row))
    if any(status not in ('PASS', 'INCONCLUSIVE') for status in statuses):
        return 'INCOMPLETE'
    if 'INCONCLUSIVE' in statuses:
        return 'INCONCLUSIVE'
    if returncode == 1:
        return 'FAIL'
    return 'PASS' if body.get('status') == 'PASS' and statuses and returncode == 0 else 'INCOMPLETE'


def r002f_tabhide_status(body, lane, returncode, timed_out):
    result = {'status':'INCOMPLETE','stopAll':False,'returncode':returncode,'timedOut':timed_out,
              'nativeQualification':'LIFECYCLE_OBSERVATION_ONLY','humanAcceptance':'OUTSTANDING'}
    if isinstance(body,dict) and body.get('status') == 'ISOLATION_FAIL':
        return {**result,'status':'ISOLATION_FAIL','stopAll':True}
    if returncode == 86:
        veto = isinstance(body,dict) and body.get('status') == VETO_STATUS and body.get('continuationVetoed') is True
        return {**result,'status':VETO_STATUS if veto else 'ISOLATION_FAIL','stopAll':True,
                'reason':VETO_REASON if veto else 'headed browser boundary or current isolation admission failed'}
    rows = body.get('rows') if isinstance(body,dict) else None
    if returncode == 1 or isinstance(body,dict) and (body.get('status') == 'FAIL'
            or isinstance(rows,list) and any(isinstance(row,dict) and isinstance(row.get('verdict'),dict)
                and row['verdict'].get('status') == 'FAIL' for row in rows)):
        return {**result,'status':'FAIL'}
    if timed_out or returncode != 0 or not isinstance(body,dict): return result
    expected = lane['result']
    if (body.get('protocol') != 'r002f-tabhide-native/1' or body.get('status') != TABHIDE_OBSERVED
            or body.get('sourceManifestSha256') != R002F_TABHIDE_MANIFEST_SHA256
            or expected.get('expectedSourceManifestSha256') != R002F_TABHIDE_MANIFEST_SHA256
            or body.get('sources') != expected.get('expectedSources')):
        return result
    try:
        tabhide_manifest()
        output = Path(lane['output']); trees = lane['preparation']['trees']
        isolation = output.parents[1]/'isolation'/lane['id']/'receipt.json'
        argv = [lane['argv'][0],str(HERE/'r002f_tabhide.cjs'),'--verify-json',expected['path'],
                trees['baseline']['root'],trees['candidate']['root'],str(isolation)]
        stdout,stderr=output/'verification.stdout',output/'verification.stderr'
        verification=run_bounded(argv,str(HERE),dict(os.environ),stdout,stderr,45)
        result['verification']={**verification,'argv':argv,'cwd':str(HERE),'timeoutSeconds':45,
                                'stdout':str(stdout),'stderr':str(stderr)}
        verdict=json.loads(stdout.read_text()) if verification['returncode']==0 and not verification['timedOut'] else None
        if verdict == {'status':TABHIDE_OBSERVED,'nativeQualification':'LIFECYCLE_OBSERVATION_ONLY','humanAcceptance':'OUTSTANDING'}:
            result['status']=TABHIDE_OBSERVED
    except (OSError,ValueError,KeyError,TypeError,AttributeError,subprocess.SubprocessError) as error:
        result['reason']=str(error)
    return result


def r0040_capture_status(body, lane, returncode, timed_out, *, admitted_status=CAPTURE_ADMITTED,
                        timing_class='instrumented-host-retention'):
    """Acquisition admission cannot confer cadence, image or owner acceptance."""
    result = {'status': 'INCOMPLETE', 'nativeQualification': 'NOT_VERIFIED', 'humanAcceptance': 'OUTSTANDING'}
    path = Path(lane['result']['finalAdmissionPath'])
    try:
        if path.is_symlink(): return result
        data = path.read_bytes(); final = json.loads(data)
        result['finalAdmission'] = {'path': str(path), 'sha256': hashlib.sha256(data).hexdigest()}
    except (OSError, ValueError): final = None
    if type(returncode) is int and returncode > 0:
        return {**result, 'status': 'FAIL'}
    if (isinstance(final, dict) and final.get('protocol') == 'r0040-capture-final-admission/1'
            and final.get('status') == 'FAILED'):
        return {**result, 'status': 'FAIL'}
    if timed_out or returncode != 0 or not isinstance(body, dict) or not isinstance(final, dict):
        return result
    if (final.get('protocol') != 'r0040-capture-final-admission/1' or final.get('status') != admitted_status
            or any(type(final.get(k)) is not int or final[k] != 0 for k in ('originalExitCode', 'exitCode'))
            or final.get('continuationVetoed') is not False
            or any(final.get(k) != [] for k in ('issues', 'reportIssues', 'errors', 'driverErrors'))
            or final.get('retentionError') is not None or 'retentionError' not in final
            or final.get('nativeQualification') != 'NOT_VERIFIED' or final.get('humanAcceptance') != 'OUTSTANDING'
            or final.get('timingClass') != timing_class
            or not isinstance(final.get('requests'), list) or not isinstance(final.get('pages'), list)):
        return result
    closes = final.get('closes')
    if (not isinstance(closes, dict) or set(closes) != {'context', 'browser', 'server'}
            or any(not isinstance(row, dict) or row.get('returned') is not True or row.get('event') is not True
                   for row in closes.values())):
        return result
    expected = lane['result'].get('expectedCapture'); pins = lane['result'].get('pins')
    if not isinstance(expected, dict) or not expected or not isinstance(pins, dict) or not pins:
        return result
    if (any(body.get(k) != v for k, v in expected.items() if k not in ('source', 'effectiveRateMmPerHour'))
            or any(body.get(k) != v for k, v in pins.items())
            or any(body.get(k) != expected.get('source') for k in ('before', 'after'))):
        return result
    report = Path(lane['result']['path'])
    try:
        if report.is_symlink(): return result
        raw = report.read_bytes()
        if final.get('originalReport') != {'file': str(report), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}:
            return result
    except OSError: return result
    return {**result, 'status': admitted_status}


def _dateonly_node(lane, script, payload, timeout):
    """Read-only checks retain both streams and actual process completion."""
    env = dict(os.environ)
    env.pop('NODE_OPTIONS', None)
    try:
        result = subprocess.run([lane['evidenceRetention']['originalArgv'][0], '-e', script,
                                 str(HERE/'r0040_dateonly.cjs')], cwd=HERE, env=env,
                                input=json.dumps(payload, allow_nan=False), capture_output=True, text=True, timeout=timeout)
        return {'returncode': result.returncode, 'timedOut': False, 'stdout': result.stdout, 'stderr': result.stderr}
    except subprocess.TimeoutExpired as error:
        def stream(value):
            return value.decode('utf-8', errors='replace') if isinstance(value, bytes) else value
        return {'returncode': None, 'timedOut': True, 'stdout': stream(error.stdout), 'stderr': stream(error.stderr)}
    except OSError as error:
        return {'returncode': None, 'timedOut': False, 'stdout': '', 'stderr': str(error)}


def _dateonly_current_check(lane, source, manifest):
    """Re-admit actual namespace, original byte closure and actual preparation."""
    script = r'''
const fs=require('fs'),path=require('path'),crypto=require('crypto'),{execFileSync}=require('child_process'),{isDeepStrictEqual}=require('util');
const d=require(process.argv[1]),r=require(path.join(path.dirname(process.argv[1]),'retain_r0040_capture.cjs'));
const p=JSON.parse(fs.readFileSync(0,'utf8')),a=p.args,o=p.options,m=p.manifest,s=p.source;
const need=(ok,msg)=>{if(!ok)throw Error(msg)},sha=x=>crypto.createHash('sha256').update(x).digest('hex');
const isolation=r.verifyIsolation(s.isolation.file);
need(isDeepStrictEqual(isolation,s.isolation),'current namespace receipt differs');
need(sha(fs.readFileSync(o.manifest))===s.manifestSha256,'current manifest differs');
for(const [name,key] of [['prepared','prepared'],['preparationProcess','preparationProcess']])
  need(path.resolve(o[name])===s[key].path&&sha(fs.readFileSync(o[name]))===s[key].sha256,'current preparation receipt differs');
r.verifyDriver(o.driver);
const research=path.resolve(path.dirname(o.driver),'../../..');
const git=(root,...args)=>execFileSync('git',['-C',root,...args],{encoding:'utf8',timeout:30000,
  env:{...process.env,GIT_NO_LAZY_FETCH:'1',GIT_TERMINAL_PROMPT:'0'}}).trim();
need(git(research,'rev-parse','HEAD')===m.researchCommit,'current research head differs');
need(git(a[2],'rev-parse','HEAD')===m.main.head&&!git(a[2],'status','--porcelain=v1','--untracked-files=all'),'current main is not genuine and clean');
const checked={research:r.verifySourceRows(research,m.researchInputs),historical:r.verifySourceRows(a[1],m.stages.at(-1).files),main:r.verifySourceRows(a[2],m.main.runtimeFiles)};
need(isDeepStrictEqual(checked,s.sources),'current executed source closure differs');
const files=[];function walk(root,rel=''){for(const e of fs.readdirSync(path.join(root,rel),{withFileTypes:true})){
 const n=path.posix.join(rel,e.name);if(e.isDirectory())walk(root,n);else files.push(n);}}
walk(a[1]);need(isDeepStrictEqual(files.sort(),Object.keys(m.stages.at(-1).files).sort()),'current historical population differs');
const inv=fs.readFileSync(path.join(a[2],'GENERATED.json'));
need(sha(inv)===m.main.generatedInventorySha256,'current generated inventory differs');
const inventory=JSON.parse(inv);need(inventory.fileCount===m.main.generatedMembers&&Object.keys(inventory.files).length===inventory.fileCount,'current generated population differs');
r.verifySourceRows(a[2],inventory.files);
const preparationEntry=d.admitPreparationEntry(o.preparationEntry,o,a);
need(isDeepStrictEqual(preparationEntry,s.preparationEntry),'actual outer entry differs');
const diagnostic=d.diagnosticIdentity(d.transformHelper(fs.readFileSync(path.join(a[1],'tools/qa/precip_eval_lib.cjs'))).identity);
need(isDeepStrictEqual(diagnostic,s.diagnostic),'actual helper transformation differs');
process.stdout.write(JSON.stringify({isolation,preparationEntry,diagnostic,sourcePopulation:Object.fromEntries(Object.entries(checked).map(([k,v])=>[k,Object.keys(v).length]))}));
'''
    preparation = lane['preparation']
    return _dateonly_node(lane, script, {'args': lane['evidenceRetention']['originalArgv'][2:],
        'options': {'driver': lane['evidenceRetention']['originalArgv'][1], 'manifest': preparation['manifest'],
                    'prepared': preparation['prepared'], 'preparationProcess': preparation['process'],
                    'preparationEntry': preparation['entryReceipt']['path']}, 'source': source, 'manifest': manifest}, 90)


def r0040_dateonly_status(body, lane, returncode, timed_out, *, passive_tail=False):
    """A durable supplemental admission is never a replacement capture report."""
    result = {**r0040_capture_status(body, lane, returncode, timed_out,
                                  admitted_status=R0040_DATEONLY_ADMITTED, timing_class='instrumented-date-only-clock'),
              'timingClass': 'instrumented-date-only-clock'}
    if result['status'] != R0040_DATEONLY_ADMITTED:
        return result
    result['status'] = 'INCOMPLETE'
    def need(value, message):
        if not value: raise ValueError(message)
    def regular(path):
        path=Path(path).absolute()
        need(path.is_file() and not any(p.is_symlink() for p in (path,*path.parents)), 'regular Date-only evidence path required')
        return path.read_bytes()
    def reference(row, expected_path, file_key='path'):
        need(isinstance(row,dict) and row.get(file_key)==str(expected_path), 'Date-only custody path differs')
        raw=regular(row[file_key]);need(hashlib.sha256(raw).hexdigest()==row.get('sha256'), 'Date-only custody bytes differ')
        return json.loads(raw)
    try:
        report=lane['result'];preparation=lane['preparation'];identity=r0040_dateonly_identity()
        need(digest(HERE/'r0040_dateonly.cjs')==R0040_DATEONLY_WRAPPER_SHA256, 'Date-only entry source differs')
        need(same_json(report.get('diagnostic'),identity) and same_json(preparation.get('dateOnlyDiagnostic'),identity), 'Date-only planned identity differs')
        final=json.loads(regular(report['finalAdmissionPath']))
        need(same_json(final.get('diagnostic'),identity), 'Date-only final identity differs')
        manifest=json.loads(regular(R0040_MANIFEST))
        need(digest(R0040_MANIFEST)==R0040_MANIFEST_SHA256==preparation['sourceCustody']['manifestSha256'], 'Date-only original manifest differs')
        need(set(preparation['sourceCustody'])=={'manifestSha256','recipeSourceSha256','preparationProcess','prepared','preparationOuterExit'}
             and preparation['sourceCustody']['recipeSourceSha256']=='9fc26a75cb62c145f9de7bd7aa386ac6714c238f3e08089558d34f02882f9730',
             'complete original preparation source custody required')
        raw=regular(report['journalPath']);need(raw.endswith(b'\n'), 'complete terminal journal line required')
        rows=[json.loads(line) for line in raw.splitlines()]
        need(rows and all(isinstance(row,dict) and type(row.get('sequence')) is int and row['sequence']==i+1
                          for i,row in enumerate(rows)), 'contiguous Date-only journal required')
        selected={name:[(i,row) for i,row in enumerate(rows) if row.get('event')==name]
                  for name in ('sources','date-only-clock-proof','driver-process-ended')}
        need(all(len(value)==1 for value in selected.values()), 'one source, clock and terminal event required')
        source_index,source=selected['sources'][0];proof_index,proof_event=selected['date-only-clock-proof'][0]
        terminal_index,terminal=selected['driver-process-ended'][0]
        if passive_tail:
            need(lane['result']['kind'] == passive.KIND, 'passive journal extension requires its own route')
            passive.check_tail(rows, final)
        need(source_index<proof_index<terminal_index==len(rows)-(2 if passive_tail else 1), 'Date-only source/proof/final order differs')
        need(same_json({k:v for k,v in terminal.items() if k not in ('sequence','atUtc','monotonicNs','event')},final), 'terminal journal and final receipt differ')
        proofs=final.get('clockProofs')
        need(isinstance(proofs,list) and len(proofs)==1 and proofs[0].get('status')=='OBSERVED'
             and proofs[0].get('error') is None and same_json(proof_event.get('proof'),proofs[0]), 'complete retained native clock proof required')
        need(same_json(source.get('diagnostic'),identity) and same_json(source.get('originalArgv'),lane['evidenceRetention']['originalArgv'][2:]), 'original capture argv or source identity differs')
        wanted={'research':manifest['researchInputs'],'historical':manifest['stages'][-1]['files'],'main':manifest['main']['runtimeFiles']}
        need(same_json(source.get('sources'),wanted), 'complete original executed source population required')
        need(all(same_json(source.get(k),v) for k,v in preparation['sourceCustody'].items()), 'source preparation custody differs')
        for key,path in (('prepared',preparation['prepared']),('preparationProcess',preparation['process'])):
            reference(source[key],path)
        entry=source.get('preparationEntry')
        need(same_json(entry,preparation['dateOnlyPreparation']) and same_json(entry,{**preparation['entryReceipt'],'actualExitCode':0}), 'actual outer preparation identity differs')
        reference(entry,preparation['entryReceipt']['path'])
        isolation=reference(source.get('isolation'),report['isolationReceiptPath'],'file')
        need(isolation.get('protocol')=='salah-hosted-native-isolation/1' and isolation.get('passed') is True
             and type(isolation.get('uid')) is int and isolation['uid']>0 and isolation.get('browserControl',{}).get('passed') is True,
             'successful nonroot namespace evidence required')
        expected=report['expectedCapture']
        need(all(same_json(body.get(k),v) for k,v in expected.items() if k not in ('source','effectiveRateMmPerHour')),
             'strict original capture metadata differs')
        scene=final.get('scene');need(isinstance(scene,dict) and isinstance(scene.get('base'),str), 'complete capture scene required')
        need(scene.get('options',{}).get('clock')=='running' and same_json(scene['options'].get('utcMs'),expected['utcMs']), 'original running scene differs')
        need(scene.get('log',{}).get('continuedExternal')==[] and not scene.get('log',{}).get('errors'), 'original final scene errors remain')
        need(len(final['pages'])==1 and final['pages'][0].get('id')==1 and final['pages'][0].get('closed') is True
             and final['pages'][0].get('errors')==[] and not final['pages'][0].get('crashed'), 'complete uncrashed closed page required')
        need(all(row.get('called') is True and not row.get('error') for row in final['closes'].values())
             and same_json(final['closes']['browser'].get('disconnections'),[{'duringClose':True}]), 'original cleanup or disconnection differs')
        requests=final['requests'];need(bool(requests), 'complete observed request population required')
        for i,row in enumerate(requests):
            actions=row.get('actions')
            need(type(row.get('id')) is int and row['id']==i+1 and row.get('callbackState')=='returned'
                 and sorted(row.get('observedBy',[]))==['context','route'] and isinstance(actions,list) and actions, 'request identity or route completion differs')
            need(all(a.get('action') in ('continue','fulfill','abort') and a.get('state')=='completed' and a.get('refused') is False
                     for a in actions), 'request action was incomplete or refused')
            need(row.get('browserState')=='finished' or row.get('browserState')=='failed' and actions[-1]['action']=='abort', 'late request failure remains')
        clock_script=r'''
const fs=require('fs'),path=require('path'),{isDeepStrictEqual}=require('util'),d=require(process.argv[1]);
const g=require(path.join(path.dirname(process.argv[1]),'retain_r0040.cjs')),p=JSON.parse(fs.readFileSync(0,'utf8'));
const admission=d.admitClockProof(p.proof.raw,p.utcMs);
if(!isDeepStrictEqual(admission,p.proof.admission))throw Error('retained native clock admission differs');
for(const row of p.requests)for(const action of row.actions)
 if(action.action==='continue'&&!g.allowedContinuation(action.destination,p.base))throw Error('unadmitted external continuation');
process.stdout.write(JSON.stringify(admission));
'''
        result['clockCheck']=_dateonly_node(lane,clock_script,{'proof':proofs[0],'utcMs':expected['utcMs'],
                                                            'requests':requests,'base':scene['base']},10)
        check=result['clockCheck'];need(type(check['returncode']) is int and check['returncode']==0 and check['timedOut'] is False,
                                       'native clock proof or request-route recomputation failed')
        need(same_json(json.loads(check['stdout']),proofs[0]['admission']), 'recomputed native clock receipt differs')
        result['currentSourceCheck']=_dateonly_current_check(lane,source,manifest)
        check=result['currentSourceCheck'];need(type(check['returncode']) is int and check['returncode']==0 and check['timedOut'] is False,
                                                'current namespace, preparation or source closure did not re-admit')
        wanted_check={'isolation':source['isolation'],'preparationEntry':entry,'diagnostic':identity,
                      'sourcePopulation':{k:len(v) for k,v in wanted.items()}}
        need(same_json(json.loads(check['stdout']),wanted_check), 'current Date-only source receipt differs')
        result.update(status=R0040_DATEONLY_ADMITTED,diagnostic=identity,
                      journal={'path':report['journalPath'],'sha256':hashlib.sha256(raw).hexdigest()})
    except (OSError, ValueError, KeyError, IndexError, TypeError, AttributeError) as error:
        result['reason']=str(error)
    return result


def r0040_passive_status(body, lane, returncode, timed_out):
    result = r0040_dateonly_status(body, lane, returncode, timed_out, passive_tail=True)
    result['dateOnlyStatus'] = result['status']
    result['timingClass'] = passive.TIMING
    if result['status'] != R0040_DATEONLY_ADMITTED:
        return result
    result['status'] = 'INCOMPLETE'
    try:
        rows = [json.loads(row) for row in passive.regular(lane['result']['journalPath']).splitlines()]
        source = next(row for row in rows if row.get('event') == 'sources')
        check, artifacts = passive.final_check(lane, returncode, source, rows)
        result['passiveVerification'] = check
        passive.need(type(check.get('returncode')) is int and check['returncode'] == 0 and check.get('timedOut') is False,
                     'actual passive receipt or raw original stop replay failed')
        replay = json.loads(check['stdout'])
        passive.need(replay.get('protocol') == 'r0040-passive-central-inspection/1' and replay.get('status') == 'OBSERVED'
                     and type(replay.get('actualExitCode')) is int and replay['actualExitCode'] == returncode
                     and same_json(replay.get('identity'), lane['result']['passiveDiagnostic'])
                     and same_json(replay.get('artifacts'), artifacts), 'current passive replay identity differs')
        result.update(status=passive.ADMITTED, passiveDiagnostic=replay['identity'],
                      passiveInspection=replay['inspection'], passiveArtifacts=artifacts)
    except (OSError, ValueError, KeyError, IndexError, TypeError, AttributeError, StopIteration) as error:
        result['reason'] = str(error)
    return result


def _r0035_cost_current_check(lane, final):
    """Bounded actual namespace/preparation/full-source re-admission after trial."""
    script=r'''
import json,sys
from pathlib import Path
sys.path.insert(0,sys.argv[1])
import r0035_cost_materialize as m
p=json.load(sys.stdin);lane=p['lane'];prep=lane['preparation'];final=p['final'];loader=m.support()
isolation=loader.verify_isolation(final['isolation']['file'])
m.need(isolation==final['isolation'],'current cost namespace differs')
custody=m.preparation_process(prep['process'],lane['evidenceRetention']['originalArgv'][1],prep['plan'],prep['identity'],prep['custody']['process']['sha256'])
m.need(custody==prep['custody']==final['preparation'],'current cost preparation differs')
driver=loader.load_driver(lane['evidenceRetention']['originalArgv'][1])
record=m.admit(json.loads(Path(prep['plan']).read_bytes()),driver,prep['identity'])
print(json.dumps({'status':'CURRENT','isolation':isolation,'preparation':custody,
                  'originalFiles':len(record['baseFiles']),'derivedFiles':len(record['files'])}))
'''
    env=dict(os.environ);env.pop('PYTHONPATH',None);env.pop('PYTHONSTARTUP',None)
    try:
        process=subprocess.run([sys.executable,'-B','-c',script,str(HERE)],cwd=HERE,env=env,
            input=json.dumps({'lane':lane,'final':final},allow_nan=False),capture_output=True,text=True,timeout=90)
        return {'returncode':process.returncode,'timedOut':False,'stdout':process.stdout,'stderr':process.stderr}
    except subprocess.TimeoutExpired as error:
        def stream(value):return value.decode('utf-8',errors='replace') if isinstance(value,bytes) else value
        return {'returncode':None,'timedOut':True,'stdout':stream(error.stdout),'stderr':stream(error.stderr)}
    except OSError as error:
        return {'returncode':None,'timedOut':False,'stdout':'','stderr':str(error)}


def r0035_stage_status(lane, returncode, timed_out):
    """Supplemental custody cannot replace an original qualification or exit."""
    costs=cost_lane(lane);material=cost_material if costs else stage_material
    inspector=inspect_cost_trace if costs else inspect_stage_trace
    wrapper_sha=R0035_COST_WRAPPER_SHA256 if costs else R0035_STAGE_WRAPPER_SHA256
    result = {'status': 'INCOMPLETE', 'timingClass': cost_material.TIMING if costs else 'instrumented-stage-observation',
              'nativeQualification': 'UNCHANGED_ORIGINAL_REPORT_ONLY', 'humanAcceptance': 'OUTSTANDING'}
    need = stage_material.need
    def read(path, expected=None):
        path = Path(path).absolute()
        need(path.is_file() and not any(p.is_symlink() for p in (path,*path.parents)), 'regular stage evidence required')
        raw = path.read_bytes(); sha = hashlib.sha256(raw).hexdigest()
        need(expected is None or expected == sha, 'stage evidence digest mismatch')
        return json.loads(raw), {'path': str(path), 'sha256': sha}
    try:
        final, receipt = read(lane['result']['stageDriverPath']); result['receipt'] = receipt
        preparation = lane['preparation']; evidence = Path(lane['evidenceRetention']['output'])
        original = lane['evidenceRetention']['originalArgv']; custody = preparation['custody']
        need(returncode == 0 and not timed_out, 'stage child did not complete normally')
        if costs: need(type(returncode) is int and timed_out is False, 'cost child completion must be explicit')
        need(final.get('protocol') == ('r0035-cost-driver/1' if costs else 'r0035-stage-driver/1') and final.get('status') == 'OBSERVED'
             and type(final.get('trials')) is int and final['trials'] == lane['result']['expectedRows']
             and final.get('observationErrors') == [] and final.get('originalException') is None
             and final.get('continuationVetoed') is False and final.get('originalArgv') == original[2:]
             and final.get('timingClass') == result['timingClass']
             and final.get('nativeQualification') == result['nativeQualification']
             and final.get('wrapperSha256') == wrapper_sha
             and final.get('identitySha256') == custody['identitySha256'] and final.get('preparation') == custody,
             'stage driver receipt is incomplete or has different custody')
        read(preparation['process'], custody['process']['sha256'])
        plan, _ = read(preparation['plan'], custody['planSha256'])
        identity,_=read(preparation['identity'], custody['identitySha256'])
        if costs:
            need(final.get('baseWrapperSha256')==COST_BASE_WRAPPER_SHA256 and final.get('collectorSha256')==cost_material.HELPER_SHA256,
                 'cost host or collector identity differs')
        isolation_path = Path(lane['output']).parents[1]/'isolation'/lane['id']/'receipt.json'
        isolation, isolation_receipt = read(isolation_path)
        need(final.get('isolation') == {'file': str(isolation_path), 'sha256': isolation_receipt['sha256']}
             and isolation.get('protocol') == 'salah-hosted-native-isolation/1' and isolation.get('passed') is True
             and isolation.get('browserControl', {}).get('passed') is True, 'stage current isolation receipt is missing')
        wanted = {name: stage_material.pins()['files']['tools/r0035/'+name]['sha256']
                  for name in ('native_trials.py','trial_admission.py','trial_clock.js')}
        need(final.get('sources') == [{'name': 'tools/r0035/'+name,
                'file': str(Path(original[1]).with_name(name)), 'sha256': sha} for name,sha in wanted.items()],
             'stage original driver/helper closure differs')
        summary, summary_receipt = read(lane['result']['path'])
        need(final.get('originalSummary') == summary_receipt, 'stage original summary is not bound')
        expected = lane['result']['expectedArms']
        rows = final.get('observations')
        need(isinstance(summary, list) and len(summary) == 3 and isinstance(rows, list) and len(rows) == 3
             and len({r.get('path') for r in rows if isinstance(r,dict)}) == 3,
             'stage selected trial population is missing or duplicated')
        wanted_paths = []
        summary_keys = ('arm','commit','clock','scene','motion','capture','observedProducerDuringTrial','qualification',
                        'p95FrameMs','p99FrameMs','maxFrameMs','framesOver50Ms','admitted')
        for ordinal, label in enumerate(expected,1):
            path = evidence/f'trial-{ordinal:03}-{label}.json'; wanted_paths.append(path)
            row = rows[ordinal-1]
            need(row.get('ordinal') == ordinal and row.get('arm') == label and row.get('path') == str(path),
                 'stage selected trial identity differs')
            trial, _ = read(path,row['sha256'])
            target = Path(lane['output'])/('01-'+label); report, report_receipt = read(target/'trial.json')
            need(trial.get('protocol') == ('r0035-cost-trial/1' if costs else 'r0035-stage-trial/1') and trial.get('ordinal') == ordinal and trial.get('arm') == label
                 and trial.get('timingClass') == result['timingClass'] and trial.get('contextClosed') is True
                 and trial.get('originalOutput') == str(target) and trial.get('originalReport') == report_receipt
                 and not trial.get('originalException') and not trial.get('continuationVeto'), 'stage original trial custody differs')
            need(summary[ordinal-1] == {key: report[key] for key in summary_keys}, 'original summary differs from original trial')
            need(report.get('arm') == label and report.get('scope') == material.KIND
                 and all(report.get(key) == plan['arms'][label][key] for key in ('root','commit'))
                 and report.get('flags') == plan['arms'][label]['flags'].lstrip('&')
                 and report.get('driverSha256') == wanted and report.get('engine') == lane['engine']
                 and report.get('capture') is False and report.get('scene') == 'dark'
                 and report.get('motion') == 'normal' and report.get('clock') == 'ordinary',
                 'stage original trial source or selected cell differs')
            need(trial.get('originalArguments',{}).get('plan') == preparation['plan']
                 and trial['originalArguments'].get('output') == lane['output']
                 and trial.get('originalMeasuredWindow') == {k:report['trace'][k] for k in ('start','end')},
                 'stage original arguments or measured window differ')
            observations = trial.get('observations')
            need(isinstance(observations,list) and len(observations) == 1, 'stage page population is incomplete')
            observed = observations[0]
            if label == 'main':
                need(observed == {'status':'NOT_APPLICABLE','trace':None}, 'main has unexpected stage instrumentation')
            else:
                need(observed.get('status') == 'OBSERVED' and same_json(observed.get('intervals'),inspector(observed.get('trace'))),
                     'stage raw trace validation is incomplete')
        need(set(evidence.glob('trial-*.json')) == set(wanted_paths), 'stage evidence population has extra or missing members')
        if costs:
            result['currentSourceCheck']=_r0035_cost_current_check(lane,final)
            check=result['currentSourceCheck']
            need(type(check['returncode']) is int and check['returncode']==0 and check['timedOut'] is False,
                 'current cost source, preparation or namespace did not re-admit')
            need(same_json(json.loads(check['stdout']),{'status':'CURRENT','isolation':final['isolation'],'preparation':custody,
                'originalFiles':len(identity['baseFiles']),'derivedFiles':len(identity['files'])}), 'current cost receipt differs')
        result['status'] = 'OBSERVED'
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        result['reason'] = str(error)
    return result


def matrix_result(lane, body, returncode, timed_out):
    result={'status':'INCOMPLETE','stopAll':False,'nativeQualification':'NOT_EVALUATED','humanAcceptance':'OUTSTANDING'}
    if returncode in (3,86) or isinstance(body,dict) and (body.get('network',{}).get('ok') is False or body.get('status')=='ISOLATION FAIL'):
        return {**result,'status':'ISOLATION_FAIL','stopAll':True}
    if returncode==4 or isinstance(body,dict) and body.get('status')=='ANDON':return {**result,'status':'ANDON'}
    if returncode!=0 or timed_out or not isinstance(body,dict) or lane.get('preparation',{}).get('status')!='PASS':return result
    folder=Path(lane['output']).with_name(Path(lane['output']).name+'-intake')
    try:
        folder.mkdir(mode=0o700)
        admission=lane['preparation'];original=lane['matrixObservation']['originalArgv']
        request={'python':admission['python'],'node':original[0],'root':admission['root'],'pinsSha256':MATRIX_PINS,
                 'preparationEntry':admission['entry']['path'],'driverReceipt':lane['result']['driverPath'],
                 'originalArgv':original,'selection':lane['result']['selection'],'file':lane['result']['path'],
                 'materialization':matrix.MATERIALIZATION,'pngjs':str(Path(lane['env']['NODE_PATH'])/'pngjs'),'output':str(folder)}
        matrix.save(folder/'request.json',request)
        command=[original[0],str(HERE/'r003f_matrix_intake.cjs'),'--request',str(folder/'request.json')]
        process=run_bounded(command,str(HERE),dict(os.environ,NODE_PATH=lane['env']['NODE_PATH']),folder/'stdout',folder/'stderr',lane['postCaptureCheckSeconds'])
        matrix.save(folder/'process.json',{**process,'argv':command,'cwd':str(HERE)})
        result['intakeProcess']=process
        if process['returncode']==86:return {**result,'status':'ISOLATION_FAIL','stopAll':True}
        matrix.success(process,'matrix final intake')
        checked=json.loads((folder/'stdout').read_bytes());result['matrixIntake']=checked
        full=request['selection']['variant']=='all'
        status='VERIFIED_MATRIX_CAPTURE' if full else 'ADMITTED_MATRIX_DIAGNOSTIC'
        qualification='ORIGINAL_COMPLETE_EIGHT_REPLAY_ONLY' if full else 'NOT_EVALUATED'
        selection=request['selection']
        control=matrix.matrix_controls({k:selection[k] for k in ('id','variant')},'corrected-matrix',['R003F'],selection['engine'],selection['dpr'])
        if (checked.get('protocol')!='R003F/matrix-intake/1' or checked.get('status')!=status
                or checked.get('nativeAcceptance')!=qualification or checked.get('humanAcceptance')!='OUTSTANDING'
                or checked.get('summary')!=matrix.record(lane['result']['path'])
                or checked.get('driver')!=matrix.record(lane['result']['driverPath']) or checked.get('noVariantUnion') is not True
                or checked.get('originalStatus')!=('ACQUIRED' if full else 'DIAGNOSTIC')
                or not same_json(checked.get('sourceAdmission'),{**admission,'matrix':control})
                or checked.get('isolation')!=matrix.record(os.environ['SALAH_HOSTED_NATIVE_ISOLATION_RECEIPT'])):
            raise ValueError('matrix actual intake result or original report binding differs')
        result.update(status=status,nativeQualification=qualification)
    except (OSError,ValueError,KeyError,TypeError,subprocess.SubprocessError) as error:result['reason']=str(error)
    return result


def classify_lane(lane, returncode, timed_out=False):
    kind = lane['result']['kind']
    if diagnostics.mode_for_lane(lane):
        try:body=diagnostics.load(lane['result']['path'])
        except (OSError,ValueError):body=None
        return {'returncode':returncode,'timedOut':timed_out,
                **diagnostics.classify(lane,body,returncode,timed_out)}
    if kind == 'r002f-tabhide':
        try: body=json.loads(Path(lane['result']['path']).read_text())
        except (OSError,ValueError): body=None
        return r002f_tabhide_status(body,lane,returncode,timed_out)
    result = {'status': 'INCOMPLETE', 'stopAll': False, 'returncode': returncode, 'timedOut': timed_out}
    if 'evidenceRetention' in lane:
        result['evidenceRetention'] = lane['evidenceRetention']
    if returncode == 86 and retained_lane(lane):
        return {**result, 'status': VETO_STATUS, 'stopAll': True, 'reason': VETO_REASON}
    if returncode == ISOLATION_EXIT or kind in ('r003f-b0','r003f-matrix') and returncode == 3:
        return {**result, 'status': 'ISOLATION_FAIL', 'stopAll': True}
    if kind == 'r0035-trials' and psf_lane(lane):
        original=classify_lane({k:v for k,v in lane.items() if k!='psfObservation'},returncode,timed_out)
        supplemental=psf.post_observation(lane,returncode,timed_out)
        status=original['status']
        if status=='PASS':
            status=psf.OBSERVED if (type(returncode) is int and returncode==0 and timed_out is False
                and supplemental.get('status')=='COMPLETE'
                and supplemental.get('intake',{}).get('originalStatus')=='PASS') else 'INCOMPLETE'
        return {**original,'status':status,'originalStatus':original['status'],'psfObservation':supplemental,
                'timingClass':psf.TIMING,'nativeQualification':'UNCHANGED_ORIGINAL_REPORT_ONLY','humanAcceptance':'OUTSTANDING'}
    if kind == 'r0035-trials' and 'stageObservation' in lane:
        original = classify_lane({k:v for k,v in lane.items() if k != 'stageObservation'}, returncode, timed_out)
        supplemental = r0035_stage_status(lane,returncode,timed_out)
        status = original['status']
        if status == 'PASS': status = (COSTS_OBSERVED if cost_lane(lane) else STAGES_OBSERVED) if supplemental['status'] == 'OBSERVED' else 'INCOMPLETE'
        return {**original, 'status': status, 'originalStatus': original['status'], 'stageObservation': supplemental,
                'timingClass': cost_material.TIMING if cost_lane(lane) else 'instrumented-stage-observation', 'nativeQualification': 'UNCHANGED_ORIGINAL_REPORT_ONLY'}
    try: body = json.loads(Path(lane['result']['path']).read_text())
    except (OSError, ValueError): body = None
    if kind == 'r003f-matrix':
        return {**result,**matrix_result(lane,body,returncode,timed_out)}
    if kind == 'r002f-probe':
        return {**result, 'status': r002f_report_status(body, lane, returncode, timed_out)}
    if kind == 'r0040-capture':
        return {**result, **r0040_capture_status(body, lane, returncode, timed_out)}
    if kind == 'r0040-capture-dateonly':
        return {**result, **r0040_dateonly_status(body, lane, returncode, timed_out)}
    if kind == passive.KIND:
        return {**result, **r0040_passive_status(body, lane, returncode, timed_out)}
    # Preserve observed recipe failures even if later acquisition is interrupted.
    # Return codes alone do not distinguish failed admission from missing evidence.
    if kind == 'r003f-b0':
        if isinstance(body, dict) and (body.get('isolation', {}).get('ok') is False
                                      or body.get('status') == 'ISOLATION FAIL'):
            return {**result, 'status': 'ISOLATION_FAIL', 'stopAll': True}
        if returncode == 4 or isinstance(body, dict) and body.get('status') == 'FAIL (Andon)':
            return {**result, 'status': 'ANDON'}
    elif kind == 'r0035-trials' and isinstance(body, list):
        if any(isinstance(row, dict) and row.get('qualification', {}).get('verdict') == 'failed' for row in body):
            return {**result, 'status': 'FAIL'}
    if timed_out: return result
    defaults = {'r003f-b0': {'1': 'FAIL', '2': 'INCOMPLETE'},
                'r0040-options': {'1': 'FAIL'}, 'r0035-trials': {'1': 'INCOMPLETE'},
                'r002f-probe': {'1': 'FAIL', '2': 'INCOMPLETE'}}
    declared = lane.get('exitStatuses', defaults.get(kind, {})).get(str(returncode))
    if body is None:
        return {**result, 'status': 'FAIL' if declared == 'FAIL' else 'INCOMPLETE'}
    if kind == 'r003f-b0':
        passed = (isinstance(body, dict) and body.get('status') == 'MEASURED'
                  and body.get('isolation', {}).get('ok') is True)
        if 'expectedHarness' in lane['result']:
            def complete_ui(receipt):
                return (isinstance(receipt, dict) and receipt.get('protocol') == 'R003F/native-ui/1'
                        and receipt.get('status') == 'PASS' and receipt.get('failures') == []
                        and isinstance(receipt.get('observed'), dict) and bool(receipt['observed']))
            captures = body.get('captures') if isinstance(body, dict) else None
            passed = (passed and body.get('protocol') == 'R003F/P1/B0-owner/2'
                      and body.get('engine') == lane['engine'] and type(body.get('dpr')) is int
                      and body['dpr'] == lane['dpr'] and body.get('harness') == lane['result']['expectedHarness']
                      and body.get('indexSha256') == lane['result']['expectedIndexSha256']
                      and isinstance(captures, dict) and set(captures) == set(lane['result']['expectedCaptures'])
                      and all(isinstance(row, dict) and isinstance(row.get('state'), dict)
                              and complete_ui(row['state'].get('nativeUi')) and complete_ui(row.get('nativeUiAfter'))
                              for row in captures.values()))
    elif kind == 'r0040-options':
        cells = body.get('cells', []) if isinstance(body, dict) else []
        passed = (isinstance(cells, list) and len(cells) == len(RAIN_CELLS)
                  and all(isinstance(c, dict) for c in cells)
                  and sorted(c.get('id', '') for c in cells) == sorted(RAIN_CELLS))
    elif kind == 'r0035-trials':
        expected_rows = lane['result'].get('expectedRows', 3)
        expected_arms = lane['result'].get('expectedArms', ['main', 'unmodified', 'mitigated'])
        passed = (isinstance(body, list) and len(body) == expected_rows and expected_rows > 0
                  and all(isinstance(row, dict) for row in body)
                  and expected_rows % len(expected_arms) == 0
                  and sorted(r.get('arm', '') for r in body) == sorted(expected_arms * (expected_rows // len(expected_arms))))
        passed = passed and all(r.get('admitted') is True and r.get('qualification', {}).get('verdict') == 'passed'
                                for r in body)
    else:
        raise ValueError('unknown recipe result kind')
    result['status'] = 'PASS' if returncode == 0 and passed else ('FAIL' if declared == 'FAIL' else 'INCOMPLETE')
    return result


def namespace_status(lane, process, inner):
    """An inner observation cannot overrule abnormal wrapper completion."""
    outer_admitted = (isinstance(process, dict) and type(process.get('returncode')) is int
                      and type(process.get('timedOut')) is bool)
    admitted = (isinstance(inner, dict) and inner.get('id') == lane['id']
                and inner.get('status') in (psf.OBSERVED, 'PASS', 'FAIL', 'INCOMPLETE', 'INCONCLUSIVE', 'ANDON', 'ISOLATION_FAIL', VETO_STATUS, CAPTURE_ADMITTED, R0040_DATEONLY_ADMITTED, passive.ADMITTED, STAGES_OBSERVED, COSTS_OBSERVED, TABHIDE_OBSERVED, 'ADMITTED_MATRIX_DIAGNOSTIC','VERIFIED_MATRIX_CAPTURE', *[r['status'] for r in diagnostics.ROUTES.values()])
                and isinstance(inner.get('stopAll'), bool))
    if admitted:
        admitted = inner['stopAll'] == (inner['status'] in ('ISOLATION_FAIL', VETO_STATUS))
    if admitted:
        admitted=diagnostics.namespace_admitted(lane,inner)
    if admitted and inner['status'] == VETO_STATUS:
        admitted = retained_lane(lane) and inner.get('returncode') == 86 and inner['stopAll'] is True
    if admitted and inner['status'] == CAPTURE_ADMITTED:
        admitted = (lane.get('result', {}).get('kind') == 'r0040-capture' and type(inner.get('returncode')) is int and inner['returncode'] == 0
                    and inner.get('timedOut') is False and inner.get('nativeQualification') == 'NOT_VERIFIED')
    if admitted and inner['status'] == R0040_DATEONLY_ADMITTED:
        admitted = (lane.get('result', {}).get('kind') == 'r0040-capture-dateonly'
                    and type(inner.get('returncode')) is int and inner['returncode'] == 0 and inner.get('timedOut') is False
                    and inner.get('nativeQualification') == 'NOT_VERIFIED' and inner.get('humanAcceptance') == 'OUTSTANDING'
                    and inner.get('timingClass') == 'instrumented-date-only-clock'
                    and same_json(inner.get('diagnostic'), r0040_dateonly_identity()))
    if admitted and inner['status'] == passive.ADMITTED:
        admitted = (lane.get('result', {}).get('kind') == passive.KIND
                    and type(inner.get('returncode')) is int and inner['returncode'] == 0 and inner.get('timedOut') is False
                    and inner.get('nativeQualification') == 'NOT_VERIFIED' and inner.get('humanAcceptance') == 'OUTSTANDING'
                    and inner.get('timingClass') == passive.TIMING and inner.get('dateOnlyStatus') == R0040_DATEONLY_ADMITTED
                    and same_json(inner.get('diagnostic'), r0040_dateonly_identity())
                    and same_json(inner.get('passiveDiagnostic'), lane.get('result', {}).get('passiveDiagnostic'))
                    and inner.get('passiveDiagnostic', {}).get('entrySha256') == passive.ENTRY_SHA256
                    and type(inner.get('passiveVerification', {}).get('returncode')) is int
                    and inner['passiveVerification']['returncode'] == 0 and inner['passiveVerification'].get('timedOut') is False
                    and inner.get('passiveInspection', {}).get('status') == 'OBSERVED')
    if admitted and lane.get('result', {}).get('kind') in ('r0040-capture', 'r0040-capture-dateonly', passive.KIND) and inner['status'] == 'PASS':
        admitted = False  # This lane can admit acquisition, never report a cadence PASS.
    if admitted and inner['status'] in (STAGES_OBSERVED,COSTS_OBSERVED):
        admitted = ('stageObservation' in lane and inner.get('returncode') == 0 and inner.get('timedOut') is False
                    and (inner['status']==COSTS_OBSERVED)==cost_lane(lane)
                    and (not cost_lane(lane) or type(inner.get('returncode')) is int)
                    and inner.get('originalStatus') == 'PASS' and inner.get('stageObservation',{}).get('status') == 'OBSERVED'
                    and inner.get('timingClass') == (cost_material.TIMING if cost_lane(lane) else 'instrumented-stage-observation')
                    and inner.get('nativeQualification') == 'UNCHANGED_ORIGINAL_REPORT_ONLY')
    if admitted and 'stageObservation' in lane and inner['status'] == 'PASS': admitted = False
    if admitted and inner['status']==psf.OBSERVED:
        intake=inner.get('psfObservation',{}).get('intake',{})
        admitted=(psf_lane(lane) and type(inner.get('returncode')) is int and inner['returncode']==0
                  and inner.get('timedOut') is False and inner.get('originalStatus')=='PASS'
                  and inner.get('psfObservation',{}).get('status')=='COMPLETE' and intake.get('status')=='COMPLETE'
                  and intake.get('role')==lane['psfObservation']['role'] and intake.get('originalStatus')=='PASS'
                  and same_json(intake.get('sourceAdmission'),lane.get('preparation'))
                  and inner.get('timingClass')==psf.TIMING
                  and inner.get('nativeQualification')=='UNCHANGED_ORIGINAL_REPORT_ONLY'
                  and inner.get('humanAcceptance')=='OUTSTANDING')
    if admitted and psf_lane(lane) and inner['status']=='PASS':admitted=False
    if admitted and inner['status'] == TABHIDE_OBSERVED:
        admitted = (lane.get('result',{}).get('kind') == 'r002f-tabhide' and type(inner.get('returncode')) is int
                    and inner['returncode'] == 0 and inner.get('timedOut') is False
                    and inner.get('nativeQualification') == 'LIFECYCLE_OBSERVATION_ONLY')
    if admitted and lane.get('result',{}).get('kind') == 'r002f-tabhide' and inner['status'] == 'PASS': admitted=False
    if admitted and inner['status'] in ('ADMITTED_MATRIX_DIAGNOSTIC','VERIFIED_MATRIX_CAPTURE'):
        admitted = lane.get('result',{}).get('kind') == 'r003f-matrix'
    if admitted and lane.get('result',{}).get('kind')=='r003f-matrix':
        if inner['status']=='PASS':admitted=False
        if inner['status'] in ('ADMITTED_MATRIX_DIAGNOSTIC','VERIFIED_MATRIX_CAPTURE'):
            full=lane['result']['selection']['variant']=='all'
            admitted=(inner['status']==('VERIFIED_MATRIX_CAPTURE' if full else 'ADMITTED_MATRIX_DIAGNOSTIC')
                      and type(inner.get('returncode')) is int and inner['returncode']==0 and inner.get('timedOut') is False
                      and inner.get('humanAcceptance')=='OUTSTANDING'
                      and inner.get('nativeQualification')==('ORIGINAL_COMPLETE_EIGHT_REPLAY_ONLY' if full else 'NOT_EVALUATED'))
    result = {**(inner if admitted else {}), 'id': lane['id'],
              'innerStatus': inner, 'namespaceProcess': process}
    if outer_admitted and process['returncode'] == ISOLATION_EXIT or admitted and inner['status'] == 'ISOLATION_FAIL':
        result.update(status='ISOLATION_FAIL', stopAll=True, reason='namespace boundary reported isolation failure')
    elif not outer_admitted or process['returncode'] != 0 or process['timedOut'] or not admitted:
        result.update(status='ISOLATION_UNCONFIRMED', stopAll=True,
                      reason='namespace completion or inner admission receipt is unconfirmed')
    return result


def controls(args, runtime, label):
    folder = args.task/'capture'/'isolation'/label
    folder.mkdir(parents=True, exist_ok=False)
    receipt = {'protocol': 'salah-hosted-native-isolation/1', 'passed': False,
               'outerNetns': args.outer_netns, 'uid': os.getuid()}
    try:
        snapshot = kernel_snapshot(); receipt['kernel'] = snapshot; receipt['netns'] = snapshot['netns']
        validate_snapshot(snapshot, args.outer_netns)
        env = dict(os.environ)
        env['PLAYWRIGHT_BROWSERS_PATH'] = str(args.task/'node-browsers')
        command = [runtime['node'], str(HERE/'browser-control.cjs'), runtime['playwright'], str(folder/'browser.json')]
        result = run_bounded(command, str(HERE), env, folder/'browser.stdout', folder/'browser.stderr', 45)
        receipt['browserProcess'] = result
        if result['returncode'] or result['timedOut']: raise ValueError('real browser boundary control failed')
        browser = json.loads((folder/'browser.json').read_text())
        if browser.get('passed') is not True: raise ValueError('real browser boundary control incomplete')
        receipt['browserControl'] = browser
        # Recheck the namespace after running the real browser, before any recipe.
        validate_snapshot(kernel_snapshot(), args.outer_netns)
        receipt['passed'] = True
    except Exception as exc:
        receipt['error'] = str(exc)
    path = folder/'receipt.json'; write_json(path, receipt)
    if not receipt['passed']: return None
    return str(path)


def prepare_stages(args, runtime, destination):
    """Optional child failure remains private evidence and blocks only its lane."""
    costs=cost_campaign(args)
    folder = args.task/'capture'/('r0035-cost-preparation' if costs else 'r0035-stage-preparation'); folder.mkdir(mode=0o700)
    derived = args.task/'work'/('r0035-costs' if costs else 'r0035-stages')
    materializer='r0035_cost_materialize.py' if costs else 'r0035_stage_materialize.py'
    driver = args.research/'tools/r0035/native_trials.py'
    command = [runtime['python'], str(HERE/materializer), '--driver', str(driver),
               '--plan', str(folder/'source-plan.json'), '--out', str(derived),
               '--receipt', str(folder/'identity.json'), '--plan-out', str(folder/'plan.json')]
    try:
        prepared_path = destination/'receipts/prepared.json'
        prepared = json.loads(prepared_path.read_text())
        shutil.copy2(prepared_path, folder/'original-prepared.json')
        shutil.copy2(args.task/'capture/preparation-process.json', folder/'original-preparation-process.json')
        shutil.copy2(Path(prepared['trees']['r0035']['root'])/'r0035-lab-identity.json', folder/'original-lab-identity.json')
        stars = star_campaign(args)
        write_json(folder/'source-plan.json', original_star_plan(prepared, stars['guard'], stars['scope']))
        optional = run_bounded(command, str(HERE), dict(os.environ), folder/'stdout', folder/'stderr', 240)
    except (OSError, ValueError, KeyError, TypeError) as error:
        optional = {'returncode': None, 'timedOut': False, 'error': str(error)}
    record = {**optional, 'protocol': 'r0035-cost-preparation-process/1' if costs else 'r0035-stage-preparation-process/1', 'argv': command,
              'cwd': str(HERE), 'timeoutSeconds': 240, 'root': str(derived),
              'materializerSha256': digest(HERE/materializer)}
    if costs:
        record.update(collectorSha256=cost_material.HELPER_SHA256,stageMaterializerSha256=cost_material.STAGE_MATERIALIZER_SHA256)
    for key, path in {'driver': driver, 'sourcePlan': folder/'source-plan.json',
                      'originalPreparation': folder/'original-prepared.json',
                      'originalPreparationProcess': folder/'original-preparation-process.json',
                      'originalLabIdentity': folder/'original-lab-identity.json',
                      'identity': folder/'identity.json', 'plan': folder/'plan.json'}.items():
        try:
            if path.is_file() and not path.is_symlink():
                record[key] = {'path': str(path), 'sha256': digest(path)}
        except OSError as error:
            record['retentionError'] = str(error)
    write_json(folder/'process.json', record)
    return record


def prepare_psf(args,runtime):
    command=psf.prepare_argv(args.task,runtime)
    child=run_bounded(command,str(HERE),dict(os.environ),args.task/'capture/r0035-psf-preparation.stdout',
                      args.task/'capture/r0035-psf-preparation.stderr',240)
    return psf.preparation_entry(args.task,runtime,child)


def prepare_matrix(args,runtime,destination):
    folder=args.task/'capture/r003f-matrix-preparation'
    inputs={'prepared':str(destination/'receipts/prepared.json'),'common-process':str(args.task/'capture/preparation-process.json'),
            'common-context':str(args.task/'capture/preparation-context.json'),'out':str(args.task/'work/r003f-matrix'),
            'receipts':str(folder),'node':runtime['node'],'pins-sha256':MATRIX_PINS}
    command=matrix.prepare_argv(runtime['python'],inputs)
    try:
        result=run_bounded(command,str(HERE),dict(os.environ),args.task/'capture/r003f-matrix-preparation.stdout',args.task/'capture/r003f-matrix-preparation.stderr',180)
    except (OSError,ValueError) as error:result={'returncode':None,'timedOut':False,'error':str(error)}
    try:
        manifest=Path(inputs['out'])/'materialization.json'
        if manifest.is_file():shutil.copy2(manifest,folder/'materialization.json')
    except OSError as error:result['retentionError']=str(error)
    matrix.save(args.task/'capture/r003f-matrix-preparation-entry.json',{**result,'protocol':matrix.ENTRY_PROTOCOL,
               'argv':command,'cwd':str(HERE),'timeoutSeconds':180,'process':str(folder/'process.json')})


def prepare_diagnostic(args,runtime):
    mode=diagnostic_campaign(args)['mode'];p=diagnostics.paths(args.task,mode)
    command=diagnostics.preparation_argv(mode,args.task,runtime)
    try:
        result=run_bounded(command,str(HERE),dict(os.environ),
            args.task/'capture/r003f-diagnostic-preparation.stdout',
            args.task/'capture/r003f-diagnostic-preparation.stderr',180)
    except (OSError,ValueError) as error:result={'returncode':None,'timedOut':False,'error':str(error)}
    diagnostics.save(p['preparationEntry'],{**result,'protocol':diagnostics.PREPARATION_ENTRY,
        'argv':command,'cwd':str(HERE),'timeoutSeconds':180,'sourceSha256':digest(HERE/'r003f_diagnostics.py'),
        'process':str(p['preparationProcess'])})


def inside(args, runtime):
    selected = campaign_selection(args)
    label = args.lane or 'preparation'
    receipt = controls(args, runtime, label)
    if not receipt: return ISOLATION_EXIT
    os.environ['SALAH_HOSTED_NATIVE_ISOLATION_RECEIPT'] = receipt
    if args.phase == 'prepare':
        destination = args.task/'work'/'prepared'
        command = [runtime['python'], str(HERE/'prepare.py'), '--research', str(args.research),
                   '--baseline', str(args.baseline), '--historical', str(args.historical), '--out', str(destination)]
        result = run_bounded(command, str(HERE), dict(os.environ),
                             args.task/'capture'/'preparation.stdout', args.task/'capture'/'preparation.stderr', 900)
        # Source bodies are public and reproducible; seal only private receipts/logs.
        if (destination/'receipts').exists():
            shutil.copytree(destination/'receipts', args.task/'capture'/'preparation')
        write_json(args.task/'capture'/'preparation-process.json', result)
        if matrix_campaign(args) or diagnostic_campaign(args) or psf_campaign(args):
            matrix.save(args.task/'capture/preparation-context.json',{'protocol':'hosted-common-preparation-execution/1',
                'argv':command,'cwd':str(HERE),'timeoutSeconds':900,'sourceSha256':digest(HERE/'prepare.py'),
                'nativeIsolationClaim':True,'isolation':matrix.record(receipt)})
        if result['returncode'] or result['timedOut']: return 2
        if matrix_campaign(args):prepare_matrix(args,runtime,destination)
        if diagnostic_campaign(args):prepare_diagnostic(args,runtime)
        if psf_campaign(args):prepare_psf(args,runtime)
        if stage_campaign(args):
            prepare_stages(args, runtime, destination)
        r0040_destination = args.task/'work'/'r0040-capture'
        if rain_campaign(args) in R0040_CAPTURE_MODES:
            command = [runtime['python'], str(HERE/'r0040_capture_prepare.py'), '--manifest', str(R0040_MANIFEST),
                       '--research', str(args.research), '--historical', str(args.historical),
                       '--main', str(destination/'trees/main'), '--out', str(r0040_destination),
                       '--receipts', str(args.task/'capture/r0040-preparation')]
            try:
                optional = run_bounded(command, str(HERE), dict(os.environ),
                                       args.task/'capture/r0040-preparation.stdout',
                                       args.task/'capture/r0040-preparation.stderr', 240)
            except (OSError, ValueError) as error:
                optional = {'returncode': None, 'timedOut': False, 'error': str(error)}
            # Original recipe receipts are retained even when only one patch
            # completed. Its disposable source remains outside capture.
            try:
                if (r0040_destination/'receipts').exists():
                    shutil.copytree(r0040_destination/'receipts', args.task/'capture/r0040-preparation-original')
            except OSError as error:
                optional['retentionError'] = str(error)
            write_json(args.task/'capture/r0040-preparation-entry.json',
                       {**optional, 'protocol': 'r0040-capture-preparation-entry/1', 'argv': command,
                        'cwd': str(HERE), 'timeoutSeconds': 240, 'wrapperSha256': digest(HERE/'r0040_capture_prepare.py')})
        r003f_destination = args.task/'work'/'r003f-corrected'
        if moon_campaign(args) == 'corrected-b0':
            command = [runtime['node'], str(HERE/'r003f_materialize.cjs'), '--source', str(args.research),
                       '--out', str(r003f_destination)]
            try:
                optional = run_bounded(command, str(HERE), dict(os.environ),
                                       args.task/'capture'/'r003f-preparation.stdout',
                                       args.task/'capture'/'r003f-preparation.stderr', 60)
            except (OSError, ValueError) as error:
                optional = {'returncode': None, 'timedOut': False, 'error': str(error)}
            write_json(args.task/'capture'/'r003f-preparation-process.json',
                       {**optional, 'argv': command, 'cwd': str(HERE), 'timeoutSeconds': 60})
            materialization = r003f_destination/'materialization.json'
            if materialization.is_file() and not materialization.is_symlink():
                shutil.copy2(materialization, args.task/'capture'/'r003f-materialization.json')
        r002f_destination = args.task/'work'/'r002f-prepared'
        if getattr(args, 'r002f', False):
            command = [runtime['python'], str(HERE/'r002f_prepare.py'), '--research', str(args.research),
                       '--baseline', str(args.baseline), '--out', str(r002f_destination), '--node', runtime['node']]
            try:
                optional = run_bounded(command, str(HERE), dict(os.environ),
                                       args.task/'capture'/'r002f-preparation.stdout',
                                       args.task/'capture'/'r002f-preparation.stderr', 900)
            except (OSError, ValueError) as error:
                optional = {'returncode': None, 'timedOut': False, 'error': str(error)}
            write_json(args.task/'capture'/'r002f-preparation-process.json',
                       {**optional, 'argv': command, 'cwd': str(HERE), 'timeoutSeconds': 900})
            # The wrapper writes only receipts/logs at its root. Its source arms
            # and materialized patch stay outside the encrypted evidence capture.
            retained = args.task/'capture'/'r002f-preparation'
            retained.mkdir(mode=0o700)
            if r002f_destination.exists():
                for path in sorted(r002f_destination.iterdir()):
                    if path.is_file() and not path.is_symlink() and path.suffix in ('.json', '.stdout', '.stderr'):
                        shutil.copy2(path, retained/path.name)
            # Failed optional preparation is interpreted by the planner as a
            # blocked R002F lane; it cannot erase the already prepared recipes.
        command = [runtime['python'], str(HERE/'lanes.py'), '--plan-json', '--prepared',
                   str(destination/'receipts'/'prepared.json'), '--out', str(args.task/'capture'/'lanes'),
                   '--python-playwright', runtime['python'], '--node', runtime['node'],
                   '--node-modules', runtime['modules'], '--pngjs', runtime['pngjs'], '--engine', args.engine,
                   '--r003f-dpr', str(getattr(args, 'r003f_dpr', 1)), '--work-orders', *selected]
        command += star_arguments(args)
        if stage_campaign(args):
            folder=args.task/'capture'/('r0035-cost-preparation' if cost_campaign(args) else 'r0035-stage-preparation')
            command += ['--r0035-stages', '--r0035-stage-process', str(folder/'process.json')]
        if cost_campaign(args): command.append('--r0035-costs')
        if psf_campaign(args): command.append('--r0035-psf')
        command += ['--r003f-harness', moon_campaign(args)]
        if matrix_campaign(args):command += ['--r003f-matrix',json.dumps(args.r003f_matrix),'--r003f-matrix-entry',str(args.task/'capture/r003f-matrix-preparation-entry.json')]
        command += ['--r0040-mode', rain_campaign(args)]
        if rain_campaign(args) in R0040_CAPTURE_MODES:
            command += ['--r0040-work', str(r0040_destination),
                        '--r0040-process', str(args.task/'capture/r0040-preparation/process.json'),
                        '--r0040-entry-process', str(args.task/'capture/r0040-preparation-entry.json')]
        if moon_campaign(args) == 'corrected-b0':
            command += ['--r003f-prepared', str(r003f_destination/'materialization.json'),
                        '--r003f-process', str(args.task/'capture'/'r003f-preparation-process.json')]
        if getattr(args, 'retain_evidence', False):
            command.append('--retain-evidence')
        if getattr(args, 'r002f', False):
            command += ['--r002f', '--r002f-prepared', str(r002f_destination/'build-result.json'),
                        '--r002f-process', str(args.task/'capture'/'r002f-preparation-process.json'),
                        '--r002f-dpr', str(args.r002f_dpr), '--r002f-rounds', str(args.r002f_rounds),
                        '--r002f-section', args.r002f_section]
            if tabhide_campaign(args) == 'tabhide': command += ['--r002f-route','tabhide']
        plan = run_bounded(command, str(HERE), dict(os.environ), args.task/'capture'/'lanes.json',
                           args.task/'capture'/'plan.stderr', 120 if rain_campaign(args) in R0040_CAPTURE_MODES or stage_campaign(args) or matrix_campaign(args) or diagnostic_campaign(args) or psf_campaign(args) else 30)
        return 0 if plan['returncode'] == 0 and not plan['timedOut'] else 2
    plan = json.loads((args.task/'capture'/'lanes.json').read_text())
    try:lane = next(x for x in admit_plan(plan, args, runtime) if x['id'] == args.lane)
    except (OSError,ValueError,KeyError,TypeError,StopIteration) as error:
        if not psf_campaign(args):raise
        write_json(args.task/'capture/lane-status'/(args.lane+'.json'),
                   {'id':args.lane,'status':'INCOMPLETE','stopAll':False,'returncode':None,'timedOut':False,
                    'reason':'PSF actual current source admission failed: '+str(error),'nativeStatus':'NOT_RUN'})
        return 0
    env = dict(os.environ)
    # Recipe env is declarative data from the reviewed planner; arbitrary variables
    # cannot restore a credential/proxy/loader setting that the wrapper removed.
    for key, value in lane.get('env', {}).items():
        if key != 'NODE_PATH' and not (lane['result']['kind'] in ('r0040-capture', 'r0040-capture-dateonly', passive.KIND) and key == 'R0040_DISPERSION' and value == 'common'):
            raise ValueError('unapproved lane environment variable')
        env[key] = value
    for key in lane.get('clearEnv', []):
        if lane['result']['kind'] not in ('r0040-capture', 'r0040-capture-dateonly', passive.KIND) or key != 'R0040_OPTIONS':
            raise ValueError('unapproved cleared lane environment variable')
        env.pop(key, None)
    env['PLAYWRIGHT_BROWSERS_PATH'] = str(args.task/('python-browsers' if lane['result']['kind'] == 'r0035-trials' else 'node-browsers'))
    result = run_bounded(lane['argv'], lane['cwd'], env, lane['stdout'], lane['stderr'], lane['timeoutSeconds'])
    if diagnostics.mode_for_lane(lane):diagnostics.record_entry(lane,result)
    verdict = classify_lane(lane, result['returncode'], result['timedOut'])
    if diagnostics.mode_for_lane(lane):verdict['preExecutionCurrentness']=lane.get('preExecutionCurrentness')
    write_json(args.task/'capture'/'lane-status'/(args.lane+'.json'), {**result, **verdict, 'id': args.lane,
               **({'preExecutionCurrentness': lane['preExecutionCurrentness']} if 'preExecutionCurrentness' in lane else {})})
    # All in-namespace descendants are also killed when the namespace init exits.
    # A retained child veto is carried by its admitted receipt, including its
    # actual exit 86. Normal coordinator completion does not claim child success;
    # outer 86 remains reserved for an actual namespace/boundary failure.
    return ISOLATION_EXIT if verdict['stopAll'] and verdict['status'] != VETO_STATUS else 0


def isolated_command(args, runtime, phase, lane=None):
    selected = campaign_selection(args)
    env = clean_environment(runtime['node'], runtime['python'], args.task, args.task/'node-browsers',
                            runtime['modules'], args.baseline, args.research)
    inner = [runtime['python'], str(HERE/'observe.py'), '--task', str(args.task), '--research', str(args.research),
             '--baseline', str(args.baseline), '--historical', str(args.historical), '--engine', args.engine,
             '--r003f-dpr', str(getattr(args, 'r003f_dpr', 1)), '--work-orders', *selected,
             '--inside', '--phase', phase, '--outer-netns', os.readlink('/proc/self/ns/net')]
    inner += star_arguments(args)
    if stage_campaign(args): inner.append('--r0035-stages')
    if cost_campaign(args): inner.append('--r0035-costs')
    if psf_campaign(args): inner.append('--r0035-psf')
    inner += ['--r003f-harness', moon_campaign(args)]
    if matrix_campaign(args):inner += ['--r003f-matrix',json.dumps(args.r003f_matrix)]
    inner += ['--r0040-mode', rain_campaign(args)]
    if getattr(args, 'retain_evidence', False):
        inner.append('--retain-evidence')
    if getattr(args, 'r002f', False):
        inner += ['--r002f', '--r002f-dpr', str(args.r002f_dpr), '--r002f-rounds', str(args.r002f_rounds),
                  '--r002f-section', args.r002f_section]
        if tabhide_campaign(args) == 'tabhide': inner += ['--r002f-route','tabhide']
    if lane: inner += ['--lane', lane]
    return ['/usr/bin/sudo', '-n', '/usr/bin/unshare', '--net', '--pid', '--fork', '--mount-proc',
            '--kill-child=KILL', '/bin/bash', str(HERE/'namespace.sh'), str(os.getuid()), str(os.getgid()),
            *[k+'='+v for k, v in env.items()], *inner]


def outside(args, runtime):
    selected = campaign_selection(args)
    capture = args.task/'capture'
    parent_env = {'PATH': '/usr/sbin:/usr/bin:/sbin:/bin', 'LANG': 'C.UTF-8', 'LC_ALL': 'C.UTF-8'}
    budget = observation_budget(args)
    deadline = time.monotonic() + budget['coordinatorSeconds']  # leaves sealing/upload time within the selected step ceiling
    preparation = run_bounded(isolated_command(args, runtime, 'prepare'), str(HERE), parent_env,
                              capture/'namespace-preparation.stdout', capture/'namespace-preparation.stderr',
                              diagnostic_campaign(args)['budget']['preparationSeconds'] if diagnostic_campaign(args) else
                              psf.PREPARATION_SECONDS if psf_campaign(args) else
                              matrix_campaign(args)['budget']['preparationSeconds'] if matrix_campaign(args) else
                              (1920 if getattr(args, 'r002f', False) else 1020) + (330 if rain_campaign(args) in R0040_CAPTURE_MODES else 0)
                              + (240 if stage_campaign(args) else 0))
    overall = {'protocol': 'salah-hosted-native-observation/1', 'engine': args.engine,
               'workOrders': selected, 'evidenceRetention': getattr(args, 'retain_evidence', False),
               'r0035Controls': star_campaign(args),
               'r0035Stages': stage_campaign(args),
               **({'r0035Psf':True,'budget':budget} if psf_campaign(args) else {}),
               'r003fHarness': moon_campaign(args),
               **({'r003fMatrix':args.r003f_matrix} if matrix_campaign(args) else {}),
               'r0040Mode': rain_campaign(args),
               'preparation': preparation, 'lanes': [], 'status': 'INCOMPLETE'}
    if rain_campaign(args) == passive.MODE:
        overall['budget'] = budget
    if tabhide_campaign(args) == 'tabhide':
        overall.update(r002fRoute='tabhide', budget=budget)
    write_json(capture/'observation.json', overall)
    if preparation['returncode'] or preparation['timedOut']:
        overall['status'] = 'ISOLATION_FAIL' if preparation['returncode'] == ISOLATION_EXIT else 'INCOMPLETE'
        write_json(capture/'observation.json', overall); return 2
    plan = json.loads((capture/'lanes.json').read_text())
    try:lanes = admit_plan(plan, args, runtime)
    except ReturnedCurrentnessRefusal as error:
        # The dedicated type is emitted only after exact single-lane canonical
        # admission and retained actual child completion. No lane was launched.
        overall['lanes']=[{'id':error.lane['id'],'workOrder':error.lane['workOrder'],'status':'NOT_RUN',
                           'reason':str(error),'outerCurrentness':error.process,'currentnessReceipt':error.receipt}]
        overall['status']='OBSERVED_WITH_INCOMPLETE_OR_FAILED_LANES'
        write_json(capture/'observation.json',overall);return 2
    except (OSError,ValueError,KeyError,TypeError) as error:
        if not psf_campaign(args):raise
        overall['lanes']=[{'id':'r0035-chromium-psf-'+role,'workOrder':'R0035','status':'NOT_RUN',
                           'reason':'PSF outer current source admission failed: '+str(error)} for role in psf.ROLES]
        overall['psfPair']=psf.pair_status(plan,overall['lanes'])
        overall['status']='OBSERVED_WITH_INCOMPLETE_OR_FAILED_LANES'
        write_json(capture/'observation.json',overall);return 2
    stopped = set(); stop_all = False; stop_reason = None
    for lane in lanes:
        remaining = deadline - time.monotonic()
        if lane.get('preparation', {}).get('status', 'PASS') != 'PASS':
            status = {'id': lane['id'], 'status': 'NOT_RUN', 'preparationStatus': 'INCOMPLETE',
                      'reason': lane['preparation'].get('reason', 'lane preparation incomplete')}
        elif remaining <= 75:
            status = {'id': lane['id'], 'status': 'NOT_RUN', 'reason': 'bounded observation budget exhausted'}
        elif stop_all or lane['workOrder'] in stopped:
            status = {'id': lane['id'], 'status': 'NOT_RUN',
                      'reason': stop_reason if stop_all else 'workstream stopped by scoped Andon'}
        else:
            result = run_bounded(isolated_command(args, runtime, 'lane', lane['id']), str(HERE), parent_env,
                                 capture/'namespaces'/(lane['id']+'.stdout'), capture/'namespaces'/(lane['id']+'.stderr'),
                                 min(psf.LANE_SECONDS if psf_lane(lane) else
                                     diagnostics.budget(diagnostics.mode_for_lane(lane))['namespaceSeconds'] if diagnostics.mode_for_lane(lane)
                                     else lane['timeoutSeconds'] + 75 + (lane.get('postCaptureCheckSeconds',0) if lane.get('result',{}).get('kind') in ('r0040-capture-dateonly', passive.KIND, 'r003f-matrix') else 0)
                                     + (passive.READMISSION_SECONDS if lane.get('result', {}).get('kind') == passive.KIND else 0)
                                     + (90 if cost_lane(lane) else 0), remaining))
            path = capture/'lane-status'/(lane['id']+'.json')
            try: inner = json.loads(path.read_text())
            except (OSError, ValueError): inner = None
            status = namespace_status(lane, result, inner)
            if status.get('stopAll'):
                stop_all = True
                stop_reason = status.get('reason', status['status'])
            if status['status'] == 'ANDON': stopped.add(lane['workOrder'])
        if 'preExecutionCurrentness' in lane:
            status['outerCurrentness'] = lane['preExecutionCurrentness']
        status['workOrder'] = lane['workOrder']
        overall['lanes'].append(status); write_json(capture/'observation.json', overall)
    overall['status'] = ('ISOLATION_FAIL' if any(x['status'] == 'ISOLATION_FAIL' for x in overall['lanes']) else
                         'ISOLATION_UNCONFIRMED' if any(x['status'] == 'ISOLATION_UNCONFIRMED' for x in overall['lanes']) else
                         VETO_STATUS if any(x['status'] == VETO_STATUS for x in overall['lanes']) else
                         'OBSERVED' if overall['lanes'] and all(x['status'] in (psf.OBSERVED, 'PASS', CAPTURE_ADMITTED, R0040_DATEONLY_ADMITTED, passive.ADMITTED, STAGES_OBSERVED, COSTS_OBSERVED, TABHIDE_OBSERVED, 'ADMITTED_MATRIX_DIAGNOSTIC','VERIFIED_MATRIX_CAPTURE', *[r['status'] for r in diagnostics.ROUTES.values()]) for x in overall['lanes']) else
                         'OBSERVED_WITH_INCOMPLETE_OR_FAILED_LANES')
    if psf_campaign(args):
        overall['psfPair']=psf.pair_status(plan,overall['lanes'])
        if overall['status']=='OBSERVED' and overall['psfPair']['status']!='OBSERVED':
            overall['status']='OBSERVED_WITH_INCOMPLETE_OR_FAILED_LANES'
    write_json(capture/'observation.json', overall)
    return 0 if overall['status'] == 'OBSERVED' else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('task', 'research', 'baseline', 'historical'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--engine', choices=('chromium', 'firefox', 'webkit'), default='chromium')
    parser.add_argument('--campaign', type=Path)
    parser.add_argument('--r003f-dpr', type=int, choices=(1, 2), default=1)
    parser.add_argument('--r003f-harness', choices=('published', 'corrected-b0', 'corrected-matrix', *diagnostics.ROUTES), default='published')
    parser.add_argument('--r003f-matrix',type=json.loads)
    parser.add_argument('--r0040-mode', choices=('options', *R0040_CAPTURE_MODES), default='options')
    parser.add_argument('--work-orders', nargs='+')
    parser.add_argument('--retain-evidence', action='store_true')
    parser.add_argument('--r0035-guard', choices=('default', 'off'), default='default')
    parser.add_argument('--r0035-scope', choices=('all', 'preview-members'), default='all')
    parser.add_argument('--r0035-mode', choices=('both', 'timing', 'capture'), default='both')
    parser.add_argument('--r0035-stages', action='store_true')
    parser.add_argument('--r0035-costs', action='store_true')
    parser.add_argument('--r0035-psf', action='store_true')
    parser.add_argument('--r002f', action='store_true')
    parser.add_argument('--r002f-dpr', type=int, choices=(1, 2, 3), default=1)
    parser.add_argument('--r002f-rounds', type=int, choices=range(1, 11), default=1)
    parser.add_argument('--r002f-section', choices=('all', 'prayer', 'preview'), default='all')
    parser.add_argument('--r002f-route', choices=('offscreen','tabhide'), default='offscreen')
    parser.add_argument('--inside', action='store_true')
    parser.add_argument('--phase', choices=('prepare', 'lane'))
    parser.add_argument('--outer-netns'); parser.add_argument('--lane')
    args = parser.parse_args()
    os.umask(0o077)
    def interrupted(signum, _frame):
        raise InterruptedError('observation interrupted by signal '+str(signum))
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    runtime = json.loads((args.task/'runtime.json').read_text())
    try:
        if args.campaign:
            campaign = read_campaign(args.campaign)
            args.engine = campaign['engine']; args.r003f_dpr = campaign['r003fDpr']
            args.r002f = campaign['r002f']['enabled']; args.r002f_dpr = campaign['r002f']['dpr']
            args.r002f_rounds = campaign['r002f']['rounds']; args.r002f_section = campaign['r002f']['section']
            args.r002f_route = campaign.get('r002fRoute','offscreen')
            args.work_orders = campaign.get('workOrders'); args.retain_evidence = campaign.get('evidenceRetention', False)
            args.r003f_harness = campaign.get('r003fHarness', 'published')
            args.r003f_matrix = campaign.get('r003fMatrix')
            args.r0040_mode = campaign.get('r0040Mode', 'options')
            args.r0035_stages = campaign.get('r0035Stages', False)
            args.r0035_costs = campaign.get('r0035Costs', False)
            args.r0035_psf = campaign.get('r0035Psf', False)
            for key, value in star_controls(campaign.get('r0035')).items():
                setattr(args, 'r0035_'+key, value)
            write_json(args.task/'capture'/'campaign.json', campaign)
        args.work_orders = campaign_selection(args)
        star_campaign(args)
        stage_campaign(args)
        cost_campaign(args)
        psf_campaign(args)
        moon_campaign(args)
        matrix_campaign(args)
        diagnostic_campaign(args)
        observation_budget(args)
        rain_campaign(args)
        tabhide_campaign(args)
        return inside(args, runtime) if args.inside else outside(args, runtime)
    except Exception as exc:
        write_json(args.task/'capture'/('coordinator-error-'+(args.lane or args.phase or 'outer')+'.json'),
                   {'type': type(exc).__name__, 'error': str(exc)})
        return 2


if __name__ == '__main__': sys.exit(main())
