"""Create an explicitly instrumented R0035 lab without editing its source lab.

Only two standalone lab modules change. The original lab identity is retained
unchanged and deliberately cannot admit those altered modules. A separate plan
protocol and full-file transformation identity admit the diagnostic derivative.
"""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import types

HERE = Path(__file__).resolve().parent
PINS_PATH = HERE/'r0035-stage-pins.json'
PINS_SHA256 = '26a180b7aad4d54fa139eb20484e95efdc2e9cb759a77b2eaa5c175996a7233e'
SUPPORT_SHA256 = 'b486ff54cdad7c939b5cd131b56bfbc0843a43a21430ab6927fd66bf4abed347'
RETENTION_PINS_SHA256 = '32f31a2029adacb9c15e471e30bea69d41b2ca5d1ab5079d11b87efe2525bab3'
KIND = 'instrumented-r0035-stages/1'
IDENTITY = 'r0035-stage-identity/1'
LIVE = 'tools/r0035/live_lab.mjs'
WORKER = 'tools/r0035/lab_worker.mjs'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def need(condition, message):
    if not condition:
        raise ValueError(message)


def pins():
    raw = PINS_PATH.read_bytes()
    need(digest(raw) == PINS_SHA256, 'stage source pins digest mismatch')
    return json.loads(raw)


def support():
    path = HERE/'retain_r0035.py'; source = path.read_bytes()
    need(digest(source) == SUPPORT_SHA256, 'reviewed original-driver loader digest mismatch')
    need(digest((HERE/'retention-pins.json').read_bytes()) == RETENTION_PINS_SHA256,
         'original-driver source pins digest mismatch')
    module = types.ModuleType('r0035_stage_original_support'); module.__file__ = str(path)
    exec(compile(source, str(path), 'exec'), module.__dict__)
    return module


MAIN_SETUP = """  const stageLog={protocol:'r0035-stage-observation/1',clockDomain:'page-performance-now-ms',
    startedAt:performance.now(),limit:2048,overflow:false,events:[]};
  let stageFirstRequested=null,stageFirstPublished=null;
  function stage(kind,details={}){
    if(stageLog.events.length>=stageLog.limit){stageLog.overflow=true;return;}
    stageLog.events.push({at:performance.now(),kind,...details});
  }
  stage('installed',{config:{...config}});
"""
WORKER_SETUP = """// Diagnostic marks use only this worker's clock. No main/worker subtraction.
function stageMark(trace,kind,details={}){
  if(trace)trace.marks.push({at:performance.now(),kind,...details});
}
"""


