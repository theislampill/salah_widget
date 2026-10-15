// Fixture-only r0024-forecast-fixture/v1. Load after unchanged classic product bodies.
// Only weatherForecast is decorated; actual decision/reconciliation/header/paint remain product code.
(() => {
  const control=window.__weatherFixtureControl,api=window.__smokeWeather;
  if(!control||!api) throw Error('owned weather fixture control required');
  const original=weatherForecast;
  let installed=null,decorated=false;
  const finite=v=>typeof v==='number'&&Number.isFinite(v);
  const preview=()=>SIM.wx!=null||ADVANCING||_clockPreview;
  const same=(a,b)=>a&&b&&a.generation===b.generation&&a.lat===b.lat&&a.lon===b.lon;
  const refuse=reason=>{throw Error('synthetic forecast refused: '+reason);};
  const invalidate=()=>{_wxDecisionCache=null;if(typeof render==='function')render();};
  const dependency=(track,target,now)=>{
    if(installed&&preview()&&same(installed.target,target)&&now>=installed.issuedAt&&now>=installed.retrievedAt&&now<installed.validUntil&&
      now-installed.retrievedAt<=_WX_FORECAST_TTL) return installed;
    return original(track,target,now);
  };
  api.installSyntheticForecast=(owner,raw)=>{
    control.assertOwned(owner);if(!preview())return refuse('ordinary live lane');
    const now=Date.now(),target=currentWeatherTarget(),a=raw&&raw.amount,p=raw&&raw.probability,e=raw&&raw.probabilityEvent;
    if(!raw||raw.scope!=='simulation-fixture'||raw.policy!=='synthetic-forecast-v1'||raw.provider!=='Synthetic QA'||raw.product!=='probability contract'||
      !same(raw.target,target))return refuse('identity or target');
    if(!finite(raw.issuedAt)||!finite(raw.retrievedAt)||raw.issuedAt<0||raw.retrievedAt<raw.issuedAt||raw.retrievedAt>now||now-raw.retrievedAt>_WX_FORECAST_TTL||
      !finite(raw.validFrom)||!finite(raw.validUntil)||raw.validFrom<=now||raw.validUntil<=raw.validFrom)return refuse('time window');
    if(!a||a.kind!=='interval-amount'||a.units!=='mm'||!finite(a.value)||a.value<0)return refuse('amount');
    if(p!==null&&(!finite(p)||p<0||p>100||!e||e.event!=='precipitation'||e.from!==raw.validFrom||e.to!==raw.validUntil))return refuse('probability event/window');
    if(p===null&&e!==null)return refuse('null probability event');
    if(raw.resolution!=='synthetic fixture; calibration unavailable')return refuse('resolution provenance');
    const accepted=Object.freeze({provider:raw.provider,product:raw.product,scope:raw.scope,policy:raw.policy,
      target:Object.freeze({...target}),issuedAt:raw.issuedAt,retrievedAt:raw.retrievedAt,validFrom:raw.validFrom,validUntil:raw.validUntil,
      amount:Object.freeze({...a}),probability:p,probabilityEvent:e?Object.freeze({...e}):null,resolution:raw.resolution});
    installed=accepted;if(!decorated){weatherForecast=dependency;decorated=true;}invalidate();return accepted;
  };
  api.clearSyntheticForecast=owner=>{control.assertOwned(owner);installed=null;invalidate();};
})();
