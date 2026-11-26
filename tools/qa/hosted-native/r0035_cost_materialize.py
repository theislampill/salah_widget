"""Distinct, reversible aggregate-cost derivative of the original R0035 lab.

The original stage recipe and physical dependencies remain unchanged. Four lab
modules change and one explicitly inventoried diagnostic collector is added.
"""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil

HERE = Path(__file__).resolve().parent
STAGE_MATERIALIZER_SHA256 = '1890dbdeacf3bcd3fc7f9624a8a970770ae4dbb43f6987e43919c7161e17bf4a'
if hashlib.sha256((HERE/'r0035_stage_materialize.py').read_bytes()).hexdigest() != STAGE_MATERIALIZER_SHA256:
    raise ValueError('reviewed stage materializer changed')
import r0035_stage_materialize as stages

digest, need, pins = stages.digest, stages.need, stages.pins
support, inventory, write_json, original_plan = stages.support, stages.inventory, stages.write_json, stages.original_plan
PINS_SHA256 = stages.PINS_SHA256
KIND = 'instrumented-r0035-costs/1'
IDENTITY = 'r0035-cost-identity/1'
TIMING = 'instrumented-preparation-costs'
LIVE, WORKER = stages.LIVE, stages.WORKER
STELLAR, REPLAY = 'tools/r0035/stellar_replay.mjs', 'tools/r0035/prepared_replay.mjs'
HELPER = 'tools/r0035/r0035_costs.mjs'
MODIFIED = (LIVE, WORKER, STELLAR, REPLAY)
HELPER_SHA256 = '37435a7567eec1eecf7e648e854682e3d9fab9ddb6cf888e83f7515846d88fa8'
IMPORT = "import {createCosts,costStart,costEnd,countCost,finishCosts} from './r0035_costs.mjs';\n"


