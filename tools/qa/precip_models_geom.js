// Pure geometry for the precipitation model prototypes (research only). Loaded in the page before precip_models.js
// and by tests/precip-eval-direction.test.cjs. Conventions follow real-sky/core/src/projection.mjs (rectilinear,
// f = H / (2 tan(fovY/2)) = 265 px for 530 px and 90 deg): camera right = (cos a, -sin a, 0) in (E, N, U),
// forward = (sin a cos e, cos a cos e, sin e), up = (-sin a sin e, -cos a sin e, cos e). Wind FROM theta, speed S:
// air velocity (E, N) = (-S sin theta, -S cos theta). Source of the expected table: the independent verification
// of the precipitation advisory (2026-11-15), section 5.
(function(root){
  const DEG=Math.PI/180;
  function basis(azDeg,altDeg){const a=azDeg*DEG,e=altDeg*DEG;
    return {rt:[Math.cos(a),-Math.sin(a),0],fw:[Math.sin(a)*Math.cos(e),Math.cos(a)*Math.cos(e),Math.sin(e)],up:[-Math.sin(a)*Math.sin(e),-Math.cos(a)*Math.sin(e),Math.cos(e)]};}
  const dot=(p,q)=>p[0]*q[0]+p[1]*q[1]+p[2]*q[2];
  // drop velocity in the world (m/s): horizontal = air, vertical = -vt
  function dropVelocity(windFromDeg,S,vt){const t=windFromDeg*DEG;return [-S*Math.sin(t),-S*Math.cos(t),-vt];}
  // cross-view component u_r (+ = screen-right) and along-view u_f (+ = away from the viewer)
  function components(azDeg,windFromDeg,S){const b=basis(azDeg,0),V=dropVelocity(windFromDeg,S,0);return {ur:dot(V,b.rt),uf:dot(V,[Math.sin(azDeg*DEG),Math.cos(azDeg*DEG),0])};}
  // image-plane velocity (px/s, x right, y DOWN) of a drop at screen pixel (px,py) and depth z (m along forward)
  function imageVelocity(cam,px,py,z,V){const b=basis(cam.az,cam.alt),f=cam.H/(2*Math.tan(cam.fov/2*DEG));
    const VR=dot(V,b.rt),VU=dot(V,b.up),VF=dot(V,b.fw),X=(px-cam.W/2)/f,Y=(cam.H/2-py)/f;   // normalised image coords
    return [f*(VR-X*VF)/z,-(f*(VU-Y*VF)/z)];}
  // screen lean at a pixel: angle of the image velocity from straight down (deg); + = lower end toward screen-right
  function screenLean(cam,px,py,windFromDeg,S,vt){const v=imageVelocity(cam,px,py,1,dropVelocity(windFromDeg,S,vt));return {deg:Math.atan2(v[0],v[1])/DEG,vx:v[0],vy:v[1],speed:Math.hypot(v[0],v[1])};}
  // product cloud drift direction on screen (src/native/index.html: phase -= windX*wspd*dt, windX = -sin(theta)):
  // clusters move toward smaller x for windX > 0. The product does NOT use the camera azimuth.
  function productCloudDriftSign(windFromDeg){const wx=-Math.sin(windFromDeg*DEG);return Math.abs(wx)<1e-9?0:-Math.sign(wx);}
  // product rain slant sign today (rainSlant = windX * wind01 * 120 px): + = screen-right
  function productRainSlantSign(windFromDeg){const wx=-Math.sin(windFromDeg*DEG);return Math.abs(wx)<1e-9?0:Math.sign(wx);}
  const api={basis,components,dropVelocity,imageVelocity,screenLean,productCloudDriftSign,productRainSlantSign};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.__PMGEOM=api;
})(typeof window!=='undefined'?window:globalThis);
