# R0007 font-settlement Andon diagnosis

## Identity and authority

- Exact inspected candidate: `b20e3aa64f4cec47a8b025be1b77a9b9c0bb955b`.
- Inspected repository: `/workspace/scratch/8726e3e6def5/r0007-work`.
- Actual caller and decision owner: `/root`.
- Entry: explicit direct audit-Andon cord pull; bounded diagnosis only.
- Executing skill: `/home/agent/.codex/skills/remote-skills/skill-6a85962852508191a70c4b0eedbd1928/SKILL.md`, audit-andon version 0.4.0.
- Authority ceiling: read-only diagnosis and recommendations, plus this report artifact. No source, state, branch, browser, lifecycle, PASS, release, merge, or closure authority is claimed or exercised.
- This report preserves the completed diagnosis already returned to the caller. Its creation involved no additional investigation.

## Diagnosis and recommendation

Use an R0007-owned, early font-event observer with deferred receipts, bounded to the existing static authored stylesheet lifecycle. This removes the demonstrated assumption that `document.fonts.ready` implies completion of the product's set-wide event callbacks. A per-face receipt alone does not establish general quiescence across arbitrary font removal, replacement, insertion, or reload.

The caller supplied a pure counterexample in which readiness resolves while a set-wide terminal event remains queued, followed by the unchanged product callback dirtying the render state after the existing barrier. The caller also supplied contrary implementation evidence: inspected Blink and current Gecko coalesce or order notifications differently. Actual incidence in the targeted Windows Playwright 1.62 environment remains UNVERIFIED. This diagnosis does not claim a native browser bug or an observed native product failure.

## Established facts and inspected evidence

The following files were inspected at the exact candidate above:

- `tests/rlgwo/R0007-next-event-recipes.json`, specifically `NE07-recovery24`, `NE07-recovery12`, `NE07-dst-recovery24`, and `NE07-mut-remove-next-dirty`.
- `tools/cp9/r0007_browser.py`, including context creation, action execution, release, and trace export.
- `tests/rlgwo/prayer-browser-fixture.cjs`, including preload and observation hooks.
- `tests/r0007-recovery-precondition.test.cjs`.
- `src/native/index.html`, including the product font callbacks around lines 3200-3227 and a bounded search of font-related operations.

The four barriers await `document.fonts.ready` and then accept `document.fonts.status === 'loaded' && snapshot.dirty === false`. The product independently dirties through both `face.loaded.then(cnFontChanged, cnFontChanged)` and the `loadingdone`/`loadingerror` listeners.

The CSS Font Loading draft resolves the set's ready promise before queuing its completion-event task. Its terminal events distinguish successful and failed faces. This supports the supplied scheduling counterexample, not native incidence. The same specification shows that adding an already-loaded face need not initiate a loading cycle and that replacing a CSS font source creates a new face object. Primary documentation inspected: [CSS Font Loading Module Level 3](https://drafts.csswg.org/css-font-loading/), especially sections 2.3, 3, and 3.1; retrieved draft dated 22 October 2026. Browser tool references supplied to the caller were `turn2368030view0` and `turn9432809view0`.

The bounded source search found the authored Google Fonts stylesheet with its `media='all'` load handler and the three product font listeners. It found no direct `document.fonts.add/delete/clear` operation or font stylesheet reload operation. This supports a static-lifecycle scope; it is not a claim that every possible future document mutation was exhaustively ruled out.

The caller reported existing 19+5+9 controls passing. I did not independently rerun them, launch a browser, or verify the target native environment.

## Causal account

The defect is in the qualification setup's interpretation of readiness:

1. Font loading settles and the ready promise resolves.
2. The barrier observes a clear dirty flag.
3. The held prayer reply becomes eligible for release.
4. A previously queued font event calls the unchanged product callback and sets dirty.
5. That unrelated wakeup can affect what the recovery or removed-wakeup control demonstrates.

The inspected tests cover loading, layout-triggered loading, dirty work, and stylesheet terminality. The existing callback test invokes the product callback before resolving font readiness. It therefore does not distinguish the supplied ordering in which ready resolves while the terminal event remains queued.

### Local versus systemic disposition

This is a local qualification-mechanism weakness replicated across four R0007 recipes. The general lesson concerns completion promises versus later notification callbacks. Current evidence does not establish a project-wide defect or justify changing the shared fixture, product, browser scheduler, or another issue's ownership.

The countermeasure should leave product code, shared fixture code, expected prayer values, existing deadlines, and native scheduling behavior intact. The observer adds observation tasks; it must neither replace product timers/rAF nor invoke product rendering.

## Conditions for the proposed observer

### 1. Record actual events, then defer their acceptance

Install the observer before the document's fixture and product scripts. Capture the original native `setTimeout` at installation.

For an actual terminal event:

