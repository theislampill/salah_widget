"""Pure real-controller/driver controls; native objects are explicit boundary doubles.

Every test names the wrong production decision it detects. No browser is launched.
"""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import tempfile
import subprocess
import shutil
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
CSS = 'https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400..700&family=Inter:wght@400;500;600&display=swap'
FONT = 'https://fonts.gstatic.com/s/inter/v1/test.woff2'
CSS_BODY = ("@font-face {font-family:'Inter';font-style:normal;font-weight:400;"
            "font-display:swap;src:url(" + FONT + ") format('woff2');unicode-range:U+0000-00FF;}").encode()
MODE = 'late-css-held-fonts-v1'

def load(relative, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

SYNTHETIC_ERROR_MARKERS=('SYNTHETIC_AUTH_MARKER','SYNTHETIC_COOKIE_MARKER','SYNTHETIC_UA_MARKER','SYNTHETIC_UNKNOWN_HEADER_MARKER')

def protocol_error():
    """Installed Playwright formatting, with invented values and no native request."""
    from playwright._impl._helper import parse_error
    from playwright._impl._connection import format_call_log
    return parse_error({'name':'Error','message':'synthetic transport failure','stack':''},format_call_log([
        '  - -> GET '+CSS,'  - authorization: Bearer '+SYNTHETIC_ERROR_MARKERS[0],
        '  - cookie: '+SYNTHETIC_ERROR_MARKERS[1],'  - user-agent: '+SYNTHETIC_ERROR_MARKERS[2],
        '  - x-unanticipated-name: '+SYNTHETIC_ERROR_MARKERS[3]]))

def assert_external_error_omitted(test,value):
    serialized=json.dumps(value)
    for marker in SYNTHETIC_ERROR_MARKERS:test.assertNotIn(marker,serialized)
    test.assertIn('OMITTED_UNTRUSTED_ERROR_TEXT',serialized)

class Request:
    def __init__(self, page, url, kind='font', method='GET', previous=None):
        self.url, self.resource_type, self.method = url, kind, method
        self.frame = page.main_frame
        self.redirected_from, self.redirected_to = previous, None
        if previous: previous.redirected_to = self
        self.failure = None
        self.finished = False

class Response:
    def __init__(self, page, request, data, status=200, mime='font/woff2'):
        self.page, self.request, self.data = page, request, data
        self.url, self.status, self.headers = request.url, status, {'content-type': mime}
        self.body_error = None
        self.body_delay = 0
        self.reads = 0
    def body(self):
        if self.page.in_callback or not self.request.finished:
            raise AssertionError('body read before successful native terminal or inside callback')
        self.reads += 1
        if self.page.body_hook: self.page.body_hook(self)
        self.page.now += self.body_delay
        if self.body_error: raise self.body_error
        return self.data

class APIResponse:
    def __init__(self, page):
        self.page, self.url, self.status = page, CSS, 200
        self.headers, self.data = {'content-type': 'text/css; charset=utf-8'}, CSS_BODY
        self.disposed = 0
    def body(self):
        if self.page.in_callback: raise AssertionError('API body inside callback')
        return self.data
    def dispose(self):
        self.disposed += 1
        self.page.calls.append(('dispose',))
        if self.page.dispose_error: raise self.page.dispose_error

class Route:
    def __init__(self, page, request):
        self.page, self.request, self.actions = page, request, []
    def fetch(self, **kwargs):
        self.actions.append(('fetch', kwargs))
        if self.page.fetch_error: raise self.page.fetch_error
        return self.page.api
    def fulfill(self, **kwargs):
        self.actions.append(('fulfill', kwargs))
        if kwargs != {'response': self.page.api}: raise AssertionError('edited CSS fulfillment')
        self.page.calls.append(('fulfill',))
        self.page.applied = True
        self.page.complete(self.request, self.page.api.data, mime='text/css')
        for _ in range(self.page.demand): self.page.font()
    def continue_(self, **kwargs):
        self.actions.append(('continue', kwargs))
        if kwargs: raise AssertionError('request overridden')
        if self.page.continue_error: raise self.page.continue_error
        if self.request.resource_type == 'font' and self.page.auto_finish:
            response = self.page.complete(self.request, self.page.font_body, status=self.page.font_status, mime=self.page.font_mime)
            response.body_error, response.body_delay = self.page.body_error, self.page.body_delay
    def abort(self):
        self.actions.append(('abort', {}))
        if self.page.abort_error: raise self.page.abort_error
        self.request.failure = 'aborted'
        self.page.emit('requestfailed', self.request)

class Page:
    def __init__(self, demand=1):
        self.now, self.demand, self.in_callback = 0.0, demand, False
        self.main_frame = self
        self.handlers, self.routes, self.transactions, self.calls = {}, [], [], []
        self.applied, self.auto_finish = False, True
        self.font_body, self.font_status, self.font_mime = b'actual-native-font', 200, 'font/woff2'
        self.fetch_error = self.abort_error = self.dispose_error = self.body_error = self.continue_error = None
        self.body_delay, self.native_css_error = 0, None
        self.wait_hook = self.body_hook = self.unroute_hook = None
        self.api = APIResponse(self)
        self.face_error = self.lifecycle_error = False
        self.media_state=None;self.media_close_error=None
    def on(self, name, callback): self.handlers.setdefault(name, []).append(callback)
    def remove_listener(self, name, callback): self.handlers[name].remove(callback)
    def route(self, pattern, handler): self.routes.append((pattern, handler))
    def unroute(self, pattern, handler):
        if self.unroute_hook:
            hook,self.unroute_hook=self.unroute_hook,None
            hook()
        self.routes.remove((pattern, handler))
    def emit(self, name, value):
        previous, self.in_callback = self.in_callback, True
        try:
            for callback in list(self.handlers.get(name, [])): callback(value)
        finally: self.in_callback = previous
    def request(self, url, kind, method='GET', previous=None):
        request = Request(self, url, kind, method, previous)
        route = Route(self, request)
        self.transactions.append((request, route))
        self.emit('request', request)
        for pattern, callback in reversed(self.routes):
            if pattern.search(url):
                previous_flag, self.in_callback = self.in_callback, True
                try: callback(route)
                finally: self.in_callback = previous_flag
                break
        return request, route
    def css(self): return self.request(CSS, 'stylesheet')
    def font(self): return self.request(FONT, 'font')
    def complete(self, request, data, status=200, mime='font/woff2'):
        response = Response(self, request, data, status, mime)
        if request.resource_type == 'stylesheet': response.body_error = self.native_css_error
        self.emit('response', response)
        request.finished = True
        self.emit('requestfinished', request)
        return response
    def wait_for_timeout(self, milliseconds):
        self.calls.append(('wait', milliseconds))
        self.now += milliseconds / 1000
        if self.wait_hook: self.wait_hook(milliseconds)
    def evaluate(self, expression, arg=None):
        if isinstance(arg,dict) and arg.get('operation') in {'install','close'}:
            if arg['operation']=='install':
                self.media_state={'installed':True,'closed':False,'disconnected':False,'records':[],
                                  'totalRecords':0,'firstError':None,'secondaryErrors':[]}
            else:
                self.media_state.update(closed=True,disconnected=True)
                if self.media_close_error:self.media_state['firstError']=self.media_close_error
            return copy.deepcopy(self.media_state)
        fonts = [r for r, _ in self.transactions if r.resource_type == 'font' and r.url == FONT]
        loading = any(not r.finished for r in fonts)
        face_status = 'error' if self.face_error else 'loading' if loading else 'loaded' if fonts else 'unloaded'
        faces = [{'id': 1, 'family': 'Inter', 'weight': '400', 'style': 'normal', 'status': face_status,
                  'loadingdoneReceipt': face_status == 'loaded', 'loadingerrorReceipt': self.face_error}] if self.applied else []
        terminal = {'event': 'load', 'url': CSS, 'isTrusted': True, 'at': self.now * 1000,
                    'mediaAtDispatch': 'print', 'observer': 'document-capture'} if self.applied else None
        return {'pagePerformanceMs': self.now * 1000, 'pageReadStartedMs':self.now*1000,'pageReadFinishedMs':self.now*1000,
                'mediaObservation':copy.deepcopy(self.media_state),'renderOrdinal': 7, 'current': {'date': '01-11-2026'},
                'next': {'date': None}, 'text': {'.nt': {'text': '05:00', 'geometry': {'width': 40, 'height': 20}}},
                'link': {'url': CSS, 'connected': True, 'identityMatches': True, 'media': 'all' if self.applied else 'print', 'terminal': terminal},
                'fontSettlement': {'settled': not loading, 'pendingDeferred': 0, 'lifecycleErrors': ['removed:1'] if self.lifecycle_error else [],
                                   'status': 'loading' if loading else 'loaded', 'faces': faces, 'events': [], 'stylesheetEvents': []}}

class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue((ROOT/'tools/cp9/r0007_font_ingress.py').is_file(), 'reviewed real controller has not been implemented')
        self.module = load('tools/cp9/r0007_font_ingress.py', 'ingress_test_subject')
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.page, self.trace = Page(), {}
        self.clock = patch.object(self.module.time, 'monotonic', side_effect=lambda: self.page.now)
        self.clock.start(); self.addCleanup(self.clock.stop)
        self.case = {'caseId': 'NE07-fall24', 'entry': 'index.html', 'fontIngress': MODE}
    def controller(self):
        control = self.module.FontIngressController(self.page, Path(self.temp.name), self.trace, self.case)
        control.install(); return control
    def run_control(self):
        control = self.controller(); self.page.css(); control.run(self.page); return control
    def test_protocol_call_log_is_omitted_from_latch_and_public_rethrow(self):
        """Break: fetch protocol headers survive in the first latch or formatted exception chain."""
        import traceback
        self.page.fetch_error=protocol_error()
        control=self.controller();self.page.css()
        escaped=None
        try:control.run(self.page)
        except Exception as error:escaped=''.join(traceback.format_exception(error))
        self.assertIsNotNone(escaped)
        control.close()
        assert_external_error_omitted(self,{'trace':self.trace,'exception':escaped})
        first=self.trace['fontIngress']['firstError']
        self.assertEqual((first['errorType'],first['operation'],first['phase']),('Error','run','css-acquisition'))
        self.assertEqual(first['messageProvenance'],'OMITTED_UNTRUSTED_ERROR_TEXT')
    def test_native_css_unavailability_and_failed_request_omit_external_text(self):
        """Break: optional native CSS reason or requestfailed bypasses the error-custody boundary."""
        self.page.native_css_error=protocol_error()
        control=self.run_control()
        native=self.trace['fontIngress']['css']['nativeBody']
        self.assertEqual(native['status'],'unavailable')
        assert_external_error_omitted(self,native)
        self.page.auto_finish=False
        request,_=self.page.font();request.failure=str(protocol_error())
        self.page.emit('requestfailed',request)
        with self.assertRaises(Exception):control.finalize(self.page)
        self.assertEqual(control.close()['status'],'FAILED')
        assert_external_error_omitted(self,self.trace)
    def test_protocol_callback_and_cleanup_errors_remain_fatal_without_text(self):
        """Break: callback, abort, API-dispose or detached-route errors persist raw native text."""
        self.page.dispose_error=protocol_error();self.page.continue_error=protocol_error()
        self.page.abort_error=protocol_error()
        control=self.controller();self.page.css()
        with self.assertRaises(Exception):control.run(self.page)
        # A distinct out-of-scope route also exercises the unassociated cleanup receipt.
        self.page.request('https://fonts.gstatic.com/unrelated.woff2','font')
        receipt=control.close()
        self.assertEqual(receipt['status'],'FAILED')
        operations=[row['operation'] for row in receipt['errors']]
        self.assertIn('api-dispose',operations);self.assertIn('route',operations)
        self.assertIn('unassociated-route-abort',operations);self.assertIn('route-abort',operations)
        assert_external_error_omitted(self,self.trace)
    def test_delayed_css_and_fonts_preserve_bytes(self):
        """Break: early forwarding, edited CSS/request, or hold anchored to first demand."""
        control = self.controller(); _, css_route = self.page.css()
        self.assertEqual(css_route.actions, [])
        control.run(self.page)
        self.assertEqual(css_route.actions[0], ('fetch', {'timeout': 10000, 'max_redirects': 0, 'max_retries': 0}))
        self.assertEqual(css_route.actions[1], ('fulfill', {'response': self.page.api}))
        self.assertEqual(self.page.transactions[1][1].actions, [('continue', {})])
        self.assertEqual([row[1] for row in self.page.calls if row[0] == 'wait'], [500, 2000])
        self.assertLess(self.page.calls.index(('fulfill',)), self.page.calls.index(('dispose',)))
        css = self.trace['fontIngress']['css']
        self.assertEqual(css['deliveredCssSha256'], hashlib.sha256(CSS_BODY).hexdigest())
        self.assertEqual((Path(self.temp.name)/css['apiBody']['path']).read_bytes(), CSS_BODY)
        self.assertEqual(css['nativeBody']['status'], 'captured')
        self.page.wait_for_timeout(1000); control.finalize(self.page)
        self.assertEqual(control.close()['status'], 'CLOSED')
        self.assertEqual(self.page.api.disposed, 1)
    def test_route_scope_and_shared_cache_contract(self):
        """Break: callable broad interceptor, unrelated rewrite or missing shared-cache receipt."""
        control = self.controller()
        self.assertTrue(all(isinstance(pattern, re.Pattern) for pattern,_ in self.page.routes))
        self.assertFalse(any(pattern.search('https://example.invalid/'+CSS) for pattern,_ in self.page.routes))
        _, unrelated = self.page.request('https://fonts.gstatic.com/unrelated.woff2', 'font')
        self.assertEqual(unrelated.actions, [('continue', {})])
        self.assertTrue(self.trace['fontIngress']['routingHttpCacheDisabled'])
        control.close()
    def test_validation_rejects_conflicts_and_only_absence_disables(self):
        """Break: unsupported modes/entries silently gaining a route capability."""
        self.assertFalse(self.module.validate_font_ingress({'entry':'index.html'}, 7))
        for changes, issue in [({'fontIngress': None},7), ({'fontIngress':'other'},7), ({},2),
                               ({'offline':True},7), ({'imageRules':[{}]},7), ({'iframe':True},7), ({'entry':'offline.html'},7)]:
            with self.subTest(changes=changes, issue=issue), self.assertRaises(ValueError):
                self.module.validate_font_ingress(dict(self.case, **changes), issue)
    def test_duplicate_native_requests_have_distinct_custody(self):
        """Break: deduplicating request/response or retained bytes by URL/hash."""
        self.page.demand = 2
        control = self.run_control()
        rows = [r for r in self.trace['fontIngress']['requests'] if r['kind']=='font']
        self.assertEqual(len(rows), 2)
        self.assertNotEqual(rows[0]['requestId'], rows[1]['requestId'])
        self.assertNotEqual(rows[0]['responseId'], rows[1]['responseId'])
        self.assertTrue(all(r['terminal']=='finished' and r['body']['bytes']==18 for r in rows))
        self.assertEqual(self.trace['fontIngress']['retainedFontBytes'], 36)
        control.close()
    def test_response_without_finished_cannot_earn_body_custody(self):
        """Break: equating headers/observer settlement with native completion."""
        self.page.auto_finish=False
        control=self.controller(); self.page.css()
        with self.assertRaisesRegex(Exception, 'settlement|deadline|terminal'): control.run(self.page)
        self.assertGreaterEqual(self.page.now, 17.5)
        control.close()
    def test_bad_status_mime_body_and_font_error_fail(self):
        """Break: accepting HTTP error completion, arbitrary MIME, failed/empty body or error face."""
        for attribute, value in [('font_status',404), ('font_mime','text/html'), ('font_body',b''),
                                 ('body_error',RuntimeError('native body unreadable')), ('face_error',True), ('lifecycle_error',True)]:
            with self.subTest(attribute=attribute):
                self.page=Page(); self.trace={}; setattr(self.page,attribute,value)
                control=self.controller(); self.page.css()
                with self.assertRaises(Exception): control.run(self.page)
                control.close()
    def test_install_failure_is_latched_before_cleanup(self):
        """Break: route-install failure recorded as a clean controller close."""
        def reject_route(*args): raise RuntimeError('route install broke')
        self.page.route=reject_route
        control=self.module.FontIngressController(self.page,Path(self.temp.name),self.trace,self.case)
        with self.assertRaisesRegex(RuntimeError,'OMITTED_UNTRUSTED_ERROR_TEXT'):control.install()
        self.assertIn('firstError',self.trace['fontIngress'])
        first=self.trace['fontIngress']['firstError']
        self.assertEqual((first['operation'],first['errorType']),('install','RuntimeError'))
        self.assertEqual(control.close()['status'],'FAILED')

    def test_body_failure_latches_its_actual_controller_phase(self):
        """Break: an orchestration body error lacks the controller error receipt used at final close."""
        self.page.body_error=RuntimeError('native body unreadable')
        control=self.controller();self.page.css()
        with self.assertRaisesRegex(RuntimeError,'OMITTED_UNTRUSTED_ERROR_TEXT'):control.run(self.page)
        self.assertIn('firstError',self.trace['fontIngress'])
        error=self.trace['fontIngress']['firstError']
        self.assertEqual((error['phase'],error['operation'],error['errorType']),('settlement','run','RuntimeError'))
        self.assertEqual(error['messageProvenance'],'OMITTED_UNTRUSTED_ERROR_TEXT')
        self.assertEqual(control.close()['status'],'FAILED')

    def test_css_cap_and_unsupported_import_fail_before_fulfillment(self):
        """Break: parsing/saving oversized or externally importing CSS."""
        for data in [b'x'*262145, b'@import url(https://other.invalid/a.css);'+CSS_BODY]:
            with self.subTest(size=len(data)):
                self.page=Page(); self.trace={}; self.page.api.data=data
                control=self.controller(); _,route=self.page.css()
                with self.assertRaises(Exception): control.run(self.page)
                self.assertFalse(any(action=='fulfill' for action,_ in route.actions))
                control.close(); self.assertEqual(self.page.api.disposed,1)
    def test_font_retained_byte_limits_apply_before_save(self):
        """Break: off-by-one per-body/total cap or saving rejected oversized evidence."""
        for size, demand, allowed in [(4194304,2,True),(4194305,1,False),(2796203,3,False)]:
            with self.subTest(size=size,demand=demand):
                self.page=Page(demand); self.trace={}; self.page.font_body=b'f'*size
                control=self.controller(); self.page.css()
                if allowed: control.run(self.page)
                else:
                    with self.assertRaisesRegex(Exception,'cap|limit'): control.run(self.page)
                saved=sum(p.stat().st_size for p in Path(self.temp.name).glob('font-ingress/font-*.bin'))
                self.assertLessEqual(saved,8388608)
                control.close()
                for p in Path(self.temp.name).glob('font-ingress/*'): p.unlink()
    def test_late_request_and_body_deadline_cannot_reopen_success(self):
        """Break: ignoring post-release demand or resetting deadline for late body custody."""
        control=self.run_control()
        self.page.body_delay=16
        self.page.font()
        with self.assertRaisesRegex(Exception,'deadline|budget'): control.finalize(self.page)
        control.close()
    def test_late_request_cap_and_incomplete_tail_fail(self):
        """Break: counting only initial held requests or waiting indefinitely after the tail."""
        for cap in [False,True]:
            with self.subTest(cap=cap):
                self.page=Page(); self.trace={}; control=self.run_control()
                if cap:
                    for _ in range(16): self.page.font()
                else:
                    self.page.auto_finish=False; self.page.font()
                before=self.page.now
                with self.assertRaises(Exception): control.finalize(self.page)
                self.assertEqual(self.page.now,before)
                control.close()
    def test_observer_error_during_late_body_read_is_fatal(self):
        """Break: sealing a stale pre-body observer snapshot after protocol pumping."""
        control=self.run_control()
        self.page.font()
        self.page.body_hook=lambda response: setattr(self.page,'face_error',True)
        with self.assertRaisesRegex(Exception,'font|observer'): control.finalize(self.page)
        control.close()

    def test_native_css_body_unavailability_is_explicit(self):
        """Break: relabeling API bytes as independently captured native bytes."""
        self.page.native_css_error=RuntimeError('native CSS body unavailable')
        control=self.run_control()
        css=self.trace['fontIngress']['css']
        self.assertEqual(css['nativeBody']['status'],'unavailable')
        self.assertEqual(css['nativeBody']['reason'],'OMITTED_UNTRUSTED_ERROR_TEXT')
        self.assertEqual(css['nativeBody']['reasonDetails']['errorType'],'RuntimeError')
        self.assertEqual(css['deliveredCssSha256'],hashlib.sha256(CSS_BODY).hexdigest())
        control.close()
    def test_redirect_and_failed_terminal_are_latched(self):
        """Break: treating first redirect response or failed native download as delivered font."""
        for redirected in [False,True]:
            with self.subTest(redirected=redirected):
                self.page=Page(); self.trace={}; control=self.run_control()
                request=self.page.transactions[1][0]
                if redirected:
                    hop=Request(self.page,'https://other.invalid/font.woff2',previous=request)
                    self.page.emit('request',hop)
                else:
                    request.failure='lost';self.page.emit('requestfailed',request)
                with self.assertRaises(Exception): control.finalize(self.page)
                control.close()
    def test_close_retains_abort_failure_and_is_idempotent(self):
        """Break: successful release receipt for failed abort, or duplicate effects on close."""
        control=self.controller(); _,route=self.page.css(); self.page.abort_error=RuntimeError('abort broke')
        first=control.close(); second=control.close()
        self.assertEqual(first,second); self.assertEqual(first['status'],'FAILED')
        self.assertEqual(route.actions,[('abort',{})])
        self.assertTrue(any(r.get('disposition')=='abort-failed' for r in self.trace['fontIngress']['requests']))
    def test_failed_out_of_scope_pass_through_is_cleaned_up(self):
        """Break: losing custody of an intercepted route whose unchanged continuation raises."""
        control=self.controller();self.page.continue_error=RuntimeError('pass failed')
        _,route=self.page.request('https://fonts.gstatic.com/unrelated.woff2','font')
        receipt=control.close()
        self.assertEqual(route.actions,[('continue',{}),('abort',{})])
        self.assertEqual(receipt['status'],'FAILED')

    def test_late_css_during_close_receives_abort_attempt(self):
        """Break: a callback pumped by unroute escaping the held-route cleanup census."""
        control=self.run_control(); late=[]
        self.page.unroute_hook=lambda: late.append(self.page.css()[1])
        receipt=control.close()
        self.assertEqual(late[0].actions,[('abort',{})])
        self.assertEqual(receipt['status'],'FAILED')

    def test_css_and_request_count_boundaries(self):
        """Break: rejecting exact caps or admitting the next declared URL/native demand."""
        self.page.api.data=CSS_BODY+b'/*'+b'x'*(262144-len(CSS_BODY)-4)+b'*/'
        control=self.run_control(); self.assertEqual(self.trace['fontIngress']['css']['apiBody']['bytes'],262144);control.close()
        for declared in [64,65]:
            with self.subTest(declared=declared):
                self.page=Page();self.trace={}
                self.page.api.data=CSS_BODY+b''.join(CSS_BODY.replace(b'test.woff2',str(i).encode()+b'.woff2') for i in range(declared-1))
                control=self.controller();self.page.css()
                if declared==64: control.run(self.page)
                else:
                    with self.assertRaisesRegex(Exception,'64|cap'):control.run(self.page)
                control.close()
        for count in [16,17]:
            with self.subTest(count=count):
                self.page=Page(count);self.trace={};control=self.controller();self.page.css()
                if count==16: control.run(self.page)
                else:
                    with self.assertRaisesRegex(Exception,'16|cap'):control.run(self.page)
                control.close()

    def test_missing_application_duplicate_css_and_api_response_fail(self):
        """Break: URL/status/MIME or original native link identity used as a readiness proxy."""
        for defect in ['missing','duplicate','api-status','api-url','api-mime','native-hash','untrusted']:
            with self.subTest(defect=defect):
                self.page=Page();self.trace={};control=self.controller()
                if defect!='missing': self.page.css()
                if defect=='duplicate':self.page.css()
                if defect=='api-status':self.page.api.status=302
                if defect=='api-url':self.page.api.url='https://other.invalid/css'
                if defect=='api-mime':self.page.api.headers={'content-type':'text/html'}
                if defect=='native-hash':self.page.body_hook=lambda response:setattr(response,'data',b'conflicting native CSS') if response.request.resource_type=='stylesheet' else None
                if defect=='untrusted':
                    actual=self.page.evaluate
                    def observation(*args):
                        result=actual(*args)
                        if result['link']['terminal']: result['link']['terminal']['isTrusted']=False
                        return result
                    self.page.evaluate=observation
                with self.assertRaises(Exception):control.run(self.page)
                control.close()

    def test_phase_protocol_error_retains_host_brackets(self):
        """Break: an unsuccessful phase evaluate loses its timing/error custody."""
        control=self.controller();self.page.css();actual=self.page.evaluate
        def fail_phase(expression,arg=None):
            if arg==CSS:raise RuntimeError('phase protocol broke')
            return actual(expression,arg)
        self.page.evaluate=fail_phase
        with self.assertRaisesRegex(RuntimeError,'OMITTED_UNTRUSTED_ERROR_TEXT'):control.run(self.page)
        self.assertIn('hostEvaluations',self.trace['fontIngress'])
        row=self.trace['fontIngress']['hostEvaluations'][-1]
        self.assertFalse(row['returned'])
        self.assertLessEqual(row['startedMonotonic'],row['finishedMonotonic'])
        self.assertEqual(row['pageTimingStatus'],'UNAVAILABLE_NO_RETURN')
        self.assertEqual(row['errorType'],'RuntimeError')
        control.close()

    def test_media_cleanup_error_is_fatal_and_does_not_skip_route_cleanup(self):
        """Break: failed media drain/disconnect is ignored after otherwise successful phases."""
        control=self.run_control();self.page.media_close_error='media drain broke'
        receipt=control.close()
        self.assertEqual(receipt['status'],'FAILED')
        self.assertTrue(self.page.media_state['closed'])
        self.assertEqual(self.page.routes,[])
        self.assertTrue(any(row['operation']=='media-close' and row['errorType']=='DiagnosticError' for row in receipt['errors']))

    def test_unused_fallback_faces_do_not_require_font_downloads(self):
        """Break: requiring all faces or optional binary demand in fallback arm."""
        self.case['variant']='font-fallback'; self.page.demand=0
        control=self.run_control(); control.finalize(self.page)
        self.assertEqual(self.trace['fontIngress']['retainedFontBytes'],0)
        self.assertEqual(control.close()['status'],'CLOSED')

class BindingTests(unittest.TestCase):
    def test_selected_mode_requires_helper_before_import_or_launch(self):
        """Break: accepting an unbound effect-bearing helper in actual driver validation."""
        driver=load('tools/cp9/r0007_browser.py','binding_driver')
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); observer=root/'tools/cp9/r0007_font_observer.js'
            observer.parent.mkdir(parents=True);observer.write_text('bound observer')
            case={'caseId':'NE07-fall24','entry':'index.html','hash':'#fixture','fontIngress':MODE,
                  'clockPolicy':{'mode':'fixed'},'cacheSeeds':[],'responseRules':[],
                  'orderedActions':[{'type':'wait','predicate':'true'}],'expected':[{'reviewOnly':True}]}
            packet={'schema':'remaining-prayer-cases/v1','issue':7,'sourceFiles':{'tools/cp9/r0007_font_observer.js':hashlib.sha256(observer.read_bytes()).hexdigest()},'cases':[case]}
            with self.assertRaisesRegex(ValueError,'helper|binding'): driver.validate_cases(packet,root)

    def test_committed_helper_is_required_and_hidden_drift_rejected(self):
        """Break: binding a selected helper outside actual committed blob custody."""
        native=load('tools/qualification/r0007_native.py','ingress_binding_native')
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); case={'caseId':'NE07-fall24','fontIngress':MODE}
            helper='tools/cp9/r0007_font_ingress.py'
            for relative in ['src/native/index.html','index.html','offline.html','config.js',native.DRIVER,
                             native.FIXTURE,native.RUNTIME,native.FONT_OBSERVER,'tools/qualification/r0007_native.py',helper]:
                path=root/relative;path.parent.mkdir(parents=True,exist_ok=True);path.write_text('synthetic binding: '+relative)
            recipe=root/native.DEFAULT_RECIPE
            recipe.write_text(json.dumps({'schema':'remaining-prayer-cases/v1','issue':7,'cases':[case]}))
            def git(*args): return subprocess.check_output(['git','-C',str(root),*args],stderr=subprocess.STDOUT)
            git('init','--quiet');git('add','.')
            git('-c','user.name=Synthetic fixture','-c','user.email=fixture@example.invalid','commit','--quiet','-m','binding fixture')
            identity=native.clean_identity(root)
            packet=native.bind_packet(root,recipe,identity,[case])
            self.assertIn(helper,packet['sourceFiles'])
            git('update-index','--assume-unchanged',helper)
            (root/helper).write_text('hidden helper drift')
            self.assertEqual(native.clean_identity(root),identity)
            with self.assertRaisesRegex(ValueError,'committed bytes'): native.bind_packet(root,recipe,identity,[case])

