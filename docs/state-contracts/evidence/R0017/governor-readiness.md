# R0017 executing-governor readiness and Andon routing

## Disposition

The installed IMPLEMENTAUDIT governor supports the ordinary governor/helper route already used by root. The independent support work found a concrete **internal-child routing failure** in the installed layout. It must not be described as a working `audit-andon` route, a complete atomic package, or a verified installed release.

Root reports that controller `r0017-explicit` has already been claimed, its seven templates initialized and authored, and full run-root validation, new-session resume, receipt verification, and currentness enforcement have passed. Read-only discovery by this support agent subsequently resolved that same controller to:

- Worktree: `/workspace/scratch/7a8daf93afaa/r0017-explicit-work`
- Run root: `/workspace/scratch/7a8daf93afaa/r0017-explicit-work/.IMPLEMENTAUDIT/runs/r0017-explicit-regression-lifecycle-Cro7Xr`
- Claim: `629c4740e8627e8cd22dc9b5e1206c62`
- Receipt reported by root: `refs/implementaudit/continuity-receipts/r0017-explicit/G0001@01af128042a95577d152f2158b061d517bb8deb5`

**Do not create another controller or run root.** This report does not independently attest the continued validity of root's receipt after subsequent STATE, ROADMAP, or source changes. Root owns that currentness check and every transition. This support agent did not claim, invalidate, resume, mutate, or supersede any controller.

Ordinary source repair, the governor's own deterministic Andon diagnosis, and independent in-scope verification can proceed with bounded claims. The commission expressly says that a missing tool limits the corresponding claim, rather than all local source work. The governor itself says a missing child gate refuses child loading while ordinary cheap-path actions stay on the Execution Spine. If root reaches a later mandatory gate that depends on the unavailable child or conditional checker, only that gate and its dependents remain blocked; the records must say so.

## Executing package identity

The host-designated executing directory is:

`/home/agent/.codex/skills/remote-skills/skill-6a85962852788191bb717a1a61592b58`

Its real `SKILL.md` identifies `name: implementaudit` and has frontmatter `metadata.version: "0.4.0"`. That is an observed metadata label, **not established runtime-release provenance**. The installed package's own command

```bash
bash /home/agent/.codex/skills/remote-skills/skill-6a85962852788191bb717a1a61592b58/scripts/detect-env.sh \
  --package-version /home/agent/.codex/skills/remote-skills/skill-6a85962852788191bb717a1a61592b58
```

returned exit `0` and the literal result `unknown`. No runtime-version manifest exists at the resolver's three supported locations: the package's `IMPLEMENTAUDIT_PACKAGE.json`, its two-level parent's `IMPLEMENTAUDIT_PACKAGE.json`, or that parent's `package/implementaudit-package.json`. Do not replace `unknown` with a guessed release number, the methodology source ref, a catalog label, or the frontmatter label.

Read-only inventory found 54 regular files. These hashes characterize the installed bytes inspected; they are not an upstream release attestation:

| Installed file | SHA-256 |
|---|---|
| `SKILL.md` | `325cb0f7be5c89aa300d859b27b69f109dbcab65c29511dc69317c5315fa58b7` |
| `scripts/claim-run.sh` | `9c9945fdf650c72b8019f0dd908fff360162cc11ae7eb3197ccafe0f6ab3730f` |
| `scripts/validate-run-root.sh` | `5d5c0535449d0fdfdc5b65eb02f47ea95c717b6fc46c84ded0c55406a8b32e2a` |
| `scripts/resolve-internal-skill.py` | `be553c29e1092643a71e6b50260d760bab15bbc76cd3c2091d05c4b52b8f302e` |

Local inventory digest: `bc98edd07cfa1d6f97e9805ebe094d65dc24e4e54254c089ed51b91b51eb2675`. The input was the path-sorted set of regular files; each contributed `relative-path + NUL + file-sha256-hex + LF`, hashed once more with SHA-256. This is an explicitly local diagnostic identity, not a package-defined fingerprint.

