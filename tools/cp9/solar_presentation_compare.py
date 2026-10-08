"""Compare the size-only control with corrected actual-widget solar captures.

This is a display regression, not a solar spectrum calibration. The independent
pixel control measures radial chromaticity: a white centre and orange collar
have a large colour discontinuity even when their CSS bounding boxes agree.
"""
import argparse, json
from pathlib import Path
from PIL import Image, ImageDraw, ImageStat

def load(folder):
    rows=json.loads((folder/'measurements.json').read_text())
    return {(r['direction'],r['targetAltitude']):r for r in rows if r['version']==folder.name}

def radial(folder,row):
    im=Image.open(folder/(row['shot'][:-4]+'-body-only.png')).convert('RGB')
    scale=im.width/330
    r=row['parts']['.sunbody .disc']['rect']
    cx,cy=r['x']+r['w']/2,r['y']+r['h']/2
    samples=[]
    for fraction in [.1,.25,.4,.55,.7,.8]:
        x,y=round((cx+r['w']/2*fraction)*scale),round(cy*scale)
        rgb=ImageStat.Stat(im.crop((x-1,y-1,x+2,y+2))).median
        total=sum(rgb)
        samples.append({'radiusFraction':fraction,'rgb':rgb,'chromaticity':[(v/total if total else 0) for v in rgb]})
    span=max(max(s['chromaticity'][k] for s in samples)-min(s['chromaticity'][k] for s in samples) for k in range(3))
    return {'samples':samples,'radialChromaticitySpan':span}

def run(before,after,out):
    out.mkdir(parents=True,exist_ok=True);old,new=load(before),load(after);checks=[]
    for key,row in new.items():
        control=old[key];e=key[1];disc=row['parts']['.sunbody .disc']['rect'];prior=control['parts']['.sunbody .disc']['rect']
        check={'direction':key[0],'targetElevation':e,'diameter':disc['w'],
               'sizeUnchanged':abs(disc['w']-prior['w'])<.01,
               'centreUnchanged':abs(disc['x']+disc['w']/2-prior['x']-prior['w']/2)<.01 and abs(disc['y']+disc['h']/2-prior['y']-prior['h']/2)<.01}
        if e in [0,1,3]:
            check.update(control=radial(before,control),corrected=radial(after,row))
            # Predeclared display continuity tolerance. No fixed colour, white
            # brightness, or minimum luminance is imposed on an attenuated Sun.
            check['noWhiteCentreOrangeCollar']=check['corrected']['radialChromaticitySpan']<=.10
        # The owner's preferred control retains blue/cream separation. Sample
        # actual browser pixels outside the body, UI and moving cloud support
        # in the CLEAR matched run. A body repair must not tint the whole card.
        # One code allows display rounding, not a global warmth adjustment.
        from PIL import ImageChops
        a=Image.open(before/control['shot']).convert('RGB')
        b=Image.open(after/row['shot']).convert('RGB')
        diff=ImageChops.difference(a,b)
        check['outsideBody']={name:{'before':ImageStat.Stat(a.crop(box)).mean,
            'after':ImageStat.Stat(b.crop(box)).mean,
            'maximumDifference':max(x[1] for x in diff.crop(box).getextrema())}
            for name,box in [('upperRight',(220,65,300,120)),
                             ('openRight',(220,200,300,225)),
                             # Outside the prayer panels. A fixed y425 gap
                             # crossed the newly selected Maghrib plate in
                             # sunset scenes and measured the H6 repair.
                             ('lowerMargin',(315,405,319,440))]}
        check['noWholeCardTint']=all(p['maximumDifference']<=1 for p in check['outsideBody'].values())
        checks.append(check)
    for direction in ['rise','set']:
        elevations=[-2,0,1,3,5.5,10,40]
        sheet=Image.new('RGB',(330*7,566*2),'#192439');draw=ImageDraw.Draw(sheet)
        for ri,(label,folder) in enumerate([('Size-only lamp control',before),('Complete air + body + cloud join',after)]):
            for ci,e in enumerate(elevations):
                im=Image.open(folder/f'{direction}-{e}.png').convert('RGB').resize((330,534))
                sheet.paste(im,(ci*330,ri*566+32));draw.text((ci*330+5,ri*566+8),f'{label}: {direction} {e} deg',fill='white')
        sheet.save(out/f'{direction}-comparison.png')
    negative=any(c.get('control',{}).get('radialChromaticitySpan',0)>.10 for c in checks)
    passed=all(c['sizeUnchanged'] and c['centreUnchanged'] and c['noWholeCardTint'] and c.get('noWhiteCentreOrangeCollar',True) for c in checks)
    report={'status':'PASS_SCOPED' if passed and negative else 'FAIL','before':str(before),'after':str(after),
            'scope':'Matched clear-weather body-only pixels. Size gate and radial-colour gate are separate. Does not certify motion or cloud opacity; use the corresponding browser campaigns.',
            'controlFailsColourGate':negative,'checks':checks}
    (out/'results.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':report['status'],'controlFailsColourGate':negative}));return report['status']!='FAIL'

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--before',type=Path,required=True);p.add_argument('--after',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();raise SystemExit(0 if run(a.before,a.after,a.out) else 1)
