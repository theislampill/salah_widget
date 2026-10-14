"""Dependency-free raw RGBA/PNG custody and independent visible-color oracles."""
import hashlib
import json
from pathlib import Path
import struct
import zlib

WIDTH,HEIGHT=144,232
def sha(data): return hashlib.sha256(data).hexdigest()
def write_json(path,value): path.write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
def png(width,height,rgba):
    if len(rgba)!=width*height*4:raise ValueError('RGBA dimensions mismatch')
    def chunk(kind,data):return struct.pack('!I',len(data))+kind+data+struct.pack('!I',zlib.crc32(kind+data)&0xffffffff)
    raw=b''.join(b'\0'+bytes(rgba[y*width*4:(y+1)*width*4]) for y in range(height))
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!2I5B',width,height,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b'')
def decode_png(data):
    if not data.startswith(b'\x89PNG\r\n\x1a\n'):raise ValueError('PNG signature')
    pos=8;compressed=bytearray();width=height=bpp=None
    while pos<len(data):
        length=struct.unpack_from('!I',data,pos)[0];kind=data[pos+4:pos+8];body=data[pos+8:pos+8+length]
        crc=struct.unpack_from('!I',data,pos+8+length)[0]
        if zlib.crc32(kind+body)&0xffffffff!=crc:raise ValueError('PNG CRC failure')
        if kind==b'IHDR':
            width,height,depth,color,compression,filter_method,interlace=struct.unpack('!2I5B',body)
            if depth!=8 or color not in (2,6) or compression or filter_method or interlace:raise ValueError('unsupported PNG layout')
            bpp=4 if color==6 else 3
        elif kind==b'IDAT':compressed.extend(body)
        elif kind==b'IEND':break
        pos+=length+12
    raw=zlib.decompress(compressed);stride=width*bpp
    if len(raw)!=(stride+1)*height:raise ValueError('PNG scanline length')
    rows=[];prev=bytearray(stride);offset=0
    def paeth(a,b,c):
        p=a+b-c;pa,pb,pc=abs(p-a),abs(p-b),abs(p-c)
        return a if pa<=pb and pa<=pc else b if pb<=pc else c
    for y in range(height):
        filt=raw[offset];row=bytearray(raw[offset+1:offset+1+stride]);offset+=stride+1
        for x in range(stride):
            a=row[x-bpp] if x>=bpp else 0;b=prev[x];c=prev[x-bpp] if x>=bpp else 0
            predictor=(0,a,b,(a+b)//2,paeth(a,b,c))[filt] if filt<5 else None
            if predictor is None:raise ValueError('unsupported PNG filter')
            row[x]=(row[x]+predictor)&255
        rows.append(row);prev=row
    rgba=bytearray()
    for row in rows:
        if bpp==4:rgba.extend(row)
        else:
            for x in range(0,stride,3):rgba.extend(row[x:x+3]);rgba.append(255)
    return width,height,bytes(rgba)
def measure(a,b):
    if len(a)!=WIDTH*HEIGHT*4 or len(a)!=len(b):raise ValueError('actual 144x232 RGBA required')
    total=maximum=changed=over5=alpha_max=visible=0
    for i in range(0,len(a),4):
        diffs=[abs(a[i+k]*a[i+3]-b[i+k]*b[i+3]) for k in range(3)]
        total+=sum(diffs);maximum=max(maximum,*diffs);changed+=any(diffs);over5+=any(d>5*255 for d in diffs)
        alpha_max=max(alpha_max,abs(a[i+3]-b[i+3]));visible+=(a[i+3]>0 or b[i+3]>0)
    return {'changedVisiblePixels':changed,'changedOver5':over5,'meanAbsolutePremultipliedRGB':total/(255*WIDTH*HEIGHT*3),
        'maxPremultipliedRGB':maximum/255,'maxAlphaDelta':alpha_max,'visibleUnionPixels':visible,
        'definition':'P_RGB=RGB*alpha/255; >5 is a historical discriminator, never a calibrated perceptibility threshold'}
def composite(rgba,background):
    if len(background)!=3:raise ValueError('three fixed background channels')
    out=bytearray()
    for i in range(0,len(rgba),4):
        alpha=rgba[i+3]
        out.extend(round((rgba[i+k]*alpha+background[k]*(255-alpha))/255) for k in range(3));out.append(255)
    return bytes(out)
def difference(a,b,gain=4):
    out=bytearray()
    for i in range(0,len(a),4):
        out.extend(min(255,round(abs(a[i+k]*a[i+3]-b[i+k]*b[i+3])*gain/255)) for k in range(3));out.append(255)
    return bytes(out)

def historical(base):
    folder=base/'historical/captures';pairs={'wind-failing':('wind-baseline-before.png','wind-baseline-after.png'),
        'wind-phase-diagnostic':('wind-phase-before.png','wind-phase-after.png'),
        'first-image-phase-parity':('wind-baseline-before.png','wind-phase-before.png'),
        'no-op':('wind-baseline-before.png','noop-cloud.png'),'day-failing':('boundary-a.png','boundary-b.png'),
        'ordinary-76ms':('ordinary-a.png','ordinary-b.png')}
    results={}
    for name,(before,after) in pairs.items():
        aw,ah,a=decode_png((folder/before).read_bytes());bw,bh,b=decode_png((folder/after).read_bytes())
        if (aw,ah,bw,bh)!=(WIDTH,HEIGHT,WIDTH,HEIGHT):raise ValueError('retained crop dimensions')
        results[name]={'before':before,'after':after,'beforeSha256':sha((folder/before).read_bytes()),'afterSha256':sha((folder/after).read_bytes()),**measure(a,b)}
    assert results['wind-failing']['changedOver5']==5520
    assert results['day-failing']['changedOver5']==6571
    for name in ['wind-phase-diagnostic','first-image-phase-parity','no-op']:assert results[name]['changedVisiblePixels']==0
    assert results['ordinary-76ms']['changedOver5']==0
    receipt={'schema':'r0025-retained-historical-pixels/1','sourceIndexSha256':'446453b522f56f5f1bc0afd1a3abd09b73756754fa58a6b3b0ff09ce953a2eec',
        'historicalCommit':'fd2972ba64225fe9d6848e92497e6d0ed20ea624','kind':'RECOMPUTED_RETAINED_NATIVE_IMAGES_NOT_FRESH_BROWSER_EXECUTION',
        'engine':'historical Windows Chromium152; viewport394x614 DPR2.2800001188 recorded in copied receipts',
        'comparisons':results,'limits':'True original failures/controls preserved byte-for-byte. The phase diagnostic was incomplete and is not a production donor. No current raster/native credit.'}
    write_json(base/'historical/recomputed.json',receipt);return receipt
if __name__=='__main__':
    value=historical(Path(__file__).resolve().parent)
    print(json.dumps({'historicalChecks':6,'windChangedOver5':value['comparisons']['wind-failing']['changedOver5'],
        'dayChangedOver5':value['comparisons']['day-failing']['changedOver5'],'currentNativeCredit':False}))
