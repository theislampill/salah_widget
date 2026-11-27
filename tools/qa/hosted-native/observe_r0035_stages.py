"""Read bounded R0035 stage traces after each unchanged original trial interval.

This entry admits a distinctly identified diagnostic derivative. It retains
separate observations; it never rewrites trial.json or the original verdicts.
No screenshot, per-frame host I/O or repeated producer polling is added.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import traceback
import types

import r0035_stage_materialize as material

READ_STAGES = '() => window.R0035Lab?.observeStages?.() ?? null'
MAIN_CLOCK = 'page-performance-now-ms'
WORKER_CLOCK = 'worker-performance-now-ms'


def error_data(error):
    return {'type': type(error).__name__, 'message': str(error),
            'traceback': ''.join(traceback.format_exception(type(error), error, error.__traceback__))}


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def elapsed(first, last):
    if first is None or last is None:
        return None
    material.need(first['clockDomain'] == last['clockDomain'], 'mixed clock domains cannot be subtracted')
    material.need(finite(first['at']) and finite(last['at']) and last['at'] >= first['at'], 'invalid same-domain interval')
    return last['at']-first['at']


def inspect(trace):
    """Validate bounded structure and derive only same-domain intervals."""
    material.need(isinstance(trace, dict) and trace.get('protocol') == 'r0035-stage-observation/1', 'stage observation missing')
    material.need(trace.get('clockDomain') == MAIN_CLOCK and trace.get('limit') == 2048, 'stage main clock or bound mismatch')
    material.need(trace.get('overflow') is False, 'stage observation overflow')
    events = trace.get('events')
    material.need(isinstance(events, list) and 0 < len(events) <= 2048, 'stage event population missing or invalid')
    material.need(events[0].get('kind') == 'installed', 'stage startup observation missing')
    prior = -math.inf
    for row in events:
        material.need(isinstance(row, dict) and finite(row.get('at')) and row['at'] >= prior, 'stage main clock order invalid')
        prior = row['at']
    owners = {e['epoch']: e for e in events if e['kind'] == 'owner'}
    material.need(len(owners) == sum(e['kind'] == 'owner' for e in events), 'duplicate stage owner epoch')
    rows = []
    point = lambda event, clock: None if event is None else {'at': event['at'], 'clockDomain': clock}
    for epoch, owner in owners.items():
        def first(kind):
            return next((e for e in events if e['kind'] == kind and e.get('messageEpoch', e.get('epoch')) == epoch), None)
        dispatch, built, sent = [first(k) for k in ('prepare-dispatch-start','prepare-message-built','prepare-dispatch-returned')]
        reply, requested, publication = [first(k) for k in ('prepare-reply','first-sample-request','first-publication')]
        for kind in ('first-sample-request','first-publication'):
            material.need(sum(e['kind'] == kind and e.get('epoch') == epoch for e in events) <= 1, 'duplicate first stage marker')
        durations = {}
        for name, a, b in [('ownerToDispatch',owner,dispatch),('messageConstruction',dispatch,built),
                           ('postMessageCall',built,sent),('dispatchToReplyInclusive',dispatch,reply),
                           ('replyToFirstRequest',reply,requested),('firstRequestToPublication',requested,publication),
                           ('ownerToFirstPublication',owner,publication)]:
            durations[name] = elapsed(point(a, MAIN_CLOCK), point(b, MAIN_CLOCK))
        worker = reply.get('worker') if reply else None
        worker_durations = {}; worker_marks = None
        if worker is not None:
            material.need(isinstance(worker, dict) and worker.get('protocol') == 'r0035-worker-stages/1'
                          and worker.get('clockDomain') == WORKER_CLOCK and worker.get('epoch') == epoch, 'worker stage custody mismatch')
            worker_marks = worker.get('marks')
            material.need(isinstance(worker_marks, list) and 1 <= len(worker_marks) <= 16, 'worker stage population invalid')
            sequence = ['received','catalogue-start','catalogue-ready','source-verified','stars-prepared','replay-prepared',
                        'nominal-verified','census-complete','candidate-returned','ready-post']
            kinds = [mark.get('kind') for mark in worker_marks if isinstance(mark,dict)]
            material.need(kinds == sequence if reply['op'] == 'ready' else
                          kinds[-1:] == ['failed'] and kinds[:-1] == sequence[:len(kinds)-1],
                          'worker stage sequence is incomplete or contradictory')
            previous = -math.inf; seen = {}
            for mark in worker_marks:
                material.need(isinstance(mark, dict) and finite(mark.get('at')) and mark['at'] >= previous, 'worker stage clock order invalid')
                material.need(mark.get('kind') not in seen, 'duplicate worker stage marker')
                previous = mark['at']; seen[mark['kind']] = mark
            for name, a, b in [('catalogueAcquisition','catalogue-start','catalogue-ready'),
                               ('sourceVerification','catalogue-ready','source-verified'),
                               ('stellarPreparation','source-verified','stars-prepared'),
                               ('replayPreparation','stars-prepared','replay-prepared'),
                               ('nominalCheck','replay-prepared','nominal-verified'),
                               ('census','nominal-verified','census-complete'),('receivedToReadyPost','received','ready-post')]:
                worker_durations[name] = elapsed(point(seen.get(a),WORKER_CLOCK),point(seen.get(b),WORKER_CLOCK))
        elif reply and reply['op'] == 'ready':
            raise ValueError('prepared reply has no worker stage observation')
        later = next((e for e in events if e['kind'] == 'owner' and e['epoch'] > epoch), None)
        rows.append({'epoch': epoch, 'mainDurationsMs': durations, 'workerDurationsMs': worker_durations,
                     'workerMarks': worker_marks, 'replyAcceptedForCurrentEpoch': None if not reply else
                     reply['activeEpoch'] == epoch and not reply['terminal'],
                     'supersededWithoutObservedDispatch': dispatch is None and later is not None,
                     'firstPublicationObserved': publication is not None})
    return {'protocol': 'r0035-stage-intervals/1', 'epochs': rows,
            'clockRule': 'Subtract only within one page clock or one worker preparation trace; no cross-domain residual is a measured transfer latency.',
            'nativeQualification': 'UNCHANGED_ORIGINAL_REPORT_ONLY', 'humanAcceptance': 'OUTSTANDING'}


class Proxy:
    def __init__(self, raw, owner):
        self.raw, self.owner = raw, owner
    def __getattr__(self, name):
        return getattr(self.raw, name)


class Route(Proxy):
    def __init__(self, raw, owner, trial):
        super().__init__(raw, owner); self.trial = trial
    def continue_(self, *args, **kwargs):
        url = kwargs.get('url', self.raw.request.url)
        if not self.owner.loader.allowed_continuation(url, self.trial['base']):
            error = ValueError('external continuation prevented by stage observation guard')
            self.owner.veto = error; self.trial['continuationVeto'] = {'url': url, 'error': error_data(error)}
            try:
                self.raw.abort()
            except BaseException as abort_error:
                self.trial['abortError'] = error_data(abort_error)
            raise error
        return self.raw.continue_(*args, **kwargs)
    def fetch(self, *args, **kwargs):
        error = ValueError('unsupported route bypass during stage observation')
        self.owner.errors.append(error_data(error)); raise error
    fallback = fetch


class Context(Proxy):
    def __init__(self, raw, owner, trial):
        super().__init__(raw, owner); self.trial, self.routed = trial, False
    def route(self, pattern, handler, *args, **kwargs):
        material.need(pattern == '**/*', 'original catch-all route required')
        result = self.raw.route(pattern, lambda route: handler(Route(route,self.owner,self.trial)), *args, **kwargs)
        self.routed = True; return result
    def unroute(self, *args, **kwargs):
        error = ValueError('route removal refused during stage observation')
        self.owner.errors.append(error_data(error)); raise error
    unroute_all = unroute
    def new_page(self, *args, **kwargs):
        material.need(self.routed, 'install catch-all route before creating page')
        page = self.raw.new_page(*args, **kwargs); self.trial['pages'].append(page); return page
    def close(self, *args, **kwargs):
        primary = sys.exc_info()[1]
        if primary is not None:
            self.trial['unwinding'] = error_data(primary)
        # Original normal path has stopped measurement and written trial.json
        # before entering its finally. A fault path yields the available prefix.
        for page in self.trial['pages']:
            try:
                trace = page.evaluate(READ_STAGES)
            except BaseException as error:
                detail = error_data(error)
                self.trial['observations'].append({'status': 'UNAVAILABLE', 'trace': None, 'extractionError': detail})
                self.owner.errors.append(detail)
                continue
            # Custody of retrieved bytes precedes interpretation. An invalid or
            # overflowed prefix is evidence, even though it supplies no verdict.
            observation = {'status': 'INCOMPLETE', 'trace': trace}
            self.trial['observations'].append(observation)
            try:
                if self.trial['arm'] == 'main':
                    material.need(trace is None, 'unexpected instrumented main')
                    observation['status'] = 'NOT_APPLICABLE'
                else:
                    observation.update(intervals=inspect(trace), status='OBSERVED')
            except BaseException as error:
                observation['validationError'] = error_data(error)
                self.owner.errors.append(observation['validationError'])
        try:
            result = self.raw.close(*args, **kwargs); self.trial['contextClosed'] = True; return result
        except BaseException as error:
            self.trial['closeError'] = error_data(error); raise


class Browser(Proxy):
    def new_context(self, *args, **kwargs):
        material.need(kwargs.get('service_workers') == 'block', 'original service-worker block required')
        return Context(self.raw.new_context(*args,**kwargs),self.owner,self.owner.current)


class Observer:
    def __init__(self, directory, loader):
        self.directory = directory.resolve(); self.directory.mkdir(mode=0o700)
        self.loader, self.current = loader, None
        self.trials, self.errors, self.veto, self.receipts = 0, [], None, []
    def install(self, driver):
        original = driver.trial
        def trial(browser, engine, base, arm, label, out, args):
            self.trials += 1
            active = self.current = {'ordinal': self.trials, 'arm': label, 'base': base, 'pages': [], 'observations': [],
                                     'protocol': 'r0035-stage-trial/1', 'timingClass': 'instrumented-stage-observation',
                                     'originalOutput': str(out), 'originalArguments': json.loads(json.dumps(vars(args),default=str)), 'contextClosed': False}
            try:
                return original(Browser(browser,self),engine,base,arm,label,out,args)
            except BaseException as error:
                active['originalException'] = error_data(error); raise
            finally:
                # No writes or fsync occur during the measured interval. Keep a
                # failed extraction separate from the original exception/result.
                try:
                    active.pop('pages')
                    report = Path(out)/'trial.json'
                    if report.is_file():
                        data = report.read_bytes(); active['originalReport'] = {'path': str(report), 'sha256': hashlib.sha256(data).hexdigest()}
                        try:
                            body = json.loads(data); active['originalMeasuredWindow'] = {k: body['trace'][k] for k in ('start','end')}
                        except (ValueError, KeyError, TypeError):
                            active['originalMeasuredWindow'] = None
                    if not active['observations']:
                        raise ValueError('original trial produced no stage extraction')
                    path = self.directory/f'trial-{self.trials:03}-{label}.json'
                    material.write_json(path, active)
                    self.receipts.append({'ordinal': self.trials, 'arm': label, 'path': str(path),
                                          'sha256': material.digest(path.read_bytes())})
                except BaseException as error:
                    self.errors.append(error_data(error))
        driver.trial = trial; return driver


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('driver','identity','preparation-process','evidence'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--preparation-sha256', required=True)
    if '--' not in argv:
        parser.error('separate original driver arguments with --')
    separator = argv.index('--'); args = parser.parse_args(argv[:separator]); original = argv[separator+1:]
    if len(original) < 2:
        parser.error('instrumented plan and fresh original output required')
    loader = material.support()
    isolation = loader.verify_isolation(os.environ.get('SALAH_HOSTED_NATIVE_ISOLATION_RECEIPT'))
    sources = loader.verify_inputs(args.driver)
    preparation = material.preparation_process(args.preparation_process, args.driver, Path(original[0]), args.identity,
                                               args.preparation_sha256)
    output = Path(original[1]).resolve(); evidence = args.evidence.resolve()
    material.need(not output.exists() and not evidence.exists() and output != evidence and output not in evidence.parents and evidence not in output.parents,
                  'separate fresh original and stage evidence directories required')
    driver = loader.load_driver(args.driver)
    checker = types.SimpleNamespace(check_plan=driver.check_plan, verify_reconstructed_flags=driver.verify_reconstructed_flags)
    plan = json.loads(Path(original[0]).read_bytes())
    identity = material.admit(plan,checker,args.identity)
    # The dispatcher is explicitly for a new plan protocol. The original source
    # checker still executes on the intact original plan, and rejects the changed
    # derivative if asked to admit it as an unmodified reconstruction.
    def admitted_plan(candidate):
        material.need(candidate == plan, 'instrumented plan changed after source admission')
        return identity
    driver.check_plan = admitted_plan
    os.umask(0o077); observer = Observer(evidence,loader); observer.install(driver)
    prior_argv = sys.argv; primary = None
    try:
        sys.argv = [str(args.driver.resolve()),*original]; driver.main()
    except BaseException as error:
        primary = error
    finally:
        sys.argv = prior_argv
        try:
            summary = output/'summary.json'
            record = {'protocol': 'r0035-stage-driver/1', 'status': 'INCOMPLETE' if primary or observer.errors or observer.veto else 'OBSERVED',
                      'sources': sources, 'isolation': isolation, 'originalArgv': original, 'trials': observer.trials,
                      'preparation': preparation, 'observations': observer.receipts,
                      'originalException': error_data(primary) if primary else None, 'observationErrors': observer.errors,
                      'continuationVetoed': observer.veto is not None, 'timingClass': 'instrumented-stage-observation',
                      'identitySha256': material.digest(args.identity.read_bytes()), 'wrapperSha256': material.digest(Path(__file__).read_bytes()),
                      'originalSummary': {'path': str(summary), 'sha256': material.digest(summary.read_bytes())} if summary.is_file() else None,
                      'nativeQualification': 'UNCHANGED_ORIGINAL_REPORT_ONLY'}
            material.write_json(evidence/'driver.json',record)
        except BaseException as error:
            observer.errors.append(error_data(error))
            try: print('Stage observation finalization failed:',repr(error),file=sys.stderr)
            except Exception: pass
    if observer.veto is not None:
        raise SystemExit(86) from primary
    if primary is not None and not (isinstance(primary,SystemExit) and primary.code in (None,0) and observer.errors):
        raise primary.with_traceback(primary.__traceback__)
    if observer.errors:
        raise RuntimeError('Stage observation incomplete; original reports remain unchanged')


if __name__ == '__main__': main()
