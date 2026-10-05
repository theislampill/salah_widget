# CP9 integration candidate

This branch integrates the supplied cumulative CP1–CP9 real-sky programme onto
`main` **fd2972ba64225fe9d6848e92497e6d0ed20ea624** (tree
`c5382ee6cb32e71992da963f56b00c2eaa091d1c`). It is a Draft PR candidate, not release
or merge approval. The post-CP9 DAG is the implementation and qualification map.

## Source reconstruction

The attached `Salah_Real_Sky_Checkpoint_9.zip` is 218,870,451 bytes, SHA-256
`8d094b138c5970eae087a96458bcaefd8c988a12b2abd1fbc0c1b34b9f0c9bff`.
CRC, all 2,230 manifest-listed payloads, all 162 native baseline entries and the
213-file authoritative `widget/` inventory verified locally. Its canonical
runtime-tree SHA-256 is
`2ebde007ff96fa1b69e9df97f785d41bcf6c38437342913a2d10bed128cdd45b`.

The archive records native commit `205750350c64b77ebdc3ebcadcc39a6eb949994b`,
parent CP8.3 archive `a056d3789cb614355cc27af286907add231293ba42b2288894cdd3edca8d29a3`,
and scientific CP7.6 archive `f30470a68d02e47d83e5fd0d063a5320936802161e5d2b9ba701ba48d72f5e45`.
These are **archive provenance**, not an assertion of independent ancestry.
PR #38's branch, patch, commits and files were not acquired or used as donors;
the implementation inputs are current main and the supplied CP9 archive.

There are two meaningful deltas:

1. Current main → CP9's native baseline: 22 of main's 34 files are byte-identical;
   twelve differ; no main-only file is missing from the archive. Changes cover
   admission/generation ownership, accepted clock/calendar, weather evidence,
   cloud continuity, native lunar fallback/opacity, configuration and installer
   safeguards, builder recovery and their regression fixtures. These native
   prerequisites are reconstructed in their own commit.
2. Native baseline → cumulative CP9 product: 51 additions and eleven changed
   files, comprising generated index integration and ten fixture adaptations.
   The real catalogue, registered diffuse source, physical transport, currentness,
   worker-failure policy, composition and asset lifecycle are the new runtime.

Main's resolved-latitude solar calculation and 325×530 embed geometry are retained.
There is no newer main-only semantic delta to arbitrate at intake. The existing
main documentation/plans are retained and amended; historical galleries,
receipts, reconciliation donor and checkpoint copies are not installed as product.

The native source baseline's WEATHER fixture omitted `_pbrFailed`: 129 failures
were reproduced before carrying forward CP9's explicit declaration extraction.
That repair changes fixture coverage, not product assertions. Four inherited TODO
placeholders remain TODO and are not qualification evidence.

## DAG execution

Starting state: eleven historically closed findings, one scientific boundary,
and three mandatory OPEN nodes. N001 and N002 are independently ready; N003's
final acceptance depends on both. Historical PASS does not qualify changed bytes.
The per-node ledger and fresh command receipts record the final dispositions.

## Ownership and future Moon package

Native authored HTML/CSS, lunar geometry/orientation, phase and terminator,
material/PBR, Earthshine and textures live in `src/native/index.html`; native
configuration and builder sources live beside it. `tools/build_native.py` owns
the deterministic root entry, worker/bundle/CSS/data and offline expansion.
`real-sky/native-*.mjs` and `native-host-hooks.js` own the integration boundaries.
`vendor/real-sky` is an immutable scientific oracle and its test inputs; copied
`real-sky/core` is generated. Physical Moon illumination/occultation stays distinct
from the enlarged native calendar Moon. Composition is owned by
`real-sky/native-composition.mjs`. The forthcoming Moon-PBR donor should be
reconciled at those authored owners, then regenerate outputs and rerun lunar,
material, opacity, composition, currentness and performance controls.

## Acceptance boundary

No newly written status file supplies completion by itself. N001 retains the
250 ms maximum heartbeat/dialog budget across every loaded trial. N002 retains
the 30,000 ms accepted-UTC fence and the four-rate availability target. N003
requires actual platform/entry/lifecycle/provider evidence and rejects stale,
missing, duplicated or fixture-mislabelled records. Independent review remains
required before merge/release. This task ends with a Draft PR, without merging.
