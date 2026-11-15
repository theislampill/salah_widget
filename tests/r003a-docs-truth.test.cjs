'use strict';
// R003A R3A-03.1: the OPTICS.md crepuscular section carries every numeric constant of the shipped gate expressions
// (ray, broken, directional, humid) taken from the authored source at run time. R3A_SOURCE overrides the source
// (mutation control: changing one constant in a scratch copy must fail this pin).
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'..');
const src=fs.readFileSync(process.env.R3A_SOURCE||path.join(root,'src/native/index.html'),'utf8');
const optics=fs.readFileSync(process.env.R3A_OPTICS||path.join(root,'OPTICS.md'),'utf8');
const section=optics.slice(optics.indexOf('### Crepuscular rays'),optics.indexOf('### Anticrepuscular rays'));
const one=re=>{const m=src.match(re);assert(m,'expression not found: '+re);return m[1];};
test('R3A-03.1 OPTICS crepuscular gate constants equal the shipped expressions',()=>{
 assert(section.length>100,'crepuscular section present');
 const exprs={ray:one(/const ray=(Math\.min\([^;]*\));/),broken:one(/const broken=(clamp\([^;]*\));/),
  directional:one(/const directional=([^;]*);/),humid:one(/humid: dewC==null\?0:(r\(dewC,[^)]*\))/)};
 const nums=new Set(Object.values(exprs).flatMap(e=>e.match(/\d+(?:\.\d+)?/g)||[]));
 const text=section.replace(/²/g,'*2');
 for(const n of nums)assert(new RegExp('(^|[^0-9.])'+n.replace('.','\.')+'(?![0-9])').test(text),'OPTICS crepuscular section lacks constant '+n+' from '+JSON.stringify(exprs));
 assert.match(exprs.directional,/1-D\.cloud\*D\.cloud/);assert.match(section,/directional = 1 − cloud²/);
});