def replacements():
    return {
        LIVE: [],  # The existing short-circuit restart expression is untouched.
        WORKER: [
            ('collector-import', "import {prepareStars,preparePatch,glassMembership} from './stellar_replay.mjs';", IMPORT+"import {prepareStars,preparePatch,glassMembership} from './stellar_replay.mjs';"),
            ('preview-cost-argument', 'export function livePreviewStars(raster,sources){', 'export function livePreviewStars(raster,sources,costs=null){'),
            ('preview-visited', '  for(const s of sources){', "  for(const s of sources){\n    countCost(costs,'previewInputSources');"),
            ('preview-spectrum-start', '    const flux=spectralStarFlux(s,s.altDeg,{}, {response:', "    countCost(costs,'spectralSources');costStart(costs,'spectralFlux');\n    const flux=spectralStarFlux(s,s.altDeg,{}, {response:"),
            ('preview-transport-count', 'transportAt:wavelength=>directTransmission(wavelength,s.altDeg,atmosphere,1)});', "transportAt:wavelength=>{countCost(costs,'transportSamples');return directTransmission(wavelength,s.altDeg,atmosphere,1);}});\n    costEnd(costs,'spectralFlux');"),
            ('preview-patch-cost', 'stars.push(preparePatch({...s,detectable:true},flux,raster.width,raster.height));', 'stars.push(preparePatch({...s,detectable:true},flux,raster.width,raster.height,costs));'),
            ('local-cost-reference', 'export async function prepareLiveFrame(msg,trace=null) {', 'export async function prepareLiveFrame(msg,trace=null) {\n  const costs=trace?.costs??null;'),
            ('full-stars-cost', 'const stars=preview?livePreviewStars(raster,expected):prepareStars({...msg.frame,sources:expected},catalogue);', 'const stars=preview?livePreviewStars(raster,expected,costs):prepareStars({...msg.frame,sources:expected},catalogue,costs);'),
            ('replay-cost', 'const prepared=prepareReplay(raster,stars,msg.config,msg.foreground);', 'const prepared=prepareReplay(raster,stars,msg.config,msg.foreground,costs);'),
            ('per-epoch-collector', "clockDomain:'worker-performance-now-ms',epoch:msg.epoch,marks:[]}:null;", "clockDomain:'worker-performance-now-ms',epoch:msg.epoch,marks:[],costs:createCosts(msg.epoch)}:null;"),
            ('complete-preparation', "      stageMark(trace,'candidate-returned');", "      if(trace)finishCosts(trace.costs,'COMPLETE');\n      stageMark(trace,'candidate-returned');"),
            ('failed-prefix', "if(trace)stageMark(trace,'failed');", "if(trace){if(trace.costs.status==='COLLECTING')finishCosts(trace.costs,'FAILED');stageMark(trace,'failed');}"),
        ],
        STELLAR: [
            ('collector-import', "import {renderStars} from '../../real-sky/core/src/renderer.mjs';", IMPORT+"import {renderStars} from '../../real-sky/core/src/renderer.mjs';"),
            ('stars-cost-argument', 'export function prepareStars(frame, catalogue) {', 'export function prepareStars(frame, catalogue, costs=null) {'),
            ('full-visited', '  for (const source of frame.sources) {', "  for (const source of frame.sources) {\n    countCost(costs,'fullInputSources');"),
            ('spectral-start', '    const flux = spectralStarFlux(record, source.altDeg, {}, {response:', "    countCost(costs,'spectralSources');costStart(costs,'spectralFlux');\n    const flux = spectralStarFlux(record, source.altDeg, {}, {response:"),
            ('transport-count', 'transportAt: wavelength => directTransmission(wavelength,source.altDeg,raster.atmosphere,d.cloudTransmission)});', "transportAt: wavelength => {countCost(costs,'transportSamples');return directTransmission(wavelength,source.altDeg,raster.atmosphere,d.cloudTransmission);}});\n    costEnd(costs,'spectralFlux');"),
            ('stars-patch-cost', 'stars.push(preparePatch({...source, detectable:true},flux,raster.width,raster.height));', 'stars.push(preparePatch({...source, detectable:true},flux,raster.width,raster.height,costs));'),
            ('patch-cost-argument', 'export function preparePatch(star, flux, width, height) {', 'export function preparePatch(star, flux, width, height, costs=null) {'),
            ('patch-start', '  const patch = renderStars', "  countCost(costs,'patchCalls');countCost(costs,'patchPixelsRequested',w*h);costStart(costs,'psfRaster');\n  const patch = renderStars"),
            ('patch-completed', '  return {...star,x0,y0,w,h,linear:patch.linear,modes:starModes(star.id)};', "  costEnd(costs,'psfRaster');countCost(costs,'drawnPatches',patch.drawn);\n  // Derived from the unchanged default reference renderer/optics: 3 channels, 2 positive parts.\n  countCost(costs,'referencePsfChannels',3*patch.drawn);countCost(costs,'referenceGaussianCalls',6*patch.drawn);\n  return {...star,x0,y0,w,h,linear:patch.linear,modes:starModes(star.id)};"),
        ],
        REPLAY: [
            ('collector-import', "import {nativeCalendarRegion,nativeForeground} from '../../real-sky/native-composition.mjs';", IMPORT+"import {nativeCalendarRegion,nativeForeground} from '../../real-sky/native-composition.mjs';"),
            ('replay-cost-argument', 'export function prepareReplay(raster,stars,config,foreground) {', 'export function prepareReplay(raster,stars,config,foreground,costs=null) {'),
            ('calendar', '  const base=nativeCalendarRegion(raster,mask), gas=raster.skyBackgroundLinear??raster.backgroundLinear;', "  countCost(costs,'replayInputSources',stars.length);costStart(costs,'calendarTransfer');\n  const base=nativeCalendarRegion(raster,mask), gas=raster.skyBackgroundLinear??raster.backgroundLinear;\n  costEnd(costs,'calendarTransfer');"),
            ('nominal-envelope', '  const nominal=compose(raster,base,gas,cloud,moon), envelope=new Float64Array(base.length);', "  costStart(costs,'nominalCompose');\n  const nominal=compose(raster,base,gas,cloud,moon);\n  costEnd(costs,'nominalCompose');countCost(costs,'fullComposeCalls');costStart(costs,'envelopeBounds');\n  const envelope=new Float64Array(base.length);"),
            ('envelope-pixel-count', '    const bound=.04*config.multiplier*glassScale;', "    countCost(costs,'envelopePatchPixelsScheduled',star.w*star.h);\n    const bound=.04*config.multiplier*glassScale;"),
            ('envelope-ended', '  const extremum=sign=>{', "  costEnd(costs,'envelopeBounds');countCost(costs,'replaySelectedSources',sources.length);\n  const extremum=sign=>{\n    const costBucket=sign<0?'lowerBoundCompose':'upperBoundCompose';costStart(costs,costBucket);"),
            ('extremum-composed', '    return compose(raster,linear,gas,cloud,moon);', "    const encoded=compose(raster,linear,gas,cloud,moon);\n    costEnd(costs,costBucket);countCost(costs,'fullComposeCalls');return encoded;"),
            ('variable-start', '  for(let p=0;p<map.length;p++) {', "  costStart(costs,'variableSelection');\n  for(let p=0;p<map.length;p++) {"),
            ('weights-start', '  for(const source of sources){', "  costEnd(costs,'variableSelection');countCost(costs,'variablePixels',indices.length);costStart(costs,'patchWeights');\n  for(const source of sources){"),
            ('offset-count', '    source.offsets=Uint32Array.from(offsets);source.weights=Float64Array.from(weights);', "    source.offsets=Uint32Array.from(offsets);source.weights=Float64Array.from(weights);\n    countCost(costs,'variablePatchOffsets',source.offsets.length);"),
            ('gathers-start', '  const bg=gather(base,indices,3), atmosphere=gather(gas,indices,3),direct=gather(signalMask,indices,1);', "  costEnd(costs,'patchWeights');costStart(costs,'inputGathers');\n  const bg=gather(base,indices,3), atmosphere=gather(gas,indices,3),direct=gather(signalMask,indices,1);"),
            ('gathers-ended', '  const linear=new Float64Array(bg.length), rgba=nominal.slice();', "  const linear=new Float64Array(bg.length), rgba=nominal.slice();\n  costEnd(costs,'inputGathers');\n  countCost(costs,'inputGatherValues',bg.length+(atmosphere?.length??0)+(direct?.length??0)+(cloudPixels?.length??0)+(moonPixels?.length??0));"),
            ('withdrawal-start', '  const centers=sources.map', "  costStart(costs,'centerWithdrawal');\n  const centers=sources.map"),
            ('withdrawal-compose-start', '  const without=compose(raster,withdrawal,gather(gas,centers,3),gather(cloud,centers,4),gather(moon,centers,4));', "  costEnd(costs,'centerWithdrawal');countCost(costs,'withdrawalCenters',centers.length);costStart(costs,'withdrawalCompose');\n  const without=compose(raster,withdrawal,gather(gas,centers,3),gather(cloud,centers,4),gather(moon,centers,4));\n  costEnd(costs,'withdrawalCompose');countCost(costs,'centerComposeCalls');costStart(costs,'centerRanking');"),
            ('ranking-ended', '  return {nominal,indices,sourceCount:sources.length,contributingCenters,present(utcMs,motion={}){', "  costEnd(costs,'centerRanking');\n  return {nominal,indices,sourceCount:sources.length,contributingCenters,present(utcMs,motion={}){"),
        ],
    }


