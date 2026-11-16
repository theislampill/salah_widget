'use strict';
// Moon-reuse audit / R0041 drafting: pixel-based Moon-disc presence detector, validated on committed crops.
// For a crop of the .mphoto rectangle (square, disc centred, disc radius ~0.483 of the side):
//   disc set  = pixels with r <= 0.47*S ; sky set = corner pixels with r >= 0.53*S (outside the disc)
//   mDisc, mSky = mean luma (Rec.709 on sRGB codes); medDisc = median luma of the disc set
//   stars = count of disc pixels with Y > max(medDisc, medSky) + 40          (stars showing inside the disc area)
//   dRef  = mean |Y - Y_ref| over the disc set against a REFERENCE frame of the same cell in which the disc is
//           known present (e.g. the first frame after the first refined result)
//   ABSENT  if stars >= 10  OR  dRef > 4 codes ; PRESENT otherwise.
//   Normal tier swaps measured in the study change dRef by <= 0.33 (initial->preview) and <= 0.04 (preview->refined);
//   the blank events give dRef 8-106 (new / full Moon). A contrast-to-corner-sky rule does NOT work: during the full-
//   Moon blank the dark star-occluder disc remains, so the disc area is darker than the sky (43 vs 56).
//   Model frame analysis, not human perception.
// Usage: node presence-detector.cjs <reference.png> <png...>
const fs=require('node:fs');const {decodePng}=require('./png.cjs');
const Y=(d,i)=>.2126*d[i]+.7152*d[i+1]+.0722*d[i+2];
function load(file){const img=decodePng(fs.readFileSync(file)),S=Math.min(img.width,img.height),cx=img.width/2,cy=img.height/2,disc=[];for(let y=0;y<img.height;y++)for(let x=0;x<img.width;x++)if(Math.hypot(x+.5-cx,y+.5-cy)<=.47*S)disc.push(Y(img.data,4*(y*img.width+x)));return disc;}
let REF=null;
function classify(file){const img=decodePng(fs.readFileSync(file)),S=Math.min(img.width,img.height),cx=img.width/2,cy=img.height/2;const disc=[],sky=[];
  for(let y=0;y<img.height;y++)for(let x=0;x<img.width;x++){const r=Math.hypot(x+.5-cx,y+.5-cy),v=Y(img.data,4*(y*img.width+x));if(r<=.47*S)disc.push(v);else if(r>=.53*S)sky.push(v);}
  const med=a=>{const s=[...a].sort((p,q)=>p-q);return s[s.length>>1];},mean=a=>a.reduce((p,q)=>p+q,0)/a.length;
  const mDisc=mean(disc),mSky=mean(sky),thr=Math.max(med(disc),med(sky))+40,stars=disc.filter(v=>v>thr).length;
  const dRef=REF&&REF.length===disc.length?disc.reduce((p,v,i)=>p+Math.abs(v-REF[i]),0)/disc.length:null;
  return {file:file.split(/[\/]/).pop(),mDisc:+mDisc.toFixed(2),mSky:+mSky.toFixed(2),stars,dRef:dRef==null?null:+dRef.toFixed(2),verdict:stars>=10||(dRef!=null&&dRef>4)?'ABSENT':'PRESENT'};}
const [ref,...files]=process.argv.slice(2);REF=load(ref);for(const f of files)console.log(JSON.stringify(classify(f)));
