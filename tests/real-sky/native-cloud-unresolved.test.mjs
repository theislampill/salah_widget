import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import {nativeCloudSolarLighting} from '../../real-sky/native-preview.mjs';

const hooks=fs.readFileSync(new URL('../../real-sky/native-host-hooks.js',import.meta.url),'utf8');
const config=fs.readFileSync(new URL('../../src/native/config.js',import.meta.url),'utf8');
const at=Date.parse('2026-10-02T12:00:00Z');

// Only browser layout/visibility bindings are inert. The entire production host
// adapter, configuration resolver and physical cloud-lighting owner run unchanged.
function host(lat,lon,{lighting=nativeCloudSolarLighting,clock=at,params=''}={}){
 const world={window:{SalahNativeCloudLighting:lighting},lat,lon,tz:'UTC',units:'f',LPOLL:0,
  _runtimeGeneration:0,TIMESCALE:1,today:null,_pbrFailed:false,document:{hidden:false},q:new URLSearchParams(params),
  $:()=>null,simulationReady:()=>true,skySceneIdentity:()=>[world.lat,world.lon,'UTC','wall'].join('|'),
  selectedWeather:()=>null,simNow:()=>clock,isMotionReduced:()=>false};
 vm.runInNewContext(hooks,world,{filename:'native-host-hooks.js'});
 return {world,adapter:world.window.SalahNativeSkyHost};
}

function unresolved(storage){
 const world={window:{},URLSearchParams};
 if(storage===undefined)Object.defineProperty(world.window,'localStorage',{get(){throw new DOMException('blocked getter','SecurityError');}});
 vm.runInNewContext(config,world,{filename:'config.js'});
 const resolved=world.window.SalahConfig.resolve('#local=1',storage);
 assert.equal(resolved.cfg,null);
 assert.equal(resolved.needsDetect,true);
 return host(resolved.cfg?.lat??null,resolved.cfg?.lon??null);
}

test('blocked storage getter leaves optional cloud lighting unavailable during manual recovery',()=>{
 assert.equal(unresolved().adapter.cloudLighting(),null);
});

test('denied reads and invalid saved records do not require an astronomical observer',()=>{
 for(const value of ['read-denied','{not-json',JSON.stringify({v:2,lat:51.5,lon:-.12})]){
  const storage={getItem(){if(value==='read-denied')throw new DOMException('blocked read','SecurityError');return value;},removeItem(){assert.fail('read fallback must not erase saved bytes');}};
  assert.equal(unresolved(storage).adapter.cloudLighting(),null);
 }
});

test('either missing coordinate withdraws optional lighting without coercion',()=>{
 for(const [lat,lon] of [[null,null],[null,31],[30,null],[undefined,31],[30,undefined]])assert.equal(host(lat,lon).adapter.cloudLighting(),null);
});

test('valid native observer still reaches the unchanged physical lighting owner',()=>{
 const {adapter}=host(30,31),snapshot=adapter.capture(false),actual=adapter.cloudLighting();
 const expected=nativeCloudSolarLighting(snapshot);
 assert.equal(actual.utcMs,at);
 assert.deepEqual(actual.sun,expected.sun);
 assert.deepEqual(actual.camera,expected.camera);
 for(const [u,v] of [[0,0],[.5,.5],[1,1]])assert.deepEqual(actual.sample(u,v),expected.sample(u,v));
});

test('numeric invalid coordinates retain strict native validation',()=>{
 for(const [lat,lon] of [[NaN,31],[Infinity,31],[91,31],[30,NaN],[30,181]])assert.throws(()=>host(lat,lon).adapter.cloudLighting(),/Invalid native (latitude|longitude)/);
});

test('invalid native clock and camera remain errors for a resolved observer',()=>{
 assert.throws(()=>host(30,31,{clock:NaN}).adapter.cloudLighting(),/Invalid native UTC/);
 assert.throws(()=>host(30,31,{params:'skyAz=bad'}).adapter.cloudLighting(),/Invalid native camera azimuth/);
});

test('manual coordinate recovery recaptures the accepted target',()=>{
 const {world,adapter}=host(null,null);
 assert.equal(adapter.cloudLighting(),null);
 world.lat=30;world.lon=31;
 const recovered=adapter.cloudLighting();
 assert.equal(recovered.utcMs,at);
 assert.deepEqual(recovered.sun,nativeCloudSolarLighting(adapter.capture(false)).sun);
});

test('missing optional lighting module still returns unavailable',()=>{
 const {world,adapter}=host(30,31);world.window.SalahNativeCloudLighting=undefined;
 assert.equal(adapter.cloudLighting(),null);
});
