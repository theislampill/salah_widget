"""Primary-only serial browser bridge. D prepares this file but does not run browsers.

Production scripts remain exact; only the isolated fixture doubles the service,
storage, GPS and clipboard sinks. Stream cases use native fetch/Response/signal.
"""
import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
import traceback
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
ROOT = Path(r'C:\Users\theis\.codex\worktrees\hotfix-startup-clouds\salah_widget')
NODE = Path(r'C:\workspace\ai\cp9-integration-20261005\toolchain\node-v22.16.0-win-x64\node.exe')
SHA = '18ff14860ff41c084b1db5f396bb62aa9c22b1be'
RUNTIME = 'f443cf0820e6879dfa7c3ce857d6b2baf554b1fdd2f889433d22e2c532cec260'
sys.path.insert(0, str(ROOT / 'tools/cp9'))
from browser_runtime import browser_identity, launch_browser
from playwright.sync_api import sync_playwright


def dump(path, obj):
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf-8')


def fetch_json(url):
    with urllib.request.urlopen(url, timeout=3) as response:
        return json.load(response)


def check(row, name, value, detail=None):
    row['checks'].append({'name': name, 'passed': bool(value), 'detail': detail})
    if not value:
        raise AssertionError(name + ': ' + repr(detail))


def wait_predicate(page, predicate, arg=None, timeout=5000):
    # Browser-protocol function evaluation preserves the actual CSP. Playwright's
    # string wait_for_function path calls eval inside the protected document.
    until = time.monotonic() + timeout / 1000
    while time.monotonic() < until:
        if page.evaluate(predicate, arg):
            return
        page.wait_for_timeout(80)
    raise TimeoutError('Required function predicate did not become true: ' + predicate)


def app(page):
    return page.evaluate('() => (window.__locationFixture.application())')


def snap(page, row, name):
    value = app(page)
    row['snapshots'][name] = value
    return value


def settle(page):
    page.wait_for_timeout(120)


def pending(page, kind):
    wait_predicate(page, '(k)=>window.__locationFixture.pendingProviders(k).length>0', arg=kind, timeout=2500)
    return page.evaluate('(k)=>window.__locationFixture.pendingProviders(k).at(-1).id', kind)


def release(page, job, payload=None):
    if payload is None:
        page.evaluate('(id)=>window.__locationFixture.releaseProvider(id)', job)
    else:
        page.evaluate('([id,payload])=>window.__locationFixture.releaseProvider(id,payload)', [job, payload])
    settle(page)


def search(page, text, label='label'):
    page.locator('#' + label).fill(text)
    page.locator('#' + label).press('Enter')
    return pending(page, 'search')


def open_settings(page):
    page.locator('.buckle').click()
    wait_predicate(page, '() => (document.querySelector(".c").classList.contains("settings-open"))')
    page.wait_for_timeout(60)


def same_after(page, row, baseline, action, name):
    action()
    settle(page)
    current = snap(page, row, name)
    check(row, name + ' whole application unchanged', current == baseline, {'before': baseline, 'after': current})


def selected(page):
    return page.evaluate('()=>{const x=document.activeElement;return {id:x?.id,value:x?.value,readonly:x?.readOnly,start:x?.selectionStart,end:x?.selectionEnd}}')


