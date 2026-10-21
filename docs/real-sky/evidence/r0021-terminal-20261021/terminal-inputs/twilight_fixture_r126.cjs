// Existing source functions evaluated only to choose a meaningful partial-fade fixture.
const fs=require('node:fs'),vm=require('node:vm'),crypto=require('node:crypto'),path=require('node:path');
const sourcePath='${REPO_ROOT}/src/native/index.html';
const source=fs.readFileSync(sourcePath,'utf8');
const slice=(start,end)=>source.slice(source.indexOf(start),source.indexOf(end,source.indexOf(start)));
const funcs=slice('function solarElevationDeg(M,a){','function sunAltAt(')+slice('function nativeLunarPresentation(moon,solarElevation,surfaceFailed){','function lunarPresentation(');
const sandbox={lat:28.5383,clamp:x=>Math.max(0,Math.min(1,x))};vm.createContext(sandbox);vm.runInContext(funcs,sandbox);
const model={sunrise:446,sunset:1148,noon:797,decl:0};
const rows=[390,410,418].map(minute=>{const altitude=sandbox.solarElevationDeg(model,minute);return {localMinute:minute,altitude,moonShow:sandbox.nativeLunarPresentation({frac:.95,alt:20},altitude,false).moonShow};});
if(!(rows[2].moonShow>0&&rows[2].moonShow<1))throw Error('Not a partial fade fixture');
const result={scope:'Source-only fixture arithmetic; no native visual PASS',sourceSha256:crypto.createHash('sha256').update(source).digest('hex'),model,rows,selectedUtc:'2026-09-24T10:58:00Z',selectedLocalMinute:418};
fs.writeFileSync(path.join(__dirname,'intake/twilight-fixture-r126.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result));
