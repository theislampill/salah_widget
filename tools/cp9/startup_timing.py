"""Pure admission/clock join for byte-bound first-scene pixel observations.

No UTC conversion, product getter, guessed bridge, or eventual-ready fallback.
Actual navigation/clock, selected observer and frame-row/pixel byte associations
are checked here. Pixel decoding and native acquisition authority remain separate.
"""
import math
import re
import hashlib
import json
from pathlib import Path
from contextvars import ContextVar


class MissingTiming(ValueError):
    pass


class InvalidTiming(ValueError):
    pass


_REVIEW_SNAPSHOT = ContextVar('startup_review_snapshot', default=None)


class ReviewArtifactSnapshot:
    """One offline review's byte snapshot, with a mandatory final drift guard.

    No semantic validation is cached. Strict parsed values are reused read-only;
    their serialization is guarded too. The default readers remain uncached.
    Callers must publish their staged output only after this context exits.
    """
    def __init__(self):
        self._bytes = {}
        self._digests = {}
        self._parsed = {}
        self._parsed_digests = {}
        self._used = False
        self._token = None
        self.stats = {'diskReads': 0, 'jsonParses': 0, 'frameParses': 0}

    def __enter__(self):
        if self._used or _REVIEW_SNAPSHOT.get() is not None:
            raise RuntimeError('Require one fresh, nonnested review snapshot')
        self._used = True
        self._token = _REVIEW_SNAPSHOT.set(self)
        return self

    def _path(self, path):
        if self._token is None or _REVIEW_SNAPSHOT.get() is not self:
            raise RuntimeError('Review snapshot is inactive')
        return Path(path).absolute()

    def read_bytes(self, path):
        path = self._path(path)
        if path not in self._bytes:
            raw = path.read_bytes()
            self._bytes[path] = raw
            self._digests[path] = hashlib.sha256(raw).hexdigest()
            self.stats['diskReads'] += 1
        return self._bytes[path]

    def digest(self, path):
        return self._digests[self._path(path)]

    def parsed(self, reference, kind):
        return self._parsed.get((self._path(reference['file']), kind))

    def remember(self, reference, kind, value):
        key = (self._path(reference['file']), kind)
        self._parsed[key] = value
        self._parsed_digests[key] = self._value_digest(value)
        self.stats[kind + 'Parses'] += 1

    @staticmethod
    def _value_digest(value):
        serialized = json.dumps(value, separators=(',', ':'), allow_nan=False)
        return hashlib.sha256(serialized.encode('utf-8')).hexdigest()

    def verify(self):
        for path, expected in self._digests.items():
            try:
                actual = hashlib.sha256(path.read_bytes()).hexdigest()
            except OSError as exc:
                raise InvalidTiming('raw artifact unavailable after review: ' + str(path)) from exc
            if actual != expected:
                raise InvalidTiming('raw artifact changed during review: ' + str(path))
        for key, expected in self._parsed_digests.items():
            try:
                actual = self._value_digest(self._parsed[key])
            except (TypeError, ValueError) as exc:
                raise InvalidTiming('parsed snapshot changed during review') from exc
            if actual != expected:
                raise InvalidTiming('parsed snapshot changed during review')

    def __exit__(self, exc_type, exc, traceback):
        try:
            self.verify()
        finally:
            _REVIEW_SNAPSHOT.reset(self._token)
            self._token = None
        return False


def number(value, name, minimum=None):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise InvalidTiming('invalid ' + name)
    if minimum is not None and value < minimum:
        raise InvalidTiming('invalid ' + name)
    return value


def text(value, name):
    if not isinstance(value, str) or not value:
        raise InvalidTiming('invalid ' + name)
    return value


def artifact(value):
    if value is None:
        raise MissingTiming('missing raw artifact binding')
    if not isinstance(value, dict):
        raise InvalidTiming('invalid raw artifact binding')
    text(value.get('file'), 'artifact file')
    if not isinstance(value.get('sha256'), str) or not re.fullmatch('[0-9a-f]{64}', value['sha256']):
        raise InvalidTiming('invalid artifact SHA256')
    return value



def _unique_raw_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise InvalidTiming('duplicate raw timing field ' + key)
        result[key] = value
    return result


