# R0013: Repair Bash installer input, supported-shell and cached-path contracts

Live read: https://github.com/theislampill/salah_widget/issues/19
State: open; updated 2026-11-07T01:26:27Z

<!-- salah-widget-audit-20260907:SW-019 -->
# R0013: Repair Bash installer input, supported-shell and cached-path contracts

**Repository-local identity:** `R0013` in `theislampill/salah_widget`; existing tracker [#19](https://github.com/theislampill/salah_widget/issues/19). The SW identifier is historical draft provenance.


Campaign draft alias: SW-019. Product defect; proposed priority P1. This work order retains three accepted failures, VAL-003/006/007, under one existing Bash launch owner. It authorizes no implementation or external effect.

The advertised command must obtain answers from the person at the terminal, detect targets on the claimed Bash floor, and deliver one actual asset path to its caller. Today’s pinned evidence shows three breaks in that chain: script bytes become the menu answer, macOS detection requires an unavailable builtin, and cached download status contaminates the returned path. A successful helper exit or a printed “Done” did not establish installation.

## Bind the repair before editing

The evidence baseline is main `fd2972ba64225fe9d6848e92497e6d0ed20ea624`; candidate `9d9c43649748555afbe09e3ca49bc47db2d7e7bb` reproduced the same cases. The candidate is not a branch-adoption instruction. In the explicitly authorized future checkout run:

```text
git --no-optional-locks rev-parse --show-toplevel
git --no-optional-locks remote get-url origin
git --no-optional-locks status --short --branch
git --no-optional-locks rev-parse HEAD
git --no-optional-locks diff fd2972ba64225fe9d6848e92497e6d0ed20ea624 HEAD -- install.sh builder.html README.md
```

Confirm the `theislampill/salah_widget` target, read closer guidance, and preserve unrelated dirty work. Inspect relevant differences before using the pinned extraction ranges below. Stop if stdin handling, staging return types, target encoding or the generated command changed incompatibly; adapt the fixture to the actual named functions rather than attributing an old defect to arbitrary HEAD.

Exact owners: [install.sh initialization, output and detection](https://github.com/theislampill/salah_widget/blob/fd2972ba64225fe9d6848e92497e6d0ed20ea624/install.sh#L16-L246), [download and install callers](https://github.com/theislampill/salah_widget/blob/fd2972ba64225fe9d6848e92497e6d0ed20ea624/install.sh#L282-L427), [selection and terminal text](https://github.com/theislampill/salah_widget/blob/fd2972ba64225fe9d6848e92497e6d0ed20ea624/install.sh#L446-L502), [builder installCmd](https://github.com/theislampill/salah_widget/blob/fd2972ba64225fe9d6848e92497e6d0ed20ea624/builder.html#L344-L357), and [README invocation/manual boundary](https://github.com/theislampill/salah_widget/blob/fd2972ba64225fe9d6848e92497e6d0ed20ea624/README.md#L41-L68). [Candidate installer](https://github.com/theislampill/salah_widget/blob/9d9c43649748555afbe09e3ca49bc47db2d7e7bb/install.sh) is a comparison source only.

## Incident, causal chain and limits

1. README and `installCmd()` send downloaded program text through `bash` stdin. The line-464 `read` uses that same stream. In the saved controlled-source run it consumed the following assignment, producing `selection=<selection="${selection:-all}">`, exit 0. Running the identical excerpt through `bash -c` with `all\n` on stdin produced `selection=<all>`. An unrecognized selection matches no target at lines 474–477; the loop can finish and still print “Downloads and presets were staged”. The source also has four later interactive reads at 364/372/381/404, so fixing only the initial menu leaves the same ownership error downstream.
2. Darwin is admitted at line 55, but both profile branches call `mapfile`. The retained [Apple Bash 3.2 builtin source](https://github.com/apple-oss-distributions/bash/blob/51bf3fc6f26e9517c3a2e4bc3d208f9b39b87178/bash-3.2/builtins/Makefile.in) lacks it. The actual detector with inert profile helpers printed `detected` on Git Bash 5.3.9; disabling only `mapfile` exited 127. This identifies a required capability. It is not a native macOS installation or a complete emulation of Bash 3.2.
3. `download_tablissng_asset` checks its cached file, calls `ok`, prints the path and returns 0. `ok` writes stdout. The caller captures both lines through `path="$(...)"`; extraction and Firefox clipboard instructions consume that polluted value. The saved result was `<[OK] Already downloaded tabliss-chromium.zip\n/fixture/v1/tabliss-chromium.zip>`. No full installer, remote asset, browser or profile was exercised.

These are independent causal subcases. The good builder serializer, fixed 325×530 iframe and manual import boundary are retained controls, not evidence against the launch defects. URL encoding already kept quote/newline/command-substitution text inert; preserve it.

## Public RED fixture, without the private audit harness

Save the following as `red-bash.cjs` in a disposable fixture directory and run `node red-bash.cjs /absolute/path/to/the/pinned/install.sh`. It reads the source but executes only the named excerpts with inert effects; it never invokes installer top level. `BASH_EXE` may name the host Bash executable. Use the pinned source for the fixed ranges.

```js
const fs = require('fs'), cp = require('child_process');
const src = fs.readFileSync(process.argv[2], 'utf8').split(/\r?\n/);
const exact = (a,b) => src.slice(a-1,b).join('\n');
const bash = process.env.BASH_EXE || 'bash';
const run = (input,args=[]) => {
  const r=cp.spawnSync(bash,['--noprofile','--norc',...args],{input,encoding:'utf8'});
  return {exit:r.status,stdout:r.stdout,stderr:r.stderr};
};
const menu='set -Eeuo pipefail\n'+exact(464,465)+'\nprintf "selection=<%s>\\n" "$selection"\n';
console.log('source-on-stdin',run(menu));
console.log('answer-on-stdin',run('all\n',['-c',menu]));
const detector='set -Eeuo pipefail\n'+exact(215,246)+`
CONFIGS=("c|Chrome|chromium|fixture|chrome|new|old|store|manager|newtab")
find_exe(){ printf chrome; }
chromium_profiles(){ printf fixture; }
has_id_dir(){ return 1; }
add_target(){ printf 'detected\\n'; }
`;
console.log('builtin-present',run(detector+'detect_targets\n'));
console.log('builtin-disabled',run(detector+'enable -n mapfile\ndetect_targets\n'));
console.log('cache',run('set -Eeuo pipefail\n'+exact(40,40)+'\n'+exact(112,114)+'\n'+exact(282,304)+`
DOWNLOAD_ROOT=/fixture
DRY_RUN=0
select_asset(){ printf 'v1\\ttabliss-chromium.zip\\thttps://example.invalid/file\\n'; }
mkdir(){ :; }
curl(){ printf 'unexpected-network' >&2; return 99; }
[(){ if test "$1" = -f; then return 0; else builtin [ "$@"; fi; }
path="$(download_tablissng_asset chromium)"
printf 'captured=<%s>\\n' "$path"
`));
```

The RED oracles are the three exact outcomes above, with the `-c` and builtin-present positives. Keep the archived outputs as historical, not a new execution report. For GREEN use symbol-bounded extraction after range changes and separately exercise the real entry path; a fixture that only tests a new helper while old reads remain reachable cannot qualify this issue.

## Ordered repair and executable contracts

**A. Give interactive input one owner.** Preserve the pipe command by opening a dedicated readable controlling-terminal descriptor once, before staging or prompts. Use a fixed descriptor such as 3 for Bash 3.2 compatibility (`exec 3</dev/tty`, checked); route every human `read` through `-u 3`. Keep structured record reads (`IFS='|' read`, here-strings, release TSV) on their explicit data input. Print prompts on stderr. On unavailable terminal or EOF, emit an error and exit nonzero before installation effects; do not turn EOF into the default answer. A successful empty terminal line may retain default `all`/source 1. Close the descriptor at exit without interfering with the staging owner's cleanup.

This makes a tiny input helper warranted: the menu, source choice and three confirmation branches must all call it. It must return failure to the caller; callers may not swallow it and continue. Do not let it write answers to stdout where a path-returning caller could capture them. `read -r -u 3 variable` in the caller, or a helper using Bash `read`'s caller-scope variable behavior with distinct local names, is sufficient; no new CLI parser or dependency is needed.

**B. Validate target intent before effects.** Normalize whitespace, admit only `all` or comma-separated existing indices, reject a malformed/out-of-range token with a named diagnostic, and deduplicate valid repeated indices. Compute the selected set before downloads. Preserve the legacy-Tabliss skip rule. An empty detection set, invalid selection, EOF, or an all-legacy selection cannot claim staged completion. Track eligible targets and whether a preset/asset was actually produced; terminal text distinguishes “no eligible target”, “manual action pending”, and “files staged”. Pressing Enter is acknowledgment, not independent proof of extension installation.

**C. Replace both `mapfile` calls locally.** Reset `profiles=()` for each browser config, then use `while IFS= read -r p || [ -n "$p" ]; do profiles+=("$p"); done < <(chromium_profiles "$user_data")`, with the corresponding Firefox producer. The redirection keeps the loop in the current shell; `producer | while ...` would lose the populated array in a subshell. Retain the zero-profile fallback when an executable or user-data directory exists. Check native Bash 3.2 empty-array behavior under `set -u`, using a guarded iteration if necessary; do not globally relax `nounset`. Paths with spaces/Unicode/backslashes are single entries. The existing newline-delimited profile format cannot represent newline-bearing paths; disclose that retained limitation instead of claiming arbitrary-byte path support or replacing the whole target record format.

**D. Preserve the value/status boundary.** Make `ok` write stderr, then inspect actual command-substitution consumers (`find_exe`, `select_asset`, `download_tablissng_asset`, `expand_chromium_asset`, `download_preset`) for stray status output. Success from the download helper means stdout is exactly one newline-terminated absolute existing file path; failure is nonzero with no usable path. Cached and fresh calls return the same bytes. Retain quoting in extraction/copy/open callers. Cache policy and ownership remain with [R0015](https://github.com/theislampill/salah_widget/issues/21); this issue proves reuse of a valid owned cache entry, not trust in an old shared path.

**E. Integrate the generated command and actual entry.** Retain `URLSearchParams` serialization in `hash()` and `SALAH_WIDGET_HASH='encoded-value'` at the Bash process. README and builder should explain a terminal is required and retain review/download/file invocation. The visible command can remain `curl ... | bash` after input separation; qualify that exact shape under a pseudo-terminal with local script bytes and effect stubs. A file-only documentation workaround is a legitimate smaller fallback only if both public generators change and the old route fails clearly; it leaves copied historical pipe commands broken, so it is not the preferred repair.

## GREEN, controls and mutation matrix

| Case | Expected final behavior / discriminating control |
|---|---|
| Pipe + real PTY; answers `all`, `1,3`, empty line | Select the actual eligible set; all subsequent prompts read only PTY bytes. Effect stubs log expected selected targets. |
| No controlling terminal, EOF, `999`, `1,bad`, no targets | Nonzero, explicit reason, no staging/open/copy; no “files staged” success. |
| Targets 1/2/3; answer `1,1,3`; target 3 legacy | Target 1 reached once; target 3 explicitly refused; no legacy profile write. |
| Both browser families; zero/one/multiple profiles, `/fixture/Profile One`, `/fixture/مدينة`, trailing line without newline | Stable cardinality and exact path values on native Apple Bash 3.2 and modern Bash; empty-array nounset boundary included. |
| Fresh vs valid owned cached ZIP/XPI | Single existing path on stdout, diagnostics only stderr; cache hit makes zero asset fetches; extraction/copy receives byte-identical path. |
| Malicious label literal `a'"&\u0060$(x)\n<z>` through builder | Percent-encoded shell value and exact decode roundtrip; local mode omits coordinates; iframe remains 325×530 with original permission scope. |
| Mutants: restore one stdin read; restore `mapfile`; send cache status to stdout | Corresponding entry/host/path control fails separately. This prevents one corrected subcase masking two remaining failures. |

Use in-memory/effect-stubbed controls first. Native macOS evidence must come from actual `/bin/bash --version` plus detector and terminal entry execution on that host; disabling a builtin in a modern shell is insufficient. Do not open real profiles, install extensions or contact a live release in these controls.

## Integration, public effects and closure

[R0014](https://github.com/theislampill/salah_widget/issues/20) owns Windows parsing/selection. [R0015](https://github.com/theislampill/salah_widget/issues/21) owns safe staging and retention. [R0016](https://github.com/theislampill/salah_widget/issues/22) has the accepted qualification dependency on this launch contract and shares `bash/download-return`; its dry-run must not return a pretend existing path to extraction. Agree these interfaces before merging shared installer hunks, with one installer writer.

**Private-cache interface finalized for parent JOIN:** [R0015](https://github.com/theislampill/salah_widget/issues/21) supplies one newly created, verified private download root for an installer attempt. This owner calls `download_tablissng_asset` twice for the same selected fixture asset within that attempt: the first call creates the regular file, the second recognizes that same owned file, returns byte-identical single-path stdout and makes zero further asset downloads. Neither this test nor the helper adopts an earlier invocation’s predictable/shared path. A later invocation gets a different private root; the security owner deliberately retires automatic cross-run reuse of old shared caches and retains any user-facing manual bundle without treating it as a trusted new download cache. Thus same-attempt cache output/reuse is this owner’s invariant, while cross-run root admission/lifetime is the staging owner’s invariant. Disclose that compatibility behavior in README and integrated evidence. The parent owns the corresponding SW-021→SW-019 interface edge and exact path-creation hunk reconciliation; this text creates no independent graph mutation or whole-issue prerequisite. Shared docs/test insertion uses the designated integrator, not competing README rewrites.

IMPLEMENTAUDIT R001D applies to script, builder command and README as one public capability. Preserve preset configuration carry-through, 325×530 layout, geolocation permission, manual import and dashboard replacement warning. No auto-install, package-manager prerequisite, staging security redesign, or whole candidate adoption belongs here. Retaining Bash 3.2 via two loops is smaller than requiring Homebrew/new Bash; changing all stdout to a machine protocol or rewriting the installer would add unrelated compatibility risks.

Rollback each subcase with its matching command/docs/tests. Never leave the public terminal/shell claim stronger than the reverted script, and never restore unsafe staging as a convenience rollback. On partial success retain exact staged paths and state manual actions remain pending; do not remove prior user artifacts. Stop on incompatible drift, failed native floor, malformed return bytes or an unresolved staging/preview interface.

DONE requires final-tree RED→GREEN and the listed negative/mutation controls, the minimum-host/real-entry evidence claimed, independent exact-tree review where installer integration warrants it, and an evidence comment binding commit, commands, host versions, results and remaining limits. Any distribution claim also needs authorized raw-script and generated-command readback; local tests do not prove deployed bytes. Use non-closing `Implements #19` PR wording, then manual closure after evidence. Publishing this work order repairs no installer.

Methodology references (separate repository, not Salah work owners): [R001D in IMPLEMENTAUDIT](https://github.com/theislampill/IMPLEMENTAUDIT.md/issues/155).

Identity provenance: first repository-local allocation batch; existing GitHub object order was used to assign distinct monotonic hex-4 IDs. Closed/held IDs are not reused. Issue number is not implementation priority.


