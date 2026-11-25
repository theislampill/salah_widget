// Compare delivered samples in both clock domains. Sampling the history at
// 100 ms bounds its size even on high refresh displays.
export class SampleHistory {
  constructor(){this.reset();}
  reset(){this.points=[];this.last=null;}
  add(at,utc,sample,identity){
    const prev=this.last;
    if(prev&&(prev.id!==sample.id||prev.identity!==identity||at<prev.at||at-prev.at>250
       ||utc<prev.utc||Math.abs((utc-prev.utc)-(at-prev.at))>100))this.reset();
    const point={at,utc,factor:sample.factor,id:sample.id,identity};this.last=point;
    if(!this.points.length||at-this.points.at(-1).at>=100)this.points.push(point);
    while(this.points.length&&at-this.points[0].at>60300)this.points.shift();
  }
  line(now){
    const cur=this.last;
    const delta=windowMs=>{
      if(!cur||now-cur.at>250)return '—';
      const p=this.points.reduce((best,p)=>!best||Math.abs(cur.at-p.at-windowMs)<Math.abs(cur.at-best.at-windowMs)?p:best,null);
      if(!p||cur.at-this.points[0].at<windowMs||Math.abs(cur.at-p.at-windowMs)>150||Math.abs(cur.utc-p.utc-windowMs)>150)return '—';
      return (cur.factor-p.factor).toFixed(4);
    };
    return 'factor Δ 10s '+delta(10000)+' 60s '+delta(60000);
  }
}
