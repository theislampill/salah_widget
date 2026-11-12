# run1-ef6549c9 (superseded)

First native run by the root on candidate `ef6549c9` with the original driver (`b34591ac`).

- Its `retirement` cell reports `pass: true`, but that driver had no precondition check: the solar cloud mask at
  pagehide was the clear gradient, so there was nothing new to publish and the pass is vacuous. It is NOT evidence
  for the retirement-publication finding.
- The Firefox folders hold only screenshots 1-2: the run died in the `cycles` cell (synthetic-pagehide crash,
  present on main as well) and that driver lost its report on a crash.

Use `../run2-22048e3e/` and the "Native observation" section of `docs/state-contracts/R0021.md`.
