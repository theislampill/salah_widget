// R0034 owner-artifact: TEST-ONLY in-page A/B (evaluated by r0034_artifact_probe.cjs with the clock frozen, so the
// product's own compose loop does not run between captures). It rebuilds the accepted frame's daytime display
// decomposition with solar fields on the worker's own background lattice (41x67 instead of the product's 24x40),
// encodes both with the product encoder, and writes the per-pixel code DELTA onto the visible refined canvas for the
// rows below the native foreground support (status.last.composition.updatedRows), where the canvas holds the encoded
// raw raster tail. "restore" puts the saved canvas pixels back. The accepted frame object is not modified. Nothing is
// written to the repository and nothing persists past the page. window.__r34mode = 'patch' | 'restore'.
(async()=>{
 const f=window.realSkyFrame?.(),k=document.querySelector('.real-sky-canvas');if(!f||!k)return {error:'no refined frame/canvas'};
 const ctx=k.getContext('2d');
 if(window.__r34mode==='restore'){if(window.__r34saved){ctx.putImageData(window.__r34saved,0,0);return {restored:true};}return {restored:false};}
 const P=await import('./real-sky/native-preview.mjs'),E=await import('./real-sky/native-encoding.mjs');
 const R=f.raster,st=window.realSkyState(),view=st.last.view,reg=R.displayPresentation.solarRegistration,anchor={...reg.display,presence:reg.presence};
 const src=R.physicalSkyBackgroundLinear,n=src.length,rawLinear=new Float64Array(n);for(let i=0;i<n;i++)rawLinear[i]=R.linear[i]-R.skyBackgroundLinear[i]+src[i];
 const raw={...R,linear:rawLinear,skyBackgroundLinear:src,backgroundLinear:Float64Array.from(src,(v,i)=>v+(R.diffuseLinear?.[i]??0))};
 delete raw.displayPresentation;delete raw.physicalSkyBackgroundLinear;
 const gx=Math.ceil(325/8),gy=Math.ceil(530/8),all=P.nativeAtmosphereFields(R.physicalState,R.atmosphere,view,undefined,gx,gy);
 const patched=P.nativeSkyPresentation({...raw,solarAerosolLinear:all.solarAerosolLinear,solarBackgroundLinear:all.solarBackgroundLinear,lunarBackgroundLinear:all.lunarBackgroundLinear,twilightDisplay:all.twilightDisplay},view,anchor);
 const a=E.encodeNativeFrame(R.linear,R.effectiveExposure),b=E.encodeNativeFrame(patched.linear,R.effectiveExposure);
 const img=ctx.getImageData(0,0,325,530);window.__r34saved=new ImageData(Uint8ClampedArray.from(img.data),325,530);
 const row0=st.last?.composition?.updatedRows??0;let changed=0,maxd=0;
 for(let y=row0;y<530;y++)for(let x=0;x<325;x++){const j=(y*325+x)*4;for(let c=0;c<3;c++){const d=b[j+c]-a[j+c];if(d){changed++;maxd=Math.max(maxd,Math.abs(d));img.data[j+c]=img.data[j+c]+d;}}}
 ctx.putImageData(img,0,0);return {patched:true,grid:[gx,gy],fromRow:row0,channelsChanged:changed,maxCodeDelta:maxd};})()
