"""Write reviewer-owned closure proposals from read-only source/evidence inspection.
This script does not execute product tests, launch browsers, or mutate the repo.
"""
from pathlib import Path
import datetime, gzip, hashlib, json, re, subprocess

ROOT = Path(r'C:\Users\theis\.codex\worktrees\hotfix-startup-clouds\salah_widget')
AUDIT = Path(r'C:\Users\theis\Documents\Codex\pr42-rlgwo-closure-20261008')
OUT = AUDIT / 'workers' / 'F'
SHA = '18ff14860ff41c084b1db5f396bb62aa9c22b1be'
TREE = '35208181eea714c17f5e77b2644e76434345db60'
RUNTIME = 'f443cf0820e6879dfa7c3ce857d6b2baf554b1fdd2f889433d22e2c532cec260'
INDEX = 'ff728552442f4bcce7f213a089bf01d4cf70ea8d74040bdd3323768ca453beee'
FINAL = 'docs/real-sky/evidence/startup-cloud-20261007/final-v49/'

def digest(b): return hashlib.sha256(b).hexdigest()
def read(p): return (ROOT / p).read_text(encoding='utf-8')
def link(p, a=None, z=None):
    suffix = '' if a is None else f'#L{a}' + (f'-L{z}' if z is not None else '')
    return f'https://github.com/theislampill/salah_widget/blob/{SHA}/{p}{suffix}'
def ref(p, a=None, z=None):
    if a is not None:
        line_count=len(read(p).splitlines())
        if a<1 or a>line_count:raise AssertionError(('source range start',p,a,line_count))
        z=min(z or a,line_count)
    return {'path': p, 'lines': None if a is None else [a, z or a], 'url': link(p, a, z)}
def function_ref(p, needle, count=12):
    lines = read(p).splitlines()
    found = [i for i, s in enumerate(lines) if needle in s]
    if not found: raise AssertionError((p, needle))
    a = found[0] + 1
    return ref(p, a, min(a + count - 1, len(lines)))
def native_consumer(needle, count=12): return function_ref('index.html', needle, count)
def evidence(p, scope): return {'source': ref(p), 'freshness': 'historical reuse inspected in this audit', 'scope': scope}
def row(n, obligation, owner, consumer, discriminator, expected, observed, status, evidence_refs=()):
    return {'id': n, 'obligation': obligation, 'authoredOwners': owner if isinstance(owner, list) else [owner],
            'deliveredConsumers': consumer if isinstance(consumer, list) else [consumer], 'discriminator': discriminator,
            'expected': expected, 'observed': observed, 'status': status, 'evidence': list(evidence_refs)}
def log(p):
    data = gzip.decompress((ROOT / p).read_bytes()).decode('utf-8') if p.endswith('.gz') else read(p)
    return data

S = 'satisfied'
U = 'unverified'
M = 'unmet'
V = 'validly superseded'
ASSESSMENTS = {}

def add(number, completed, matrix, gaps, next_increment, checks, deps, controls, improvements=(), decisions=()):
    packet = json.loads((AUDIT / 'issues' / f'{number}.json').read_text(encoding='utf-8'))
    contract = packet['contract']
    assert digest(packet['issue']['body'].encode()) == contract['bodySha256']
    ASSESSMENTS[number] = {
        'schema': 'rlgwo-closure-assessment-v1', 'reviewer': 'F', 'issueNumber': number,
        'canonicalId': contract['canonicalId'], 'title': packet['issue']['title'],
        'originalBodySha256': contract['bodySha256'], 'originalUpdatedAt': contract['updatedAt'],
        'packetCapturedAtUtc': packet['capturedAtUtc'], 'commentRevisions': contract['commentRevisions'],
        'fullPacketRead': True, 'discussionAmendments': 'No comments; renamed/referenced events read without treating them as authority.',
        'target': {'commit': SHA, 'tree': TREE, 'runtimeTreeSha256': RUNTIME, 'indexSha256': INDEX, 'auditDate': '2026-10-08'},
        'targetCustody': 'Clean reviewed head 4bccdf43363926c3077f60de87e5617ccb9abcb9 has identical merge tree; source read there.',
        'model': {'requested': 'gpt-6.1-sol', 'requestedEffort': 'max', 'effectiveConfigurationConfirmed': False},
        'scopeOfDone': completed, 'requirementMatrix': matrix, 'negativeControls': controls,
        'gaps': gaps, 'dependencies': deps, 'improvements': list(improvements), 'ownerDecisions': list(decisions),
        'verdict': 'LEAVE OPEN', 'proposedNextRlgwoIncrement': next_increment, 'missingChecksRequested': checks,
        'freshExecution': {'productTests': [], 'browsers': [], 'reason': 'Primary resource-release message was not received; read-only source/evidence inspection only.'},
        'reuseBasis': 'Final-v49 receipts retain the exact ff7285 index and f443cf runtime. Earlier Moon/CP9 receipts retain their earlier identities and qualify only mapped unchanged mechanisms; no old aggregate PASS is promoted to current closure.',
        'inheritedQualification': {'N001': 'PARTIAL', 'N002': 'PARTIAL', 'N003': 'BLOCKED', 'scope': 'Only mapped mandatory obligations are affected; these are not blanket blockers.'},
        'publication': {'reconciledByPrimary': False, 'approved': False, 'posted': False,
                        'hold': 'Primary must establish delivered baseline and reconcile each comment before any GitHub effect.'},
        'risks': 'Evidence gaps are not all product defects. Source mechanics, raw numerical equality, displayed pixels, native default actions and real OS lifecycle are distinct claims.'
    }

