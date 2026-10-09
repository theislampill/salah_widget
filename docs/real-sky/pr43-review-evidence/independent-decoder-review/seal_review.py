"""Seal this independent decoder-only review; no source or shared ledger edits."""
import datetime
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUN = HERE.parents[2]
WORKER = RUN / 'workers/install/pr43-decode-cost'

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for data in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(data)
    return h.hexdigest()

def binding(path):
    return {'path': str(path), 'sha256': sha(path), 'bytes': path.stat().st_size}

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def write(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2, ensure_ascii=True) + '\n', encoding='utf-8')

def main():
    snapshots = read(HERE / 'SNAPSHOT_AUDIT.json')
    controls = read(HERE / 'BYTE_ERROR_CONTROLS.json')
    command = read(HERE / 'CONTROL_COMMAND.json')
    reuse = read(HERE / 'PRIOR_CONSUMER_REUSE_BINDING.json')
    assert snapshots['runtime04MatchesExpected'] and snapshots['moonBuildMetadataExactlyDerivedDecoderDelta']
    assert all(row['onlyExactDecoderDelta'] for row in snapshots['generatedEmbeddings'])
    assert controls['decoded']['byteIdentical'] and controls['allTestedErrorsExact'] and controls['negativeControls'] == 37
    assert command['exitCode'] == 0 and command['timingBenchmark'] is False
    assert reuse['candidate02RuntimeEqualsCandidate03'] and reuse['allProtectedNumericalOwnersUnchanged']
    original_attempt = HERE / 'attempt-01-HARNESS-IDENTITY-ASSUMPTION'
    failure = {'status': 'PRESERVED_REVIEW_HARNESS_API_ASSUMPTION_FAILURE',
               'cause': 'The first independent control expected a flat identity.parentReceiverSha256 property. Candidate03 already exposes nested identity.parent.initialReceiverSha256 and initialManifestSha256 through the unchanged builder/factory API.',
               'sourceReadback': 'tools/build_moon.py lines62-65 defines the nested parent; moon/src/moon-initial.mjs line35 returns the exact pin identity.',
               'repair': 'Bind the existing nested receiver and manifest SHA fields; retain the exact before/after identity equality assertion. No product/test source or gate was changed.',
               'files': [binding(original_attempt / name) for name in ['check_decoder.cjs', 'controls.stdout.log', 'controls.stderr.log', 'CONTROL_COMMAND.json']]}
    write('FAILURE_HISTORY.json', failure)
    nonproduct = []
    for name, description in [
        ('tests/r000c-weather.test.cjs', 'Fixture includes the actual native lunar wrapper helper next to the late native owner; avoids spanning generated head and native script elements. No weather assertion changed.'),
        ('tests/real-sky/native-celestial-startup.test.mjs', 'Extraction begins at nativeLunarPresentation so the already present wrapper dependency is included. No assertion changed.'),
        ('tests/real-sky/native-first-paint.test.mjs', 'Daytime admission fixture supplies the already required head Moon interface, real background-rule function and DPR; restores globals. It asserts actual --moongrp zero and explicitly scopes compose double to daytime admission. No Moon pixel claim.'),
        ('tools/cp9/pr43_entry_stream.py', 'Returns the existing report and makes process exit fail unless owned observations/current runtime/page errors/causal held-source and requested final consumer checks pass. Capture, cuts, bounds and browser behavior are unchanged; visual/S1 remain separately reviewed.'),
    ]:
        row = next(row for row in snapshots['changed'] if row['relativePath'] == name)
        nonproduct.append({**row, 'disposition': 'DECLARED_QA_ONLY_DELTA', 'description': description,
                           'diff': binding(HERE / (Path(name).name + '.diff.patch'))})
    write('NONPRODUCT_DELTA_REVIEW.json', {'scope': 'Bounded distinction of QA/evidence changes from production and numerical owners',
                                          'changes': nonproduct, 'addedEvidenceFiles': len(snapshots['added']),
                                          'allAddedFilesWithinDocsEvidence': all(row['relativePath'].startswith('docs/real-sky/pr43-review-evidence/') for row in snapshots['added']),
                                          'removedFiles': snapshots['removed'], 'assertionAndStartupThresholdRelaxationFound': False,
                                          'nativeOrS1Qualification': False})
    worker_report = read(WORKER / 'REPORT.json')
    current_worker = binding(WORKER / 'REPORT.json')
    assert current_worker['sha256'] == snapshots['workerReturn']['sha256']
    integrated = read(RUN / 'evidence/PR43-review/R1-decoder-integration-01/receipt.json')
    assert integrated['workerReportSha256'] == current_worker['sha256']
    assert integrated['workerControlsSha256'] == sha(WORKER / 'CONTROLS.json')
    assert integrated['beforeSha256'] == controls['retainedControlResult']['sourceHashes']['production']
    assert integrated['afterSha256'] == controls['retainedControlResult']['sourceHashes']['candidate']
    report = {
        'schema': 'pr43-decoder-independent-review/v1', 'status': 'PASS_BOUNDED_SOURCE_BYTE_ERROR_REVIEW_ONLY',
        'sealedAtUtc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'workerStateAfterReturn': 'IDLE_AVAILABLE',
        'scope': 'Candidate03 to candidate04 sole production decoder optimization; exact identity link to candidate02 reviewed numerical consumers. No broad consumer replay.',
        'writeScope': str(HERE), 'sourceEdited': False, 'ledgerEdited': False, 'githubEffects': [],
        'beforeCandidate': snapshots['beforeCandidate'], 'afterCandidate': snapshots['afterCandidate'],
        'runtimeBefore': snapshots['runtimeBefore']['treeSha256'], 'runtimeAfter': snapshots['runtimeAfter']['treeSha256'],
        'runtimeFileCount': len(snapshots['runtimeAfter']['files']),
        'runtimeIsInventoryHashNotFileSha': True,
        'indexBefore': snapshots['runtimeBefore']['files']['index.html'], 'indexAfter': snapshots['runtimeAfter']['files']['index.html'],
        'workerReturn': current_worker, 'workerControls': binding(WORKER / 'CONTROLS.json'),
        'integrationReceipt': snapshots['integrationReceipt'], 'buildReceipts': snapshots['buildBindings'],
        'workerReturnInputBindingsMatch': all(row['matchesReturn'] for row in snapshots['workerBindings']),
        'productChanges': ['moon/src/moon-initial-compact.mjs: 8-bit canonical Huffman prefix lookup and receiver scalar writes'],
        'derivedRuntimeChanges': ['index.html', 'offline.html', 'moon/moon-host.js', 'moon/BUILD.json'],
        'generatedDeltaProof': snapshots['generatedEmbeddings'],
        'moonBuildMetadataDelta': 'Only decoder source digest and derived host digest changed; payload/initial parent/kernel/worker/assets/profile/source consumer digests unchanged.',
        'protectedOwners': snapshots['protectedIntegrationOwners'], 'protectedClasses': snapshots['protectedClasses'],
        'nonproductChanges': binding(HERE / 'NONPRODUCT_DELTA_REVIEW.json'),
        'encoded': controls['encoded'], 'decoded': controls['decoded'],
        'bootstrapEncodingEqual': controls['encodingEqual'], 'decodedPinEqual': controls['decodedPinEqual'],
        'initialConsumerIdentityEqual': controls['initialConsumerIdentityEqual'],
        'initialConsumerIdentity': controls['initialConsumerIdentity'], 'digestCallsPreserved': controls['unchangedDigestCalls'],
        'errorControls': {'retained': 32, 'extraSmallHeader': 5, 'total': 37, 'allTestedClassAndMessageExact': True,
                          'command': command, 'results': binding(HERE / 'BYTE_ERROR_CONTROLS.json')},
        'algorithmReview': [
            'Each short canonical word of length1..8 fills its exact256-entry prefix interval. Packed length/symbol fits Uint16; positive length makes zero a safe unmatched sentinel.',
            'Peek runs only with eight bits available. At an aligned last byte, the unused missing next-byte term is coerced to zero without changing the first byte; unaligned eight-bit availability implies the next byte exists.',
            'Long/unmatched prefixes and final partial bytes use the unchanged bit loop, truncated/invalid word ordering, extra-byte and padding validation.',
            'Oversubscribed codebooks reject before any symbol decoding. Paeth prediction, modulo channel reconstruction, mask/count, scalar range checks, normalization/rounding, horizon reconstruction and both SHA checks remain unchanged.',
            'Scalar writes preserve the same component values, access order and arithmetic for internally created typed channels and admitted JSON ranges; receiver output bytes establish this on the complete actual payload.',
        ],
        'findings': [],
        'reuseBoundary': {'accepted': 'Preserved compact representation, decoded byte identity and unchanged numerical/phase/profile/initial consumer owners support reuse of already sealed numerical/source consumer evidence.',
                         'priorBinding': binding(HERE / 'PRIOR_CONSUMER_REUSE_BINDING.json'),
                         'candidate02RuntimeEqualsCandidate03': True,
                         'protectedNumericalOwnerCount': len(reuse['owners']), 'allUnchangedAcross02_03_04': True,
                         'notQualified': ['S1/first-scene wall time or scheduling', 'Chromium/Firefox pixel/opacity/coverage/continuous-phase controls', 'Ordinary/held-response new-entry behavior', 'Resource/performance budgets', 'Public delivery or issue closure'],
                         'driftRule': 'Reuse is valid only at these exact decoded and owner identities; changed metadata/config/numerical owner or decoded bytes reopens the affected proof.'},
        'preservedOwnFailure': binding(HERE / 'FAILURE_HISTORY.json'),
        'timingReview': {'workerBenchmark': binding(WORKER / 'BENCHMARK.json'),
                         'disposition': 'SEALED_CONTEXT_ONLY_NOT_REPLAYED_OR_INDEPENDENTLY_VALIDATED',
                         'claim': 'Node decode timings are not browser first-scene/S1 evidence; no benchmark or clock/CPU measurement was performed in this follow-up.'},
        'browserExecuted': 0, 'performanceBenchmarkExecuted': 0, 'buildExecuted': 0, 'terrainExecuted': 0,
        'nextAction': 'Root consumes this exact-source review while finishing already leased ordinary browser captures and independent unchanged-bound S1/visual/consumer disposition. No new integration change requested by this review.',
        'artifacts': [binding(HERE / name) for name in ['SNAPSHOT_AUDIT.json', 'RUNTIME_DELTA.json', 'DECODER_SOURCE_DIFF.patch', 'BYTE_ERROR_CONTROLS.json', 'CONTROL_COMMAND.json', 'PRIOR_CONSUMER_REUSE_BINDING.json', 'NONPRODUCT_DELTA_REVIEW.json', 'FAILURE_HISTORY.json']],
    }
    write('REVIEW.json', report)
    markdown = '''# PR43 decoder independent review

**PASS for bounded source/byte/error equivalence. No new product finding.** Candidate04 runtime inventory is `040192b555fa0db2fad760470ec020a06d86d3e0c7615153062ec5e76c50a2d5`,141 runtime files; its index file is `67e2ff84eb1e7422bfc390f98b641c8e3f93f76a77400401681be10676eb8d3d`. Candidate03 runtime is `d76eab2a27a00e23d786d40d2a2a7a6b57cc36e94921eda4344aa7ecba08b8ed`, index `90a8429c77fce50425b6e8effca7d7e7b6a210d25110394c72e2a074d0465b83`. Runtime inventory and file identities are distinct.

The only production owner change is `moon/src/moon-initial-compact.mjs`, from `65baddcf…` to `7281b9d4…`. Replacing exactly that new source with the old source makes candidate04 `index.html`, `offline.html` and `moon/moon-host.js` byte-identical to candidate03. Each has one occurrence; the exact byte increase is576. `moon/BUILD.json` differs only by decoder source and derived host digests. Actual141-file runtime readback equals both retained deterministic build manifests and the build receipt. No build was repeated.

The complete snapshot comparison finds nine changed files,222 added files and no removed files. The extra changes are three test fixture adaptations and `pr43_entry_stream.py` exit handling; all additions are in `docs/real-sky/pr43-review-evidence/`. Source native UI/clock/weather, numerical Moon, host lifecycle, head composition, kernel, worker, builder, scientific assets, renderer, config, presets, vendor and frozen V1 remain unchanged. The stream runner now rejects failed/currentness/error/held-causal/final-consumer captures through process exit; it does not relax a startup bound. Fixture changes bind the already existing native wrapper/head interfaces and do not qualify rendered Moon behavior. Exact nonproduct diffs are retained.

| Independent control | Result |
|---|---|
| Actual generated base64 payload and inline encoding | Byte-identical549,170 bytes, SHA256 `dc131b3858aa20ddc858ccf1058fdcba533ec70d98f5d3bb28d1afc77b307269` |
| Full decoded output and coverage header/mask | Byte-identical3,965,156 bytes, SHA256 `25755b217ec6da7401740b3d4df06d23c917e4bfc447d5667938b7b960a69331` |
| Generated decoded pin and actual initial consumer identity | Exact equality, nested parent receiver/manifest ancestry retained |
| Healthy digest checks | Two calls in both implementations, same reviewed digest source |
| Error controls | All32 retained negatives plus five short-header boundaries preserve exact class/message |
| Prior numerical owner reuse | Candidate02 retained runtime equals candidate03;17 protected source/asset owners equal across02/03/04 |

The eight-bit table covers exactly each canonical short-word prefix interval; positive packed lengths keep zero an unmatched sentinel. Long words, unmatched prefixes and fewer than eight remaining bits retain the original bit reader and rejection order. Eight available bits with nonzero alignment require the next byte; an aligned final-byte peek uses only that byte. Canonical bounds, Paeth, quantization/ranges, scalar rounding, oct-normal reconstruction, horizon fields and decoded admission are unchanged. Removing temporary arrays does not alter the scalar arithmetic. The controls use the actual frozen candidates and generated bootstrap; no numerical phase/render sweep was repeated.

One initial review control failed on candidate03 because it assumed a flat `identity.parentReceiverSha256` property. The unchanged builder actually writes `parent.initialReceiverSha256` and `parent.initialManifestSha256`, and the factory returns that pin. The failed script/command/raw stderr are preserved under `attempt-01-HARNESS-IDENTITY-ASSUMPTION`; the corrected assertion binds both existing nested fields. This was reviewer harness drift, not a decoder regression. `FAILURE_HISTORY.json` records the source readback and repair.

Already sealed numerical/source consumer evidence is reusable at the identical decoded bytes, pin and protected owner identities. Quantization approximations persist unchanged. Arbitrary hostile JavaScript getters/prototype behavior is outside these concrete binary/JSON controls. New Chromium/Firefox entry behavior, pixels, continuous-phase/currentness, first-scene timing and S1 remain separate root qualification. The worker's Node timing return is sealed context only; this review neither reruns nor independently validates a benchmark. No browser, performance, build, terrain, shared source, ledger or GitHub effect occurred. Root retains the active heavy lease; this worker is idle and available after sealing.
'''
    (HERE / 'REVIEW.md').write_text(markdown, encoding='utf-8')
    files = [{'relativePath': path.relative_to(HERE).as_posix(), 'sha256': sha(path), 'bytes': path.stat().st_size}
             for path in sorted(HERE.rglob('*')) if path.is_file() and path.name not in ('SEAL.json', 'ARTIFACTS.json')]
    write('ARTIFACTS.json', {'schema': 'bounded-independent-review-files/v1', 'scope': str(HERE), 'files': files})
    write('SEAL.json', {'schema': 'pr43-decoder-independent-review-seal/v1', 'status': report['status'],
                        'reviewJson': binding(HERE / 'REVIEW.json'), 'reviewMarkdown': binding(HERE / 'REVIEW.md'),
                        'manifest': binding(HERE / 'ARTIFACTS.json'), 'fileCount': len(files),
                        'runtime04': report['runtimeAfter'], 'workerState': 'IDLE_AVAILABLE',
                        'browserExecuted': 0, 'performanceBenchmarkExecuted': 0, 'buildExecuted': 0, 'terrainExecuted': 0})
    print(json.dumps(read(HERE / 'SEAL.json')))

if __name__ == '__main__':
    main()
