"""Decode retained native video without cropping, scaling or repairing its frames."""
import argparse, hashlib, json, subprocess
from pathlib import Path
from PIL import Image, ImageDraw

def main():
    p=argparse.ArgumentParser();p.add_argument('folders',nargs='+',type=Path);p.add_argument('--paginate-only',action='store_true');a=p.parse_args()
    for folder in a.folders:
        videos=list((folder/'video').glob('*.webm'));assert len(videos)==1,videos
        video=videos[0];out=folder/'frames';out.mkdir(exist_ok=True)
        if a.paginate_only:
            paths=sorted(out.glob('frame-*.png'));assert paths
            pages=[]
            for start in range(0,len(paths),48):
                sheet=Image.new('RGB',(800,990),'#555');draw=ImageDraw.Draw(sheet)
                for i,path in enumerate(paths[start:start+48]):
                    im=Image.open(path);im.thumbnail((98,148));x=(i%8)*100;y=(i//8)*165;sheet.paste(im,(x,y));draw.text((x,y+148),path.stem.split('-')[-1],fill='white')
                target=out/('contact-%03d.jpg'%(start//48+1));sheet.save(target,quality=92)
                pages.append({'file':target.name,'firstFrame':start+1,'lastFrame':min(start+48,len(paths)),'sha256':hashlib.sha256(target.read_bytes()).hexdigest()})
            (out/'contact-pages.json').write_text(json.dumps({'navigationOnly':True,'originalFrameCount':len(paths),'pages':pages},indent=2)+'\n')
            print(json.dumps({'case':folder.name,'contactPages':len(pages)}),flush=True);continue
        assert not list(out.glob('frame-*.png')),'original decode already exists; do not overwrite'
        probe=subprocess.check_output(['ffprobe','-v','quiet','-show_format','-show_streams','-of','json',str(video)])
        (out/'probe.json').write_bytes(probe)
        with (out/'decode-full.log').open('w') as log:
            subprocess.run(['ffmpeg','-hide_banner','-i',str(video),'-vf','showinfo','-fps_mode','passthrough',str(out/'frame-%04d.png')],stderr=log,stdout=log,check=True)
        paths=sorted(out.glob('frame-*.png'));rows=[]
        width=8*100;height=((len(paths)+7)//8)*165
        # Contact index is navigation only. Every referenced original PNG is retained.
        sheet=Image.new('RGB',(width,height),'#555');draw=ImageDraw.Draw(sheet)
        for i,path in enumerate(paths):
            im=Image.open(path);rows.append({'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'size':list(im.size)})
            im.thumbnail((98,148));x=(i%8)*100;y=(i//8)*165;sheet.paste(im,(x,y));draw.text((x,y+148),str(i+1),fill='white')
        sheet.save(out/'index.jpg',quality=90)
        (out/'frame-manifest.json').write_text(json.dumps({'videoSha256':hashlib.sha256(video.read_bytes()).hexdigest(),'frameCount':len(rows),'frames':rows},indent=2)+'\n')
        print(json.dumps({'case':folder.name,'frames':len(rows),'index':str(out/'index.jpg')}),flush=True)
if __name__=='__main__':main()