smoke = ref('tests/smoke.html', 39, 80)
cfg = ref('src/native/config.js', 178, 218)
cfg_consumer = ref('config.js', 178, 218)
wrapper = ref('tests/widget-fixture.html', 104, 182)
smoke_log = FINAL + 'logs/native/r0017-contract.log.gz'
transport_log = FINAL + 'logs/native/r0017-transport.log.gz'
old_smoke = 'docs/moon/evidence/post-horizon/native-smoke/results.json.gz'
add(23,
    'Required-case accounting, non-pass missing execution, private config storage dependency, exact scene/run/document/source readiness, deterministic pre-script transport, bounded async callbacks, and explicit reduced/full branches are implemented. They predate PR42 except the joined current-model policy adaptations.',
    [
      row('17-01', 'Re-anchor/reconcile intended repo, target and existing interfaces; no framework/dependency adoption.', ref('docs/real-sky/INTEGRATION.md', 64, 87), native_consumer('function render(){'), 'Read-only Git tree/hash and authored/generated owner trace.', 'Reviewed and delivered identities agree; unrelated work preserved.', 'Clean reviewed tree equals audit merge tree; index digest equals ff7285; no production mutation.', S),
      row('17-02', 'Every named required callback must finish; FAIL errors, INCOMPLETE missing, PASS only full execution; preserve pass/fail/skip and finalize exceptions.', smoke, ref('tests/smoke.html', 422, 429), 'Null iframe, missing config, suppressed callback, timeout-as-executed and missing-denominator mutants.', 'Missing/failed execution cannot be green; bounded late callbacks cannot alter another case.', 'Final retained r0017-contract has 35 PASS cases; actual assertions were read and distinguish recorder/readiness from widget health.', S, [evidence(smoke_log, 'Recorder/storage/readiness VM; no real widget/browser qualification')]),
      row('17-03', 'Keep all original config/weather/moon/dawn/cloud/orientation/motion/observability checks required; optional live diagnostic cannot replace them.', ref('tests/smoke.html', 40, 54), ref('tests/smoke.html', 274, 420), 'Complete actual healthy browser case ledger bound to current source.', 'Every existing required scene executes against actual current widget.', 'Current denominator has 30 named cases. Historical post-horizon healthy run had 30/30,141/0/0 on runtime13fb06; it is not final-v49 evidence.', U, [evidence(old_smoke, 'Earlier actual browser healthy path only')]),
      row('17-04', 'Optional Storage-like input reaches storageAvailable/load/save/clear plus BOTH local/preferLocal resolve consumers; omitted args and KEY/version remain compatible.', [cfg, ref('src/native/config.js', 298, 317)], [cfg_consumer, ref('config.js', 298, 317)], 'Explicit private store/default APIs/throwing getter and dropped savedP/savedL argument mutants.', 'No real-origin calls; same precedence and safe denied-storage shapes.', 'Source resolves default getter inside try; both resolve edges pass storage. Retained35-case contract covers default APIs, denied getter and both mutants.', S, [evidence(smoke_log, 'Contained VM normal-entry/storage seam')]),
      row('17-05', 'Original valid/malformed/absent config and unrelated sentinel bytes survive pass/fail/throw/timeout, including __sw_probe__; no global Storage prototype monkeypatch.', ref('tests/smoke.html', 82, 85), cfg_consumer, 'Sentinel store call ledger across four recorder outcomes and unavailable main path.', 'Exact bytes/absence survive; zero calls to real storage.', 'Retained contract directly asserts these raw values and zero calls. Full-browser sentinel matrix for final source was not found.', U, [evidence(smoke_log, 'VM recorder storage isolation covers all specified raw values/outcomes')]),
      row('17-06', 'Static wrapper fetches exact source/digest, isolates hooks BEFORE config/widget parsing, validates static anchors/font policy and unchanged bodies, no fabricated renderer/prayerLoaded.', wrapper, wrapper, 'Source-anchor/Moon/extra-script failures; actual browser DOMParser/document.write path.', 'Bad source or failed isolation terminates setup; actual response consumer boots unchanged scripts.', 'Transport17-case final receipt exercises pre-parser hooks with parser deliberately stopped. Old browser30/30 proves an earlier reached wrapper; final actual document path unverified.', U, [evidence(transport_log, 'Actual wrapper pre-parser transport/hooks only')]),
      row('17-07', 'Fixed2026-09-07T09:30Z clock, exact Asia/Riyadh hash/attempt, private fresh cache, expected date/coords/method/school and actual request/JSON/render/countdown.', wrapper, ref('tests/smoke.html', 89, 119), 'Healthy actual prayer response: current Dhuhr, next Asr15:30,180min; stale attempt/hash/source/cache/no-JSON controls.', 'Current transport consumption plus actual render required, stale frame rejected.', 'Readiness guards and request validation are implemented and tested by bounded VM. Earlier browser healthy success is not rebound to current policy/runtime.', U, [evidence(smoke_log, 'Named stale-input readiness controls'), evidence(transport_log, 'Real Response/json fixture; parser stopped')]),
      row('17-08', 'Separate healthy/reject/hang/bootstrap-error browser invocations, bounded non-pass, no generic offline label; actual unchanged index control.', wrapper, ref('tests/smoke.html', 117, 119), 'Fresh private iframe per mode; source/digest and console/ledger readback.', 'Three negatives non-pass even with config successes; actual index loads.', 'Modes and bounded summaries exist. No final-tree retained browser run of all three negatives was located; normal-root-v1 final runtime entry receipt is narrower positive evidence.', U, [evidence(FINAL+'runs/joined-v49-final-chromium-normal-root-v1/results.json', 'Actual normal entry/settings/current model; not smoke negatives')]),
      row('17-09', 'Explicit reduce=true/false and separate motion=full; restore EXACT matchMedia on success/throw/timeout; ignore-reduction/override mutants fail.', ref('tests/smoke.html', 395, 409), native_consumer('const moonObject=', 12), 'Actual browser under both OS signals plus two semantic mutants.', 'Default honors OS; explicit full override wins; no restored-OS assumption.', 'Explicit branches/finally implemented; prior browser healthy checks passed. Final two OS envelopes and product-mutant results unverified.', U),
      row('17-10', 'README safe-origin/outcome instructions and source/public wrapper delivery; no appearance/M0 certification from frozen font-suppressed fixture.', ref('README.md', 1, 16), [ref('tests/smoke.html', 9, 16), ref('tests/smoke.html', 427, 427)], 'README instructions plus source-bound public smoke readback.', 'README explains safe test origin and PASS/FAIL/INCOMPLETE; limitations public.', 'README has no smoke/INCOMPLETE/isolated-fixture instructions. The smoke page itself states its narrower scope.', M),
      row('17-11', 'Independent exact-tree RED/GREEN/mutation review and evidence comment before closure; preserve geometry/moon/dawn/accessibility and interface shared with R0011.', cfg, [cfg_consumer, ref('docs/real-sky/STARTUP_CLOUD_HOTFIX.md', 396, 419)], 'Current required browser matrix and independent pixel owners at interfaces.', 'No false closure or claim of deployed/visual proof from helper-only tests.', 'This is an unreconciled reviewer proposal. Broad native runner has eight separate legacy failures and four TODOs; none automatically blocks this instrument.', U)
    ],
    ['README lacks the required safe-origin/status instructions.', 'Final actual30/30 healthy browser proof and reject/hang/bootstrap-error controls with sentinel bytes, current response consumption and motion mutants are unverified.', '8s orientation readiness versus measured terrain acquisition is a hypothesis to reproduce, not an observed final defect.'],
    {'owner': 'tests/smoke.html + tests/widget-fixture.html; narrow src/native/config.js seam only if a reproduced failure requires it',
     'preserve': 'Keep execution ledger, private storage, current model/observation distinction, exact identity guards, and all required checks.',
     'steps': ['Run current unchanged smoke healthy and three separate negatives on isolated origin; record all30 required cases, fetched digest, attempts, current/tomorrow JSON reads, real sentinel bytes and errors.', 'Exercise true/false OS preference and ignore-reduction/override mutants using the real product branch; repair only a concrete instrument failure.', 'Add README safe-origin/outcome/scope instructions; repeat affected controls and independent exact-tree review.'],
     'acceptance': 'Healthy PASS30/30 with zero missing/failure and actual fetch/render; each negative bounded non-pass; exact sentinel bytes survive all outcomes; semantic mutants detected; public source/readback matches if public repair claimed.',
     'nonGoals': 'No renderer/runtime redesign, provider addition, dependency, storage migration, live-M0 claim, or production data cleanup.'},
    [{'name': 'current browser instrument matrix', 'command': 'Serve the exact tree statically; open tests/smoke.html?fixture=healthy|reject|hang|bootstrap-error as four separate isolated-profile invocations; inspect __smoke and __widgetFixture.', 'reason': 'Mandatory actual consumer and negative execution proof; serial primary browser ownership.'}],
    ['R0011 same save/clear seam: failure results and omitted-argument behavior retained; not whole-issue prerequisite.', 'R0024 weather policy interface consumes owner-authorized current model estimates without converting them to observations.', 'Delivered baseline/publication remain primary-owned.'],
    ['Retained35-case VM instrument/storage suite has meaningful null/missing/timeout/suppression/storage-edge controls; it does not qualify a real widget.', 'Retained17-case transport suite stops DOM parsing by design and cannot supply browser readiness.', 'Current exact-name/readiness guards reject stale run/attempt/document/hash/source and cache-without-JSON envelopes.'])

timetable = ref('src/native/index.html', 411, 425)
add(24,
    'An opt-in contrast appearance provides full row opacity and a bounded dark backing. The default remains glass with .p.past opacity .42; PR42 strengthens NEXT with an opaque dark-text accent while CURRENT retains its own outline.',
    [
      row('18-01', 'Preserve325x530 card, row geometry/fonts/strings and surrounding sky/header/footer; no global redesign.', timetable, native_consumer('/* prayer-times grid */', 15), 'Geometry declaration equality and representative final crops.', 'Local timetable treatment only; exact established geometry/content.', 'Source declaration guards preserve grid/padding/font sizes. Viewed final night and twilight sheets retain visible full card/footer. Full compact/long/stale geometry matrix remains unverified.', U, [evidence(FINAL+'logs/native/r0018-timetable-contrast.log.gz', '14 authored-composition controls; not native pixels')]),
      row('18-02', 'Names/times full informational opacity in EVERY state; remove .p.past group attenuation while retaining state hierarchy.', timetable, native_consumer('.p.past{opacity:.42}', 2), 'Original opacity mutant and default/contrast source comparison.', 'No .42 information attenuation in intended repair.', 'Default source still .p.past{opacity:.42}; only data-appearance=contrast overrides to1. Tests intentionally assert .42 remains under glass.', M),
      row('18-03', 'Every state has local backing/foreground >=4.5:1 under intended-color/background evaluation, including next override and bright animated sky.', timetable, native_consumer('.c[data-appearance="contrast"] .p{', 3), 'White sky/accent stress and past/next independent composition mutants.', 'All timetable states meet invariant; no child opacity workaround.', 'Final14-case guard establishes4.5 only for opt-in contrast and explicitly requires default glass ratio<4.5. This is a direct contract-policy difference pending trusted amendment.', M, [evidence(FINAL+'logs/native/r0018-timetable-contrast.log.gz', 'Authored colors/bounds, not full filter/antialias conformance')]),
      row('18-04', 'Reproduce pinned noon RED and final GREEN at date2026-09-07,12:30Riyadh, actual325x530/DPR with specified synthetic prayer values and settled fonts.', ref('tests/r0018-timetable-contrast.cjs', 1, 36), native_consumer('/* prayer-times grid */', 15), 'Matched12 text rectangles plus text-hidden same-scene background.', 'Visible RED, readable GREEN and correct intended-color composition.', 'Historical issue supplies RED values but date was unpinned. No final exact12-rectangle frozen-noon text/background pair was found.', U),
      row('18-05', 'Representative sunrise/sunset/night/clear/broken/overcast past/current/next scenes and local bright stress; contrast mutants must detect losses.', ref('tests/r0018-timetable-contrast.cjs', 69, 101), native_consumer('/* prayer-times grid */', 15), 'Final actual composites, .42 past mutant and next presentation mutant.', 'Pixel readability and >=4.5 where contract binds; named mutants independently fail.', 'Numerical authored guards distinguish past/next contrast faults. Viewed final twilight default past rows are visibly faint; no measured native whole-composition matrix.', U, [evidence(FINAL+'visual-review/firefox-startup-twilight.png', 'Viewed historical final-runtime default-glass startup sheet')]),
      row('18-06', 'Compare repaired noon to original/fresh RED, preserve art hierarchy and compact/long/stale dates, independent sequential pixel review.', ref('DESIGN.md', 98, 108), native_consumer('/* prayer-times grid */', 15), 'Matched baseline/current crops; surrounding geometry/content controls.', 'Local darker readable cells; no sky dim/full-card overlay.', 'Final images show NEXT/current differentiation but are not original-to-final matched noon repair proof.', U),
      row('18-07', 'DESIGN readability acceptance/document truthful public claim; builder/config/install/preset and embed bounds compatible.', ref('DESIGN.md', 103, 108), ref('README.md', 233, 248), 'Inspect docs and interface policy readback.', 'Scope of default/optional accessibility and known owner amendment explicit.', 'Docs say other rows stay readable glass; no supplied issue comment amends original full-opacity/all-state guarantee. Owner production iframe330x534 around325x530 is explicit separate amendment.', U),
      row('18-08', 'Exact-tree evidence comment, independent visual review and served source/rendered readback before claimed public closure.', ref('docs/real-sky/STARTUP_CLOUD_HOTFIX.md', 377, 393), ref(FINAL+'QUALIFICATION.json'), 'Current bounded pixel/composition proofs plus owner reconciliation.', 'No metric override of visibly weak text or invented accessibility certification.', 'Unreconciled proposal; source model confirms the default-contract mismatch, not general WCAG nonconformance in every scene.', U)
    ],
    ['The original full-opacity/all-state contrast contract is not met by default glass; whether an explicit trusted owner amendment validly supersedes it is unresolved.', 'Final frozen-noon12-rectangle RED/GREEN/text-free pair and native bright stress/mutant/scene/geometry proof are missing.'],
    {'owner': 'src/native/index.html timetable CSS/backing and DESIGN.md; existing appearance mode owners retained',
     'steps': ['Resolve the actual owner amendment before selecting any production change; a test comment saying owner-authorized is not authority.', 'If original contract remains binding, repair only local cell opacity/backing/foreground in all states. If superseded, document exact amended default versus optional guarantee and its preserved invariant.', 'Produce pinned12-rectangle matched noon/text-hidden proof, representative scenes, independent past/next mutants, bright stress and compact/long/stale geometry; review pixels sequentially.'],
     'acceptance': 'Every still-binding timetable contrast and geometry obligation has rendered and composition proof; any superseded obligation has exact trusted owner authorization and a demonstrated replacement.',
     'nonGoals': 'No global sky dimming, layout redesign, token framework, screenshot score substituted for visual review, or general accessibility certification.'},
    [{'name':'contrast closure matrix','command':'Use the issue-specified frozen noon fixture and text-only visibility knockout; record12 rectangles, DPR/fonts/row classes, intended colors and original/current/mutant crops.','reason':'Actual composition and pixel proof required, not authored-only calculator.'}],
    ['Appearance policy must be reconciled with trusted owner decisions.', 'R000A/H6 row classification and opaque NEXT emphasis remain independently accepted behavior.', '330x534 production iframe amendment does not change325x530 card or automatically amend text contrast.'],
    ['Authored white-stress composition distinguishes glass from contrast.', 'Final guard includes past-opacity and next-foreground/backing faults, but native compositor mutant crops were not located.'],
    ['NEXT opaque accent restores measured contrast in the final H6 warm-horizon control without relabelling other future rows.'],
    ['Provide the exact trusted authorization, if it exists, for keeping default faded glass and moving the original4.5 guarantee to opt-in contrast. No new owner decision is inferred from code comments.'])