All 21 installed shell/Python helper scripts passed `bash -n` or Python `ast.parse` respectively. This supports syntax availability only. It does not establish all helper behavior, release currentness, source parity, package completeness, or every gate's executability.

## Confirmed internal-child route failure

The actual installed resolver was executed, without changing its inputs or layout:

```bash
python3 /home/agent/.codex/skills/remote-skills/skill-6a85962852788191bb717a1a61592b58/scripts/resolve-internal-skill.py \
  --governor /home/agent/.codex/skills/remote-skills/skill-6a85962852788191bb717a1a61592b58/SKILL.md \
  --child audit-andon
```

Observed exit: `1`.

Observed stderr:

```text
resolve-internal-skill: governor directory identity is not implementaudit
```

Direct inspection of the resolver explains the result. It requires the real governor parent directory to be named exactly `implementaudit`. After that check it accepts one of two complete layouts: a standalone `internal-procedures` directory with all four exact child Markdown names, or canonical `skills/<child>/SKILL.md` sibling directories with the exact child population. It rejects ambiguous layouts and does not permit discovery/search order as a substitute.

The executing directory instead has the host's hashed name beneath `remote-skills`. It has no `internal-procedures` directory and no canonical sibling children. The host advertises separate child skill packages, but that discovery surface does not satisfy this installed resolver's path and population requirements. The runtime command and the filesystem/static-code examination are two structurally different probes of this specific negative capability.

### Bounded diagnosis for the governor's Andon record

- **Observed gap:** the installed resolver cannot establish a governed `audit-andon` child path.
- **Immediate cause:** its mandatory real-directory identity check rejects the host-exposed hashed package path before child selection.
- **Further supported cause:** the actual package also lacks both complete child layouts accepted by the resolver.
- **Owner boundary:** this concerns the executing skill's installation/layout contract. It is not a demonstrated defect in `salah_widget`, its regression runner, or the R0017 source candidate.
- **Unknown:** which distribution/provisioning step produced this mismatch, and which supported repair its owner intends. No supported manifest proves a particular runtime release.
- **Countermeasure within this commission:** preserve the actual failing result and contain the unavailable route; use the governor's ordinary Execution Spine and its own proportional diagnosis where sufficient.
- **Countermeasure outside this support authority:** rename, symlink, copy, reconstruct, or patch the installed package, substitute a methodology checkout as the executing install, or alter the resolver. None was attempted.
- **Recheck trigger:** a real executing-package/host-layout change or a newly supplied supported route. Repeating the same command under renamed probe labels cannot establish availability.

A suitable official abnormality class is `failed-criterion`, with the executing-package route as the failing criterion. `executing-package-layout` can be a descriptive blocker discriminator; it is not an invented official class. If root records a negative capability, include the required fields rather than a blanket environment failure:

```text
blocked_scope: governed audit-andon child loading through the installed resolver
unblocked_work: ordinary R0017 source repair, governor-owned deterministic diagnosis, and independent in-scope verification
negative-capability: true
probe_methods: installed-resolver-execution, installed-layout-and-resolver-inspection
probe_evidence: installed-resolver-execution::behavioral=>exit 1, governor directory identity is not implementaudit; installed-layout-and-resolver-inspection::structural=>hashed real directory, no internal-procedures, no canonical exact child population
falsification_attempted: tested the actual host-designated SKILL.md with the installed resolver and inspected both accepted layout alternatives; neither supplies a supported child route
```

These are **recommended record contents**, not a claimed root Andon transition. Root must bind its real phase, occurrence id, full capture anchor, evidence paths, and observed dispositions. The `probe_evidence` value has two semicolon-separated `method::method-class=>evidence` entries; retain those entry boundaries when incorporating it into the actual record.

