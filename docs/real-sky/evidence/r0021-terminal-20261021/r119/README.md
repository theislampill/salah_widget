# r119: stable owner callbacks

The refined compositor, preview compositor and solar-mask publication owner now reuse owner/prototype handlers on unchanged work. The existing preparation/capture records carry per-publication context. The exact encoder helper is initialized once with its immutable table. No additional science, UI, asset, quality-gate or currentness change is included.

The new context regression failed before the correction. The final affected suites pass **77 tests**, including cancellation, reentrant publication and failure-context controls; the exact encoder passes **seven controls**. [Original and projected receipts](../PUBLICATION.json) retain the baseline and RED result. Two canonical builds produce the same [142-file runtime](RUNTIME.json), `3e18b2fa83d0cbfce0a4360d789f7927aef5c064f963e8c18acb430507995821`; 136 entries are inherited unchanged.

[Independent source/build review](../reviews/owner-callback-r119-source-review-r1.json) found no blocking finding. This is source/build qualification only. Actual callback cost, native decode settlement/resources and affected native transitions remain open in the [finite ledger](../../../R0021_POST_QUOTA_LEDGER.md).

Reproduce from the repository root using its existing Node toolchain:

```text
node --test tests/real-sky/native-solar-publication.test.mjs tests/real-sky/native-host-composition.test.mjs tests/real-sky/native-preview-host.test.mjs tests/real-sky/native-lifecycle.test.mjs tests/real-sky/native-preservation.test.mjs
node --test tests/real-sky/native-encoding.test.mjs tests/real-sky/native-host-encoding.test.mjs
python tools/build_native.py
```

Build outputs are generated; change their authored owners only. This nondeploying checkpoint is not merge-ready.
