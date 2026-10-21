'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const root=path.resolve(__dirname,'..'),source=fs.readFileSync(path.join(root,'src/native/index.html'),'utf8');
const body=source.slice(source.indexOf('async function applyConfig('),source.indexOf('// Diagnostic control of the EXISTING native clock'));
const bind=source.slice(source.indexOf('function bindConfig('),source.indexOf('\nif(window.SalahConfig)'));
function fixture(failSave=false){
 const calls=[],data=new Map(),card={dataset:{}},weather={identity:'existing-weather'},sky={identity:'accepted-sky'},timings={identity:'accepted-prayers'};
 const s={URLSearchParams,Date,Intl,console,document:{querySelector:()=>card},weather,sky,today:timings,_runtimeGeneration:7,
  localStorage:{getItem:k=>data.get(k)??null,setItem(k,v){if(failSave)throw Error('controlled storage failure');data.set(k,v);}},
  _publishPersistence:(...a)=>calls.push(['persistence',...a]),
  beginRuntimeGeneration(){calls.push(['generation']);s._runtimeGeneration++;},
  resetForNewLocation(){calls.push(['reset']);s.weather=s.sky=s.today=null;},
  simulationReady:()=>true,startWeather:()=>calls.push(['weather']),loadPrayerData:async()=>calls.push(['prayer']),startRenderLoop:()=>calls.push(['loop']),render:()=>calls.push(['render'])};
 s.window=s;vm.createContext(s);vm.runInContext(fs.readFileSync(path.join(root,'config.js'),'utf8'),s);
 s.CONFIG=s.SalahConfig.normalize({lat:28.5383,lon:-81.3792,tz:'America/New_York',label:'CENTRAL FL',source:'manual',appearance:'glass',seed:1});
 vm.runInContext(bind+'\n'+body,s);
 return {s,calls,card,weather,sky,timings,apply:patch=>{s.next={...s.CONFIG,...patch};return vm.runInContext('applyConfig(next,{save:true})',s);}};
}
for(const failSave of [false,true])test('appearance-only A-B-A preserves weather, sky, prayer and request generation; save failure='+failSave,async()=>{
 const h=fixture(failSave);
 for(const appearance of ['contrast','glass']){
  await h.apply({appearance});
  assert.equal(h.card.dataset.appearance,appearance);assert.equal(h.s.CONFIG.appearance,appearance);
  assert.equal(h.s._runtimeGeneration,7,'appearance has no authority to revoke astronomical/provider work');
  assert.equal(h.s.weather,h.weather);assert.equal(h.s.sky,h.sky);assert.equal(h.s.today,h.timings);
 }
 assert.deepEqual(h.calls.map(c=>c[0]),['persistence','persistence']);
 assert.equal(h.s.SalahConfig.loadLocal()?.appearance??null,failSave?null:'glass');
});
test('appearance-only changes preserve the provider-adopted timezone instead of restoring the config hint',async()=>{
 const h=fixture();vm.runInContext('bindConfig(CONFIG)',h.s);
 h.s.tz='Asia/Riyadh';const cacheTz=h.s._cacheTz;
 for(const appearance of ['contrast','glass']){
  await h.apply({appearance});assert.equal(h.s.tz,'Asia/Riyadh');
  assert.equal(h.s._cacheTz,cacheTz);assert.equal(h.s.CONFIG.tz,'America/New_York');
  assert.equal(h.s._runtimeGeneration,7);assert.equal(h.s.today,h.timings);
 }
});
for(const patch of [{lat:29},{lon:-82},{tz:'UTC'},{units:'c'},{method:'4'},{school:'1'},{seed:2},{lp:.5},{time:'12'},{datefmt:'DD MMM YYYY'},{label:'changed'}, {locationEvidence:{source:'manual',area:'new evidence'}}])test('appearance change cannot bypass other config changes: '+JSON.stringify(patch),async()=>{
 const h=fixture();await h.apply({...patch,appearance:'contrast'});
 assert.equal(h.s._runtimeGeneration,8);assert(h.calls.some(c=>c[0]==='reset'));assert(h.calls.some(c=>c[0]==='weather'));assert(h.calls.some(c=>c[0]==='prayer'));
});
