import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

test('foreground bridge cannot substitute the legacy canvas for absent current terrain',()=>{
 const w={SalahMoonRuntime:{surface:()=>null}},old={identity:'legacy'},c={window:w,_pbrReady:true,_moonFallbackReady:true,_moonCv:old};
 vm.runInNewContext(fs.readFileSync(new URL('../../real-sky/native-host-hooks.js',import.meta.url),'utf8'),c);
 assert.equal(w.SalahNativeSkyHost.lunarSurface(),null);
 const final={identity:'current-refined'};w.SalahMoonRuntime.surface=()=>final;
 assert.equal(w.SalahNativeSkyHost.lunarSurface(),final);
});

test('native cutout and SVG admit exactly the same current terrain surface',()=>{
 const source=fs.readFileSync(new URL('../../src/native/index.html',import.meta.url),'utf8');
 const start=source.indexOf('function updateSkySurface(){'),end=source.indexOf('\nfunction commitSkyScene',start);
 const toggles={},classes={toggle:(name,on)=>toggles[name]=on},nodes={'.c':{classList:classes},'.moon-mask-disc':{classList:classes},'.mphoto':{getAttribute:()=> 'legacy-data-url'}};
 const w={SalahMoonRuntime:{surface:()=>null}},c={window:w,$:s=>nodes[s],_pbrReady:true,_moonFallbackReady:true,_skySceneKey:'accepted-A',_skyMoonPresence:1};
 vm.runInNewContext(source.slice(start,end)+'\nupdateSkySurface();',c);
 assert.equal(toggles['moon-ready'],false);assert.equal(toggles['mask-on'],false);
 w.SalahMoonRuntime.surface=()=>({});vm.runInNewContext('updateSkySurface();',c);
 assert.equal(toggles['moon-ready'],true);assert.equal(toggles['mask-on'],true);
 w.SalahMoonRuntime.surface=()=>null;vm.runInNewContext('updateSkySurface();',c);
 assert.equal(toggles['moon-ready'],false);assert.equal(toggles['mask-on'],false);
});
