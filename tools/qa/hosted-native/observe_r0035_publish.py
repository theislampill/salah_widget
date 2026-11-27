"""Explicit private-module adapter for one publish-decision observation.

The pinned original driver supplies every scientific function, native call,
clock, warmup, arm loop and report. Only identified plan admission and the
already reviewed route/trial custody wrapper are adapted.
"""
import argparse
import json
import os
from pathlib import Path
import sys
import traceback

import r0035_publish as publish
import r0035_stage_materialize as original
import r003f_matrix_campaign as isolation
from observe_r0035_psf import Browser,Context,Route,error_data


class PlanAdapter:
    def __init__(self,driver,reference,derived,current):
        self.driver,self.reference,self.expected=driver,reference,derived
        self.original_check,self.current,self.calls=driver.check_plan,current,0

    def __call__(self,plan):
        publish.need(publish.same(plan,self.expected),'publish adapter accepts only its canonical derived plan')
        self.current();self.original_check(self.reference);self.driver.verify_reconstructed_flags(plan['arms'])
        for name in publish.ARMS:self.driver.producer_flags(name,plan['arms'][name].get('flags',''),True)
        self.calls+=1


class Custody:
    def __init__(self,directory,loader):
        self.directory,self.loader=Path(directory),loader
        self.current=None;self.trials=[];self.errors=[];self.veto=None;self.calls=0

    def install(self,driver):
        original_trial=driver.trial
        def trial(browser,engine,base,arm,label,out,args):
            self.calls+=1;ordinal=self.calls
            current=self.current={'protocol':'r0035-publish-adapted-trial/1','ordinal':ordinal,
                'arm':label,'base':base,'sourceArm':arm,'engine':engine,'browserVersion':browser.version,
                'originalArguments':json.loads(json.dumps(vars(args),default=str)),
                'originalOutput':str(out),'pages':0,'catchAllRoute':False,'contextClosed':False}
            try:return original_trial(Browser(browser,self),engine,base,arm,label,out,args)
            except BaseException as error:current['originalException']=error_data(error);raise
            finally:
                try:
                    report=Path(out)/'trial.json'
                    if report.is_file():current['originalReport']=publish.record(report)
                    path=self.directory/f'trial-{ordinal:03}-{label}.json';publish.save(path,current)
                    self.trials.append({'ordinal':ordinal,'arm':label,'receipt':publish.record(path)})
                except BaseException as error:self.errors.append(error_data(error))
        driver.trial=trial


def main(argv=None):
    argv=list(sys.argv[1:] if argv is None else argv)
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ('task','preadmission','evidence'):parser.add_argument('--'+key,type=Path,required=True)
    publish.need('--' in argv,'exact original native argument delimiter required')
    delimiter=argv.index('--');args=parser.parse_args(argv[:delimiter]);native=argv[delimiter+1:]
    os.umask(0o077);task=args.task.absolute();p=publish.paths(task);runtime=publish.load(task/'runtime.json')
    publish.need(runtime.get('python')==sys.executable,'actual publish Python differs from acquired runtime')
    sources=publish.source_identity();publish.runtime_authority(task,runtime)
    publish.need(args.preadmission==task/'capture/r0035-publish-preadmission.json','actual publish preadmission path differs')
    admission=publish.admitted_process(publish.load(args.preadmission),task,runtime,native=True)
    publish.need(publish.same(publish.record(p['identity']),admission['identity'])
                 and publish.same(sources,admission['sources']),'publish complete source identity changed after preadmission')
    identity=publish.load(p['identity']);reference=publish.load(p['referencePlan']);derived=publish.load(p['derivedPlan'])
    publish.need(publish.same(publish.record(p['referencePlan']),admission['referencePlan'])
                 and publish.same(publish.record(p['derivedPlan']),admission['derivedPlan'])
                 and publish.same(reference,identity['referencePlan'])
                 and publish.same(derived,publish.derived_plan(reference,p['candidate'],publish.record(p['identity']))),
                 'publish actual complete canonical source plans changed after preadmission')
    target=task/'capture/lanes'/publish.LANE;expected=[str(p['derivedPlan']),str(target),*publish.DRIVER_ARGS]
    publish.need(native==expected and args.evidence==target.with_name(publish.LANE+'-custody'),
                 'publish actual output or original driver arguments differ')
    publish.need(os.environ.get('PLAYWRIGHT_BROWSERS_PATH')==str(task/'python-browsers'),
                 'publish actual managed Python browser root differs')
    loader=original.support();driver_path=Path(admission['driver']);driver=loader.load_driver(driver_path)
    original_sources=loader.verify_inputs(driver_path)
    namespace=Path(os.environ.get('SALAH_HOSTED_NATIVE_ISOLATION_RECEIPT',''))
    loader.verify_isolation(namespace);isolation.original_isolation(namespace)
    publish.need(namespace==task/'capture/isolation'/publish.LANE/'receipt.json','publish actual namespace path differs')
    namespace_record=publish.record(namespace);preadmission_record=publish.record(args.preadmission)
    args.evidence.mkdir(mode=0o700);custody=Custody(args.evidence,loader)
    def current():
        publish.need(publish.same(publish.source_identity(),sources),'publish merged source changed before original plan admission')
        publish.candidate_files(task,runtime,identity)
    adapter=PlanAdapter(driver,reference,derived,current)
    driver.check_plan=adapter;custody.install(driver)
    saved_argv=sys.argv;failure=None
    try:
        sys.argv=[str(driver_path),*native];driver.main()
    except BaseException as error:
        failure=error_data(error);traceback.print_exception(type(error),error,error.__traceback__,file=sys.stderr)
    finally:sys.argv=saved_argv
    summary_record=None
    try:
        if (target/'summary.json').is_file():summary_record=publish.record(target/'summary.json')
    except BaseException as error:custody.errors.append(error_data(error))
    receipt={'protocol':'r0035-publish-adapted-driver/1','status':'DRIVER_RETURNED' if failure is None else 'DRIVER_FAILED',
             'adapter':publish.ADAPTER,'adapterCalls':adapter.calls,'sourceAdmission':admission,'preadmission':preadmission_record,
             'sources':sources,'isolation':namespace_record,'actualPython':sys.executable,
             'actualOriginalArgv':[runtime['python'],str(driver_path),*native],'originalSources':original_sources,
             'trialCalls':custody.calls,'trials':custody.trials,'errors':custody.errors,'originalException':failure,
             'continuationVeto':None if custody.veto is None else error_data(custody.veto),'originalSummary':summary_record,
             'nativeQualification':'UNCHANGED_ORIGINAL_REPORT_ONLY','speed':'NOT_ESTABLISHED','humanAcceptance':'OUTSTANDING'}
    publish.save(args.evidence/'driver.json',receipt)
    if custody.veto is not None:return 86
    return 1 if failure is not None or custody.errors else 0


if __name__=='__main__':raise SystemExit(main())
