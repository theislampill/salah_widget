'use strict';
// Source-level lifecycle controls only. These doubles launch no browser and
// establish no native network, renderer sandbox, or product evidence.
const test=require('node:test'),assert=require('node:assert/strict');
const {refuseExternalThenReadLoopback}=require('./browser-control.cjs');

function doubles({external='net::ERR_INTERNET_DISCONNECTED',marker='private-marker',closeError=false,freshError=false}={}) {
  const calls=[];
  const page={
    async goto(url){calls.push(['old-goto',url]);
      if(url.startsWith('http://192.0.2.1:443/')){if(external)throw Error(external);return;}
      throw Error('interrupted by another navigation to chrome-error://chromewebdata/');},
    async close(){calls.push(['old-close']);if(closeError)throw Error('close failed');},
    async textContent(){return 'private-marker';}
  };
  const browser={async newPage(options){calls.push(['new-page',options]);return {
    async goto(url){calls.push(['fresh-goto',url]);if(freshError)throw Error('fresh loopback unavailable');},async textContent(){return marker;}
  };}};
  return {calls,page,browser};
}

test('failed document is closed before fresh same-browser loopback check',async()=>{
  const {calls,page,browser}=doubles(),report={};
  await refuseExternalThenReadLoopback(browser,page,'http://127.0.0.1:1234','private-marker',report);
  assert.deepEqual(calls.map(x=>x[0]),['old-goto','old-close','new-page','fresh-goto']);
  assert.deepEqual(calls[2][1],{serviceWorkers:'block'});
  assert.equal(calls[3][1],'http://127.0.0.1:1234/after');
  assert.match(report.externalNavigationError,/ERR_INTERNET_DISCONNECTED/);
  assert.equal(report.postNegativePage,'fresh-page-same-browser');
});

test('external success or unrelated failure cannot reach fresh positive control',async()=>{
  for(const external of [null,'Timeout 10000ms exceeded','net::ERR_CONNECTION_REFUSED']){
    const {calls,page,browser}=doubles({external});
    await assert.rejects(refuseExternalThenReadLoopback(browser,page,'http://127.0.0.1:1234','private-marker',{}),
      /did not fail at the routing boundary/);
    assert.deepEqual(calls.map(x=>x[0]),['old-goto']);
  }
});

test('wrong fresh marker is rejected',async()=>{
  const {page,browser}=doubles({marker:'wrong-marker'});
  await assert.rejects(refuseExternalThenReadLoopback(browser,page,'http://127.0.0.1:1234','private-marker',{}),
    {code:'ERR_ASSERTION',actual:'wrong-marker',expected:'private-marker'});
});

test('unavailable fresh marker is rejected',async()=>{
  const {page,browser}=doubles({freshError:true}),report={};
  await assert.rejects(refuseExternalThenReadLoopback(browser,page,'http://127.0.0.1:1234','private-marker',report),
    /fresh loopback unavailable/);
  assert.equal(report.postNegativePage,undefined);
});

test('failed document closure is terminal',async()=>{
  const {calls,page,browser}=doubles({closeError:true});
  await assert.rejects(refuseExternalThenReadLoopback(browser,page,'http://127.0.0.1:1234','private-marker',{}),/close failed/);
  assert.deepEqual(calls.map(x=>x[0]),['old-goto','old-close']);
});
