import test from 'node:test';import assert from 'node:assert/strict';
import * as projection from '../src/projection.mjs';import * as df from '../src/diffuse-map.mjs';import {observationFrame,angularSeparation} from '../src/astronomy.mjs';
test('prepared inverse projection preserves the reference arithmetic across camera and all-sky inputs',()=>{
 assert.equal(typeof projection.prepareInverseProjection,'function');
 for(const type of ['camera','allsky'])for(const rollDeg of [0,27,180,-70])for(const eastLeft of [false,true]){const view={type,width:325,height:530,azDeg:359.5,altDeg:43,fovYDeg:95,rollDeg,eastLeft,padding:9};const f=projection.prepareInverseProjection(view);
 for(let y=0;y<530;y+=31)for(let x=0;x<325;x+=29){const a=f(x+.23,y+.91),b=(type==='camera'?projection.unprojectPerspective:projection.unprojectAllSky)(x+.23,y+.91,view);assert.deepEqual(a,b);}}
});
test('prepared projections own an immutable snapshot and refuse invalid construction/coordinates',()=>{
 assert.equal(typeof projection.prepareInverseProjection,'function');const c={type:'camera',width:20,height:30,rollDeg:10},f=projection.prepareInverseProjection(c),a=f(10,15);c.rollDeg=80;assert.deepEqual(f(10,15),a);assert.throws(()=>f(NaN,0));assert.throws(()=>projection.prepareInverseProjection({type:'camera',fovYDeg:180}));assert.throws(()=>projection.prepareInverseProjection({type:'allsky',width:20,height:20,padding:10}));assert.throws(()=>projection.prepareInverseProjection({type:'nope'}));
});
test('prepared inverse frame exactly matches unprepared astrometry including refraction and time changes',()=>{
 assert.equal(typeof df.prepareHorizontalToDiffuseJ2000,'function');
 for(const latDeg of [-89,-33.87,28.54,64.15,89])for(const month of [0,6])for(const pressureHpa of [0,1010]){const frame=observationFrame({utcMs:Date.UTC(2026,month,15,3),latDeg,lonDeg:39.61,pressureHpa});const convert=df.prepareHorizontalToDiffuseJ2000(frame);
 for(const altDeg of [0,10,35,89.99])for(const azDeg of [0,90,180,359.99]){const h={altDeg,azDeg};assert.deepEqual(convert(h),df.horizontalToDiffuseJ2000(h,frame));}}
});
