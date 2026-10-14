"""Index original native video and render review sheets; never controls a browser.

Metrics nominate frames only. The reviewer must inspect original first presentation
and its preceding frames, including partial/blank captures, before pixel acceptance.
"""
import argparse,hashlib,json,subprocess
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw

def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('case',type=Path);p.add_argument('--target-seconds',type=float);args=p.parse_args()
 root=args.case;video=next((root/'video').glob('*.webm'));trace=json.loads((root/'trace.json').read_bytes())
 probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height:frame=best_effort_timestamp_time','-of','json',str(video)]))
 width,height=probe['streams'][0]['width'],probe['streams'][0]['height'];times=[float(f['best_effort_timestamp_time']) for f in probe['frames']]
 command=['ffmpeg','-v','error','-i',str(video),'-vsync','0','-f','rawvideo','-pix_fmt','rgb24','-']
 proc=subprocess.Popen(command,stdout=subprocess.PIPE);frames=[];clock=[];whole=[];nbytes=width*height*3
 while True:
  data=proc.stdout.read(nbytes)
  if not data:break
  if len(data)!=nbytes:raise RuntimeError('truncated native decoded frame')
  arr=np.frombuffer(data,np.uint8).reshape(height,width,3)
  frames.append(data);clock.append(arr[285:495,250:306].copy());whole.append(float(arr[:530,:325].std()))
 if proc.wait():raise RuntimeError('native video decode failed')
 assert len(frames)==len(times)
 # Template is an actual final nonblank native frame; no generated reference pixels.
 ref=max((i for i,v in enumerate(whole) if v>5),default=len(frames)-1)
 template=clock[ref].astype(float);distance=[float(np.mean(np.abs(a.astype(float)-template))) for a in clock]
 # Record every frame's score and retain a bounded threshold transition context.
 candidates=[i for i,d in enumerate(distance) if d<1.5 and whole[i]>5]
 first=candidates[0] if candidates else None
 selected=set([0,ref])
 for sec in [0.2,0.6,1,2,3,5,10,20,30,33,34,40,50,58,59,60,61,62,65]:
  if times and sec<=times[-1]: selected.add(min(range(len(times)),key=lambda i:abs(times[i]-sec)))
 if first is not None:selected.update(range(max(0,first-12),min(len(frames),first+13)))
 for i in list(selected):
  if whole[i]<5 and i+1<len(frames):selected.add(i+1)
 selected=sorted(selected)
 out=root/'native-review';out.mkdir(exist_ok=True)
 # Native video only; PNGs are lossless decoded originals at unmodified resolution.
 for i in selected:Image.frombytes('RGB',(width,height),frames[i]).save(out/f'frame-{i:05}.png')
 thumbs=[]
 for i in selected:
  im=Image.frombytes('RGB',(width,height),frames[i]);thumb=Image.new('RGB',(185,307),'white');thumb.paste(im.resize((185,285)),(0,20));ImageDraw.Draw(thumb).text((3,3),f'{i} / {times[i]:.3f}s',fill='black');thumbs.append(thumb)
 for start in range(0,len(thumbs),24):
  batch=thumbs[start:start+24];sheet=Image.new('RGB',(185*6,307*((len(batch)+5)//6)),(220,220,220))
  for j,im in enumerate(batch):sheet.paste(im,((j%6)*185,(j//6)*307))
  sheet.save(out/f'overview-{start//24}.jpg',quality=92)
 # Each decoded clock strip remains in the sheet, preserving early/partial glyphs.
 if first is not None:
  nearby=range(max(0,first-12),min(len(frames),first+13));sheet=Image.new('RGB',(160*5,244*((len(nearby)+4)//5)),(235,235,235))
  for j,i in enumerate(nearby):
   im=Image.frombytes('RGB',(width,height),frames[i]);tile=Image.new('RGB',(160,244),'white');tile.paste(im.crop((240,280,325,530)),(0,20));ImageDraw.Draw(tile).text((2,3),f'{i} / {times[i]:.3f}s',fill='black');sheet.paste(tile,((j%5)*160,(j//5)*244))
  sheet.save(out/'transition-clock-strips.png')
 receipt={'schema':'r0006-original-video-index/v1','videoSha256':sha(video.read_bytes()),'traceSha256':sha((root/'trace.json').read_bytes()),'caseInputSha256':sha((root/'case-input.json').read_bytes()),
  'size':[width,height],'frameCount':len(frames),'durationPts':times[-1] if times else None,'referenceFrame':ref,'candidateFirstTemplateMatch':first,'threshold':1.5,
  'metricLimitation':'Template closeness nominates review frames, does not certify first-current pixels or continuous readability. Video PTS and fixture performance have distinct origins.',
  'selectedOriginalFrames':selected,'frames':[{'ordinal':i,'ptsSeconds':times[i],'clockTemplateMae':distance[i],'cardStd':whole[i],'decodedRgbSha256':sha(frames[i])} for i in range(len(frames))]}
 (out/'index.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8')
 print(root.name,len(frames),'frames; candidate',first,'at',times[first] if first is not None else None,'seconds')
if __name__=='__main__':main()