def helper_bytes():
    data = (HERE/'r0035_costs.mjs').read_bytes()
    need(digest(data) == HELPER_SHA256, 'cost collector source drift')
    return data


def transform(name, source):
    need(name in MODIFIED, 'unadmitted cost module')
    row = pins()['files'][name]
    need(len(source) == row['bytes'] and digest(source) == row['sha256'], 'original cost source drift: '+name)
    stage_proof = None
    base = source
    if name in (LIVE, WORKER):
        base, stage_proof = stages.transform(name, source)
    text = base.decode(); changes = []
    for label, old, new in replacements()[name]:
        need(text.count(old) == 1, 'missing or duplicate cost seam: '+label)
        text = text.replace(old, new)
        changes.append({'label':label, 'preimageSha256':digest(old.encode()), 'postimageSha256':digest(new.encode())})
    restored = text
    for label, old, new in reversed(replacements()[name]):
        need(restored.count(new) == 1, 'ambiguous reverse cost seam: '+label)
        restored = restored.replace(new, old)
    need(restored.encode() == base, 'cost transform is not exactly reversible')
    data = text.encode()
    return data, {'sourceSha256':digest(source), 'resultSha256':digest(data), 'stageTransformation':stage_proof,
                  'costEdits':changes, 'originalRecoveredExactly':True}


