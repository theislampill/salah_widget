# Independent review — Windows native-file identity correction

Disposition: PASS for this bounded diagnostic correction and its exact carrier pins; native execution remains required. Root reviewed the sole function delta against published cda4c6b29e8f9f2d202c0c4469a8712a74725228. This is independent of the scratch author; root did not author the proposed implementation.

## Exact reviewed inputs

- Diagnostic: 57115 bytes / SHA256 08ddd40bbdafe82cdc25bb074ee2da6b9e9ef78004d744c3daf00ea8ca06cbd5.
- Outer route: 29241 bytes / SHA256 e7abb7b6c4631f7b25a035e68c3755a68fcb0e32d34a9afc65507ceee3b87454.
- Author packet manifest: 568e9a748502615d6fd8aacba67990beddd37d16d08e02d5a5972c11bad9db9c; all 97 payloads independently checked for length and digest.
- Author report: a12544610112bfaed1d326f9b497e90fd44cee07547fc3aba9fe137bb3dad6df.

## Evidence and reasoning

The original PS5.1 run43150783894 is still FAIL. Its first actual-file assembly journal records Microsoft.Net versus Microsoft.NET, matching length586752 and SHA da18597950c115efe569dcd8f7e379704a5ee002a1f0a10421ba269deb360183. That record did not observe physical identities and is not retroactively accepted. The fresh diagnostic must establish those identities on the native filesystem.

The correction retains raw child/parent facts and their differences. It requires the exact fact schema, regular absolute paths without symlink/reparse ancestors, actual canonical resolution on both spellings, stable nonzero inode identity with the same device, and unchanged full recorded metadata before/after fresh content reads. Child length and hash must match the canonical fresh parent fact. Merely equal bytes, a lowercase path, or an arbitrary hardlink alias cannot satisfy the conjunction. Any failure still writes the journal before raising.

No lifecycle snapshot field, source-entry predicate, environment proof, guard, exit-code oracle, readiness boundary or cleanup rule changes. Root checked the full function diff and surrounding call context. The outer delta changes only the diagnostic length/digest and author-manifest pin. All21 outer function/class ASTs are unchanged; all eight actual input pins independently match the proposed/published bytes. No workflow, installer or dependency interface is changed.

## Executed verification

Root reran the author's 17 owned-filesystem/inert controls: terminal0, all17 passed. The controls include real canonical resolution; identical bytes in distinct case-sensitive files; distinct hardlink names; links; malformed facts; content races; and same-byte inode replacement. Historical baseline failures remain in the author packet.

Root separately wrote and ran four controls using only the exact selected receiver/fact functions, owned fixtures and explicit inert stat observations: zero inode refusal, reparse-ancestor refusal, mode change during the read refused, and healthy stable file acceptance after the failed attempt. All four passed, terminal0. Each retained exact journal and correct match flag. No PowerShell, installer or archived main was executed by these controls.

The independent scripts, raw journals and verification.json remain in root-windows-native-file-review. Their hashes are bound below. Unavailable Windows identity or any further PS5.1 fact discrepancy must fail; success on Linux owned fixtures is not native Windows qualification. Next step: publish these exact two inputs together, execute the existing source-free two-host route, and receive all originals. Full-entry qualification remains separately open.

Evidence independent_controls.py: 8320e6af435a151f6ba625fe48e3a71bea37e7c74b94128a38174985b54af0ce

Evidence verification.json: 5e454495b4a63f51141945758a5e7d3d4a237c8d001f6ff35c4b47d1c95fac72

Evidence static-verification.json: f813e56f77d145b525ab20e6d920023eafc5d294f9fd5ebc8c454580fa0dd427

Evidence results.json: 0f5eea3440dc04bdc26454ce0ca8e176753a9b5adad7386564c0ec6cf17f0a7d