def clipboard_failure(page, row, button):
    kind = 'embed' if button == 'copy' else 'install'
    tip = 'copied' if button == 'copy' else 'installtip'
    page.locator('#' + button).click()
    wait_predicate(page, '(id)=>!document.getElementById(id).disabled', arg=button)
    wait_predicate(page, '(kind)=>!document.getElementById(kind+"-recovery-wrap").hidden', arg=kind)
    payload = page.evaluate('() => (window.__locationFixture.copyJobs.at(-1).payload)')
    recovery = selected(page)
    status = page.locator('#' + tip).inner_text()
    raw_status = page.locator('#' + tip).evaluate('(x)=>x.textContent')
    folded = status.casefold()
    row['clipboard'].append({'button': button, 'captured': payload, 'selected': recovery, 'status': status, 'rawDOMStatus': raw_status})
    # Embed status inherits label{text-transform:uppercase} at builder.html19.
    # Keep both visible/raw strings and exclude success semantics/checkmarks.
    check(row, button + ' truthful failure', 'couldn' in folded and 'copy it manually' in folded and 'copied' not in folded and '✓' not in status and folded == raw_status.casefold(), {'rendered': status, 'raw': raw_status})
    check(row, button + ' native readonly exact selection', recovery == {'id': kind + '-recovery', 'value': payload, 'readonly': True, 'start': 0, 'end': len(payload)}, recovery)
    return payload


def caller_builder_coarse(page, row):
    coarse = pending(page, 'coarse')
    london = search(page, 'London')
    release(page, london)
    check(row, 'London first candidate', page.locator('#lat').input_value() == '51.50000', app(page))
    before = snap(page, row, 'current London before old coarse')
    same_after(page, row, before, lambda: release(page, coarse, {'latitude': '40.7', 'longitude': '-74', 'city': 'New York', 'country_code': 'US'}), 'late old coarse')
    page.locator('#label').press('Enter')
    check(row, 'same text cycles second candidate', page.locator('#lat').input_value() == '42.98000', app(page))
    page.locator('#label').press('Enter')
    check(row, 'candidate cycle returns first', page.locator('#lat').input_value() == '51.50000', app(page))
    cairo = search(page, 'Cairo')
    release(page, cairo)
    check(row, 'changed query replaces candidate owner', page.locator('#lat').input_value() == '30.04440', app(page))
    value = snap(page, row, 'current Cairo export')
    check(row, 'canonical snippet and preview carry current coordinates', 'lat=30.0444' in value['code'] and 'lat=30.0444' in value['previewSrc'], value)


def caller_builder_reverse(page, row):
    page.locator('#lat').fill('30')
    page.locator('#lon').fill('31')
    reverse = pending(page, 'reverse')
    london = search(page, 'London')
    release(page, london)
    before = snap(page, row, 'London after manual reverse launched')
    same_after(page, row, before, lambda: release(page, reverse, {'city': 'New York', 'countryCode': 'US', 'continentCode': 'NA'}), 'late old reverse')


def caller_builder_gps(page, row):
    page.locator('#geo').click()
    wait_predicate(page, '() => (window.__locationFixture.gpsCalls.length===1)')
    page.locator('#lat').fill('30')
    page.locator('#lon').fill('31')
    before = snap(page, row, 'manual builder before old GPS')
    same_after(page, row, before, lambda: page.evaluate('() => (window.__locationFixture.releaseGPS(0))'), 'late old builder GPS')
    check(row, 'manual chosen coordinates retained', before['inputs']['lat'] == '30' and before['inputs']['lon'] == '31', before)


