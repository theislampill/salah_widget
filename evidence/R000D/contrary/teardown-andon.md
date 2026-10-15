# Audit-ANDON: receipt lost during Firefox teardown

The sole independent reviewer applied the installed Audit-ANDON skill read-only.
The first Firefox manifest-header attempt reached recovered screenshots, but no
final receipt was saved. It remains unqualified. Its stderr SHA-256 is
`5551f6995296ca5a74966ab47163296ffead3e5e5192116ae768f6f592783f0a`;
the process-result SHA-256 is
`17b3225fc27a6185b30be386acface30d0b83274b8079de42dfe0e9be22ec223`.

The executed driver was
`85456d09b4f4883c1240a86d0d693b8c07295259041888baf17647e6b5055761`.
Its unguarded context.close inside finally raised the native Firefox
Browser.removeBrowserContext `_maybeDontRestoreTabs` protocol error. This skipped
browser.close, ledger collection, source checking and final receipt serialization.
The same cleanup sequence existed in both driver branches. The underlying Firefox
protocol cause is unknown; no product or recorder cause is inferred.

The reviewer's bounded causal chain was: no receipt because teardown threw;
uncaught because teardown was outside the observation catch; evidence lost
because durability depended on cleanup success; both driver branches shared the
same failure mode. Further speculative causes would not change containment.

Hansei: successful observations and successful teardown are distinct obligations.
Kaizen: checkpoint original report/source/ledger before teardown, catch each close
independently, retain raw errors, and preserve original failure status. Both close
operations are attempted. Pre/post checkpoints survive any later outer-exit error;
such a process error remains unqualified rather than being converted to success.

The bounded correction is confined to the evidence driver. Offline healthy,
context-close-error and browser-close-error controls preserve the original
failure and both close attempts in `teardown-custody-control-r2/`. The unqualified
manifest-header cell was rerun alone before the two remaining Firefox stages;
the rerun and both stages returned full native receipts and normal teardown.
Accepted weather cases were not replayed. No browser rebuild, recorder change,
desktop access or production change was made.