from contextlib import ExitStack, redirect_stdout
from io import StringIO
from types import SimpleNamespace


class DriverLifecyclePage(Page):
    """Native page boundary; all controller and driver decisions stay real."""

    def __init__(self, *, action_error=None, tail_fault=None, unroute_error=None):
        super().__init__()
        self.action_error = action_error
        self.tail_fault = tail_fault
        self.unroute_error = unroute_error
        self.tail_injected = False
        self.registered_events = []
        self.registered_routes = []
        self.observation_count = 0

    def on(self, name, callback):
        self.registered_events.append(name)
        super().on(name, callback)

    def route(self, pattern, handler):
        self.registered_routes.append(pattern)
        super().route(pattern, handler)

    def unroute(self, pattern, handler):
        if self.unroute_error:
            raise self.unroute_error
        super().unroute(pattern, handler)

    def goto(self, url, *, wait_until):
        self.calls.append(('goto', url, wait_until))
        self.css()

    def wait_for_function(self, predicate, *, timeout, polling):
        self.calls.append(('action-wait', predicate, timeout, polling))
        if self.action_error:
            raise self.action_error
        return True

    def wait_for_timeout(self, milliseconds):
        super().wait_for_timeout(milliseconds)
        if milliseconds != 1000 or self.tail_injected or self.tail_fault is None:
            return
        self.tail_injected = True
        if self.tail_fault == 'callback':
            request, _ = self.font()
            self.emit('requestfinished', request)  # Contradictory native terminal.
        elif self.tail_fault == 'body':
            self.body_error = RuntimeError('late native body broke')
            self.font()
        elif self.tail_fault == 'observer':
            self.lifecycle_error = True
        elif self.tail_fault == 'media':
            self.media_state['firstError']='media record cap exceeded'
        elif self.tail_fault == 'cap':
            for _ in range(16): self.font()
        elif self.tail_fault == 'incomplete':
            self.auto_finish = False
            self.font()
        else:
            raise AssertionError('unknown native tail fault')

    def evaluate(self, expression, arg=None):
        if isinstance(arg,dict) and arg.get('operation') in {'install','close'}:
            return super().evaluate(expression,arg)
        if arg == CSS:
            self.observation_count += 1
            return super().evaluate(expression, arg)
        if arg is not None or 'window.__prayerFixture' not in expression:
            raise AssertionError('unexpected native evaluation boundary')
        state = super().evaluate(expression)['fontSettlement']
        return {
            'startedPerformance': 0,
            'events': [],
            'snapshots': [{'stage': 'render-completed', 'checkpoint': 'literal-source',
                           'dom': {'.nt': {'text': '05:00'}}}],
            'requests': [], 'storageLog': [], 'timerLog': [], 'activeTimers': [],
            'storage': [], 'pending': [], 'unexpected': [], 'assetEvents': [],
            'resourceTiming': [], 'fontSettlement': state,
            'fonts': {'status': state['status'], 'faces': copy.deepcopy(state['faces'])},
        }


