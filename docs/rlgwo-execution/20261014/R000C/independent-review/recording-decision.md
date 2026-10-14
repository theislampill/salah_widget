# R000C bounded independent recording decision

**Decision: test one missing, reference-supported combination: the already pinned single-document preparse fixture with headed Firefox and the existing video-only recorder. Keep the invalid-precip input, assertions, readiness predicate and declared watch unchanged. No pilot currently receives continuous-pixel acceptance.**

Reviewed 2026-10-14 against base `7827099dff3c9bc5ecb1b7a67dc4c25414bcfb69`, branch `codex/r000c-close-20261014`. Scope is read-only diagnosis and independent reports/offline original-media extraction only. No browser, GUI, desktop enumeration, network mutation, source edit, build, Git write or new agent was used. Existing dirty README/DESIGN and QA preparation were preserved. The coordinator has confirmed the same bounded next acquisition; this note grants no merge, publication or issue-closure authority.

## Authority and boundary

The immutable local `../authority/R000C-spec.md` is SHA256 `90eb91ecacb3ec744d47e11bf6f58f99146c48a6b96c7e2d8b3111d14251e783`; accepted assessment is `274d3fed218a4a8b4d1c0bfed7afdf9669107a515e90021e69383a124fd2145f`. A02/C15 requires real fetchWeather ingress, admitted/cache values and actual header/effect pixels for six cases. A03/C16 adds the half-Moon malformed-to-healthy night recovery, scoped layout/opacity and 30-second real-clock default/reduced/full motion. Lines 144–172 do not prescribe a startup-time SLA or require the first navigation frame to be a complete card. They do require original relevant pixels and unchanged visual predicates.

The current driver `tools/qa/run_r000c_native.py:48,188–217` waits for fixture/consumer/model/radar readiness and the expected particle state, then starts its declared watch immediately. This is a legitimate **state-readiness** boundary; it has not established native recorded-pixel readiness. Treating it as visual proof would be wrong. The available evidence does not establish that a product startup defect, the readiness condition itself, or document replacement causes the missing recorded regions. No delay should be chosen from the last bad frame to recut an already failed watch.

C15's bounded acquisition-state pixels and C16's continuous motion are different claims. A relevant original state crop may support the former without making an unreadable continuous interval pass. This diagnosis grants neither claim to these pilots. A later complete frame is retained as counterevidence, never substituted for a blank frame within a declared watch.

## Original evidence independently checked

All paths in this table are beneath `../native/`; the case is `R000C-invalid-precip` in each lane.

| Lane / document / mode | Original frames | Original evidence |
|---|---:|---|
| `firefox-day` / document.open-write-close / headless | 306, PTS 0–12.20 s | 58 low-information candidates. Independently viewed original whole-card blank frame 104 / 4.16 s and complete frame 105 / 4.20 s. Video SHA256 `184a4f54f54fc31681c6f36c4ad178e62d1f6b332d176bab7c84e9e1d863e0dd`. |
| `firefox-headed-pilot` / same document replacement / headed | 297, PTS 0–11.84 s | Every frame nominated as low-information. The inspected last frame 296 is blank across the widget, with a narrow outer black edge. Video SHA256 `0c3eaccdb5c52088c5a6944a6df42e4f06fbb5451c81a687dcaacb661e44483f`. |
| `firefox-single-pilot` / single-document preparse / headless | 305, PTS 0–12.16 s | 47 low-information candidates through frame 95 / 3.80 s. Independently viewed blank 95 and complete 96 / 3.84 s, 100 / 4.00 s and 304 / 12.16 s. Video SHA256 `561d2a046fa9d587ada4067841b0d53d6182168755c3e239eeadbde5a1598861`. |

`pilot-binding-check.json` and `verify_pilots.py` record the independent check: all nine current source pins match; regenerated single-document binding is identical; all 908 original decoded RGB frame hashes and PTS values match their indexes; original video/receipt hashes match. The derived PNGs beside this note are exact selected native-video extractions, with no repair or omission of failed originals. Candidate counts are search aids, not a visual acceptance oracle, and I do not claim manual inspection of every frame.

