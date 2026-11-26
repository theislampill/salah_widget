# R003F WebKit served-document diagnostic

This packet prepares a separately identified WebKit DPR1 diagnostic of two
HTML resource hints. It does not change the product, the original B0 recipe,
the proxy policy, or an existing engine verdict. The hypothesis is that an
explicit preconnect hint may initiate browser activity outside ordinary page
request routing. Source inspection alone cannot establish that cause.

The only presentation input change is removal of two exact tag byte spans
before HTML parsing. This can affect resource scheduling, so every result from
this packet belongs to an altered-input diagnostic. It supplies no production
qualification, original-B0 qualification, full-matrix acceptance, or human
judgment. The original failures and owner-reserved decisions remain in force.

## Exact input and source boundary

| Input | SHA-256 | Bytes |
| --- | --- | ---: |
| Original runtime `index.html` | `88411488017ea590e6b4c5a21adc143977c0907089eabb80b0cbe8f0ba18a8a1` | 1,692,708 |
| Derived document served in memory | `16a0f207412572751609316186d5b1f64ee9b31987b9ec6f47c293c9280754b7` | 1,692,581 |

The removed spans are the 59-byte
`<link rel="preconnect" href="https://fonts.googleapis.com">` tag at byte 159
and the 68-byte
`<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>` tag at
byte 219. Both offsets refer to the original bytes. The materializer requires
the full original digest, size and one exact occurrence of each tag. It removes
the spans in reverse offset order and verifies the independently fixed derived
digest. Every other byte, including whitespace, stylesheet links and scripts,
remains identical. The runtime file on disk is never overwritten.

`r003f_preconnect_materialize.cjs` first verifies the pinned corrected-B0
materializer, UI helper and new input helper before importing them. The base
materializer verifies its seven original input files. Its deterministic receipt
must have SHA-256
`fab2e2ad49a14eee2ba715fb75365fa4b0abfa48a1d8b60247343ad29b1021e5`.
The new materialization embeds that complete receipt and records each new
driver patch's exact preimage and postimage digest.

The output closure contains eight source files: the original corrected-B0
seven-file closure, with a narrowly derived owner driver, plus the new input
helper. No product assets are copied. All corrected capture-helper, UI-helper,
physical-predicate, proxy and Node-guard bytes are unchanged. The complete
corrected `capture()` function and original catch/finally tail in the derived
driver are also byte-identical. The new receipt has its own deterministic
digest, which a trusted caller must supply independently to `admitClosure`.
That admission rereads every declared output and rejects additional files,
missing files, byte drift and symlinks.

Example source preparation, using existing local inputs and a fresh output
directory outside both source and runtime:

```sh
node tools/qa/hosted-native/r003f_preconnect_materialize.cjs \
  --source /path/to/research-source \
  --runtime /path/to/prepared-runtime \
  --out /path/to/fresh-preconnect-source
```

This command performs no native observation or dependency acquisition. It
removes only its own temporary or partial output on failure. It refuses an
existing destination and does not modify the input checkout.

## Serving and evidence

The derived driver supplies the input helper's callback to the existing
`makeServer(root, indexFor)` function. The helper wraps that server's sole
request listener to refuse every noncanonical request resolving to the runtime
index, including encoded aliases and query forms, before any index bytes are
served. Exactly `/index.html` can reach the callback. The original handler
continues serving all other assets, with its existing MIME and path checks.
The callback accepts only B0 and at most two document requests. A rejected or
late third request makes the referenced document evidence incomplete.

The original offset/B0/B0-repeat/reference sequence still opens two documents
under the original fixed clock, scene, reduced-motion setting and viewport.
Only WebKit DPR1 is supported; another engine or DPR is refused before browser
package import. Before that import the driver also checks its external source
digest and the original runtime index. No script removes tags after parsing.

For each successful original `goto`, the helper reads the actual response
body, HTTP status, MIME and URL. It records the observed body digest and size,
then retains the body in a fresh private file before checking its identity.
The two bounded files are `document-input/document-01.html` and
`document-input/document-02.html`. A response must be HTTP 200, exactly
`text/html`, at the expected loopback document URL, and have the exact derived
bytes. Both documents must use the same origin.

The output parent must already exist. Before original driver setup, the helper
checks the output's canonical location against the actual runtime and refuses
symbolic links or non-directory components anywhere in its ancestry. Only the
final output directory may be absent at that boundary. It repeats the ancestry
check before retaining each response body and during final evidence admission,
so a later parent substitution cannot redirect a write or rebind a readback to
the same bytes through an alias. These checks do not create or move directories.

