'use strict';
// Moon-reuse feasibility audit (2026-11-16): intervals in which the product's waxing flag (sign of the bright-limb
// angle chi, src/native/index.html L2072-2077) disagrees with the direction in which the phase angle alpha actually
// moves. During such an interval the host's leading-edge scene (moon/src/moon-precision.mjs L24) is offset in the
// wrong direction. Pure ephemeris replay of the product's own functions; no browser.
// Usage: node waxing-mismatch.cjs <repoRoot> <startISO> <days> <outJson>
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const [root,startISO,days,outFile]=process.argv.slice(2);
const html=fs.readFileSync(path.join(root,'src/native/index.html'),'utf8');const a=html.indexOf('const _RAD=Math.PI/180'),b=html.indexOf('// Galactic centre',a);
const ctx={Math,Date};vm.createContext(ctx);vm.runInContext(html.slice(a,b)+';this.moonIllum=moonIllum;',ctx);
const s=Date.parse(startISO),STEP=10000,N=Math.round(days*86400000/STEP);let prev=null,open=null;const out=[];
for(let i=0;i<=N;i++){const t=s+i*STEP,il=ctx.moonIllum(new Date(t)),al=Math.acos(2*il.fraction-1);
  if(prev){const dir=Math.sign(al-prev.al),expect=il.waxing?-1:1,bad=dir!==0&&dir!==expect;
    if(bad&&!open)open={from:new Date(t).toISOString(),alpha:al,waxing:il.waxing};
    if(!bad&&open){open.to=new Date(t).toISOString();open.minutes=(t-Date.parse(open.from))/60000;out.push(open);open=null;}}
  prev={al};}
const mins=out.map(x=>x.minutes);
const r={start:startISO,days:+days,stepSeconds:STEP/1000,intervals:out,count:out.length,minutesTotal:mins.reduce((a,b)=>a+b,0),minutesMin:Math.min(...mins),minutesMax:Math.max(...mins)};
fs.writeFileSync(outFile,JSON.stringify(r,null,1));console.log(JSON.stringify({count:r.count,minutesTotal:r.minutesTotal,min:r.minutesMin,max:r.minutesMax,first:out.slice(0,4)},null,1));