The initial consumer read occurs 1.188, 0.984 and 1.172 host seconds after navigation, respectively, and 989, 855 and 991 ms after fixture start. Video PTS and host monotonic times have different origins. These receipts do not provide a unique frame-to-watch-start join, so those numbers must not be subtracted as an exact association. Whole-recording inspection and the declared-watch limitation are retained.

## Exact successful reference and its limits

The delivered R0007 headed control is `docs/rlgwo-execution/20261014/R0007/headed-replacement/firefox/shared-preservation-no-preference/` in the repository. The actual retained bindings are:

- Product source SHA256 `7dd8067334c842025ea209d8cbdc20ce1ee31cd783a1f4da279072b1b310f0de`, identical to current R000C root source.
- Original prayer fixture SHA256 `f74f54f40f15eb7c6269d9f463eaac396e20a2301925a5c67c38a91b8de222ce`; observed HTML `27e4320ca4f9a51fbb7c61d7d0b5d1c9e4a5df23f7ef12a4c9cbfb6c737d116b`.
- Source candidate `87c3a19ff275197e1a49bebd7abc30ad2849137e`; original driver blob SHA256 `7dc5eb53ddb2fdb8499372129e7608adc0992c5ad38f083fa289fd60f05d1997`. The present prayer fixture/driver have later R0006 additions; they are not byte-identical to those original blobs. The bounded preparse, headed and video-only mechanisms were compared against the original candidate diff.
- Firefox `150.0.2`, `headless=false`, binary SHA256 `960a9a013187e337fc03b685ec8bed803791033620985e99fa66438b4fcd6c80`; retained native video SHA256 `caefdc4d00a221e856ceb81ab5526ef772fc61bf23a0398ea81931a6c2a63083`.
- A single server-generated document, preparse fixture, no live document replacement, video-only live acquisition, and one-second native presentation tail before close. R0007's actual readiness also required a completed current prayer render and loaded fonts. Its existing independent review accepts the headed original 30-second preservation watch and retains early loading frames and failed headless originals.

That reference uses 370×570, Honolulu/native Date and controlled broken clouds, whereas R000C requires 390×600, Riyadh and the specified acquisition/night inputs. It is evidence for a viable **recording configuration to test**, not transferable R000C weather, night or motion qualification. R0006 explicitly separates bounded first/recovered state images from continuous preservation and grants no fresh headless functional video continuous-readability credit; its accepted preservation reuses exact R0007 originals. Neither reference licenses tail rescue.

Current single-document R000C generation is already pinned: wrapper `917c651c95184eab56e72701a73a2338d3cf1e3131f38af40c4bcd77203de26f`, adapter `1ed4db83f1faaefc35029d9b555d7d7e0b429ccdc7cd8fae1436b090e641c592`, served HTML `d88743ad3f5ae7576d32deeeb78e5f7fd9d2e21e36c520a39761c6d34fbf9108`. The original ingress, private storage, controlled clock, native Response and observer spans regenerate unchanged, as do every product script body. This is a disclosed fixture adaptation, not a renderer repair.

## One bounded next action and stop

Run exactly one fresh `R000C-invalid-precip` pilot with `--single-document --headed`, preserving the pinned source/input/fixture/viewport/clock and all current assertions. Change no readiness or watch interval for this acquisition. The controlled change from the single-document pilot is the existing `headless=false` launch option; this completes the previously untested document-mode/headless combination. Retain the whole native video and raw receipts, then independently inspect original complete-frame transitions, all nominated defects and the declared watch. The coordinator's execution of this one case is separate from this review.

If its declared watch is readable, that is only a pilot acquisition result; it supplies no unexecuted six-case, malformed-to-healthy night, Moon-opacity or 30-second preference credit. Only then is running the unchanged remaining authorized matrix justified. If it remains unreadable, preserve it and stop further recording-mode changes. Do not add arbitrary settling delays, switch recorders, modify Firefox/SDK/product, retime the original watch or launch a general Firefox investigation on these facts.

Unknowns remain: the renderer/capturer/native-source cause; whether the combined mode will be readable; exact native frame association with state-ready/watch-start; first current Moon surface time; and performance of the required night/recovery/default/reduced/full contexts. No causal finding about FFmpeg, a compositor or document replacement is made.
