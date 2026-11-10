            # R000B_F01_REQUIRED_ORDINARY_HEALTHY_REFRESH_V1
            # The original30-second watch above remains uninterrupted. Reuse its
            # actual full captures when they already bracket an owned refresh.
            refresh_before = healthy_refresh_record(recovered)
            if refresh_before is None:
                raise ValueError('Recovered capture lacks a bound current record/native receipt')
            refresh_progress = page.evaluate(HEALTHY_REFRESH_PROGRESS)
            if refresh_progress['maxElapsedMs'] != 240000:
                raise ValueError('Healthy refresh requires the unchanged240-second fixture budget')
            refresh_after_stage = 'recovered-30s'
            refresh_pair = healthy_refresh_pair(recovered, final, refresh_progress['ledger'])
            refresh_acquisition = row['healthyRefreshAcquisition'] = {
                'beforeStage': 'recovered', 'afterStage': refresh_after_stage,
                'reusedRecoveredWatchCaptures': refresh_pair['ok'], 'captureAttemptsAfterWatch': 0,
                'fixtureMaxElapsedMs': refresh_progress['maxElapsedMs'], 'captureDeadlineElapsedMs': 235000,
                'captureHeadroomMs': 5000, 'waitStartElapsedMs': refresh_progress['elapsedMs'],
                'lastPairSelection': refresh_pair,
                'scope': 'Actual ordinary post-model refresh only; no forced producer or capture-before-render ordering'}
            row['checks']['healthyRefreshAcquired'] = refresh_pair['ok']
            if not refresh_pair['ok']:
                print(json.dumps({'stage': 'await-ordinary-healthy-refresh', 'case': row['id'],
                                  'captureDeadlineElapsedMs': 235000}), flush=True)
            while not refresh_pair['ok']:
                remaining = refresh_acquisition['captureDeadlineElapsedMs'] - refresh_progress['elapsedMs']
                if remaining <= 0:
                    raise TimeoutError('No owned healthy full publication after prayer recovery within the remaining240-second fixture budget: ' + str(refresh_pair['reason']))
                latest = refresh_progress.get('latest') or {}
                candidate = latest.get('candidate') or {}
                # This reads only the existing passive record. If A remains the
                # active receipt while B is a candidate, a snapshot may retain A;
                # only an ordinary full publication of B can complete selection.
                if (candidate.get('eligible') is True
                        and _finite_number(candidate.get('sourceValidAt')) and _finite_number(candidate.get('retrievedAt'))
                        and candidate['sourceValidAt'] > refresh_before['sourceValidAt']
                        and candidate['retrievedAt'] > refresh_before['retrievedAt']):
                    refresh_acquisition['captureAttemptsAfterWatch'] += 1
                    refresh_after_stage = 'healthy-refresh-' + str(refresh_acquisition['captureAttemptsAfterWatch']).zfill(3)
                    final = capture(refresh_after_stage)
                    refresh_progress = page.evaluate(HEALTHY_REFRESH_PROGRESS)
                    refresh_pair = healthy_refresh_pair(recovered, final, refresh_progress['ledger'])
                    refresh_acquisition.update(afterStage=refresh_after_stage, lastPairSelection=refresh_pair)
                    row['checks']['healthyRefreshAcquired'] = refresh_pair['ok']
                    if refresh_pair['ok']:
                        break
                    remaining = refresh_acquisition['captureDeadlineElapsedMs'] - refresh_progress['elapsedMs']
                    if remaining <= 0:
                        continue
                page.wait_for_timeout(min(1000, remaining))
                refresh_progress = page.evaluate(HEALTHY_REFRESH_PROGRESS)
            refresh_acquisition['endElapsedMs'] = refresh_progress['elapsedMs']
            refresh_acquisition['observedRequest'] = refresh_pair['afterRequest']

