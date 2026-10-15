const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const source=fs.readFileSync(path.join(__dirname,'../src/native/index.html'),'utf8');
function fixture(){
  const node=(left)=>({style:{left,removeProperty(key){delete this[key];}}});
  const drops=[node('10%'),node('90%')],flakes=[node('10%'),node('90%')],card={dataset:{fx:'snow'}};
  const context=vm.createContext({$:()=>card,_colDens:new Float32Array([5,0]),document:{querySelectorAll(selector){return [...(selector.includes('.drop')?drops:[]),...(selector.includes('.flake')?flakes:[])];}}});
  const start=source.indexOf('let _rainTiedFx="";'),end=source.indexOf('// ---- ATMOSPHERE STATE',start);
  assert(start>0&&end>start);vm.runInContext(source.slice(start,end),context);
  return {card,drops,flakes,run(){vm.runInContext('tieRainToClouds()',context);}};
}
test('snow starts at the existing cloud deck inside the card',()=>{
  const css=source.match(/\.wfx \.flake\{([^}]+)\}/)[1];assert.match(css,/(?:^|;)top:19%/);
});
test('snow uses the same cloud columns and withdrawal as rain',()=>{
  const f=fixture();f.run();assert.equal(f.flakes[0].style.display,'');assert.equal(f.flakes[1].style.display,'none');
  f.card.dataset.fx='rain';f.run();assert.equal(f.drops[0].style.display,'');assert.equal(f.drops[1].style.display,'none');
  f.card.dataset.fx='clear';f.run();assert.equal(f.flakes[1].style.display,undefined);assert.equal(f.drops[1].style.display,undefined);
});
