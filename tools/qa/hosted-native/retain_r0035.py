"""Retain private partial evidence around the exact original R0035 functions.

No driver loop or admission rule is copied. Original result files and exceptions
remain authoritative. Instrumentation I/O affects driver timing measurements.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time
import traceback
from urllib.parse import urlsplit

HERE = Path(__file__).resolve().parent
PIN_PATH = HERE/'retention-pins.json'
PINS = json.loads(PIN_PATH.read_text())


def digest(data):
    return hashlib.sha256(data).hexdigest()


def error_data(error):
    return {'name': type(error).__name__, 'message': str(error),
            'traceback': ''.join(traceback.format_exception(type(error), error, error.__traceback__))}


class Journal:
    def __init__(self, directory):
        self.directory = Path(directory).resolve()
        self.directory.mkdir(mode=0o700)
        fd = os.open(self.directory/'events.jsonl', os.O_WRONLY|os.O_CREAT|os.O_EXCL, 0o600)
        self.stream = os.fdopen(fd, 'w')
        self.sequence = 0
        self.retention_error = None
        self.record('instrumentation', protocol='salah-native-evidence-retention/1', recipe='R0035',
                    interpretation='Supplemental retention only; original results and failures remain authoritative.',
                    overhead='Host serialization, hashing, fsync and screenshot copies affect timing. Failure captures follow the fault; no presentation timestamps.')

    def record(self, event, **fields):
        self.sequence += 1
        row = dict(sequence=self.sequence, utcNs=time.time_ns(), monotonicNs=time.monotonic_ns(), event=event, **fields)
        self.stream.write(json.dumps(row, default=str)+'\n')
        self.stream.flush()
        os.fsync(self.stream.fileno())
        return row

    def preserve(self, event, **fields):
        # Preserve a primary driver exception if diagnostic retention also fails.
        try:
            self.record(event, **fields)
        except Exception as error:
            self.retention_error = error

    def blob(self, name, data):
        fd = os.open(self.directory/name, os.O_WRONLY|os.O_CREAT|os.O_EXCL, 0o600)
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        return {'file': name, 'bytes': len(data), 'sha256': digest(data)}

    def close(self):
        self.stream.close()


def verify_inputs(driver):
    directory = Path(driver).resolve().parent
    rows = []
    for name in ('native_trials.py', 'trial_admission.py', 'trial_clock.js'):
        file = Path(driver).resolve() if name == 'native_trials.py' else directory/name
        actual = digest(file.read_bytes())
        if actual != PINS['files']['tools/r0035/'+name]:
            raise ValueError('source digest mismatch: '+name)
        rows.append({'name': 'tools/r0035/'+name, 'file': str(file), 'sha256': actual})
    return rows


def verify_isolation(file):
    if not file:
        raise ValueError('admitted isolation receipt required')
    raw = Path(file).read_bytes()
    receipt = json.loads(raw)
    if (receipt.get('protocol') != 'salah-hosted-native-isolation/1'
            or receipt.get('passed') is not True or receipt.get('browserControl', {}).get('passed') is not True):
        raise ValueError('admitted isolation receipt required')
    if os.getuid() <= 0 or receipt.get('uid') != os.getuid():
        raise ValueError('nonroot receipt identity mismatch')
    if (receipt.get('netns') != os.readlink('/proc/self/ns/net') or not receipt.get('outerNetns')
            or receipt['netns'] == receipt['outerNetns']):
        raise ValueError('isolation receipt namespace mismatch')
    return {'file': str(file), 'sha256': digest(raw)}


def load_driver(file):
    verify_inputs(file)
    file = Path(file).resolve()
    prior = sys.modules.get('trial_admission')
    old_bytecode = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        def exact_source(module, path, name):
            source = path.read_bytes()
            if digest(source) != PINS['files']['tools/r0035/'+name]:
                raise ValueError('source digest mismatch: '+name)
            # A matching source-file hash must never admit stale/forged .pyc.
            exec(compile(source, str(path), 'exec'), module.__dict__)
        helper_spec = importlib.util.spec_from_file_location('trial_admission', file.with_name('trial_admission.py'))
        helper = importlib.util.module_from_spec(helper_spec)
        sys.modules['trial_admission'] = helper
        exact_source(helper, file.with_name('trial_admission.py'), 'trial_admission.py')
        spec = importlib.util.spec_from_file_location('retained_original_r0035', file)
        driver = importlib.util.module_from_spec(spec)
        exact_source(driver, file, 'native_trials.py')
        return driver
    finally:
        sys.dont_write_bytecode = old_bytecode
        if prior is None:
            sys.modules.pop('trial_admission', None)
        else:
            sys.modules['trial_admission'] = prior


def allowed_continuation(url, base):
    parsed, local = urlsplit(url), urlsplit(base)
    return (parsed.scheme in ('data', 'blob') or
            parsed.scheme in ('http', 'https') and parsed.scheme == local.scheme and parsed.netloc == local.netloc
            and parsed.hostname in ('127.0.0.1', 'localhost', '::1'))


class Retention:
    def __init__(self, directory):
        self.journal = Journal(directory)
        self.current = None
        self.trials = 0
        self.shots = 0
        self.requests = 0
        self.continuation_veto = None

    def record(self, event, **fields):
        return self.journal.record(event, trial=self.current['number'] if self.current else None, **fields)

    def failure(self, event, error, **fields):
        if self.current is not None and 'failure' not in self.current:
            self.current['failure'] = error
        self.journal.preserve(event, trial=self.current['number'] if self.current else None, error=error_data(error), **fields)

    def begin_trial(self, label, engine, base, out, arm, args):
        self.trials += 1
        self.current = {'number': self.trials, 'base': base, 'label': label, 'pages': []}
        self.record('trial-started', arm=label, engine=engine, base=base, output=str(out),
                    sourceArm=arm, arguments=vars(args))
        return self.current

    def install(self, driver):
        self.original_trial, self.original_assess = driver.trial, driver.assess
        self.driver = driver

        def assess(*args, **kwargs):
            names = ('before','after','trace','publication','scene','limits','motion','clock','probe','label','active')
            self.record('admission-called', inputs=dict(zip(names,args)), keywordInputs=kwargs)
            try:
                result = self.original_assess(*args, **kwargs)
            except BaseException as error:
                self.failure('admission-threw', error)
                raise
            self.current['admission_failed'] = result['verdict'] != 'passed'
            self.record('admission-returned', result=result)
            return result

        def trial(browser, engine, base, arm, label, out, args):
            self.begin_trial(label, engine, base, out, arm, args)
            try:
                result = self.original_trial(BrowserProxy(browser,self), engine, base, arm, label, out, args)
            except BaseException as error:
                partial = {}
                cursor = error.__traceback__
                while cursor:
                    if cursor.tb_frame.f_code is self.original_trial.__code__:
                        partial = {key:cursor.tb_frame.f_locals[key] for key in
                                   ('before','after','trace','observations','elapsed','errors','result','probe')
                                   if key in cursor.tb_frame.f_locals}
                    cursor = cursor.tb_next
                self.journal.preserve('trial-threw', trial=self.current['number'],
                                      error=error_data(error), partial=partial)
                raise
            self.record('trial-returned', result=result)
            return result

        driver.assess, driver.trial = assess, trial
        return driver

    def screenshot(self, target, args, kwargs, kind):
        self.shots += 1
        shot = self.shots
        requested = time.monotonic_ns()
        self.record('screenshot-requested', shot=shot, kind=kind, requestNs=requested)
        raw_call = time.monotonic_ns()
        try:
            data = target.screenshot(*args, **kwargs)
        except BaseException as error:
            self.failure('screenshot-threw' if kind == 'original' else 'diagnostic-failed', error)
            raise
        received = time.monotonic_ns()
        try:
            file = self.journal.blob(f'trial-{self.current["number"]:02}-shot-{shot}.png', data)
            self.record('screenshot-received', shot=shot, kind=kind, requestNs=requested, rawCallNs=raw_call, receiptNs=received, **file)
        except BaseException as error:
            self.failure('screenshot-retention-failed', error)
            raise
        return data

    def wrap_context(self, raw, active):
        return ContextProxy(raw, self, active)


class Proxy:
    def __init__(self, raw, owner):
        self.raw, self.owner = raw, owner
    def __getattr__(self, name):
        return getattr(self.raw, name)


class BrowserProxy(Proxy):
    def new_context(self, *args, **kwargs):
        if kwargs.get('service_workers') != 'block':
            raise ValueError('original service-worker block required')
        return self.owner.wrap_context(self.raw.new_context(*args, **kwargs), self.owner.current)


class ContextProxy(Proxy):
    def __init__(self, raw, owner, active):
        super().__init__(raw, owner)
        self.active, self.route_installed = active, False
    def route(self, pattern, handler, *args, **kwargs):
        if pattern != '**/*':
            raise ValueError('catch-all route required')
        def wrapped(route):
            try:
                return handler(RouteProxy(route, self.owner, self.active['base']))
            except BaseException as error:
                self.owner.failure('route-handler-threw', error)
                raise
        result = self.raw.route(pattern, wrapped, *args, **kwargs)
        self.route_installed = True
        self.owner.record('route-installed', pattern=pattern)
        return result
    def unroute(self, *args, **kwargs):
        raise ValueError('route removal forbidden during retention')
    unroute_all = unroute
    def new_page(self, *args, **kwargs):
        if not self.route_installed:
            raise ValueError('install catch-all route before creating a page')
        raw = self.raw.new_page(*args, **kwargs)
        self.active['pages'].append(raw)
        raw.on('pageerror', lambda error:self.owner.journal.preserve('pageerror', trial=self.active['number'], error=error_data(error)))
        self.owner.record('page-created')
        return PageProxy(raw, self.owner)
    def close(self, *args, **kwargs):
        caller = sys._getframe(1)
        if caller.f_code is self.owner.original_trial.__code__:
            partial = {key:caller.f_locals[key] for key in
                       ('before','after','trace','observations','elapsed','errors','probe') if key in caller.f_locals}
            self.owner.journal.preserve('trial-context-finally', trial=self.active['number'], partial=partial)
        del caller
        error = sys.exc_info()[1]
        if error is not None:
            self.owner.failure('context-unwinding', error)
        if (error is not None or self.active.get('failure') or self.active.get('admission_failed')) and self.active['pages']:
            try:
                self.owner.screenshot(self.active['pages'][-1], (), {'timeout':10000}, 'failure-diagnostic')
            except BaseException:
                pass
        try:
            result = self.raw.close(*args, **kwargs)
            self.owner.journal.preserve('context-closed', trial=self.active['number'])
            return result
        except BaseException as close_error:
            self.owner.failure('context-close-threw', close_error)
            raise


class RouteProxy(Proxy):
    def __init__(self, raw, owner, base):
        super().__init__(raw, owner)
        self.base = base
        owner.requests += 1
        self.request_id = owner.requests
        owner.record('request', requestId=self.request_id, url=raw.request.url,
                     method=raw.request.method, resourceType=raw.request.resource_type)
    def action(self, name, *args, **kwargs):
        url = kwargs.get('url', self.raw.request.url)
        refused = name == 'continue_' and not allowed_continuation(url,self.base)
        fields = {'requestId':self.request_id, 'url':url, 'action':name, 'refused':refused}
        self.owner.record('request-action', **fields)
        if refused:
            error = ValueError('external continuation refused by retention guard')
            self.owner.continuation_veto = error
            self.owner.failure('external-continuation-vetoed', error, **fields)
            try:
                self.raw.abort()
                self.owner.record('request-action-completed', **{**fields,'action':'abort','guard':True})
            except BaseException as abort_error:
                self.owner.failure('request-action-failed', abort_error, **fields)
            raise error
        try:
            result = getattr(self.raw,name)(*args, **kwargs)
        except BaseException as error:
            self.owner.failure('request-action-failed', error, **fields)
            raise
        self.owner.record('request-action-completed', **fields)
        return result
    def continue_(self, *args, **kwargs): return self.action('continue_',*args,**kwargs)
    def fulfill(self, *args, **kwargs): return self.action('fulfill',*args,**kwargs)
    def abort(self, *args, **kwargs): return self.action('abort',*args,**kwargs)
    def fetch(self, *args, **kwargs): raise ValueError('unsupported route bypass in retention successor')
    fallback = fetch


class PageProxy(Proxy):
    def evaluate(self, expression, *args, **kwargs):
        try:
            value = self.raw.evaluate(expression,*args,**kwargs)
        except BaseException as error:
            self.owner.failure('page-operation-threw',error)
            raise
        self.owner.record('evaluation-returned', expressionSha256=digest(expression.encode()), value=value)
        return value
    def locator(self, *args, **kwargs):
        return LocatorProxy(self.raw.locator(*args, **kwargs),self.owner)
    def screenshot(self, *args, **kwargs):
        return self.owner.screenshot(self.raw,args,kwargs,'original')
    def __getattr__(self, name):
        value = getattr(self.raw,name)
        if name not in ('goto','wait_for_function','wait_for_timeout'):
            return value
        def observed(*args, **kwargs):
            try:
                return value(*args, **kwargs)
            except BaseException as error:
                self.owner.failure('page-operation-threw',error)
                raise
        return observed


class LocatorProxy(Proxy):
    def screenshot(self, *args, **kwargs):
        return self.owner.screenshot(self.raw,args,kwargs,'original')


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--driver', required=True, type=Path)
    parser.add_argument('--evidence', required=True, type=Path)
    if '--' not in argv:
        parser.error('separate unchanged original arguments with --')
    separator = argv.index('--')
    args, original = parser.parse_args(argv[:separator]), argv[separator+1:]
    if len(original) < 2:
        parser.error('original plan and fresh output required')
    sources = verify_inputs(args.driver)
    isolation = verify_isolation(os.environ.get('SALAH_HOSTED_NATIVE_ISOLATION_RECEIPT'))
    output = Path(original[1]).resolve()
    if output.exists() or args.evidence.resolve() == output:
        raise ValueError('distinct fresh original and retention outputs required')
    os.umask(0o077)
    retained = Retention(args.evidence)
    retained.record('sources', sources=sources, isolation=isolation,
                    wrapperSha256=digest(Path(__file__).read_bytes()), pinsSha256=digest(PIN_PATH.read_bytes()),
                    researchCommit=PINS['researchCommit'], originalArgv=original)
    try:
        driver = retained.install(load_driver(args.driver))
        sys.argv = [str(args.driver.resolve()), *original]
        driver.main()
        retained.record('driver-returned', originalSummaryExists=(output/'summary.json').is_file())
        if retained.continuation_veto is not None:
            raise retained.continuation_veto
        if retained.journal.retention_error is not None:
            raise retained.journal.retention_error
    except BaseException as error:
        retained.failure('driver-threw',error)
        if retained.continuation_veto is not None:
            raise SystemExit(86) from error
        raise
    finally:
        pending_error = sys.exc_info()[1]
        try:
            retained.journal.close()
        except Exception as cleanup_error:
            retained.journal.retention_error = retained.journal.retention_error or cleanup_error
            # The journal may already be closed. Keep this secondary diagnostic
            # in the coordinator's private stderr without replacing a primary
            # driver exception or the reserved continuation-veto SystemExit.
            try:
                print('R0035 retention cleanup failed:', repr(cleanup_error), file=sys.stderr)
            except Exception:
                pass
            if pending_error is None or isinstance(pending_error, SystemExit) and pending_error.code in (None, 0):
                raise


if __name__ == '__main__':
    main()
