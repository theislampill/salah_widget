# Source evidence — continuation 2

The new candidate is a published all-sky integrated-starlight numerical product,
not the old HYG-only residual. It has NOT been downloaded into this workspace.
The JSON is a transcription of inspected publisher metadata, not the binary.

Inspected primary publisher resources:
- https://api.github.com/repos/TuSKan/astrogo/releases/tags/starmap-v2
- https://github.com/TuSKan/astrogo/blob/19ba61029f93d8ad7959de23bd03167d2c69c4de/skybrightness/dataset/starlight/open.go
- https://github.com/TuSKan/astrogo/blob/19ba61029f93d8ad7959de23bd03167d2c69c4de/LICENSE

The actual source hash must equal the recorded GitHub-published digest. A local
hash of a different dataset, an HTML error, or a made-up map is not sufficient.

The publisher's generic reader descriptions and writer header have different unit
wording. This is an outstanding conversion review, not a silently settled fact.
Single-band V processing is possible only after establishing the actual zero
point and whether values are passband averaged. Four columns are not full spectra.

The acquired validation workflow artifact had SHA-256
8015270ff7d63614058cc60fb66069a88462f33e44af3d05deec1e6caaa6bc61.
It contained logs and summary statistics, not the source map. Its external tests
are not claimed as tests of salah_widget. It is not used to build sky assets.

Separate finding: Stellarium's CREDITS.md at
608db95859f2393d5cc5067d90850ab2d7560c0c, section 4.4, records
credit-conditioned permission to modify/redistribute its specific older Mellinger
panorama. That does not establish a licence for every Mellinger product or its
radiometric calibration. No panorama was admitted or substituted here.
