/* SMH1 physical receiver transport. No ephemeris, phase image,
 * independent clock, terrain, worker, or V5 display mapping is present here.
 * assetDigest is the unchanged reviewed Moon digest implementation.
 */
function decodeCompactReceivers(bytes,encoding){
 if(!(bytes instanceof Uint8Array)||bytes.length!==encoding.bytes||bytes.length>600000||assetDigest(bytes)!==encoding.sha256)throw Error('Compact receiver identity');
 if(encoding.schema!=='moon-initial-compact/1'||encoding.parentReceiverSha256!=='0c5e4be7808367211ab3a8fec8a8dcba76f6f9a69ebf5591dc76ed3e188b2444'||encoding.method!=='paeth-huffman')throw Error('Compact receiver ancestry');
 const v=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength),N=v.getUint16(4,true),count=v.getUint32(6,true),maskBytes=Math.ceil(N*N/8);
 if(v.getUint32(0,true)!==0x31484d53||N!==540||count!==196435||encoding.size!==N||encoding.records!==count)throw Error('Compact receiver shape');
 const mask=bytes.subarray(10,10+maskBytes),indices=new Uint32Array(count);let n=0;
 for(let i=0;i<N*N;i++)if(mask[i>>3]&(1<<(i&7))){if(n>=count)throw Error('Compact coverage count');indices[n++]=i;}
 if(n!==count)throw Error('Compact coverage count');
 const widths=[8,5,5,5,5,5,8,8],channels=[];let at=10+maskBytes;
 const paeth=(a,b,c)=>{const p=a+b-c,da=Math.abs(p-a),db=Math.abs(p-b),dc=Math.abs(p-c);return da<=db&&da<=dc?a:db<=dc?b:c;};
 for(let field=0;field<widths.length;field++){
  if(at+5>bytes.length)throw Error('Compact channel header');
  const width=bytes[at++],length=v.getUint32(at,true);at+=4;
  if(width!==widths[field]||length<1||length>count*2||at+(1<<width)+length>bytes.length)throw Error('Compact channel bounds');
  const lengths=bytes.subarray(at,at+(1<<width));at+=1<<width;const body=bytes.subarray(at,at+length);at+=length;
  const sorted=[];for(let s=0;s<lengths.length;s++){if(lengths[s]>20)throw Error('Compact Huffman length');if(lengths[s])sorted.push([lengths[s],s]);}
  sorted.sort((a,b)=>a[0]-b[0]||a[1]-b[1]);if(!sorted.length)throw Error('Compact empty codebook');
  const firstCode=new Int32Array(21).fill(-1),firstIndex=new Int32Array(21),frequency=new Int32Array(21),prefix=new Uint16Array(256);let code=0,previous=0;
  for(let j=0;j<sorted.length;j++){
   const length=sorted[j][0];code*=2**(length-previous);if(code>=2**length)throw Error('Compact oversubscribed Huffman');
   if(!frequency[length]){firstCode[length]=code;firstIndex[length]=j;}frequency[length]++;
   if(length<=8){const start=code<<(8-length);prefix.fill((length<<8)|sorted[j][1],start,start+(1<<(8-length)));}
   code++;previous=length;
  }
  let bit=0;const dense=new Uint16Array(N*N),out=new Uint16Array(count),mod=(1<<width)-1;
  for(let ri=0;ri<count;ri++){
   let word=0,symbol=-1;
   // Short canonical words use an eight-bit prefix; long words and the final
   // partial byte retain the exact original bit reader and rejection order.
   if(body.length*8-bit>=8){const byte=bit>>3,hit=prefix[((body[byte]<<8|body[byte+1])>>>(8-(bit&7)))&255];if(hit){symbol=hit&255;bit+=hit>>>8;}}
   if(symbol<0)for(let length=1;length<=20;length++){
     if(bit>=body.length*8)throw Error('Compact truncated Huffman');word=word*2+((body[bit>>3]>>(7-(bit&7)))&1);bit++;
     const delta=word-firstCode[length];if(firstCode[length]>=0&&delta>=0&&delta<frequency[length]){symbol=sorted[firstIndex[length]+delta][1];break;}
   }
   if(symbol<0)throw Error('Compact invalid Huffman word');
   const i=indices[ri],x=i%N,y=Math.floor(i/N),pred=paeth(x?dense[i-1]:0,y?dense[i-N]:0,x&&y?dense[i-N-1]:0);
   out[ri]=(symbol+pred)&mod;dense[i]=out[ri];
  }
  if(body.length*8-bit>=8)throw Error('Compact extra Huffman bytes');
  for(;bit<body.length*8;bit++)if((body[bit>>3]>>(7-(bit&7)))&1)throw Error('Compact nonzero Huffman padding');
  channels.push(out);
 }
 if(at!==bytes.length)throw Error('Compact trailing data');
 const decoded=new Uint8Array(6+maskBytes+20*count),d=new DataView(decoded.buffer);d.setUint32(0,0x31494d53,true);d.setUint16(4,N,true);decoded.set(mask,6);at=6+maskBytes;
 const fields=encoding.fields;
 if(!Array.isArray(fields)||fields.length!==8||fields.map(f=>f.bits).join(',')!=='8,5,5,5,5,5,8,8')throw Error('Compact scalar schema');
 for(const k of [0,3,4,5])if(!Array.isArray(fields[k].range)||fields[k].range.length!==2||!fields[k].range.every(Number.isFinite)||fields[k].range[0]>=fields[k].range[1])throw Error('Compact scalar range');
 for(let ri=0;ri<count;ri++,at+=20){
  const depth=fields[0].range[0]+channels[0][ri]/255*(fields[0].range[1]-fields[0].range[0]);d.setFloat32(at,depth,true);
  let x=channels[1][ri]/31*2-1,y=channels[2][ri]/31*2-1,z=1-Math.abs(x)-Math.abs(y);
  if(z<0){const old=x;x=(1-Math.abs(y))*(old>=0?1:-1);y=(1-Math.abs(old))*(y>=0?1:-1);}
  const norm=Math.hypot(x,y,z);
  d.setInt16(at+4,Math.trunc(x/norm*32767+(x>=0?.5:-.5)),true);
  d.setInt16(at+6,Math.trunc(y/norm*32767+(y>=0?.5:-.5)),true);
  d.setInt16(at+8,Math.trunc(z/norm*32767+(z>=0?.5:-.5)),true);
  const g=channels[3][ri],red=(channels[4][ri]+g)&31,blue=(channels[5][ri]+g)&31;
  for(let k=0;k<3;k++){const range=fields[3+k].range,col=k===0?red:k===1?g:blue;d.setUint16(at+10+2*k,Math.floor(range[0]+col/31*(range[1]-range[0])+.5),true);}
  const h0=channels[6][ri],h1=(channels[7][ri]-h0+255)&255;d.setUint16(at+16,Math.floor(h0/255*65535+.5),true);d.setUint16(at+18,Math.floor(h1/255*65535+.5),true);
 }
 if(assetDigest(decoded)!==encoding.decodedSha256)throw Error('Compact decoded identity');return decoded;
}
