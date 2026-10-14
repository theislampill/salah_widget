const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const source=fs.readFileSync(__dirname+'/observer-source.js','utf8');
for(const failure of [0,1,2])for(const throws of [false,true])test(`public clear forwarding: observation failure ${failure}; original throws ${throws}`,()=>{
  let calls=0,reads=0,receiver,args;
  const value={result:true},error={originalError:true};
  const detail={clear(...a){calls++;receiver=this;args=a;if(throws)throw error;return value;},get state(){if(++reads===failure)throw Error('controlled observer failure');return {visible:true};}};
  const c={module:{exports:null},window:{SalahMoonDetail:detail},performance:{now:()=>1},__widgetFixture:{started:0},Date,document:{querySelector:()=>({className:'card',textContent:'value'})}};
  vm.runInNewContext(source,c);c.module.exports();
  const owner={},parameters=[{arg:true},7];let result,caught;
  try{result=Reflect.apply(detail.clear,owner,parameters);}catch(e){caught=e;}
  assert.equal(calls,1);assert.equal(receiver,owner);assert.deepEqual(args,parameters);
  if(throws)assert.equal(caught,error);else{assert.equal(caught,undefined);assert.equal(result,value);}
  assert.equal(c.window.__r000bMoonWithdrawal.observationErrors.length,failure?1:0);
});
