"""Host-side fault controls only; no browser or native evidence is produced."""
import importlib.util
import marshal
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace, ModuleType
import unittest
from unittest.mock import patch
import subprocess

HERE = Path(__file__).resolve().parent


class RetentionControls(unittest.TestCase):
    def test_wrapper_exists_before_exercising_evidence_contracts(self):
        self.assertTrue((HERE/'retain_r0035.py').is_file(), 'missing R0035 evidence-retention wrapper')


if (HERE/'retain_r0035.py').is_file():
    import retain_r0035 as retention

    class BrowserTimeout(Exception):
        pass

    def scene():
        box = [2, 3, 20, 10]
        return dict(composed=True, identity='accepted', paused=False, reduced=False, rate=1,
                    clock=dict(wall=True, advancing=False, preview=False, fast=False, chrome=False),
                    utcMs=1000, expectedUtc=1000, sunAlt=-30, dimensions=[325, 530], header=box,
                    footer=box, buckle=box, prayerKeys=['Fajr','Sunrise','Dhuhr','Asr','Maghrib','Isha'],
                    prayersReady=True, rowBoxes=[box]*6, cloudCurrent=True,
                    cloudPublication='eligible-published', fixtureWx={'cloud':0,'code':0},
                    catalogue='controlled-source', cloudSource='hidden', cloudAlpha=0,
                    calendarMoon={}, predicate='active', t=0)

    class FakeRoute:
        def __init__(self, url):
            self.request = SimpleNamespace(url=url, method='GET', resource_type='script')
            self.actions = []
        def continue_(self, **kwargs): self.actions.append('continue')
        def fulfill(self, **kwargs): self.actions.append('fulfill')
        def abort(self, **kwargs): self.actions.append('abort')

    class FakePage:
        def __init__(self, driver, failure=None):
            self.driver, self.failure, self.shots = driver, failure, 0
        def on(self, event, callback): pass
        def goto(self, *args, **kwargs): pass
        def wait_for_function(self, *args, **kwargs):
            if self.failure == 'timeout': raise BrowserTimeout('controlled setup timeout')
        def wait_for_timeout(self, *args, **kwargs): pass
        def locator(self, *args): return self
        def screenshot(self, **kwargs):
            self.shots += 1
            if self.failure == 'diagnostic': raise RuntimeError('controlled capture error')
            return b'controlled-png-bytes'
        def evaluate(self, expression, *args):
            if expression == self.driver.READ: return scene()
            if 'window.__r0035.end=' in expression:
                return dict(start=0,end=2000,frames=list(range(0,2000,16)),
                            states=[dict(scene(),t=100),dict(scene(),t=1100)], publication=None)
            return None

    class FakeContext:
        def __init__(self, page): self.page, self.calls = page, []
        def route(self, pattern, handler): self.calls.append('route'); self.handler=handler
        def add_init_script(self, script): pass
        def new_page(self): self.calls.append('new_page'); return self.page
        def close(self): self.calls.append('close')

    class FakeBrowser:
        version='offline-control'
        def __init__(self, driver, failure=None):
            self.context = FakeContext(FakePage(driver,failure))
        def new_context(self, **kwargs):
            assert kwargs['service_workers']=='block'
            return self.context

    class EvidenceControls(unittest.TestCase):
        def setUp(self):
            self.temp=tempfile.TemporaryDirectory(prefix='star-retention-')
            self.root=Path(self.temp.name)
            self.driver=retention.load_driver(HERE.parent.parent/'r0035/native_trials.py')
            self.retained=retention.Retention(self.root/'evidence')
            self.retained.install(self.driver)
            module=ModuleType('playwright.sync_api'); module.TimeoutError=BrowserTimeout
            self.old_api=sys.modules.get('playwright.sync_api'); sys.modules['playwright.sync_api']=module
            self.args=SimpleNamespace(scene='dark',motion='normal',utc='2026-11-09T00:00:00Z',
                scene_inputs=(-91,-20,'&simWx=0&simCloud=0',''),clock='ordinary',warmup=0,
                capture=False,seconds=15,observe_producer=True,scope='controlled-test',driver_sha256={})
            self.arm={'root':str(self.root),'commit':'a'*40,'flags':''}
        def tearDown(self):
            self.retained.journal.close()
            if self.old_api is None: sys.modules.pop('playwright.sync_api',None)
            else: sys.modules['playwright.sync_api']=self.old_api
            self.temp.cleanup()
        def events(self):
            return [json.loads(line) for line in (self.root/'evidence/events.jsonl').read_text().splitlines()]
        def trial(self,name,browser=None):
            return self.driver.trial(browser or FakeBrowser(self.driver),'chromium','http://127.0.0.1:8765',
                self.arm,'main',self.root/name,self.args)
        def test_original_pass_and_unexpected_admission_failure_preserve_prior_trial(self):
            first=self.trial('one')
            self.assertEqual(first['qualification']['verdict'],'passed')
            self.assertEqual(json.loads((self.root/'one/trial.json').read_text()),first)
            marker=RuntimeError('controlled mid-admission failure')
            def bad_admission(*args): raise marker
            self.retained.original_assess=bad_admission
            browser=FakeBrowser(self.driver)
            with self.assertRaises(RuntimeError) as caught: self.trial('two',browser)
            self.assertIs(caught.exception,marker)
            self.assertFalse((self.root/'two/trial.json').exists())
            events=self.events()
            self.assertEqual(sum(e['event']=='trial-returned' for e in events),1)
            self.assertTrue(any(e['event']=='admission-threw' for e in events))
            self.assertTrue(any(e['event']=='trial-threw' and e['partial']['before']['identity']=='accepted' for e in events))
            self.assertTrue(any(e['event']=='screenshot-received' and e['kind']=='failure-diagnostic' for e in events))
            self.assertEqual(browser.context.calls,['route','new_page','close'])
        def test_original_browser_timeout_result_is_not_promoted(self):
            result=self.trial('timeout',FakeBrowser(self.driver,'timeout'))
            self.assertFalse(result['admitted'])
            self.assertEqual(result['qualification']['verdict'],'indeterminate')
            self.assertEqual(json.loads((self.root/'timeout/trial.json').read_text()),result)
        def test_diagnostic_failure_does_not_replace_original_exception(self):
            marker=ValueError('admission error')
            def fail(*args): raise marker
            self.retained.original_assess=fail
            with self.assertRaises(ValueError) as caught:
                self.trial('failed',FakeBrowser(self.driver,'diagnostic'))
            self.assertIs(caught.exception,marker)
            self.assertTrue(any(e['event']=='diagnostic-failed' for e in self.events()))
        def test_screenshot_bounds_hash_and_bytes_are_durable_before_later_failure(self):
            browser=FakeBrowser(self.driver)
            active=self.retained.begin_trial('main','chromium','http://127.0.0.1:8765',self.root/'unit',self.arm,self.args)
            wrapped=self.retained.wrap_context(browser.context,active)
            wrapped.route('**/*',lambda route:route.abort())
            page=wrapped.new_page()
            data=page.locator('.c').screenshot(timeout=10000)
            event=next(e for e in self.events() if e['event']=='screenshot-received')
            self.assertEqual(event['sha256'],hashlib.sha256(data).hexdigest())
            self.assertEqual((self.root/'evidence'/event['file']).read_bytes(),data)
            self.assertLessEqual(event['requestNs'],event['receiptNs'])
        def test_missing_route_is_refused_before_page_creation(self):
            browser=FakeBrowser(self.driver)
            active=self.retained.begin_trial('main','chromium','http://127.0.0.1:8765',self.root/'unit',self.arm,self.args)
            wrapped=self.retained.wrap_context(browser.context,active)
            with self.assertRaisesRegex(ValueError,'route.*before.*page'): wrapped.new_page()
            self.assertEqual(browser.context.calls,[])
        def test_route_ledger_observes_actions_and_refuses_external_continue(self):
            browser=FakeBrowser(self.driver)
            active=self.retained.begin_trial('main','chromium','http://127.0.0.1:8765',self.root/'unit',self.arm,self.args)
            wrapped=self.retained.wrap_context(browser.context,active)
            wrapped.route('**/*',lambda route:route.continue_())
            bad=FakeRoute('https://unknown.invalid/payload')
            with self.assertRaisesRegex(ValueError,'external continuation'): browser.context.handler(bad)
            self.assertEqual(bad.actions,['abort'])
            good=FakeRoute('http://127.0.0.1:8765/file.js'); browser.context.handler(good)
            self.assertEqual(good.actions,['continue'])
            self.assertTrue(any(e['event']=='request-action' and e.get('refused') for e in self.events()))
        def test_source_drift_and_absent_namespace_receipt_refuse(self):
            altered=self.root/'native_trials.py'; altered.write_text('changed')
            with self.assertRaisesRegex(ValueError,'digest'): retention.verify_inputs(altered)
            with self.assertRaisesRegex(ValueError,'receipt'): retention.verify_isolation(None)
        def test_source_pins_execute_source_bytes_and_ignore_forged_bytecode_cache(self):
            folder=self.root/'source';folder.mkdir()
            source_dir=Path(self.driver.__file__).parent
            for name in ('native_trials.py','trial_admission.py','trial_clock.js'):
                (folder/name).write_bytes((source_dir/name).read_bytes())
            driver=folder/'native_trials.py'
            stat=driver.stat()
            cache=Path(importlib.util.cache_from_source(str(driver)));cache.parent.mkdir()
            code=compile('raise RuntimeError("forged cached driver executed")',str(driver),'exec')
            header=importlib.util.MAGIC_NUMBER+b'\0'*4+int(stat.st_mtime).to_bytes(4,'little')+stat.st_size.to_bytes(4,'little')
            cache.write_bytes(header+marshal.dumps(code))
            loaded=retention.load_driver(driver)
            self.assertEqual(loaded.trial.__code__.co_name,'trial')
        def test_actual_failed_admission_remains_failed_and_original_report_is_preserved(self):
            browser=FakeBrowser(self.driver)
            evaluate=browser.context.page.evaluate
            def observed(expression,*args):
                value=evaluate(expression,*args)
                if expression==self.driver.READ: value['prayersReady']=False
                return value
            browser.context.page.evaluate=observed
            result=self.trial('rejected',browser)
            self.assertEqual(result['qualification']['verdict'],'failed')
            self.assertFalse(result['admitted'])
            self.assertEqual(json.loads((self.root/'rejected/trial.json').read_text()),result)
        def test_original_capture_metadata_and_png_survive_mid_admission_exception(self):
            self.args.capture=True
            moments=iter([0,0,1000000,2000000,15000000000,15000000000])
            self.driver.time=SimpleNamespace(monotonic_ns=lambda:next(moments))
            marker=RuntimeError('controlled capture-lane admission failure')
            def fail(*args): raise marker
            self.retained.original_assess=fail
            with self.assertRaises(RuntimeError) as caught: self.trial('captured')
            self.assertIs(caught.exception,marker)
            self.assertEqual((self.root/'captured/00000.png').read_bytes(),b'controlled-png-bytes')
            self.assertFalse((self.root/'captured/trial.json').exists())
            event=next(e for e in self.events() if e['event']=='trial-threw')
            self.assertEqual(event['partial']['observations'][0]['startMs'],1)
            self.assertEqual(event['partial']['observations'][0]['endMs'],2)
            acquired=next(e for e in self.events() if e['event']=='screenshot-received' and e['kind']=='original')
            self.assertEqual(acquired['sha256'],event['partial']['observations'][0]['sha256'])
        def test_cli_missing_receipt_refuses_before_driver_main_or_output_creation(self):
            env=dict(os.environ);env.pop('SALAH_HOSTED_NATIVE_ISOLATION_RECEIPT',None)
            result=subprocess.run([sys.executable,str(HERE/'retain_r0035.py'),'--driver',self.driver.__file__,
                '--evidence',str(self.root/'cli-evidence'),'--','unopened-plan',str(self.root/'cli-output'),
                '--engine','chromium'],env=env,text=True,capture_output=True)
            self.assertNotEqual(result.returncode,0)
            self.assertIn('admitted isolation receipt required',result.stderr)
            self.assertFalse((self.root/'cli-evidence').exists())
            self.assertFalse((self.root/'cli-output').exists())
        def test_swallowed_external_veto_still_stops_the_wrapper(self):
            original_argv=list(sys.argv)
            prior_umask=os.umask(0o077)
            def simulated_main():
                self.retained.begin_trial('main','chromium','http://127.0.0.1:8765',self.root/'unit',self.arm,self.args)
                raw=FakeRoute('https://unknown.invalid/payload')
                try: retention.RouteProxy(raw,self.retained,'http://127.0.0.1:8765').continue_()
                except ValueError: pass
                self.assertEqual(raw.actions,['abort'])
            self.driver.main=simulated_main
            try:
                with patch.object(retention,'verify_isolation',return_value={'offlineControl':True}), \
                     patch.object(retention,'load_driver',return_value=self.driver), \
                     patch.object(retention,'Retention',return_value=self.retained):
                    with self.assertRaises(SystemExit) as caught:
                        retention.main(['--driver',self.driver.__file__,'--evidence',str(self.root/'unused'),
                                        '--','unopened-plan',str(self.root/'cli-output')])
                self.assertEqual(caught.exception.code,86)
            finally:
                sys.argv=original_argv
                os.umask(prior_umask)
        def test_retention_close_preserves_primary_exception_and_veto_but_fails_standalone(self):
            for kind in ('primary','veto','standalone'):
                with self.subTest(kind=kind):
                    retained=retention.Retention(self.root/('close-'+kind))
                    cleanup=OSError('injected final close failure')
                    primary=ValueError('original driver failure')
                    real_close=retained.journal.close
                    def failed_close():
                        real_close()
                        raise cleanup
                    retained.journal.close=failed_close
                    if kind=='veto': retained.continuation_veto=ValueError('external continuation refused')
                    def driver_main():
                        if kind!='standalone': raise primary
                    fake_driver=SimpleNamespace(main=driver_main,trial=lambda:None,assess=lambda:None)
                    original_argv=list(sys.argv);prior_umask=os.umask(0o077)
                    diagnostics=io.StringIO()
                    try:
                        with patch.object(retention,'verify_isolation',return_value={'offlineControl':True}), \
                             patch.object(retention,'load_driver',return_value=fake_driver), \
                             patch.object(retention,'Retention',return_value=retained), \
                             patch.object(sys,'stderr',diagnostics):
                            expected=SystemExit if kind=='veto' else ValueError if kind=='primary' else OSError
                            with self.assertRaises(expected) as caught:
                                retention.main(['--driver',self.driver.__file__,'--evidence',str(self.root/'unused'),
                                                '--','unopened-plan',str(self.root/('output-'+kind))])
                        if kind=='veto': self.assertEqual(caught.exception.code,86)
                        elif kind=='primary': self.assertIs(caught.exception,primary)
                        else: self.assertIs(caught.exception,cleanup)
                        self.assertIn('injected final close failure',diagnostics.getvalue())
                        events=[json.loads(line) for line in (self.root/('close-'+kind)/'events.jsonl').read_text().splitlines()]
                        if kind!='standalone':
                            self.assertTrue(any(e['event']=='driver-threw' and e['error']['message']==str(primary) for e in events))
                    finally:
                        sys.argv=original_argv;os.umask(prior_umask)


if __name__ == '__main__':
    unittest.main()