def replacements():
    """Literal seams remain independently reversible to the complete originals."""
    return {
        LIVE: [
            ('startup-buffer', '  const guard=new FrameGuard(config.guard!==false);',
             MAIN_SETUP+'  const guard=new FrameGuard(config.guard!==false);'),
            ('existing-events', '  function event(kind,details={}){\n    if(!trial)return;',
             """  function event(kind,details={}){
    if(kind!=='publication'||stageFirstPublished!==epoch){
      if(kind==='publication')stageFirstPublished=epoch;
      stage(kind==='publication'?'first-publication':kind,{epoch,tier:source?.tier??null,
        identity:source?.job.native.identity??null,...details});
    }
    if(!trial)return;"""),
            ('dispatch-boundaries', '    try{worker.postMessage(make());}catch(e){failed(String(e));}',
             """    stage('prepare-dispatch-start',{messageEpoch:preparing,activeEpoch:epoch});
    try{const message=make();
      stage('prepare-message-built',{messageEpoch:message.epoch,activeEpoch:epoch});
      worker.postMessage(message);
      stage('prepare-dispatch-returned',{messageEpoch:message.epoch,activeEpoch:epoch});
    }catch(e){failed(String(e));}"""),
            ('reply-before-stale-filter', '  worker.onmessage=({data:m})=>{\n    if(terminal)return;',
             """  worker.onmessage=({data:m})=>{
    if(m.op==='ready'||m.op==='failed')stage('prepare-reply',{op:m.op,messageEpoch:m.epoch,
      activeEpoch:epoch,preparingEpoch:preparing,latestQueued:!!latest,terminal,worker:m.r0035Stages??null});
    if(terminal)return;"""),
            ('first-sample-request', "      requestedUtc=s.utcMs;pending=true;worker.postMessage({op:'sample',epoch,utcMs:requestedUtc,motion:{gain,paused:s.paused,reduced:s.reducedMotion}});",
             """      requestedUtc=s.utcMs;pending=true;
      if(stageFirstRequested!==epoch){stageFirstRequested=epoch;stage('first-sample-request',{epoch,utcMs:requestedUtc});}
      worker.postMessage({op:'sample',epoch,utcMs:requestedUtc,motion:{gain,paused:s.paused,reduced:s.reducedMotion}});"""),
            ('replacement-references', "      epoch++;pending=false;prepared=false;inactive('preparing accepted frame');writer.invalidate();",
             """      stage('source-replacement',{nextEpoch:epoch+1,previousEpoch:epoch,hadSource:!!source,
        rasterReferenceChanged:source?.raster!==r,canvasReferenceChanged:source?.canvas!==canvas,
        discKeyChanged:source?.discKey!==discKey,cloudReferenceChanged:source?.cloud!==capture.cloudRGBA,
        moonReferenceChanged:source?.moon!==capture.moonRGBA,maskReferenceChanged:source?.mask!==mask});
      epoch++;pending=false;prepared=false;inactive('preparing accepted frame');writer.invalidate();"""),
            ('separate-snapshot', '  return {publish,present,clear,dispose,renew,',
             "  return {publish,present,clear,dispose,renew,\n    observeStages:()=>structuredClone(stageLog),"),
        ],
        WORKER: [
            ('local-recorder', 'let current=null, generation=0, catalogue=null;',
             WORKER_SETUP+'let current=null, generation=0, catalogue=null;'),
            ('optional-local-trace', 'export async function prepareLiveFrame(msg) {',
             'export async function prepareLiveFrame(msg,trace=null) {'),
            ('catalogue-start', '  const catalogue=await records(preview?.sha256??msg.frame.catalogue.sha256);',
             "  stageMark(trace,'catalogue-start');\n  const catalogue=await records(preview?.sha256??msg.frame.catalogue.sha256);\n  stageMark(trace,'catalogue-ready');"),
            ('source-verified', '  const stars=preview?livePreviewStars(raster,expected):prepareStars({...msg.frame,sources:expected},catalogue);',
             "  stageMark(trace,'source-verified',{projected:sources.length,preview:!!preview});\n  const stars=preview?livePreviewStars(raster,expected):prepareStars({...msg.frame,sources:expected},catalogue);\n  stageMark(trace,'stars-prepared',{stars:stars.length});"),
            ('replay-prepared', '  const prepared=prepareReplay(raster,stars,msg.config,msg.foreground);',
             "  const prepared=prepareReplay(raster,stars,msg.config,msg.foreground);\n  stageMark(trace,'replay-prepared',{sources:prepared.sourceCount,variablePixels:prepared.indices.length});"),
            ('nominal-verified', "  if(msg.nominal.length!==prepared.nominal.length||prepared.nominal.some((value,i)=>value!==msg.nominal[i]))throw new Error('Nominal native bytes mismatch');",
             "  if(msg.nominal.length!==prepared.nominal.length||prepared.nominal.some((value,i)=>value!==msg.nominal[i]))throw new Error('Nominal native bytes mismatch');\n  stageMark(trace,'nominal-verified');"),
            ('census-complete', '  return prepared;', "  stageMark(trace,'census-complete');\n  return prepared;"),
            ('per-message-trace', '  const msg=event.data;\n  try{',
             """  const msg=event.data;
  const trace=msg.op==='prepare'?{protocol:'r0035-worker-stages/1',clockDomain:'worker-performance-now-ms',epoch:msg.epoch,marks:[]}:null;
  if(trace)stageMark(trace,'received');
  try{"""),
            ('prepare-with-local-trace', 'generation=msg.epoch;current=null;const candidate=await prepareLiveFrame(msg);',
             "generation=msg.epoch;current=null;const candidate=await prepareLiveFrame(msg,trace);\n      stageMark(trace,'candidate-returned');"),
            ('ready-piggyback', "      current=candidate;self.postMessage({op:'ready',epoch:generation,sources:candidate.sourceCount,contributingCenters:candidate.contributingCenters,variablePixels:candidate.indices.length,census:candidate.census});",
             "      current=candidate;stageMark(trace,'ready-post');self.postMessage({op:'ready',epoch:generation,sources:candidate.sourceCount,contributingCenters:candidate.contributingCenters,variablePixels:candidate.indices.length,census:candidate.census,r0035Stages:trace});"),
            ('failed-prefix', "  }catch(error){self.postMessage({op:'failed',epoch:msg.epoch,reason:String(error?.message??error)});}",
             "  }catch(error){if(trace)stageMark(trace,'failed');self.postMessage({op:'failed',epoch:msg.epoch,reason:String(error?.message??error),...(trace?{r0035Stages:trace}:{})});}"),
        ],
    }


