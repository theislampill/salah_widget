'use strict';
const phases=[.01,.04,.08,.15,.314,.5,.75,.85,.99];
const horizon=[-30,-6,-4,-3,-2.05,-2,-1.95,-1.5,-1,-.5,0,1,2,3,4,6,10];
const weather={
  clear:{weather_code:0,cloud_cover:0,visibility:24000,relative_humidity_2m:55},
  partly:{weather_code:2,cloud_cover:50,visibility:24000,relative_humidity_2m:55},
  overcast:{weather_code:3,cloud_cover:100,visibility:24000,relative_humidity_2m:55},
  fog:{weather_code:45,cloud_cover:100,visibility:500,relative_humidity_2m:98},
  haze:{weather_code:0,cloud_cover:0,visibility:5000,relative_humidity_2m:90}
};
const night='2026-11-15T09:42:00.000Z', twilight='2026-11-15T11:05:00.000Z';
function cells(engine,dpr){
  const result=[];
  function add(group,overrides={}){
    const c={group,epoch:night,fraction:.314,waxing:true,alt:-20,angle:150,weather:'clear',mode:'shipped',
      repeats:1,owner:false,motion:'reduce',gpu:'default',...overrides};
    c.id=[group,c.epoch.slice(5,16).replace(/[^0-9]/g,''),c.owner?'owner':c.fraction,c.waxing?'wax':'wane',c.alt,c.angle,c.weather,c.mode,c.motion,c.gpu].join('_');
    result.push(c);
  }
  for(const fraction of phases)for(const waxing of [true,false])add('phase',{fraction,waxing});
  add('owner',{owner:true,alt:-81.9});add('owner-control',{alt:20});
  add('ineligible',{mode:'daylight',alt:20,epoch:'2026-11-15T17:00:00.000Z'});
  add('ineligible',{mode:'unavailable',alt:20});
  for(const fraction of phases)for(const waxing of [true,false])add('physical',{fraction,waxing,alt:20});
  if(dpr===1){
    for(const fraction of [.314,.85,.99])for(const w of Object.keys(weather))for(const epoch of [night,twilight])
      add('weather',{fraction,waxing:fraction!==.85,weather:w,epoch});
    for(const fraction of [.08,.314,.5,.85,.99])for(const alt of horizon)add('horizon',{fraction,waxing:![.5,.85].includes(fraction),alt});
    if(engine!=='webkit')for(const fraction of [.314,.99])for(const motion of ['reduce','no-preference'])
      add('motion',{fraction,epoch:'2026-11-03T05:50:00.000Z',motion,alt:null});
  }
  for(const [w,fraction] of [['partly',.314],['clear',.99]])for(const mode of ['shipped','no-backdrop','away','long-text','hour-min','hour-max']){
    add('strap',{weather:w,fraction,mode,repeats:10,angle:mode==='hour-min'?-180:mode==='hour-max'?180:150});
  }
  for(const fraction of [.85,.08,.99,.314])for(const gpu of ['default','software'])for(const mode of ['shipped','header-toggle'])
    add('buckle',{fraction,owner:fraction===.314,alt:fraction===.314?-81.9:-20,mode,gpu,repeats:20});
  return result;
}
function fragment(c,offset=false){
  const base='#lat=28.54&lon=-81.38&label=Orlando&method=2&tz=America%2FNew_York&seed=1&qa=1';
  if(c.group==='owner-control')return base+'&simMoonAlt=20'+(offset?'&simMoon=.01&simWax=1':'');
  if(c.owner)return base+(offset?'&simMoon=0.01&simWax=1':'');
  const phase='&simMoon='+(offset?.01:c.fraction)+'&simWax='+(c.waxing?1:0);
  if(c.group==='motion')return base+phase+'&timeScale=60';
  return base+phase+'&simMoonAlt='+c.alt+'&simMoonH='+c.angle;
}
module.exports={cells,weather,fragment,phases,horizon,night};