def caller_settings_display(page, row):
    open_settings(page)
    check(row, 'real delayed label focus', selected(page)['id'] == 'set-label', selected(page))
    original = app(page)['inputs']
    london = search(page, 'London', 'set-label')
    page.locator('#set-label').fill('Cairo')
    page.locator('#set-label').press('Shift+Enter')
    before = snap(page, row, 'display only Cairo')
    same_after(page, row, before, lambda: release(page, london), 'late old settings London')
    check(row, 'Shift Enter retains previous coordinates', before['inputs']['set-lat'] == original['set-lat'] and before['inputs']['set-lon'] == original['set-lon'], before)
    page.locator('#set-label').press('Escape')
    wait_predicate(page, '() => (!document.querySelector(".c").classList.contains("settings-open"))')
    check(row, 'native Escape restores opener', page.evaluate('() => (document.activeElement.classList.contains("buckle"))'), selected(page))
    stored = json.loads(app(page)['savedBytes'])
    check(row, 'close autosaves current form', stored['label'] == 'Cairo' and float(stored['lat']) == float(original['set-lat']), stored)
    open_settings(page)
    late = search(page, 'London', 'set-label')
    page.locator('#setClose').click()
    open_settings(page)
    before = snap(page, row, 'reopened session')
    same_after(page, row, before, lambda: release(page, late), 'callback from closed session')
    focusables = [handle for handle in page.locator('#settings a[href],#settings button,#settings input,#settings select,#settings [tabindex]').element_handles()
        if handle.evaluate('(x)=>!x.disabled&&x.offsetParent!==null&&x.getAttribute("tabindex")!=="-1"')]
    first, last = focusables[0], focusables[-1]
    describe = '(x)=>({id:x.id,tag:x.tagName,ariaLabel:x.getAttribute("aria-label"),href:x.getAttribute("href")})'
    limits = {'first': first.evaluate(describe), 'last': last.evaluate(describe)}
    # The real footer anchors have no id (src/native/index.html640-654).
    # Focus actual native handles; do not invent ids or change production DOM.
    last.focus()
    page.keyboard.press('Tab')
    check(row, 'native focus wraps at end', page.evaluate('(expected)=>document.activeElement===expected', first), selected(page))
    page.keyboard.press('Shift+Tab')
    check(row, 'native focus wraps at start', page.evaluate('(expected)=>document.activeElement===expected', last), selected(page))
    row['focusReadback'] = {'limits': limits, 'final': selected(page)}


def caller_settings_candidates(page, row):
    open_settings(page)
    london = search(page, 'London', 'set-label')
    release(page, london)
    page.locator('#set-label').press('Enter')
    check(row, 'settings cycles Ontario', page.locator('#set-lat').input_value() == '42.98000', app(page))
    cairo = search(page, 'Cairo', 'set-label')
    release(page, cairo)
    check(row, 'settings new candidate query', page.locator('#set-lat').input_value() == '30.04440', app(page))
    page.locator('#set-pin').click()
    wait_predicate(page, '() => (window.__locationFixture.gpsCalls.length===1)')
    page.evaluate('() => (window.__locationFixture.releaseGPS(0))')
    wait_predicate(page, '() => (document.getElementById("set-lat").value==="52.52000")')
    check(row, 'current GPS positive accepted with accessible accuracy', '25 m' in app(page)['pin']['name'], app(page))
    page.locator('#set-label').press('Escape')
    stored = json.loads(app(page)['savedBytes'])
    check(row, 'actual close retains GPS acquisition', stored['locationEvidence']['accuracyM'] == 25 and stored['locationEvidence']['acquiredAt'] == 1790942400000, stored)
    open_settings(page)
    check(row, 'saved fix accessible source', 'Saved browser position' in app(page)['pin']['name'], app(page))


def caller_settings_gps(page, row):
    open_settings(page)
    page.locator('#set-pin').click()
    wait_predicate(page, '() => (window.__locationFixture.gpsCalls.length===1)')
    page.locator('#set-lat').fill('30')
    page.locator('#set-lon').fill('31')
    before = snap(page, row, 'manual settings before old GPS')
    same_after(page, row, before, lambda: page.evaluate('() => (window.__locationFixture.releaseGPS(0))'), 'late old settings GPS')
    page.locator('#set-label').press('Escape')
    open_settings(page)
    value = app(page)
    check(row, 'manual config saved and reopened', value['inputs']['set-lat'] == '30' and value['inputs']['set-lon'] == '31' and value['config']['locationEvidence']['intent'] == 'fixed-site', value)
    page.locator('#set-pin').click()
    wait_predicate(page, '() => (window.__locationFixture.gpsCalls.length===2)')
    page.locator('#setClose').click()
    open_settings(page)
    before = snap(page, row, 'reopened before old GPS')
    same_after(page, row, before, lambda: page.evaluate('() => (window.__locationFixture.releaseGPS(1))'), 'old GPS from closed session')