Wrong but bounded bodies remain available for diagnosis. An oversized body
records its observed digest and size plus a retention-limit failure; it does
not claim that a body file exists. Navigation, response-read and file-write
errors retain the fields actually obtained and leave unavailable fields absent.
There are no placeholder bodies or fabricated response records. The response
population is bounded at two, and rejected document request counting saturates
at three. Completion rereads both retained files and the original runtime
index. A missing, changed or symlinked retained body prevents completion.

Reading and retaining the response bodies adds diagnostic work. Neither source
controls nor a future instrumented observation calibrate that overhead or
establish a cross-machine performance comparison.

## Result and failure identity

| Object | Identity |
| --- | --- |
| Source materialization | `R003F/preconnect-input-source/1` |
| Document evidence | `R003F/preconnect-served-input/1` |
| Driver report | `R003F/P1/B0-preconnect-input/1` |
| Harness | `R003F/preconnect-input-harness/1` |
| Completed diagnostic status | `OBSERVED_PRECONNECT_INPUT_DIAGNOSTIC` |
| Qualification class | `ALTERED_INPUT_DIAGNOSTIC_ONLY` |

The report retains the original disk index digest separately from the served
document identity. `originalRecipeStatus: MEASURED` is written only after every
original measurement assertion and both document admissions complete. It
records that sequence of assertions; it does not convert the altered document
into original-input evidence. Native acceptance remains `NOT_EVALUATED` and
human acceptance remains `OUTSTANDING`.

Original raw PNG retention, scene/light/UI checks, Andon handling, browser
cleanup and final strict isolation precedence remain unchanged. A locally
refused external attempt still fails isolation. There is no new proxy or font
allowlist, sandbox flag, browser preference, renderer setting or fixture policy.
A provisional diagnostic label cannot override incomplete document evidence,
the actual outer process, a timeout, missing final evidence, a cleanup error,
an isolation failure or an original Andon. If original cleanup fails before
writing a terminal report, a caller must retain the available partial evidence
and classify the observation as incomplete; it must not manufacture a report.

The served-document object stays referenced by the report, so a late callback
failure is retained even after an earlier completion check. Final intake must
read the terminal report after the actual process ends and independently call
`admitEvidence` against the retained raw documents. A success string alone is
insufficient. Existing generic corrected-B0 and matrix paths do not admit the
new source, report or status identity.

## Required integration boundary

This source packet adds no hosted selector, workflow, coordinator or dispatch
route. A later central integration requires independent exact-tree review. It
must use a distinct lane/result kind and must bind preparation and final intake
to the actual expected entry and child-process receipts, current source closure
and independently acquired Node, Python, Playwright and PNGJS locations. It
must check those runtime bindings before evaluating a derived verifier.

Native preparation must retain its original hosted protocol and bound original
namespace/browser evidence. A local source-only preparation cannot be promoted
by adding a current lane receipt. Current admission must be recomputed from
the actual expected receipt paths and equal the complete copied plan admission;
copied metadata cannot supply its own expected paths or executable identity.
The trusted central caller must validate the new source and external expected
materialization digest before executing the derived driver. The driver's
self-check is an additional check, not a trust root.

Final intake must reread the exact original and served-document identities,
the complete source closure and terminal document evidence, and preserve the
strict original isolation, Andon, timeout and outer-process ordering. Missing
or failed optional preparation must block this lane without fallback. The
engineering envelope must sum common and optional preparation, source checks,
the existing 900-second B0 acquisition bound, namespace checks, final intake,
and workflow acquisition/sealing overhead. No budget or acceptance waiver is
introduced by this packet.

Original B0 baseline/discriminator prerequisites, complete-eight replay,
software-backend evidence and owner rules remain separate obligations. A
future clean diagnostic can support a bounded resource-hint hypothesis; it
cannot relabel an original failure or establish causal attribution by itself.

## Source verification

The registered command `hosted-native-r003f-preconnect-source-controls` contains
28 source controls. They cover exact byte transformation, complete output
closure, original code preservation, actual local HTTP delivery and alias
refusal, retained-response replay, malformed/missing/late evidence, file faults,
and rejection of unsupported engine/DPR before browser import. Output-alias
controls cover initial parent/root links, substitution before a body write,
late same-byte readback aliases and a valid fresh canonical output. HTTP tests use
Node loopback only; response doubles are explicitly synthetic. No browser is
launched and no native, sandbox, visual, human or product verdict is inferred.

```sh
python tools/cp9/run_native_regressions.py \
  --output /path/to/fresh-controls \
  --select native-runner-contract hosted-native-r003f-preconnect-source-controls
```

The registry command count and input closure are updated with this packet.
All existing commands, expected counts and declared failures are preserved.