def _raw_artifact_bytes(reference, role):
    reference = artifact(reference)
    snapshot = _REVIEW_SNAPSHOT.get()
    try:
        raw = snapshot.read_bytes(reference['file']) if snapshot is not None else Path(reference['file']).read_bytes()
    except ValueError as exc:
        raise InvalidTiming('invalid raw ' + role + ' artifact path') from exc
    except OSError as exc:
        raise MissingTiming('unavailable raw ' + role + ' artifact: ' + str(exc)) from exc
    digest = snapshot.digest(reference['file']) if snapshot is not None else hashlib.sha256(raw).hexdigest()
    if digest != reference['sha256']:
        raise InvalidTiming('raw ' + role + ' artifact SHA256 mismatch')
    return raw


def _raw_json_artifact(reference, role):
    raw = _raw_artifact_bytes(reference, role)
    snapshot = _REVIEW_SNAPSHOT.get()
    if snapshot is not None:
        retained = snapshot.parsed(reference, 'json')
        if retained is not None:
            return retained
    try:
        def invalid_constant(value):
            raise InvalidTiming('nonfinite raw timing JSON ' + value)
        value = json.loads(raw, object_pairs_hook=_unique_raw_object, parse_constant=invalid_constant)
    except (ValueError, UnicodeError) as exc:
        if isinstance(exc, InvalidTiming):
            raise
        raise InvalidTiming('invalid raw ' + role + ' JSON') from exc
    if not isinstance(value, dict):
        raise InvalidTiming('invalid raw ' + role + ' object')
    if snapshot is not None:
        snapshot.remember(reference, 'json', value)
    return value


def _raw_fields(metadata, raw, fields, role):
    if not isinstance(metadata, dict) or not isinstance(raw, dict):
        raise InvalidTiming('invalid ' + role + ' field association')
    for field in fields:
        if field not in raw:
            raise MissingTiming('missing serialized ' + role + ' field ' + field)
        if field not in metadata or type(metadata[field]) is not type(raw[field]) or metadata[field] != raw[field]:
            raise InvalidTiming(role + ' raw field mismatch: ' + field)


def validate_clock_custody(comparison, require_navigation=False):
    """Read actual raw bytes and bind all carried clock math before conversion.

    This is association, not proof that a synthetic sample was native. Diagnostic
    UTC/timeOrigin values never become elapsed-time origins or timing endpoints.
    """
    if not isinstance(comparison, dict):
        raise InvalidTiming('invalid clock custody comparison')
    navigation = comparison.get('navigation')
    if navigation is None:
        if require_navigation:
            raise MissingTiming('original navigation request absent')
    elif not isinstance(navigation, dict):
        raise InvalidTiming('invalid original navigation request')
    else:
        raw_navigation = _raw_json_artifact(navigation.get('artifact'), 'navigation')
        _raw_fields(navigation, raw_navigation, ('kind', 'clockId', 'atMs'), 'navigation')
    bridges = comparison.get('bridges', [])
    if not isinstance(bridges, list):
        raise InvalidTiming('invalid raw clock bridge collection')
    fields = ('kind', 'sampleId', 'sourceClockId', 'sourceKind', 'targetClockId',
              'sourceAtMs', 'targetBeforeMs', 'targetAfterMs')
    pairs = []
    # Check all math-field contradictions first: incomplete serialized payloads
    # in one record cannot mask an observed substitution in another record.
    for bridge in bridges:
        if not isinstance(bridge, dict):
            raise InvalidTiming('invalid raw clock bridge')
        raw = _raw_json_artifact(bridge.get('artifact'), 'clock sample')
        _raw_fields(bridge, raw, fields, 'clock sample')
        pairs.append((bridge, raw))
    for bridge, raw in pairs:
        kind = bridge['sourceKind']
        if kind == 'window-performance':
            sample = raw.get('sample')
            if not isinstance(sample, dict) or not isinstance(sample.get('clock'), dict):
                raise MissingTiming('serialized browser clock sample absent')
            _raw_fields({'atMs': bridge['sourceAtMs']}, sample, ('atMs',), 'browser sample')
            clock = sample['clock']
        elif kind == 'node-hrtime':
            request, response = raw.get('request'), raw.get('response')
            if not isinstance(request, dict) or not isinstance(response, dict) or not isinstance(response.get('clock'), dict):
                raise MissingTiming('serialized driver clock request/response absent')
            expected_request = {'schema': 'salah-capture-clock-request/1', 'requestId': bridge['sampleId']}
            _raw_fields(expected_request, request, ('schema', 'requestId'), 'driver request')
            expected_response = {'schema': 'salah-capture-clock-response/1', 'requestId': bridge['sampleId'], 'atMs': bridge['sourceAtMs']}
            _raw_fields(expected_response, response, ('schema', 'requestId', 'atMs'), 'driver response')
            actual_request = _raw_json_artifact(raw.get('requestArtifact'), 'driver request')
            actual_response = _raw_json_artifact(raw.get('responseArtifact'), 'driver response')
            _raw_fields(request, actual_request, ('schema', 'requestId'), 'driver request artifact')
            _raw_fields(response, actual_response, ('schema', 'requestId', 'atMs'), 'driver response artifact')
            if actual_request != request or actual_response != response:
                raise InvalidTiming('serialized driver request/response differs from actual raw bytes')
            if raw.get('responseSha256') != raw['responseArtifact']['sha256']:
                raise InvalidTiming('raw driver response SHA256 association mismatch')
            clock = response['clock']
        else:
            raise InvalidTiming('unsupported raw clock sample source kind')
        _raw_fields({'id': bridge['sourceClockId'], 'kind': kind, 'unit': 'ms'},
                    clock, ('id', 'kind', 'unit'), 'sample clock')
    return {'status': 'BYTE_AND_FIELD_BOUND', 'navigationChecked': navigation is not None,
            'bridgeArtifactsChecked': len(pairs),
            'scope': 'Actual raw navigation/clock bytes and field association; native acquisition remains separately required'}



