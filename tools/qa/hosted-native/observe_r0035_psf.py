"""Explicit operational adapter for a separately admitted PSF source pair.

The original driver files and scientific predicates are byte-exact. Operation
is adapted: a private module's plan checker and trial entry are intercepted.
Every interception is identified in source and retained receipts. No original
report, summary, assessment function, clock or renderer source is rewritten.
"""
import argparse
import json
import os
from pathlib import Path
import sys
import traceback

import r0035_psf as psf
import r0035_stage_materialize as original
import r003f_matrix_campaign as isolation


def error_data(error):
    return {'type':type(error).__name__,'message':str(error),
            'traceback':''.join(traceback.format_exception(type(error),error,error.__traceback__))}


class PlanAdapter:
    """Named, invocation-local admission adapter; never edits global admission."""
    def __init__(self,driver,reference,derived,role,current):
        psf.need(role in psf.ROLES,'identified PSF plan role required')
        self.driver,self.reference,self.expected=driver,reference,reference if role=='reference' else derived
        self.original_check,self.current,self.calls=driver.check_plan,current,0

    def __call__(self,plan):
        psf.need(psf.same(plan,self.expected),'PSF adapter accepts only its canonical identified plan')
        self.current()
        self.original_check(self.reference)
        self.driver.verify_reconstructed_flags(plan['arms'])
        for name in psf.ARMS:
            arm=plan['arms'][name]
            self.driver.producer_flags(name,arm.get('flags',''),True)
        self.calls+=1


class Proxy:
    def __init__(self,raw,owner):self.raw,self.owner=raw,owner
    def __getattr__(self,name):return getattr(self.raw,name)


class Route(Proxy):
    def continue_(self,*args,**kwargs):
        url=kwargs.get('url',self.raw.request.url)
        if not self.owner.loader.allowed_continuation(url,self.owner.current['base']):
            error=ValueError('PSF adapter prevented external continuation before the real action')
            self.owner.veto=error;self.owner.current['continuationVeto']={'url':url,'error':error_data(error)}
            try:self.raw.abort()
            except BaseException as failure:self.owner.current['abortError']=error_data(failure)
            raise error
        return self.raw.continue_(*args,**kwargs)
    def fetch(self,*args,**kwargs):
        error=ValueError('PSF adapter refuses route bypass')
        self.owner.errors.append(error_data(error));raise error
    fallback=fetch


class Context(Proxy):
    def __init__(self,raw,owner):super().__init__(raw,owner);self.routed=False
    def route(self,pattern,handler,*args,**kwargs):
        psf.need(pattern=='**/*','original catch-all route required before PSF page')
        result=self.raw.route(pattern,lambda route:handler(Route(route,self.owner)),*args,**kwargs)
        self.routed=True;self.owner.current['catchAllRoute']=True;return result
    def unroute(self,*args,**kwargs):
        error=ValueError('PSF adapter refuses route removal');self.owner.errors.append(error_data(error));raise error
    unroute_all=unroute
    def new_page(self,*args,**kwargs):
        psf.need(self.routed,'original catch-all route must precede page creation')
        self.owner.current['pages']+=1;return self.raw.new_page(*args,**kwargs)
    def close(self,*args,**kwargs):
        primary=sys.exc_info()[1]
        if primary is not None:self.owner.current['unwinding']=error_data(primary)
        try:
            result=self.raw.close(*args,**kwargs);self.owner.current['contextClosed']=True;return result
        except BaseException as error:
            self.owner.current['closeError']=error_data(error);raise


class Browser(Proxy):
    def new_context(self,*args,**kwargs):
        psf.need(not args and psf.same(kwargs,{'viewport':{'width':360,'height':570},'device_scale_factor':1,
                    'timezone_id':'UTC','reduced_motion':'no-preference','service_workers':'block'}),
                 'original PSF native context controls differ')
        self.owner.current['contextOptions']=kwargs
        return Context(self.raw.new_context(*args,**kwargs),self.owner)


class Custody:
    def __init__(self,directory,loader,role):
        self.directory,self.loader,self.role=Path(directory),loader,role
        self.current=None;self.trials=[];self.errors=[];self.veto=None;self.calls=0
    def install(self,driver):
        original_trial=driver.trial
        def trial(browser,engine,base,arm,label,out,args):
            self.calls+=1;ordinal=self.calls
            current=self.current={'protocol':'r0035-psf-adapted-trial/1','ordinal':ordinal,'role':self.role,
                'arm':label,'base':base,'sourceArm':arm,'engine':engine,'browserVersion':browser.version,
                'originalArguments':json.loads(json.dumps(vars(args),default=str)),
                'originalOutput':str(out),'pages':0,'catchAllRoute':False,'contextClosed':False}
            try:return original_trial(Browser(browser,self),engine,base,arm,label,out,args)
            except BaseException as error:current['originalException']=error_data(error);raise
            finally:
                try:
                    report=Path(out)/'trial.json'
                    if report.is_file():current['originalReport']=psf.record(report)
                    path=self.directory/f'trial-{ordinal:03}-{label}.json';psf.save(path,current)
                    self.trials.append({'ordinal':ordinal,'arm':label,'receipt':psf.record(path)})
                except BaseException as error:self.errors.append(error_data(error))
        driver.trial=trial