The governor's routing section explicitly reserves `audit-andon` for L4 after a non-trivial Andon is established and bounded diagnosis can change the response; cheap deterministic Andons bypass that child. Even for a useful non-trivial diagnosis, the route's package gate still has to pass. Do not emit a child-loaded marker or claim an `audit-andon` review when only this governor-side diagnosis ran. This support report makes no readiness, release, mutation, or closure decision.

## Separate conditional validator gate

The installed `validate-run-root.sh` contains this conditional branch (observed in its current lines 1110–1117): when any run-root Markdown file has a line beginning `successor-review:` or `lane-status: status: REVIEWER_RUNTIME_NON_VERDICT`, it requires a source-repository checker reached three directories above the validator.

Under this installation that exact path resolves to:

`/home/agent/.codex/skills/scripts/check-cold-review-contract.sh`

Direct filesystem examination found that path absent. The validator's own source comments that the source checker is absent from the installed skill by design. Its rejection text is:

```text
live successor/non-verdict rows require the repository cold-review checker
```

This is a **conditional gate**, not a claim that root's present ordinary validator invocation must fail. Root reports the current invocation passed. If truthful later records trigger this branch, the installed validator cannot validate that contract from its current path. Do not create misleading replacement files, substitute a same-named target-repository script, omit truthful failure records to evade the branch, or report this condition as exercised successfully.

The standard prospective `cold-review:` contract has distinct requirements and is not identical to the successor/non-verdict branch. Where it applies, it requires a final independent reviewer report, bound actual/requested model, declared context independence, full distinct base/head SHAs with ancestry, exact attestation, and one terminal disposition. A support report or self-review does not satisfy that gate. No cold-review PASS is asserted here.

## Current-work guidance

Initialization guidance is superseded by root's successful existing controller setup. Use the existing run root, installed helper path, and exact controller id. Do not create a second micro or full root, supersede the claim, generate a fake compaction boundary, or mint a redundant new-session receipt.

The original full claim needs all seven templates (`STATE.md`, `PROTOCOL.md`, `ROADMAP.md`, `THINKING.md`, `sidecars.md`, `tools.md`, `context.md`), plus applicable phase goals and brownfield evidence. Root has supplied the initialized validated state. Any later changes still require truthful current evidence and the installed validator's applicable checks. The recorded authority should retain the commission's explicit local-commit, own-branch push, evidence-comment, and non-closing-review-PR permissions, with merge/main-push/deployment boundaries intact. Do not leave contradictory template default denials after recording actual granted authority.

At the initial read-only baseline observation, target HEAD was `f71fef6ccf7e4efcb57b5a26688d2360461a3253`, tree `79aedcac840d624b5ea423922314f0832dc3f750`, common Git directory `/workspace/scratch/7a8daf93afaa/repository/.git`. That was an observed local baseline while root populated the worktree, not proof of current remote main and not a later candidate attestation. Root must maintain the fresh source baseline and candidate identities.

No RC, self-dogfood, release-currentness, or maintainer route applies merely because the user requested IMPLEMENTAUDIT for ordinary R0017 source work. This support task did not start such a workflow. No package repair, source edit, publication, controller mutation, independent child invocation, or lifecycle completion took place here.

## Sources and review coverage

Read fully: the installed `SKILL.md`; issue-ready work orders, planning depth, lean operating discipline, continuity, child-agents, and plan-lifecycle references; the governor protocol's entire Andon escalation section; `claim-run.sh`, `resolve-internal-skill.py`, and `detect-env.sh`; STATE, ROADMAP, context, tools, and sidecars templates. The conditional validator branch and its claim-validation entry were directly inspected. This was not a full semantic audit of all 54 package files. Commission excerpts and live Git/controller metadata supplied task scope and actual initialization facts; root retains full commission and repository-instruction responsibility.

Evidence sources are the exact installed files and command outputs described above, plus root's explicit controller progress message. The report distinguishes independently observed results from parent-reported validations and unexecuted recommendations.