radio = ref('src/native/builder.html', 226, 252)
add(26,
    'The existing two-button Embed type group now has one checked/active/tabbable selection, scoped arrow wrapping, disabled-control handling, and native Tab/Enter/Space preserved in the application handler.',
    [
      row('1A-01','Preserve two mutually exclusive Embed buttons, values/callers; no accessibility redesign or preference redefinition.',ref('src/native/builder.html',174,177),ref('builder.html',174,177),'Source/generated equality and selected/output state.', 'Portable/local semantics unchanged.', 'Markup retains role=radiogroup/radio and values; generated builder matches authored owner under final preservation evidence.',S),
      row('1A-02','setMode single owner updates active/aria-checked/tabIndex for initial, click and programmatic changes.',radio,ref('builder.html',226,252),'8-case retained VM selected-state/output assertions.', 'Exactly one enabled selected/checked/tabbable radio; none enabled is safe.', 'Current source and retained8/8 prove state synchronization and disabled fixtures; terminal explicitly native=NOT_RUN.',S,[evidence(FINAL+'logs/native/r001a-radio.log.gz','VM behavior/output, no native default-action proof')]),
      row('1A-03','Scoped Right/Down next and Left/Up previous, wrap, focus+setMode once; exclude disabled and other event targets.',radio,ref('builder.html',243,252),'Real native arrows, scroll prevention and preview revision count.', 'Selection/focus/output agree, handled arrows prevent default, one update.', 'VM checks all four arrows and revision+1. Required actual native event delivery not located.',U),
      row('1A-04','Native Enter/Space click preserved; do not handle keydown twice; native Tab/ShiftTab enter selection then leave without trap.',radio,ref('builder.html',243,252),'Real browser Tab sequence and Enter/Space click/preview counters.', 'One native activation; one group tab stop and escape.', 'Handler returns for these keys; VM says native default activation is not emulated. No native final-tree receipt.',U),
      row('1A-05','Pointer and programmatic modes update selected/focused/generated output, local=1/allow=geolocation and existing embed size.',radio,ref('builder.html',211,239),'Actual output/readback after arrow/click/setMode.', 'Mode/output agree; correct local-only delegation and325x530 builder payload.', 'Retained8-case VM verifies exact hash, allow and dimensions. Served/native browser parity remains unverified.',U),
      row('1A-06','One/zero enabled safety and unrelated group target ignored; omit arrow or tabIndex mutant fails the right behavior.',ref('tests/r001a-radio.cjs',8,77),ref('tests/r001a-mutations.cjs',1,12),'Real consumer mutation with no bootstrap substitute.', 'Each semantic fault detected.', 'Mutation script rejects nonzero plus exact Right-arrow failure without TypeError/setup failures, but no final execution receipt was found.',U),
      row('1A-07','Mobile375x800 and ordinary desktop focused selected/unselected crops: focus visible and no clipped text.',ref('src/native/builder.html',35,36),ref('builder.html',53,55),'Native keyboard and actual crop at both widths.', 'Visible focus, unclipped controls.', 'Focus CSS exists. Native mobile/desktop focused crops unverified; no speech/AT claim added.',U),
      row('1A-08','Final native RED/GREEN, exact-tree review of Tab/double activation, evidence comment and served builder readback before public repair claim.',radio,ref('builder.html',226,252),'Current native sequence plus matched served source.', 'Complete all bounded group obligations before manual closure.', 'Only source/VM proof located; primary/public reconciliation pending. No whole R0010 issue dependency imposed.',U)
    ],
    ['Required final-tree native keyboard/default-action and focus-crop evidence is absent from inspected retained packets.', 'Final arrow/tabIndex mutant receipt and actual served builder output readback are unverified.'],
    {'owner':'src/native/builder.html existing radio group and focused tests only',
     'preserve':'Keep setMode, portable/local values, output/hash/delegation and existing preview update behavior.',
     'steps':['Run actual native Right/Left/Up/Down/wrap and Tab/ShiftTab/Enter/Space at375x800 and desktop; count actual click and preview revisions.', 'Inspect selected/output/hash/allow after click and programmatic changes; run omit-arrow/tabIndex controls and capture focus crops.', 'If all pass, add exact source/served digests, event/readback/crop receipts and primary independent reconciliation; repair only observed group failures.'],
     'acceptance':'All original native group controls pass, mutations fail the named behavior, one tab stop and one native activation, visible focus/no clipping at both widths.',
     'nonGoals':'No framework, screen-reader speech claim, settings focus-trap redesign, new preference semantics or installer changes.'},
    [{'name':'native radio evidence','command':'Open exact delivered builder in isolated browser; use native keyboard presses at375x800 and desktop; inspect aria-checked/tabIndex/activeElement/embedMode/iframe hash and revision after each step.','reason':'VM does not emulate native defaults; mandatory platform evidence.'}],
    ['R0010 owns selected local preferences; preserve its output interface, not whole-issue closure.', 'Production iframe330x534 owner policy is separate from the builder group interaction repair.'],
    ['Current disabled one/none and unrelated-target controls are explicit VM fixtures, not new disabled UI features.', 'Mutation script demands behavior failure and rejects bootstrap errors; actual final receipt unverified.'])

