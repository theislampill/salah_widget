'use strict';
// R0041 candidate helper: recompute the source identities that tests/native-script-contract.js and
// tests/r0017-transport.cjs pin (moon-initial split body, authored native source, legacy-Moon structural control and
// its parent) from the CURRENT generated index, and rewrite the R0041 candidate entries in place. Only the R0041
// entries (marked "R0041") are touched; every earlier pin and its history are kept.
// Usage: node tools/qa/r0041/rebind-pins.cjs   (from the repository root)
const fs=require('node:fs'),crypto=require('node:crypto');
const h=x=>crypto.createHash('sha256').update(x).digest('hex');
const src=fs.readFileSync('index.html','utf8');
const scripts=[...src.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)];
const initial=h(scripts.find(m=>/id="moon-initial-code"/.test(m[1]))[2]);
let b=src;for(const id of ['moon-initial-code','moon-refinement-code']){const m=scripts.filter(s=>s[1].trim()==='id="'+id+'"');if(m.length){const i=b.indexOf(m[0][0]);b=b.slice(0,i)+b.slice(i+m[0][0].length);}}
const legacy=h(b.replace('</body>','<script>if(location.protocol==="file:")window.__SALAH_MOON_OFFLINE__=true;</script><script src="moon/moon-host.js"></script></body>'));
const parent=h(src),authored=h(fs.readFileSync('src/native/index.html'));
let c=fs.readFileSync('tests/native-script-contract.js','utf8');
c=c.replace(/'moon-initial':'[0-9a-f]{64}'/,`'moon-initial':'${initial}'`);
c=c.replace(/(\/\/ R0041 \(issue 143\) CANDIDATE[\s\S]*?\n    ')[0-9a-f]{64}(':Object\.freeze\(\{\n      profile:'current-authored-native')/,`$1${authored}$2`);
c=c.replace(/(profile:'current-authored-native',kind:'current-authored-source',commit:')[0-9a-f]+(',path:'src\/native\/index\.html',layout:'config,native'\}\),\n    ')[0-9a-f]{64}(':Object\.freeze\(\{\n      profile:'retained-legacy-moon-structural-control',kind:'structural-control',commit:')[0-9a-f]+(',path:'index\.html',\n      parentSha256:')[0-9a-f]{64}/,
 (m,a,b2,c2,d)=>`${a}candidate${b2}${legacy}${c2}candidate${d}${parent}`);
fs.writeFileSync('tests/native-script-contract.js',c);
let t=fs.readFileSync('tests/r0017-transport.cjs','utf8');
t=t.replace(/(\/\/ R0041 candidate rebind[^\n]*\n    assert\.equal\(sourceProfiles\.legacyMoon\.sourceSha256,')[0-9a-f]{64}/,`$1${legacy}`);
fs.writeFileSync('tests/r0017-transport.cjs',t);
console.log(JSON.stringify({initial,authored,legacy,parent}));
