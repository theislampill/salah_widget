"""Bind the six affected R000B acquisitions; no pixel acceptance is inferred."""
from pathlib import Path
import hashlib,importlib.util,json

ROOT=Path(r'C:\Users\theis\.codex\worktrees\r000b-close\salah_widget')
E=Path(__file__).parent
spec=importlib.util.spec_from_file_location('r000b_receipts',ROOT/'tools/qa/verify_r000b_receipts.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
runtime=json.loads((E/'recovery-handoff-source/flash-counterexample/candidate.json').read_bytes())['runtime']
rows=[]
for browser in ['chromium','firefox']:
    driver=ROOT/'tools/qa/run_r000b_native.py' if browser=='chromium' else E/'handoff-capture-fixture/run_r000b_handoff_capture.py'
    for mode in ['default','reduced','full']:
        path=E/f'native-atomic-qualified/{browser}-{mode}/receipt.json'
        row=module.audit(path);assert row['status']=='PASS',row
        r=json.loads(path.read_bytes())
        assert r['runtime']==runtime and r['driverSha256']==sha(driver)
        assert r['wrapperSha256']==sha(ROOT/'tests/rlgwo/r000b-weather-fixture.html')
        final=r['observations'][-1]['state']
        assert final['motion']=={'reduced':mode!='default','full':mode=='full'}
        if browser=='firefox':
            for key,watch,seconds in [('recovery',r['recoveryPixels'],6),('motion',r['watches'][0],30)]:
                frames=watch['frames'];interval=watch['reviewInterval']
                assert len(frames)>=(48 if seconds==6 else 240)
                assert frames[-1]['beforeClock']['elapsedMs']>=interval['endFixtureElapsedMs']
                assert frames[-1]['startHostMonotonic']>=interval['endHostMonotonic']
                assert interval['endFixtureElapsedMs']-interval['startFixtureElapsedMs']==seconds*1000
                assert max(b['startHostMonotonic']-a['startHostMonotonic'] for a,b in zip(frames,frames[1:]))<=.25
                for frame in frames:
                    assert sha(path.parent/frame['file'])==frame['sha256']
                    assert frame['endHostMonotonic']-frame['startHostMonotonic']<=.25
                    assert abs((frame['afterClock']['wallUtcMs']-frame['beforeClock']['wallUtcMs'])-(frame['afterClock']['elapsedMs']-frame['beforeClock']['elapsedMs']))<10
                row[key]={'originalCount':len(frames),'reviewInterval':interval,'allOriginalHashesMatch':True}
            recovery=r['recoveryPixels'];retry=recovery['ordinaryRetry']
            first=recovery['frames'][0]['afterClock']['elapsedMs'];last=recovery['frames'][-1]['beforeClock']['elapsedMs']
            assert first<retry['requestElapsedMs']<=retry['jsonElapsedMs']<=retry['firstEligibleConsumer']['elapsedMs']<=last-2000
        rows.append(row)
out={'schema':'r000b-affected-native-reconciliation/v1','status':'SIX_AFFECTED_CASES_SOURCE_STATE_AND_CUSTODY_PASS',
    'cases':rows,'currentRuntimeSha256':runtime['treeSha256'],
    'reusedRadarSourceReceiptChecks':'post-handoff-currentness.json',
    'originalCompleteMatrix':'native-reconciliation.json',
    'limitations':['This supplements, and does not weaken or replace, the original complete-matrix verifier.',
        'The affected visual reruns omit the unchanged ten-minute radar retry; its exact source/fixture/driver reuse is separately bound.',
        'No state assertion, PNG hash or cadence measurement proves visual preservation or visible motion. Independent pixel review is required.']}
(E/'handoff-native-reconciliation.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print(out['status'])