def transform(name, source):
    row = pins()['files'][name]
    need(len(source) == row['bytes'] and digest(source) == row['sha256'], 'original stage source drift: '+name)
    text = source.decode(); changes = []
    for label, old, new in replacements()[name]:
        need(text.count(old) == 1, 'missing or duplicate stage seam: '+label)
        text = text.replace(old, new)
        changes.append({'label': label, 'preimageSha256': digest(old.encode()), 'postimageSha256': digest(new.encode())})
    data = text.encode()
    # Mechanical reversibility protects every original line outside the seams.
    restored = text
    for label, old, new in reversed(replacements()[name]):
        need(restored.count(new) == 1, 'ambiguous reverse stage seam: '+label)
        restored = restored.replace(new, old)
    need(restored.encode() == source, 'stage transform is not exactly reversible')
    return data, {'sourceSha256': digest(source), 'resultSha256': digest(data), 'edits': changes}


def inventory(root):
    """Complete private file closure; no links or traversal."""
    rows = {}
    for base, dirs, files in os.walk(root, followlinks=False):
        for name in dirs+files:
            path = Path(base)/name
            need(not path.is_symlink(), 'symlink in diagnostic source tree')
        for name in files:
            path = Path(base)/name
            need(stat.S_ISREG(path.stat().st_mode), 'nonregular diagnostic source input')
            data = path.read_bytes()
            rows[path.relative_to(root).as_posix()] = {'sha256': digest(data), 'bytes': len(data)}
    return dict(sorted(rows.items()))


def write_json(path, value):
    pending = path.with_name(path.name+'.pending')
    with pending.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2); stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
    os.link(pending, path)


def original_plan(driver, plan):
    need(plan.get('kind') == 'independent-reconstruction', 'original independent-reconstruction plan required')
    base = Path(plan['arms']['unmodified']['root']).resolve()
    def regular(name):
        relative = PurePosixPath(name)
        need(not relative.is_absolute() and '..' not in relative.parts, 'unsafe original lab receipt path')
        target = base
        for part in relative.parts:
            target = target/part
            need(not target.is_symlink(), 'symlink in original lab receipt input')
        need(target.is_file(), 'regular original lab receipt input required')
        return target
    base_receipt = json.loads(regular('r0035-lab-identity.json').read_bytes())
    for name in base_receipt['sha256']:
        regular(name)
    driver.check_plan(plan)
    driver.verify_reconstructed_flags(plan['arms'])
    expected = pins()['researchCommit']
    need(all(plan['arms'][key]['commit'] == expected for key in ('unmodified','mitigated')), 'immutable lab source head required')
    for name, row in pins()['files'].items():
        data = regular(name).read_bytes()
        need(len(data) == row['bytes'] and digest(data) == row['sha256'], 'original lab source pin mismatch: '+name)
    return base