def main(argv=None):
    argv=list(sys.argv[1:] if argv is None else argv)
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--task',type=Path,required=True);parser.add_argument('--role',choices=psf.ROLES,required=True)
    parser.add_argument('--preadmission',type=Path,required=True);parser.add_argument('--evidence',type=Path,required=True)
    psf.need('--' in argv,'exact original native argument delimiter required')
    delimiter=argv.index('--');args=parser.parse_args(argv[:delimiter]);native=argv[delimiter+1:]
    os.umask(0o077);task=args.task.absolute();p=psf.paths(task);runtime=psf.load(task/'runtime.json')
    psf.need(runtime.get('python')==sys.executable,'actual PSF Python differs from acquired runtime')
    psf.source_pins();psf.runtime_authority(task,runtime)
    psf.need(args.preadmission==task/'capture'/('r0035-psf-preadmission-'+args.role+'.json'),
             'current lane PSF preadmission path required')
    preadmission=psf.load(args.preadmission)
    admission=psf.admitted_process(preadmission,task,runtime,native=True)
    psf.need(psf.same(psf.record(p['identity']),admission['identity']) and psf.same(psf.source_pins(),admission['sourcePins'])
             and psf.same(psf.caller_sources(),admission.get('callerSources')),
             'PSF source identity changed after actual preadmission')
    identity=psf.load(p['identity']);reference=psf.load(p['referencePlan']);derived=psf.load(p['derivedPlan'])
    psf.need(psf.same(psf.record(p['referencePlan']),admission['referencePlan'])
             and psf.same(psf.record(p['derivedPlan']),admission['derivedPlan'])
             and psf.same(reference,identity['referencePlan'])
             and psf.same(derived,psf.derived_plan(reference,p['candidate'],psf.record(p['identity']))),
             'PSF actual canonical plans changed after current preadmission')
    identifier='r0035-chromium-psf-'+args.role;target=task/'capture/lanes'/identifier
    plan_path=p['referencePlan' if args.role=='reference' else 'derivedPlan']
    expected=[str(plan_path),str(target),*psf.DRIVER_ARGS]
    psf.need(native==expected and args.evidence==target.with_name(identifier+'-custody'),
             'PSF actual role, output or original driver arguments differ')
    psf.need(os.environ.get('PLAYWRIGHT_BROWSERS_PATH')==str(task/'python-browsers'),
             'PSF actual managed Python browser root differs')
    loader=original.support();driver_path=Path(admission['driver'])
    driver=loader.load_driver(driver_path);sources=loader.verify_inputs(driver_path)
    namespace=Path(os.environ.get('SALAH_HOSTED_NATIVE_ISOLATION_RECEIPT',''))
    loader.verify_isolation(namespace);isolation.original_isolation(namespace)
    psf.need(namespace==task/'capture/isolation'/identifier/'receipt.json','PSF actual lane namespace path differs')
    namespace_record=psf.record(namespace);preadmission_record=psf.record(args.preadmission)
    args.evidence.mkdir(mode=0o700)
    custody=Custody(args.evidence,loader,args.role)
    adapter=PlanAdapter(driver,reference,derived,args.role,lambda:psf.pair_files(task,runtime,identity))
    # Explicit local mutation is part of this separately identified entry, not
    # a claim that the original checker admitted changed bytes. No other module
    # or original scientific assessment binding is altered.
    driver.check_plan=adapter;custody.install(driver)
    saved_argv=sys.argv;failure=None
    try:
        sys.argv=[str(driver_path),*native];driver.main()
    except BaseException as error:
        failure=error_data(error)
        # Actual private stderr retains the primary failure even if later
        # receipt I/O also fails, after the original measured interval.
        traceback.print_exception(type(error),error,error.__traceback__,file=sys.stderr)
    finally:sys.argv=saved_argv
    summary=target/'summary.json'
    summary_record=None
    try:
        if summary.is_file():summary_record=psf.record(summary)
    except BaseException as error:custody.errors.append(error_data(error))
    receipt={'protocol':'r0035-psf-adapted-driver/1','status':'DRIVER_RETURNED' if failure is None else 'DRIVER_FAILED',
             'role':args.role,'adapter':psf.ADAPTER,'adapterCalls':adapter.calls,
             'sourceAdmission':admission,'preadmission':preadmission_record,
             'sourcePins':admission['sourcePins'],'isolation':namespace_record,'actualPython':sys.executable,
             'actualOriginalArgv':[runtime['python'],str(driver_path),*native],
             'sources':sources,'trialCalls':custody.calls,'trials':custody.trials,'errors':custody.errors,
             'originalException':failure,'continuationVeto':None if custody.veto is None else error_data(custody.veto),
             'originalSummary':summary_record,
             'nativeQualification':'UNCHANGED_ORIGINAL_REPORT_ONLY','humanAcceptance':'OUTSTANDING'}
    psf.save(args.evidence/'driver.json',receipt)
    if custody.veto is not None:return 86
    return 1 if failure is not None or custody.errors else 0


if __name__=='__main__':raise SystemExit(main())
