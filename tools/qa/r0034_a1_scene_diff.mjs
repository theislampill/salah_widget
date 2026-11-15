// R0034-A1 scene matrix (VM level, deterministic, no browser). For each scene, renders the worker background with the
// real core, runs the accept() body of origin/main (git object) and of the working tree on the same raw raster, encodes
// both with the product encoder and reports the lattice ridge (as in tests/real-sky/r0034-a1-aureole-lattice.test.mjs,
// at the physical Sun's projected row band when it is in view, else the owner band), the per-channel code difference
// (max, share of pixels changed, bounding box) and byte identity. Optionally writes main/candidate PNG-ready RGBA.
// Usage: node tools/qa/r0034_a1_scene_diff.mjs [--base origin/main] [--out <dir>]
import fs from 'node:fs';
import vm from 'node:vm';
import path from 'node:path';
import {execFileSync} from 'node:child_process';
import {nativeJob} from '../../real-sky/native-contract.mjs';
import {renderPhysicalSky} from '../../real-sky/core/src/physical-sky-renderer.mjs';
import {encodeNativeFrame} from '../../real-sky/native-encoding.mjs';
import {nativeSkyPresentation,nativeAtmosphereFields,nativeSolarRegistration} from '../../real-sky/native-preview.mjs';
import {luminanceToSurfaceMagnitude} from '../../real-sky/core/src/sky-background.mjs';

const a={};const v=process.argv.slice(2);for(let i=0;i<v.length;i+=2)a[v[i].slice(2)]=v[i+1];
const base=a.base||'origin/main',out=a.out?path.resolve(a.out):null;if(out)fs.mkdirSync(out,{recursive:true});
const body=s=>s.slice(s.indexOf(' function accept('),s.indexOf('\n function failure('));
const mainSrc=execFileSync('git',['show',`${base}:real-sky/native-host.mjs`],{encoding:'utf8'});
const candSrc=fs.readFileSync(new URL('../../real-sky/native-host.mjs',import.meta.url),'utf8');
function accept(src,result,request,anchor){
 const s={snapshot:()=>({}),lifecycle:{current:()=>true},status:{rejections:0,renders:0,errors:[]},physical:true,host:{capture:()=>({solarAnchor:anchor})},
  frame:null,job:null,compose(){},publish(){},nativeAtmosphereFields,nativeSkyPresentation,Error,Number,Math,__r:result,__q:request};
 vm.createContext(s);vm.runInContext(body(src)+'\naccept(__r,1,__q);',s);return s.frame;
}
// Corner anchor as the live host measures it at these scenes (sunbody centre in canvas coordinates; presence 1 by day).
const anchorFor=alt=>({x:20.12,y:40+176*(1-Math.min(1,Math.max(0,alt/40))),presence:Math.min(1,Math.max(0,(alt+1.5)/7))});
const SITES={orlando:{lat:28.54,lon:-81.38},madinah:{lat:24.47,lon:39.61}};
// UTC instants: Orlando 2026-11-14 (EST = UTC-5), Madinah 2026-11-14 (UTC+3).
const SCENES=[
 ['orlando','10:26 sun high in view','2026-11-14T15:26:00Z'],['orlando','12:14 near transit','2026-11-14T17:14:00Z'],
 ['orlando','15:45 sun ~20 off-camera','2026-11-14T20:45:00Z'],['orlando','16:15 sun ~14','2026-11-14T21:15:00Z'],
 ['orlando','17:10 sun ~3 (twilight shoulder above -3)','2026-11-14T22:10:00Z'],['orlando','17:55 civil twilight below -3','2026-11-14T22:55:00Z'],
 ['orlando','18:40 nautical/astro twilight','2026-11-14T23:40:00Z'],['orlando','22:00 night','2026-11-15T03:00:00Z'],
 ['madinah','08:30 morning','2026-11-14T05:30:00Z'],['madinah','11:30 near transit','2026-11-14T08:30:00Z'],
 ['madinah','16:30 low sun','2026-11-14T13:30:00Z'],['madinah','17:40 sun near horizon (-1.9)','2026-11-14T14:40:00Z']];
const rows=[];
for(const [site,label,utc] of SCENES)for(const vis of [20000,6000]){
 const st={utcMs:Date.parse(utc),...SITES[site],heightM:0,generation:2,sceneIdentity:'r0034-a1',camera:{azDeg:180,altDeg:45,fovYDeg:90,rollDeg:0},weather:{vis,cloud:100,code:3,temp:60},units:'f',lp:0};
 const j=nativeJob(st,true);
 const raw=renderPhysicalSky([],{...j.options,observer:j.observer,diffuse:null,atmosphere:{...j.options.atmosphere,nightZenithVMag:luminanceToSurfaceMagnitude(.00014)}});
 const alt=raw.physicalState.sun.altDeg,anchor=anchorFor(alt);
 if(alt<-20)raw.nativeLunarDisplayPrepared=true;
 const clone=()=>({status:'ready',raster:{...raw}});
 const fm=accept(mainSrc,clone(),j,anchor),fc=accept(candSrc,clone(),j,anchor);
 const bm=encodeNativeFrame(fm.raster.linear,fm.raster.effectiveExposure),bc=encodeNativeFrame(fc.raster.linear,fc.raster.effectiveExposure);
 const reg=nativeSolarRegistration(raw,j.options.view,anchor),src=reg.source;
 const band=src&&src.inFrame&&src.y>=10&&src.y<=520?Math.round(src.y):287,x0=src&&src.inFrame?Math.max(12,Math.round(src.x)-60):30,x1=Math.min(312,x0+170);
 const ridge=b=>{const P=x=>{let t=0;for(let y=band-3;y<=band+3;y++){const i=4*(y*325+x);t+=.2126*b[i]+.7152*b[i+1]+.0722*b[i+2];}return t/7;};let m=0;for(let x=x0;x<=x1;x++)m=Math.max(m,Math.abs(P(x)-(P(x-9)+P(x+9))/2));return m;};
 let max=0,changed=0,bx0=999,by0=999,bx1=-1,by1=-1;
 for(let p=0;p<325*530;p++){let d=0;for(let k=0;k<3;k++)d=Math.max(d,Math.abs(bm[4*p+k]-bc[4*p+k]));if(d){changed++;const x=p%325,y=(p/325)|0;bx0=Math.min(bx0,x);bx1=Math.max(bx1,x);by0=Math.min(by0,y);by1=Math.max(by1,y);}max=Math.max(max,d);}
 const row={site,scene:label,utc,vis,sunAltDeg:+alt.toFixed(2),sunAzDeg:+raw.physicalState.sun.azDeg.toFixed(2),physicalSunInView:!!src?.inFrame,physicalSunXY:src?[+src.x.toFixed(1),+src.y.toFixed(1)]:null,
  registrationActive:reg.active,ridgeBand:band,ridgeMain:+ridge(bm).toFixed(2),ridgeCandidate:+ridge(bc).toFixed(2),maxCodeDiff:max,pixelsChanged:changed,shareChanged:+(changed/(325*530)).toFixed(4),
  bbox:changed?[bx0,by0,bx1,by1]:null,byteIdentical:changed===0};
 rows.push(row);console.log(JSON.stringify(row));
 if(out){const tag=`${site}-${utc.slice(11,16).replace(':','')}-vis${vis/1000}`;fs.writeFileSync(path.join(out,tag+'.main.rgba'),bm);fs.writeFileSync(path.join(out,tag+'.cand.rgba'),bc);}
}
if(out)fs.writeFileSync(path.join(out,'scene-diff.json'),JSON.stringify({base,rows},null,1));