class DriverNativeBoundaries:
    """Real orchestration calls these native boundary objects; no process starts."""

    CLEANUP = ['context.close', 'browser.close', 'playwright.stop',
               'server.shutdown', 'server.server_close', 'thread.join']

    def __init__(self, page, executable, trace_path, *, fail_cleanup=None, thread_alive=False, cleanup_error=None):
        self.page, self.trace_path = page, trace_path
        self.fail_cleanup, self.thread_alive = fail_cleanup, thread_alive
        self.cleanup_error=cleanup_error
        self.cleanup_calls, self.status_at_cleanup, self.routes_at_cleanup = [], [], []
        self.join_timeouts = []
        context = SimpleNamespace(
            add_init_script=lambda script: None,
            new_page=lambda: page,
            close=lambda: self.cleanup('context.close'))
        browser = SimpleNamespace(
            version='native-boundary-double',
            new_context=lambda **options: context,
            close=lambda: self.cleanup('browser.close'))
        browser_type = SimpleNamespace(
            name='firefox', executable_path=str(executable), launch=lambda **options: browser)
        self.playwright = SimpleNamespace(
            firefox=browser_type, stop=lambda: self.cleanup('playwright.stop'))
        self.launcher = SimpleNamespace(start=lambda: self.playwright)
        self.server = SimpleNamespace(
            server_port=47111, serve_forever=lambda: None,
            shutdown=lambda: self.cleanup('server.shutdown'),
            server_close=lambda: self.cleanup('server.server_close'))
        self.thread = SimpleNamespace(
            start=lambda: None, join=self.join, is_alive=lambda: self.thread_alive)

    def cleanup(self, operation):
        self.cleanup_calls.append(operation)
        status = json.loads(self.trace_path.read_text())['status'] if self.trace_path.exists() else None
        self.status_at_cleanup.append(status)
        self.routes_at_cleanup.append(len(self.page.routes))
        if operation == self.fail_cleanup:
            if self.cleanup_error is not None:raise self.cleanup_error
            raise RuntimeError(operation + ' broke')

    def join(self, *, timeout):
        self.join_timeouts.append(timeout)
        self.cleanup('thread.join')


