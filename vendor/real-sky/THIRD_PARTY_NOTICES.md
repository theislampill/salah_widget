# Third-party attribution — current cumulative successor

**Catalogue:** David Nash / Astronexus, HYG4.0, CC BY-SA4.0. Full authenticated source is included as deterministic gzip. See LICENSE-DATA.md and provenance/hyg-primary-acquisition.json. Recovered4.1 secondary-name aliases are separately marked unofficial; they are NOT the complete4.1 database.

**Regions:** Nancy G. Roman1987, Identification of a Constellation from a Position, CDS VI/42. Exact Astropy-carried table and names are in upstream/. The Astropy BSD-3-clause licence is preserved as upstream/ASTROPY_LICENSE.rst, copyright2011–2026 Astropy Developers. Three spelling corrections occur only in derived metadata; raw source bytes are unchanged. Partition edges and areas are generated derivatives of the table.

**Pattern annotations:** Stellarium team, Western sky culture v0.22.2. Preserve upstream/stellarium-western-info.ini's notice: CC BY-SA4.0 International Public License + Free Art License. Only line geometry and identifiers are included; NO sky-culture artwork, images or fonts. Derived pattern data preserves upstream attribution and terms; independent implementation code is MIT. Big/Little Dipper annotations subset these lines; Summer/Winter Triangle annotations retain independently authored CP1 paths. Stick figures are not an official IAU prescription or a physical structure.

**Methods and tools:** Primary method references remain in docs/RESEARCH.md and provenance/sources.json. Swiss Ephemeris is a separately installed verification tool, not redistributed runtime code. Fixtures and their newly authored generators are included. Playwright and Chromium were test tools; browser captures use system fonts. No font files are distributed. Historical CP1/CP2 notices are retained in history/ and do not describe current runtime selections.

## Checkpoint 5 spectral and colour assets
IRAF/NOAO legacy spectrophotometric standards HR7001, HR3982, HR4534: see
vendor/spectral/IRAF-LICENSE.txt. The 29-band data are described as sources
transformed to the Hayes–Latham system, unpublished, in IRAF onedstds/README.
They are not newly acquired CALSPEC spectra. Exact full small data files were
Git-blob verified. HR4534 is retained for review but rejected by the builder.

CIE 1931 numeric 5 nm table extracted from Mitsuba3 source (95 XYZ triples):
see vendor/spectral/MITSUBA-LICENSE.txt. Original scientific table is CIE 1931
2-degree observer, CIE 018:2019 Table 6. Retained source slice is pinned, not a
claim to have recovered or verified the full upstream C++ blob or official CSV.

Bessell B/V numeric passband slices via Speclite: see
vendor/spectral/SPECLITE-LICENSE.txt, Bessell (1990), PASP 102, 1181,
doi:10.1086/132749. Reference responses are not instrument calibrations.
All acquisition records and local digests: provenance/cp5-spectral-acquisition.json.
HYG-derived spectral assignments remain under the existing HYG CC BY-SA 4.0 terms.


## CP6 model methods and numerical fixtures

The new CP6 source is an independent implementation of cited physical equations and empirical fits. See `provenance/cp6-model-sources.json` for authors, URLs, limited numerical coefficients/validation facts and explicitly non-original extensions. Whole papers, pbrt source, Swiss Ephemeris implementation/data and font files are not included. Independently generated numerical ephemeris comparison fixtures do not make the reference library a runtime dependency; regenerating them requires that separately acquired library under its applicable terms. Existing source-data and code licences above remain in force. No endorsement or measured local weather is implied.

## CP7 partial diagnostic assets
The finite-source partition and map tiers are HYG4.0-derived CC BY-SA 4.0 data, with David Nash / Astronexus attribution. They are not Pioneer, Mellinger, GAMBONS or an acquired diffuse survey. New source-independent implementation code is under the inherited code licence. NumPy is an external build/test dependency, not redistributed. No paper illustrations or font files are included.

## CP7 admitted numerical integrated-starlight source

Rener Castro / TuSKan, astrogo `starmap-v2`, source commit
19ba61029f93d8ad7959de23bd03167d2c69c4de. MIT notice retained in
`provenance/cp7/admitted/ASTROGO-LICENSE.txt`. Actual release bytes are retained
under `upstream/cp7/`. Credit ESA/Gaia/DPAC, ESA Hipparcos, Gaia@AIP and the
Bright Star Catalogue; see `docs/cp7/SOURCE_QUALIFICATION.md` for source terms,
transformations and limitations. HYG-dependent exclusion/derived assets retain
David Nash / Astronexus CC-BY-SA-4.0 attribution; original licences are unchanged.

## Checkpoint 7.4 integration additions

No additional astronomical dataset or third-party runtime library was introduced.
The existing Gaia/Hipparcos V source, HYG-linked exclusion provenance and attribution
requirements remain unchanged. New binding, direct transport, composition, tests and
viewer code use the package's existing implementation licence. The portable SHA-256
implementation is checked against Node crypto; its standard and primary transport
references are listed in `provenance/cp74/model-references.json`. Referencing pbrt does
not distribute its illustrations or chapter text. The demonstration's residual-night
value and effective within-V Vega weighting are assumptions, not newly acquired data.


## Checkpoint 7.5 additions
No new third-party astronomical data, fonts or vendored software was introduced. Existing licences and attributions remain unchanged. Newly authored asset/worker/verification code follows the package implementation licence. Platform documentation consulted is identified separately in `checkpoints/cp75/ENGINEERING_REFERENCES.md`. The runtime integrity manifest is not an upstream signature or a new redistribution licence.
