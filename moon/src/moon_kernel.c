/* Moon terrain worker kernel, MB1. Derived from the preserved V4-R1 reference.
 * Numerical units: kilometres, radians, nominal relative linear light.
 * No phase images, sphere day-mask, fabricated relief, or main-thread runtime.
 * Conservative bounds apply to this bilinear radial DEM, not unseen terrain.
 */
#include <stdint.h>
#include <stddef.h>
#ifdef __wasm__
#define IMPORT(n) __attribute__((import_module("math"),import_name(#n))) extern double n(double)
IMPORT(sin); IMPORT(cos); IMPORT(asin); IMPORT(atan); IMPORT(exp); IMPORT(expm1); IMPORT(log);
__attribute__((import_module("math"),import_name("atan2"))) extern double atan2(double,double);
__attribute__((import_module("math"),import_name("pow"))) extern double pow(double,double);
#define sqrt __builtin_sqrt
#define floor __builtin_floor
#define ceil __builtin_ceil
#define fabs __builtin_fabs
#define isfinite __builtin_isfinite
extern unsigned char __heap_base;
static uintptr_t heap_end=0;
void *memset(void *dst,int c,size_t n){unsigned char *d=dst;for(size_t i=0;i<n;i++)d[i]=(unsigned char)c;return dst;}
void *memcpy(void *dst,const void *src,size_t n){unsigned char *d=dst;const unsigned char*s=src;for(size_t i=0;i<n;i++)d[i]=s[i];return dst;}
static void *space(size_t n){
 if(!heap_end)heap_end=(uintptr_t)&__heap_base;
 uintptr_t a=(heap_end+15)&~(uintptr_t)15, end=a+n;
 if(end<a||end>512u*1024u*1024u)return 0;
 size_t pages=__builtin_wasm_memory_size(0),needed=(end+65535)/65536;
 if(needed>pages && __builtin_wasm_memory_grow(0,needed-pages)==(size_t)-1)return 0;
 heap_end=end;return (void*)a;
}
#else
#include <math.h>
#include <stdlib.h>
#include <string.h>
static void *space(size_t n){return malloc(n);}
#endif
#define API __attribute__((visibility("default")))
#define PI 3.141592653589793238462643383279502884
static double mn(double a,double b){return a<b?a:b;}
static double mx(double a,double b){return a>b?a:b;}
static double clip(double a,double lo,double hi){return mx(lo,mn(hi,a));}
static int clampi(int a,int l,int h){return a<l?l:a>h?h:a;}
static int mod(int a,int b){int r=a%b;return r<0?r+b:r;}
typedef struct {double x,y,z;} V;
typedef struct {double lo,hi;} Bound;
typedef struct {double t;int code,visits;} Hit;
static V vec(double x,double y,double z){V a={x,y,z};return a;}
static V add(V a,V b){return vec(a.x+b.x,a.y+b.y,a.z+b.z);}
static V sub(V a,V b){return vec(a.x-b.x,a.y-b.y,a.z-b.z);}
static V mul(V a,double s){return vec(a.x*s,a.y*s,a.z*s);}
static double dot(V a,V b){return a.x*b.x+a.y*b.y+a.z*b.z;}
static double norm(V a){return sqrt(dot(a,a));}
static V unit(V a){return mul(a,1/norm(a));}
static V cross(V a,V b){return vec(a.y*b.z-a.z*b.y,a.z*b.x-a.x*b.z,a.x*b.y-a.y*b.x);}
static V at(V o,V d,double t){return add(o,mul(d,t));}
static uint16_t *dem=0,*colour=0,*pmin[16],*pmax[16];
static int DW,DH,CW,CH,pw[16],ph[16],levels;
static double hmin,hmax,R=1737.4;
static float *colour_lut=0;
static double height(uint16_t h){return (double)(float)(((float)h-20000.0f)/2000.0f);}
static double dh(int y,int x){return height(dem[y*DW+mod(x,DW)]);}
static double uv(double u,double v){
 v=clip(v,0,DH-1);int j=(int)floor(u),i=(int)floor(v),i1=clampi(i+1,0,DH-1);double fx=u-j,fy=v-i;
 return (dh(i,j)*(1-fx)+dh(i,j+1)*fx)*(1-fy)+(dh(i1,j)*(1-fx)+dh(i1,j+1)*fx)*fy;
}
static double sample_h(double lon,double lat){return uv((lon/(2*PI)+.5)*DW-.5,(.5-lat/PI)*DH-.5);}
static V gradient(double lon,double lat){
 double u=(lon/(2*PI)+.5)*DW-.5,v=clip((.5-lat/PI)*DH-.5,0,DH-1);int j=(int)floor(u),i=(int)floor(v),i1=clampi(i+1,0,DH-1);double fx=u-j,fy=v-i;
 double a=dh(i,j),b=dh(i,j+1),c=dh(i1,j),d=dh(i1,j+1);
 return vec((a*(1-fx)+b*fx)*(1-fy)+(c*(1-fx)+d*fx)*fy,((b-a)*(1-fy)+(d-c)*fy)*DW/(2*PI),-((c-a)*(1-fx)+(d-b)*fx)*DH/PI);
}
static double sample_c(double lon,double lat,int ch){
 double u=(lon/(2*PI)+.5)*CW-.5,v=clip((.5-lat/PI)*CH-.5,0,CH-1);int j=(int)floor(u),i=(int)floor(v),i1=clampi(i+1,0,CH-1),j0=mod(j,CW),j1=mod(j+1,CW);double fx=u-j,fy=v-i;
 double a=colour_lut[colour[(i*CW+j0)*3+ch]],b=colour_lut[colour[(i*CW+j1)*3+ch]],c=colour_lut[colour[(i1*CW+j0)*3+ch]],d=colour_lut[colour[(i1*CW+j1)*3+ch]];
 return (a*(1-fx)+b*fx)*(1-fy)+(c*(1-fx)+d*fx)*fy;
}
static double residual(V p){double rr=norm(p);return rr-R-sample_h(atan2(p.y,p.x),asin(clip(p.z/rr,-1,1)));}
API uintptr_t alloc_buffer(int bytes){if(bytes<0)return 0;return (uintptr_t)space((size_t)bytes);}
API int init_assets(uint16_t *D,int w,int h,uint16_t *C,int cw,int ch){
 if(!D||!C||w<2||h<2||cw<2||ch<2||w>8192||h>8192||cw>8192||ch>8192)return 0;
 DW=w;DH=h;CW=cw;CH=ch;dem=D;colour=C;
 uint16_t lo=65535,hi=0;for(size_t i=0;i<(size_t)w*h;i++){if(D[i]<lo)lo=D[i];if(D[i]>hi)hi=D[i];}
 hmin=height(lo);hmax=height(hi);if(hmin< -12||hmax>15)return 0;
 pmin[0]=dem;pmax[0]=dem;pw[0]=w;ph[0]=h;levels=1;
 while(w>1||h>1){
  int nw=(w+1)/2,nh=(h+1)/2,l=levels;uint16_t *a=space((size_t)nw*nh*2),*b=space((size_t)nw*nh*2);if(!a||!b)return 0;
  pmin[l]=a;pmax[l]=b;pw[l]=nw;ph[l]=nh;
  for(int y=0;y<nh;y++)for(int x=0;x<nw;x++){
   uint16_t mi=65535,ma=0;
   for(int dy=0;dy<2;dy++)for(int dx=0;dx<2;dx++){int i=clampi(2*y+dy,0,h-1)*w+clampi(2*x+dx,0,w-1);uint16_t va=pmin[l-1][i],vb=pmax[l-1][i];if(va<mi)mi=va;if(vb>ma)ma=vb;}
   a[y*nw+x]=mi;b[y*nw+x]=ma;
  }
  levels++;w=nw;h=nh;
 }
 colour_lut=space(65536*sizeof(float));if(!colour_lut)return 0;
 for(int i=0;i<65536;i++){double s=(double)((float)i/65535.0f);colour_lut[i]=(float)(s<=.04045?s/12.92:pow((s+.055)/1.055,2.4));}
 return 1;
}
static Bound rectangle(double u0,double u1,double v0,double v1){
 int j0=(int)floor(u0),j1=(int)floor(u1)+1,i0=clampi((int)floor(v0),0,DH-1),i1=clampi((int)floor(v1)+1,0,DH-1);
 int span=clampi(j1-j0+1,0,DW),start=mod(j0,DW),l=0,ext=span>i1-i0+1?span:i1-i0+1;
 while(l+1<levels&&(1<<(l+1))<=ext)l++;
 int scale=1<<l,count=start+span<=DW?1:2;uint16_t lo=65535,hi=0;
 for(int k=0;k<count;k++){
  int a=k==0?start:0,b=k==0?clampi(start+span-1,0,DW-1):start+span-1-DW;
  for(int i=i0/scale;i<=i1/scale;i++)for(int j=a/scale;j<=b/scale;j++){int ix=i*pw[l]+j;uint16_t va=pmin[l][ix],vb=pmax[l][ix];if(va<lo)lo=va;if(vb>hi)hi=vb;}
 }
 return (Bound){height(lo),height(hi)};
}
static Bound local_bounds(double u0,double u1,double v0,double v1){
 v0=clip(v0,0,DH-1);v1=clip(v1,0,DH-1);
 if(u1-u0>3||v1-v0>3)return rectangle(u0,u1,v0,v1);
 double xs[6],ys[6];int nx=1,ny=1;xs[0]=u0;ys[0]=v0;
 for(int j=(int)ceil(u0);j<=(int)floor(u1);j++)xs[nx++]=j;
 for(int i=(int)ceil(v0);i<=(int)floor(v1);i++)ys[ny++]=i;
 xs[nx++]=u1;ys[ny++]=v1;double lo=1e30,hi=-1e30;
 for(int i=0;i<nx;i++)for(int j=0;j<ny;j++){double a=uv(xs[i],ys[j]);lo=mn(lo,a);hi=mx(hi,a);}
 return (Bound){lo,hi};
}
API double probe_wrap(double x){return x>PI?x-2*PI:x< -PI?x+2*PI:x;}
static Bound segment(V o,V d,double a,double b){
 V pa=at(o,d,a),pb=at(o,d,b);double od=dot(o,d),dd=dot(d,d),t=clip(-od/dd,a,b),rl=norm(at(o,d,t)),rh=mx(norm(pa),norm(pb));
 if(rl>R+hmax||rh<R+hmin)return (Bound){rl-R-hmax,rh-R-hmin};
 double dxy=d.x*d.x+d.y*d.y,txy=clip(-(o.x*d.x+o.y*d.y)/mx(dxy,1e-30),a,b);V xy=at(o,d,txy);
 if(xy.x*xy.x+xy.y*xy.y<1e-18)return (Bound){rl-R-hmax,rh-R-hmin};
 double l0=atan2(pa.y,pa.x),l1=atan2(pb.y,pb.x),dl=probe_wrap(l1-l0);l1=l0+dl;
 double u0=(mn(l0,l1)/(2*PI)+.5)*DW-.5,u1=(mx(l0,l1)/(2*PI)+.5)*DW-.5;
 double p0=atan2(pa.z,sqrt(pa.x*pa.x+pa.y*pa.y)),p1=atan2(pb.z,sqrt(pb.x*pb.x+pb.y*pb.y)),pl=mn(p0,p1),phh=mx(p0,p1);
 double C=dot(o,o),den=d.z*od-o.z*dd;
 if(fabs(den)>1e-20){double te=-(d.z*C-o.z*od)/den;if(a<te&&te<b){V p=at(o,d,te);double lt=atan2(p.z,sqrt(p.x*p.x+p.y*p.y));pl=mn(pl,lt);phh=mx(phh,lt);}}
 Bound h=local_bounds(u0,u1,(.5-phh/PI)*DH-.5,(.5-pl/PI)*DH-.5);
 return (Bound){rl-R-h.hi,rh-R-h.lo};
}
static Hit trace(V o,V d,double start,double end,double tol,int maxnodes,int any){
 if(end<=start)return (Hit){end,0,0};
 double aa[80],bb[80],pending=0;int have=0,top=1,visits=0,unknown=0;aa[0]=start;bb[0]=end;
 while(top){
  --top;double a=aa[top],b=bb[top];visits++;if(visits>maxnodes)return (Hit){a,2,visits};
  Bound B=segment(o,d,a,b);if(B.lo>1e-9)continue;
  if(any){
   double mid=(a+b)*.5;if(B.hi< -1e-9)return (Hit){mid,1,visits};
   double ts[3]={a,mid,b};for(int i=0;i<3;i++)if(residual(at(o,d,ts[i]))< -1e-9)return (Hit){ts[i],1,visits};
   if(b-a<=mn(tol,1e-7)){unknown=1;continue;}
   if(top+2>80){unknown=1;continue;}
  }else{
   if(residual(at(o,d,a))<=0){if(have&&a-pending>tol)return (Hit){pending,2,visits};return (Hit){a,1,visits};}
   if(b-a<=tol){
    for(int i=1;i<=4;i++){double t=a+(b-a)*(i*.25);if(residual(at(o,d,t))<=0){if(have&&t-pending>tol)return (Hit){pending,2,visits};return (Hit){t,1,visits};}}
    if(b-a<=1e-7){if(!have){pending=a;have=1;}continue;}
   }
   if(top+2>80)return (Hit){a,2,visits};
  }
  double m=(a+b)*.5;aa[top]=m;bb[top++]=b;aa[top]=a;bb[top++]=m;
 }
 return (Hit){have?pending:end,(have||unknown)?2:0,visits};
}
static double source_exit(V P,V s,double rho,double outer){
 double along=dot(P,s),rr=dot(P,P),cr=sqrt(mx(0,rr-along*along));double mi=rho==0?along:along*cos(rho)-cr*sin(rho);if(rho>=PI/2)mi=-sqrt(rr);
 return mx(0,-mi+sqrt(mx(0,mi*mi+outer*outer-rr)));
}
static Bound cone_segment(V P,V s,double a,double b,double rho){
 V pa=at(P,s,a),pb=at(P,s,b),pc=at(P,s,clip(-dot(P,s),a,b));double e=2*mx(fabs(a),fabs(b))*sin(rho/2),rl=mx(0,norm(pc)-e),rh=mx(norm(pa),norm(pb))+e;
 Bound global={rl-R-hmax-1e-8,rh-R-hmin+1e-8};if(rl>R+hmax||rh<R+hmin)return global;
 V C=at(P,s,(a+b)*.5);double c=norm(C),radius=(b-a)*.5+e;if(c<=radius||c==0)return global;
 double angle=asin(mn(1,radius/c))+1e-12,lat=asin(clip(C.z/c,-1,1)),lon=atan2(C.y,C.x);if(fabs(lat)+angle>=PI/2)return global;
 double dl=asin(mn(1,sin(angle)/mx(1e-15,cos(lat))));Bound h=local_bounds(((lon-dl)/(2*PI)+.5)*DW-.5,((lon+dl)/(2*PI)+.5)*DW-.5,(.5-(lat+angle)/PI)*DH-.5,(.5-(lat-angle)/PI)*DH-.5);
 return (Bound){rl-R-h.hi-1e-8,rh-R-h.lo+1e-8};
}
/* A shadow is existential in distance: a single slab strictly inside the
 * represented body for EVERY cap direction proves full-source blockage. These
 * sampled distances are only positive witnesses; failed probes never prove clear. */
