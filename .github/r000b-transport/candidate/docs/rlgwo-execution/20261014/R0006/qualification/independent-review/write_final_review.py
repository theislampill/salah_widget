"""Write the independent pre-delivery finding from already inspected original evidence."""
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent


def read(name):
    return json.loads((HERE / name).read_bytes())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def readable(value):
    if isinstance(value, dict):
        return {key: readable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [readable(item) for item in value]
    if not isinstance(value, str):
        return value
    replacements = {
        'All135': 'All 135', 'All31': 'All 31', 'All20': 'All 20',
        'all31': 'all 31', 'all20': 'all 20', 'all135': 'all 135',
        'Twenty selected': 'Twenty selected', 'has72pass': 'has 72 pass',
        'has91 exact': 'has 91 exact', 'have91 exact': 'have 91 exact',
        'contains72passing': 'contains 72 passing', '0failures': '0 failures',
        '0skips': '0 skips', '0TODO': '0 TODO', '0fail': '0 fail', '0skip': '0 skip',
        'comment607': 'comment 607', 'Comment607': 'Comment 607',
        'source18ff': 'source 18ff', 'accepted6.': 'accepted 6.', 'Accepted6.': 'Accepted 6.',
        'all residualA01': 'all residual A01', 'all original6.': 'all original 6.',
        'all residualA': 'all residual A', '20selected': '20 selected',
        '31retained': '31 retained', '23derivedJSON': '23 derived JSON',
        '23 newly': '23 newly', '57local-only': '57 local-only',
        'only23': 'only 23', 'through65': 'through 65', 'after65': 'after 65',
        'the60': 'the 60', 'original30': 'original 30', 'qualified30': 'qualified 30',
        'normal30': 'normal 30', 'supported15': 'supported 15',
        'including3021': 'including 3021', 'Chromium3021': 'Chromium 3021',
        'Firefox5057': 'Firefox 5057', 'contains3021': 'contains 3021',
        'and5057': 'and 5057', 'traces532790911': 'traces 532790911',
        'from507872': 'from 507872', 'byte XZ': 'byte XZ',
        'with100': 'with 100', 'and100': 'and 100', 'full10000': 'full 10000',
        'three10000': 'three 10000', 'asynchronous10000': 'asynchronous 10000',
        'nominal32700': 'nominal 32700', 'nominal32.7': 'nominal 32.7',
        'ordered16-item': 'ordered 16-item', 'original120x': 'original 120x',
        'canonical10-case': 'canonical 10-case', 'snapshot': 'snapshot',
        'at5/15/30': 'at 5/15/30', 'SHA256290': 'SHA256 290',
        'SHA2562d8': 'SHA256 2d8', 'SHA256960': 'SHA256 960',
        'Playwright1.60': 'Playwright 1.60', 'chrome.exe148': 'chrome.exe 148',
        'TIMESCALE0': 'TIMESCALE 0', 'TIMESCALE120': 'TIMESCALE 120',
        'UTC2026': 'UTC 2026', 'lat24.47/lon39.61/method4/school0': 'latitude 24.47 / longitude 39.61 / method 4 / school 0',
        'y1200': 'y=1200', 'y0/325x530': 'y=0 / 325x530',
        'frame1522': 'frame 1522', 'Sep7': 'Sep 7', 'Sep8': 'Sep 8', 'Sep9': 'Sep 9',
        'frozenV1': 'frozen V1',
    }
    for old, new in replacements.items():
        value = value.replace(old, new)
    value = re.sub(r'(?<=\d)(ms|s)\b', r' \1', value)
    value = re.sub(r'\b(frame|first recovered|first cached|initial loading|recovered-state|first initial|first promoted|Initial|initial|refresh|refreshed)(?=\d)', r'\1 ', value)
    value = re.sub(r'(?<=\d)(files|bytes)\b', r' \1', value)
    value = re.sub(r'\bnames(?=\d)', 'names ', value)
    return value


def main():
    bindings = read('bindings.json')
    traces = read('selected-trace-review.json')
    pixels = read('native-pixel-index.json')
    projection = read('public-projection-review.json')
    portable = read('portable-path-review.json')
    assert not bindings['failures'] and not projection['failures']
    assert traces['count'] == pixels['selectedCount'] == bindings['selectedCount'] == 20
    assert all(row['status'] == 'PASS_TRACE_ONLY' and not row['errors'] for row in traces['traces'])
    assert all(row['boundedVerdict'] == 'PASS_FIRST_PRESENTATION_ONLY' for row in pixels['entries'] if row['selected'])
    assert all(not row['continuousClipCredit'] and not row['motionCredit'] for row in pixels['entries'])
    assert bindings['selectionSha256'] == traces['selectionSha256'] == pixels['selectionSha256']
    assert portable['filesChanged'] == 23

    rows = [
        ('6.01', 'ACCEPTED_CURRENT', 'One operation retains its slot across at most three attempts; controller/deadline belongs to the attempt; obsolete generation stops and cannot release its successor.', 'Exact original owner spans and ownership tests retained; native cold/third-success/generation receipts separately identify operation, attempt, timer and generation.'),
        ('6.02', 'ACCEPTED_CURRENT', '10000ms deadline begins before fetch and covers pending asynchronous body/admission; terminal paths clear it and observe late settlement.', 'Both cold-body traces have immediate ok headers, unresolved JSON, three real deadline firings and cleanup. Original headers-hang/body-hang and headers-only mutant controls remain current.'),
        ('6.03', 'ACCEPTED_CURRENT', 'At most three attempts with 900/1800ms backoffs; success exits immediately and eligible attempts do not overlap.', 'Native third-success is exactly three current calls with one adoption and no fourth current retry. Cold attempts retain one operation. Timer receipts and original source tests agree.'),
        ('6.04', 'ACCEPTED_CURRENT', 'Late ignored-abort bodies, delayed deadlines and old finally cannot mutate adopted data/cache/error or release a newer slot.', 'Cold before/after late-release checkpoints are stable; generation A/B receipts preserve B. Exact original delayed-timer and ownership controls remain current.'),
        ('6.05', 'ACCEPTED_CURRENT', 'Eligibility is generation/day/operation-specific real elapsed time, 60000ms from operation start, with busy ownership separate.', 'Native cold, frozen TIMESCALE0 and accelerated TIMESCALE120 recover only after the real fence. Original forward/backward wall-clock and failed-prefetch controls retained.'),
        ('6.06', 'ACCEPTED_CURRENT', 'Cold failure settles boot/apply so the existing loop can schedule same-day missing data despite early render return.', 'Both cold-body traces settle three attempts, retain unavailable state during cooldown, dispatch fourth current call and render admitted Sep7 without reload or midnight.'),
        ('6.07', 'ACCEPTED_CURRENT', 'Admitted current cache remains usable through refresh/network/persistence failure; no fabricated timetable or false network-current claim.', 'Native cache-offline and denied-write controls preserve adopted current data. Healthy refresh remains in memory when persistence is denied. Boot loading before cache adoption is not treated as a post-adoption blank.'),
        ('6.08', 'ACCEPTED_CURRENT', 'Failed tomorrow retains its day-specific cooldown; matching usable tomorrow suppresses redundant calls; promotion permits the next successor once.', 'Original failed-tomorrow starts/backoffs remain current. Native matching tomorrow is held beyond65s with no redundant request, then Sep8 promotion produces exactly one Sep9 prefetch.'),
        ('6.09', 'ACCEPTED_CURRENT', 'New generation/day does not inherit old failure locks; late adoption/reclassification cannot clear unrelated active owners.', 'Native generation A to B retains B through late A cleanup. Original pending-owner, reverse-day, null/remove-retirement controls are unchanged and passing.'),
        ('6.10', 'ACCEPTED_CURRENT', 'Existing hidden/offscreen pause is retained; first eligible resumed opportunity starts one operation without catch-up or background promise.', 'Selected native stimulus moves the actual card to y1200 while document stays visible, observes paused state across the fence, restores y0/325x530 and obtains one fourth current call. This is offscreen-branch evidence only.'),
        ('6.11', 'ACCEPTED_CURRENT', 'Monotonic cadence claim is limited to performance.now hosts; Date.now-only fallback is not promised monotonic.', 'Current source and README retain that limit. Qualified browser controls use native performance elapsed time; no fallback-host or universal-host qualification is inferred.'),
        ('6.12', 'ACCEPTED_CURRENT', 'Deadline, cold-data branch and outer-cooldown negative mutations must fail the actual caller fixtures with real backoff accounting.', 'Five original test files and the affected original owners are equal after newline normalization. Retained current TAP has72pass,0fail,0skip,0TODO; the original mutation assertions remain present, not replaced by a green checker aggregate.'),
        ('6.13', 'CONTENT_QUALIFIED_DELIVERY_PENDING', 'README accurately states finite attempts, nominal asynchronous bound, recovery/cache/day/visibility and fallback limitations.', 'A01 content qualified at the exact README SHA. Its required public merge and delivery remain in A07.'),
        ('6.14', 'ACCEPTED_CURRENT', 'Preserve one rAF loop, offscreen pause, preferences, readable card, opaque Moon and existing provider/schema/runtime boundaries.', 'All135 runtime files match base. Eight exact qualified preservation controls/91files retain supported normal/reduced/full motion and warm opaque Moon in their original environments. No new runtime, reload feature, provider or schema change.'),
        ('6.15', 'PRE_DELIVERY_QUALIFIED', 'Native unavailable-to-recovered evidence plus supported15-60s default motion and exact preservation controls.', 'A02-A05 qualified within the stated state/image and original30s preservation scopes. No fresh functional clip is credited as continuously readable or as motion proof; all contrary native frames remain failures.'),
        ('6.16', 'A06_QUALIFIED_A07_RESERVED', 'All three liveness subcases and independent ownership/cleanup qualification precede delivered source/docs/consumer readback and closure.', 'This exact candidate satisfies A06 pre-delivery. A07, delivered-proof schema, owner merge authorization, evidence comment and manual closure are not supplied by this review.'),
    ]
    residuals = [
        ('R0006-A01', 'PRE_DELIVERY_QUALIFIED', [
            'README has three full asynchronous10000ms attempts,900/1800ms backoffs and nominal32700ms plus event-loop delay.',
            'It explicitly rejects a hard CPU/provider-latency guarantee, retains the60s operation-start cadence, usable-cache rules, matching-tomorrow suppression and day/generation reclassification.',
            'Hidden/offscreen pause, first resumed eligible opportunity, no catch-up/background guarantee, simulation/wall independence on performance hosts and nonmonotonic Date.now fallback are explicit.',
            'Inherited location-day, invalid/absent-data precision and no-offline-application clauses remain accurate; only the reviewed retry clarification changes. Public delivery is pending A07.'
        ], ['bindings.json', '../docs-review.json']),
        ('R0006-A02', 'PRE_DELIVERY_QUALIFIED', [
            'Empty cache; UTC2026-09-07T12:00Z; lat24.47/lon39.61/method4/school0; native progressing Date and native timers; three immediate-ok-header, unresolved-JSON attempts.',
            'Three10000ms timers fire and clear,900/1800ms waits occur, ownership releases after nominal32.7s plus measured delay, and no current call occurs during cooldown.',
            'Healthy fourth current call occurs at/after operation-start+60000ms and commits the same Sep7 with complete earliest native recovered card; normal tomorrow prefetch is a separate kind.',
            'Late release of all stalled ignored-abort bodies leaves adopted data/cache/error/slots unchanged. Loading-body-pending and exhausted-unavailable images are honest; native first-frame and continuity limits remain explicit.'
        ], ['selected-trace-review.json', 'native-pixel-index.json', '../../native/chromium/R0006-cold-body', '../../native/firefox/R0006-cold-body']),
        ('R0006-A03', 'PRE_DELIVERY_QUALIFIED', [
            'Actual widget IntersectionObserver pause, y1200/document-visible, persists through the60s fence; restoring the saved inline translation restores y0/325x530 and one eligible fourth current call after65s.',
            'Frozen TIMESCALE0 and accelerated TIMESCALE120 cases retain native performance timers and same-day recovery; all completed snapshots are retained, including3021/5057 original accelerated renders.',
            'New-generation B adopts and owns its slots while ignored-abort late A settlement cannot release B. Original wall-forward/backward and day-owner controls remain current.',
            'Failed parent-display and headed observer attempts remain contrary/incomplete; no document-hidden success or background-recovery claim is made.'
        ], ['bindings.json', 'selected-trace-review.json', 'native-pixel-index.json']),
        ('R0006-A04', 'PRE_DELIVERY_QUALIFIED', [
            'Two prompt failures followed by success yield exactly three current calls,900/1800ms native waits, one adopted record and no fourth current retry.',
            'Selected admitted cache stays in the product state during actual offline refresh failure; denied writes preserve in-memory usable data and healthy refresh. Original first cache and first refreshed images are inspected separately.',
            'A usable matching tomorrow suppresses redundant acquisition through65s; actual civil-day promotion uses that record and makes only one next successor eligible.',
            'Original deadline/cold-branch/cooldown mutant TAP and exact owners remain current. Firefox promotion uses the separately bound existing headed/video-only mode with100ms observation polling; no product/provider/clock/scheduler behavior is changed.'
        ], ['bindings.json', 'selected-trace-review.json', 'native-pixel-index.json']),
        ('R0006-A05', 'PRE_DELIVERY_QUALIFIED', [
            'Twenty selected case/engine acquisitions have complete bounded earliest native current/recovery images; promotion additionally checks the earliest new-day image. All six rows, clocks, header/buckle, arc/next/countdown and CE/AH footer fit the325x530 card.',
            'Loading while a body is pending and exhausted unavailable state show em dashes/unavailable dates instead of invented times. This is not a claim that every startup or functional-video frame is complete.',
            'Eight exact qualified original controls/91files, with identical observed HTML, source, case input, config and original executable/mode receipts, retain the30s normal/reduced/full motion and warm mostly-in-frame ashen opaque Moon/no-stars-through-disc predicates.',
            'Full Chromium preservation is not transferred to fresh headless-shell motion. Headed Firefox preservation stays in its original mode. Currentness/root/offline/iframe and frozenV1 checks retain the unaffected boundaries.',
            'Fresh Firefox blank/partial frames remain failed continuity evidence. No fresh functional video supplies whole-clip readability or motion; exact original qualified continuous preservation supplies that separate predicate.'
        ], ['bindings.json', 'native-pixel-review.md', 'native-pixel-index.json', '../preservation-reuse.json']),
        ('R0006-A06', 'PRE_DELIVERY_QUALIFIED', [
            'Every original6.01-6.16 row and all residualA01-A07 obligations are reconciled explicitly, with accepted source controls preserved rather than reimplemented.',
            'All31 acquired/failed/retained inputs regenerate byte-identical observed HTML;20 selected inputs equal the canonical packet or separately bound headed-promotion polling variant.',
            'Native trace, first-frame/body boundary, observation/export changes, original failures, output schemas, docs and preservation limits are independently reviewed.',
            'The reviewed654-file pre-delivery projection is losslessly equivalent to original payloads; this report and portable derived-note overlay require the final manifest/commit/public readback before claiming an exact published revision.',
            'Certificate remains PRE_DELIVERY with closeR0006Issued=false, issueVerifiedClosed=false, deliveryProof=null and merge reserved. No unresolved product-specific counterexample is established by the retained acquisition failures; their native pixel failures and unassigned cause remain explicit.'
        ], ['bindings.json', 'public-projection-review.json', 'portable-path-review.json', 'final-review.md']),
        ('R0006-A07', 'RESERVED_NOT_QUALIFIED', [
            'Owner approval of exact reviewed head/base/effects is still required for merge; this reviewer grants no external-effect authority.',
            'After authorized merge, verify delivered README/evidence, public runtime bytes and actual public consumer, record r0006-delivered-proof/v1, publish/read back the approved evidence comment, then separately authorized manual completed closure and independent issue-state readback.',
            'A draft PR, local hashes, command success, source tests or this pre-delivery finding do not satisfy delivery or closure. Issue6 must remain open until those gates complete.'
        ], ['../closure-certificate.json']),
    ]
    limits = [
        'PRE_DELIVERY qualification only; no merge, public runtime delivery, CLOSE-R0006, issue closure or universal-host qualification.',
        'Original native frame ordinals/PTS are video coordinates. DOM-render ordinals and video frames are not uniquely associated; late diagnostic screenshot receipts do not replace earliest original native pixels.',
        'Fresh functional clips have no continuous-readability or motion credit. Headless Firefox blank/partial original frames and early font-incomplete loading remain failures with no established renderer/capturer cause.',
        'Exact accepted30s preservation watches are reused after byte/input/environment joins. Independent5/15/30s samples were inspected; this reviewer does not claim a new full continuous watch or fresh browser execution.',
        'Selected offscreen evidence covers actual card intersection with document visible, not successful document-hidden resume.',
        'Fresh Chromium uses headless-shell; retained motion used explicit full chrome.exe. Firefox promotion alone selects the separately bound headed/video-only100ms observation variant.',
        'Concurrent cache-current/prefetch backoff ownership is not uniquely observable for each native timer; candidate receipts are retained and exact original owner controls supply that association. No false unique attribution is made.',
        'Sealed snapshot export retains all snapshots at the cut; the later export-tail video is not further traced qualification. Lossless compression changes transport only.',
        'Nominal asynchronous deadlines cannot preempt synchronous parsing or a blocked/suspended event loop. Date.now fallback is not monotonic; performance-clock claims stay scoped to qualified hosts.',
        'No whole-scene startup, new weather/Moon/scientific policy, offline application, background recovery, external provider-health or physical download-cancellation guarantee follows.',
        'Authority accepted-assessment preserves already-public historical local path literals byte-for-byte. Only23 newly derived review-note JSON files had57 local-only locators normalized; acquisition payloads were untouched.'
    ]
    contrary = [
        {'acquisition': 'browser/firefox/R0006-cold-body', 'finding': 'First recovered1523/60.92s has lower white region hiding lower rows/footer; FAIL retained.'},
        {'acquisition': 'browser/chromium/R0006-accelerated-recovery', 'finding': 'Native actions reached recovery but object export did not finish; interrupted incomplete result retained.'},
        {'acquisition': 'batch2/chromium/R0006-accelerated-recovery', 'finding': 'JSON export exceeded Node string length; explicit ERR_STRING_TOO_LONG and native files retained.'},
        {'acquisition': 'batch5/firefox', 'finding': 'Headed cold observation timeout, hidden RAF-observer timeout and interrupted frozen attempt retained without selected native qualification.'},
        {'acquisition': 'batch6/firefox/R0006-hidden-resume', 'finding': 'Parent display:none did not yield the asserted paused boundary; failed fixture remains, replaced only by explicit actual-card offscreen stimulus.'},
        {'acquisition': 'batch6/firefox/R0006-cache-denied', 'finding': 'First cached16/0.64s lower-partial;17 loses font labels. Later complete refresh44 cannot replace failed first current.'},
        {'acquisition': 'batch6/firefox/R0006-tomorrow-promotion', 'finding': 'First initial18/0.72s lower-partial and first promoted1664/66.56s upper-partial; both retained failures.'},
        {'acquisition': 'batch10/firefox/R0006-tomorrow-promotion', 'finding': 'Initial18/0.72s complete but first promoted1632/65.28s hides header/arc/next; FAIL retained despite later healthy images.'},
        {'acquisition': 'batch6/firefox/R0006-cold-body', 'finding': 'Selected bounded first recovered1519 is complete, while initial loading16 lacks labels and recovered-state1522 is blank. Continuous-clip FAIL remains.'},
        {'acquisition': 'batch7', 'finding': 'Unsupported action failed input preflight before browser launch; not counted as successful native execution.'},
        {'acquisition': 'browser/chromium/R0006-hidden-resume', 'finding': 'Original complete first recovered1633/65.32s retained but superseded by selected actual-card offscreen control.'},
    ]

    paragraph = [
        '# R0006 independent pre-delivery qualification',
        '',
        '**A01-A06 are qualified for this exact pre-delivery candidate, within the explicit scopes below. A07 remains reserved and unqualified. R0006 is not closed, and this finding is not merge authorization.**',
        '',
        'This reviewer read the immutable original issue, audit parent and remaining-work specification independently; inspected current source/fixture/driver/checker/README, all selected native traces and original first-presentation pixels; and reconciled contrary evidence. No browser was launched and no source, Git, GitHub or original acquisition file was mutated. Writes were limited to independent review reports and offline derived media.',
        '',
        '## Exact candidate and authority',
        '',
        f"Base and current pre-commit HEAD: `{bindings['sourceBase']}`, branch `codex/r0006-close`. The candidate is the following working-file digest set, not an invented future commit:",
        '',
        '| File | SHA256 |', '|---|---|',
    ]
    paragraph.extend(f'| `{path}` | `{value}` |' for path, value in bindings['candidateFiles'].items())
    paragraph += [
        '',
        f"Authority: specification commit `21e7a84365fae37a86cae5c7d5e41008c0adc53f`, SHA256 `{bindings['authority']['specSha256']}`; original issue body `{bindings['authority']['issueBodySha256']}`; audit comment6073060055 `{bindings['authority']['auditBodySha256']}`. Comment6074567030 publishes the remaining specification and supplies no waiver. All exact copies reconcile with the canonical receipts.",
        '',
        f"All135 runtime files match the base and currentness receipt (aggregate `{bindings['runtime']['aggregateSha256']}`). Root index `{bindings['packetSourcePins']['index.html']['sha256']}`, authored native index `{bindings['packetSourcePins']['src/native/index.html']['sha256']}` and generated offline `{bindings['packetSourcePins']['offline.html']['sha256']}` are unchanged. Nine unique original owner spans from audit source18ff14860ff41c084b1db5f396bb62aa9c22b1be match current authored and both generated consumers exactly after newline normalization; all five original affected tests match as well. Accepted6.01-6.12/6.14 are retained as current, not attributed to this evidence/docs change.",
        '',
        f"Retained current source TAP `{bindings['retainedCurrentSourceTap']['sha256']}` contains72passing tests,0failures,0skips and0TODO. The original deadline/cold-branch/cooldown mutation controls remain in those exact tests. The retained V1 output reports `PASS: frozen V1 payload and anchored manifest`. This reviewer did not replay qualified source/native controls.",
        '',
        '## Every original row',
        '',
        '| Row | Disposition | Obligation and evidence |', '|---|---|---|',
    ]
    paragraph.extend(f'| {key} | {status} | {claim} {evidence} |' for key, status, claim, evidence in rows)
    paragraph += ['', '## Every residual condition', '']
    for key, status, conditions, evidence in residuals:
        paragraph += [f'### {key}: {status}', '']
        paragraph.extend(f'- {condition}' for condition in conditions)
        paragraph += ['', 'Evidence: ' + ', '.join(f'`{name}`' for name in evidence) + '.', '']
    paragraph += [
        '## Native timing, fixture and first-image boundary',
        '',
        'The independent bounded-memory reader consumed all20 selected raw traces, including both large accelerated traces. It checked every completed-render ordinal, exact clock mode, six admitted finite clocks/date, request kind/day/generation/operation/attempt, owned10000ms timers and cleanup, native backoffs, real recovery fences, cache/adoption and generation behavior. `selected-trace-review.json` records per-case hashes and observations, not just an aggregate verdict. Source tests cover accepted paths not separately replayed natively, including delayed callback and wall-step controls.',
        '',
        '| Cold engine | First operation start, native ms | Third deadline fire, native ms | Eligible fence, native ms | Fourth current call, native ms | Earliest recovered native image |',
        '|---|---:|---:|---:|---:|---|',
        '| Chromium | 527.3 | 33243 | 60527.3 | 60541 | frame1506, PTS60.24s |',
        '| Firefox | 376 | 33092 | 60376 | 60376 | frame1519, PTS60.76s |',
        '',
        'These native trace times and video PTS use distinct origins. They are not subtracted or asserted to be an exact render-to-frame association. Original diagnostic captures sometimes report a later render than the receipt label; the review uses the earliest visible current pixels from original videos instead. The cold first images, their predecessors, body-pending loading and exhausted-unavailable states are all retained with PNG and whole decoded-frame hashes.',
        '',
        'The unchanged provider observer produces byte-identical observed HTML for all31 acquisition inputs. All20 selected case inputs equal the canonical10-case packet or the separate Firefox promotion packet. The adapter changes are limited to streamed JSON encoding, optional sealed snapshot export in ordered16-item chunks, native100ms observation polling where specified, and the actual-card offscreen stimulus with exact inline-style restoration. No product clock, timer, scheduler, renderer, admission function or provider recipe was invoked as a shortcut. The original120x input was not reduced and no snapshot was thinned. The sealed export contains3021 Chromium and5057 Firefox original completed renders; export-tail video is outside that sealed trace claim.',
        '',
        'The selected original native images are indexed in `native-pixel-index.json` (20selected plus retained failed/superseded acquisitions). It joins case/engine, original acquisition, public destination, video SHA, first current/promotion ordinal and PTS, original lossless PNG receipt/hash and whole-frame RGB hash. The expanded descriptions and preservation samples are in `native-pixel-review.md`. Metrics/contact sheets nominate frames only; original full frames decide the findings.',
        '',
        '## Preservation and contrary evidence',
        '',
        'Eight retained qualified original controls have91 exact original files, regenerated identical observed HTML and matched input/config/environment receipts. Full Chromium preservation used explicit chrome.exe148.0.7778.96, SHA256290fa7018fda22c52ada5eddb0113baf3ebc41fd0fde6085eddb19793606c635; unchanged browser_runtime passes that same explicit executable to launch. Its default identity is distinguishable. Fresh Chromium functional captures instead use headless-shell SHA2562d8f2abad1a0f2998aaf861967c374d4aad6a104916b8794318760ed35db772f and acquire no copied motion claim. Retained Firefox preservation is headed, with executable SHA256960a9a013187e337fc03b685ec8bed803791033620985e99fa66438b4fcd6c80. The private pinned cached Playwright1.60 tool environment is recorded; this is not a product dependency change.',
        '',
        'Independent original samples at5/15/30s show supported cloud movement, reduced-preference holding and full-motion override in the retained environments. Warm below-horizon/new-calendar samples show a mostly-in-frame ashen opaque disc with no visible star through it. The original accepted continuous watch and its certificate retain the30s continuity predicate after those exact joins; this reviewer does not claim a fresh full-frame-by-frame watch. No new atmospheric/scientific or whole-scene startup acceptance follows.',
        '',
        '**No fresh functional video receives continuous-readability or motion credit.** Headless Firefox blank/partial original frames remain failed continuity evidence; complete later frames do not erase them. The bounded A02 loading/unavailable/first-recovered images are distinct from the A05 original30s continuous preservation control. The cause of the recorded gaps is not assigned to the renderer, recorder or FFmpeg.',
        '',
    ]
    paragraph.extend(f"- `{entry['acquisition']}`: {entry['finding']}" for entry in contrary)
    paragraph += [
        '',
        '## Packaging and lifecycle',
        '',
        f"The independently verified pre-delivery manifest `{projection['manifestSha256']}` names{projection['fileCount']}files/{projection['totalNamedBytes']}bytes,31retained/selected acquisitions and20selected pixel/video joins. Every listed file hash/size and every native member roundtrip matches its original acquisition. The two raw accelerated traces532790911/635596468bytes restore exactly from507872/339428byte XZ members. JSON/gzip/XZ decoding is transport only. The canonical authority copies and already-public assessment remain exact. No raw snapshot or failed native acquisition was dropped.",
        '',
        'This manifest snapshot precedes adding this review, the final pixel-index status and portable derived-note overlay. `portable-path-review.json` records before/after hashes for23derivedJSON notes/57local-only locators; no acquisition trace, original video or sampled pixel bytes changed. Original already-public local locators inside the accepted assessment are preserved as historical literals. Final projection must include these reports and regenerate its manifest, then receive independent exact-head/public readback. This review deliberately avoids a self-referential future-commit/hash claim.',
        '',
        'Required local output schemas are present: `cases.json` is `r0006-native-proof/v1`; `qualification/docs-review.json` is `r0006-docs/v1`; `qualification/closure-certificate.json` is `r0006-closure-certificate/v1`. The inspected certificate is PRE_DELIVERY, has no issued CLOSE-R0006, no verified closed issue, no delivery proof and reserves merge authority. Its A06 pending field may be advanced to this bounded pre-delivery finding after integration; report inclusion/status/manifest changes require the final readback. `r0006-delivered-proof/v1` remains absent because delivery has not occurred.',
        '',
        '## Limits and remaining action',
        '',
    ]
    paragraph.extend(f'- {limit}' for limit in limits)
    paragraph += [
        '',
        'The next reviewer action is exact final committed-head and public Draft PR artifact readback after the integrator adds this finding, updates only derived certificate/manifest data and supplies the commit identity. Actual merge, public runtime/consumer delivery, approved evidence comment and manual completed closure remain A07 actions under separate owner authority. No native replay is needed for those metadata-only integration steps if the reviewed bindings remain equal.',
        '',
    ]
    markdown = readable('\n'.join(paragraph))
    (HERE / 'final-review.md').write_text(markdown, encoding='utf-8')
    proof_files = ['bindings.json', 'selected-trace-review.json', 'native-pixel-index.json', 'native-pixel-review.md',
                   'public-projection-review.json', 'portable-path-review.json']
    result = {
        'schema': 'r0006-independent-final-review/v1',
        'reviewedAtUtc': datetime.now(timezone.utc).isoformat(),
        'workOrder': 'R0006', 'phase': 'PRE_DELIVERY',
        'status': 'A01_A06_QUALIFIED_A07_RESERVED',
        'reviewerEffects': 'Read-only source/original evidence; writes limited to independent-review reports and offline derived media; no browser/GUI/GitHub/source/Git effects.',
        'sourceBase': bindings['sourceBase'], 'observedHead': bindings['head'],
        'exactFinalCommit': None, 'finalHeadPublicReadback': 'PENDING_AFTER_REVIEW_INTEGRATION',
        'authority': bindings['authority'], 'candidateFiles': bindings['candidateFiles'],
        'runtime': bindings['runtime'], 'runtimePins': bindings['packetSourcePins'],
        'originalOwnerSpans': bindings['originalOwnerSpans'],
        'sourceTests': bindings['sourceTests'], 'retainedCurrentSourceTap': bindings['retainedCurrentSourceTap'],
        'selectionSha256': bindings['selectionSha256'], 'selectedAcquisitions': 20,
        'allRetainedAcquisitions': len(bindings['completedNativeBindings']),
        'preservationControls': len(bindings['preservation']), 'preservationFiles': bindings['preservationFileCount'],
        'originalRows': [{'id': key, 'status': status, 'obligation': claim, 'evidence': evidence} for key, status, claim, evidence in rows],
        'acceptance': [{'id': key, 'status': status, 'conditions': conditions, 'evidence': evidence} for key, status, conditions, evidence in residuals],
        'contraryEvidence': contrary, 'limits': limits,
        'preDeliveryReviewedManifest': {key: projection[key] for key in ('manifestSha256', 'fileCount', 'totalNamedBytes', 'acquisitions', 'selectedAcquisitions', 'selectedPixelVideoJoins')},
        'reviewOverlay': 'Final review files, pixel-index status and portable derived-note locators follow the inspected manifest snapshot. Reproject and regenerate manifest; independent exact-head/public readback remains required.',
        'proofFiles': [{'path': name, 'sha256': sha(HERE / name)} for name in proof_files],
        'reportSha256': sha(HERE / 'final-review.md'),
        'closeR0006Issued': False, 'issueVerifiedClosed': False,
        'mergeAuthorizationGranted': False, 'deliveryProof': None,
        'remainingGate': 'R0006-A07 plus exact final-head/public artifact binding after metadata-only review integration',
    }
    result = readable(result)
    (HERE / 'final-review.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': result['status'], 'markdownSha256': result['reportSha256'],
                      'jsonSha256': sha(HERE / 'final-review.json'), 'originalRows': len(rows), 'residuals': len(residuals)}))


if __name__ == '__main__':
    main()
