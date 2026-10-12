'use strict';
// Bounded actual Credits RED/GREEN plus the unchanged accepted whole-README guard.
const fs = require('node:fs'), assert = require('node:assert/strict'), crypto = require('node:crypto'), vm = require('node:vm');
const input = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const digest = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
function exact(record) {
  const bytes = fs.readFileSync(record.path);
  assert.equal(bytes.length, record.bytes); assert.equal(digest(bytes), record.sha256);
  return bytes.toString('utf8');
}
const r1 = exact(input.r1Readme), successor = exact(input.successorReadme), accepted = exact(input.acceptedDisclosureReadme);
const guard = exact(input.guard), fixture = exact(input.currentFixture);
assert.equal(fixture.split(guard).length - 1, 1, 'existing strengthened guard must be present exactly once');
const blanketAssert = guard.split('\n').find(line => line.includes("'whole README retains an unsupported blanket privacy claim'"));
assert(blanketAssert, 'existing guard first assertion is required');
function credits(text) {
  const start = text.indexOf('\n## Credits\n'); assert(start >= 0);
  const end = text.indexOf('\n## ', start + 4); assert(end > start);
  return text.slice(start, end);
}
function privacy(text) {
  const start = text.indexOf('### Auto-detect, precise location & privacy'); assert(start >= 0);
  const end = text.indexOf('\n---', start); assert(end > start);
  return text.slice(start, end);
}
function creditsCheck(text) {
  const readme = credits(text);
  // Execute the accepted assertion without altering its regex/error semantics;
  // its input here is explicitly scoped to the actual Credits section.
  vm.runInNewContext(blanketAssert, {assert, readme});
  assert(readme.includes(input.acceptedCreditsClause), 'Credits must retain accepted browser settings/cache disclosure');
  assert(readme.includes(input.providerUncertainty), 'Credits must retain accepted provider-policy uncertainty');
}
async function wholeCheck(text) {
  let result;
  await vm.runInNewContext('(async () => {\n' + guard + '\n})()', {
    assert, sources: {'README.md': text},
    check(name, callback) { assert.equal(name, 'docs: README privacy whole-document storage consistency'); result = callback(); return result; }
  });
}
async function probe(label, text, run, expectedStatus, scope) {
  let status = 'PASS', error;
  try { await run(text); } catch (failure) { status = 'FAIL'; error = failure.message; }
  assert.equal(status, expectedStatus, label);
  if (status === 'FAIL') assert.equal(error, 'whole README retains an unsupported blanket privacy claim', label);
  console.log(JSON.stringify({label, status, ...(error ? {error} : {}), inputSha256:digest(Buffer.from(text)), scope,
                             delivered:false, wholeDocumentPASS:false}));
}
(async () => {
  const r2 = exact(input.r2Readme);
  await probe('actual-r1-Credits-RED-retained', r1, creditsCheck, 'FAIL', 'sealed r1 actual Credits');
  await probe('actual-r2-whole-README-RED-retained', r2, wholeCheck, 'FAIL', 'sealed r2 actual postimage; old coarse paragraph');
  await probe('actual-r3-Credits-GREEN', successor, creditsCheck, 'PASS', 'actual r3 proposed README Credits');
  await probe('actual-r3-whole-README-guard-GREEN', successor, wholeCheck, 'PASS', 'actual r3 proposed README; bounded existing contradiction guard');
  await probe('actual-r3-blanket-claim-outside-privacy-RED', successor + '\nControl: stores nothing about you.\n', wholeCheck, 'FAIL', 'negative control appended outside privacy section');
})().catch(error => { console.error(error.stack); process.exitCode = 1; });