class DriverLifecycleTests(unittest.TestCase):
    SUCCESS = 'PASS_ASSERTIONS_PENDING_PIXEL_REVIEW'

    def run_driver(self, *, selected=True, page=None, fail_cleanup=None, thread_alive=False, write_failure=None,
                   second_case=False,cleanup_error=None,write_error=None,await_result=False):
        page = page or DriverLifecyclePage()
        temporary = tempfile.TemporaryDirectory(prefix='r0007-driver-lifecycle-')
        self.addCleanup(temporary.cleanup)
        directory = Path(temporary.name)
        root, output = directory / 'source', directory / 'evidence'
        root.mkdir()
        files = ['tools/cp9/browser_runtime.py', 'tools/cp9/r0007_font_observer.js']
        if selected:
            files.append('tools/cp9/r0007_font_ingress.py')
        for relative in files:
            destination = root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes((ROOT / relative).read_bytes())
        (root / 'index.html').write_text('<!doctype html><title>Native boundary fixture</title>')
        files.append('index.html')
        executable = directory / 'firefox-boundary'
        executable.write_bytes(b'Never executable: bound native-launch test input')
        case = {
            'caseId': 'NE07-lifecycle-control', 'entry': 'index.html', 'hash': '#fixture',
            'clockPolicy': {'mode': 'fixed', 'epoch': '2026-11-01T05:30:00Z'},
            'cacheSeeds': [], 'responseRules': [],
            'orderedActions': [{'type': 'wait', 'predicate': 'window.__prayerFixture.snapshots.length > 0'}],
            'expected': [{'stage': 'literal-source', 'equals': {'dom/.nt/text': '05:00'}}],
        }
        if selected:
            case['fontIngress'] = MODE
        if await_result:case['orderedActions'][0]['awaitResult']=True
        packet = {
            'schema': 'remaining-prayer-cases/v1', 'issue': 7, 'sourceCommit': 'a' * 40,
            'sourceFiles': {relative: hashlib.sha256((root / relative).read_bytes()).hexdigest()
                            for relative in files},
            'cases': [case],
        }
        if second_case:
            packet['cases'].append(dict(case,caseId=case['caseId']+'-second'))
        cases = directory / 'bound-cases.json'
        cases.write_text(json.dumps(packet))
        lease = directory / 'capacity-lease.json'
        lease.write_text(json.dumps({'resource': 'heavy-browser', 'status': 'GRANTED',
                                    'owner': 'prayer', 'sourceCommit': 'a' * 40}))
        trace_path = output / case['caseId'] / 'trace.json'
        native = DriverNativeBoundaries(page, executable, trace_path,
                                        fail_cleanup=fail_cleanup, thread_alive=thread_alive,cleanup_error=cleanup_error)
        driver = load('tools/cp9/r0007_browser.py', 'driver_lifecycle_subject')
        result, escaped = None, None
        stdout=StringIO()
        with ExitStack() as stack:
            stack.enter_context(redirect_stdout(stdout))
            stack.enter_context(patch.dict(os.environ, {'SALAH_BROWSER': 'firefox',
                                                        'SALAH_BROWSER_EXECUTABLE': str(executable)}))
            stack.enter_context(patch('playwright.sync_api.sync_playwright', new=lambda: native.launcher))
            stack.enter_context(patch.object(driver.http.server, 'ThreadingHTTPServer',
                                            new=lambda *args, **kwargs: native.server))
            stack.enter_context(patch.object(driver.threading, 'Thread',
                                            new=lambda *args, **kwargs: native.thread))
            stack.enter_context(patch.object(driver.subprocess, 'check_output',
                                            new=lambda arguments: (root / 'index.html').read_bytes()))
            # The real helper imports this same clock module from the bound source.
            stack.enter_context(patch.object(driver.time, 'monotonic', new=lambda: page.now))
            if write_failure:
                actual_dump=driver.dump
                def failing_write(path, value):
                    if Path(path).name==write_failure: raise write_error or OSError(write_failure+' write broke')
                    return actual_dump(path,value)
                stack.enter_context(patch.object(driver,'dump',new=failing_write))
            try:
                result = driver.main([
                    '--issue', '7', '--engine', 'firefox', '--source-root', str(root),
                    '--cases', str(cases), '--output', str(output), '--capacity-lease', str(lease),
                    '--headed', '--video-only'])
            except Exception as error:
                escaped = repr(error)
        trace = json.loads(trace_path.read_text()) if trace_path.exists() else None
        summary_path = output / 'summary.json'
        summary = json.loads(summary_path.read_text()) if summary_path.exists() else None
        return SimpleNamespace(result=result, escaped=escaped, trace=trace, summary=summary,
                               page=page, native=native, case_id=case['caseId'], case=case, root=root, output=output, packet=packet,
                               stdout=stdout.getvalue())

    def assert_received(self, run, status, exit_code):
        self.assertIsNone(run.escaped, 'driver must retain the failure and finish cleanup: ' + str(run.escaped))
        self.assertEqual(run.result, exit_code)
        self.assertIsNotNone(run.trace, 'driver did not write its final trace')
        self.assertEqual(run.trace['status'], status)
        self.assertIsNotNone(run.summary, 'driver did not write its final summary')
        self.assertEqual([(row['caseId'], row['status']) for row in run.summary['receipts']],
                         [(run.case_id, status)])

    def assert_all_native_cleanup(self, run, *, diagnostic=True):
        self.assertEqual(run.native.cleanup_calls, DriverNativeBoundaries.CLEANUP)
        self.assertEqual(run.native.join_timeouts, [2])
        if diagnostic:
            self.assertTrue(all(status != self.SUCCESS for status in run.native.status_at_cleanup),
                            'diagnostic success was written before native cleanup finished')
            self.assertEqual([row['operation'] for row in run.trace['fontIngressNativeCleanup']],
                             DriverNativeBoundaries.CLEANUP)

    def test_selected_driver_errors_omit_protocol_text_and_preserve_primary_order(self):
        """Break: action/capture/secondary/native cleanup or stdout stores protocol call-log headers."""
        class CaptureFailurePage(DriverLifecyclePage):
            def evaluate(self,expression,arg=None):
                if 'return {events:f.events' in expression:raise protocol_error()
                return super().evaluate(expression,arg)
        page=CaptureFailurePage(action_error=protocol_error(),unroute_error=protocol_error())
        page.abort_error=protocol_error()
        run=self.run_driver(page=page,fail_cleanup='context.close',cleanup_error=protocol_error())
        self.assert_received(run,'FAIL',1);self.assert_all_native_cleanup(run)
        assert_external_error_omitted(self,{'trace':run.trace,'stdout':run.stdout,'escaped':run.escaped})
        self.assertEqual(run.trace['failureStage'],'case-actions')
        self.assertEqual(run.trace['failureError']['errorType'],'Error')
        self.assertEqual(run.trace['failureCaptureError']['errorType'],'Error')
        self.assertEqual([row['stage'] for row in run.trace['secondaryFailures']],
                         ['font-ingress-close','context.close','font-ingress-final-latch'])
        self.assertEqual(run.trace['fontIngressNativeCleanup'][0]['errorDetails']['errorType'],'Error')

    def test_selected_page_errors_and_final_write_rethrow_omit_protocol_text(self):
        """Break: pageerror custody or an exception escaping final trace/summary writing leaks native text."""
        class PageErrorPage(DriverLifecyclePage):
            def goto(self,*args,**kwargs):
                super().goto(*args,**kwargs);self.emit('pageerror',protocol_error())
        run=self.run_driver(page=PageErrorPage())
        self.assert_received(run,'FAIL',1)
        self.assertEqual(len(run.trace['pageErrors']),1)
        assert_external_error_omitted(self,{'trace':run.trace,'stdout':run.stdout})
        for filename in ['trace.json','summary.json']:
            with self.subTest(filename=filename):
                failed=self.run_driver(write_failure=filename,write_error=protocol_error())
                self.assertIsNone(failed.result);self.assertIsNotNone(failed.escaped)
                assert_external_error_omitted(self,failed.escaped)
                self.assertIn('Error: OMITTED_UNTRUSTED_ERROR_TEXT',failed.escaped)
                self.assertEqual(failed.native.cleanup_calls,DriverNativeBoundaries.CLEANUP)

    def test_selected_async_wait_error_and_cleanup_custody_is_sanitized(self):
        """Break: async state error/cancel/dispose bypasses omission or masks its original failure."""
        for fault in ['state-error','state-cleanup','state-dispose']:
            with self.subTest(fault=fault):
                calls=[]
                class State:
                    def evaluate(self,expression):
                        calls.append('cancel')
                        if fault=='state-cleanup':raise protocol_error()
                        return {'pending':False,'accepted':False,'cancelled':True,'error':str(protocol_error()),
                                'attempts':1,'falseResults':0,'startedAt':10,'acceptedAt':None,'finishedAt':20}
                    def dispose(self):
                        calls.append('dispose')
                        if fault=='state-dispose':raise protocol_error()
                class AsyncPage(DriverLifecyclePage):
                    def evaluate_handle(self,expression):return State()
                    def wait_for_function(self,predicate,*,arg,timeout,polling):raise protocol_error()
                run=self.run_driver(page=AsyncPage(),await_result=True)
                self.assert_received(run,'FAIL',1);self.assert_all_native_cleanup(run)
                self.assertEqual(calls,['cancel','dispose'])
                self.assertEqual(run.trace['failureStage'],'case-actions')
                assert_external_error_omitted(self,{'trace':run.trace,'stdout':run.stdout})
                self.assertEqual(run.trace['failureError']['errorType'],'Error')
                receipt=run.trace['asyncWaitReceipts'][0]
                self.assertEqual(receipt['status'],'FAILED')
                self.assertEqual(receipt['errors'][0]['operation'],'wait')
                if fault!='state-error':self.assertEqual(len(receipt['errors']),2)

    def test_selected_async_wait_retains_awaited_truth_and_disposes_all_handles(self):
        """Break: omission changes predicate truth, timeout/polling, or successful-handle cleanup."""
        for accepted in [True,False]:
            with self.subTest(accepted=accepted):
                calls=[]
                class State:
                    def evaluate(self,expression):
                        calls.append('cancel')
                        return {'pending':False,'accepted':accepted,'cancelled':True,'error':None,
                                'attempts':1,'falseResults':0,'startedAt':10,'acceptedAt':20 if accepted else None,'finishedAt':30}
                    def dispose(self):calls.append('state-dispose')
                class Result:
                    def json_value(self):return accepted
                    def dispose(self):calls.append('result-dispose')
                class AsyncPage(DriverLifecyclePage):
                    def evaluate_handle(self,expression):return State()
                    def wait_for_function(page,predicate,*,arg,timeout,polling):
                        self.assertEqual((arg['source'],timeout,polling),('window.__prayerFixture.snapshots.length > 0',15000,'raf'))
                        return Result()
                run=self.run_driver(page=AsyncPage(),await_result=True)
                self.assert_received(run,self.SUCCESS if accepted else 'FAIL',0 if accepted else 1)
                self.assertEqual(calls,['result-dispose','cancel','state-dispose'])
                self.assertEqual(run.trace['asyncWaitReceipts'][0]['status'],'AWAITED_TRUE' if accepted else 'FAILED')
                self.assert_all_native_cleanup(run)

    def test_absent_mode_preserves_existing_external_error_representation(self):
        """Break: diagnostic omission changes the original no-mode error/mutant matching interface."""
        error=protocol_error();run=self.run_driver(selected=False,page=DriverLifecyclePage(action_error=error))
        self.assert_received(run,'FAIL',1)
        self.assertEqual(run.trace['failure'],repr(error))
        self.assertNotIn('failureError',run.trace)
        self.assert_all_native_cleanup(run,diagnostic=False)

    def test_success_is_sealed_only_after_finalization_and_every_cleanup(self):
        """Break: skipped helper phase, early success write or changed presentation tail."""
        run = self.run_driver()
        self.assert_received(run, self.SUCCESS, 0)
        self.assertIn('fontIngress', run.trace)
        self.assertIn('fontIngress', run.trace)
        ingress = run.trace['fontIngress']
        self.assertEqual(ingress['css']['deliveredCssSha256'], hashlib.sha256(CSS_BODY).hexdigest())
        self.assertEqual(ingress['css']['nativeTerminal'], 'finished')
        self.assertEqual(ingress['finalization']['status'], 'FINALIZED')
        self.assertEqual(ingress['close']['status'], 'CLOSED')
        self.assertEqual([row[1] for row in run.page.calls if row[0] == 'wait'], [500, 2000, 1000])
        self.assert_all_native_cleanup(run)
        self.assertTrue(all(row['returned'] for row in run.trace['fontIngressNativeCleanup']))
        self.assertEqual(run.native.routes_at_cleanup, [0] * 6)

    def test_success_then_close_failure_is_fatal(self):
        """Break: successful source/finalization receipt survives a failed real controller close."""
        run = self.run_driver(page=DriverLifecyclePage(unroute_error=RuntimeError('unroute broke')))
        self.assert_received(run, 'FAIL', 1)
        self.assertEqual(run.trace['fontIngress']['finalization']['status'], 'FINALIZED')
        self.assertEqual(run.trace['fontIngress']['close']['status'], 'FAILED')
        self.assertTrue(any(row['operation']=='unroute' and row['errorType']=='RuntimeError'
                            for row in run.trace['fontIngress']['close']['errors']))
        self.assertTrue(run.trace['failure'])
        self.assert_all_native_cleanup(run)

    def test_late_tail_failure_is_fatal(self):
        """Break: post-release callback/body/observer or incomplete-transaction failures are ignored."""
        for fault, fragment in [('callback', 'terminal'), ('body', 'OMITTED_UNTRUSTED_ERROR_TEXT'),
                                ('observer', 'lifecycle'), ('incomplete', 'incomplete'), ('cap','cap'), ('media','media observer')]:
            with self.subTest(fault=fault):
                run = self.run_driver(page=DriverLifecyclePage(tail_fault=fault))
                self.assert_received(run, 'FAIL', 1)
                self.assertIn(fragment, run.trace['failure'])
                if fault=='body':self.assertEqual(run.trace['failureError']['errorType'],'RuntimeError')
                self.assertEqual([row[1] for row in run.page.calls if row[0] == 'wait'], [500, 2000, 1000])
                self.assert_all_native_cleanup(run)

    def test_primary_failure_and_abort_failure_reach_all_cleanup(self):
        """Break: failed abort masks the primary action error or prevents later native cleanup."""
        page = DriverLifecyclePage(action_error=ValueError('primary action broke'))
        page.abort_error = RuntimeError('abort route broke')
        run = self.run_driver(page=page)
        self.assert_received(run, 'FAIL', 1)
        self.assertEqual(run.trace['failureError'],{'errorType':'ValueError','message':'OMITTED_UNTRUSTED_ERROR_TEXT',
                                                  'messageProvenance':'OMITTED_UNTRUSTED_ERROR_TEXT'})
        self.assertEqual(run.trace['failureStage'], 'case-actions')
        self.assertIn('fontIngress', run.trace)
        ingress = run.trace['fontIngress']
        self.assertEqual(ingress['close']['status'], 'FAILED')
        css = next(row for row in ingress['requests'] if row['kind'] == 'css')
        self.assertEqual(css['disposition'], 'abort-failed')
        self.assertEqual([(row['action'], row['returned']) for row in css['attempts']], [('abort', False)])
        self.assertTrue(any(row['operation']=='route-abort' and row['errorType']=='RuntimeError' for row in ingress['close']['errors']))
        self.assertTrue(run.trace['secondaryFailures'])
        self.assert_all_native_cleanup(run)

    def test_native_cleanup_failure_still_reaches_every_later_cleanup(self):
        """Break: any native cleanup exception escapes, preserves success or skips later cleanup."""
        for failed in DriverNativeBoundaries.CLEANUP:
            with self.subTest(failed=failed):
                run = self.run_driver(fail_cleanup=failed)
                self.assert_received(run, 'FAIL', 1)
                self.assertEqual(run.trace['fontIngress']['close']['status'], 'CLOSED')
                self.assertEqual(run.trace['failureStage'],failed)
                self.assertEqual(run.trace['failureError']['errorType'],'RuntimeError')
                self.assert_all_native_cleanup(run)
                rows = run.trace['fontIngressNativeCleanup']
                self.assertEqual([(row['operation'], row['returned']) for row in rows],
                                 [(operation, operation != failed) for operation in DriverNativeBoundaries.CLEANUP])
                error=next(row['errorDetails'] for row in rows if row['operation']==failed)
                self.assertEqual((error['errorType'],error['messageProvenance']),('RuntimeError','OMITTED_UNTRUSTED_ERROR_TEXT'))

    def test_live_thread_after_the_existing_join_is_incomplete_cleanup(self):
        """Break: a returned join is treated as proof that its server thread stopped."""
        run = self.run_driver(thread_alive=True)
        self.assert_received(run, 'FAIL', 1)
        self.assert_all_native_cleanup(run)
        self.assertIn('thread', run.trace['failure'])

    def test_failed_native_cleanup_stops_the_direct_diagnostic_case_loop(self):
        """Break: a second diagnostic browser starts after known failed native cleanup."""
        run=self.run_driver(fail_cleanup='context.close',second_case=True)
        self.assertIsNone(run.escaped)
        self.assertEqual(run.result,1)
        self.assertEqual([r['caseId'] for r in run.summary['receipts']],[run.case_id])
        self.assertEqual(run.summary['status'],'DIAGNOSTIC_CLEANUP_NOT_ESTABLISHED')
        self.assertEqual([r['caseId'] for r in run.summary['unattempted']],[run.case_id+'-second'])
        self.assertEqual(len([row for row in run.page.calls if row[0]=='goto']),1)
        self.assert_all_native_cleanup(run)

    def test_driver_cleanup_receipt_stops_existing_native_collector(self):
        """Break: summary-format cleanup credit lets the real collector launch another producer."""
        run=self.run_driver(fail_cleanup='context.close')
        native=load('tools/qualification/r0007_native.py','collector_ingress_subject')
        root=run.root
        for relative in [native.DRIVER,native.FIXTURE,'tools/qualification/r0007_native.py']:
            path=root/relative;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes((ROOT/relative).read_bytes())
        for relative in ['src/native/index.html','offline.html','config.js']:
            path=root/relative;path.parent.mkdir(parents=True,exist_ok=True);path.write_text('synthetic bound input '+relative)
        cases=[run.case,dict(run.case,caseId=run.case_id+'-second')]
        recipe=root/native.DEFAULT_RECIPE
        recipe.parent.mkdir(parents=True,exist_ok=True)
        recipe.write_text(json.dumps({'schema':'remaining-prayer-cases/v1','issue':7,'cases':cases,
                                      'execution':{'defaultCaseIds':[case['caseId'] for case in cases]}}))
        def git(*args):return subprocess.check_output(['git','-C',str(root),*args],stderr=subprocess.STDOUT)
        git('init','--quiet');git('add','.')
        git('-c','user.name=Synthetic fixture','-c','user.email=fixture@example.invalid','commit','--quiet','-m','collector fixture')
        attempted=[]
        def producer(command,cwd,env,directory,timeout):
            attempted.append(command[command.index('--case-id')+1])
            consumer=Path(command[command.index('--output')+1])
            shutil.copytree(run.output,consumer)
            summary=json.loads((consumer/'summary.json').read_text())
            summary['receipts'][0]['trace']=str(consumer/run.case_id/'trace.json')
            (consumer/'summary.json').write_text(json.dumps(summary))
            return {'command':command,'terminalState':'exited','exitCode':run.result}
        evidence=root.parent/'collector-evidence'
        with patch.object(native,'run_producer',side_effect=producer):
            code=native.main(['--source-root',str(root),'--evidence-root',str(evidence),'--engine','firefox','--headed','--video-only'])
        self.assertEqual(code,1)
        self.assertEqual(attempted,[run.case_id])
        summary=json.loads(next(evidence.glob('*/summary.json')).read_text())
        self.assertFalse(summary['results'][0]['cleanupEstablished'])
        self.assertEqual([row['caseId'] for row in summary['unattempted']],[run.case_id+'-second'])

    def test_final_evidence_write_failure_cannot_return_zero(self):
        """Break: a failed final trace/summary write becomes a successful producer return."""
        for name in ['trace.json','summary.json']:
            with self.subTest(name=name):
                run=self.run_driver(write_failure=name)
                self.assertNotEqual(run.result,0)
                self.assertIsNotNone(run.escaped)
                self.assertIn('OSError: OMITTED_UNTRUSTED_ERROR_TEXT',run.escaped)
                self.assertEqual(run.native.cleanup_calls,DriverNativeBoundaries.CLEANUP)
                self.assertEqual(run.native.join_timeouts,[2])

    def test_absent_mode_keeps_the_original_driver_path(self):
        """Break: unselected mode reads a missing helper or changes original routing/tail/cleanup."""
        run = self.run_driver(selected=False)
        self.assert_received(run, self.SUCCESS, 0)
        self.assertNotIn('fontIngress', run.trace)
        self.assertNotIn('fontIngressNativeCleanup', run.trace)
        self.assertEqual(run.page.registered_routes, [])
        self.assertEqual(run.page.registered_events, ['pageerror'])
        self.assertEqual(run.page.observation_count, 0)
        self.assertEqual([row[1] for row in run.page.calls if row[0] == 'wait'], [1000])
        self.assert_all_native_cleanup(run, diagnostic=False)
        self.assertEqual(run.native.status_at_cleanup, [self.SUCCESS] * 6)