static int cap_block_witness(V P,V s,double rho,double eps,double end){
 double tc=clip(-dot(P,s),eps,end);
 if(cone_segment(P,s,tc,tc,rho).hi<0)return 1;
 for(double t=eps*2;t<end;t*=2)if(cone_segment(P,s,t,t,rho).hi<0)return 1;
 return 2;
}
static int classify_cap(V P,V s,double rho,double eps,int maxnodes){
 double end=source_exit(P,s,rho,R+hmax+1e-5);if(end<=eps)return 0;if(maxnodes<=0)return 2;
 double aa[80],bb[80];aa[0]=eps;bb[0]=end;int top=1,visits=0,unknown=0;
 while(top){--top;double a=aa[top],b=bb[top];if(++visits>maxnodes)return cap_block_witness(P,s,rho,eps,end);
  Bound B=cone_segment(P,s,a,b,rho);if(B.lo>0)continue;if(B.hi<0)return 1;
  if(b-a<=1e-5||top+2>80){unknown=1;continue;}
  double m=(a+b)*.5;aa[top]=m;bb[top++]=b;aa[top]=a;bb[top++]=m;
 }
 return unknown?cap_block_witness(P,s,rho,eps,end):0;
}
API double probe_height(double lon,double lat){return sample_h(lon,lat);}
API void probe_segment(double *o,double *d,double a,double b,double *out){Bound z=segment(vec(o[0],o[1],o[2]),vec(d[0],d[1],d[2]),a,b);out[0]=z.lo;out[1]=z.hi;}
API void probe_trace(double *o,double *d,double a,double b,double tol,int nodes,int any,double*out){Hit z=trace(vec(o[0],o[1],o[2]),vec(d[0],d[1],d[2]),a,b,tol,nodes,any);out[0]=z.t;out[1]=z.code;out[2]=z.visits;}
API int probe_cap(double *p,double*s,double rho,double eps){return classify_cap(vec(p[0],p[1],p[2]),vec(s[0],s[1],s[2]),rho,eps,128);}

