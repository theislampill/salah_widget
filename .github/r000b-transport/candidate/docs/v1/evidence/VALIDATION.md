# Preservation validation receipt

Tested on Windows build 26200, Chromium `148.0.7778.96`, Python `3.11.9`,
Playwright `1.57.0`, Pillow `12.2.0`, Node `22.16.0`. Existing installations were
reused; no dependencies installed. Full browser receipt:
[browser-results.json](browser-results.json), including runtime/test hashes,
settings, fixture clocks, font hashes, geometry, request paths and screenshot hashes.
Retained JSON/HTML evidence is normalized to LF; the original Windows output and
replayed font files remain in the outside-repository test directory. Runtime and
PNG bytes are unchanged.

| Check | Result |
|---|---|
| Frozen payload/anchored manifest | PASS |
| Root index/config equal pinned production | PASS |
| Static Pages inclusion prerequisites | PASS; hosted deployment pending |
| Disposable index tamper | Correctly rejected as `v1/index.html` changed |
| Storage tests | 10 passed, 0 failed |
| Day, DPR 1, root vs V1 | 0 changed pixels / 176220 |
| Night, DPR 1, root vs V1 | 0 changed pixels / 176220 |
| Day, DPR 2, root vs V1 | 0 changed pixels / 704880 |
| Countdown advancement | PASS on all six comparison scenes after 61 virtual seconds |
| Six rows, Gregorian/Hijri dates | PASS on both paths |
| Coarse `#local=1`, GPS grant and denial | All four root/V1 permission cases passed |
| Manual recovery after denied GPS | Save/reload passed on both paths |
| V1 settings save/root unchanged | PASS |
| Later incompatible root settings ignored | PASS |
| V1 prayer/weather cache namespaces | PASS |
| Disposable root index/config replaced | V1 unchanged: 0 changed pixels / 176220 |
| Page errors / failed local or external fixture requests | 0 |

Storage cases cover valid import, V1 precedence, isolated save/reset, reset before
import, missing/corrupt/future-schema/invalid-coordinate legacy settings, blocked
storage fallback and isolated probe. Root settings and caches are never changed
by the V1 functions. The tamper and root-replacement controls use temporary copies.

Captures were visually inspected. Header, six rows, countdown, dates/footer and
existing legacy day/night presentation match. The settings panel remains inside
the card. Iframe viewport is `330×534`, internal card `325×530`, document scroll
size `330×534`; footer bottom is `520.34375` CSS px (within the iframe).
No dimensions, typography, rendering or shadow choices were altered.

| Scene | Root | V1 |
|---|---|---|
| Day / DPR 1 | [root](root-day-dpr1.png) | [V1](v1-day-dpr1.png) |
| Night / DPR 1 | [root](root-night-dpr1.png) | [V1](v1-night-dpr1.png) |
| Day / DPR 2 | [root](root-day-dpr2.png) | [V1](v1-day-dpr2.png) |

[V1 settings](v1-settings.png) ·
[V1 after disposable root replacement](v1-root-replaced.png) ·
[root iframe fixture](root-iframe.html) · [V1 iframe fixture](v1-iframe.html).

These are controlled comparisons: `#local=1` is unchanged; time, observer, provider
responses, permissions, fonts, viewport and DPR are fixtures. Browser permission
grant/denial is emulated; physical GPS and the actual Tabliss host were not tested.
External provider correctness/availability and post-merge public `/v1/` remain
outside this receipt. No CP9 or V5 renderer qualification is claimed.

During harness development, two expectations were corrected against unchanged
production source: six rows include Sunrise; the countdown displays minutes at
these intervals, so advancement is checked over 61 seconds rather than two.
Those were test assumptions, not application changes or suppressed failures.