def caller_settings_reset(page, row):
    open_settings(page)
    page.locator('#set-reset').click()
    coarse = pending(page, 'coarse')
    page.locator('#set-lat').fill('30')
    page.locator('#set-lon').fill('31')
    before = snap(page, row, 'manual input supersedes pending reset')
    same_after(page, row, before, lambda: release(page, coarse), 'late old reset detection')
    page.locator('#setClose').click()
    open_settings(page)
    page.locator('#set-reset').click()
    coarse = pending(page, 'coarse')
    page.locator('#setClose').click()
    open_settings(page)
    before = snap(page, row, 'reopened before old reset')
    same_after(page, row, before, lambda: release(page, coarse), 'old reset from closed session')
    page.locator('#set-reset').click()
    current = pending(page, 'coarse')
    page.locator('#set-units').select_option('f')
    release(page, current)
    wait_predicate(page, '() => (Number(document.getElementById("set-lat").value)===24.47)')
    check(row, 'positive current reset with newer preference', app(page)['inputs']['set-units'] == 'f' and app(page)['savedBytes'] is None, app(page))


def caller_copy_long(page, row):
    page.locator('#label').fill('Long display ' + '<&\" apostrophe\' ' * 30)
    clipboard_failure(page, row, 'copy')
    command = clipboard_failure(page, row, 'install')
    check(row, 'Windows carried command exact fixture', "$env:SALAH_WIDGET_HASH='" in command and 'install.ps1 | iex' in command, command)
    page.keyboard.press('Tab')
    check(row, 'native Tab moves onward', selected(page)['id'] != 'install-recovery', selected(page))
    page.set_viewport_size({'width': 390, 'height': 844})
    clipboard_failure(page, row, 'copy')
    clipboard_failure(page, row, 'install')
    geometry = page.evaluate('()=>({width:innerWidth,body:document.body.scrollWidth,root:document.documentElement.scrollWidth,areas:[...document.querySelectorAll(".manual-recovery:not([hidden]) textarea")].map(x=>({id:x.id,client:x.clientWidth,scroll:x.scrollWidth,left:x.getBoundingClientRect().left,right:x.getBoundingClientRect().right}))})')
    row['geometry'] = geometry
    check(row, 'narrow page avoids horizontal overflow', geometry['body'] <= 391 and geometry['root'] <= 391 and all(x['left'] >= 0 and x['right'] <= 391 for x in geometry['areas']), geometry)


def caller_copy_pending(page, row):
    captured = page.locator('#code').input_value()
    page.locator('#copy').click()
    wait_predicate(page, '() => (window.__locationFixture.copyJobs.length===1)')
    check(row, 'native button disabled while awaiting', page.locator('#copy').is_disabled())
    page.locator('#label').fill('Changed after capture')
    current = page.locator('#code').input_value()
    check(row, 'pending form really changes canonical output', captured != current, {'captured': captured, 'current': current})
    page.evaluate('() => (window.__locationFixture.releaseCopy(0,false))')
    wait_predicate(page, '() => (!document.getElementById("embed-recovery-wrap").hidden)')
    check(row, 'native recovery selects captured old iframe', selected(page)['value'] == captured and selected(page)['end'] == len(captured), selected(page))
    check(row, 'canonical output stays current', page.locator('#code').input_value() == current)
    page.evaluate('() => (window.__locationFixture.copyMode="deny")')
    command = clipboard_failure(page, row, 'install')
    check(row, 'Bash carried command exact fixture', "| SALAH_WIDGET_HASH='" in command and command.endswith("' bash"), command)


