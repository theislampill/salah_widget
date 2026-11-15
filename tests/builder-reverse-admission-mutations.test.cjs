'use strict';
// R0031 mutation controls (R31-10). Each mutant is a disposable in-memory edit of the generated builder.html or
// config.js applied inside builder-reverse-admission.test.cjs (R0031_MUTANT); nothing is written to disk. A mutant is
// killed only when its named discriminator fails (behaviour), never by a bootstrap or anchor error.
// Mutant (e) of the issue is `await-permission` (owner decision D-31-3 = A, issue 98 comment 6878230757).
const { test } = require('node:test');
const assert = require('node:assert/strict');
const { spawnSync } = require('node:child_process');
const path = require('node:path');

const suite = path.join(__dirname, 'builder-reverse-admission.test.cjs');
// The child is an independent runner: drop the parent runner's context so it reports its own results.
const { NODE_TEST_CONTEXT, ...baseEnv } = process.env;
const cases = {
  'drop-ok': 'R31-02 non-OK 429 with a well-formed EU body writes nothing',                 // (a)
  'else-4': 'R31-02 reply {} writes nothing (method stays 2)',                                // (b)
  'no-deadline': 'R31-04 a body pending past 8 s settles once at the deadline',              // (c)
  'local-request': 'R31-06 local mode: coordinate edits and builder GPS send no reverse request', // (d)
  'mode-epoch': 'R31-06 a mode change supersedes a pending portable lookup',
  'epoch-compare': 'R31-06 a portable → local → portable round trip supersedes the pending lookup',
  'epoch-bump': 'R31-06 a portable → local → portable round trip supersedes the pending lookup',
  'loose-continent': 'R31-03a malformed continentCode "na" leaves the method',
  'await-permission': 'R31-07 a never-settling permission query does not block a valid GPS fix',                 // (e)
  'retract-on-reject': 'R31-07 a rejected diagnostic is unknown and never retracts the fix',
  'diagnostic-unguarded': 'R31-07 a diagnostic settling after a newer location intent is not written',
  'publish-before-owner': 'R31-07 a fix arriving after a newer location intent is not published',
  'double-publish': 'R31-07 the diagnostic is read after publication and only reported',
  'class-only': 'R31-08 place preference selects the city for a category-keyed Springfield reply', // (f)
};
for (const [mutant, discriminator] of Object.entries(cases))
  test(`R31-10 mutant ${mutant} is killed by: ${discriminator}`, () => {
    const r = spawnSync(process.execPath, ['--test', '--test-reporter=tap', suite], { encoding: 'utf8', env: { ...baseEnv, R0031_MUTANT: mutant } });
    const out = r.stdout + r.stderr;
    assert.equal(r.status, 1, `${mutant} must fail the suite`);
    assert.doesNotMatch(out, /mutant anchor missing|unknown mutant/, 'mutant applied to the actual source');
    const failed = out.split(/\r?\n/).filter(line => /^\s*not ok \d+ - /.test(line)).map(line => line.replace(/^\s*not ok \d+ - /, ''));
    assert.ok(failed.some(name => name.startsWith(discriminator)), `${mutant} did not reach its discriminator; failed: ${failed.join(' | ')}`);
  });
test('R31-10 control: the unmutated suite passes', () => {
  const r = spawnSync(process.execPath, ['--test', '--test-reporter=tap', suite], { encoding: 'utf8', env: { ...baseEnv, R0031_MUTANT: '' } });
  assert.equal(r.status, 0, r.stdout.slice(-2000));
});
