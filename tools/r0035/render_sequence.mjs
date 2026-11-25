// Reproducible synthetic-time signal material. ffmpeg & ffprobe on PATH.
// node tools/r0035/render_sequence.mjs NEW_OUTPUT_DIRECTORY
import assert from 'node:assert/strict';
import {readFileSync,mkdirSync,writeFileSync} from 'node:fs';
import {resolve,join} from 'node:path';
import {spawn,execFileSync} from 'node:child_process';
import {once} from 'node:events';
import {createHash} from 'node:crypto';
import {prepareScene,replayObserver} from './qualification_scene.mjs';
import {prepareReplay} from './prepared_replay.mjs';
import {replayFrame} from './stellar_replay.mjs';
import {PresentationWriter} from './changed_rectangles.mjs';

if(!process.argv[2])throw new Error('A new output directory is required');
const out=resolve(process.argv[2]);mkdirSync(out);
const read=name=>readFileSync(new URL('../../vendor/real-sky/data/'+name,import.meta.url),'utf8');
const pack={catalogueText:read('bright-stars.json'),manifestText:read('registered-starlight/runtime-manifest.json'),
  assetTexts:{128:read('registered-starlight/V-nside128.json')}};
const utcMs=Date.parse('2026-11-09T00:00:00Z'),{raster,stars}=await prepareScene(pack,{...replayObserver,utcMs},'refined');
const width=raster.width,height=raster.height,frames=900,fps=60,foreground={glass:[],mask:null,moonRGBA:null,cloudRGBA:null};
const results={scope:'Synthetic accepted UTC on one fixed native refined raster. No native browser, UI, glass, cloud, calendar Moon, wall-clock cadence or perceptual verdict.',width,height,frames,fps,startUtc:new Date(utcMs).toISOString(),
  encoder:execFileSync('ffmpeg',['-version'],{encoding:'utf8'}).split('\n')[0],sequences:[]};
function framebuffer(){
  const data=new Uint8ClampedArray(width*height*4);
  return {data,putImageData(img,dx,dy,x=0,y=0,w=width,h=height){
    for(let j=y;j<y+h;j++){const i=4*(j*width+x);data.set(img.data.subarray(i,i+4*w),i);}
  }};
}
const digest=bytes=>createHash('sha256').update(bytes).digest('hex');
function png(name,rgba){
  execFileSync('ffmpeg',['-loglevel','error','-f','rawvideo','-pix_fmt','rgba','-s',width+'x'+height,
    '-i','pipe:0','-frames:v','1','-threads','1',join(out,name)],{input:rgba});
}
for(const multiplier of [1,2]){
  const config={scope:'all',multiplier,glassFactor:1,margin:0},prepared=prepareReplay(raster,stars,config,foreground);
  const name='r0035-reconstruction-x'+multiplier+'.mkv',target=join(out,name),hash=createHash('sha256');
  const ff=spawn('ffmpeg',['-loglevel','error','-f','rawvideo','-pix_fmt','rgba','-s',width+'x'+height,
    '-framerate',String(fps),'-i','pipe:0','-an','-c:v','libx264rgb','-crf','0','-preset','medium','-pix_fmt','rgb24',
    '-g','120','-threads','1','-fflags','+bitexact','-flags:v','+bitexact',target],{stdio:['pipe','inherit','inherit']});
  const done=once(ff,'close'),dest=framebuffer(),writer=new PresentationWriter(dest,'changed');
  const writes=[],areas=[],checks=[],ids=[...stars].sort((a,b)=>a.vmag-b.vmag);
  const tracked=[ids[0],ids.find(s=>s.vmag>4.5)],centers=tracked.map(()=>[]);
  if(multiplier===1)png('r0035-unmodulated-sky.png',prepared.nominal);
  for(let i=0;i<frames;i++){
    const utc=utcMs+1000*i/fps,{rgba}=prepared.present(utc);
    // The writer receives recycled buffers, exactly as in the hot presentation path.
    const report=writer.publish({width,height,data:rgba});
    writes.push(report.writes);areas.push(report.pixels);
    assert.ok(Buffer.from(dest.data.buffer).equals(Buffer.from(rgba.buffer)),'dirty destination differs at frame '+i);
    if(i%100===0||i===frames-1){
      const oracle=replayFrame(raster,stars,utc,config,foreground).rgba;
      assert.ok(Buffer.from(oracle.buffer).equals(Buffer.from(rgba.buffer)),'full PSF oracle at frame '+i);
      checks.push({frame:i,sha256:digest(rgba)});
    }
    for(let j=0;j<tracked.length;j++){
      const s=tracked[j],p=4*(Math.floor(s.y)*width+Math.floor(s.x));centers[j].push([...rgba.subarray(p,p+3)]);
    }
    if(i===0)png('r0035-x'+multiplier+'-first.png',rgba);
    hash.update(dest.data);
    // Node may retain a pipe write's backing store until the callback, so wait
    // for that write BEFORE the prepared renderer or mock canvas recycles it.
    await new Promise((ok,fail)=>ff.stdin.write(dest.data,e=>e?fail(e):ok()));
  }
  ff.stdin.end();const [code]=await done;assert.equal(code,0);
  const expected=hash.digest('hex');
  const decoder=spawn('ffmpeg',['-v','error','-i',target,'-f','rawvideo','-pix_fmt','rgba','-threads','1','pipe:1'],{stdio:['ignore','pipe','inherit']});
  const closed=once(decoder,'close'),decoded=createHash('sha256');let bytes=0;
  for await(const chunk of decoder.stdout){decoded.update(chunk);bytes+=chunk.length;}
  assert.equal((await closed)[0],0);assert.equal(bytes,width*height*4*frames);assert.equal(decoded.digest('hex'),expected);
  const ffprobe=JSON.parse(execFileSync('ffprobe',['-v','error','-select_streams','v','-show_entries',
    'stream=codec_name,pix_fmt,width,height,r_frame_rate:format=duration','-of','json',target],{encoding:'utf8'}));
  assert.equal(ffprobe.streams[0].r_frame_rate,'60/1');assert.equal(Number(ffprobe.format.duration),frames/fps);
  const median=a=>[...a].sort((a,b)=>a-b)[Math.floor(a.length/2)];
  results.sequences.push({name,multiplier,ffprobe,sha256:digest(readFileSync(target)),decodedRGBAsha256:expected,
    decodedBytes:bytes,wholeFrameOracle:checks,changedRectanglesComparedEveryFrame:frames,maximumPossiblePixels:width*height,
    medianRectanglesPerUpload:median(writes.slice(1)),medianPixelsPerUpload:median(areas.slice(1)),
    physicallyEligible:prepared.sourceCount,possiblyVariablePixels:prepared.indices.length,
    trackedCenters:tracked.map((s,j)=>({id:s.id,vmag:s.vmag,x:s.x,y:s.y,distinctRGB:new Set(centers[j].map(c=>c.join(','))).size,
      minRGB:[0,1,2].map(k=>Math.min(...centers[j].map(rgb=>rgb[k]))),maxRGB:[0,1,2].map(k=>Math.max(...centers[j].map(rgb=>rgb[k])))}))});
}
writeFileSync(join(out,'sequence-receipt.json'),JSON.stringify(results,null,2)+'\n');