moon_geometry = ref('src/native/index.html',1856,1866)
moon_sampler = ref('src/native/index.html',1868,1887)
add(29,
    'renderMoon stamps finite produced geometry from captured absolute minute/date/location/zone. applyTheme records immutable last-consumed atmosphere/paint status; QA separates last consumption from recomputed geometry. Sampler now reads current terrain backing canvas, shared radius and checked coordinates.',
    [
      row('1D-01','Producer owns date/absolute-minute/context stamp after valid geometry; direct callers and same-minute reuse; failed geometry does not advance success marker.',[moon_geometry,ref('src/native/index.html',1890,1934)],native_consumer('function renderMoon(){',45),'Actual boot/config/cache/network/day paths and alternate-date/location controls.', 'No equal-minute false freshness; successful production owns metadata.', 'Retained final11-case lifecycle reaches actual boot/applyConfig/rAF day adoption and strictfresh result; source checks date/context and failed production marker.',S,[evidence(FINAL+'logs/native/r001d-lifecycle.log.gz','Whole inline source lifecycle with contained boundaries; no compositor')]),
      row('1D-02','Capture immutable state at actual atmosphere->paint boundary; later producer cannot rewrite consumed snapshot; stricttrue only and pre-first/missing/fail unavailable.',ref('src/native/index.html',2979,2990),native_consumer('let _lastMoonPaint=null;',12),'Consumer-before-update, missing/throwing atmosphere, failed paint, pre-first query, restore !==false/recompute mutants.', 'Reordered old consume stays stale; failures never true.', 'Source capture is correct and QA uses lastMoonPaint; full diagnostics/mutation tests exist but their final execution is not in native runner receipt.',U,[evidence(FINAL+'logs/native-results.json','Runner includes lifecycle, not r001d-diagnostics/mutations')]),
      row('1D-03','Keep atmosphere pure, cadence/PBR threshold/cache and bounded warnings at consumption; no scheduler or default appearance changes.',ref('src/native/index.html',2980,2990),native_consumer('function applyTheme(M){',12),'Existing .001 reuse/.006 repaint, failure controls and no default readbacks.', 'Diagnostic repair preserves rendering/cache and bounded warning.', 'Native legacy PBR tests describe correct threshold but current terrain path supersedes that producer. Actual current geometry/terrain bridge tests are separate; no final full diagnostic preservation proof.',U),
      row('1D-04','Sampler uses actual width/height/shared renderer radius/center, checks integer bounds before flattened index; absent/context/error data unavailable.',moon_sampler,native_consumer('function moonDebugSamples(){',13),'Synthetic dark-limb/bright-disc,300/negative/y=height,empty/error controls through actual readout.', 'Auditable in/out/OOB samples; no row wrapping or hardcoded darkness.', 'Current sampler reads SalahMoonRuntime.surface(), normally300x300 via moon-native9,73,79,193; raw bounds code rejects OOB. Existing diagnostics fixture only sets _moonCv, so it no longer supplies the selected current surface.',U,[evidence('tests/r001d-diagnostics.cjs','Read actual assertions; current surface fixture adaptation required')]),
      row('1D-05','Meaningful inner/limb/edge and valid exterior295/299; expose dimensions/coordinates, name canvas exterior and no clamp-as-original.',moon_sampler,native_consumer('if(DEBUGMOON){',8),'Actualcurrent surface plus bright/dark synthetic current-surface controls.', '300/R144 gives222,293,294,295,299 samples and distinct alpha/luminance.', 'Source enumerates these coordinates and qualified labels. No retained current native debugMoon readout linked to current terrain was located.',U),
      row('1D-06','Required whole-render freshness smoke and sampler mutations must reach actual consumers; missing diagnostics not a pass.',ref('tests/r001d-mutations.cjs',1,42),ref('tests/smoke.html',363,366),'Strict smoke under reorder/notfalse/recompute and R58/removebounds.', 'Each respective defect detected by reached assertion, no helper-only or setup credit.', 'Read mutation anchors include removed synthetic star-appearance case; diagnostics legacy canvas fixture cannot certify current terrain readout. No final replacement discriminator receipt supplied.',U),
      row('1D-07','Nonthrowing opt-in native sanity and appearance-preservation crops across crescent/half/gibbous/full/new/below; no transparency/blackcutout, no art-improvement claim.',moon_sampler,[ref('moon/src/moon-native.mjs',189,203),ref('moon/src/moon-detail.mjs',31,40)],'Current debug readout at real terrain publication plus matched composition crops/star-positive control.', 'Diagnostics change no default pixels; physical/calendar semantics preserved.', 'Final-v49 normal Moon and matched-layer source-bound imagery exist, but they do not inspect this exact opt-in sampler/error boundary. Viewed calendar-motion sheet contains a dark below-horizon disc with faint limb; no blankettexture/opacity certification.',U,[evidence(FINAL+'visual-review/chromium-moon-cold-motion.png','Viewed retained current terrain/calendar frames20.031..97.953s')]),
      row('1D-08','Affected AGENTS/DESIGN/smoke claims current; independent exact-tree positive/negative review and evidence before closure/public instrument claim.',ref('AGENTS.md',7,28),ref('DESIGN.md',198,204),'Source/debug readback and bounded diagnostic regression packet.', 'Truthful current-owner diagnostic limits and public delivery scope.', 'Owner docs separate geometry/material/currentness. Final mandatory diagnostic/browser matrix is unverified; this reviewer proposal has no primary reconciliation.',U)
    ],
    ['Final whole-render reordered/error/missing/sampler mutation receipts are absent; current runner only executes11-case lifecycle.', 'Existing sampler fixture sets legacy _moonCv while current readout selects SalahMoonRuntime.surface; this is a fixture-interface gap, not demonstrated faulty production coordinates.', 'Current native opt-in debug sanity and appearance-preservation evidence bound to sampler are unverified.'],
    {'owner':'src/native/index.html diagnostic metadata/readout and tests/r001d-*; actual current terrain interface moon/src/moon-native.mjs',
     'preserve':'Keep finite producer stamp, immutable consumed snapshot, stricttrue projection, real-time cadence, current terrain, shared radius and no default getImageData.',
     'steps':['Update only isolated diagnostic fixtures to supply the actual selected current-surface API; disclose doubles and retain original expectations.', 'Run actual render reordering/error/context and R58/OOB/notfalse/recompute mutants with stage and consumer identity proof; remove neither negative nor expectation.', 'Under serial primary preview, inspect opt-in debugMoon on current terrain with coordinates/dimensions/errors and matched default moon crops; repair only a demonstrated instrument fault.'],
     'acceptance':'All original two-subcase positives/negatives/mutations pass at exact source with actual paint/readout reached; missing/failed stays unavailable, reordered consumption stays stale, rawcanvas samples are correct, native default appearance preserved.',
     'nonGoals':'No lunar art/physics redesign, old-canvas substitution, new shader, scheduler, persisted diagnostics or visual improvement claim.'},
    [{'name':'current diagnostic consumer controls','command':'Run tests/r001d-diagnostics.cjs and tests/r001d-mutations.cjs on current source after an explicitly disclosed isolated current-surface fixture adaptation; retain actual consumer stage assertions.','reason':'Existing final runner omits these; legacy fixture is not equivalent current sampler proof.'},
     {'name':'native debugMoon sanity','command':'Use exact current entry with debugMoon=1 after a current terrain surface; record sampled coordinates/radius/backing and normal matched crops.','reason':'Mandatory opt-in native/error/appearance preservation; serial browser owner.'}],
    ['R0022 consumes native light diagnostics; current scientific sky has its own separate accepted astronomical state.', 'Current V5 terrain publication/quality must not be confused with geometry freshness.', 'N003 real OS/BFCache is outside this diagnostic contract unless a mapped native failure needs it.'],
    ['Producer/context and actual failed-atmosphere/paint/readout controls exist in source tests, but a present test file is not executed final evidence.', 'Old-surface debug fixture mismatch must not be counted as detection of a production sampler mutant.'])

reveal = ref('src/native/index.html',2060,2094)
add(33,
    'Accepted-scene pending/initializing coordination, independent lunar background cutout, correct target projection and current terrain publication boundary are implemented. PR42 adds measured first-paint preview republishing and bounded current terrain continuity rather than broad transition removal.',
    [
      row('21-01','Before first visible sky exposure, position/size/visibility/light eligibility share accepted scene; retain intermittent baseline and repeat new documents.',reveal,native_consumer('function beginSkyScene(){',28),'Repeated cold/warm native entry with captured first-visible transforms/images and timing.', 'No small-to-final moon growth or daytime night-layer flash; accepted geometry first.', 'Final-v49 sixteen cold/warm startup pairs cover direct/iframe/weather/location acquisition; actual source-bound sheets show coherent day/twilight. Exact repeated original crescent/0/800ms growth negative sequence is not identified.',U,[evidence(FINAL+'QUALIFICATION.json','16 final cold/warm pairs retain exact runtime and sampling limits')]),
      row('21-02','Initial scene suppressed only until accepted astronomical state; no wait for all fonts/weather/network or whole-widget hidden; unresolved location neutral usable UI.',reveal,native_consumer('function commitSkyScene(A){',10),'Pending fonts/weather/coordinates/failed first paint and healthy recovery.', 'Truthful finite partial state; prayer/settings usable; no prior-target precip.', 'Source pending decorations and commit require strict geometry/scene identity. Final native lifecycle386 assertions and startup acquiring/missing/recovery cases prove scoped native behavior.',S,[evidence(FINAL+'runs/joined-v49-final-firefox-native-lifecycle/results.json','Actual native entries/workers; event/transport doubles, no real OS/BFCache')]),
      row('21-03','Initial stars use accepted local target/time after async resolution; never retain fallback0/0; config reinit clears all layers coherently.',reveal,[ref('real-sky/native-host-hooks.js',11,39),ref('real-sky/native-star-preview.mjs',61,86)],'Wrong/late accepted target and first native catalogue sink/current scene discriminator.', 'Actual displayed catalogue belongs to accepted observer/time, not old fallback.', 'Removed synthetic-array tests are explicit exclusions; actual catalogue/worker target identity tests and final acquiring lifecycle support replacement interfaces. Specific local/no-saved first projection witness unverified.',U),
      row('21-04','Twilight fade natural but stars/glints/MilkyWay cannot pass through visible moon; correct geometry/AA and no blackcutout/day hole.',[reveal,ref('moon/src/moon-detail.mjs',31,40)],native_consumer('function updateSkySurface(){',7),'Interior3px and outside-positive star probes at actual displayed sinks across densely sampled dawn/dusk phases.', 'Interior rejected through fade, outside preserved, continuous natural transition/no mask hole.', 'Current detail equation blocks direct sources independent of opacity; actual same-runtime Moon sheets/terrain material exist. No current hostile interior+outside probe after the actual star sink across .01/.08/.5/1 dawn/dusk was located.',U),
      row('21-05','Settled opaque textured calendar moon every night inclnew/below; daytime hidden; sun nucleus/low-left/flattening/registered optics preserved.',[ref('moon/src/moon-native.mjs',75,90),ref('moon/src/moon-detail.mjs',96,118)],native_consumer('moonTruth:(()=>{',15),'Current actual phase/sun/no-star-through crops, genuine outside-star control.', 'No vanished calendar slot, black limb or solar regression.', 'Final normal cold/warm terrain continuity has zero blanks after first current surface; prior exactmaterial/phase imagery narrowly supports lineage. Calendar-preview/final/physical geometry remain separate; complete demanded opacity/sun matrix not demonstrated here.',U,[evidence(FINAL+'visual-review/chromium-moon-cold-motion.png','Actual20..98s current calendar continuity; not every phase or initial acquisition')]),
      row('21-06','Cloud/rain truth retained; missing/delayed providers recover current scene; supported rain positive and dry negatives.',ref('src/native/index.html',3068,3080),native_consumer('function render(){',13),'Startuprain, unavailable assets/provider and target/currentness rejection.', 'No stale-location rain or invented precip; partial UI recovers.', 'Final startup and lifecycle consume controlled finite current records; owner model-estimate policy is explicit separate amendment. No actual observation claim made.',S,[evidence(FINAL+'runs/joined-v49-final-firefox-startup-rain/results.json','Exact runtime supported current-model rain fixture')]),
      row('21-07','Visible15-60s normal elapsed cloud/star motion; reduced/full fresh docs; later weather/config transition survives.',ref('src/native/index.html',3208,3235),native_consumer('function startRenderLoop(){',20),'Normal1x clip/pixels plus reduced/full native branch.', 'No wallpaper, hash-only proof or global animation ban.', 'Viewed final Moon-motion sheet shows cloud shape/position change over20..98s; normal1x WebM retained. Full/reduced and exact whole-motion matrix require narrow reuse/revalidation, not static stills.',U,[evidence(FINAL+'motion/chromium-normal1x-cold.webm','Retained actual normal1x clip; this audit inspected sheet, not all video frames')]),
      row('21-08','Card/header/buckle/footer/prayer bounds and at least one mobile/constrained native embed; no extra loop/allocation or startup/steady cost regression.',ref('src/native/index.html',2065,2094),[ref(FINAL+'runs/joined-v49-final-chromium-startup-direct/results.json'),ref(FINAL+'runs/joined-v49-final-chromium-startup-warm-moon/results.json')],'Native constrained iframe plus baseline/current callback/cost and first-frame geometry.', 'Card325x530 and owner-amended production iframe330x534 remain usable; no extra render loop.', 'Final startup includes current constrained iframe and source preserves one native loop. First scene geometry and quiescent baseline/current cost binding to original repair is unverified.',U),
      row('21-09','Update high-value DESIGN/ARCHITECTURE/HANDOFF statements; preserve accepted clock/config sources and independent exact-tree review.',ref('docs/real-sky/STARTUP_CLOUD_HOTFIX.md',347,376),ref('ARCHITECTURE.md',11,20),'Documentation/currentness trace and returned review reconciliation.', 'First compositor timing and captured gaps explicit; no historical failure relabel.', 'Final report retains real startup failures and actual first-visible times; legacy PBR byteguard failure is not a blanket defect. Missing original hostile/repeated-entry replacement discriminators remain.',U)
    ],
    ['A matched current repeated crescent/zero800ms cold-warm first-visible transform/pixel sequence and exact local/no-saved first catalogue projection proof are not bound to the original controls.', 'Current dense dawn/dusk hostile interior/outside star+glint probe and continuous transition evidence are missing; empty/starless/helper-only fixtures cannot qualify opacity.', 'Startup/steady callback-cost comparison for this contract and complete preserved sun/phase/reduced-motion controls require narrow mapping.'],
    {'owner':'src/native/index.html beginSkyScene/commitSkyScene/updateSkySurface and current real-sky/moon composition interfaces',
     'preserve':'Retain successful H1 preview republishing, usable neutral/prayer UI, current terrain bridge, independent stellar cutout and normal transitions.',
     'steps':['Map/reuse exact final startup entries, then execute only missing repeated original growth/day-flash and accepted-local initial catalogue controls.', 'Inject hostile star/glint contributions at the actual displayed sink after paint and retain outside positive control; run dense dawn/dusk fade plus continuous sequence with current terrain.', 'Capture mandatory retained sun/phase/UI/constrained embed and normal/reduced/full motion controls; compare startup/steady callback costs; update only affected docs/tests if evidence shows a gap.'],
     'acceptance':'First visible accepted geometry matches scene in repeated cold/warm cases; partial providers do not deadlock UI; current actual stellar sink cannot leak through twilight moon and no black/dayhole; settled art/motion/geometry preserved.',
     'nonGoals':'No astronomy/time/provider redesign, richer catalogue, permanent extra loop, global transition removal or whole-widget loading hide.'},
    [{'name':'entry and twilight replacement controls','command':'Serial native browser on exact current runtime; use original issue Date/prayer/crescent fixture, new documents and native transitions, then actual-sink interior/outside probes and dense/continuous dawn/dusk.','reason':'Current scene/source tests and final general startup receipts do not prove these original discriminators.'}],
    ['R0003/R0004 accepted target/attempt/day consumed at interfaces; not whole-issue gates.', 'R001D consumed diagnostic and R0022 physical/calendar policies share integration writers.', 'R0025 established wind/day cloud continuity remains separate; N003 real OS/BFCache is not automatically required by these controlled startup claims.'],
    ['Final startup retains rejected dark shell/warm gap as failures, not final PASS.', 'Legacy PBR-source byte equality is superseded only by actual current terrain/material/crop evidence; removed synthetic-array tests require actual catalogue sink controls.'],
    ['PR42 current preview republishing repairs a measured Firefox cache-warm first-paint gap; current terrain bridge avoids later phasebucket/footprint withdrawal within unchanged bounds.'])

