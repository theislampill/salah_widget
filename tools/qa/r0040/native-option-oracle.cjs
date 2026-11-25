'use strict';
const assert=require('node:assert/strict');
function check(id,state,amount){
  assert.deepEqual([state.width,state.height],[325,530]);assert.equal(state.current,amount);
  const expectedLit=id==='night'?false:true;
  if(id==='night')assert.ok(state.sunElevation< -12&&state.moonlight===0);
  else if(id==='twilight')assert.ok(state.sunElevation>=-12&&state.sunElevation<0);
  else assert.ok(state.sunElevation>0);
  assert.equal(state.lit,expectedLit?'on':'off');
  if(id==='dry'||id==='reduced-none'||!expectedLit){assert.equal(state.visible,0);return;}
  assert.ok(state.visible>0);assert.equal(state.animation,'fall');
  // Known crosswind positive must genuinely produce nonzero lean and rotation.
  assert.ok(state.slant>20&&state.computedAxis< -5);
  assert.ok(Math.abs(state.computedAxis+Math.atan2(state.slant,142)*180/Math.PI)<=5);
  assert.ok(Math.abs(parseFloat(state.duration)-parseFloat(state.inlineDuration))<.001);
  assert.equal(state.playState,id==='reduced-still'?'paused':'running');
}
module.exports={check};
if(require.main===module){
  const v={width:325,height:530,current:1.25,sunElevation:40,lit:'on',visible:30,animation:'fall',
    slant:142,computedAxis:-45,duration:'.8s',inlineDuration:'.8s',playState:'running'};
  check('day-rain',v,1.25);
  assert.throws(()=>check('day-rain',{...v,lit:'off',visible:0},1.25));
  assert.throws(()=>check('day-rain',{...v,computedAxis:0},1.25));
  console.log('positive, suppressed-day and rotation-off option checks pass');
}
