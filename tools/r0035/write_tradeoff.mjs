// Number/area of byte-exact writes. These are not browser frame intervals.
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {prepareScene,replayObserver} from './qualification_scene.mjs';
import {prepareReplay} from './prepared_replay.mjs';
import {changedRectangles} from './changed_rectangles.mjs';
const read=n=>readFileSync(new URL('../../vendor/real-sky/data/'+n,import.meta.url),'utf8');
const pack={catalogueText:read('bright-stars.json'),manifestText:read('registered-starlight/runtime-manifest.json'),
  assetTexts:{128:read('registered-starlight/V-nside128.json')}};
const utcMs=Date.parse('2026-11-09T00:00:00Z'),{stars,raster}=await prepareScene(pack,{...replayObserver,utcMs},'refined');
const results={scope:'120 consecutive prescribed 60-Hz clock transitions; clear pre-glass field; pure area and call count, no browser cost',results:[]};
function stats(values){const s=values.sort((a,b)=>a-b);return {median:s[59],p95:s[113],max:s[119]};}
for(const scope of ['preview-members','all'])for(const multiplier of [1,2]){
  const prepared=prepareReplay(raster,stars,{scope,multiplier,glassFactor:1,margin:0},{glass:[]});
  let old=prepared.present(utcMs).rgba.slice();
  const policies=[8,16,32,64,128,530].map(tile=>({tile,calls:[],areas:[]}));
  for(let i=1;i<=120;i++){
    const rgba=prepared.present(utcMs+1000*i/60).rgba;
    for(const p of policies){
      const rects=changedRectangles(old,rgba,325,530,p.tile);
      p.calls.push(rects.length);p.areas.push(rects.reduce((n,r)=>n+r.width*r.height,0));
      const copy=old.slice();
      for(const r of rects)for(let y=r.y;y<r.y+r.height;y++){
        const at=4*(325*y+r.x);copy.set(rgba.subarray(at,at+4*r.width),at);
      }
      assert.ok(Buffer.from(copy.buffer).equals(Buffer.from(rgba.buffer)));
    }
    old.set(rgba);
  }
  for(const p of policies)results.results.push({scope,multiplier,tile:p.tile,calls:stats(p.calls),pixels:stats(p.areas)});
}
console.log(JSON.stringify(results,null,2));
