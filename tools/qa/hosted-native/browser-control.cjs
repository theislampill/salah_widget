'use strict';
// Deliberately has NO route stubs, proxy or DNS override. The kernel namespace
// must permit a real loopback marker and refuse a real TEST-NET navigation.
const fs = require('node:fs'), http = require('node:http'), crypto = require('node:crypto');
const assert = require('node:assert/strict');
const [playwright, output] = process.argv.slice(2);
const digest = async file => {
  const hash=crypto.createHash('sha256');
  for await (const chunk of fs.createReadStream(file)) hash.update(chunk);
  return hash.digest('hex');
};
async function main() {
  assert.ok(process.getuid() > 0);
  const marker = crypto.randomBytes(24).toString('hex');
  let hits = 0, browser;
  const server = http.createServer((req, res) => { hits++; res.end(marker); });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const report = {protocol:'salah-hosted-browser-boundary/1', passed:false, chromiumSandbox:true,
    netns:fs.readlinkSync('/proc/self/ns/net'), uid:process.getuid()};
  try {
    browser = await require(playwright).chromium.launch({headless:true, chromiumSandbox:true});
    report.version = browser.version();
    const page = await browser.newPage({serviceWorkers:'block'});
    await page.goto('http://127.0.0.1:'+server.address().port+'/marker');
    assert.equal(await page.textContent('body'), marker);
    const processes=[], digests=new Map();
    for (const item of fs.readdirSync('/proc').filter(x=>/^\d+$/.test(x))) {
      try {
        const exe = fs.readlinkSync('/proc/'+item+'/exe');
        const cmdline=fs.readFileSync('/proc/'+item+'/cmdline','utf8').split('\0').filter(Boolean);
        if (/chrome|headless_shell/.test(exe)) {
          assert.ok(!cmdline.includes('--no-sandbox'), 'Chromium sandbox was disabled');
          if (!digests.has(exe)) digests.set(exe,await digest(exe));
          processes.push({exe,sha256:digests.get(exe),cmdline});
        }
      } catch (error) { if (error.code !== 'ENOENT' && error.code !== 'EACCES') throw error; }
    }
    assert.ok(processes.length, 'no live browser executable identity');
    report.processes = processes;
    let denied;
    try { await page.goto('http://192.0.2.1:443/network-boundary-marker', {timeout:10000}); }
    catch (error) { denied=String(error.message); }
    assert.ok(denied && /ERR_(NETWORK|ADDRESS)_UNREACHABLE|ERR_INTERNET_DISCONNECTED/.test(denied),
      'TEST-NET navigation did not fail at the routing boundary');
    report.externalNavigationError=denied;
    await page.goto('http://127.0.0.1:'+server.address().port+'/after');
    assert.equal(await page.textContent('body'),marker);
    assert.ok(hits>=2); report.loopbackRequests=hits; report.passed=true;
  } catch (error) { report.error=String(error.stack||error); process.exitCode=1; }
  finally {
    if (browser) await browser.close();
    await new Promise(resolve=>server.close(resolve));
    fs.writeFileSync(output, JSON.stringify(report,null,2)+'\n',{mode:0o600,flag:'wx'});
  }
}
main().catch(error=>{console.error(error);process.exitCode=1;});
