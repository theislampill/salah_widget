// Exercise the shipped lunar WASM and material in the native foreground join.
// Placement and card geometry are controlled inputs, not browser measurements.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {join} from 'node:path';
import {nativeDiscMask} from '../../real-sky/native-contract.mjs';
import {prepareScene,replayObserver} from './qualification_scene.mjs';
import {prepareReplay} from './prepared_replay.mjs';
const asset=n=>readFileSync(new URL('../../moon/'+n,import.meta.url));
const units=['asset-digest','surface_v5','moon-detail','moon-calendar','moon-engine','moon-quality','moon-precision'];
const api=Function(units.map(n=>asset('src/'+n+'.mjs').toString()).join('\n')+'\nreturn {MoonEngine,canonicalScene};')();
const manifest=JSON.parse(asset('asset-manifest.json'));
const lunar=await api.MoonEngine.create({wasm:asset('moon_kernel.wasm'),dem:asset(manifest.assets.dem.path),colour:asset(manifest.assets.colour.path),manifest});
const read=n=>readFileSync(new URL('../../vendor/real-sky/data/'+n,import.meta.url),'utf8');
const pack={catalogueText:read('bright-stars.json'),manifestText:read('registered-starlight/runtime-manifest.json'),
  assetTexts:{128:read('registered-starlight/V-nside128.json')}};
const t=Date.parse('2026-11-09T00:00:00Z'),{stars,raster}=await prepareScene(pack,{...replayObserver,utcMs:t},'refined');
const config={scope:'all',multiplier:2,glassFactor:1,margin:0},width=325,height=530;
const output=process.argv[2],gallery=process.argv[3];if(gallery)mkdirSync(gallery);
const results={skyUtc:new Date(t).toISOString(),geometry:'synthetic calendar disc center (110,100), diameter 90 CSS pixels; independent physical ephemeris; V5 surface rendered through the real WASM with 96 model samples/side',cells:[]};
for(const [label,fraction] of [['crescent',.08],['half',.5],['gibbous',.90],['full',.99]]){
  const scene=api.canonicalScene({fraction,waxing:true,size:96,outSize:96,diameter:90});
  const rendered=await lunar.render(scene),moonRGBA=new Uint8ClampedArray(width*height*4),x=110,y=100;
  for(let j=0;j<96;j++)moonRGBA.set(rendered.rgba.subarray(4*j*96,4*(j+1)*96),4*((y-48+j)*width+x-48));
  const mask=nativeDiscMask(width,height,{left:0,top:0,width,height},{a:1,b:0,c:0,d:1,e:x,f:y},45);
  const prepared=prepareReplay(raster,stars,config,{glass:[],mask,moonRGBA});
  let changedInside=0,changedOutsideFrames=0,comparedInside=0;
  for(let f=0;f<60;f++){
    const {rgba}=prepared.present(t+1000*f/60);let changedOutside=false;
    for(let p=0;p<mask.length;p++){
      if(mask[p]===0)comparedInside++;
      const changed=rgba[4*p]!==prepared.nominal[4*p]||rgba[4*p+1]!==prepared.nominal[4*p+1]||rgba[4*p+2]!==prepared.nominal[4*p+2];
      if(changed&&mask[p]===0)changedInside++;
      if(changed&&mask[p]===1)changedOutside=true;
    }
    changedOutsideFrames+=+changedOutside;
    if(gallery&&f===0)execFileSync('ffmpeg',['-loglevel','error','-f','rawvideo','-pix_fmt','rgba','-s','325x530','-i','pipe:0','-frames:v','1','-threads','1',join(gallery,label+'.png')],{input:rgba});
  }
  assert.equal(changedInside,0);assert.equal(changedOutsideFrames,60);
  const colors=new Set();for(let p=0;p<96*96;p++)if(rendered.rgba[4*p+3]===255)colors.add(rendered.rgba.subarray(4*p,4*p+3).join(','));
  assert.ok(colors.size>8);
  results.cells.push({label,fraction,kernel:rendered.diagnostics.kernel,surfaceSha256:createHash('sha256').update(rendered.rgba).digest('hex'),
    opaqueMaterialColors:colors.size,physicalIdentity:rendered.physicalIdentity,profileIdentity:rendered.profileIdentity,
    modeledStarsInside:stars.filter(s=>mask[Math.floor(s.y)*width+Math.floor(s.x)]===0).length,
    frames:60,comparedInside,changedInside,changedOutsideFrames});
}
const text=JSON.stringify(results,null,2)+'\n';if(output)writeFileSync(output,text);else process.stdout.write(text);
