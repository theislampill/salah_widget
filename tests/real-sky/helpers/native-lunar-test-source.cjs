'use strict';
const fs=require('node:fs'),path=require('node:path'),{fileURLToPath}=require('node:url');
function nativeLunarOwner(root){
 root=root instanceof URL?fileURLToPath(root):root;
 const source=fs.readFileSync(path.join(root,'src/native/index.html'),'utf8');
 const section=(start,end)=>{if(source.split(start).length!==2||source.split(end).length!==2)throw Error('Native lunar test owner boundary');return source.slice(source.indexOf(start),source.indexOf(end,source.indexOf(start)));};
 const clamp=source.match(/^const clamp=.*$/gm);if(clamp?.length!==1)throw Error('Native lunar test clamp boundary');
 return [clamp[0],section('const _RAD=Math.PI/180','// Galactic centre'),section('function moonPhase(date){','// ---- PBR MOON:'),section('const MOON_SCALE_MIN=','function renderMoon(){'),section('function nativeLunarPresentation(','function lunarPresentation(')].join('\n');
}
// Daytime admission isolates the atmosphere owner. Its new lunar eligibility
// dependency uses actual source math/guards with the stated calendar/no-reference
// context; full lifecycle state is exercised by the separate runtime fixture.
function daytimeHeadCurrent(root){
 root=root instanceof URL?fileURLToPath(root):root;
 const runtime=fs.readFileSync(path.join(root,'moon/src/moon-native.mjs'),'utf8');
 const lines=['const scope=','const phaseDrift=','const phaseError='].map(marker=>{const matches=runtime.split('\n').filter(s=>s.includes(marker));if(matches.length!==1)throw Error('Native lunar guard test boundary');return matches[0];});
 const start=runtime.indexOf(' function headCurrent('),end=runtime.indexOf(' function syncTexture(',start);if(start<0||end<=start)throw Error('Native lunar head guard test boundary');
 const precision=fs.readFileSync(path.join(root,'moon/src/moon-precision.mjs'),'utf8'),head=fs.readFileSync(path.join(root,'moon/src/moon-first-paint.mjs'),'utf8');
 return Function(nativeLunarOwner(root)+'\n'+precision+'\n'+head+'\nlet disposed=false,profileMode="calendar",referenceScene=null;\n'+lines.join('\n')+'\n'+runtime.slice(start,end)+'\nreturn headCurrent;')();
}
module.exports={nativeLunarOwner,daytimeHeadCurrent};
