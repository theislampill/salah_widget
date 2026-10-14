# PR43 R1 bounded decoder cost return

**One byte-identical candidate returned; browser startup gate remains open.**
The draft adds a 256-entry eight-bit canonical Huffman prefix table per channel
and removes per-receiver normal/colour arrays and the normal entries iterator.
Long words, unmatched prefixes and the final partial byte retain the original
bit reader. Both reviewed digest calls, validations, Paeth prediction, scalar
arithmetic, payload and numerical/phase/profile consumers remain unchanged.

| Existing Windows Node v24.14.0 decode-only mode | Production median / p95 ms | Candidate median / p95 ms | Samples each |
| --- | ---: | ---: | ---: |
| First decoder call, fresh process | 135.1931 / 137.6139 | 115.1233 / 121.8658 | 9 |
| Warmed decoder | 112.6732 / 145.4429 | 92.7904 / 119.2221 | 21 |

First-call medians differ by 20.0698 ms (14.85%).
Warm medians differ by 19.8828 ms (17.65%).
BENCHMARK.json retains every alternating serial pair, min/quartiles/mean/max,
five warmups per implementation and source/environment identities. p95 uses
nearest rank; with nine first-call samples it is the observed maximum. One
warm pair was 3.6851 ms slower in the candidate. Natural GC is retained; no
outlier removal, forced GC or digest-cost subtraction was used.

Timing includes the complete decode function and both unchanged digest calls.
It excludes Node startup, input/API preparation, independent output hashing,
base64 conversion, source parsing and all rendering. These Windows Node/V8
timings establish no Chromium/Firefox first-scene improvement or S1 PASS.
Root's browser diagnostic and original first-scene bounds remain separate.

Decoded output is byte-identical, 3,965,156 bytes, SHA256
`25755b217ec6da7401740b3d4df06d23c917e4bfc447d5667938b7b960a69331`. All 32 concrete rejection controls preserve
the exact production error class/message, including all original eight decoder
controls and added codebook/truncation/padding/order boundaries. CONTROLS.json
and sealed raw stdout/stderr retain the actual run. Source/admission controls
do not qualify pixels or arbitrary malicious JavaScript object behavior.

Production decoder: `65baddcf5ef56e724b13ab14b840534610f62eda72129ca32e29122f2a0f8cc7`.
Candidate decoder: `7281b9d439361af739c5a57ce5f008e608a118db59802a4c8ba8ecdfdd5473f0`.
Digest source remains `41a02370ec87de6e028d34b7ec2ecf947c8c37bee11d3047bc903b06f15c0620`.
Payload remains `dc131b3858aa20ddc858ccf1058fdcba533ec70d98f5d3bb28d1afc77b307269` (549,170 bytes).
Live production readback matches measured baseline: True.

The minimal DECODER.patch and replacement source are owned drafts only. Root
owns review/integration and actual browser qualification. No shared source,
build, browser, terrain, GitHub or subagent work occurred. This one candidate
is the end of the bounded comparison; no representation or precision search
was started and no startup threshold was changed.
