'use strict';
// R0033 R33-17 pixel control: decode PNG pairs in a headless Chromium canvas and count differing pixels.
// Usage: node tools/qa/r0033_pixel_diff.cjs --pairs <json file: [[label,a.png,b.png],...]> [--playwright <pkg>]
const fs=require('node:fs');const a={};const v=process.argv.slice(2);for(let i=0;i<v.length;i+=2)a[v[i].slice(2)]=v[i+1];
const PW=require(a.playwright||'playwright');
(async()=>{const b=await PW.chromium.launch({headless:true}),p=await b.newPage();
 for(const [label,x,y] of JSON.parse(fs.readFileSync(a.pairs,'utf8'))){
  const u=f=>'data:image/png;base64,'+fs.readFileSync(f).toString('base64');
  const r=await p.evaluate(async([ua,ub])=>{const load=s=>new Promise((res,rej)=>{const i=new Image();i.onload=()=>res(i);i.onerror=rej;i.src=s;});
   const [ia,ib]=await Promise.all([load(ua),load(ub)]);if(ia.width!==ib.width||ia.height!==ib.height)return {sizeMismatch:true};
   const d=im=>{const c=document.createElement('canvas');c.width=im.width;c.height=im.height;const x=c.getContext('2d');x.drawImage(im,0,0);return x.getImageData(0,0,im.width,im.height).data;};
   const A=d(ia),B=d(ib);let n=0,max=0;for(let i=0;i<A.length;i+=4){const m=Math.max(Math.abs(A[i]-B[i]),Math.abs(A[i+1]-B[i+1]),Math.abs(A[i+2]-B[i+2]));if(m){n++;if(m>max)max=m;}}
   return {pixels:A.length/4,differing:n,maxChannelDelta:max};},[u(x),u(y)]);
  console.log(JSON.stringify({label,...r}));
 }
 await b.close();})();