class ObservationSourceTests(unittest.TestCase):
    def test_phase_span_encloses_every_retained_read(self):
        """Break: the claimed page span ends before ordinal/envelope/media/link/terminal reads."""
        module=load('tools/cp9/r0007_font_ingress.py','observation_read_order_subject')
        script=r'''
const input=JSON.parse(require('fs').readFileSync(0,'utf8'));
let tick=10;const reads=[];
const mark=(name,value)=>{reads.push({name,at:++tick});return value;};
global.performance={now:()=>tick};
const node={textContent:'fixture',getBoundingClientRect:()=>({x:1,y:2,width:40,height:20})};
const link={get href(){return mark('link.href',input.css);},get isConnected(){return mark('link.isConnected',true);},
 get ownerDocument(){return mark('link.ownerDocument',document);},get media(){return mark('link.media','all');}};
global.document={fonts:[],querySelector:s=>s.startsWith('link[')?link:node,querySelectorAll:()=>[]};
global.getComputedStyle=()=>({fontFamily:'Inter',fontWeight:'400',fontStyle:'normal',fontStretch:'normal',fontSize:'14px'});
global.today={get date(){return mark('current.date',null);},get timings(){return mark('current.timings',{});}};
global.tomorrow={get date(){return mark('next.date',null);},get timings(){return mark('next.timings',{});}};
global.window={__prayerFixture:{get ordinal(){return mark('fixture.ordinal',7);}},
 __r0007FontIngressMedia:{read:()=>mark('media.read',{installed:true})},
 __r0007FontSettlement:{read:()=>mark('fonts.read',{faces:[],settled:true,pendingDeferred:0}),
 stylesheetTerminal:()=>mark('stylesheetTerminal',{event:'load',url:input.css,isTrusted:true})}};
const observation=eval('('+input.expression+')')(input.css);
process.stdout.write(JSON.stringify({observation,reads}));
'''
        result=subprocess.run(['node','-e',script],input=json.dumps({'expression':module.OBSERVATION,'css':CSS}),
                              text=True,capture_output=True,check=True)
        result=json.loads(result.stdout);observation=result['observation'];reads=result['reads']
        self.assertNotIn('observationError',observation)
        self.assertEqual(observation['renderOrdinal'],7)
        self.assertEqual(observation['link']['terminal']['event'],'load')
        self.assertEqual({row['name'] for row in reads},{'fonts.read','fixture.ordinal','current.date','current.timings',
                         'next.date','next.timings','media.read','link.href','link.isConnected','link.ownerDocument',
                         'link.media','stylesheetTerminal'})
        self.assertTrue(all(observation['pageReadStartedMs']<=row['at']<=observation['pageReadFinishedMs'] for row in reads),
                        {'claimedSpan':[observation['pageReadStartedMs'],observation['pageReadFinishedMs']],
                         'outside':[row for row in reads if row['at']>observation['pageReadFinishedMs']]})

    def test_executed_observation_whitelists_required_text_and_face_descriptors(self):
        """Break: aggregate parent fonts stand in for actual text runs, or unused faces become defects."""
        module=load('tools/cp9/r0007_font_ingress.py','observation_subject')
        script=r'''
const fs=require('fs'),input=JSON.parse(fs.readFileSync(0,'utf8'));
const keys=['Fajr','Sunrise','Dhuhr','Asr','Maghrib','Isha'];
const times=['05:00','06:00','12:00','15:30','18:00','19:30'];
const elements=new Map();
function element(text,family){
 const node={textContent:text,getBoundingClientRect:()=>({x:1,y:2,width:40,height:20}),
  css:{fontFamily:family,fontWeight:'500',fontStyle:'italic',fontStretch:'normal',fontSize:'14px'}};
 for(const property of ['innerHTML','outerHTML'])Object.defineProperty(node,property,{get(){throw Error('HTML transport forbidden');}});
 return node;
}
for(const selector of ['.c','.cn','.nt','.left','.times','#loc','#wt','#wi','#weather-information','#ce','#ah','.left .until-time','.left .until-prayer'])
 elements.set(selector,element('literal:'+selector,'"Inter", sans-serif'));
for(let i=0;i<6;i++){
 elements.set('.times .p[data-prayer-key="'+keys[i]+'"] b',element(keys[i],'"Inter", sans-serif'));
 elements.set('.times .p[data-prayer-key="'+keys[i]+'"] .tm',element(times[i],'"Fraunces", serif'));
}
const labels=[element('left','Inter'),element('until','Inter')];
const nativeFaces=[{family:'Inter',weight:'400',style:'normal',stretch:'normal',unicodeRange:'U+0000-00FF',display:'swap',status:'unloaded'},
 {family:'Fraunces',weight:'400 700',style:'italic',stretch:'normal',unicodeRange:'U+0100-024F',display:'swap',status:'loaded'},
 {family:'Unrelated',weight:'400',style:'normal',stretch:'normal',unicodeRange:'U+0-10FFFF',display:'block',status:'loaded'}];
const link={href:input.css,isConnected:true,media:'all'};
global.document={fonts:nativeFaces,querySelector:selector=>selector.startsWith('link[')?link:elements.get(selector)??null,
 querySelectorAll:selector=>selector==='.left .until-label'?labels:[]};link.ownerDocument=document;
document.fonts.load=()=>{throw Error('font loading forbidden');};
global.getComputedStyle=node=>node.css;global.performance={now:()=>1234};
global.today={date:{gregorian:{date:'01-11-2026'}},timings:{Fajr:'05:00'},secret:'not transported'};
global.tomorrow=null;global.render=()=>{throw Error('product render forbidden');};
global.window={__prayerFixture:{ordinal:7},__r0007FontSettlement:{
 stylesheetTerminal:node=>node===link?{event:'load',url:input.css,isTrusted:true,mediaAtDispatch:'print',at:1000}:null,
 read:()=>({settled:true,pendingDeferred:0,lifecycleErrors:[],status:'loaded',
   faces:[{id:11,family:'Inter',weight:'400',style:'normal',status:'unloaded'},
          {id:12,family:'Fraunces',weight:'400 700',style:'italic',status:'loaded'}],
   events:[{kind:'deferred-receipt',type:'loadingdone',at:1200,faces:[]}],stylesheetEvents:[]})}};
const result=eval('('+input.expression+')')(input.css);process.stdout.write(JSON.stringify(result));
'''
        completed=subprocess.run(['node','-e',script],input=json.dumps({'expression':module.OBSERVATION,'css':CSS}),
                                 text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True)
        observation=json.loads(completed.stdout)
        self.assertIn('prayerRows',observation)
        self.assertEqual([row['key'] for row in observation['prayerRows']],['Fajr','Sunrise','Dhuhr','Asr','Maghrib','Isha'])
        self.assertEqual([row['name']['text'] for row in observation['prayerRows']],['Fajr','Sunrise','Dhuhr','Asr','Maghrib','Isha'])
        self.assertEqual([row['time']['text'] for row in observation['prayerRows']],['05:00','06:00','12:00','15:30','18:00','19:30'])
        self.assertTrue(all(row['time']['font']['family']=='"Fraunces", serif' for row in observation['prayerRows']))
        for selector in ['.cn','.nt','.left','#loc','#wt','#ce','#ah']:
            self.assertEqual(observation['text'][selector]['text'],'literal:'+selector)
            self.assertEqual(observation['text'][selector]['font'],{'family':'"Inter", sans-serif','weight':'500','style':'italic','stretch':'normal','size':'14px'})
        self.assertEqual([(face['observerId'],face['family'],face['unicodeRange'],face['display'],face['status']) for face in observation['relevantFaces']],
                         [(11,'Inter','U+0000-00FF','swap','unloaded'),(12,'Fraunces','U+0100-024F','swap','loaded')])
        self.assertEqual(observation['fontSettlement']['events'][0]['at'],1200)
        self.assertEqual(observation['pagePerformanceMs'],1234)
        self.assertEqual((observation['pageReadStartedMs'],observation['pageReadFinishedMs']),(1234,1234))
        self.assertEqual([row['text'] for row in observation['leftLabels']],['left','until'])
        self.assertEqual(observation['text']['.left .until-time']['text'],'literal:.left .until-time')
        self.assertEqual(observation['text']['.left .until-prayer']['text'],'literal:.left .until-prayer')
        self.assertNotIn('not transported',completed.stdout)

