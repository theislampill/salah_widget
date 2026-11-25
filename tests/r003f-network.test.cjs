'use strict';
const test = require('node:test'), assert = require('node:assert/strict');
const fs = require('node:fs'), os = require('node:os'), path = require('node:path');
const {spawnSync} = require('node:child_process');
const root = path.resolve(__dirname,'..');

// Exercise the recipe entry point with the existing fake Playwright transport.
// No network packet or image capture is needed to detect a routing escape.
for (const mutant of [false,true]) {
  test('R003F network ledger '+(mutant?'fails a continued foreign request':'blocks foreign requests before capture'), t=>{
    const temp=fs.mkdtempSync(path.join(os.tmpdir(),'r003f-net-'));
    t.after(()=>fs.rmSync(temp,{recursive:true,force:true}));
    const stub=path.join(temp,'pw.cjs'),logFile=path.join(temp,'calls.json');
    const requests=['https://api.aladhan.com/v1/timings/15-11-2026','https://external.test/path'];
    fs.writeFileSync(stub,`
      if (process.platform!=='win32') process.umask(0o022);
      const {create}=require(${JSON.stringify(require.resolve('./r0033-fake-playwright.cjs'))});
      const iso=require(${JSON.stringify(require.resolve('../tools/qa/r0033_isolation.cjs'))});
      const classify=iso.classify;
      if (${mutant}) iso.classify=(url,policy)=>url==='https://external.test/path'
        ? {action:'continue',why:'negative control',host:'external.test'} : classify(url,policy);
      const fake=create({requests:${JSON.stringify(requests.map(url=>({url}))) }},log=>require('node:fs').writeFileSync(${JSON.stringify(logFile)},JSON.stringify(log)));
      exports.chromium={launch:async options=>{
        const browser=await fake.chromium.launch(options),newContext=browser.newContext;
        browser.newContext=async options=>{
          const ctx=await newContext(options),newPage=ctx.newPage;
          ctx.newPage=async()=>{
            const page=await newPage();page.clock.setFixedTime=async()=>{};
            page.waitForFunction=async()=>{throw Error('synthetic end after request');};
            return page;
          };
          return ctx;
        };
        return browser;
      }};
    `);
    const out=path.join(temp,'receipt');
    const run=spawnSync(process.execPath,['tools/qa/r003f_owner_baseline.cjs','--root',root,'--out',out,
      '--playwright',stub,'--pngjs','node:assert'],{cwd:root,encoding:'utf8',timeout:15000});
    assert.equal(run.status,mutant?3:2,run.stderr+run.stdout);
    if (process.platform!=='win32') assert.equal(fs.statSync(out).mode & 0o077,0,'private receipt directory');
    const report=JSON.parse(fs.readFileSync(path.join(out,'summary.json')));
    assert.equal(report.isolation.allowedOffLoopback,mutant?1:0);
    const calls=JSON.parse(fs.readFileSync(logFile));
    assert.ok(calls.find(c=>c.call==='route'&&c.pattern==='**/*'&&c.pagesBefore===0));
    assert.ok(calls.find(c=>c.call==='routeWebSocket'&&c.pagesBefore===0));
    const decisions=calls.filter(c=>c.call==='disposition').map(c=>c.disposition);
    assert.deepEqual(decisions,['fulfill',mutant?'continue':'abort']);
    assert.equal(report.status,mutant?'ISOLATION FAIL':'INCOMPLETE');
  });
}
