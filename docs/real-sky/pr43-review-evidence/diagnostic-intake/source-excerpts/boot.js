async function boot(){
  const generation=_runtimeGeneration;
  if(_cfgMode==="local"||_cfgMode==="preferLocal") enableSettingsAffordance();
  beginSkyScene();
  if(!simulationReady()) return;
  if(QA){ lastWxAt=0; lastWxTry=0; }
  buildSceneOnce();
  renderMoon();
  if(lat==null||lon==null){
    window.SalahStartSkyPreview?.();
    if(_needsDetect && window.SalahConfig){
      _autoDetectStatus="pending";
      let det=null; try{ det=await SalahConfig.coarseDetect(); }catch(e){ det={ok:false}; }
      if(generation!==_runtimeGeneration) return;
      if(det && det.ok){
        bindConfig(SalahConfig.applyHashPrefs(det.cfg,_hashCfg));
        _autoDetectStatus="ok"; _autoDetectSource=det.provider||det.source||"coarse-ip";
        enableSettingsAffordance();
      } else {
        _autoDetectStatus="failed";
        enableSettingsAffordance();
        openSettings();
        startRenderLoop();
        return;
      }
    } else {
      showError("Add lat & lon to the URL");
      return;
    }
  }
  if(!simulationReady()) return;
  startWeather(true);
  render();
  if(window.SalahSkyPreview) window.SalahSkyPreview.update();
  else window.SalahStartSkyPreview?.();
  await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(()=>{
    const turn=new MessageChannel();
    turn.port1.onmessage=()=>{turn.port1.close();turn.port2.close();resolve();};
    turn.port2.postMessage(null);
  })));
  if(generation!==_runtimeGeneration) return;
  fetchWeather(); fetchRadar();
  await loadPrayerData();
  if(generation!==_runtimeGeneration) return;
  startRenderLoop();
}