light = ref('src/native/index.html',2633,2653)
add(34,
    'The native atmospheric path shares phase/altitude eligibility across beam/cloud light/local glow/optics, separates opaque calendar/PBR presence, and refreshes appearance independently of held synthetic projection. The scientific sky/catalogue now has a distinct astronomical Moon state.',
    [
      row('22-01','Enumerate all actual writers/consumers and use consumed accepted phase/altitude without new clock/ephemeris; separate physical light/calendar surface.',light,[native_consumer('const moonObject=',21),ref('real-sky/native-contract.mjs',11,24),ref('real-sky/core/src/sky-background.mjs',39,45)],'Compare native consumed light summary with actual scientific sky/star/background owners.', 'One accepted physical permission for all enumerated atmospheric consumers.', 'Native summary is explicit. Scientific nativeJob carries no lunar eligibility; independent astronomical Moon term enters sky-background. Strict original shared-zero obligation has no supplied equivalent or amendment.',U),
      row('22-02','Daylight/below-horizon/near-new zero EVERY physical illumination/star wash/halo/corona/paraselenae/local glow; calendar disc remains opaque/textured.',light,native_consumer('const moonObject=',21),'Native zero matrix plus actual current scientific sky/star contributions and canvas crops.', 'All enumerated contributionszero in ineligible states; calendar does not inheritzero.', 'Final native24-case suite verifies native zero consumers. Scientific moonSkyLuminance only gates ground/below-disc/extinction, with no nearnew/daylight zero; native phase presentation override is not passed to that function.',U,[evidence(FINAL+'logs/native/r0022-lunar-consumers.log.gz','24 actual native paint/consumer VM cases; removed syntheticstar cases explicitly excluded')]),
      row('22-03','No prior-frame eligibility leaks; refresh later star appearance while held positions remain deliberate, including glints.',[light,ref('real-sky/native-star-preview.mjs',78,86)],ref('real-sky/core/src/physical-sky-renderer.mjs',61,72),'Actual displayed catalogue Moon-state/currentness release negative, with positions/inputs held.', 'Appearance uses same currentphysical light without forced positional animation.', 'Old synthetic _starEls/_glintEls proofs explicitly excluded. Real catalogue state has physical Moon; no final actual-star wash release replacement mapped to original gate was found.',U),
      row('22-04','Local .mglow and each distinct conditional optic sharezero permission; forcedoptic cannot bypasszero.',light,native_consumer('const moonObject=',21),'Restoreglowfloor/independentoptics envelope mutants; nearnew forcedhalo/paraselene.', 'Native consumerszero while physical eligibilityzero.', 'Actual paint writes --mgo and all native optic values from light; retained24 cases include forced zero and accepted weather-expiry gates. Final semantic mutation receipt unverified.',U,[evidence(FINAL+'logs/native/r0022-lunar-consumers.log.gz','Nativezero/optics control scope')]),
      row('22-05','Eligible crescent/half/gibbous/full baseline balance preserved unless optional phase refinement has matched independent adopted evidence; do not require Lambert.',ref('moon/src/moon-native.mjs',59,82),ref('moon/src/moon-detail.mjs',96,118),'Actual matched phase/material/source/encoding/crop lineage; no-op positive and old policy fault.', 'Readable uprighttexture/phase and differentiated optics; changed curve honestly bounded.', 'New V5 terrain/material has separate receiving/phase proof; six old balance cases stop at removed _glintEls and PBR byteguards differ. They do not demonstrate original eligible-layer balance. No mandatory Lambert replacement invented.',U,[evidence(FINAL+'controls/lunar-veil-v37-comparison/before-after-actual-crops.png','Same-current-terrain corona order correction, not allphase balance')]),
      row('22-06','Eligible weather controls clear/ice/droplet/overcast retain distinct halo/corona/rare lateral paraselenae and lunar source position.',light,native_consumer('const moonObject=',21),'Actual weather-layer inputs plus forcedcondition pixels and native consumedopacities.', 'Condition gates distinct and registered; cloud source unavailable failsclosed.', '24-case suite checks these native conditions. PR42 additionally requires actual admitted midwater cloud/fog for corona instead of humidity only; matched layer controls support that correction.',S,[evidence(FINAL+'logs/native/r0022-lunar-consumers.log.gz','Native weather-optics consumers'), evidence(FINAL+'controls/lunar-veil-v37-comparison/before-after-actual-crops.png','Retained matched current terrain/corona layer correction')]),
      row('22-07','Current/new/below/daylight opaque disc and outside-starpositive control, no black limb or spin; no genericglow/dawn/palette change.',ref('moon/src/moon-detail.mjs',31,40),native_consumer('moonTruth:(()=>{',15),'Actual current Moon composition/starpositive and edge/interior phase crops.', 'Zero physicalpermission never removes/transparently fades calendar surface.', 'Detail blocksdirect regardlessgroup emphasis; final cold/warm calendarsurface persists afterfirstterrain. Current comprehensive actualstarpositive opacity matrix unverified.',U),
      row('22-08','15-60s real elapsed cloud/glint motion, reduced/fullfresh docs; header/footer/prayer/sun/weather truth preserved; no added loops/network/readback/texture allocation; warmedpaint cost comparison.',light,[ref('moon/src/moon-detail.mjs',91,120),ref(FINAL+'motion/chromium-normal1x-cold.webm')],'Current actual elapsed clip/branch plus same-scene cost and boundedstate.', 'No motion/art/UI regression and no physicalauthority leakage.', 'Final normal imagery/sourceboundmotion and broadcost receipts are narrowerthan original all-consumer controls; exact warmedbeforeafter comparison forshared eligibility not identified.',U),
      row('22-09','DESIGN/OPTICS/HANDOFF/high-valuecomments current; independentcompleteconsumer enumeration and exact beforeafter evidence before closure.',ref('DESIGN.md',198,204),[ref('OPTICS.md',157,176),ref('HANDOFF.md',111,118)],'Explicit policy/currentconsumer documentation and independentreview.', 'No old calendarvariable silently equated to current physical astronomy.', 'Docs retain zero calendar physical-light wording; supplied brief has model/iframe amendments but no explicit lunar gate supersession. Primary must reconcile exact policy/interface gap.',U)
    ],
    ['Native24-case controls do not enumerate the later scientific Moon sky/background/catalogue consumer; strict original day/nearnew/allphysicalzero policy is not demonstrated across those interfaces.', 'Removed synthetic-star and PBR-byteguard failures need actual current-state/phase-balance replacement discriminators; a label saying obsolete is insufficient.', 'Final semantic mutation, actualstarpositive opacity/phase/optics and warmedpaint proofs are incomplete.'],
    {'owner':'Native physical-light eligibility in src/native/index.html plus authored real-sky integration boundaries; immutable scientific oracle must not be casually edited',
     'steps':['Reconcile whether the original categorical lightgate remains binding for scientific astronomy; identify exact trusted policy if replaced, never infer permission from a new ephemeris.', 'Enumerate native and scientific currentlunar consumers with produced/consumed identity; supply direct zero/eligible/star-wash/fault controls for the selected policy.', 'Retaincurrent V5 material/calendar presence; run matchedphase/optics/opacity/motion and warmedcost controls; amend docs and repair only proven gaps under fresh authorization.'],
     'acceptance':'Every still-binding physicalconsumer obeys the same acceptedeligibility and allzero/eligible/forced/weatherfault controls discriminate; any changed policy has exact authority and demonstrated equivalent consumer behavior; calendaropaque textured presence and current V5 quality remain.',
     'nonGoals':'No Lambert mandate, empiricalcalibration programme, nativepresentation override silently treated as astronomy, flattened sprite, maria spin, newclock/network/loop or calendartransparency.'},
    [{'name':'scientific/native lunar permission map','command':'On exact current source, trace nativeJob -> accepted astronomical state -> sky-background/catalogue and native consumed-light summary; run bounded source-level zero/eligiblecontrols plus actual-star wash/currentness negative before any native visual matrix.','reason':'Laterconsumer is outside old24-case native test; strictsharedgate replacement proof required.'}],
    ['R001D owns consumed native geometry diagnostic; V5 materialcurrentness and realastronomy are separate inputs.', 'R0021 owns stellarocclusion/initialreveal, R0009 calendar truth, R0008/R0020 time authority; do not absorb them.', 'Ownercurrent modelprecip amendment does not itself amend lunar eligibility.'],
    ['Retained24 native positives/negatives are meaningful at their actual paint path.', 'Six _glintEls failures are setup failures, not detections or evidence of bad current stars.', 'Newcorona clearhumid/droplet layerorder controls are relevant improvements but do not substitute for completephysicalconsumergate.'],
    ['PR42 excludes humidity-only corona and places currentopaque terrain after nativeoptics background, removing the darkside veil without material gain.'],
    ['Need exact trusted lunarpolicy supersession/equivalentgate if the scientific astronomical term is intentionally exempt from original day/nearnew categoricalzero. No new astrophysical defect is asserted solely from tiny nonzero rawradiance.'])

