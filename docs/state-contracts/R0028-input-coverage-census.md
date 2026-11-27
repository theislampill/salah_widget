# R0028 source inputs and instrument selection

The census keeps two sets with different purposes. Total coverage remains the
union of command arguments, command `inputs` and explicit `covers`. That set
continues to identify any unregistered instrument. Selection for the
selected-versus-declared conflict is the existing command-argument and explicit
`covers` population. Merely hashing a source input does not claim to execute it.

A declared imported module or excluded native recipe may therefore be a command
input. Its bytes remain required and hashed by the unchanged setup checks. The
module/exclusion declaration remains present. If that same path occurs in an
actual command argument or explicit `covers`, the conflict is still refused.

Missing declared paths, unregistered instruments, native glob additions/deletions,
glob time bounds, command execution, source identity, expected-failure ledger,
classification and qualification levels retain their existing rules. No
declaration, input, ledger row or required observation is removed by this fix.

The motivating R003F integration added the unchanged acquisition identity helper
to its complete command input closure. The previous census treated that input
as an executed instrument and returned `INCOMPLETE` despite all selected
commands passing. That failed invocation is retained separately; it is not
relabelled as a successful gate.

Seven focused runner controls distinguish input-only modules/exclusions from
actual argv/covers conflicts, verify actual input hashing still responds to byte
changes, preserve total input coverage, and retain missing/unregistered/glob
refusals. Against the original runner, the two input-only cases fail and the
five refusal/coverage controls pass. The narrow implementation changes only the
set used for the declared-selection overlap. The original 46 runner cases remain
in the same instrument alongside the seven new cases.