def prepare(driver_path, plan_path, output, receipt_path, plan_output):
    os.umask(0o077)
    for path in (output, receipt_path, plan_output):
        need(not path.exists() and not path.is_symlink(), 'fresh derivative, receipt and plan required')
    output, receipt_path, plan_output = [p.resolve() for p in (output, receipt_path, plan_output)]
    for path in (output, receipt_path, plan_output):
        need(not path.exists() and not path.is_symlink(), 'fresh derivative, receipt and plan required')
    plan_bytes = plan_path.read_bytes(); plan = json.loads(plan_bytes)
    loader = support(); driver = loader.load_driver(driver_path); base = original_plan(driver, plan)
    inputs = [base, Path(plan['arms']['main']['root']).resolve(), Path(driver_path).resolve().parents[2]]
    for target in (output, receipt_path, plan_output):
        need(all(target != root and root not in target.parents for root in inputs), 'diagnostic outputs must be outside original sources')
    targets = (output, receipt_path, plan_output)
    need(len(set(targets)) == 3 and all(a not in b.parents for a in targets for b in targets if a != b),
         'separate derivative source, private receipt and plan required')
    before = inventory(base)
    modified = {}; patches = {}
    for name in (LIVE, WORKER):
        modified[name], patches[name] = transform(name, (base/name).read_bytes())
    record = {'protocol': IDENTITY, 'status': 'INCOMPLETE', 'nativeStatus': 'NOT_RUN', 'timingClass': 'instrumented-stage-observation',
              'sourcePlanSha256': digest(plan_bytes), 'sourcePlan': plan, 'baseRoot': str(base), 'root': str(output),
              'baseIdentitySha256': digest((base/'r0035-lab-identity.json').read_bytes()), 'baseFiles': before,
              'sourcePinsSha256': PINS_SHA256, 'materializerSha256': digest(Path(__file__).read_bytes()), 'patches': patches}
    try:
        shutil.copytree(base, output, copy_function=shutil.copy2)
        for name, data in modified.items():
            (output/name).write_bytes(data)
        after = inventory(output)
        need(set(before) == set(after), 'diagnostic source population changed unexpectedly')
        changed = [name for name in before if before[name] != after[name]]
        need(set(changed) == {LIVE, WORKER}, 'only the two identified stage modules may change')
        need(inventory(base) == before, 'original lab changed during materialization')
        record.update(status='PREPARED', files=after, changedFiles=changed)
        write_json(output/'r0035-stage-identity.json', record)
        write_json(receipt_path, record)
        mapped = copy.deepcopy(plan); mapped['kind'] = KIND
        for label in ('unmodified','mitigated'):
            mapped['arms'][label]['root'] = str(output)
        mapped['diagnostic'] = {'identity': str(receipt_path), 'sha256': digest(receipt_path.read_bytes())}
        write_json(plan_output, mapped)
        return record
    except BaseException as error:
        # Keep the failed tree and completed patch state. A failure receipt is
        # separate and cannot overwrite an already-published prepared identity.
        record.update(status='INCOMPLETE', error={'type': type(error).__name__, 'message': str(error)})
        failure = receipt_path.with_name(receipt_path.name+'.failure.json')
        if not failure.exists():
            write_json(failure, record)
        raise


def admit(plan, driver, expected_identity=None):
    need(plan.get('kind') == KIND, 'distinct instrumented stage plan required')
    diagnostic = plan.get('diagnostic', {})
    path = Path(diagnostic.get('identity', ''))
    if expected_identity is not None:
        need(path.resolve() == Path(expected_identity).resolve(), 'unexpected diagnostic identity path')
    raw = path.read_bytes(); need(digest(raw) == diagnostic.get('sha256'), 'diagnostic identity digest mismatch')
    record = json.loads(raw)
    need(record.get('protocol') == IDENTITY and record.get('status') == 'PREPARED' and record.get('nativeStatus') == 'NOT_RUN',
         'prepared diagnostic identity required')
    need(record.get('sourcePinsSha256') == PINS_SHA256 and record.get('materializerSha256') == digest(Path(__file__).read_bytes()),
         'diagnostic transformation source mismatch')
    base = original_plan(driver, record['sourcePlan'])
    need(str(base) == record['baseRoot'] and inventory(base) == record['baseFiles'], 'original lab identity or bytes changed')
    need(digest((base/'r0035-lab-identity.json').read_bytes()) == record['baseIdentitySha256'], 'original lab receipt changed')
    output = Path(record['root']).resolve()
    expected = copy.deepcopy(record['sourcePlan']); expected['kind'] = KIND
    for label in ('unmodified','mitigated'):
        expected['arms'][label]['root'] = str(output)
    expected['diagnostic'] = diagnostic
    need(plan == expected, 'instrumented plan changed original flags, probes or main')
    actual = inventory(output)
    for name in ('r0035-stage-identity.json', 'r0035-stage-identity.json.pending'):
        need(actual.pop(name, {}).get('sha256') == digest(raw), 'derived tree identity receipt mismatch')
    need(actual == record['files'], 'diagnostic runtime source drift or population mismatch')
    need(set(actual) == set(record['baseFiles']), 'diagnostic source population changed from its original')
    changed = {name for name in actual if actual[name] != record['baseFiles'][name]}
    need(changed == {LIVE, WORKER}, 'only the two identified stage modules may change')
    need(set(record['changedFiles']) == {LIVE, WORKER}, 'unexpected diagnostic patch population')
    for name in (LIVE, WORKER):
        changed, proof = transform(name, (base/name).read_bytes())
        need(record['patches'][name] == proof and (output/name).read_bytes() == changed, 'diagnostic patch postimage mismatch')
    # The original checker remains strict: it is run on the intact source plan,
    # never tricked into treating the derivative's altered bytes as original.
    return record