cloud = ref('src/native/index.html',2462,2513)
add(37,
    'Established scene population is stable across ordinary days; displacement/lifecycle/wander integrate bounded monotonic intervals once per deck, oldwind before accepted refresh, with hidden/reduced/longgap rebasing and explicit seek reconstruction. Actual visible copies supply rain density.',
    [
      row('25-01','Stable acceptedtarget+explicitseed identity; no ordinaryUTCday/month/year population replacement; retain original morphology/colors/canvas.',cloud,native_consumer('const _cloudMotion=',39),'Current actualpainter identity/noise and originalboundary failure/control.', 'Ordinaryboundary preserves population; deliberate target/seek reconstructed.', 'Final9-case continuity+16-case lifecycle use actualpainter commands/noise and cover UTC/month/year; source captures initialday seed once.',S,[evidence(FINAL+'logs/native/r0025-continuity.log.gz','9 actualpainter command/noise controls'),evidence(FINAL+'logs/native/r0025-lifecycle.log.gz','16 actualtime/loop/axes/rain controls')]),
      row('25-02','Integrate once per deck independentclusters/coverage; sameinstant windspeed/heading/calm/reversal/gust refresh cannot move accumulatedposition.',[cloud,ref('src/native/index.html',2845,2866)],native_consumer('function applyCloudState(A){',18),'Sameinstant actualrender/paint command/column comparison and oldvelocity pendingintervalcontrol.', 'Changedwind affects futuretravel only; equal-time idempotence.', 'Finalcommands directly assert same-time trace/columns equality and oldvelocity integratedbefore setter; all25 mappedcasespass.',S,[evidence(FINAL+'logs/native/r0025-continuity.log.gz','actualweather->render->paint owner trace')]),
      row('25-03','Emptydeck return and longgaps cannot apply newvelocity retroactively; finitebounded retention and periodicvisiblewrapcontinuity.',cloud,native_consumer('function advanceCloudMotion(',27),'Empty/visible axes,2s suspension,1ms edgewrap and1e12rate bound controls.', 'Allaxesadvanceindependently; no wrapjump or unboundedbacklog.', '16-case lifecycle directly tests each realpainter/axescondition; boundedarrays3+3+wander and _colDens144.',S,[evidence(FINAL+'logs/native/r0025-lifecycle.log.gz','actualsource boundary/retainedstatecontrols; no nativepixels')]),
      row('25-04','Separatecivilclock from visualelapsed; hidden/resumed/reduced/full rebase, wallcorrections continuous, explicitforward/backseek deterministically reconstruct; singleloop.',cloud,native_consumer('function advanceCloudMotion(',27),'Actualownedloop visibilityrepeat/wallseek/reduced/full controls.', 'No replacedconstanttimestamp/epochjump, no multipleloops.', 'Retained16-case source suite verifies exactsinglecallback and axes; native current lifecycle also exercises controlledvisibility/clock/reduced states, not realOS.',S,[evidence(FINAL+'logs/native/r0025-lifecycle.log.gz','ownedrAF/event boundarydoubles; no realOS claim')]),
      row('25-05','Coverage mapping/cadence snapfirstaccepted deck and easeexisting .08 response; preserve coherentstartup without fakeempty introduction.',ref('src/native/index.html',2849,2861),native_consumer('function applyCloudState(A){',13),'Firstacceptedcloudstartup and establishedcoverage refresh.', 'No cadencechange without elapsed-response reference; no longartificialempty wait.', 'Source retains0.08/nonadvancing andfirstsnap; finalstartup partial/heavy/rain sheets cover actualscene. No new adaptivegovernor introduced.',S,[evidence(FINAL+'runs/joined-v49-final-firefox-startup-partial/results.json','exactruntime consumedstartup currentmodel cloud')]),
      row('25-06','Recompute actualvisible _colDens and retain rainalignment; permissions expire/change target immediately, no faded rain authority.',ref('src/native/index.html',2539,2609),native_consumer('function tieRainToClouds(){',17),'Visiblecopydensity/dropcolumn and expiredcurrentweather controls; actualrainpixels.', 'Particlesorigin follows actualcloudcolumns; no stale/forecast/oldtargetauthority.', '16-case suite verifies columns/drops/expiry and sourceweather withdraws permission independently. Finalmodelrain clips exist but fullnamed target/cloudorigin pixelcontrol unverified.',U,[evidence(FINAL+'logs/native/r0025-lifecycle.log.gz','actualcolumns plus containeddrop/permission consumer')]),
      row('25-07','Retain originals failingwind/dayimages; current same-time wind/heading/calm/reversal/gust, no-op firstimage parity and boundary/ordinary rendered controls.',cloud,native_consumer('function paintClouds(t){',15),'Matched rawRGBA premultRGB controls, not only traces/hash.', 'Pixelsandmodelagree; no massesrelocateordinarywind/day.', 'Issue preserves originaldiscriminators; final25 sourcecases are command/noise evidence only. No currentboundwind/daybeforeafter RGBA/crop packet was located.',U),
      row('25-08','Actual15-60s liveclock finiteweather realisticnonzerowind provestravel/lifecycle; reduced/full freshdocs; clearnegative; preservecurrent/new/belowmoon andrain.',cloud,[ref(FINAL+'motion/chromium-normal1x-cold.webm'),ref(FINAL+'visual-review/chromium-moon-cold-motion.png')],'Realelapsed watched clip/pixelinterval, not frozen simTime/hash.', 'Meaningfulvisiblemotionandsettledart survive.', 'Viewedfinalnormal1x sheet showscloudmotion20..98s and realclockminuteschange. Fullclip/reduced/full and exactcontinuouswind/daycontrols require specifiedsourceboundreceiptmapping.',U),
      row('25-09','Newacceptedtarget resetscoherently without oldprecipfade; wallclock/dayadoption/asyncstate consumers coordinated, no wholeissue prerequisites.',ref('src/native/index.html',2067,2074),native_consumer('function beginSkyScene(){',8),'TargetA->B->newA acceptedgeneration and rainorigin/expiry controls.', 'Sceneidentitynew; no oldlocationparticles.', 'SourcebeginSkyScene clearscoverage/density/canvas; finalgeography/currentness supportsactualtargetflow. Mandatorycloud-specific negative pixelinterface not identified.',U),
      row('25-10','Samequiescent setup beforeafter steady paintercost andretainedstate; no extraprovider/history/perclusterallocation/permanentloop; no GPU/battery inference.',cloud,native_consumer('const _cloudMotion=',39),'Quiescentbeforeaftermeasureandboundedstate/callbackinventory.', 'No materialcost/state/loopregression in chosenscene.', 'Statebounded andsingleloop sourcecontrols; finalgeneralperformance gates do not provideoriginalcloudpainter beforeaftercost. N001partial is not blanketblocking but this mappedcostproof is unverified.',U),
      row('25-11','Affectedhigh-valuecontinuity/timecomments/docs current; no-buildruntime/staticembed,325x530, opaqueMoon,honestdawn,solaroptics/prayer/accessibility preserved and independentpixelreview.',cloud,[ref('AGENTS.md',7,28),ref('docs/real-sky/STARTUP_CLOUD_HOTFIX.md',350,394)],'Focusedsource/docs pluscurrentartcontrols and exactevidencecomment.', 'No adaptivePlan07 expansion or diagnostic-only closure.', 'Currentcomments stateoldwindintegration andsuspensionpolicy. Comprehensiveoriginal cloudpixel/cost closurepacket notpresent; thisis anunreconciled proposal.',U)
    ],
    ['Exact-current sameinstant wind/day/month/year/no-op pixel comparisons and originalfailingimages pairedwithcandidate are missing;25command/statecases alone do not satisfy pixelcontract.', 'Current normal1x motion imagery supports narrower visiblemovement, but named actualraincolumn/target and reduced/full transitions need exactreceiptmapping.', 'Quiescent old/new steadycloudpaintercostcomparison is absent; do not promote broadperformance status.'],
    {'owner':'src/native/index.html cloudSceneIdentity/advanceCloudMotion/applyCloudState/paintClouds/tieRainToClouds and narrow cloudfixture/evidence',
     'preserve':'Keep stablepopulation, oldvelocityintegration, monotonicboundedaxes,2srebase, periodicedgecopies,firstcoverage and separateimmediateprecippermission.',
     'steps':['Reuse25exactsource command/statecases; execute only missing same-time/boundary renderedbeforeafter controls atoriginalsyntheticinputs with no-op and constantpositivewind controls.', 'Supply normal15-60slive/reduced/full/hidden-resume renderedevidence and cloudcolumn/permissionexpiry/targetnegative; reuse currentMoon/sun/UI proofs narrowly.', 'Measuresteadycloudpaintercost/retainedstate beforeafter ononequiescent setup; repaironlydemonstratedcontinuity/costfaults; updateaffectedcomments/docs.'],
     'acceptance':'Ordinarywind/day/month/year updates preserve renderedpopulation/accumulatedposition, equal-timepaintsidempotent, futurewindmotionvisible; chosenresume/seekpolicyandrainorigin/expiry remaincorrect; no materialcost/state/loopregression.',
     'nonGoals':'No adaptivePlan07governor,batteryprogramme,densityfieldbackend, palette/solarrepair,ephemeris, liveownerlocation orperiodictastechecks.'},
    [{'name':'cloudpixelandcostclosure','command':'Use originalissue finiteDate/prayer/weather fixture; save actualcloudRGBA/fullcard atsameT wind3->3.1,heading/calm/reversal/gust,no-op and UTC/month/year boundaries; run live1x15-60s and quiescent old/new paintercost serially.','reason':'Requiredpixel/costcontrols missing beyond25sourcecommand/statecases; no hashbasedmotioncredit.'}],
    ['R0020wallclockauthority consumed separately from cloudmonotonicvisualtime.', 'R0003asyncacceptedtarget andR0024precippermission consumedatinterfaces; ownercurrentmodelprecip amendment retained.', 'R0021firstacceptedreveal,R0022physicalMoon eligibilityandotherUI/calendargates notabsorbed; Plan07broadergovernor staysheld.'],
    ['Retained9+16cases cover actualpainter/columns/noise/clock boundaries withexplicit no-nativepixel limit.', 'Oldr0025-mutations driverfirstrequiresfullr0021pass andobsoletePBRguard; runningitsfailureis not a cloudmutation detection.', 'No cloudhash credited as normalelapsedM0 proof.'])

