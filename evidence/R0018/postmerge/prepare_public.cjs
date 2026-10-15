'use strict';
// Extract only the established fixture adapters; never serve the rebuilt HTML.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root='C:/Users/theis/.codex/worktrees/r0018-readability/salah_widget';
const f=require(path.join(root,'tests/r0018-appearance-browser-fixture.cjs'));
const request=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
const source=fs.readFileSync(path.join(root,'index.html'),'utf8'),s=f.spec('noon','default');
const built=f.buildPage(source,s,{assetPaths:request.assetPaths});
const tag='<script src="config.js">',start=source.indexOf(tag),end=built.indexOf(tag);
const pre=built.slice(start,end);
const marker='<script>window.__appearanceFixture.snapshot=';
if(built.split(marker).length!==2)throw Error('Unique snapshot adapter required');
const a=built.indexOf(marker),b=built.indexOf('</script>',a)+9,inspect=built.slice(a,b);
if(built.replace(pre,'').replace(inspect,'')!==source)throw Error('Unexpected fixture/product modification');
const script=t=>{if(!t.startsWith('<script>')||!t.endsWith('</script>'))throw Error('Expected plain adapter');return t.slice(8,-9);};
process.stdout.write(JSON.stringify({spec:s,hash:f.routeHash(s)+'&school=0',sourceSha256:crypto.createHash('sha256').update(source).digest('hex'),pre:script(pre),inspect:script(inspect),reconstructedProductExact:true}));