/* Stable private ABI: p[0..2], n[3..5], material[6..8], outgoing[9..11],
 * solar 12, Earth 13, unshadowed solar 14, solar/earth unknown 15/16,
 * coverage 17, camera-quality 18, camera nodes 19, source classes 20/21.
 */
static double *pixels=0;static size_t capacity=0;
#ifdef __wasm__
static uintptr_t frame_mark=0;
#endif
static int N=0,nr=8,na=32,rule_n=0;
static V basis[3],Sun,Earth,O;static double distance,extent,tolerance,epsilon,model_k,gain,rho;
static double gnodes[64],gweights[64],rule_t[8192],rule_c[8192],rule_s[8192],rule_w[8192],sun_w[8192];static V sun_d[8192];
static double counters[8]={0};
static V readv(double*p){return vec(p[0],p[1],p[2]);}
static void putv(double*p,V v){p[0]=v.x;p[1]=v.y;p[2]=v.z;}
static void gauss(int order){
 for(int i=0;i<(order+1)/2;i++){
  double z=cos(PI*(i+.75)/(order+.5)),p=0,dp=0;
  for(int it=0;it<30;it++){double p0=1,p1=z;for(int j=2;j<=order;j++){double q=((2*j-1)*z*p1-(j-1)*p0)/j;p0=p1;p1=q;}p=order==1?z:p1;dp=order*(z*p-p0)/(z*z-1);double next=z-p/dp;if(fabs(next-z)<2e-16){z=next;break;}z=next;}
  /* Re-evaluate derivative at the final root. */
  double p0=1,p1=z;for(int j=2;j<=order;j++){double q=((2*j-1)*z*p1-(j-1)*p0)/j;p0=p1;p1=q;}p=order==1?z:p1;dp=order*(z*p-p0)/(z*z-1);
  double w=2/((1-z*z)*dp*dp);gnodes[i]=-z;gnodes[order-1-i]=z;gweights[i]=w;gweights[order-1-i]=w;
 }
}
static void make_rule(int r,int a){
 nr=r;na=a;rule_n=r*a;gauss(r);V v=fabs(Sun.z)<.9?vec(0,0,1):vec(0,1,0),u=unit(cross(v,Sun));v=cross(Sun,u);
 double cosmin=cos(rho),normalizer=0;int q=0;
 for(int j=0;j<r;j++)for(int i=0;i<a;i++,q++){
  double angle=(i+.5*(j%2))*2*PI/a;
  rule_t[q]=(gnodes[j]+1)/2;rule_c[q]=cos(angle);rule_s[q]=sin(angle);rule_w[q]=gweights[j]*.5/a;
  double ct=cosmin+(gnodes[j]+1)*.5*(1-cosmin),st=sqrt(mx(0,1-ct*ct));
  sun_d[q]=add(mul(Sun,ct),mul(add(mul(u,rule_c[q]),mul(v,rule_s[q])),st));sun_w[q]=rule_w[q];normalizer+=sun_w[q]*dot(sun_d[q],Sun);
 }
 for(int i=0;i<q;i++)sun_w[i]/=normalizer;
}
API int set_rule(int radial,int azimuth){if(radial<1||radial>64||azimuth<4||azimuth>256||radial*azimuth>8192)return 0;make_rule(radial,azimuth);return 1;}
API int begin_scene(int size,double*b,double*s,double*e,double dist,double ex,double tol,double eps,double k,double gg,double solar_rho,int radial,int azimuth){
 if(!dem||size<8||size>768||!isfinite(dist)||dist<=R+hmax||!isfinite(ex)||ex<1||ex>2||tol<=0||eps<=0||k<0||k>1||gg<=0||solar_rho<0||solar_rho>.1)return 0;
 for(int i=0;i<9;i++)if(!isfinite(b[i]))return 0;
 for(int i=0;i<3;i++){if(!isfinite(s[i])||!isfinite(e[i]))return 0;basis[i]=readv(b+3*i);}
 if(fabs(dot(basis[0],basis[1]))>1e-10||fabs(dot(basis[0],basis[2]))>1e-10||fabs(dot(basis[1],basis[2]))>1e-10||dot(cross(basis[0],basis[1]),basis[2])<.999999999)return 0;
 for(int i=0;i<3;i++)if(fabs(norm(basis[i])-1)>1e-10)return 0;
 Sun=readv(s);if(fabs(norm(Sun)-1)>1e-10)return 0;Sun=unit(Sun);Earth=readv(e);if(norm(Earth)<=R+hmax+6371)return 0;
 N=size;distance=dist;extent=ex;tolerance=tol;epsilon=eps;model_k=k;gain=gg;rho=solar_rho;O=mul(basis[2],dist);
 size_t need=(size_t)N*N*24;if(need>capacity){
#ifdef __wasm__
 if(!frame_mark)frame_mark=heap_end;else heap_end=frame_mark;
#else
 if(pixels)free(pixels);
#endif
 pixels=space(need*sizeof(double));if(!pixels)return 0;capacity=need;}memset(pixels,0,need*sizeof(double));memset(counters,0,sizeof(counters));
 return set_rule(radial,azimuth);
}
API uintptr_t get_pixels(void){return (uintptr_t)pixels;}
API uintptr_t get_counters(void){return (uintptr_t)counters;}
API int pixel_stride(void){return 24;}
API int camera_rows(int first,int count){
 if(!pixels||first<0||count<0||first+count>N)return -1;
 double outer=R+hmax+1e-4,half=extent*R/sqrt((distance-R)*(distance+R));int unknown=0;
 for(int y=first;y<first+count;y++)for(int x=0;x<N;x++){
  double *z=pixels+24*(y*N+x),xx=(2*(x+.5)/N-1)*half,yy=(1-2*(y+.5)/N)*half;
  V d=unit(sub(add(mul(basis[0],xx),mul(basis[1],yy)),basis[2]));double ct=-dot(O,d);V org=at(O,d,ct);double rr2=dot(org,org);
  if(rr2>=outer*outer)continue;double dt=sqrt(mx(0,outer*outer-rr2));Hit hit=trace(org,d,mx(-dt,-ct),dt,tolerance,20000,0);
  z[18]=hit.code;z[19]=hit.visits;counters[0]+=hit.visits;
  if(hit.code!=1){if(hit.code==2){unknown++;if(rr2<(R+hmin)*(R+hmin)){z[17]=1;counters[6]++;}else counters[7]++;}continue;}
  V p=at(org,d,hit.t);double r=norm(p),lon=atan2(p.y,p.x),lat=asin(clip(p.z/r,-1,1));V g=gradient(lon,lat);p=mul(p,(R+g.x)/r);r=R+g.x;
  double cl=cos(lon),sl=sin(lon),cp=cos(lat),sp=sin(lat),hl=g.y/mx(1e-8,r*cp),hp=g.z/r;
  V n=unit(vec(cp*cl+hl*sl+hp*sp*cl,cp*sl-hl*cl+hp*sp*sl,sp-hp*cp));
  putv(z,p);putv(z+3,n);for(int c=0;c<3;c++)z[6+c]=(float)sample_c(lon,lat,c);putv(z+9,unit(sub(O,p)));z[17]=1;
 }
 return unknown;
}
static double disk(double mu0,double mu){return model_k*2*mu0/(mu0+mu)+(1-model_k)*mu0;}
static double blocker_t=-1;static int witness_enabled=1;
API void set_witness_reuse(int enabled){witness_enabled=!!enabled;}
static int visible(V p,V d,int cap){
 if(cap!=2)return cap;double end=source_exit(p,d,0,R+hmax+1e-5);
 /* A concrete previous blocker is a new-ray witness only after the ACTUAL new
  * point is tested strictly inside terrain. Never infer clearance from it. */
 if(witness_enabled&&blocker_t>epsilon&&blocker_t<end&&residual(at(p,d,blocker_t))< -1e-9){counters[4]++;return 1;}
 Hit h=trace(p,d,epsilon,end,tolerance,20000,1);counters[1]+=h.visits;counters[2]++;if(h.code==1)blocker_t=h.t;return h.code;
}
static double analytic_cap(double mu,double nu){
 if(rho==0)return disk(nu,mu);double delta=2*sin(rho/2)*sin(rho/2),out=0;
 for(int j=0;j<nr;j++){
  double u=1-delta*(1-gnodes[j])/2,v2=(1-nu*nu)*mx(0,(1-u)*(1+u)),a=mu+nu*u,rt=sqrt(mx(0,a*a-v2));
  double ratio=(2*mu*nu*u+nu*nu*u*u-v2)/(rt*(rt+mu));out+=gweights[j]*ratio;
 }
 return model_k*out*2/(2-delta)+(1-model_k)*nu;
}
static int light_rows_impl(int first,int count,int lights,int bundle,int analytic,const uint8_t *mask){
 if(!pixels||first<0||count<0||first+count>N)return 0;
 for(int y=first;y<first+count;y++)for(int x=0;x<N;x++){
  int selected=mask?(lights&mask[y*N+x]):lights;if(!selected)continue;
  double*z=pixels+24*(y*N+x);if(z[18]!=1)continue;V p=readv(z),n=readv(z+3),v=readv(z+9);double mu=dot(n,v);if(mu<=0)continue;
  if(selected&1){
   blocker_t=-1;
   z[12]=z[14]=z[15]=0;z[20]=255;double nu=dot(n,Sun),crossn=sqrt(mx(0,1-nu*nu));
   if(nu*cos(rho)+crossn*sin(rho)>0){
    int c=bundle?classify_cap(p,Sun,rho,epsilon,128):2;z[20]=c;
    if(analytic&&c==0&&nu*cos(rho)-crossn*sin(rho)>0){z[12]=z[14]=analytic_cap(mu,nu);counters[3]++;}
    else for(int j=0;j<rule_n;j++){
     double mu0=dot(n,sun_d[j]);if(mu0<=0)continue;double f=sun_w[j]*disk(mu0,mu);z[14]+=f;int code=visible(p,sun_d[j],c);if(code==0)z[12]+=f;else if(code==2)z[15]+=f;
    }
   }
  }
  if(selected&2){
   blocker_t=-1;
   z[13]=z[16]=0;V rel=sub(Earth,p);double dist=norm(rel);V axis=mul(rel,1/dist);double erho=asin(6371./dist),delta=2*sin(erho/2)*sin(erho/2);V v0=fabs(axis.z)<.9?vec(0,0,1):vec(0,1,0),u=unit(cross(v0,axis));v0=cross(axis,u);
   int c=bundle?classify_cap(p,axis,erho,epsilon,128):2;z[21]=c;
   if(c==1)continue;
   for(int j=0;j<rule_n;j++){
    double ct=1-delta*(1-rule_t[j]),st=sqrt(mx(0,(1-ct)*(1+ct)));V di=add(mul(axis,ct),mul(add(mul(u,rule_c[j]),mul(v0,rule_s[j])),st));double mu0=dot(n,di);if(mu0<=0)continue;
    double td=dist*ct-sqrt(mx(0,6371.*6371.-dist*dist*st*st));V en=mul(sub(at(p,di,td),Earth),1/6371.);double inc=mx(0,dot(en,Sun));if(inc<=0)continue;
    double f=rule_w[j]*(2*PI*delta)*(1.5*.434/PI)*inc*disk(mu0,mu);int code=visible(p,di,c);if(code==0)z[13]+=f;else if(code==2)z[16]+=f;
   }
  }
 }
 return 1;
}
API int light_rows(int first,int count,int lights,int bundle,int analytic){return light_rows_impl(first,count,lights,bundle,analytic,0);}
API int light_rows_selected(int first,int count,int lights,int bundle,int analytic,const uint8_t *mask){return light_rows_impl(first,count,lights,bundle,analytic,mask);}
API double material_gain(void){return gain;}
API int kernel_version(void){return 1;}

API int set_lights(double*s,double*e,int radial,int azimuth){
 V ss=readv(s),ee=readv(e);if(!isfinite(norm(ss))||fabs(norm(ss)-1)>1e-10||!isfinite(norm(ee))||norm(ee)<=R+hmax+6371)return 0;
 Sun=unit(ss);Earth=ee;for(int i=1;i<6;i++)counters[i]=0;return set_rule(radial,azimuth);
}
