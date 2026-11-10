#!/usr/bin/env python3
"""Reproduce the actual-source coverage preview and raw bright-star orientation record."""
import json,subprocess
import numpy as np
from scipy.spatial import cKDTree
from PIL import Image,ImageDraw
from qualify_starmap import ROOT,load_source,write_json
from healpix_grid import centres,ang2pix,pix2ang,pixel_area

def main():
 a,h=load_source(ROOT);v=a[:,1];points=centres(256);tree=cKDTree(points)
 cat=json.loads(subprocess.run(['node',str(ROOT/'tools/export_cp7_emitters.mjs')],cwd=ROOT,capture_output=True,text=True,check=True).stdout);land=[]
 for s in cat['stars'][:24]:
  d=s['directions'][1];rr,dd=np.deg2rad([d['raDeg'],d['decDeg']]);u=np.array([np.cos(dd)*np.cos(rr),np.cos(dd)*np.sin(rr),np.sin(dd)])
  near=tree.query_ball_point(u,2*np.sin(np.deg2rad(.5)/2));p=max(near,key=lambda p:v[p]);lon,lat=pix2ang(256,np.array([p]));sep=np.rad2deg(np.arctan2(np.linalg.norm(np.cross(u,points[p])),u@points[p]))
  land.append({'id':s['id'],'hip':s['hip'],'vmag':s['vmag'],'nativePixel':int(p),'peakRaDeg':float(lon[0]),'peakDecDeg':float(lat[0]),'catalogueSeparationDeg':float(sep),'peakRelativeV0Flux':float(v[p]*pixel_area(256)/3.62708e-11),'catalogueRelativeV0Flux':10**(-.4*s['vmag'])})
 write_json(ROOT/'provenance/cp7/admitted/raw-bright-landmarks.json',{'purpose':'Source-derived independent gross orientation check; catalogue positions are not used to move the map. Photometric ratios are observations, not acceptance of exact HYG/Gaia equality.','limitDeg':.5,'landmarks':land})
 w,h=1440,720;lon=np.broadcast_to((np.arange(w)+.5)/w*360,(h,w));lat=np.broadcast_to((90-(np.arange(h)+.5)/h*180)[:,None],(h,w));q=v[ang2pix(256,lon,lat)]
 t=np.clip((np.log10(q)+10.7)/3,0,1);im=Image.fromarray(np.uint8(t*255)).convert('RGB');canvas=Image.new('RGB',(w,h+85),'#111c2c');canvas.paste(im,(0,60));dr=ImageDraw.Draw(canvas);dr.text((16,12),'AUTHENTICATED SOURCE · Gaia DR3 + Hipparcos integrated starlight · V band',fill='white');dr.text((16,32),'ICRS: RA increases right, 0–360°; north at top. Log inspection stretch, not physical display exposure.',fill='white');dr.text((16,h+66),'Source contains bright-star light; the uncorrected map must not be added to the CP6 catalogue.',fill='white');canvas.save(ROOT/'provenance/cp7/admitted/raw-V-coverage.png')
 print(json.dumps({'rawSourceLandmarks':len(land),'maximumCatalogueSeparationDeg':max(s['catalogueSeparationDeg'] for s in land)}))
if __name__=='__main__':main()
