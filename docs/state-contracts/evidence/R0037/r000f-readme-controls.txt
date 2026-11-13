# R37-11 controls: R000F invariants scenario (ES0F-15) in a disposable copy of tests/src/presets/builder/config/index/real-sky; README variants swapped in. 2026-11-12.
== RED: new scenario vs origin/main README (V1 snippet 330x534)
ℹ pass 0
ℹ fail 1
  AssertionError [ERR_ASSERTION]: README wrapper is 325×530
== GREEN: new scenario vs branch README
ℹ pass 1
ℹ fail 0
== MUTANT: branch README with V1 snippet restored to 330x534
ℹ pass 0
ℹ fail 1
  AssertionError [ERR_ASSERTION]: README wrapper is 325×530
== MUTANT: V1 snippet removed
ℹ pass 0
ℹ fail 1
  AssertionError [ERR_ASSERTION]: README V1 snippet present
== BASELINE: old scenario vs origin/main README (passes while ignoring V1)
ℹ pass 1
ℹ fail 0