def caller_copy_timers(page, row):
    for button, tip in [('copy', 'copied'), ('install', 'installtip')]:
        page.evaluate('() => (window.__locationFixture.copyMode="success")')
        page.locator('#' + button).click()
        wait_predicate(page, '(id)=>!document.getElementById(id).disabled', arg=button)
        check(row, button + ' current success restores button focus', selected(page)['id'] == button and 'copied' in page.locator('#' + tip).inner_text().lower(), selected(page))
        page.evaluate('() => (window.__locationFixture.copyMode="deny")')
        clipboard_failure(page, row, button)
    page.wait_for_timeout(9000)
    for kind, tip in [('embed', 'copied'), ('install', 'installtip')]:
        status = page.locator('#' + tip).inner_text()
        check(row, kind + ' manual recovery and failure persist beyond old timer', page.locator('#' + kind + '-recovery-wrap').is_visible() and 'couldn' in status.casefold() and 'copied' not in status.casefold() and '✓' not in status, status)


def caller_copy_fallback(page, row):
    for button, tip in [('copy', 'copied'), ('install', 'installtip')]:
        expected = page.evaluate('()=>document.getElementById("code").value' if button == 'copy' else '()=>installCmd().cmd')
        page.locator('#' + button).click()
        wait_predicate(page, '(id)=>!document.getElementById(id).disabled', arg=button)
        call = page.evaluate('() => (window.__locationFixture.fallbackCalls.at(-1))')
        check(row, button + ' native textarea fallback exact bytes', call['payload'] == expected and call['selectionStart'] == 0 and call['selectionEnd'] == len(expected), call)
        check(row, button + ' true fallback reports success and returns focus', 'copied' in page.locator('#' + tip).inner_text().lower() and selected(page)['id'] == button, selected(page))


def stream_case(page, row, origin, mode, caller):
    began = time.monotonic()
    if mode == 'fail' and caller == 'widget':
        wait_predicate(page, '() => (document.querySelector(".c").classList.contains("settings-open"))', timeout=14000)
        check(row, 'native failed widget opens manual form', page.locator('#set-label').is_visible(), app(page))
        page.locator('#set-label').fill('Manual recovery')
        page.locator('#set-label').press('Shift+Enter')
        page.locator('#set-lat').fill('30')
        page.locator('#set-lon').fill('31')
        page.locator('#setClose').click()
        wait_predicate(page, '() => (window.qaState().config.lat===30)', timeout=4000)
        check(row, 'actual manual form restores configured target', app(page)['config']['lon'] == 31, app(page))
    elif mode == 'fail':
        wait_predicate(page, '() => (document.getElementById("geotip").textContent.includes("Couldn"))', timeout=14000)
        check(row, 'native failed builder offers manual recovery', 'type a place' in app(page)['status'] and 'off' in app(page)['pin']['classes'], app(page))
    else:
        target = 51.5 if mode == 'stall' else 24.47
        if caller == 'widget':
            wait_predicate(page, '(target)=>window.qaState().config.lat===target', arg=target, timeout=14000)
        else:
            wait_predicate(page, '(target)=>Number(document.getElementById("lat").value)===target&&document.getElementById("geotip").textContent.startsWith("Detected")', arg=target, timeout=14000)
        check(row, 'native full-body result reaches ' + caller, True, app(page))
    settle(page)
    row['elapsedConsumerSeconds'] = time.monotonic() - began
    jobs = page.evaluate('window.__locationFixture.providerJobs.filter(x=>x.kind==="coarse-stream")')
    records = [x for x in fetch_json(origin + '/ledger')[row['ledgerStart']:] if x['path'] != '/ledger']
    row['nativeStreamJobs'] = jobs
    row['nativeStreamLedger'] = records
    if mode == 'stall':
        check(row, 'native headers observed before body abort', len(jobs) == 2 and jobs[0].get('headersReturned') and jobs[0]['signalAborted'] and jobs[0]['http'] == 200, jobs)
        check(row, 'one healthy native fallback, stalled socket closes without completion', [x['path'] for x in records] == ['/geojs-stall', '/ipinfo'] and records[0]['closedAt'] is not None and not records[0]['completed'] and records[1]['completed'], records)
    elif mode == 'finite':
        check(row, 'healthy finite body has no fallback or abort', len(jobs) == 1 and not jobs[0]['signalAborted'] and [x['path'] for x in records] == ['/geojs-finite'] and records[0]['completed'], {'jobs': jobs, 'ledger': records})
    else:
        check(row, 'exhaustion uses exactly two failed providers', len(jobs) == 2 and all(x['http'] == 503 for x in jobs) and [x['path'] for x in records] == ['/failure', '/failure'], {'jobs': jobs, 'ledger': records})