WORD_SPACING = {
 'actualsource':'actual source','actualpaint':'actual paint','actualpainter':'actual painter',
 'actualrender':'actual render','actualtime':'actual time','actualstar':'actual star',
 'actual-star':'actual star','actualcurrent':'actual current','actualscene':'actual scene',
 'currentterrain':'current terrain','currenttarget':'current target','currentmodel':'current model',
 'currentphysical':'current physical','currentlunar':'current lunar','current V5':'current V5',
 'current-state':'current state','sourcebound':'source-bound','sourcelevel':'source-level',
 'fullclip':'full clip','fullsource':'full source','allphase':'all phase','allzero':'all zero',
 'allphysicalzero':'all physical zero','oldwind':'old wind','oldvelocity':'old velocity',
 'newvelocity':'new velocity','sameinstant':'same instant','sametime':'same time',
 'old/new':'old/new','samequiescent':'same quiescent','beforeafter':'before/after',
 'targetA':'target A','sceneidentitynew':'new scene identity','slotnew':'new slot',
 'firstaccepted':'first accepted','firstterrain':'first terrain','firstimage':'first image',
 'firstvisible':'first visible','initialday':'initial day','intermittentbaseline':'intermittent baseline',
 'oldtarget':'old target','oldlocation':'old location','futurewind':'future wind',
 'emptysource':'empty source','emptydeck':'empty deck','longgaps':'long gaps',
 'longgap':'long gap','lightgate':'light gate','sharedgate':'shared gate',
 'completephysicalconsumergate':'complete physical consumer gate',
 'physicalconsumer':'physical consumer','physicalconsumers':'physical consumers',
 'physicalauthority':'physical authority','physicalastronomy':'physical astronomy',
 'physicallunar':'physical lunar','lunarpolicy':'lunar policy','consumergate':'consumer gate',
 'originalgate':'original gate','originalboundary':'original boundary','originaldiscriminators':'original discriminators',
 'originalfailingimages':'original failing images','originalcloudpainter':'original cloud painter',
 'matchedphase':'matched phase','phasebalance':'phase balance','phase-balance':'phase balance',
 'clearhumid':'clear humid','dropletlayer':'droplet layer','clearhumid/droplet':'clear humid/droplet',
 'layerorder':'layer order','localglow':'local glow','glowfloor':'glow floor',
 'independentoptics':'independent optics','forcedoptic':'forced optic',
 'forcedcondition':'forced condition','nearnew':'near-new','belowhorizon':'below horizon',
 'zeropermission':'zero permission','zeroeligible':'zero/eligible',
 'no-star-through':'no stars through','starpositive':'star-positive','star-wash':'star wash',
 'terraincurrentness':'terrain currentness','materialcurrentness':'material currentness',
 'nativepresentation':'native presentation','opaqueMoon':'opaque Moon',
 'calendaropaque':'calendar opaque','calendartransparency':'calendar transparency',
 'calendarvariable':'calendar variable','calendartransparently':'calendar transparently',
 'Moonlight':'Moonlight','semanticmutation':'semantic mutation','recompute mutants':'recompute mutants',
 'wrongframe':'wrong frame','defaultappearance':'default appearance','consumeridentity':'consumer identity',
 'current-surface':'current surface','paintercost':'painter cost','warmedpaint':'warmed paint',
 'boundedstate':'bounded state','retainedstate':'retained state','fixedamount':'fixed amount',
 'singleloop':'single loop','multipleloops':'multiple loops','extraprovider':'extra provider',
 'perclusterallocation':'per-cluster allocation','permanentloop':'permanent loop',
 'steadycloudpainter':'steady cloud painter','cloudpixel':'cloud pixel','cloudpixels':'cloud pixels',
 'cloudcolumn':'cloud column','cloudcolumns':'cloud columns','cloudorigin':'cloud origin',
 'cloudhash':'cloud hash','failingwind':'failing wind','dayimages':'day images',
 'firstcoverage':'first coverage','coverageindependent':'coverage independent',
 'visiblewrapcontinuity':'visible wrap continuity','periodicvisiblewrapcontinuity':'periodic visible wrap continuity',
 'periodicedgecopies':'periodic edge copies','accumulatedposition':'accumulated position',
 'futuretravel':'future travel','cloudmonotonicvisualtime':'cloud monotonic visual time',
 'wallclockauthority':'wall-clock authority','liveownerlocation':'live owner location',
 'periodictastechecks':'periodic taste checks','Plan07broadergovernor':'Plan 07 broader governor',
 'adaptivePlan07governor':'adaptive Plan 07 governor','batteryprogramme':'battery programme',
 'densityfieldbackend':'density-field backend','solarrepair':'solar repair','newclock':'new clock',
 'permanentextra':'permanent extra','wholeissue':'whole issue','issueDate':'issue Date',
 'readoutcontrols':'readout controls','stageassertions':'stage assertions',
 'bodyfield':'body field','testfile':'test file','exactsource':'exact source','exactruntime':'exact runtime',
 'testcontrols':'test controls','faultcontrols':'fault controls','weatherfault':'weather fault',
 'errorcontrols':'error controls','quiescentbefore':'quiescent before',
 'fullrequired':'full required','reducedmotion':'reduced motion','fullmotion':'full motion',
 'freshdocs':'fresh docs','freshdocuments':'fresh documents','hidden-resume':'hidden/resume',
 'clipsource':'clip source','steadycallback':'steady callback','callbackinventory':'callback inventory',
 'R58/OOB/notfalse/recompute':'R58/OOB/not-false/recompute','notfalse':'not-false',
 'produced/consumed':'produced/consumed','sharedeligibility':'shared eligibility',
 'texture/phase':'texture/phase','uprighttexture':'upright texture','sinkscontrols':'sink controls',
 'beforefirst':'before first','permissionexpiry':'permission expiry','targetnegative':'target negative',
 'high-valuecontinuity/timecomments':'high-value continuity/time comments',
 'independentpixelreview':'independent pixel review','motioncredit':'motion credit',
 'programme':'programme','darkside':'dark side','rawradiance':'raw radiance',
 'staticsource':'static source','date2026':'date 2026','Noop':'No-op'
}
def readable(value):
    if not isinstance(value,str): return value
    for word, replacement in sorted(WORD_SPACING.items(), key=lambda item: -len(item[0])):
        value = re.sub(r'(?<![\w/])'+re.escape(word)+r'(?![\w/.])', replacement, value)
    value = re.sub(r'(?<=\d)(?=(?:case|cases|named|actual|source|command|VM|required|final|native|physical|synthetic|glass)\b)', ' ', value)
    value = re.sub(r'\b([a-z][A-Za-z-]{2,})(?=\d)', r'\1 ', value)
    return value
def text_cell(value): return readable(str(value)).replace('|', '\\|').replace('\n', ' ')
def label(r):
    p = r['path']
    return f'[{p}]({r["url"]})'
