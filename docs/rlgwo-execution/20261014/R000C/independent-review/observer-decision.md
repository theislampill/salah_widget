# R000C independent night evidence and bounded observer decision

The original Firefox recovered watches fail. One observer-only default-night pilot is justified; no product defect or capture cause has been established.

## Original evidence

`firefox-night-readback-check.json` independently reconciles the three canonical night inputs, unchanged source/runtime/browser identities, actual request/native JSON consumption, raw admission/cache/header/effect assertions, two ordinary ingress requests, native 1× wall progression and both declared host watch lengths. All semantic assertions pass. All 9,552 original decoded RGB frame digests and PTS match their original indexes. This is not a pixel PASS.

| Case beneath `../native/firefox-night/` | Video SHA256 | Frames / final PTS | Independently viewed failure |
|---|---|---:|---|
| `R000C-night-default` | `c2535d95f8ca670c003e7384288aa72992fbf62b117f05932c4521409fb94e19` | 3,187 / 127.44 s | Original 2776 / 111.04 s loses the footer and lower card to a white region. |
| `R000C-night-full` | `41e3b63823206f7ee964ad333ab0430d64f9f56fa4bf7de559897860a15e0144` | 3,199 / 127.92 s | Original 2485 / 99.40 s is whole-card blank. |
| `R000C-night-reduced` | `e85d382ed00f040eee5d4915cd008f91f4dc4844354606f1ca40545db2ffa87c` | 3,166 / 126.60 s | Original 2997 / 119.88 s is whole-card blank. |

Exact independently extracted failure PNGs are `firefox-night/<case>/defect-<ordinal>.png` beside this note. These late failures occur in the recovered-watch portion and cannot be repaired by subsequent readable originals. No full recovered interval qualifies. The videos also retain all startup and intervening defects. Default/reduced have candidates during the initial watch. Full-motion has candidates through 0.36 s and then at 60.68, 64.20 and 99.40 s; those timestamps alone do not establish an initial-watch defect. That initial sub-interval remains unqualified here, rather than being labelled failed solely because other parts of its recording fail. The original full acquisition is rejected for continuous recovery evidence.

## Concrete observer concern

The current weather bridge calls `qaState()` for every read. The current driver uses full reads at readiness, every five seconds during each watch, and roughly every 200 ms while awaiting recovery. Reads also append a copied full snapshot to the fixture log, which is later returned with each capture.

The source establishes that this is not a passive observation surface:

- `index.html:5180–5186` reads cloud-canvas pixels with `getImageData` and recomputes `atmosphere(model())`.
- `index.html:5247–5255` invokes lunar `surface()` and `state` accessors. Their implementation may adopt a pending preview; `_lastMoonPaint` is separately a consumed-state summary.
- `index.html:3753–3780` shows that `weatherDecision()` maintains `_wxDecisionCache`; `gateWeatherCode()` also updates `_wxDowngrade`. A replacement that calls this owner is not intrinsically pure either.
- The exact accepted R0007 preservation driver/observer avoids calling `qaState`, model or render to manufacture an observation. Its post-capture Moon diagnostic explicitly checks visible surface before/after because that getter is not intrinsically passive.

This is evidence for removing an unnecessary observer disturbance. It does not establish that a diagnostic call caused any particular missing video frame. Video PTS and host/fixture clocks are not uniquely associated at each read, and the recording has other environmental differences from R0007. The renderer/capturer/encoder/source cause remains unknown.

## Smallest meaningful next acquisition

Prefer the coordinator's simpler proposal over constructing a new diagnostic object: retain the same original full assertion predicates immediately before and after each already declared 30-second watch; remove full diagnostic reads inside those watches; and replace full-read recovery polling with an owner-checked passive read of existing admitted `weather.precip`, actual card `data-precip`, and visible particle DOM. No new `weatherDecision`, `qaState`, atmosphere/model, canvas pixel read or lunar surface/state getter belongs in that polling path. If a readiness predicate is changed, preserve each existing condition against the same actual owner, rather than replacing readiness with elapsed time or a weaker condition.

A02/A03 require actual state and original continuous pixels, not a five-second diagnostic cadence. The reduced cadence must be disclosed as an observer change. The unchanged state assertions still run at both boundaries, native ingress remains ordinary, and the full original video/index remains the continuity evidence. Optional passive intermediate reads are unnecessary to decide this pilot and should not add a new observer architecture.

Preserve the current fixture, driver, packet, receipts, videos and indexes as an immutable prior version. Pin a separate successor fixture/driver/packet. Execute only the original night-default case first, with the same browser/mode/recorder, input, native 1× clock, normal retry, 30-second initial watch and separate 30-second recovered watch. Do not add a settling delay or choose a new start from a healthy frame. Inspect original media before deciding whether the two other affected preferences should use the same successor. Success would qualify only the observed successor interval; it would not prove causation or rewrite the original failures. Failure would require a new evidence-led diagnosis, not automatic repetition.

Full reads immediately before/after the watches can still affect presentation. Keep that residual limitation visible; their placement is a controlled reduction of observer disturbance, not a claim of completely passive acquisition. Bounded direct state crops remain valid C15 evidence independently of this experiment. No C16 Firefox PASS, exact-head qualification, delivery or closure is granted by this diagnostic note.

This review used source inspection, raw receipt reconciliation, offline original-video decoding and native PNG inspection only. All writes are private independent reports or derived original media.
