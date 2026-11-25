"""Make labeled first-frame crops without interpolating either the sky or the residual."""
import argparse
import json
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw, ImageFont


def main(folder):
    receipt=json.loads((folder/'sequence-receipt.json').read_text())
    base=Image.open(folder/'r0035-unmodulated-sky.png').convert('RGB')
    active=Image.open(folder/'r0035-x2-first.png').convert('RGB')
    width,height=base.size
    sheet=Image.new('RGB',(810,640),'#101722')
    draw=ImageDraw.Draw(sheet)
    try:
        title=ImageFont.truetype('DejaVuSans.ttf',20)
        small=ImageFont.truetype('DejaVuSans.ttf',13)
    except OSError:
        title=small=ImageFont.load_default()
    draw.text((18,12),'R0035   Reconstructed star field',font=title,fill='white')
    draw.text((19,44),'Synthetic time, 325 × 530 pixels, before glass and prayer UI',font=small,fill='#ced6dd')
    sheet.paste(active,(18,77))
    draw.text((18,615),'Complete frame, ×2 experiment',font=small,fill='white')
    residual=ImageChops.difference(base,active)
    for row,star in enumerate(receipt['sequences'][1]['trackedCenters']):
        x=int(star['x']);y=int(star['y']);left=max(0,min(width-19,x-9));top=max(0,min(height-19,y-9))
        box=(left,top,left+19,top+19)
        draw.rectangle((18+left,77+top,18+left+18,77+top+18),outline='#edbc68')
        y0=96+row*220
        draw.text((371,y0),f"{star['id']}    V {star['vmag']:.2f}    ({x}, {y})",font=small,fill='white')
        for col,(name,img) in enumerate([('Unmodulated',base),('×2',active),('RGB difference ×64',residual.point(lambda c:min(255,c*64)))]):
            tile=img.crop(box).resize((133,133),Image.Resampling.NEAREST)
            xx=369+col*144
            sheet.paste(tile,(xx,y0+30))
            draw.text((xx,y0+172),name,font=small,fill='#ced6dd')
    draw.text((369,551),'19 × 19 crops enlarged 7× with nearest-neighbor sampling.',font=small,fill='#ced6dd')
    draw.text((369,576),'Differences are amplified only in the rightmost column.',font=small,fill='#ced6dd')
    draw.text((369,602),'All three crops use the same source position and instant.',font=small,fill='#ced6dd')
    sheet.save(folder/'r0035-reconstruction-crops.png')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder',type=Path)
    main(parser.parse_args().folder)
