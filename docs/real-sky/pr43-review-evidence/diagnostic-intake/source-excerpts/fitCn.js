let _cnFit="";
function fitCn(M){
  const cn=$(".cn"), nt=$(".nt"), rail=document.querySelector(".arc .rail"),
        hz=document.querySelector(".arc .horizon"), bar=$(".bar");
  if(!cn||!nt||!rail||!hz||!bar) return;
  const key=M.currentKey+"|"+Math.round(M.sunrise)+"|"+Math.round(M.sunset);
  if(key===_cnFit) return;
  const Mu=16, gap=Mu/2;
  const box=el=>{ const r=document.createRange(); r.selectNodeContents(el); return r.getBoundingClientRect(); };
  cn.style.fontSize="30px";
  const g0=box(cn), w30=g0.width, cx=(g0.left+g0.right)/2;
  const ctx=fitCn._x||(fitCn._x=document.createElement("canvas").getContext("2d"));
  ctx.font=`600 30px ${getComputedStyle(cn).fontFamily}`;
  const cm=ctx.measureText(cn.textContent);
  const ascR=(cm.actualBoundingBoxAscent||21)/30, descR=(cm.fontBoundingBoxDescent||7.2)/30;
  const horizonY=hz.getBoundingClientRect().top;
  const svg=rail.ownerSVGElement, L=rail.getTotalLength(), railMatrix=rail.getScreenCTM(), pts=[];
  for(let i=0;i<=200;i++){ const p=rail.getPointAtLength(L*i/200); const s=svg.createSVGPoint(); s.x=p.x; s.y=p.y; pts.push(s.matrixTransform(railMatrix)); }
  const halfAt=ty=>{ let l=-1e9,r=1e9; for(let i=1;i<pts.length;i++){ const a=pts[i-1],b=pts[i]; if((a.y-ty)*(b.y-ty)<=0&&a.y!==b.y){ const t=(ty-a.y)/(b.y-a.y), x=a.x+(b.x-a.x)*t; if(x<cx) l=Math.max(l,x); else r=Math.min(r,x); } } return Math.min(cx-l, r-cx); };
  let font=30;
  for(let i=0;i<12;i++){
    const half=halfAt((horizonY-gap)-ascR*font);
    if(!isFinite(half)||half<=0) break;
    const fit=(2*half-2*Mu)/w30*30, nf=Math.max(13,Math.min(30,fit)), nx=(font+nf)/2;
    if(Math.abs(nx-font)<0.1){ font=nx; break; } font=nx;
  }
  cn.style.fontSize=font.toFixed(1)+"px";
  const gb=box(cn), curTop=parseFloat(getComputedStyle(cn).top)||0;
  cn.style.top=(curTop+((horizonY-gap+descR*font)-gb.bottom)).toFixed(2)+"px";
  const barTop=bar.getBoundingClientRect().top, tgt=(horizonY+barTop)/2;
  const mid=()=>{ const b=box(nt); return (b.top+b.bottom)/2; };
  const curM=parseFloat(getComputedStyle(cn).marginBottom)||0;
  cn.style.marginBottom=(curM+(tgt-mid())).toFixed(2)+"px";
  try{ if(!document.fonts || document.fonts.check('600 24px "Fraunces"')) _cnFit=key; }catch(e){ _cnFit=key; }
}