def _serialized_equal(carried, retained, role):
    # Canonical JSON compares every serialized field, including nested types.
    # It does not turn a bool into an equal numeric timestamp or generation.
    try:
        left = json.dumps(carried, sort_keys=True, separators=(',', ':'), allow_nan=False)
        right = json.dumps(retained, sort_keys=True, separators=(',', ':'), allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise InvalidTiming('invalid serialized ' + role) from exc
    if left != right:
        raise InvalidTiming(role + ' differs from retained capture record')


def validate_observer_custody(comparison):
    """Bind one retained capture record before using carried first/stage data."""
    raw = _raw_json_artifact(comparison.get('observerArtifact'), 'observer results')
    runs = raw.get('runs')
    if runs is None or runs == []:
        raise MissingTiming('retained observer capture records absent')
    if not isinstance(runs, list):
        raise InvalidTiming('invalid retained observer capture records')
    navigation = comparison.get('navigation')
    if not isinstance(navigation, dict):
        raise MissingTiming('original navigation selection absent')
    navigation_reference = artifact(navigation.get('artifact'))
    selected = []
    available = 0
    for index, run in enumerate(runs):
        if not isinstance(run, dict):
            raise InvalidTiming('invalid retained capture record')
        capture = run.get('captureTiming')
        if capture is None:
            continue
        if not isinstance(capture, dict):
            raise InvalidTiming('invalid retained capture timing')
        retained_navigation = capture.get('navigation')
        if retained_navigation is None:
            continue
        if not isinstance(retained_navigation, dict):
            raise InvalidTiming('invalid retained capture navigation')
        retained_reference = retained_navigation.get('artifact')
        if retained_reference is None:
            continue
        artifact(retained_reference)
        available += 1
        if retained_reference == navigation_reference:
            selected.append((index, run, capture))
    if not selected and not available:
        raise MissingTiming('retained navigation/capture selection provenance absent')
    if len(selected) != 1:
        raise InvalidTiming('observer capture record selection is absent or ambiguous')
    index, run, capture = selected[0]
    for field in ['captureClock', 'navigation', 'bridges']:
        if field not in capture:
            raise MissingTiming('retained capture ' + field + ' absent')
        _serialized_equal(comparison.get(field), capture[field], 'capture ' + field)
    retained_observer = capture.get('observer')
    if not isinstance(retained_observer, dict) or retained_observer.get('firstValidAdmission') is None:
        raise MissingTiming('retained first observer admission absent')
    required = ['schema', 'clock', 'firstValidAdmission', 'admissions', 'events', 'rejected', 'overflow']
    if any(field not in retained_observer for field in required):
        raise MissingTiming('retained serialized observer fields absent')
    _serialized_equal(comparison.get('observer'), retained_observer, 'observer')
    return run, {'status': 'BYTE_AND_FIELD_BOUND', 'runIndex': index, 'mode': run.get('mode'),
                 'artifact': comparison['observerArtifact'],
                 'scope': 'Selected retained navigation/capture record and complete serialized observer; native acquisition remains separate'}


def _raw_frame_records(reference):
    raw = _raw_artifact_bytes(reference, 'native frame receipts')
    snapshot = _REVIEW_SNAPSHOT.get()
    if snapshot is not None:
        retained = snapshot.parsed(reference, 'frame')
        if retained is not None:
            return retained
    rows = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        try:
            def invalid_constant(value):
                raise InvalidTiming('nonfinite raw frame JSON ' + value)
            row = json.loads(line, object_pairs_hook=_unique_raw_object, parse_constant=invalid_constant)
        except (ValueError, UnicodeError) as exc:
            if isinstance(exc, InvalidTiming):
                raise
            raise InvalidTiming('invalid raw frame receipt JSON') from exc
        if not isinstance(row, dict):
            raise InvalidTiming('invalid raw frame receipt object')
        rows.append(row)
    if not rows:
        raise MissingTiming('raw frame receipt rows absent')
    if snapshot is not None:
        snapshot.remember(reference, 'frame', rows)
    return rows


def _retained_frame_path(value):
    try:
        return Path(value).resolve()
    except (OSError, ValueError) as exc:
        raise InvalidTiming('invalid retained frame artifact path') from exc


def validate_frame_custody(source, presented, capture_record):
    """Bind carried callback endpoints to one actual retained row and pixels."""
    reference = artifact(source.get('receiptArtifact'))
    rows = _raw_frame_records(reference)
    video = capture_record.get('video')
    if video is None:
        raise MissingTiming('retained capture video identity absent')
    text(video, 'retained capture video identity')
    if _retained_frame_path(reference['file']) != _retained_frame_path(str(video) + '.frames.jsonl'):
        raise InvalidTiming('frame receipt artifact belongs to another capture video')
    if not any(row.get('sourceEventId') is not None for row in rows):
        raise MissingTiming('retained native source event identity absent')
    matched = [row for row in rows if row.get('sourceEventId') == source.get('eventId')]
    if len(matched) != 1:
        raise InvalidTiming('native source frame selection is absent or ambiguous')
    row = matched[0]
    expected = {'sourceEventId': source['eventId'], 'presentedReceiptEventId': presented['eventId'],
                'receiptMonotonicMs': source['atMs'], 'sourceTimeSeconds': source['rawProtocolTimeSeconds']}
    _raw_fields(expected, row, tuple(expected), 'native frame receipt')
    clock = row.get('receiptClock')
    if not isinstance(clock, dict):
        raise MissingTiming('retained frame receipt clock absent')
    _raw_fields({'id': source['clockId'], 'kind': 'node-hrtime', 'unit': 'ms'},
                clock, ('id', 'kind', 'unit'), 'native frame clock')
    name = row.get('file')
    if name is None:
        raise MissingTiming('retained native source pixel file absent')
    if not isinstance(name, str) or not re.fullmatch('[0-9]{6}\.jpeg', name):
        raise InvalidTiming('invalid retained native source frame name')
    pixel_reference = artifact(source.get('artifact'))
    pixels = _raw_artifact_bytes(pixel_reference, 'native source pixels')
    expected_pixel = Path(str(video) + '.frames') / name
    if _retained_frame_path(pixel_reference['file']) != _retained_frame_path(expected_pixel):
        raise InvalidTiming('pixel artifact differs from selected raw frame path')
    if 'bytes' not in row:
        raise MissingTiming('retained native source byte count absent')
    if type(row.get('bytes')) is not int or row['bytes'] != len(pixels):
        raise InvalidTiming('selected native frame byte count mismatch')
    return {'status': 'BYTE_AND_FIELD_BOUND', 'sourceEventId': source['eventId'],
            'receiptArtifact': reference, 'pixelArtifact': pixel_reference,
            'scope': 'Actual retained callback row and pixel bytes; decoding/render/native authority remains separate'}


def binding(value):
    if not isinstance(value, dict):
        raise InvalidTiming('invalid scene/config binding')
    text(value.get('sceneIdentity'), 'scene identity')
    text(value.get('configIdentity'), 'config identity')
    generation = value.get('generation')
    if isinstance(generation, bool) or not isinstance(generation, int) or not 0 <= generation <= 9007199254740991:
        raise InvalidTiming('invalid generation')
    if number(value.get('dpr'), 'DPR', 0) == 0:
        raise InvalidTiming('invalid DPR')
    if set(value) != {'sceneIdentity', 'configIdentity', 'generation', 'dpr'}:
        raise InvalidTiming('unrecognized scene/config binding')
    return value


def clock_bounds(event, comparison, source_kind):
    """Return conservative bounds in the capture monotonic clock."""
    validate_clock_custody(comparison)
    validate_observer_custody(comparison)
    if not isinstance(event, dict):
        raise MissingTiming('missing timed event')
    clock_id = text(event.get('clockId'), 'event clock ID')
    at = number(event.get('atMs'), 'event timestamp', 0)
    target = comparison['captureClock']['id']
    if clock_id == target:
        if source_kind != 'python-monotonic':
            raise InvalidTiming('source clock mislabeled as capture domain')
        return [at, at]
    samples = [b for b in comparison.get('bridges', []) if b.get('sourceClockId') == clock_id]
    if not samples:
        raise MissingTiming('missing monotonic bridge for ' + clock_id)
    offsets = []
    for sample in samples:
        if sample.get('kind') != 'bracketed-clock-sample' or sample.get('targetClockId') != target or sample.get('sourceKind') != source_kind:
            raise InvalidTiming('wrong clock bridge identity/kind')
        artifact(sample.get('artifact'))
        text(sample.get('sampleId'), 'clock sample ID')
        source = number(sample.get('sourceAtMs'), 'clock sample source', 0)
        before = number(sample.get('targetBeforeMs'), 'clock bracket before', 0)
        after = number(sample.get('targetAfterMs'), 'clock bracket after', 0)
        if after < before:
            raise InvalidTiming('reversed clock bracket')
        offsets.append([before - source, after - source])
    lower, upper = max(x[0] for x in offsets), min(x[1] for x in offsets)
    if lower > upper:
        raise InvalidTiming('inconsistent monotonic clock brackets')
    return [at + lower, at + upper]


def _normalize(comparison, components):
    if comparison is None:
        raise MissingTiming('first-admission timing contract absent; legacy endpoint is diagnostic only')
    if not isinstance(comparison, dict) or comparison.get('schema') != 'salah-startup-comparison/1':
        raise InvalidTiming('invalid first-admission timing contract')
    capture = comparison.get('captureClock')
    if not isinstance(capture, dict) or capture.get('kind') != 'python-monotonic' or capture.get('unit') != 'ms':
        raise InvalidTiming('invalid capture monotonic domain')
    if not text(capture.get('id'), 'capture clock ID').startswith('capture:'):
        raise InvalidTiming('wrong capture clock namespace')
    navigation = comparison.get('navigation')
    if not isinstance(navigation, dict):
        raise MissingTiming('original navigation request absent')
    if navigation.get('kind') != 'navigation-request' or navigation.get('clockId') != capture['id']:
        raise InvalidTiming('navigation domain/origin mismatch')
    nav = number(navigation.get('atMs'), 'original navigation timestamp', 0)
    artifact(navigation.get('artifact'))
    custody = validate_clock_custody(comparison, require_navigation=True)
    observer = comparison.get('observer')
    if not isinstance(observer, dict) or observer.get('firstValidAdmission') is None:
        raise MissingTiming('first valid shared-scene admission absent')
    if observer.get('schema') != 'salah-startup-timing/1':
        raise InvalidTiming('invalid observer schema')
    artifact(comparison.get('observerArtifact'))
    capture_record, observer_custody = validate_observer_custody(comparison)
    if observer.get('overflow') is not False:
        raise MissingTiming('observer history incomplete/overflowed')
    if observer.get('rejected'):
        raise InvalidTiming('observer rejected an admission/stage')
    doc_clock = observer.get('clock')
    if not isinstance(doc_clock, dict) or doc_clock.get('kind') != 'window-performance' or doc_clock.get('unit') != 'ms':
        raise InvalidTiming('invalid document monotonic domain')
    doc = text(doc_clock.get('documentId'), 'document ID')
    if doc_clock.get('id') != 'document:' + doc:
        raise InvalidTiming('document/clock mismatch')
    number(doc_clock.get('timeOriginMs'), 'diagnostic performance time origin', 0)
    admissions = observer.get('admissions')
    if not isinstance(admissions, list) or not admissions:
        raise MissingTiming('ordered admissions absent')
    first = observer['firstValidAdmission']
    if first != admissions[0]:
        raise InvalidTiming('first admission replaced by a later event')
    known, keys, last = {}, set(), -1
    for row in admissions:
        if not isinstance(row, dict) or row.get('kind') != 'valid-shared-scene-admission' or row.get('source') not in ['head', 'native']:
            raise InvalidTiming('invalid admission event')
        identity = binding(row.get('binding'))
        admission_id = text(row.get('admissionId'), 'admission ID')
        if row.get('eventId') != admission_id or row.get('clockId') != doc_clock['id'] or row.get('documentId') != doc:
            raise InvalidTiming('admission document/event mismatch')
        at = number(row.get('atMs'), 'admission time', 0)
        number(row.get('utcMs'), 'diagnostic astronomical UTC')
        identity_key = tuple(identity[k] for k in ['sceneIdentity', 'configIdentity', 'generation', 'dpr'])
        if admission_id in known or identity_key in keys or at < last:
            raise InvalidTiming('duplicate/unordered admission')
        known[admission_id] = row; keys.add(identity_key); last = at
    marker_tokens = [row.get('markerToken') for row in admissions]
    if any(not isinstance(x, str) or not re.fullmatch('[0-9a-f]{32}', x) for x in marker_tokens) or len(set(marker_tokens)) != len(marker_tokens):
        raise InvalidTiming('missing/ambiguous pixel admission marker')
    stages = observer.get('events')
    if not isinstance(stages, list):
        raise MissingTiming('stage history absent')
    head_start, head_end, native = [], [], []
    seen, last = set(), -1
    for row in stages:
        if not isinstance(row, dict) or row.get('kind') not in ['head-work-start', 'head-work-end', 'native-adoption']:
            raise InvalidTiming('invalid stage event')
        admission = known.get(row.get('admissionId'))
        if admission is None or binding(row.get('binding')) != admission['binding']:
            raise InvalidTiming('stage scene/config mismatch')
        if row.get('clockId') != doc_clock['id'] or row.get('documentId') != doc:
            raise InvalidTiming('stage document/clock mismatch')
        event_id = text(row.get('eventId'), 'stage event ID')
        at = number(row.get('atMs'), 'stage time', 0)
        number(row.get('utcMs'), 'diagnostic astronomical UTC')
        if event_id in seen or at < last or at < admission['atMs']:
            raise InvalidTiming('duplicate/unordered stage')
        seen.add(event_id); last = at
        if row['kind'].startswith('head-') and row.get('source') != 'head':
            raise InvalidTiming('head stage source mismatch')
        if row['kind'] == 'native-adoption':
            if row.get('source') != 'native':
                raise InvalidTiming('native stage source mismatch')
            native.append(row)
        if row['admissionId'] == first['admissionId']:
            if row['kind'] == 'head-work-start': head_start.append(row)
            if row['kind'] == 'head-work-end': head_end.append(row)
    if not head_start or not head_end or not native:
        raise MissingTiming('head start/end or native adoption absent')
    if len(head_start) != 1 or len(head_end) != 1 or head_start[0]['atMs'] > head_end[0]['atMs']:
        raise InvalidTiming('ambiguous/reversed first head work')
    if first.get('source') != 'head' or head_end[0].get('status') != 'published':
        raise InvalidTiming('first admitted head scene was not published')
    first_bounds = clock_bounds(first, comparison, 'window-performance')
    first_bounds = [x - nav for x in first_bounds]
    if first_bounds[1] < 0:
        raise InvalidTiming('admission predates original navigation')
    observations = comparison.get('observations')
    if not isinstance(observations, dict):
        raise MissingTiming('byte-bound source/presented observations absent')
    result = {}
    frame_custody = {}
    for component in components:
        observation = observations.get(component)
        if not isinstance(observation, dict):
            raise MissingTiming('missing ' + component + ' pixel observation')
        if (observation.get('admissionId') != first['admissionId'] or
            observation.get('documentId') != doc or observation.get('markerToken') != first['markerToken'] or
            binding(observation.get('binding')) != first['binding']):
            raise InvalidTiming(component + ' pixel scene/config/document mismatch')
        source, presented = observation.get('sourceReceipt'), observation.get('presentedReceipt')
        if not isinstance(source, dict) or not isinstance(presented, dict):
            raise MissingTiming(component + ' source/presented receipts absent')
        if source.get('kind') != 'native-source-receipt' or presented.get('kind') != 'presented-pixels-receipt-upper-bound':
            raise InvalidTiming('source receipt and presentation event roles conflated')
        source_id = text(source.get('eventId'), 'source event ID')
        if text(presented.get('eventId'), 'presented receipt ID') == source_id:
            raise InvalidTiming('source/presented receipt roles share an event ID')
        if presented.get('sourceEventId') != source_id:
            raise InvalidTiming('presented receipt has wrong source frame')
        source_artifact = artifact(source.get('artifact'))
        if artifact(presented.get('artifact')) != source_artifact:
            raise InvalidTiming('source/presented pixel byte binding mismatch')
        if artifact(source.get('receiptArtifact')) != artifact(presented.get('receiptArtifact')):
            raise InvalidTiming('source/presented raw receipt byte binding mismatch')
        frame_custody[component] = validate_frame_custody(source, presented, capture_record)
        raw_time = source.get('rawProtocolTimeSeconds')
        number(raw_time, 'raw protocol source timestamp')
        # Both receipt roles describe this callback, never an inferred display time.
        if source.get('clockId') != presented.get('clockId') or source.get('atMs') != presented.get('atMs'):
            raise InvalidTiming('native receipt upper bound changed to another endpoint')
        text(source.get('clockId'), 'native source receipt clock ID')
        bounds = clock_bounds(presented, comparison, 'node-hrtime')
        if bounds[1] < nav or bounds[1] < clock_bounds(head_end[0], comparison, 'window-performance')[0]:
            raise InvalidTiming('published pixels receipt predates head publication/navigation')
        result[component] = [x - nav for x in bounds]
    stage_bounds = {row['eventId']: {'kind': row['kind'], 'admissionId': row['admissionId'],
        'binding': row['binding'], 'boundsMs': [x-nav for x in clock_bounds(row, comparison, 'window-performance')]}
        for row in stages}
    return {'status': 'BOUND', 'firstAdmissionId': first['admissionId'],
        'firstAdmissionBoundsMs': first_bounds, 'binding': first['binding'],
        'componentBoundsMs': result, 'stages': stage_bounds, 'captureClock': capture,
        'clockCustody': custody,
        'observerCustody': observer_custody, 'frameCustody': frame_custody,
        'scope': 'native source pixel receipt upper bounds, not physical-display timestamps'}


def normalize_startup_timing(comparison, components):
    try:
        return _normalize(comparison, components)
    except MissingTiming as exc:
        return {'status': 'UNKNOWN', 'failures': [str(exc)]}
    except (InvalidTiming, KeyError, TypeError, AttributeError) as exc:
        return {'status': 'INVALID', 'failures': [str(exc)]}


def interval_check(bounds, lower=None, upper=None):
    """No tolerance or budget inflation: straddling a boundary is UNKNOWN."""
    lo, hi = bounds
    if (lower is None or lo >= lower) and (upper is None or hi <= upper):
        return True
    if (lower is not None and hi < lower) or (upper is not None and lo > upper):
        return False
    return None
