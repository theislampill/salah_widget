# Closure index (append-only)

Repository-side index of the closure authority that lives in GitHub issue comments (R0028, ISM-BLD-005).
It records, per certificate-bearing work order, the FINAL certificate and its bound commit, withdrawals,
corrections and reopenings, contract lines that a later certificate supersedes, and acceptance bases that
are not fresh observations. Historical contract text is never edited; the supersession is stated here.

Rules:

- Append rows; never edit or delete an earlier row. A wrong row is corrected by a later row that names it.
- `Marker` is the exact start of the comment's first line, and `Bound commit` the SHA it carries (if any).
  `tools/qa/r0028_closure_readback.py` re-reads each cited comment read-only and compares both.
- `tests/r0028-closure-index.test.cjs` checks this file structurally: every contract line that says
  `wholeContractComplete` remains false, in a contract whose work order has a FINAL certificate here, must
  have a supersession row quoting that exact line; every quoted line must still match its contract.
- This index grants no authority and certifies nothing. The certificates do; this file only points at them.

## Certificates

| WO | Issue | Kind | Comment | Marker | Bound commit | Contract |
|---|---|---|---|---|---|---|
| R0003 | #3 | CLOSE | 6182373378 | `# CLOSE-R0003` | - | docs/state-contracts/R0003.md |
| R0003 | #3 | FINAL | 6805636415 | `<!-- R0003-FINAL-CERTIFICATE:` | a4766a1b25d6fa0cc74a989a78384035881b543f | docs/state-contracts/R0003.md |
| R0007 | #7 | CLOSE | 6162239043 | `# CLOSE-R0007` | - | docs/state-contracts/R0007.md |
| R0007 | #7 | FINAL | 6787290418 | `<!-- R0007-FINAL-CERTIFICATE:` | dbf3370f39d569936ae74ad795638525b53ccd98 | docs/state-contracts/R0007.md |
| R000B | #11 | CLOSE | 6178041776 | `## CLOSE-R000B` | - | docs/state-contracts/R000B.md |
| R000B | #11 | FINAL | 6788969371 | `<!-- R000B-FINAL-CERTIFICATE:` | da12688033c9481a3fea12e6aeed68b23a385694 | docs/state-contracts/R000B.md |
| R000D | #13 | CLOSE | 6183596140 | `**CLOSE-R000D` | - | docs/state-contracts/R000D.md |
| R000D | #13 | FINAL | 6791942315 | `<!-- R000D-FINAL-CERTIFICATE:` | 645b53cc5d04d35444f6da0e27bf5a5b6b11ce67 | docs/state-contracts/R000D.md |
| R000F | #15 | FINAL | 6806041365 | `<!-- R000F-FINAL-CERTIFICATE:` | 32f97b06b373bb9fd2801295529b078f5100cd24 | docs/state-contracts/R000F.md |
| R0013 | #19 | FINAL | 6814244464 | `<!-- R0013-FINAL-CERTIFICATE:` | a1072ae1ede1fd3f7a666bb6992c749df44bc67b | docs/state-contracts/R0013.md |
| R0015 | #21 | FINAL | 6828391831 | `<!-- R0015-FINAL-CERTIFICATE:` | 363c3e536c8004935ef80230e43f7712e339e3a5 | docs/state-contracts/R0015.md |
| R0016 | #22 | FINAL | 6828374683 | `<!-- R0016-FINAL-CERTIFICATE:` | e4dbf91be91f7539b36297e030f86e2a0e99f54d | docs/state-contracts/R0016.md |
| R0017 | #23 | CLOSE | 6181111816 | `# CLOSE-R0017` | - | docs/state-contracts/R0017.md |
| R0017 | #23 | FINAL | 6785616297 | `<!-- R0017-FINAL-CERTIFICATE:` | 539c13665797ee9052ea1c09d639155ade52a8b0 | docs/state-contracts/R0017.md |
| R0021 | #33 | CLOSE | 6326407465 | `<!-- CLOSE-R0021:v1:PR67:` | f71fef6ccf7e4efcb57b5a26688d2360461a3253 | docs/state-contracts/R0021.md |
| R0021 | #33 | FINAL | 6809435795 | `<!-- R0021-FINAL-CERTIFICATE:` | 5279958a086710eec15a427bab86d8e81b59d9bc | docs/state-contracts/R0021.md |
| R0026 | #68 | FINAL | 6804824819 | `<!-- R0026-FINAL-CERTIFICATE:` | 7f2e8d1614d6af4ced8366ac2300d8b481b01e72 | docs/state-contracts/R0026.md |
| R0027 | #69 | FINAL | 6810490146 | `<!-- R0027-FINAL-CERTIFICATE:` | 546d88281c4bdd0ae0a54d0b6ec5f9e5310c7c3a | docs/state-contracts/R0027.md |

