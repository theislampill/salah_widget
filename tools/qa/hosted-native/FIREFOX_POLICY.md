# Firefox managed-policy diagnostic

This source packet defines a separate, opt-in research observation. It is not
selected by the checked-in campaign and has **no native result at source freeze**.
The earlier Firefox isolation failure and missing refined capture remain intact.
An effective policy observation cannot promote that earlier run, qualify a Moon
capture, or establish why a background request occurred.

## Question and primary sources

The question is narrow: before launching a disposable, already acquired managed
Firefox, can the diagnostic install the exact per-installation
`DisableAppUpdate: true` policy, observe Firefox reporting that policy as active,
and complete a bounded ordinary-clock dwell with the original strict isolation
verdict intact?

Mozilla documents `DisableAppUpdate` as an application-update policy, including
manual and automatic application updating. It does not establish the cause of an
unattributed request or promise suppression of every browser service:

- [DisableAppUpdate](https://firefox-admin-docs.mozilla.org/reference/policies/disableappupdate/)
- [Firefox update design: disabling updates](https://firefox-source-docs.mozilla.org/toolkit/mozapps/update/docs/HowToDisable.html)

Mozilla's Linux per-installation location is `distribution/policies.json` within
the Firefox installation. Its configuration guide directs administrators to
check applied policies in `about:policies`. This recipe uses that installation
location exclusively; it writes no system or user-wide policy:

- [Customizing Firefox using policies.json](https://support.mozilla.org/en-US/kb/customizing-firefox-using-policiesjson?mobile=0)
- [Policy configuration and verification](https://firefox-admin-docs.mozilla.org/guides/policies-configuration/)

Current upstream source handles `DisableAppUpdate` in `onBeforeAddons` and
disallows the `appUpdate` feature. Current `about:policies` markup contains the
active and error table bodies used by this bounded DOM reader. These are source
design references, not evidence about the installed managed binary. The actual
page must satisfy the contract; incompatible markup or inaccessible privileged
content produces `INCOMPLETE`:

- [Enterprise policy implementation](https://searchfox.org/firefox-main/source/browser/components/enterprisepolicies/Policies.sys.mjs)
- [about:policies markup](https://raw.githubusercontent.com/mozilla-firefox/firefox/main/browser/components/enterprisepolicies/content/aboutPolicies.html)

`BackgroundAppUpdate` is documented as Windows-only and is not included in this
Linux recipe: [policy reference](https://firefox-admin-docs.mozilla.org/reference/policies/backgroundappupdate/).

## Custody and ordering

The entry requires the current hosted task's actual `runtime.json`,
`capture/acquisition-identity.json`, and current namespace isolation receipt.
The invoking Node path must equal the independently acquired runtime. Module
paths, browser-cache location, installed package versions, original and installed
lock files, the managed Firefox descriptor, and the recorded executable population
must agree. A complete current file population of the installed Playwright,
Playwright Core and PNG packages is retained and compared before and after use.
That current population is distinguished from the acquisition record's existing
version, descriptor, lock and executable evidence.

Before any output, policy or browser creation, the entry requires the original
successful kernel/browser isolation evidence and the same current nonroot
UID/GID, network namespace, empty supplementary groups, zero capabilities and
no-new-privileges state. It binds the original browser control body to its
retained sibling and streams. That original boundary control is Chromium; it is
not represented as a Firefox-specific external navigation test.

Only the task-owned acquired Firefox installation may receive the policy. Any
existing policy file, symlink, changed source/package/executable, or process
currently using the installation blocks creation. Other regular distribution
files are preserved. The new file is created exclusively with these exact UTF-8
bytes, including the trailing newline:

```json
{"policies":{"DisableAppUpdate":true}}
```

The file is installed before **this diagnostic launch**. Neither absence of a
live process nor the file's creation proves that the installation was never
started historically. `historicalFirstStartup` remains `NOT_ESTABLISHED` in the
receipt. Future hosted integration must place this entry before the first
Firefox startup in its fresh acquisition flow if it needs that stronger ordering
claim. The pre-existing Chromium boundary does not establish a Firefox startup.

The original `r0033_isolation.cjs` launcher and `v1_net_guard.cjs` remain unchanged.
Their exact bytes are in the independently pinned source manifest. Firefox gets
the same refusing proxy, preferences, arguments, service-worker restriction,
catch-all HTTP route and WebSocket route. Only an explicit 45-second launch
deadline is added. The entry refuses sandbox-disabling overrides in its current
environment and preserves the original empty direct Firefox argument list.
No request is allowed externally for diagnostic purposes.

The actual Firefox launch options, reported version, acquired executable hashes,
observed process IDs/start ticks/command lines and current namespace identities
remain private evidence. The directly owned Firefox root must match the current
UID/GID and namespaces. Observed installation descendants are retained; this is
not an exhaustive content-process sandbox certification.

Each bounded process census is retained before owner admission, including its
entry/candidate counts, observed executable paths, partial candidate identities
and read-failure phase/code. Permission errors are not silently discarded. A
nontransient read failure, overflow, unidentified installation candidate, or zero
or multiple owned roots is incomplete. An unreadable prelaunch census cannot
establish that the installation is unused. A vanished process is recorded as a
transient read; no cause is inferred from another browser's failed census.

## Effective readback and lifecycle

One guarded context opens a genuine `about:policies` page. Initial and final DOM
readbacks require exactly one active row, `DisableAppUpdate` with Boolean text
`true`, no error rows, no visible inactive/no-policy message, a complete document,
the exact page URL and no collection overflow. The helper reads the actual DOM;
it never derives effective state from the policy file. The bounded collector
retains row/cell counts and overflow rather than silently dropping extra content.

The two readbacks surround a complete 60-second ordinary timer dwell. Their
ordering and dwell duration use one driver monotonic clock. There is no Date
replacement, clock acceleration, performance comparison, cross-process clock
subtraction, GC inference or claim that a request could never occur later.

Browser disconnect, context close, page close, page crash and page errors are
bound as their owners are acquired, before subsequent setup awaits. Unexpected
closure remains a fault even if cleanup is requested later. A failed navigation
retains its obtained ledger, page faults, policy and original setup error.
Cleanup failure is recorded separately. The original launcher cannot return its
private proxy ledger when launch itself fails; that limitation is recorded as
unconfirmed session/proxy cleanup and cannot become an admitted observation.

The parent records a genuine child process with argv, cwd, PID, exit/signal,
timeout, duration and separate retained streams. It re-reads the final source,
acquisition, policy and current namespace, recomputes the original strict
network verdict from the retained ledger, and checks that tracked Firefox
processes have ceased. Missing or malformed outer completion cannot promote an
inner success label. Namespace teardown remains the enclosing final process
fence, including an incomplete launch with no returned session handle.

## Bounds and outcomes

The child has a 270-second hard deadline. Its documented phase allowances sum to
240 seconds: source/policy 30, launch 45, context and page 20, navigation 20,
initial readback 10, ordinary dwell 60, final readback 10, cleanup 30 and final
currentness 15. The remaining 30 seconds cover settlement and overhead. A parent
allocation includes initial admission 30, child 270, termination grace 4 and final
intake 16, totaling 320 seconds. **Future callers must place the entire entry
under a real 330-second outer process bound**, then add the existing namespace
control and teardown allowance to their selected campaign budget. Synchronous
filesystem work is bounded by that outer process, not by a fictional JS timer.
No original B0 capture wait or default campaign budget is changed by this packet.

| Result | Required interpretation |
| --- | --- |
| `OBSERVED_FIREFOX_POLICY`, exit 0 | This exact diagnostic obtained effective policy readback, full bounded dwell, original strict network verdict, current custody and cleanup. Product/native visual acceptance is not evaluated. |
| `ISOLATION_FAIL`, exit 86 | Current isolation admission failed, or the original strict ledger/Node guard failed. Subsequent native work must stop. Every blocked proxy attempt still fails; none is waived. |
| `INCOMPLETE`, exit 2 | Setup, DOM, source, package, process, time bound, retention, currentness or cleanup was incomplete. There is no fallback observation. |

Isolation failure takes precedence over another setup/cleanup error. Otherwise,
an outer timeout or malformed/nonzero process result prevents an observation
even when a retained inner body looks complete. Fault and DOM bounds are
operational retention controls, not new product acceptance thresholds.

The source manifest records exactly eight public leaves and requires an
independently supplied SHA-256. It does not authenticate its own replacement.
Future root integration must pin the independently reviewed manifest digest and
review the resulting exact coordinator tree before activation.

## Recipe and source-only verification

The future entry, run inside the existing isolated namespace, is:

```text
<acquired-node> tools/qa/hosted-native/firefox_policy_probe.cjs
  --task <current-task>
  --out <current-task>/capture/firefox-policy
  --isolation <current-task>/capture/isolation/<current-lane>/receipt.json
  --pins-sha256 <independently-reviewed-firefox-policy-pins-sha256>
```

`SALAH_HOSTED_NATIVE_ISOLATION_RECEIPT`, `NODE_PATH` and
`PLAYWRIGHT_BROWSERS_PATH` must already bind the same current task and acquired
runtime. Output must be fresh. The internal child mode is not an alternative
admission route; an observation requires the actual parent process receipt and
final intake.

The registered source controls use synthetic installation files, DOM records,
browser/process doubles and small actual Node-only process controls. They never
launch Firefox or turn synthetic acquisition data into native evidence. They
exercise positive flow plus package/binary/policy drift, exclusive creation,
false/incomplete effective state, early setup evidence, late faults, original
network precedence, current isolation rejection and bounded process completion.

Following a successful policy observation, the original B0/refined capture and
other affected workstream observations remain required. A causal attribution
would need a separately reviewed comparison; this diagnostic makes none.
