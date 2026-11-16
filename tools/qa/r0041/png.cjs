'use strict';
// Minimal PNG decoder (8-bit RGB/RGBA, non-interlaced) for screenshot analysis in the Moon-reuse audit. No dependency.
const zlib=require('node:zlib');
function decodePng(buf){
  if(buf.readUInt32BE(0)!==0x89504e47)throw new Error('not png');
  let p=8,w=0,h=0,bd=0,ct=0,il=0;const idat=[];
  while(p<buf.length){const len=buf.readUInt32BE(p),type=buf.toString('ascii',p+4,p+8),data=buf.subarray(p+8,p+8+len);
    if(type==='IHDR'){w=data.readUInt32BE(0);h=data.readUInt32BE(4);bd=data[8];ct=data[9];il=data[12];}
    else if(type==='IDAT')idat.push(data);else if(type==='IEND')break;p+=12+len;}
  if(bd!==8||il!==0||![2,6].includes(ct))throw new Error(`unsupported png bd=${bd} ct=${ct} il=${il}`);
  const bpp=ct===6?4:3,stride=w*bpp,raw=zlib.inflateSync(Buffer.concat(idat)),out=new Uint8Array(w*h*4);let prev=new Uint8Array(stride),cur=new Uint8Array(stride);
  for(let y=0;y<h;y++){const f=raw[y*(stride+1)],line=raw.subarray(y*(stride+1)+1,(y+1)*(stride+1));
    for(let x=0;x<stride;x++){const a=x>=bpp?cur[x-bpp]:0,b=prev[x],c=x>=bpp?prev[x-bpp]:0;let v=line[x];
      if(f===1)v+=a;else if(f===2)v+=b;else if(f===3)v+=(a+b)>>1;else if(f===4){const pp=a+b-c,pa=Math.abs(pp-a),pb=Math.abs(pp-b),pc=Math.abs(pp-c);v+=pa<=pb&&pa<=pc?a:pb<=pc?b:c;}
      cur[x]=v&255;}
    for(let x=0;x<w;x++){out[4*(y*w+x)]=cur[bpp*x];out[4*(y*w+x)+1]=cur[bpp*x+1];out[4*(y*w+x)+2]=cur[bpp*x+2];out[4*(y*w+x)+3]=bpp===4?cur[bpp*x+3]:255;}
    [prev,cur]=[cur,prev];}
  return {width:w,height:h,data:out};
}
module.exports={decodePng};
