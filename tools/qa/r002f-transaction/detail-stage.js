// Included inside the disposable Moon presenter. Material is reachable through
// its actual accepted record; withdrawal and replacement release the weak key.
const researchMaterial = new WeakMap();
function researchMoonLease(){
 const record=accepted, material=researchMaterial.get(record), runtime=window.SalahMoonRuntime;
 if(!material||!record||waitingPreview||disposed||document.hidden||!matches(record,capture()))return null;
 const originalGeometry=researchGeometryKey();
 if(!originalGeometry)return null;
 const current=()=>!disposed&&!document.hidden&&window.SalahMoonRuntime===runtime&&accepted===record&&!waitingPreview&&matches(record,capture())&&researchGeometryKey()===originalGeometry;
 return {current,token:record.token,prepare(frame,encode){
  if(!current())throw Error('lunar adoption superseded');
  const staging=startResearchDetail(current);
  staging.adopt(material);
  const geometry=staging.geometryKey();
  if(!geometry)throw Error('device Moon footprint unavailable');
  staging.compose(frame,encode);
  if(!staging.state.visible||!current()||staging.geometryKey()!==geometry)throw Error('lunar preparation superseded');
  const node=staging.node;
  node.style.visibility='hidden';
  return {node,geometry,current:()=>current()&&staging.geometryKey()===geometry};
 }};
}