CALLER = [
    ('15-builder-coarse-candidates', {'page': 'builder', 'hold': 'coarse,search', 'gps': 'held'}, caller_builder_coarse),
    ('15-builder-reverse-search', {'page': 'builder', 'hold': 'reverse,search'}, caller_builder_reverse),
    ('15-builder-gps-manual', {'page': 'builder', 'gps': 'held'}, caller_builder_gps),
    ('15-settings-display-close-session', {'page': 'widget', 'seed': 'none', 'hold': 'search', 'gps': 'held'}, caller_settings_display),
    ('15-settings-candidates-current-gps', {'page': 'widget', 'seed': 'manual', 'hold': 'search', 'gps': 'held'}, caller_settings_candidates),
    ('15-settings-gps-manual', {'page': 'widget', 'seed': 'manual', 'gps': 'held'}, caller_settings_gps),
    ('15-settings-reset-ownership', {'page': 'widget', 'seed': 'manual', 'hold': 'coarse'}, caller_settings_reset),
    ('18-denied-copy-responsive-Windows-payload', {'page': 'builder', 'copy': 'deny', 'fallback': 'false', 'platform': 'Win32', 'hold': 'search'}, caller_copy_long),
    ('18-pending-captured-copy-Bash-payload', {'page': 'builder', 'copy': 'hold', 'fallback': 'throw', 'platform': 'MacIntel', 'hold': 'search'}, caller_copy_pending),
    ('18-success-then-failure-old-timers', {'page': 'builder', 'copy': 'success', 'fallback': 'false'}, caller_copy_timers),
    ('18-absent-clipboard-true-fallback', {'page': 'builder', 'copy': 'absent', 'fallback': 'true'}, caller_copy_fallback),
]


