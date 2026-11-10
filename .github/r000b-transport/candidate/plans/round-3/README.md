# salah_widget — Plans, Round 3 (local self-configuring mode)

Read-only `/implementaudit` plan for the **in-widget local builder/settings mode with zero-permission area
auto-detect** (the additional task, 2026-06-16). Grounded against the current `index.html` (HEAD `90928c8` +
the round-1/round-2 work already committed) and `builder.html`. Same format as rounds 1–2: self-contained,
carries an adversarial self-critique whose required-fixes are folded in before coding.

> **Scope:** a generic `#local=1` iframe should (1) try a coarse, permission-free area auto-detect, (2) show
> prayer times, (3) expose an in-widget settings affordance on the header buckle, (4) let the user change
> location/settings inside the card, (5) save locally for future loads — while **existing hardcoded
> `#lat=…&lon=…` embeds keep working byte-for-byte** and the normal widget visual is unchanged outside settings.

## User decisions (locked 2026-06-16)

1. **Geo provider:** GeoJS primary (`get.geojs.io/v1/ip/geo.json`) → ipinfo.io fallback (`/json`) → manual.
   Both **live-CORS-verified** from the browser; ipapi.co/freeipapi/ipwho.is/ip-api all failed verification
   (CORS-blocked, paid-HTTPS, or unreachable in test) — see the feasibility evidence in plan 01.
2. **Config code:** **extract a shared `config.js`** (`window.SalahConfig`), loaded by both `index.html` and
   `builder.html`. This deliberately relaxes the long-standing "single self-contained `index.html`" invariant —
   docs/memory updated to record the change and why (true un-forkable single source for config logic).
3. **Pacing:** one continuous pass — plan → implement end-to-end → verify in preview → present. **No commit**
   (commit to `main` = Pages deploy; needs explicit authorization).

## The plan

| # | Plan | Class | Risk |
|---|------|-------|------|
| [01](01-local-mode-and-shared-config.md) | Shared `config.js` + local/auto-detect/settings mode (the whole feature) | feature | med |

The feature is one coherent change with a hard internal ordering, so it is **one plan with sequenced phases**
rather than several independent plans. Phases P0–P7 inside plan 01 are individually verifiable.

## Non-negotiable invariants (carried from rounds 1–2 + AGENTS/HANDOFF)

- **Existing hardcoded embeds unchanged** — `#lat=…&lon=…&method=…` resolves synchronously at module load
  exactly as today; prove byte-identical render (Smoke A vs B: `qaState` snapshot + screenshot).
- **Stale localStorage must NEVER override an intentional hardcoded embed.** Local config applies only when the
  URL opted in (`local=1`/`preferLocal=1`).
- **Normal widget visual unchanged outside settings mode**; the gear affordance must not disturb header layout
  or clip the 325×530 card; settings panel must not enlarge the iframe.
- **Never reintroduce** the moon spin / transparent moon / painted dawn (untouched here, but the smoke suite and
  render path must stay green).
- **No tracking; disclose the IP send.** Coarse detect contacts GeoJS/ipinfo with the user's IP (inherent);
  documented. Precise geolocation only on user action. Saved config stays local.
- **No-build / no-dependency / static Pages.** `config.js` is a same-origin static asset (not an npm dep); it is
  the only structural change to the single-file rule and is intentional.
- **Do not commit** unless explicitly asked. Never commit the 3 scratch files.

## Verification matrix (the task's 16 smokes)

Deterministic (config.js unit smokes in `tests/smoke.html`): hardcoded parse/serialize round-trip, precedence
(hardcoded vs local vs preferLocal), validate/normalize/clamp, storage save/load/clear, storage-blocked
graceful-degrade (mock throwing localStorage). Preview/manual receipts: `#local=1` first run, coarse detect
success + failure→manual, save+reload persistence, reset, gear by mouse/keyboard/touch, normal view restored on
close, builder generates both snippets, precise geolocation success/denied (best-effort, env-dependent),
TablissNG-equivalent plain iframe host page.

See plan 01 for the full design, the `WidgetConfig` contract, precedence algorithm, phase-by-phase acceptance
criteria, risk register, and the adversarial self-critique.
