// Effect-free VM probe (lane E). Loads the generated root index.html native inline
// runtime through the existing read-only r001d harness (network denied, no writes).
// Question: if the optional Moon runtime's request() throws, does render() still
// publish the prayer countdown, and does the loop survive? The throwing runtime is
// an injected stub: this demonstrates propagation, NOT a known natural trigger.
const path=require('node:path');
const root=process.argv[2];
const {load}=require(path.join(root,'tests','r001d-harness.cjs'));
function trial(throwing){
  const h=load({});
  h.run('render();');
  const before=h.run('document.querySelector(".cn").textContent');
  h.run('document.querySelector(".cn").textContent="SENTINEL";document.querySelector(".times").innerHTML="";lastMoonMin=-1;');
  h.run('window.SalahMoonRuntime={request(){'+(throwing?'throw new Error("injected Moon request failure")':'return false')+'},surface(){return null},invalidate(){},finishInitialDocument(){},get state(){return {}},get disposed(){return false}};');
  let error=null;try{h.run('render();');}catch(e){error=String(e.message||e);}
  return {throwing,firstRenderCn:before,threw:error,cnAfter:h.run('document.querySelector(".cn").textContent'),timesRowsAfter:h.run('document.querySelector(".times").innerHTML.length')};
}
console.log(JSON.stringify([trial(false),trial(true)],null,1));
