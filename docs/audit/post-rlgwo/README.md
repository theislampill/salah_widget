# Post-RLGWO implicit state-machine audit

Documentation-only, repository-wide audit of main `363c3e536c8004935ef80230e43f7712e339e3a5`
(tree `647b7159a60ceb7dc650563890a5a5a63af14319`), compared with the original state-machine
audit at `f71fef6c`. Nothing was remediated and no issue was filed.

| Deliverable | What it is |
|---|---|
| [IMPLICIT_STATES.md](../../../IMPLICIT_STATES.md) | Canonical registry: 110 machines by domain (`ISM-PRAY`, `ISM-WX`, `ISM-CFG`, `ISM-SKY`, `ISM-MOON`, `ISM-BLD`, `ISM-V1`, `ISM-INST`), status on three dimensions, index table |
| [REPORT.md](REPORT.md) | Method, audited identity, work-order inventory, counts, instrument history, second omission pass, verification corrections, coverage limits, checks |
| [CROSSWALK.md](CROSSWALK.md) | Every original machine (83), finding (18) and hypothesis (3) → current registry ID, work order, evidence, disposition; the 25 new machines |
| [FINDINGS.md](FINDINGS.md) | 37 documentary findings (`PRA-F-nn`) ordered by materiality, with evidence class, hard constraint, origin and `file:line` trace |
| [GDOPL_ASSESSMENT.md](GDOPL_ASSESSMENT.md) | GDOPL Post-RLGWO Assessment: schematic formulation, hard feasibility domain, inner and outer directions, historical comparison, final classification |
| [lanes/](lanes/) | Lane working papers A–G (superseded by the documents above where they differ) |
| [probes/](probes/README.md) | Effect-free probe scripts and recorded outputs |

How to read them: start with the registry index for a domain, open an entry, follow its finding
links into FINDINGS.md, and use REPORT.md §8 to see what the integrator changed relative to the
lane papers. Status values and dispositions use fixed vocabularies defined in the registry and
the crosswalk; they are never collapsed into PASS/FAIL, and "demonstrated" never means observed
in a browser (none was run).
