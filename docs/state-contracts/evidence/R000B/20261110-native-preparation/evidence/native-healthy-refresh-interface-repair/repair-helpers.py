def _healthy_refresh_target_projection(target):
    """Match the product receipt's generation/lat/lon identity projection."""
    if not isinstance(target, dict) or not all(_finite_number(target.get(key)) for key in ('generation', 'lat', 'lon')):
        return None
    return {key: target[key] for key in ('generation', 'lat', 'lon')}


def _healthy_refresh_clock(captured, origin):
    """Bind the observed fixture origins to an existing native motion sample."""
    if not isinstance(origin, dict):
        return None
    started, start_utc = origin.get('started'), origin.get('startUtc')
    motion = captured.get('actualCloud', {}).get('motion') or {}
    values = [started, start_utc, captured.get('elapsedMs'), captured.get('wallUtcMs'),
              motion.get('lastRt'), motion.get('elapsedRtMs')]
    if not all(_finite_number(value) for value in values):
        return None
    # Only an equality-of-origin floating-point allowance; this never extends an
    # attempt deadline. The epoch is checked against the already declared case.
    residual = motion['lastRt'] - motion['elapsedRtMs'] - started
    if not (started >= 0 and start_utc == INITIAL_SOURCE_UTC + 890000
            and 0 <= motion['elapsedRtMs'] <= captured['elapsedMs']
            and abs(residual) <= 1e-7
            and captured['wallUtcMs'] == math.floor(captured['wallUtcMs'])
            and captured['wallUtcMs'] >= start_utc + math.floor(captured['elapsedMs'])):
        return None
    return {'started': started, 'startUtc': start_utc, 'motionOriginResidualMs': residual}


def _healthy_refresh_request(record, captured, ledger, clock=None):
    """Bind a consumed response in its observed epoch and monotonic domains."""
    origin = _healthy_refresh_clock(captured, clock)
    if origin is None or not isinstance(record, dict) or _healthy_refresh_target_projection(record.get('target')) is None:
        return None
    started, start_utc = origin['started'], origin['startUtc']
    retrieved = record.get('retrievedAt')
    if not _finite_number(retrieved) or retrieved != math.floor(retrieved) or retrieved < start_utc:
        return None
    # Date.now() is startUtc+floor(performance.now()-started). Subtract the
    # integer epochs first, preserving the observed fractional monotonic origin.
    receipt_lower = started + (retrieved - start_utc)
    receipt_upper = receipt_lower + 1
    matches = []
    for request in ledger:
        if not isinstance(request, dict) or request.get('kind') != 'weather':
            continue
        owner, body = request.get('nativeOwner') or {}, request.get('inputBody') or {}
        current = body.get('current') or {}
        try:
            value = current.get('time')
            if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}', value):
                continue
            source = int(datetime.datetime.strptime(value, '%Y-%m-%dT%H:%M').replace(
                tzinfo=datetime.timezone(datetime.timedelta(hours=3))).timestamp() * 1000)
        except (ValueError, OverflowError):
            continue
        numbers = [request.get('elapsedMs'), request.get('wallUtcMs'), request.get('jsonElapsedMs'),
                   owner.get('deadlineAt'), request.get('weatherOrdinal')]
        if not all(_finite_number(value) for value in numbers):
            continue
        request_native = started + request['elapsedMs']
        json_native = started + request['jsonElapsedMs']
        deadline = owner['deadlineAt']
        json_wall_lower = start_utc + math.floor(request['jsonElapsedMs'])
        if (request.get('status') == 200 and request.get('jsonReads') == 1 and request.get('jsonSettled') is True
                and request.get('result') == 'json-consumed' and body.get('timezone') == 'Asia/Riyadh'
                and current.get('interval') == 900 and source == record['sourceValidAt']
                and owner.get('operationId') is not None and owner.get('attemptId') is not None
                and owner.get('generation') == record['target']['generation']
                and 0 <= request['elapsedMs'] <= request['jsonElapsedMs'] <= captured['elapsedMs']
                and start_utc + math.floor(request['elapsedMs']) <= request['wallUtcMs'] <= retrieved
                and json_wall_lower <= retrieved <= captured['wallUtcMs']
                # beginAttempt precedes this fixture request and the frozen
                # weather owner gives it a 10000 ms budget. Epoch-shaped or
                # unrelated deadlines cannot be silently accepted as monotonic.
                and request_native < deadline <= request_native + 10000 + 1e-7
                and json_native < deadline and receipt_upper < deadline):
            matches.append({'weatherOrdinal': request['weatherOrdinal'], 'elapsedMs': request['elapsedMs'],
                'wallUtcMs': request['wallUtcMs'], 'jsonElapsedMs': request['jsonElapsedMs'],
                'status': request['status'], 'jsonReads': request['jsonReads'], 'jsonSettled': request['jsonSettled'],
                'result': request['result'], 'inputSourceTime': current['time'], 'inputSourceUtc': source,
                'nativeOwner': owner, 'clockOrigin': origin,
                'timing': {'requestPerformanceMs': request_native, 'jsonPerformanceMs': json_native,
                    'retrievalPerformanceInterval': [receipt_lower, receipt_upper], 'intervalUpperExclusive': True,
                    'deadlinePerformanceMs': deadline, 'deadlineMarginFromReceiptUpperMs': deadline - receipt_upper,
                    'conservatism': 'The entire one-millisecond integer receipt interval must finish strictly before the native deadline; a valid receipt in the final millisecond can therefore be refused.'}})
    return matches[0] if len(matches) == 1 else None
