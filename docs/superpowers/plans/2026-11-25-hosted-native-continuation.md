# Hosted native continuation implementation plan

> For agentic workers: use the parallel-agent and verification workflows. The owner has already authorized autonomous execution and independent exact-tree review; routine plan confirmation is not required.

**Goal:** Recover the unpublished observation tooling, obtain privately retained native browser evidence, and pursue the useful follow-up for R002F-A2, R0035, R0040 and R003F.

**Architecture:** A separate branch owns orchestration. Acquisition receives immutable public source and integrity-locked dependencies. One browser driver at a time runs as a nonroot account in a fresh loopback-only network namespace. All observation output is encrypted to an owner-held recipient before artifact publication.

**Tech stack:** Python standard library, OpenSSL CMS, Bash/util-linux, Node Playwright 1.62.1, Python Playwright 1.57.0, pinned GitHub Actions.

**Spec:** PR160 at `55d1b3edb66d2c35679707120b01ee1d3455e4a3`, the owner's 25 November continuation handoff sections 5–8, and the original issue contracts 96, 102, 140 and 145.

## Global constraints

- Research source: `55d1b3edb66d2c35679707120b01ee1d3455e4a3`; base: `df644ef60156b67b5c487395176369bcec7a0d7b`; historical rain helper: `4029d2f67f5a880c8ad889443bb7557d96022c45`.
- No merge, deployment, issue closure, registry promotion, changed standing assertions, invented native/human evidence or owner-policy choice.
- Keep original candidate failures, failed runs, declared ledger and ordinary qualification workflow intact.
- No private key in Git or Actions. Public artifact allowlist is exactly `capture.p7m` and `envelope.json`; all logs, image/measurement content and source manifests stay encrypted.
- No browser launch outside the verified isolation wrapper. No concurrent browser drivers on a machine. Network-isolation failure stops all observation; an R003F Andon stops R003F progression.
- Independent exact-commit review and authored/decompressed privacy scan precede each publication. Guard ref writes with the observed head.

## Review focus

1. Algorithm substitution and tentative plaintext release: reject CBC, weak OAEP/MGF, altered tags, trailing DER and unsafe archives before releasing output.
2. Browser-process egress missed by page routing: prove real Chromium loopback success and TEST-NET failure without route stubs, with sandbox retained.
3. Failed or timed-out lanes: preserve private output, kill children, seal successfully, and distinguish FAIL/INCOMPLETE/ANDON from PASS.
4. Native probe false positives: baseline stale negative control, complete prayer group and same-evaluation preview-state observations.
5. Source drift: separately bind orchestration, research inputs, built candidate hashes, installed packages and browser binaries.

## Tasks

- [x] Reconcile the five PR identities, exact trees, latest workflow states and actual workspace custody. Independently read the five suite verdict strings.
- [x] Recover the existing recipient privately; verify certificate DER fingerprint and certificate/private-key agreement.
- [ ] Rebuild `tools/qa/hosted-native/envelope.py` and behavioral controls. Interface: `seal --source DIR --out DIR --certificate CRT`; `open --source DIR --out DIR --certificate CRT --key KEY`. Fresh paths only. AES-256-GCM AuthEnvelopedData, RSA3072/OAEP SHA256/MGF1 SHA256; strict DER and archive validation. Verify positive roundtrip and all security negatives using independent test keys, then the actual recipient.
- [ ] Reconstruct `prepare.py` and `lanes.py` using the published R0040, R003F B0 and R0035 recipes. Verify canonical builds twice and recorded hashes. Supply exact callable arguments and private receipts; run offline controls before native execution. Keep observations sequential and statuses honest.
- [ ] Reconstruct the R002F probe separately in `r002f_probe.cjs` with build/control support. Read the actual source contracts and comments first; test admission predicates and negative controls before adding the native lane.
- [ ] Implement `acquire.sh`, `observe.py`, namespace/browser controls and the isolated workflow. Verify clean environment, changed namespace, loopback-only interfaces/routes, nonroot UID, capabilities/no-new-privs, real browser sandbox and egress denial. Register every new helper, control and recipe in the population without changing verification levels.
- [ ] Independently review the frozen commit, resolve findings, run focused registered controls and privacy scans, then publish to the exact pilot branch and a draft PR. Read back the commit/tree and actual run identity.
- [ ] Receive/decrypt and independently inspect the first hosted observations. Preserve failures and obtain remaining meaningful engine/DPR/motion/lifecycle evidence. Publish only reviewed code and privacy-safe bounded result descriptions. Retain exact encrypted artifacts and their provenance durably for the owner.

## Verification scope

The unchanged five qualified populations are recovery evidence, not tests to repeat without cause. New envelope/isolation/admission controls, canonical disposable builds, frozen V1 verification, population census and affected recipe controls qualify the changed risks. Hosted software qualification remains separate from disposable candidate acceptance and native observations.

## Interface ownership

- Envelope worker owns envelope implementation and its controls only.
- Lane worker owns preparation and first three lane command construction only.
- R002F worker owns its probe and controls only.
- Coordinator owns workflow, isolation, dependency acquisition, recipient certificate, central registry and publication.
- A fresh reviewer assesses the complete immutable integration before any hosted observation starts.