class MediaObserverSourceTests(unittest.TestCase):
    def execute_media(self,scenario):
        module=load('tools/cp9/r0007_font_ingress.py','media_source_subject')
        self.assertTrue(hasattr(module,'MEDIA_CONTROL'),'approved media observer has not been implemented')
        script=r'''
const fs=require('fs'),input=JSON.parse(fs.readFileSync(0,'utf8'));let now=100,media='print',reads=0,instance;
const link={tagName:'LINK',href:input.css,isConnected:true,get media(){reads++;return media;}};
global.document={querySelector:()=>link};link.ownerDocument=document;
Object.defineProperty(document,'fonts',{get(){throw Error('font access forbidden in media callback');}});
global.getComputedStyle=()=>{throw Error('style access forbidden');};
link.getBoundingClientRect=()=>{throw Error('layout access forbidden');};
global.render=()=>{throw Error('product render forbidden');};
global.window={};global.performance={now:()=>now};
class NativeMutationObserver{
 constructor(callback){this.callback=callback;this.pending=[];this.takes=0;this.disconnects=0;instance=this;}
 observe(target,options){this.target=target;this.options=options;}
 takeRecords(){this.takes++;if(this.takeError)throw Error(typeof this.takeError==='string'?this.takeError:'takeRecords broke');const rows=this.pending;this.pending=[];return rows;}
 disconnect(){this.disconnects++;if(this.disconnectError)throw Error(typeof this.disconnectError==='string'?this.disconnectError:'disconnect broke');}
}
global.MutationObserver=NativeMutationObserver;
const control=eval('('+input.expression+')');const installed=control({operation:'install',url:input.css});
function record(oldValue){return {type:'attributes',target:link,attributeName:'media',oldValue};}
function deliver(olds,value,time){media=value;now=time;const before=reads;instance.callback(olds.map(record),instance);return reads-before;}
let details={installed,options:instance.options};
if(input.scenario==='batch'){
 details.singleReads=deliver(['print'],'all',200);
 deliver(['all'],'all',300);
 details.batchReads=deliver(['print','all'],'all',400);
 details.state=window.__r0007FontIngressMedia.read();
}else if(input.scenario==='cap'){
 deliver(Array(16).fill('print'),'all',200);details.atCap=window.__r0007FontIngressMedia.read();
 deliver(['all'],'all',300);details.state=window.__r0007FontIngressMedia.read();
}else if(input.scenario==='cleanup'){
 media='all';now=200;instance.pending=[record('print')];
 details.closed=control({operation:'close',url:input.css});
 details.again=control({operation:'close',url:input.css});
 details.takes=instance.takes;details.disconnects=instance.disconnects;
}else if(input.scenario==='cleanup-error'){
 instance.takeError=true;details.closed=control({operation:'close',url:input.css});
 details.takes=instance.takes;details.disconnects=instance.disconnects;
}else if(input.scenario==='untrusted-error'){
 instance.takeError=input.errorText;instance.disconnectError=input.errorText;
 details.closed=control({operation:'close',url:input.css});
 details.takes=instance.takes;details.disconnects=instance.disconnects;
}else if(input.scenario==='callback-error'){
 const bad={type:'attributes',target:link,attributeName:'class',oldValue:'x'};
 instance.callback([bad],instance);details.state=window.__r0007FontIngressMedia.read();
}
process.stdout.write(JSON.stringify(details));
'''
        completed=subprocess.run(['node','-e',script],input=json.dumps({'expression':module.MEDIA_CONTROL,'css':CSS,'scenario':scenario,
                                                                     'errorText':' '.join(SYNTHETIC_ERROR_MARKERS)}),
                                 text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        self.assertEqual(completed.returncode,0,completed.stderr)
        return json.loads(completed.stdout)
    def test_media_batches_have_delivery_bounds_without_noop_activations(self):
        """Break: callback time becomes write time, per-record current values or all→all activation."""
        result=self.execute_media('batch')
        self.assertEqual(result['options'],{'attributes':True,'attributeFilter':['media'],'attributeOldValue':True})
        rows=result['state']['records']
        self.assertEqual([(r['batch'],r['orderWithinBatch'],r['oldValue'],r['currentMediaAtDelivery'],r['deliveredAtPerformanceMs']) for r in rows],
                         [(1,1,'print','all',200),(2,1,'all','all',300),(3,1,'print','all',400),(3,2,'all','all',400)])
        self.assertEqual([r['activationUpperBoundPerformanceMs'] for r in rows],[200,None,None,None])
        self.assertEqual((result['singleReads'],result['batchReads']),(1,1))
        self.assertEqual(result['state']['timingMeaning'],'DELIVERY_UPPER_BOUND_NOT_ATTRIBUTE_WRITE_TIME')
    def test_media_error_receipts_omit_arbitrary_native_text(self):
        """Break: media drain/disconnect error messages persist arbitrary native text in page receipts."""
        result=self.execute_media('untrusted-error')
        self.assertEqual((result['takes'],result['disconnects']),(1,1))
        self.assertFalse(result['closed']['disconnected'])
        self.assertEqual(len(result['closed']['secondaryErrors']),1)
        assert_external_error_omitted(self,result)

    def test_observation_error_omits_text_and_brackets_error_class_read(self):
        """Break: page error message is transported, or error metadata is read after its closing timestamp."""
        module=load('tools/cp9/r0007_font_ingress.py','observation_error_custody_subject')
        script=r'''
const input=JSON.parse(require('fs').readFileSync(0,'utf8'));let tick=10,lastRead=10,messageReads=0;
global.performance={now:()=>tick};global.window={__prayerFixture:{ordinal:1}};
global.document={querySelector:()=>({getBoundingClientRect:()=>({x:0,y:0,width:1,height:1})}),querySelectorAll:()=>[]};
const error={get name(){lastRead=++tick;return 'TypeError';},get message(){messageReads++;return input.errorText;}};
global.getComputedStyle=()=>{throw error;};
const observation=eval('('+input.expression+')')(input.css);
process.stdout.write(JSON.stringify({observation,lastRead,messageReads}));
'''
        result=subprocess.run(['node','-e',script],input=json.dumps({'expression':module.OBSERVATION,'css':CSS,
                            'errorText':' '.join(SYNTHETIC_ERROR_MARKERS)}),text=True,capture_output=True,check=True)
        result=json.loads(result.stdout);observation=result['observation']
        assert_external_error_omitted(self,result)
        self.assertEqual(result['messageReads'],0)
        self.assertEqual(observation['observationError']['name'],'TypeError')
        self.assertLessEqual(result['lastRead'],observation['pageReadFinishedMs'])
    def test_media_record_cap_retains_overflow_as_fatal_error(self):
        """Break: unlimited callback storage or silent loss of the seventeenth record."""
        result=self.execute_media('cap')
        self.assertEqual(len(result['atCap']['records']),16)
        self.assertIsNone(result['atCap']['firstError'])
        self.assertEqual(len(result['state']['records']),16)
        self.assertEqual(result['state']['totalRecords'],17)
        self.assertIn('cap',result['state']['firstError'])
    def test_media_close_drains_disconnects_and_is_idempotent(self):
        """Break: dropping queued attribute records or leaving the observer connected."""
        result=self.execute_media('cleanup')
        self.assertEqual(result['closed'],result['again'])
        self.assertEqual((result['takes'],result['disconnects']),(1,1))
        self.assertTrue(result['closed']['closed']);self.assertTrue(result['closed']['disconnected'])
        self.assertEqual(result['closed']['records'][0]['deliveryKind'],'cleanup-drain')
    def test_media_cleanup_and_callback_errors_are_retained(self):
        """Break: a failed drain skips disconnect or an unexpected callback loses its error."""
        result=self.execute_media('cleanup-error')
        self.assertEqual(result['disconnects'],1)
        self.assertEqual(result['closed']['firstError'],'OMITTED_UNTRUSTED_ERROR_TEXT')
        self.assertEqual(result['closed']['firstErrorDetails']['errorType'],'Error')
        self.assertIsNotNone(self.execute_media('callback-error')['state']['firstError'])
    def test_observation_error_retains_page_read_span(self):
        """Break: a style/read error discards both native page read timestamps."""
        module=load('tools/cp9/r0007_font_ingress.py','observation_error_subject')
        script=r'''
const fs=require('fs'),input=JSON.parse(fs.readFileSync(0,'utf8'));let tick=10;
global.performance={now:()=>++tick};global.window={__prayerFixture:{ordinal:1}};
global.document={querySelector:()=>({getBoundingClientRect:()=>({x:0,y:0,width:1,height:1})}),querySelectorAll:()=>[]};
global.getComputedStyle=()=>{throw Error('style read broke');};
process.stdout.write(JSON.stringify(eval('('+input.expression+')')(input.css)));
'''
        result=subprocess.run(['node','-e',script],input=json.dumps({'expression':module.OBSERVATION,'css':CSS}),
                              text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        self.assertEqual(result.returncode,0,result.stderr)
        observation=json.loads(result.stdout)
        self.assertEqual((observation['pageReadStartedMs'],observation['pageReadFinishedMs']),(11,12))
        self.assertEqual(observation['observationError'],{'name':'Error','message':'OMITTED_UNTRUSTED_ERROR_TEXT',
                                                        'messageProvenance':'OMITTED_UNTRUSTED_ERROR_TEXT'})

if __name__=='__main__': unittest.main()
