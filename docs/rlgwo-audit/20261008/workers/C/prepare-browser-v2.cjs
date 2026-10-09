'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const hash=x=>crypto.createHash('sha256').update(x).digest('hex');
const v1=JSON.parse(fs.readFileSync(path.join(__dirname,'browser-fixture-preparation.json'),'utf8'));
const wrapper=fs.readFileSync(path.join(__dirname,'browser-fixtures/widget-fixture.html'));
if(hash(wrapper)!==v1.preparedFixtureSha256)throw Error('V1 wrapper changed; do not overwrite failure history');
fs.writeFileSync(path.join(__dirname,'browser-fixtures/widget-fixture-v2.html'),wrapper);
let driver=fs.readFileSync(path.join(__dirname,'run_weather_browser.py'),'utf8');
const originalDriver=hash(driver),changes=[];
function replace(from,to,purpose){const count=driver.split(from).length-1;if(count!==1)throw Error('Driver anchor '+purpose+' '+count);driver=driver.replace(from,to);changes.push({purpose,from,to});}
replace('threading, traceback, zlib','threading, time, traceback, zlib','Bounded host-monotonic predicate polling');
replace("def run(a):",`def wait_predicate(page,predicate,arg=None,timeout=45000):
 # Playwright wait_for_function string polling uses eval in the document realm.
 # Evaluate a function directly through the browser protocol; CSP stays exact.
 end=time.monotonic()+timeout/1000
 while time.monotonic()<end:
  if page.evaluate(predicate,arg):return
  page.wait_for_timeout(100)
 raise TimeoutError('Required function predicate did not become true within '+str(timeout)+'ms')

def run(a):`, 'Avoid document string eval without granting generic unsafe-eval');
replace("BASE/'browser-fixture-preparation.json'","BASE/'browser-fixture-preparation-v2.json'",'Version-specific immutable preparation');
replace("BASE/'browser-fixtures/widget-fixture.html'","BASE/'browser-fixtures/widget-fixture-v2.html'",'Version-specific wrapper; same expectation and product source bodies');
replace("'units':'c','local':1,'seed':1","'units':'c','seed':1",'Explicit fixed-site hash mode; local=1 intentionally ignores unseeded hash coordinates per config precedence');
replace(`page.wait_for_function("window.__widgetFixture?.state==='ready'||window.__widgetFixture?.state==='error'",timeout=45000)`,
 `wait_predicate(page,"() => window.__widgetFixture?.state==='ready'||window.__widgetFixture?.state==='error'",timeout=45000)`, 'Bootstrap predicate is a direct function');
replace(`page.wait_for_function("()=>{const f=window.__widgetFixture,b=window.__smokeWeather;if(f?.state!=='ready'||!b)return false;const s=b.read(b.identity());return s.qa.cache.prayerLoaded&&s.modelEligible&&!s.wxBusy&&!s.radarBusy&&s.radar?.sample&&s.qa.weatherHeader?.rawCode===95;}",timeout=45000)`,
 `wait_predicate(page,"()=>{const f=window.__widgetFixture,b=window.__smokeWeather;if(f?.state!=='ready'||!b)return false;const s=b.read(b.identity());return s.qa.cache.prayerLoaded&&s.modelEligible&&!s.wxBusy&&!s.radarBusy&&s.radar?.sample&&s.qa.weatherHeader?.rawCode===95;}",timeout=45000)`, 'Native acquisition/paint readiness predicate is a direct function; expectation unchanged');
replace(`page.wait_for_function("wet=>{const b=__smokeWeather,s=b.read(b.identity());return wet?(s.precip==='on'&&s.visibleParticles>0):(s.precip==='off'&&s.visibleParticles===0);}",arg=wet,timeout=10000)`,
 `wait_predicate(page,"wet=>{const b=__smokeWeather,s=b.read(b.identity());return wet?(s.precip==='on'&&s.visibleParticles>0):(s.precip==='off'&&s.visibleParticles===0);}",arg=wet,timeout=10000)`, 'Particle presence/absence predicates unchanged, direct function polling');
driver=driver.replaceAll("page.evaluate('__widgetFixture.state')","page.evaluate('() => __widgetFixture.state')")
 .replaceAll("page.evaluate('__widgetFixture.error')","page.evaluate('() => __widgetFixture.error')")
 .replaceAll("page.evaluate('__widgetFixture')","page.evaluate('() => __widgetFixture')");
fs.writeFileSync(path.join(__dirname,'run_weather_browser_v2.py'),driver);
const failed=path.join(__dirname,'browser14-chromium/results.json');
const receipt={...v1,status:'PREPARED V2; NOT EXECUTED BY C',version:2,
 originalDriverSha256:originalDriver,driverSha256:hash(driver),changes:[...v1.changes,...changes],
 retainedFailure:{path:failed,sha256:hash(fs.readFileSync(failed)),classification:'V1 HARNESS ERROR BEFORE CONSUMER PROOF',runtimeUnchanged:true,
  causes:['Playwright string wait evaluated under restrictive wrapper CSP','Unseeded local=1 selected coarse detect according to config precedence despite hash coordinates'],
  consequence:'Neither V1 case qualifies product behavior; original records and wrapper/driver remain intact'},
 configMode:'fixed-site hardcoded latitude/longitude/timezone/method/unit hash, permitted by the original R001E dispatch contract; no local=1 and no coarse provider fallback',
 expectations:'ALL V1 product/source/hook/ownership/transport/temperature/amount/particle/radar/layout assertions retained; no CSP relaxation beyond the disclosed original owned-Wasm allowance. No missing case changes to PASS.'};
fs.writeFileSync(path.join(__dirname,'browser-fixture-preparation-v2.json'),JSON.stringify(receipt,null,2)+'\n');
console.log(JSON.stringify({status:receipt.status,driverSha256:receipt.driverSha256,wrapperSha256:hash(wrapper)}));