def comment(a):
    cid = a['canonicalId']
    lines = [f'# RLGWO closure audit — {cid} — REMAINS OPEN', '',
             f'<!-- RLGWO-AUDIT:{SHA}:{cid}:2026-10-08 -->', '',
             f'**Recommendation: LEAVE OPEN.** {a["scopeOfDone"]}', '',
             f'Target `{SHA}`, tree `{TREE}`, runtime SHA-256 `{RUNTIME}`, index SHA-256 `{INDEX}`; audit date 2026-10-08. '
             f'Original issue body SHA-256 `{a["originalBodySha256"]}`, revision `{a["originalUpdatedAt"]}`. Complete body, discussion and events were read. '
             'No issue comment amends this contract. Referenced commits/events are provenance, not authorization.', '',
             'The review reads the clean source tree identical to the merge. **No fresh product tests or browsers were run by reviewer F.** '
             'Retained final-v49 checks are historical executions at the exact runtime, individually scoped below. Earlier receipts retain their earlier hashes. '
             'Missing native/pixel proof is unverified; it is not automatically a product defect.', '',
             '| Mandatory obligation | Owner and delivered consumer | Discriminator / expected | Observed and disposition |',
             '|---|---|---|---|']
    for r in a['requirementMatrix']:
        owners = ', '.join(label(x) for x in r['authoredOwners'])
        consumers = ', '.join(label(x) for x in r['deliveredConsumers'])
        lines.append('| '+ ' | '.join(map(text_cell, [r['id']+': '+r['obligation'], owners+' → '+consumers,
             r['discriminator']+' Expected: '+r['expected'], r['observed']+' **'+r['status'].upper()+'**']))+' |')
    paths = {}
    for r in a['requirementMatrix']:
        for e in r['evidence']: paths[e['source']['path']] = e
    lines += ['', 'Retained evidence and controls:']
    for e in paths.values(): lines += ['- '+label(e['source'])+' — '+e['scope']+'. Historical reuse inspected in this audit.']
    for control in a['negativeControls']: lines += ['- '+control]
    lines += ['', 'The final native runner keeps eight named legacy failures and four TODOs. Removed synthetic arrays or old PBR source bytes are not product counterexamples by themselves; each mapped obligation still needs its actual replacement discriminator. '
              'N001/N002 PARTIAL and N003 BLOCKED do not create blanket dependencies. No claim of CI, human approval, release authority or all-browser conformance is made.', '', '## Next RLGWO increment required for closure', '']
    for gap in a['gaps']: lines += ['- '+gap]
    nxt = a['proposedNextRlgwoIncrement']
    lines += ['', 'Semantic owner and bounded scope: '+nxt['owner']+'.']
    if nxt.get('preserve'): lines += ['', 'Preserve completed work: '+nxt['preserve']]
    lines += ['', 'Proposed steps, requiring the ordinary authorization applicable to any future production change:']
    for i, step in enumerate(nxt['steps'], 1): lines += [f'{i}. {step}']
    lines += ['', '**Acceptance and closure proof:** '+nxt['acceptance'], '', '**Non-goals:** '+nxt['nonGoals'], '', 'Dependencies and limitations:']
    for dep in a['dependencies']: lines += ['- '+dep]
    for decision in a['ownerDecisions']: lines += ['- '+decision]
    for improvement in a['improvements']: lines += ['- Demonstrated improvement retained: '+improvement]
    lines += ['', 'Execution environment for retained final checks: Windows, Node22.16.0; browser receipts identify Chromium148.0.7778.96 or Firefox150.0.2 and their synthetic/private storage/clock/transport fixtures. '
              'These fixtures do not claim owner live conditions, real OS/BFCache behavior or universal GPU/battery performance. Needed new commands/inputs are those in the original contract and the bounded steps above.', '',
              'Reviewer F returned this proposal. The primary has not yet reconciled/approved it or confirmed completion of the serial delivered-baseline rollout to this worker. '
              '**This comment is not posted and no closure is authorized by this artifact.** Primary reconciliation and an individual publication approval remain required.']
    return '\n'.join(lines)+'\n'

OUT.mkdir(parents=True, exist_ok=True)
git = lambda *args: subprocess.check_output(['git','--no-optional-locks',*args],cwd=ROOT,text=True).strip()
assert git('rev-parse', SHA+'^{tree}') == TREE
assert git('rev-parse','HEAD^{tree}') == TREE
assert digest((ROOT/'index.html').read_bytes()) == INDEX
assert git('status','--porcelain') == ''
source_paths = ['src/native/index.html','src/native/config.js','src/native/builder.html','index.html','config.js','builder.html',
                'tests/smoke.html','tests/widget-fixture.html','tests/r001a-radio.cjs','tests/r001d-diagnostics.cjs',
                'tests/r0025-continuity.cjs','tests/r0025-lifecycle.cjs','real-sky/native-contract.mjs','moon/src/moon-native.mjs']
inspection = {'createdAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(), 'target':SHA,'tree':TREE,
              'reviewedHead':git('rev-parse','HEAD'), 'remote':git('remote','get-url','origin'), 'dirtyState':'clean',
              'scope':'Fresh read-only path/tree/byte/contract/receipt parsing; no product test or browser execution',
              'files':{p: {'sha256':digest((ROOT/p).read_bytes()),'bytes':(ROOT/p).stat().st_size} for p in source_paths}}
receipt_names = ['r0017-contract','r0017-transport','r0018-timetable-contrast','r001a-radio','r001d-lifecycle','r0025-continuity','r0025-lifecycle']
inspection['retainedReceipts'] = []
for name in receipt_names:
    p = FINAL+'logs/native/'+name+'.log.gz'
    raw = log(p)
    item = {'path':p,'compressedSha256':digest((ROOT/p).read_bytes()),'decompressedSha256':digest(raw.encode()), 'freshExecution':False}
    if raw.lstrip().startswith('{'):
        obj=json.loads(raw); item['kind']=obj.get('kind',obj.get('limit'))
        item['caseCounts']={'pass':sum(r.get('result',r.get('status'))=='PASS' for r in obj.get('results',[])),
                            'fail':sum(r.get('result',r.get('status'))=='FAIL' for r in obj.get('results',[]))}
    else:
        item['terminal']=json.loads([x for x in raw.splitlines() if x.strip()][-1])
    inspection['retainedReceipts'].append(item)
(OUT/'inspection-receipt.json').write_text(json.dumps(inspection,indent=2)+'\n',encoding='utf-8')
for number, a in ASSESSMENTS.items():
    a['inspectionReceipt']='inspection-receipt.json'
    a['executedCommands']=[
        {'command':['git','--no-optional-locks','rev-parse',SHA+'^{tree}'], 'environment':str(ROOT), 'kind':'fresh read-only identity', 'expected':TREE,'observed':TREE,'exitCode':0},
        {'command':['git','--no-optional-locks','rev-parse','HEAD^{tree}'], 'environment':str(ROOT), 'kind':'fresh read-only reviewed-source equivalence', 'expected':TREE,'observed':TREE,'exitCode':0},
        {'command':['git','--no-optional-locks','status','--porcelain'], 'environment':str(ROOT), 'kind':'fresh read-only dirty state', 'expected':'','observed':'','exitCode':0},
        {'command':'SHA-256 of actual index.html bytes and complete issue body UTF-8 bytes', 'environment':'Python -I -S -B, hashlib/JSON; no network/browser', 'kind':'fresh read-only byte binding', 'expected':{'index':INDEX,'contract':a['originalBodySha256']}, 'observed':{'index':INDEX,'contract':a['originalBodySha256']},'exitCode':0},
        {'command':'Read authored source, delivered consumers, exact assertions and retained final-v49 gzip/JSON receipts', 'environment':'PowerShell UTF-8 reads + Python standard-library gzip/json/hashlib', 'kind':'fresh inspection of historical execution', 'expected':'Preserve scope and original source/runtime identities; do not invent execution', 'observed':'inspection-receipt.json records bytes, receipt hashes and original terminal/case counts; zero fresh product/browser test commands','exitCode':0}
    ]
    # Normalize human prose only. Paths, commands, hashes, literals and refs are protected.
    a['scopeOfDone']=readable(a['scopeOfDone'])
    for r in a['requirementMatrix']:
        for key in ['obligation','discriminator','expected','observed']:r[key]=readable(r[key])
    for key in ['gaps','dependencies','negativeControls','improvements','ownerDecisions']:
        a[key]=[readable(item) for item in a[key]]
    for key,value in a['proposedNextRlgwoIncrement'].items():
        if isinstance(value,str):a['proposedNextRlgwoIncrement'][key]=readable(value)
        elif isinstance(value,list):a['proposedNextRlgwoIncrement'][key]=[readable(item) for item in value]
    (OUT/f'{number}-assessment.json').write_text(json.dumps(a,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    (OUT/f'{number}-comment.md').write_text(comment(a),encoding='utf-8')
summary={'schema':'rlgwo-worker-summary-v1','reviewer':'F','target':SHA,'tree':TREE,'runtime':RUNTIME,
         'requestedModel':'gpt-6.1-sol','requestedEffort':'max','effectiveConfigurationConfirmed':False,
         'assigned':[23,24,26,29,33,34,37], 'sourceDirtyState':'clean', 'productTestsExecuted':[], 'browserTestsExecuted':[],
         'results':[{'issue':n,'canonicalId':a['canonicalId'],'verdict':a['verdict'],'gaps':a['gaps'],
                     'assessment':f'{n}-assessment.json','comment':f'{n}-comment.md','requirements':len(a['requirementMatrix'])} for n,a in ASSESSMENTS.items()],
         'crossIssueDependencies':{'23':['R0011 storage seam','R0024 amended model/observation consumer'],
                                  '24':['Trusted appearance amendment unresolved','H6/R000A row classification'],
                                  '26':['R0010 output contract only'],'29':['R0022 consumed light','current V5 terrain surface'],
                                  '33':['R0003/R0004 accepted scene','R001D','R0022','R0025 separate continuity'],
                                  '34':['R001D','R0021','actual scientific Moon gate replacement'],'37':['R0020','R0003','R0024','R0021']},
         'missingChecksRequested':[{'issue':n,**c} for n,a in ASSESSMENTS.items() for c in a['missingChecksRequested']],
         'primaryQuestions':[{'issue':24,'question':ASSESSMENTS[24]['ownerDecisions']},{'issue':34,'question':ASSESSMENTS[34]['ownerDecisions']}],
         'noBlanketBlocker':'N001/N002 PARTIAL and N003 BLOCKED considered only at mapped interfaces; no closure quota.',
         'publication':'HOLD: no primary reconciliation/individual approval yet; no GitHub effects.',
         'stop':'Worker returns completed bounded packets and waits for scoped follow-up; no new programme or uncontrolled tests.'}
(OUT/'summary.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({'writtenIssues':list(ASSESSMENTS),'matrices':sum(len(a['requirementMatrix']) for a in ASSESSMENTS.values()),
                  'verdicts':{n:a['verdict'] for n,a in ASSESSMENTS.items()},'sourceClean':True,'out':str(OUT)}))
