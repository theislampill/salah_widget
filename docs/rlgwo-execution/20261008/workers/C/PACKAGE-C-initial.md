# C independent review of primary planning package — initial

**CHANGES_REQUIRED:** three concrete graph/execution corrections. Original111 residual parents and all exact texts are preserved; no product/browser/merge/closure proof is claimed.

Reviewed graph `a98f85267f6a609823df94c765333fe28c53128382c6bba70430f72adc1cd22b`,202 nodes/441 typed edges. Exact primary tool/doc hashes are in [the JSON report](PACKAGE-C.json). The reviewed byte snapshot is `workers/C/package-review-initial`.

## C-PACKAGE-01 — unbound duplicate authority/delivery interface

tools/assemble_execution_dag.py release_stages and produced-interface join; CLOSURE_DAG.json CLOSE-R000B/CLOSE-R000C/CLOSE-R000D/CLOSE-R0024 inputs

Authored uppercase Rxxxx-exact-head-authority/v1 and Rxxxx-required-delivery/v1 remain GATED producerless externals while generated stages emit lowercase rxxxx-exact-head-authority/v1 and rxxxx-delivery/v1 at different artifacts. Completion of actual authority/delivery cannot satisfy the literal extra receipt input without an explicit adapter/reconciliation.

CLOSE-R000B receives r000b-delivery/v1 from R000B-DELIVER yet still waits for producerless R000B-required-delivery/v1. The source graph structurally passes because explicit unavailable externals are allowed.

Smallest correction: Normalize the authored IDs to actual producers or add exact receipt adapters with explicit interfaceAliases preserving consumer meaning and producer artifact path. Preserve source/spec receipt names as provenance; do not silently waive delivery.

## C-PACKAGE-02 — missing heavy resource reservation

tools/assemble_execution_dag.py generic runtime-merge DELIVER; CLOSURE_DAG.json R0024-DELIVER resources/estimate

R0024-DELIVER requires actual affected public runtime consumer readback but reserves integrator/github-writer only and0 exclusive minutes. It can overlap the already capacity1 browser/performance queue, violating the declared one-heavy-job boundary and undercounting its resource demand.

R0024 native delivered information check can run while another heavy node owns the browser lease if only listed resources are reserved. #24 uses its existing heavy-browser delivery and is already covered; it is not an affected example.

Smallest correction: For generic runtime-merge delivery with actual browser consumer proof, reserve heavy-browser and a qualified bounded planning range; preserve existing issue-specific ranges and acceptance thresholds.

## C-PACKAGE-03 — false documentation release dependency

tools/assemble_execution_dag.py release_stages review_inputs uses closure.requiredOutputs; R0013-RELEASE-REVIEW/R0013-DELIVER and R0010-RELEASE-REVIEW

Docs-merge approval/delivery waits for every issue native/qualification output. Independent accurate documentation cannot deliver while unrelated native proof/platform acquisition waits, despite an accepted source/fact interface and separate original documentation row. This contradicts the planned fastest ready-groups schedule.

R0013-DOCS requires SATISFIED bash-input-cache-config/v1 and produces reviewed terminal/review/manual/cache/newline facts for19-09. R0013-RELEASE-REVIEW nevertheless requires Apple detector/launch output and QUALIFY, and DELIVER also directly requires QUALIFY. Native detector row19-05 is a closure gate, not a dependency of the correct README delta. R0010-O09 likewise is independent of missing O12 native boot proof.

Smallest correction: Permit an independently reviewed docs-only candidate to obtain exact-head owner approval and docs delivery from its actual documentation/fact dependencies while full issue native/evidence qualification remains on CLOSE. Coalesce compatible ready docs/approval receipts without requiring all documentation batches or all issue closures. If a particular documentation fact needs new native proof, retain that exact interface gate.

Known provisional F/E review inputs and the definite startup handoff are acknowledged gates, not undiscovered findings. Model-current precipitation, accepted closures and N001/N002/N003 scope remain preserved. No new research programme, platform substitution or broad product test is requested.

Priority/cost/source/reuse/authority rules are otherwise coherent. Final shared-file writes remain owned by one source/generated integrator and one docs writer; native/platform/effect input acquisition is explicit. Preserve the initial failures and focused-review corrected graph/tool hashes before PASS.