## Withdrawals, corrections and reopenings

| WO | Issue | Kind | Comment | Marker | Effect |
|---|---|---|---|---|---|
| R000B | #11 | CORRECTION | 6178186713 | `## CLOSE-R000B — corrected` | Corrected the 2026-10-14 qualification and delivery certificate 6178041776. |
| R000D | #13 | CORRECTION | 6792330574 | `## R000D — post-closure correction` | Post-closure correction to FINAL 6791942315: its regression scope was narrower than the registered suites. |
| R0013 | #19 | CORRECTION | 6813339770 | `## R0013 lexer correction` | Lexer correction before FINAL 6814244464. |
| R0015 | #21 | REOPENED | 6816192574 | `Reopened immediately after an unintended automatic closure.` | Auto-closed by a closing keyword and reopened; FINAL 6828391831 followed. |
| R0017 | #23 | WITHDRAWN | 6703510170 | `# WITHDRAWN — R0017` | Withdrew whole-contract completion claimed by CLOSE-R0017 6181111816. |
| R0017 | #23 | CORRECTION | 6713121284 | `# R0017 corrective status` | Corrective status: OPEN, acceptance withdrawn; replaced by FINAL 6785616297. |
| R0026 | #68 | CORRECTION | 6700145812 | `<!-- SW-EXPLICIT-STATE-20261106:PUBLICATION-CORRECTION` | Publication correction and common contract, before FINAL 6804824819. |

## Superseded contract lines

| Contract | Line | Quoted line | Superseded by |
|---|---|---|---|
| docs/state-contracts/R0015.md | 221 | `` `wholeContractComplete` remains false. This section claims no completion, `` | R0015 FINAL 6828391831 (363c3e53): ES15-18 and every open row recorded as met |
| docs/state-contracts/R0015.md | 335 | `` `wholeContractComplete` remains false. No completion, approval or closure is `` | R0015 FINAL 6828391831 (363c3e53): ES15-18 and every open row recorded as met |
| docs/state-contracts/R0015.md | 450 | `` The recorded follow-ups above remain NOT DONE. `wholeContractComplete` remains false. `` | R0015 FINAL 6828391831 (363c3e53): ES15-18 and every open row recorded as met |

## Acceptance bases that are not fresh observations

| WO | Rows | Basis | Authority | Locator |
|---|---|---|---|---|
| R0007 | `recovery12`, `wall-ordinary-control` and the mutants `mut-wall-spring`, `mut-wall-fall`, `mut-remove-next-dirty` (hosted Firefox run 42953929662, which stays FAILURE/PARTIAL) | owner-approved bounded cross-run evidence reuse of earlier accepted runs of the unchanged selector code; not a fresh observation | owner, at the reviewed scope | FINAL 6787290418; docs/state-contracts/R0007.md line 240 ("a stated judgment, not a fresh observation") |

This is a disclosure index, not a certificate defect: both the certificate and R0007.md already state the
reuse. R0007 is not reopened by this row.