def preparation_process(path, driver_path, plan_path, identity_path, expected_sha256=None):
    """Require the coordinator's actual child completion before driver import."""
    def regular(file):
        file = Path(file).absolute()
        need(file.is_file() and not any(p.is_symlink() for p in (file, *file.parents)),
             'regular stage preparation custody file required')
        return file, file.read_bytes()
    process_path, raw = regular(path); body = json.loads(raw)
    need(expected_sha256 is None or digest(raw) == expected_sha256, 'stage preparation receipt changed after planning')
    need(body.get('protocol') == 'r0035-stage-preparation-process/1'
         and type(body.get('returncode')) is int and body['returncode'] == 0
         and body.get('timedOut') is False and not body.get('retentionError'),
         'stage preparation process did not complete successfully')
    need(body.get('materializerSha256') == digest(Path(__file__).read_bytes()), 'stage preparation source changed')
    def member(name, expected=None):
        row = body.get(name, {})
        file, data = regular(row.get('path', ''))
        need(expected is None or file.resolve() == Path(expected).resolve(), 'stage preparation '+name+' path mismatch')
        need(row.get('sha256') == digest(data), 'stage preparation '+name+' digest mismatch')
        return file, data
    driver_file, driver_raw = member('driver', driver_path)
    need(digest(driver_raw) == pins()['files']['tools/r0035/native_trials.py']['sha256'], 'original stage driver drift')
    plan_file, plan_raw = member('plan', plan_path)
    identity_file, identity_raw = member('identity', identity_path)
    source_file, source_raw = member('sourcePlan')
    _, common_raw = member('originalPreparation')
    _, original_process_raw = member('originalPreparationProcess')
    _, lab_raw = member('originalLabIdentity')
    record, plan, source = json.loads(identity_raw), json.loads(plan_raw), json.loads(source_raw)
    common, original_process = json.loads(common_raw), json.loads(original_process_raw)
    need(type(original_process.get('returncode')) is int and original_process['returncode'] == 0
         and original_process.get('timedOut') is False, 'original source preparation did not complete successfully')
    need(common.get('protocol') == 'salah-hosted-native-preparation/1' and common.get('status') == 'PREPARED',
         'original source preparation receipt required')
    need(record.get('sourcePlan') == source and record.get('sourcePlanSha256') == digest(source_raw)
         and record.get('baseIdentitySha256') == digest(lab_raw), 'stage preparation original source custody differs')
    need(source['arms']['main']['root'] == common['trees']['main']['root']
         and all(source['arms'][label]['root'] == common['trees']['r0035']['root'] for label in ('unmodified','mitigated'))
         and driver_file == Path(common['sources']['research']['root'])/'tools/r0035/native_trials.py',
         'stage preparation original roots differ')
    need(plan.get('diagnostic') == {'identity': str(identity_file), 'sha256': digest(identity_raw)}
         and record.get('root') == body.get('root'), 'stage preparation derivative custody differs')
    argv = body.get('argv', [])
    expected = [str(HERE/'r0035_stage_materialize.py'), '--driver', str(driver_file), '--plan', str(source_file),
                '--out', body['root'], '--receipt', str(identity_file), '--plan-out', str(plan_file)]
    need(isinstance(argv, list) and len(argv) == len(expected)+1 and isinstance(argv[0], str)
         and argv[1:] == expected, 'stage preparation invocation differs')
    return {'process': {'path': str(process_path), 'sha256': digest(raw)},
            'originalPreparation': body['originalPreparation'], 'originalSourcePlan': body['sourcePlan'],
            'originalLabIdentity': body['originalLabIdentity'], 'identitySha256': digest(identity_raw),
            'planSha256': digest(plan_raw), 'materializerSha256': body['materializerSha256']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('driver', 'plan', 'out', 'receipt', 'plan-out'):
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    prepare(args.driver, args.plan, args.out, args.receipt, args.plan_out)
    print('PREPARED instrumented R0035 derivative; native observation NOT_RUN')


if __name__ == '__main__': main()