def run(args):
    args.out.mkdir(parents=True, exist_ok=True)
    os.environ['SALAH_BROWSER'] = args.browser
    if args.executable:
        os.environ['SALAH_BROWSER_EXECUTABLE'] = args.executable
    report = {'status': 'RUNNING', 'target': SHA, 'runtime': RUNTIME, 'origin': args.origin, 'group': args.group,
        'environment': {'python': sys.version, 'platform': platform.platform()}, 'cases': [],
        'fixtureSha256': hashlib.sha256((HERE / 'r0023-current-native.html').read_bytes()).hexdigest(),
        'driverSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'effects': 'Disposable serial browser contexts and read-only loopback fixture only; no real location/storage/clipboard/provider or installer sink.',
        'limitations': ['Service/GPS/copy doubles prove native consumer events and selections, not provider availability or actual clipboard/Permissions Policy authorization.', 'Original synthetic fixed UTC epoch and fallback fonts retained; no production-font or astronomical qualification.', 'Windows/Bash payload branches use explicit platform doubles; no native Apple Bash or installer execution is claimed.', 'Screenshots require primary visual inspection; machine checks cannot establish readability.', '#16/#17/#35 mandatory documentation gaps and untested iframe policy remain open.']}
    entries = CALLER[:] if args.group in ('all', 'caller') else []
    if args.group in ('all', 'stream'):
        for caller in ('builder', 'widget'):
            for mode in ('stall', 'finite', 'fail'):
                entries.append((f'31-{caller}-native-{mode}', {'page': caller, 'seed': 'none', 'stream': mode}, (caller, mode)))
    inherited = []
    if args.resume_after:
        if not args.prior_results:
            raise ValueError('--resume-after requires --prior-results for exact custody; no implicit replay or assumed prior PASS')
        prior = json.loads(args.prior_results.read_text(encoding='utf-8-sig'))
        assert prior['target'] == SHA and prior['runtime'] == RUNTIME and prior['fixtureSha256'] == report['fixtureSha256']
        names = [entry[0] for entry in entries]
        if args.resume_after not in names:
            raise ValueError('Resume entry is outside the selected group')
        index = names.index(args.resume_after)
        prior_by_name = {case['name']: case for case in prior['cases']}
        for name in names[:index + 1]:
            case = prior_by_name[name]
            assert case['status'] == 'MACHINE_CHECKS_PASS_VISUAL_REVIEW_PENDING' and all(check['passed'] for check in case['checks'])
            assert case['fixtureIdentity']['state'] == 'ready' and case['fixtureIdentity']['bodiesPreserved']
            picture = args.prior_results.parent / case['screenshot']
            assert picture.is_file()
            inherited.append({'name': name, 'classification': 'REUSED_PRIMARY_NATIVE_IDENTICAL_TARGET_AND_FIXTURE', 'case': case,
                'screenshotPath': str(picture), 'screenshotSha256': hashlib.sha256(picture.read_bytes()).hexdigest()})
        entries = entries[index + 1:]
        report['priorReceipt'] = {'path': str(args.prior_results), 'sha256': hashlib.sha256(args.prior_results.read_bytes()).hexdigest(), 'browser': prior['browser']}
    if args.only:
        chosen = set(args.only)
        if chosen - {entry[0] for entry in entries}:
            raise ValueError('--only includes entry outside remaining selected group')
        entries = [entry for entry in entries if entry[0] in chosen]
    report['inheritedCases'] = inherited
    report['selectedEntries'] = [entry[0] for entry in entries]
    if not entries:
        raise ValueError('No remaining entries selected')
    process = None
    origin = args.origin
    if not origin:
        process = subprocess.Popen([str(NODE), str(HERE / 'audit-server.cjs'), '0'], stdout=subprocess.PIPE, stderr=(args.out / 'audit-server.stderr.log').open('w', encoding='utf-8'), text=True)
        announced = json.loads(process.stdout.readline())
        origin = announced['origin']
    report['origin'] = origin
    try:
        with sync_playwright() as playwright:
            browser = launch_browser(playwright)
            report['browser'] = browser_identity(browser)
            try:
                for name, options, action in entries:
                    row = {'name': name, 'status': 'RUNNING', 'options': options, 'checks': [], 'snapshots': {}, 'clipboard': [], 'pageErrors': [], 'outsideRequests': []}
                    report['cases'].append(row)
                    context = browser.new_context(viewport={'width': 1000, 'height': 900}, device_scale_factor=1, reduced_motion='reduce', service_workers='block')
                    page = context.new_page()
                    page.set_default_timeout(5000)
                    page.on('pageerror', lambda error, r=row: r['pageErrors'].append(str(error)))
                    def gate(route, r=row):
                        url = route.request.url
                        if url.startswith(origin + '/') or url.startswith(('blob:', 'data:', 'about:')):
                            route.continue_()
                        else:
                            r['outsideRequests'].append(url)
                            route.abort()
                    context.route('**/*', gate)
                    prepared = False
                    try:
                        row['ledgerStart'] = len(fetch_json(origin + '/ledger'))
                        params = {'detect': 'success', 'seed': 'none', 'gps': 'unsupported', **options}
                        url = origin + '/audit/r0023-current-native.html?' + urllib.parse.urlencode(params) + ('#local=1' if options['page'] == 'widget' else '')
                        row['entry'] = url
                        page.goto(url, wait_until='domcontentloaded', timeout=12000)
                        wait_predicate(page, '() => (window.__locationFixture && ["ready","error"].includes(window.__locationFixture.state))', timeout=12000)
                        identity = page.evaluate('()=>{const f=window.__locationFixture;return {state:f.state,error:f.error,target:f.target,source:f.sourceSha256,config:f.configSha256,runtime:f.runtimeInventorySha256,scriptCount:f.scriptCount,bodiesPreserved:f.productionScriptBodiesPreserved,storageIsolated:f.storageIsolated,clockFixed:f.clockFixed}}')
                        row['fixtureIdentity'] = identity
                        check(row, 'exact current script guards and isolated hooks initialize', identity['state'] == 'ready' and not identity['error'] and identity['target'] == SHA and identity['runtime'] == RUNTIME and identity['bodiesPreserved'] and identity['storageIsolated'] and identity['clockFixed'] and identity['scriptCount'] == (6 if options['page'] == 'widget' else 2), identity)
                        prepared = True
                        if options.get('hold') != 'coarse,search' and not options.get('stream'):
                            settle(page)
                        if isinstance(action, tuple):
                            stream_case(page, row, origin, action[1], action[0])
                        else:
                            action(page, row)
                        row['finalApplication'] = app(page)
                        row['fixtureRecords'] = page.evaluate('()=>{const f=window.__locationFixture;return {providerJobs:f.providerJobs,gpsCalls:f.gpsCalls,copyJobs:f.copyJobs,fallbackCalls:f.fallbackCalls,errors:f.errors,storageEvents:f.storageEvents}}')
                        check(row, 'no unhandled or unexpected sink errors', not row['pageErrors'] and not row['outsideRequests'] and not row['fixtureRecords']['errors'], {'pageErrors': row['pageErrors'], 'outsideRequests': row['outsideRequests'], 'fixtureErrors': row['fixtureRecords']['errors']})
                        row['status'] = 'MACHINE_CHECKS_PASS_VISUAL_REVIEW_PENDING'
                    except Exception as error:
                        row['status'] = 'FAIL'
                        row['error'] = str(error)
                        row['traceback'] = traceback.format_exc()
                    finally:
                        try:
                            # Original wrapper removes remote font links and CSP
                            # blocks fonts. Observe settling without changing font
                            # APIs/security; bound the screenshot even on failure.
                            try:
                                wait_predicate(page, '()=>!document.fonts||document.fonts.status==="loaded"', timeout=2500)
                                row['fontStatus'] = 'settled'
                            except TimeoutError:
                                row['fontStatus'] = 'not settled within2500ms'
                            page.screenshot(path=str(args.out / (name + '.png')), full_page=True, timeout=7000)
                            row['screenshot'] = name + '.png'
                        except Exception as error:
                            row['screenshotError'] = str(error)
                        dump(args.out / (name + '.json'), row)
                        context.close()
                        dump(args.out / 'results.json', report)
                    if not prepared:
                        report['stopReason'] = 'Fixture initialization failed; remaining cases not attempted to avoid redundant browser work.'
                        break
            finally:
                browser.close()
        report['status'] = 'MACHINE_CHECKS_PASS_VISUAL_REVIEW_PENDING' if len(report['cases']) == len(entries) and all(x['status'] == 'MACHINE_CHECKS_PASS_VISUAL_REVIEW_PENDING' for x in report['cases']) else 'FAIL'
    finally:
        if process:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=3)
        dump(args.out / 'results.json', report)
    print(json.dumps({'status': report['status'], 'cases': len(report['cases']), 'out': str(args.out)}))
    return 0 if report['status'] == 'MACHINE_CHECKS_PASS_VISUAL_REVIEW_PENDING' else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--group', choices=['caller', 'stream', 'all'], default='all')
    parser.add_argument('--browser', choices=['chromium', 'firefox', 'webkit'], default='chromium')
    parser.add_argument('--executable')
    parser.add_argument('--origin', help='Optional already running owned audit-server origin')
    parser.add_argument('--resume-after', help='Resume after named successful entry, preserving prior receipts')
    parser.add_argument('--prior-results', type=Path, help='Exact prior results.json used for reuse custody')
    parser.add_argument('--only', action='append', help='Select exact remaining case name; repeat for a subset')
    parser.add_argument('--out', type=Path, default=HERE / 'native-consumer-results')
    raise SystemExit(run(parser.parse_args()))
