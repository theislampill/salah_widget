"use strict";
// R000F (issue #15, increment ES0F-01..16): draft / canonical output / issued preview publication.
// Executes the actual generated builder.html handlers and config.js serializer (VM doubles; no network).
// Source evidence only: counts iframe src assignments, not native navigations or widget readiness.
const {test}=require("node:test");
const {S,loader}=require("./builder-preview-publication-fixture.cjs");
const mk=loader();
const cases=[
  ["ES0F-01 one initial navigation; equal-coordinate coarse result adds none","initial"],
  ["ES0F-01 equivalent input/change pairs issue no navigation or revision","inputChangePair"],
  ["ES0F-02 each actual change issues exactly one navigation with correct output","changedOnce"],
  ["ES0F-05 canonically equivalent raw spellings do not restart","equivalentSpellings"],
  ["ES0F-03 mode switches publish once; local-mode location edits and active re-click do not","localMode"],
  ["rapid typing navigates only for distinct outputs, in order, ending at the draft","rapid"],
  ["ES0F-04/11/14 issued record equals what the iframe received; no cachebuster or readiness","issuedIdentity"],
  ["ES0F-06 D1 invalid draft keeps preview and export; Copy/Install/Open refuse","invalidDraft"],
  ["ES0F-05 D2 provenance-only change updates draft without navigation","provenance"],
  ["ES0F-13 D3 Refresh re-issues the last issued preview once, never the invalid draft","refresh"],
  ["ES0F-14 throwing src assignment is not recorded; export current; retry navigates","assignmentFailure"],
  ["ES0F-07/08 stale and A-B-A lookups cannot publish even when equal-valued","staleLookup"],
  ["ES0F-09 candidate cycling retained; identical-identity candidate adds no navigation","cycling"],
  ["ES0F-12 pending copy recovery keeps captured bytes; later success copies current output","pendingCopy"],
  ["ES0F-15 325x530 wrapper, local-only geolocation, focus preserved","invariants"],
];
for(const [name,key]of cases)test("R000F publication: "+name,()=>S[key](mk));
module.exports={cases};
