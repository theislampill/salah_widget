import test from 'node:test';import assert from 'node:assert/strict';
import {nativeJob} from '../../real-sky/native-contract.mjs';
import {scintillationFactor} from '../../vendor/real-sky/src/visibility.mjs';
const input={utcMs:Date.parse('2026-09-07T20:30Z'),lat:24.47,lon:39.61,heightM:0,generation:0,sceneIdentity:'native',weather:null,lp:0,reducedMotion:false,camera:{azDeg:180,altDeg:45,fovYDeg:90,rollDeg:0}};
test('native disabled scintillation uses the real strength contract, not an ignored enabled flag',()=>{const j=nativeJob(input,true);for(const t of [0,4,8,12])for(const id of ['Sirius','HIP-113368','HIP-102098'])assert.equal(scintillationFactor(id,input.utcMs/1000+t,20,{...j.options.scintillation,reducedMotion:false}),1);});