def prepare(driver_path, plan_path, output, receipt_path, plan_output):
    os.umask(0o077)
    for path in (output,receipt_path,plan_output):
        need(not path.exists() and not path.is_symlink(), 'fresh cost derivative, receipt and plan required')
    output,receipt_path,plan_output=[p.resolve() for p in (output,receipt_path,plan_output)]
    for path in (output,receipt_path,plan_output):
        need(not path.exists() and not path.is_symlink(), 'fresh cost derivative, receipt and plan required')
    plan_bytes=plan_path.read_bytes(); plan=json.loads(plan_bytes)
    driver=support().load_driver(driver_path);base=original_plan(driver,plan)
    inputs=[base,Path(plan['arms']['main']['root']).resolve(),Path(driver_path).resolve().parents[2]]
    for target in (output,receipt_path,plan_output):
        need(all(target!=root and root not in target.parents for root in inputs), 'cost outputs must be outside original sources')
    targets=(output,receipt_path,plan_output)
    need(len(set(targets))==3 and all(a not in b.parents for a in targets for b in targets if a!=b), 'separate cost source, receipt and plan required')
    before=inventory(base);need(HELPER not in before, 'cost collector already exists in original lab')
    modified,patches={},{}
    for name in MODIFIED: modified[name],patches[name]=transform(name,(base/name).read_bytes())
    collector=helper_bytes()
    record={'protocol':IDENTITY,'status':'INCOMPLETE','nativeStatus':'NOT_RUN','timingClass':TIMING,
            'sourcePlanSha256':digest(plan_bytes),'sourcePlan':plan,'baseRoot':str(base),'root':str(output),
            'baseIdentitySha256':digest((base/'r0035-lab-identity.json').read_bytes()),'baseFiles':before,
            'sourcePinsSha256':PINS_SHA256,'stageMaterializerSha256':STAGE_MATERIALIZER_SHA256,
            'materializerSha256':digest(Path(__file__).read_bytes()),'collectorSha256':HELPER_SHA256,'patches':patches}
    try:
        shutil.copytree(base,output,copy_function=shutil.copy2)
        for name,data in modified.items(): (output/name).write_bytes(data)
        (output/HELPER).write_bytes(collector)
        after=inventory(output)
        need(set(after)==set(before)|{HELPER}, 'cost source population changed unexpectedly')
        changed=[name for name in before if before[name]!=after[name]]
        need(set(changed)==set(MODIFIED), 'only four identified cost modules may change')
        need(inventory(base)==before, 'original lab changed during cost materialization')
        record.update(status='PREPARED',files=after,changedFiles=changed,addedFiles=[HELPER])
        write_json(output/'r0035-cost-identity.json',record);write_json(receipt_path,record)
        mapped=copy.deepcopy(plan);mapped['kind']=KIND
        for label in ('unmodified','mitigated'): mapped['arms'][label]['root']=str(output)
        mapped['diagnostic']={'identity':str(receipt_path),'sha256':digest(receipt_path.read_bytes())}
        write_json(plan_output,mapped);return record
    except BaseException as error:
        record.update(status='INCOMPLETE',error={'type':type(error).__name__,'message':str(error)})
        failure=receipt_path.with_name(receipt_path.name+'.failure.json')
        if not failure.exists(): write_json(failure,record)
        raise


def admit(plan, driver, expected_identity=None):
    need(plan.get('kind')==KIND, 'distinct cost plan required')
    diagnostic=plan.get('diagnostic',{});path=Path(diagnostic.get('identity',''))
    need(path.is_file() and not any(p.is_symlink() for p in (path,*path.parents)), 'regular cost identity required')
    if expected_identity is not None: need(path.resolve()==Path(expected_identity).resolve(), 'unexpected cost identity path')
    raw=path.read_bytes();need(digest(raw)==diagnostic.get('sha256'), 'cost identity digest mismatch')
    record=json.loads(raw)
    need(record.get('protocol')==IDENTITY and record.get('status')=='PREPARED' and record.get('nativeStatus')=='NOT_RUN'
         and record.get('timingClass')==TIMING, 'prepared cost identity required')
    need(record.get('sourcePinsSha256')==PINS_SHA256 and record.get('stageMaterializerSha256')==STAGE_MATERIALIZER_SHA256
         and record.get('materializerSha256')==digest(Path(__file__).read_bytes()) and record.get('collectorSha256')==HELPER_SHA256,
         'cost transformation source mismatch')
    base=original_plan(driver,record['sourcePlan'])
    need(str(base)==record['baseRoot'] and inventory(base)==record['baseFiles'], 'original lab identity or bytes changed')
    need(digest((base/'r0035-lab-identity.json').read_bytes())==record['baseIdentitySha256'], 'original lab receipt changed')
    output=Path(record['root']).resolve();expected=copy.deepcopy(record['sourcePlan']);expected['kind']=KIND
    for label in ('unmodified','mitigated'): expected['arms'][label]['root']=str(output)
    expected['diagnostic']=diagnostic;need(plan==expected, 'cost plan changed original flags, probes or main')
    actual=inventory(output)
    for name in ('r0035-cost-identity.json','r0035-cost-identity.json.pending'):
        need(actual.pop(name,{}).get('sha256')==digest(raw), 'cost tree identity receipt mismatch')
    need(actual==record['files'] and set(actual)==set(record['baseFiles'])|{HELPER}, 'cost runtime source drift or population mismatch')
    changed={name for name in record['baseFiles'] if actual[name]!=record['baseFiles'][name]}
    need(changed==set(MODIFIED) and set(record.get('changedFiles',[]))==set(MODIFIED) and record.get('addedFiles')==[HELPER], 'cost patch population differs')
    for name in MODIFIED:
        data,proof=transform(name,(base/name).read_bytes())
        need(record['patches'][name]==proof and (output/name).read_bytes()==data, 'cost patch postimage differs')
    need((output/HELPER).read_bytes()==helper_bytes(), 'cost collector postimage differs')
    return record


