#!/usr/bin/env python3
"""R0022's original warmed cost rule, applied to retained raw browser samples.

This is an evidence consumer, not a browser launcher or authority issuer. The
paired collector is r0022-paint-cost.mjs. ROOT must review the actual adapters,
adopt the budget before the run and admit its exclusive native resource. A
structural pass cannot establish observation provenance or visual acceptance.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import statistics


COUNTERS = ('pendingJobs', 'rafChains', 'timerChains', 'intervalChains', 'listeners', 'providers',
            'networkRequests', 'renderRequests', 'readbacks', 'textureAllocations',
            'retainedArrays', 'retainedBytes')
EVENT_COUNTERS = {'networkRequests', 'renderRequests', 'readbacks', 'textureAllocations'}
ORIGINAL_SCOPES = {'atmosphere', 'paint', 'renderMoon'}
SEQUENCE = [(block, order, side) for block in range(4)
            for order, side in enumerate('ABBA')]
HOST_ACCEPT = b' function accept(result,_id,request){'
HOST_BIND = b' window.realSkyState=readState;window.realSkyFrame=()=>frame; // Diagnostics, not render authority.'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def pin(value):
    return (isinstance(value, str) and len(value) == 64 and
            all(c in '0123456789abcdef' for c in value))


def finite(value):
    try:
        return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
    except OverflowError:
        return False


def percentile95(values):
    # Nearest rank, declared here before native acquisition; retain all samples.
    return sorted(values)[math.ceil(.95 * len(values)) - 1]


def utc(value):
    try:
        date = datetime.fromisoformat(value.replace('Z', '+00:00'))
        return date.astimezone(timezone.utc) if date.tzinfo is not None else None
    except (AttributeError, TypeError, ValueError):
        return None


def prepare_host_owner(owner_bytes, expected_sha256):
    """Instrument an exact semantic owner only in ROOT's disposable cost copy.

    The sink receives raw data before presentation; the binder exposes the
    original closure and original currentness predicate. Neither hook supplies
    input, overrides an acceptance fence nor starts an extra controller. Disable
    captureRaw after setup, before warmup. The exact original bytes can be
    reconstructed by removing just the two inserted strings.
    """
    if not pin(expected_sha256) or sha(owner_bytes) != expected_sha256:
        raise ValueError('Exact selected host-owner preimage mismatch')
    if b'__r0022CostProbe' in owner_bytes:
        raise ValueError('Duplicate cost fixture instrumentation')
    if owner_bytes.count(HOST_ACCEPT) != 1 or owner_bytes.count(HOST_BIND) != 1:
        raise ValueError('Original admission/binder owner unavailable or ambiguous')
    newline = b'\r\n' if b'\r\n' in owner_bytes else b'\n'
    capture = newline + b'  if(window.__r0022CostProbe?.captureRaw)window.__r0022CostProbe.captureRaw(result,request);'
    binder = newline + b' if(window.__r0022CostProbe?.bind)window.__r0022CostProbe.bind({accept,current:request=>lifecycle.current(request,snapshot()),readState});'
    instrumented = owner_bytes.replace(HOST_ACCEPT, HOST_ACCEPT + capture, 1).replace(HOST_BIND, HOST_BIND + binder, 1)
    if instrumented.replace(capture, b'', 1).replace(binder, b'', 1) != owner_bytes:
        raise ValueError('Fixture instrumentation changed original owner bytes')
    return instrumented


def assess(raw, decision, *, decision_sha256):
    gaps, results = [], []

    def require(condition, message):
        if not condition:
            gaps.append(message)
        return condition

    if not isinstance(raw, dict) or not isinstance(decision, dict):
        return {'status': 'INCOMPLETE', 'gaps': ['Receipt/decision must be objects'], 'scopes': []}
    require(raw.get('schema') == 'r0022-paint-cost/v1', 'Wrong raw receipt schema')
    require(raw.get('measurementKind') == 'actual-browser', 'Native observation absent')
    require(raw.get('status') == 'RAW_BATCHES_RETURNED' and not raw.get('error'), 'Incomplete/interrupted acquisition')
    require(raw.get('noiseDisposition') == 'CONTROLLED', 'Noisy/unequal setup is not cost proof')
    require(decision.get('schema') == 'r0022-cost-budget-decision/v1', 'Wrong decision schema')
    require(decision.get('approved') is True, 'Budget not adopted')
    require(decision.get('approvedBeforeMeasurement') is True, 'Pre-run budget adoption absent')
    # Both explicit schema spellings identify the same pre-run owner decision.
    # A malformed/conflicting supplied field must not hide behind a valid alias.
    adoption_times = [utc(decision[k]) for k in ('adoptedAtUtc', 'approvedAtUtc') if k in decision]
    consistent_adoption = bool(adoption_times) and all(t is not None for t in adoption_times) and len(set(adoption_times)) == 1
    require(consistent_adoption, 'Missing, invalid or conflicting budget adoption timestamps')
    adopted = adoption_times[0] if consistent_adoption else None
    started = utc(raw.get('startedAtUtc'))
    require(adopted is not None and started is not None and adopted < started,
            'Actual budget decision does not precede measurement UTC')
    require(decision.get('absoluteFloorMs') == .25 and decision.get('relativeIncrease') == .1,
            'Original proposed budget changed; a revised decision needs separate review')
    authority = raw.get('authority', {})
    if not isinstance(authority, dict): authority = {}
    require(pin(decision_sha256) and authority.get('budgetDecisionSha256') == decision_sha256,
            'Budget decision bytes do not match acquisition')
    for key in ('resourceAdmissionSha256', 'independentAdapterReviewSha256'):
        require(pin(authority.get(key)), 'Missing authority binding: ' + key)
    setup = raw.get('setup', {})
    if not isinstance(setup, dict): setup = {}
    require(setup.get('engine') in ('chromium', 'firefox'), 'Unidentified admitted engine')
    for key in ('browserVersion', 'machine', 'powerSetting', 'profile'):
        require(isinstance(setup.get(key), str) and bool(setup[key]), 'Missing setup: ' + key)
    for key in ('executableSha256', 'sceneSha256', 'quiescenceSha256'):
        require(pin(setup.get(key)), 'Missing setup pin: ' + key)
    require(setup.get('card') == [325, 530], 'Wrong actual card dimensions')
    require(finite(setup.get('dpr')) and setup['dpr'] > 0, 'Missing finite DPR')
    viewport = setup.get('viewport')
    require(isinstance(viewport, list) and len(viewport) == 2 and
            all(finite(v) and v > 0 for v in viewport), 'Missing viewport')
    sources = raw.get('sources', {})
    if not isinstance(sources, dict): sources = {}
    for key in ('originalNativeBefore', 'candidateNativeAfter', 'displayBefore', 'displayAfter'):
        require(pin(sources.get(key)), 'Missing exact source: ' + key)
    changed = raw.get('changedScopes')
    require(isinstance(changed, list) and bool(changed) and
            all(isinstance(name, str) and name for name in changed), 'Changed display scope omitted')
    required = ORIGINAL_SCOPES | (set(changed) if isinstance(changed, list) and
                                  all(isinstance(n, str) for n in changed) else set())
    scopes = raw.get('scopes', [])
    if not isinstance(scopes, list): scopes = []
    names = [s.get('name') for s in scopes if isinstance(s, dict)]
    require(len(names) == len(scopes) and all(isinstance(n, str) for n in names) and
            len(names) == len(set(n for n in names if isinstance(n, str))), 'Invalid/duplicate cost scopes')
    require(required.issubset(set(n for n in names if isinstance(n, str))), 'Original/changed cost scope missing')
    for scope in scopes:
        if not isinstance(scope, dict):
            continue
        name = scope.get('name')
        prefix = str(name) + ': '
        require(scope.get('status') == 'RAW_BATCHES_RETURNED' and not scope.get('error'),
                prefix + 'Acquisition/custody failure retained')
        require(scope.get('actualFunction') == name and pin(scope.get('adapterSha256')),
                prefix + 'Actual function/adapter association absent')
        warm = scope.get('warmMs', {})
        if not isinstance(warm, dict): warm = {}
        require(all(finite(warm.get(side)) and warm[side] >= 5000 for side in 'AB'),
                prefix + 'Actual 5-second warmup missing')
        slots = scope.get('slots', [])
        if not isinstance(slots, list): slots = []
        observed = [(s.get('block'), s.get('order'), s.get('side'))
                    for s in slots if isinstance(s, dict)]
        require(len(observed) == len(slots) and observed == SEQUENCE,
                prefix + 'Four exact ABBA blocks missing/reordered')
        values = {'A': [], 'B': []}
        common_state, side_states, previous_events = None, {}, {}
        events = {side: {key: 0 for key in EVENT_COUNTERS} for side in 'AB'}
        batch_results = []
        for slot in slots:
            if not isinstance(slot, dict): continue
            side = slot.get('side')
            if side not in ('A', 'B'):
                require(False, prefix + 'Invalid observed side')
                side = None
            samples = slot.get('durationsMs')
            valid_samples = (isinstance(samples, list) and bool(samples) and
                             all(finite(v) and v >= 0 for v in samples))
            require(valid_samples, prefix + 'Finite raw call durations missing')
            elapsed = slot.get('elapsedMs')
            require(finite(elapsed) and elapsed >= 5000, prefix + '5-second measured slot missing')
            if valid_samples and finite(elapsed):
                require(sum(samples) <= elapsed + 1e-6, prefix + 'Self times exceed elapsed slot')
            require(slot.get('exceptions') == [], prefix + 'Exception/missing exception inventory retained')
            states = [slot.get('startState'), slot.get('endState')]
            states_valid = all(isinstance(state, dict) and
                               all(isinstance(state.get(k), int) and not isinstance(state[k], bool) and
                                   state[k] >= 0 for k in COUNTERS) for state in states)
            require(states_valid, prefix + 'Actual finite state/counter inventory incomplete')
            if states_valid:
                states = [{k: state[k] for k in COUNTERS} for state in states]
                stable_keys = set(COUNTERS) - EVENT_COUNTERS
                require(all(states[0][k] == states[1][k] for k in stable_keys),
                        prefix + 'Live state/retained allocation growth')
                deltas = {k: states[1][k] - states[0][k] for k in EVENT_COUNTERS}
                require(all(v >= 0 for v in deltas.values()), prefix + 'Event counters went backwards')
                require(deltas['networkRequests'] == 0, prefix + 'Network during quiescent cost slot')
                require(deltas['renderRequests'] == 0, prefix + 'Worker request during quiescent cost slot')
                if side in previous_events:
                    require(all(states[0][k] >= previous_events[side][k] for k in EVENT_COUNTERS),
                            prefix + 'Event counters reset between slots')
                    require(all(states[0][k] == previous_events[side][k]
                                for k in ('networkRequests', 'renderRequests')),
                            prefix + 'Network or worker request between quiescent slots')
                previous_events[side] = states[1]
                if side in events:
                    for k, v in deltas.items(): events[side][k] += v
                require(states[0]['pendingJobs'] == 0 and states[0]['rafChains'] <= 1,
                        prefix + 'Nonquiescent jobs or duplicate rAF chains')
                require(states[0]['timerChains'] == 0 and states[0]['intervalChains'] == 0,
                        prefix + 'Timer or interval work escaped quiescence')
                # The original contract permits declared finite CPU arrays and
                # requires their actual start/end inventory. It does not impose
                # a new equal-memory-size gate on an approved L1 display delta.
                operational = {k: states[0][k] for k in COUNTERS
                               if k not in EVENT_COUNTERS | {'retainedArrays', 'retainedBytes'}}
                if common_state is None: common_state = operational
                require(operational == common_state, prefix + 'Unequal paired operational state')
                retained = {k: states[0][k] for k in stable_keys}
                if side not in side_states: side_states[side] = retained
                require(retained == side_states[side], prefix + 'Retained side state grew between slots')
            if valid_samples and side in values:
                values[side].extend(samples)
                batch_results.append({'block': slot.get('block'), 'order': slot.get('order'),
                                      'side': side, 'calls': len(samples),
                                      'medianMs': statistics.median(samples), 'p95Ms': percentile95(samples)})
        if all(values.values()):
            for key in ('readbacks', 'textureAllocations'):
                # Exact integer cross-products compare observed events/call;
                # no new tolerance or prohibition on inherited sites is added.
                require(events['B'][key] * len(values['A']) <= events['A'][key] * len(values['B']),
                        prefix + 'New per-call ' + key)
            before = {'medianMs': statistics.median(values['A']), 'p95Ms': percentile95(values['A'])}
            after = {'medianMs': statistics.median(values['B']), 'p95Ms': percentile95(values['B'])}
            limits = {k: v + max(.25, .1 * v) for k, v in before.items()}
            results.append({'name': name, 'before': before, 'after': after, 'limits': limits,
                            'calls': {k: len(v) for k, v in values.items()}, 'batches': batch_results,
                            'retainedStateBySide': side_states,
                            'observedEventTotals': events,
                            'passesBudget': all(after[k] <= limits[k] for k in limits)})
    status = ('INCOMPLETE' if gaps else 'PASS_COST_ONLY' if results and
              all(r['passesBudget'] for r in results) else 'FAIL_COST_BUDGET')
    return {'status': status, 'gaps': gaps, 'scopes': results,
            'rule': 'candidate <= baseline + max(0.25 ms, 10% baseline), median and nearest-rank p95',
            'nativeProvenanceIndependentlyVerified': False, 'visualAccepted': False,
            'startupAccepted': False, 'nodeCredit': 0, 'wholeIssueComplete': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, help='Raw actual-browser collector receipt')
    parser.add_argument('--decision', type=Path, help='Exact pre-run adopted budget bytes')
    parser.add_argument('--admission', type=Path, help='Exact ROOT resource admission bytes')
    parser.add_argument('--adapter-review', type=Path, help='Exact independent adapter review bytes')
    parser.add_argument('--prepare-host-owner', type=Path, help='ROOT-owned disposable native-host.mjs input; no build/browser')
    parser.add_argument('--expected-source-sha256', help='Exact original semantic-owner preimage')
    parser.add_argument('--output', type=Path, required=True, help='Fresh result file; never overwrite evidence')
    args = parser.parse_args()
    if args.prepare_host_owner is not None:
        if any((args.input, args.decision, args.admission, args.adapter_review)):
            parser.error('Host-fixture preparation and receipt assessment are separate operations')
        instrumented = prepare_host_owner(args.prepare_host_owner.read_bytes(), args.expected_source_sha256)
        with args.output.open('xb') as output:
            output.write(instrumented)
        print(json.dumps({'status': 'PREPARED_DISPOSABLE_HOST_OWNER_ONLY',
                          'productionSourceSha256': args.expected_source_sha256,
                          'fixtureSourceSha256': sha(instrumented), 'output': str(args.output.resolve()),
                          'browserExecuted': False, 'nodeCredit': 0}))
        return 0
    if not all((args.input, args.decision, args.admission, args.adapter_review)):
        parser.error('Receipt assessment requires input, decision, admission and adapter-review')
    raw_bytes, decision_bytes = args.input.read_bytes(), args.decision.read_bytes()
    raw, decision = json.loads(raw_bytes), json.loads(decision_bytes)
    result = assess(raw, decision, decision_sha256=sha(decision_bytes))
    for key, path in (('resourceAdmissionSha256', args.admission),
                      ('independentAdapterReviewSha256', args.adapter_review)):
        authority = raw.get('authority', {})
        if not isinstance(authority, dict) or authority.get(key) != sha(path.read_bytes()):
            result['gaps'].append('Physical authority bytes mismatch: ' + key)
            result['status'] = 'INCOMPLETE'
    result['rawReceipt'] = {'path': str(args.input.resolve()), 'sha256': sha(raw_bytes)}
    result['budgetDecision'] = {'path': str(args.decision.resolve()), 'sha256': sha(decision_bytes)}
    with args.output.open('x', encoding='utf-8') as output:
        json.dump(result, output, indent=2, allow_nan=False)
        output.write('\n')
    print(json.dumps({'status': result['status'], 'result': str(args.output.resolve()),
                      'gaps': len(result['gaps']), 'nodeCredit': 0}))
    return 0 if result['status'] == 'PASS_COST_ONLY' else 2


if __name__ == '__main__':
    raise SystemExit(main())
