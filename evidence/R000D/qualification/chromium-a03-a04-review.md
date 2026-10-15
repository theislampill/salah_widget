# Independent Chromium A03/A04 acceptance

Executor transcription of the read-only `/root/r000d_review` return. Requested
model: GPT-6 Astra; reasoning: Max. This is bounded native qualification, not
merge, delivery or closure authority.

A03 accepted receipt SHA-256 values:

- ignored-abort: `d3d51863ed801041f2452e5b14eda0fda4c9b902ab4f4077e56bd9fbc35fae72`
- settings supersession: `c7a38da13e82f03bd11c91849e5a26b683ef51fd38a258aca269af96b9f91de2`

The reviewer verified all eight fixture and four source hashes against each
manifest, exit0 and returned teardown. The old native JSON fulfills after the
captured abort: ignored-abort body90287.2 ms versus deadline10378.8 ms; settings
case body2557.1 ms after abort1995.8 ms. B remains active with identical complete
requests, slots, busy fields, raw weather, track, radar, cache, timestamps and
storage mutations across old release, then admits healthy20C. Actual settings
inputs commit B21.42,39.83, generation1 with matching stored configuration and
cache key. The settings case is supersession before the old deadline, distinct
from the ignored-abort timeout case. Saved Image callbacks are separately proved
by unchanged actual-source tests at lines82 and132; A02 proves native late loads
with detached handlers. Physical cancellation and memory reclamation are not claimed.

A04 accepted original receipt SHA-256 values:

- reduced: `beee7f3f00417d94bc197adc8969d5b851fde971fea43b97d5580f4cfb446446`
- full override: `9395d298bfbe38883f0c6294730b656ea153f3f07ba6c4328dec53dfa1643ce2`

The reviewer directly inspected original held, expired, terminal and recovered
cards, terminal Moon crops and0/10/20/30 sky PNGs. The half Moon is present and
opaque with no stars visibly through either limb. Header, prayers and footer
remain readable. Current expires naturally after source age900000 while body2
is still active; source/receipt/cache remain unchanged and temperature withdraws.
No Date offset is used; wall-minus-monotonic differences are -0.8/-0.5 ms. Recovery
admits20C and retains the explicitly unobserved model label. This uses an initially
aged synthetic source, not a fifteen-minute receipt-age watch.

Reduced policy leaves the cloud canvas unchanged over30.328 seconds. Full override
under reduced preference produces visible cloud displacement and shape change
over30.344 seconds:17,552 cloud-canvas and44,962 sky channels change by more than2.
Those counts support the independently inspected original PNGs; they are not a
cloud-hash or countdown-motion oracle.

## Exact continuous interval and retained contrary frames

Only the separately named original-video intervals **160.00 inclusive to190.00
exclusive PTS** qualify for the30-second recovered clip predicate.

- Reduced video: `0c993dc883dd0db07f29cd010c3c3d34ae7fb12e6bc77bdf4acea990e210ca9a`
- Full video: `8b51502d761883f9fd07ca40e6d2e9ed70fe8b116b6753869d8cfec3a5cfbc91`

Each original is390x600 at25 fps and decodes750 consecutive frames in that
interval. Direct ordered pixel inspection finds a stable full325x530 card,
readable header/prayers/footer, gradual clouds and changing precipitation in
full motion; reduced sky/cloud geometry remains stationary as intended. Every
frame screening found zero blank/crop candidates within that interval. Minimum
whole-card grayscale SD is36.93/37.02; maximum adjacent-frame mean delta is
0.498/0.738. Screening supports the inspected pixels and does not replace them.

The original complete recordings and the checkpoint-containing full interval
remain **UNQUALIFIED for uninterrupted whole-card continuity**. Retained reduced
video PTS91.64 shows enlarged header over gray, with91.72/91.76 Moon-crop views.
Full video PTS107.24-107.32 shows a Moon crop, and196.36-196.40 shows an enlarged
sky crop over gray. The nearby normal frames do not rehabilitate those intervals.
Capture association is an inference; this is not a demonstrated product renderer
failure. No original frame was deleted, edited or relabelled, and no new browser
or recording was used to obtain the separately bounded positive interval.

Read-only FFmpeg8.1.1-full commands used by the independent reviewer:

```text
ffmpeg -ss 160 -t 30 -i <original.webm> -vf crop=325:530:0:0,scale=65:106,format=gray -f rawvideo -pix_fmt gray pipe:1
ffmpeg -ss 160 -t 30 -i <original.webm> -vf fps=0.4,crop=325:530:0:0,scale=195:318,tile=4x3 -frames:v 1 -f image2pipe -c:v mjpeg -q:v 4 pipe:1
```

The first stream has750 frames of6890 bytes. Screening thresholds were SD<1,
white>245 fraction>.15, or gray120..136 fraction>.20. The reviewer also inspected
full-resolution original PNGs and the video170-second frame. Decoding was in
memory and did not modify source or evidence.

Both videos come from their same single-page context configured390x600,DPR1,
Asia/Riyadh and exact source `d4e3f084aea7d264a5c790268a21aa015b5e565e1feb9ad853d953c1c8a7b26f`.
Fixture run identities are `65094900-16d6-49b5-88eb-e9a5dd9ac91b` and
`c10678bc-eadd-47ed-8746-2f2e6fff40b8`. Recovered monotonic times are
151117.7/151023.5, final times197528/197236.3. Both follow wall time at1x,
remain visible, and have no fixture weather actions during this interval.
Native reduced preference is true in both; effective reduced is true/false.

Firefox acceptance is separate native PNG/render observation, with no continuous
Firefox screencast claim. The historical failed Firefox videos remain retained.