def preparation_process(path, driver_path, plan_path, identity_path, expected_sha256=None):
    """Admit actual outer child completion and the complete original custody."""
    def regular(file):
        file=Path(file).absolute()
        need(file.is_file() and not any(p.is_symlink() for p in (file,*file.parents)), 'regular cost preparation custody required')
        return file,file.read_bytes()
    process_path,raw=regular(path);body=json.loads(raw)
    need(expected_sha256 is None or digest(raw)==expected_sha256, 'cost preparation receipt changed after planning')
    need(body.get('protocol')=='r0035-cost-preparation-process/1' and type(body.get('returncode')) is int
         and body['returncode']==0 and body.get('timedOut') is False and body.get('retentionError') is None,
         'cost preparation process did not complete successfully')
    need(body.get('materializerSha256')==digest(Path(__file__).read_bytes()) and body.get('collectorSha256')==HELPER_SHA256
         and body.get('stageMaterializerSha256')==STAGE_MATERIALIZER_SHA256, 'cost preparation source changed')
    need(body.get('cwd')==str(HERE) and type(body.get('timeoutSeconds')) is int and body['timeoutSeconds']==240,
         'cost preparation actual cwd or bound differs')
    def member(name,expected=None):
        row=body.get(name,{});file,data=regular(row.get('path',''))
        need(expected is None or file.resolve()==Path(expected).resolve(), 'cost preparation '+name+' path mismatch')
        need(row.get('sha256')==digest(data), 'cost preparation '+name+' digest mismatch')
        return file,data
    driver_file,driver_raw=member('driver',driver_path)
    need(digest(driver_raw)==pins()['files']['tools/r0035/native_trials.py']['sha256'], 'original cost driver drift')
    plan_file,plan_raw=member('plan',plan_path);identity_file,identity_raw=member('identity',identity_path)
    source_file,source_raw=member('sourcePlan');_,common_raw=member('originalPreparation')
    _,original_process_raw=member('originalPreparationProcess');_,lab_raw=member('originalLabIdentity')
    record,plan,source=json.loads(identity_raw),json.loads(plan_raw),json.loads(source_raw)
    common,original_process=json.loads(common_raw),json.loads(original_process_raw)
    need(type(original_process.get('returncode')) is int and original_process['returncode']==0
         and original_process.get('timedOut') is False, 'original preparation did not complete successfully')
    need(common.get('protocol')=='salah-hosted-native-preparation/1' and common.get('status')=='PREPARED', 'original preparation receipt required')
    need(record.get('sourcePlan')==source and record.get('sourcePlanSha256')==digest(source_raw)
         and record.get('baseIdentitySha256')==digest(lab_raw), 'cost original source custody differs')
    need(source['arms']['main']['root']==common['trees']['main']['root']
         and all(source['arms'][label]['root']==common['trees']['r0035']['root'] for label in ('unmodified','mitigated'))
         and driver_file==Path(common['sources']['research']['root'])/'tools/r0035/native_trials.py', 'cost original roots differ')
    need(plan.get('diagnostic')=={'identity':str(identity_file),'sha256':digest(identity_raw)}
         and record.get('root')==body.get('root'), 'cost derivative custody differs')
    argv=body.get('argv',[])
    expected=[str(HERE/'r0035_cost_materialize.py'),'--driver',str(driver_file),'--plan',str(source_file),
              '--out',body['root'],'--receipt',str(identity_file),'--plan-out',str(plan_file)]
    need(isinstance(argv,list) and len(argv)==len(expected)+1 and isinstance(argv[0],str)
         and Path(argv[0]).is_absolute() and argv[1:]==expected, 'cost preparation invocation differs')
    return {'process':{'path':str(process_path),'sha256':digest(raw)},'originalPreparation':body['originalPreparation'],
            'originalSourcePlan':body['sourcePlan'],'originalLabIdentity':body['originalLabIdentity'],
            'identitySha256':digest(identity_raw),'planSha256':digest(plan_raw),
            'materializerSha256':body['materializerSha256'],'collectorSha256':HELPER_SHA256,
            'stageMaterializerSha256':STAGE_MATERIALIZER_SHA256}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('driver','plan','out','receipt','plan-out'): parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();prepare(args.driver,args.plan,args.out,args.receipt,args.plan_out)
    print('PREPARED instrumented R0035 cost derivative; native observation NOT_RUN')


if __name__=='__main__': main()
