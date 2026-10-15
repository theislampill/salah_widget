# Evidence publication

This evidence branch never deploys or merges into main. Raw originals are kept
locally. `payload-manifest.json` maps every original path, byte count and SHA-256
to its published path, byte count and SHA-256. JSON larger than 1MB is published
as deterministic gzip (`mtime=0`); `gzip.decompress` recovers the original bytes.
Logical raw references inside receipts retain their original names.

For example, `matrix/<case>/results.json` may resolve through the manifest to
`matrix/<case>/results.json.gz`. Verify the published hash before decompression,
then verify the original hash and size. PNGs and source fixtures are unmodified.
The publication manifest excludes its own hash and later readback receipts.
Final reviews and delivery readbacks are additive publications, not rewrites of
the immutable qualification packet.
