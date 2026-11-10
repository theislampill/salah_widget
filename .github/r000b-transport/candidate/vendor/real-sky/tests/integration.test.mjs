import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';
import {WidgetStarBridge} from '../integration/widget-star-bridge.mjs';
const cat=JSON.parse(fs.readFileSync(new URL('../data/bright-stars.json',import.meta.url)));
const observer={utcMs:Date.UTC(2026,0,15,2),latDeg:28.54,lonDeg:-81.38};
test('bridge reports terminal readiness without taking Moon ownership',()=>{let ready;const b=new WidgetStarBridge(cat,{onTerminal:s=>ready=s});const result=b.project(observer,'accepted');assert.equal(result.status,'ready');assert.equal(ready.sceneIdentity,'accepted');assert.ok(!('moon' in result));});
test('missing catalogue reaches explicit empty terminal state, no synthetic fallback',()=>{let terminal;const b=new WidgetStarBridge(null,{onTerminal:s=>terminal=s});const result=b.project(observer,'accepted');assert.equal(result.sources.length,0);assert.equal(terminal.status,'unavailable');});
test('bridge separates physical lunar occultation from calendar display mask',()=>{const b=new WidgetStarBridge(cat);b.project(observer,'accepted');const s=b.scene.sources.find(s=>s.visible);const c=b.sourceVisibility({physicalMoon:{altDeg:s.altDeg,azDeg:s.azDeg,radiusDeg:.26}});assert.equal(c(s),false);});
test('rendering into a supplied linear background does not modify that input',()=>{const b=new WidgetStarBridge(cat);b.project(observer,'accepted');const bg=new Float64Array(325*530*3).fill(.01),copy=bg.slice();const r=b.render({backgroundLinear:bg,displayTransmissionAt:()=>0});assert.deepEqual(bg,copy);assert.deepEqual(r.linear,bg);});
