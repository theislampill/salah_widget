# Bounded Git publication helper — trace-boundary successor

Status: **31 local author controls pass; independent successor review accepted at helper scope**. No live GitHub execution or candidate publication is represented by the local results.

The original helper and its independent P1 finding remain preserved in [the original packet](../git-pack-original/README.md). The separate successor removes inherited Git trace controls and curl verbosity from its controlled child environments. Before attaching the push credential, it refuses effective `trace2.*` configuration using the existing names-only configuration check. Existing configuration and hooks are preserved.

[The frozen author handoff](HANDOFF.md) and [producer receipt](final-tests.json) bind 31 passing local controls: the existing 23 publication/ancestry/authentication checks and eight diagnostic-boundary checks. Three inherited Trace2 environment cases perform actual single-ref pushes without persisting the synthetic credential. Global, included and injected configuration cases refuse before a push, with zero attempts and unchanged configuration/ref. The original expanded RED had seven demonstrated synthetic credential leaks; the injected-count case demonstrated a policy failure without activating a trace on that Git runtime. Every raw failure remains in the archive.

[Independent successor review](independent-review.md) passes the exact two-hunk correction and independently reruns the original held-out witness with only helper path/digest substitutions. The real local push still reaches its exact target, and the synthetic credential does not persist. Original findings and failures remain preserved; this is a helper-scope result.

`FROZEN-PACKET.json` binds all 198 selected files. `author-evidence.zip` contains those files and the manifest; `archive.json` records the independently checked archive identity. The twenty embedded `.git/config` entries are synthetic fixture configuration evidence, not Git object databases. The three exact production helper files are also available under `helper/`.

The publication plan reconstructs the full immutable candidate using the actual builder, proves exact tree equality, and makes one normal push to the commissioned R0007 branch. Its intermediate tree retains the executing seed's complete workflow subtree and four bootstrap files. Root then verifies the actual intermediate and finalizes exactly six paths through the connector, yielding the full target tree. Guarded old/new/ref checks and unknown-outcome handling remain in force.

Final clean target selection, actual dry reconstruction, live ref currentness, hosted authentication and pack transfer, six-path finalization, native qualification, integration, approval and whole-owner closure are separate later evidence obligations. The two prior HTTP 422 causes remain unknown.
