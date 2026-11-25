// Experimental thresholds, never a performance PASS. Observe whole presentation
// intervals, including canvas/compositor effects. Do not time the producer alone.
export class FrameGuard {
  constructor(enabled) { this.enabled=enabled;this.reset(); }
  reset() { this.last=null;this.intervals=[];this.slowWindows=0;this.retryAt=0;this.gain=0; }
  observe(now) {
    if(!Number.isFinite(now))throw new RangeError('Finite native frame timestamp required');
    if(this.last!==null && now>this.last) this.intervals.push(now-this.last);
    this.last=now;
    if(this.intervals.length>=30){
      const sorted=this.intervals.sort((a,b)=>a-b),p95=sorted[Math.ceil(.95*sorted.length)-1];this.intervals=[];
      this.slowWindows=p95>50?this.slowWindows+1:0;
      if(this.enabled&&this.slowWindows>=2&&now>=this.retryAt){this.retryAt=now+60000;this.slowWindows=0;}
    }
  }
  nextGain(now) {
    // Applied once per completed sample opportunity, never once per missed rAF.
    const target=!this.enabled||now>=this.retryAt?1:0;
    if(!this.enabled)return this.gain=1;
    this.gain+=Math.sign(target-this.gain)*Math.min(.1,Math.abs(target-this.gain));
    if(this.gain<1e-9)this.gain=0;
    return this.gain;
  }
}
