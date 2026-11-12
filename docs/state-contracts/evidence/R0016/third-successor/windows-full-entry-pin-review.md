# Final Windows full-entry carrier pin join

**PASS — exact final pin-only/source-interface join.** The rebuilt outer carrier `ba0ff7eee150244ee63af3e6556f9e5479086a34702381acaef48de6832d05aa` (45,463 bytes) joins to the independently reviewed `bf17db5a…` source logic and the frozen product inputs. This receipt resolves the prior provisional-pin limitation for this exact packet. It does not confer native product qualification, publication authority or R0016 acceptance.

## Exact joined identities

| Item | Bytes | SHA-256 |
|---|---:|---|
| Final outer carrier | 45463 | `ba0ff7eee150244ee63af3e6556f9e5479086a34702381acaef48de6832d05aa` |
| Unchanged workflow | 5272 | `339875261c390b8324cfac1438385b91f2fc7f48096e7228b5ee2db07ffe2148` |
| Frozen product-input manifest | 890 | `a98ec3c02631c8f56c460b54bc75cec36051d6bda8c9bcf23adc4f274dd0bc5a` |
| Product fixture | 56323 | `b235e870a49c12238468e0dcb7e52135ec9db6cbe17cbd7a49f257b35ef86189` |
| Product support | 44517 | `4cba85154dc359ea0389365f76660b2d095600cad7b05de7817de92debb7a987` |
| Final twelve-role pin index | 3027 | `202576ea323573b5218311cb5b456152942ded1879812a87540219a90cbc6396` |

## Independent verification

The retained `verify_join.py` completed with exit zero and **49/49 checks passing**. The comparison masks only the `INPUTS` assignment and then compares every remaining carrier byte. The sole changed role is `tests/install-entry-product-support.py`, from provisional `5ba05d95…` / 44,048 bytes to frozen `4cba8515…` / 44,517 bytes. Every carrier function is byte-identical, including source relation, terminal/capture admission, normal postcondition replay and report admission. The workflow is also byte-identical to the one retained in the bounded source review.

All twelve declared roles were read independently and their actual byte counts and hashes matched both the carrier constants and the final pin index. Both new product paths point into root's frozen input directory; the two-file manifest and both payloads match exactly. The other ten inputs and the separately pinned host helper remain exact. Each of the twelve workflow input paths appears in both the trigger and sparse checkout.

The product fixture is byte-identical to the reviewed CLI/interface snapshot. The frozen product support is byte-identical to the actual helper used by the final thirteen focused controls. Thus the earlier helper-version disclosure is resolved by an exact byte join, without claiming that an earlier provisional helper was tested.

The AST checks confirm the product's declared CLI arguments, all twenty original cases and five refusals, the report/envelope schemas and required scope fields, and the exact digest-field mapping for product support, unchanged common composition helper and diagnostic source. The normal and source-relation admission functions are unchanged. No product module, filesystem constructor, installer or native process was executed. The thirteen unchanged controls were not rerun.

## Preserved review evidence and limits

This receipt supplements the bounded source report `705be69d74c090c7debb5c63222c1f150f4a88b5cc22c46938e4363d413f5613` and its packet `570605d2a192d48bd17d84b320de768958e6daa1e43b592a5145d1268e3a999a`. Stage 1 and the original `dcd8` and `ff7` false accepts remain preserved. No historical failure is relabeled.

Root's refreshed 51 interface checks and eight parser/path controls are retained as supplemental author evidence, without independent execution credit. This lane made no shared-source, Git, remote or dispatch mutation. There is no active native process or unknown execution outcome associated with this receipt. Publication and any native campaign remain the governor's actions; actual product results require separate original-artifact receiving.
