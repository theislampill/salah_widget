'use strict';

// Use the disposable generated tree with phase1-options.patch already applied.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const [pwDir,research,root,out,engine]=process.argv.slice(2);
if(!['chromium','firefox','webkit'].includes(engine))throw Error('usage: native-options.cjs PLAYWRIGHT RESEARCH BUILT_TREE NEW_OUT ENGINE');
const L=require(path.resolve(research,'tools/qa/precip_eval_lib.cjs'));
const options={missing:'category',zero:'cover',eyeLevel:.8,cap:null,gust:'unused',night:'environment',reduced:'none'};
async function main(){
  fs.mkdirSync(out);
  const ordinary=JSON.parse(fs.readFileSync(path.resolve(root,'tests/r0002-ordinary.json')));
  const {srv,base}=await L.serve(root);let browser;
  try{
    browser=await require(pwDir)[engine].launch();const cells=[];
    for(const [id,code,ms,os,full,reduced,amount] of [
      ['day-rain',63,12,false,false,'none',1.25],['day-drizzle',53,12,false,false,'none',.3],
      ['day-thunder',95,12,false,false,'none',3],['night',63,0,false,false,'none',1.25],
      ['twilight',63,6,false,false,'none',1.25],['reduced-none',63,12,true,false,'none',1.25],
      ['reduced-still',63,12,true,false,'still',1.25],['motion-full',63,12,true,true,'none',1.25],
      ['dry',3,12,false,false,'none',0]]){
      const opt={...options,reduced};
      const wrapper={async newContext(args){const ctx=await browser.newContext(args);
        await ctx.addInitScript(o=>{window.__R0040_OPTIONS__=o},opt);return ctx;}};
      const site=L.SITES.madinah,date='2026-09-11',sc=id==='twilight'?'blue-hour':ms===0?'night-early':'solar-noon';
      const utcMs=Math.floor(L.sceneTimes(site,date)[sc]/900000)*900000+360000;
      const wx={cloud:95,low:90,mid:80,high:50,temp:60,hum:92,dew:55,vis:20000,wind:20,wdir:90,gust:20,code,precip:amount,rain:amount};
      const s=await L.openScene(wrapper,base,ordinary,{site,utcMs,wx,reduced:os,hash:full?'&motion=full':'',clock:'running'});
      try{
        await L.waitReady(s.page,{maxMs:20000});
        await s.page.waitForFunction(expected=>window.qaState?.().cache?.prayerLoaded&&selectedWeather()?.code===expected,code);
        const state=await s.page.evaluate(()=>{
          const c=document.querySelector('.c'),drops=[...document.querySelectorAll('.wfx .drop')],visible=drops.filter(d=>getComputedStyle(d).display!=='none'&&getComputedStyle(d).visibility==='visible');
          const d=visible[0]||drops[0],css=getComputedStyle(d),mat=new DOMMatrix(css.transform==='none'?undefined:css.transform);
          const angle=parseFloat(c.style.getPropertyValue('--rain-axis')),slant=parseFloat(c.style.getPropertyValue('--rain-slant'));
          return {width:c.getBoundingClientRect().width,height:c.getBoundingClientRect().height,visible:visible.length,
            color:css.backgroundImage,lit:c.dataset.rainLit,axis:angle,slant,computedAxis:Math.atan2(mat.b,mat.a)*180/Math.PI,
            current:selectedWeather()?.precip,animation:css.animationName,duration:css.animationDuration,inlineDuration:d.style.animationDuration,
            playState:css.animationPlayState,glass:getComputedStyle(document.querySelector('.p')).backdropFilter,
            sunElevation:atmosphere(model()).solarElevationDeg,moonlight:atmosphere(model()).moonlightIntensity};
        });
        require('./native-option-oracle.cjs').check(id,state,amount);
        await s.page.screenshot({path:path.join(out,id+'.png')});
        assert.equal(s.log.continuedExternal.length,0);assert.deepEqual(s.log.errors||[],[]);
        cells.push({id,scene:sc,utcMs,options:opt,code,amount,state});
      }finally{await s.ctx.close();}
    }
    fs.writeFileSync(path.join(out,'native-options.json'),JSON.stringify({engine,cells},null,2));
  }finally{try{await browser?.close()}finally{srv.close()}}
}
main().catch(e=>{console.error(e);process.exitCode=1});
