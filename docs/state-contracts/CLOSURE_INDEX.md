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
| R0037 | #104 | FINAL-DELIVERED | 6844814360 | `<!-- R0037-FINAL-CERTIFICATE -->` | - | docs/state-contracts/R0037.md |
| R002B | #92 | FINAL-DELIVERED | 6844979120 | `<!-- R002B-FINAL-CERTIFICATE -->` | - | docs/state-contracts/R002B.md |
| R002D | #94 | FINAL-DELIVERED | 6845125534 | `<!-- R002D-FINAL-CERTIFICATE -->` | - | docs/state-contracts/R002D.md |
| R002C | #93 | FINAL-DELIVERED | 6859282902 | `<!-- R002C-FINAL-CERTIFICATE -->` | - | docs/state-contracts/R002C.md |
| R002A | #91 | FINAL-DELIVERED | 6860164878 | `<!-- R002A-FINAL-CERTIFICATE -->` | - | docs/state-contracts/R002A.md |
| R0029 | #90 | FINAL-DELIVERED | 6860166513 | `<!-- R0029-FINAL-CERTIFICATE -->` | - | docs/state-contracts/R0029.md |
| R002E | #95 | FINAL-DELIVERED | 6861511641 | `<!-- R002E-FINAL-CERTIFICATE -->` | - | docs/state-contracts/R002E.md |
| R0039 | #106 | FINAL-DELIVERED | 6862449283 | `<!-- R0039-FINAL-CERTIFICATE -->` | - | docs/state-contracts/R0039.md |

Kind `FINAL-DELIVERED` marks a final certificate whose first line carries no commit SHA (the eight rows
above, work orders closed after the R0028 population was drafted). Its bound commits, pull requests and
trees are stated in the certificate's own "Source" section and copied into the next table. The test and
the readback tool still require a SHA in the first line for kind `FINAL` only, so these rows are checked
for marker and comment id, not for a SHA. The per-issue certificates remain authoritative; this index
points at them.

## Merged delivery of the FINAL-DELIVERED certificates

Copied from each certificate's "Source" section; every commit and tree below was checked to exist with the
stated tree in the repository. "Main commit" is the merge commit on `main` that the certificate binds.

| WO | Pull request(s) and reviewed head | Main commit | Tree of the main commit |
|---|---|---|---|
| R0037 | #109 `7f3fae791e39cc196770cefa635bded6872c2dd9` (slice 1) | `f840527dbf4113626b9276cfbe3020d602df363e` | `092984ebb33e60bb33adbc50c40006cfff793e1f` |
| R0037 | #110 `dd41a6f9322b0057462411d371ddebde4db911b7` (slice 2) | `eacc3ad6355435a2bbeb50e45724469cbc133cca` | `c8d6a5bd032ede13b03ceddadb7383cd86c764e3` |
| R002B | #111 `09bebc0e737f4e9c3f5ef9b206acfc0cfdbf6754` | `559e1d59148e58199f5ce707644e081bcceb621f` | `0c390c17d8921617135fd2b45a522063050428d9` |
| R002B | #112 `e485f8f12425c24a2263de4d930ae2a9c1e657ca` (evidence and ledger only) | `8960cd7cd9bae4f5026f6f532ba8fd5da90c83fe` | `b3b02f24411a5f41070c8e560dd0bac606dff736` |
| R002D | #113 `dc967a723ab3c602edfea0cb79c58d118b66870b` | `e10da4811348ca883c30b8e6eae6dce2a67a8423` | `ec2e498a80d7424b8f937036840af4a1db90a7f9` |
| R002C | #116 `913887c23184b598e2ffab8a851e2b20e0f7e91f` | `885d5a31621733fe9025ffb36f91595ef7ae48f5` | `b640bb8b88db9e44a92eb607d8147053878d4417` |
| R002A | #117 `9cf6aec26e8319ad123ef1fcae9c923417bb4d91` | `846952ba305edcc6cf373e9a406b8fdac33fcbde` | `27e4a3774ff0ca58f6cbf3c6bfe42c05d07f4fa1` |
| R0029 | #108 `1f22c96dfe04f953fa0dce4d699ce9b6b9dcd666` | `c696b39ff1a3481c3b3dcf763fae0a6f62deb555` | `0d95d9bf9df292ae8c47cf64905fa653b99ab221` |
| R002E | #118 `b9ba16044aa144f11a021ae125f870da9c9134cd` | `cb603de4f8b5250cc3bbf8e7befa224e1541a90e` | `cfa8f1c1462dba10a27e2829b2c1d935e0939357` |
| R0039 | #119 `60431d5e2ea3a8050c22d1d79900b8b27aa9cfd8` plus one documentation-only commit, merged head `c71406affe05dc94c7b5d97f4918660f71f0b36d` | `664ebe22720a64a6e6e0014cee4c2dc22774b3c7` | `f8b3e1b977d003ddfdfb9d00b0017d0de35e1cae` |

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
| R0029 | #90 | CORRECTION | 6860222361 | `**Evidence pointer correction to the R0029 certificate` | Corrects the evidence pointers of row G-08 in FINAL-DELIVERED 6860166513: primary evidence is run 43470981217 on main 846952ba; run 43419734052 is the earliest Linux observation. The row's conclusion stands. |

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
