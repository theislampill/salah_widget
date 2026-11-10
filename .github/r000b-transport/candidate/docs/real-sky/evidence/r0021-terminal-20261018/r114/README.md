# One diagnostic reference; no production sample-budget increase

The owner approved one isolated 64x256 (16,384-sample) reference after the retained r112 comparison. [Approval](OWNER_DECISION.json) binds that limited scope. Product sources stayed at `9df79b98d8dda7a0286b1b287dc03d1b4d760bdb` throughout this diagnostic.

[RESULT](RESULT.json), SHA-256 `77f2110c1d267ce35d94560f21b48cc20e1859a9c242b0c4a0ba3847140b23d9`, compares identical scene, 82 selected receivers, four row owners and the same 4096-stage cache predecessor. Earlier-stage hashes match both stored r112 arms; coverage and unselected receiver codes are unchanged. This is a sparse empirical discriminator, not an absolute or all-scene accuracy certificate.

| Comparison to reference | Maximum projected difference, offset 0 / offset 1 |
|---|---|
| 64x128: angular 128 to 256, fixed radial 64 | 0.2256746292 / 0.2938785553 |
| 32x256: radial 32 to 64, fixed angular 256 | 0.3502306938 / 0.4560794830 |

The fixed-angular comparison supplies the radial evidence absent from r112. The 32x256 candidate's original adaptive projected change is 0.1283655167, within the unchanged 0.5 empirical gate. [Independent review](../reviews/reference-r114-result-review-r1.json) recomputed 33 retained arrays and supports the minimal production 8192-sample reallocation **for affected qualification**. It does not grant native, S1, whole-cost, merge or closure acceptance.

Contrary evidence remains: the reference differs from the 4096 predecessor by 0.5844449997, with 14 receiver heuristics remaining; r112 cross-rule differences reach 0.7499580383. The original production rejection at 0.878323555 remains a real historical failure. Do not describe all rules as converged or reinterpret this as an absolute-error proof.

The portable official Zig 0.14.1 compiler and isolated C/engine extensions are diagnostic only. [Tool identity](build/TOOL.json), [build plan](build/PLAN.json), compressed source bytes and the isolated WASM are retained. The first compiler command failed before producing a reference; [SETUP-INCOMPLETE](SETUP-INCOMPLETE.json) remains INCOMPLETE. The supported corrected CLI completed once. [Execution](EXECUTION.json) and preflight reviews preserve both attempts and cleanup limits. No product compiler dependency, kernel, guard or sample ceiling changed.

For independent numerical inspection, decompress the `.bin.gz` payloads and check each compressed/decoded hash and typed-array declaration in RESULT; the original little-endian values are preserved. `reference_quadrature.cjs` accepts five arguments: checkout at the source HEAD above, a new output directory, the published r69 scene record, the r112 payload directory, and an isolated build directory containing the decompressed reference engine and reference WASM. It asserts the old source pins; it must not be run against the later corrected owner. The projected scene-record file has different bytes from the private original, while its numerical scene is unchanged. The historical wrappers show the bounded acquisition and declared path roles; they are provenance, not directly executable placeholder paths. No repeat is needed to review these stored results.
