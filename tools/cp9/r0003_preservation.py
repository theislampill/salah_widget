"""Offline pixel/receipt measurements supporting, never replacing, original video review."""
import argparse, base64, hashlib, io, json, math
from pathlib import Path
from PIL import Image, ImageChops, ImageStat

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args();rows=[]
    for folder in sorted(a.root.glob('*')):
        if not (folder/'trace.json').exists():continue
        t=json.loads((folder/'trace.json').read_text(encoding='utf-8'));stages={s['checkpoint']:s for s in t.get('snapshots',[]) if s.get('checkpoint')}
        if 'live-start' in stages and 'live-30s' in stages:
            first,last=stages['live-start'],stages['live-30s'];delta=(last['wallUtcMs']-first['wallUtcMs'])/1000
            assert 30<=delta<=60 and first['clock']['FOLLOW_WALL_CLOCK'] and first['clock']['TIMESCALE']==1 and not first['clock']['ADVANCING']
            im1=Image.open(folder/'live-start.png').convert('RGB');im2=Image.open(folder/'live-30s.png').convert('RGB')
            # A fixed top-right cloud window avoids text/countdown; original full card remains authoritative.
            box=(230,60,320,120);diff=ImageChops.difference(im1.crop(box),im2.crop(box));mean=ImageStat.Stat(diff).mean
            rows.append({'caseId':folder.name,'kind':'live-native-clock','elapsedSeconds':delta,'traceSha256':sha(folder/'trace.json'),
                         'motionStart':first.get('cloudMotion'),'motionEnd':last.get('cloudMotion'),'cloudPixelWindow':box,'meanAbsoluteRgbDelta':mean,
                         'firstPngSha256':sha(folder/'live-start.png'),'lastPngSha256':sha(folder/'live-30s.png'),
                         'limits':'Endpoint pixels/telemetry corroborate visible cloud displacement. Original complete video and independent pixel inspection decide continuous motion; no cloud hash used.'})
        if (folder/'warm-ashen-preservation.json').exists():
            q=json.loads((folder/'warm-ashen-preservation.json').read_text(encoding='utf-8'));assert q['before']==q['after'],'observer changed presentation'
            href=q['before']['href'];assert href.startswith('data:image/png;base64,')
            data=base64.b64decode(href.split(',',1)[1]);im=Image.open(io.BytesIO(data)).convert('RGBA');w,h=im.size
            interior=[im.getpixel((x,y))[3] for y in range(h) for x in range(w) if ((x+.5-w/2)/(w/2))**2+((y+.5-h/2)/(h/2))**2<.90**2]
            # Actual native published material; antialias boundary intentionally excluded.
            rows.append({'caseId':folder.name,'kind':'warm-calendar-Moon','traceSha256':sha(folder/'trace.json'),'consumed':q['consumed'],
                         'presentationCss':q['presentationCss'],'geometry':q['geometry'],'nativeMaterialSha256':hashlib.sha256(data).hexdigest(),
                         'materialSize':[w,h],'innerDiscAlphaMin':min(interior),'innerDiscAlphaMax':max(interior),'observerBeforeAfterEqual':True,
                         'limits':'Material alpha is corroborative; original admitted disc pixels must show no stars through the disc. Legitimate unavailable startup frames remain unavailable.'})
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps({'schema':'r0003-preservation-observations/v1','rows':rows},indent=2)+'\n')
    print(json.dumps([{'case':r['caseId'],'seconds':r.get('elapsedSeconds'),'cloudDelta':r.get('meanAbsoluteRgbDelta'),'alphaMin':r.get('innerDiscAlphaMin')} for r in rows]))
if __name__=='__main__':main()