- Record a dispatch receipt immediately, including event type, face identities, face metadata, and monotonic time.
- Schedule one native zero-delay callback for that event.
- Only that callback records the deferred receipt and credits those faces.

The deferred task establishes that the observed event dispatch has returned. Its precise purpose is to avoid accepting the early observer's receipt before the later product listener has dirtied. A microtask receipt should not substitute for this task boundary.

Keep these observer timers separate from the fixture's product-timer ledger and export them explicitly.

### 2. Require receipts for the actual face and terminal type

Use object identity, not family names or descriptor strings. Prefer separate weak receipt sets or an equivalent typed identity record:

| Current relevant face state | Admission condition |
| --- | --- |
| `loading` | Reject |
| `loaded` | Deferred `loadingdone` receipt for that object |
| `error` | Deferred `loadingerror` receipt for that object |
| `unloaded` | Permitted under the existing actual-layout and ready conditions |

For mixed success and failure, one `loadingdone` receipt must not credit failed faces. This accommodates reversed or separated terminal-event delivery: admission waits for every relevant terminal face's own receipt. An empty later event cannot trigger this product callback because its relevance test uses `some`.

Maintain an explicit pending-deferred-receipt count. Require it to be zero at admission.

### 3. Evaluate the final condition after the final layout read

Retain the existing authored stylesheet load/error receipt and media-activation conditions. Retain the native layout read before awaiting readiness.

After the await, perform the final snapshot read, then inspect the current font set and observer receipts. Require:

- Current set status loaded.
- Every relevant current face admitted by the table above.
- No outstanding deferred observer receipt.
- Final snapshot dirty flag false.

This prevents a second layout read or newly visible face from being hidden behind an earlier observer assessment.

A genuine stylesheet error with no registered relevant faces can continue to admit settled fallback. It must not bypass checks on relevant faces that actually exist.

## Boundaries and failure handling

### Missing events

Reject or time out diagnostically. Do not infer a receipt from `status`, `ready`, elapsed time, or a family name.

### Loaded cache

An already-loaded object entering a set is a legitimate reason to examine liveness separately. The proposed strict rule may reject an otherwise stable environment. This is a conservative limitation, not evidence of a product failure. Obtain exact native evidence before introducing any no-event exception. Do not relax the condition to `status === 'loaded'` or use a timer-after-ready shortcut.

### Replacement

Object identity prevents an old face's receipt from admitting a new face. A replacement object with identical family, weight, and style must not inherit acceptance.

### Removal or reload

Current-set enumeration is insufficient for a universal claim. The product can retain a `face.loaded` callback for a loading face subsequently removed from the set. That callback can dirty later even though the barrier no longer enumerates the face.

The bounded source has no identified operation requiring this generality. Explicitly scope the observer to the static lifecycle; unexpected lifecycle changes should produce a diagnostic failure rather than implicit acceptance.

The observer establishes completion of the identified startup font notifications. It does not promise that arbitrary future DOM or font changes cannot dirty the product.

## Smaller alternatives

No smaller timing-only replacement was found that establishes the required property. One timer after `fonts.ready`, a fixed sleep, an extra animation frame, or repeated clean snapshots still infer completion without observing the event whose callback matters.

The early observer is proportionate if kept local to the R0007 driver and its four recipes. Avoid expanding it into a general font lifecycle framework.

## Focused evidence obligation

Before relying on a changed barrier, the caller should obtain:

1. **Decisive synthetic regression:** ready resolved and dirty false while the relevant terminal event remains queued; the barrier stays false until event dispatch, its deferred receipt, and subsequent natural dirty clearance.
2. **Ordering controls:** terminal event before ready; ready before terminal event; observer registered before the exact product listener; mixed success/error delivered in either order.
3. **Identity and fallback controls:** unused unloaded face; genuine stylesheet failure; unrelated face/event; missing receipt; replacement object with identical descriptors. Replacement must not inherit acceptance.
4. **Bounded native evidence:** the exact targeted Windows Playwright/browser configuration, with actual event dispatch and deferred receipts retained in raw success and failure traces. Show the release time relative to those receipts and the final clean snapshot.
5. **Existing discrimination:** retain existing controls and establish that the removed-next-dirty case fails for its intended missing wakeup, rather than merely because the new setup barrier timed out.

No arbitrary retries or broader browser archaeology are justified by this diagnosis.

## Escalation recommendation

Keep this within R0007-owned engineering and qualification. Do not escalate it as a native browser bug or product defect on current evidence.

If the exact native run exposes a legitimate loaded face without any terminal receipt, or exposes dynamic font lifecycle behavior outside the identified source path, return that specific trace to the owner for a bounded scope decision. Do not silently weaken the barrier.

The caller retains all implementation, qualification, integration, and closure decisions. This report grants no PASS, currentness, lifecycle transition, merge authority, or closure.
