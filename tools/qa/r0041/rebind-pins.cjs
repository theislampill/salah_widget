'use strict';
// R0041 candidate helper: recompute the source identities that tests/native-script-contract.js and
// tests/r0017-transport.cjs pin (moon-initial split body, authored native source, legacy-Moon structural control and
// its parent) from the CURRENT generated index, and rewrite the R0041 candidate entries in place. Only the R0041
// block (marked "R0041 (issue 143) CANDIDATE, same branch:") and the moon-initial split pin are touched; the script
// refuses to write if any other byte would change. (An earlier version matched the first hexadecimal commit anywhere
// and overwrote accepted R0036/R0033 records; they were restored from main 06b6e93b.)
// Usage: node tools/qa/r0041/rebind-pins.cjs   (from the repository root)
const fs=require('node:fs'),crypto=require('node:crypto');
const h=x=>crypto.createHash('sha256').update(x).digest('hex');
const src=fs.readFileSync('index.html','utf8');
const scripts=[...src.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)];
const initial=h(scripts.find(m=>/id="moon-initial-code"/.test(m[1]))[2]);
let b=src;for(const id of ['moon-initial-code','moon-refinement-code']){const m=scripts.filter(s=>s[1].trim()==='id="'+id+'"');if(m.length){const i=b.indexOf(m[0][0]);b=b.slice(0,i)+b.slice(i+m[0][0].length);}}
const legacy=h(b.replace('</body>','<script>if(location.protocol==="file:")window.__SALAH_MOON_OFFLINE__=true;</script><script src="moon/moon-host.js"></script></body>'));
const parent=h(src),authored=h(fs.readFileSync('src/native/index.html'));
const NL='\n';
let c=fs.readFileSync('tests/native-script-contract.js','utf8');
const MARK='    // R0041 (issue 143) CANDIDATE, same branch:';
if(c.split(MARK).length!==2)throw Error('expected exactly one R0041 block marker');
const END="      layout:'config,first-paint,native,sky,moon-file,moon-host'}),"+NL;
const span=x=>{const s=x.indexOf(MARK),e=x.indexOf(END,s);if(s<0||e<0)throw Error('R0041 block bounds');return [s,e+END.length];};
const [start,end]=span(c),block=c.slice(start,end);
if(block.split('Object.freeze({').length!==3)throw Error('R0041 block must hold exactly two records');
const key=profile=>new RegExp(NL+"    '[0-9a-f]{64}'(:Object\\.freeze\\(\\{"+NL+"      profile:'"+profile+"')");
const nextBlock=block.replace(key('current-authored-native'),NL+"    '"+authored+"'$1")
 .replace(key('retained-legacy-moon-structural-control'),NL+"    '"+legacy+"'$1")
 .replace(/parentSha256:'[0-9a-f]{64}'/,"parentSha256:'"+parent+"'");
const pinRe=/'moon-initial':'[0-9a-f]{64}'/;
if((c.match(new RegExp(pinRe.source,'g'))||[]).length!==1)throw Error('expected one moon-initial pin');
const out=(c.slice(0,start)+nextBlock+c.slice(end)).replace(pinRe,"'moon-initial':'"+initial+"'");
const outside=x=>{const [s,e]=span(x);return x.slice(0,s).replace(pinRe,'')+x.slice(e);};
if(outside(out)!==outside(c))throw Error('refusing to write: bytes outside the R0041 block would change');
fs.writeFileSync('tests/native-script-contract.js',out);
let t=fs.readFileSync('tests/r0017-transport.cjs','utf8');
t=t.replace(/(\/\/ R0041 candidate rebind[^\n]*\n    assert\.equal\(sourceProfiles\.legacyMoon\.sourceSha256,')[0-9a-f]{64}/,`$1${legacy}`);
fs.writeFileSync('tests/r0017-transport.cjs',t);
console.log(JSON.stringify({initial,authored,legacy,parent}));
