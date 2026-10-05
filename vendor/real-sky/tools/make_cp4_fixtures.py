#!/usr/bin/env python3
"""Independent Swiss/Moshier oracle, installed only during verification.
Writes own HYG-derived temporary sefstars.txt, never distributes Swiss data/library.
Main profile: geocentric+topocentric apparent equatorial/horizontal, NO solar deflection,
vacuum, supplied UT1/TT. Geometric J2000 profile disables parallax via heliocentric mode.
"""
import json,tempfile,hashlib,math,swisseph as swe
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def as_sef(s):
 ra=s['raDeg']/15;rh=int(ra);rm=int((ra-rh)*60);rs=((ra-rh)*60-rm)*60
 de=abs(s['decDeg']);dd=int(de);dm=int((de-dd)*60);ds=((de-dd)*60-dm)*60
 dsign='-' if s['decDeg']<0 else '+';name='H'+str(s['hygId'])
 return ','.join(map(str,[name,name,'2000',rh,rm,f'{rs:.12f}',f'{dsign}{dd}',dm,f'{ds:.12f}',s['pmRaCosDecMasYr'] or 0,s['pmDecMasYr'] or 0,s['radialVelocityKmS'] or 0,1000/s['distancePc'] if s['distancePc'] else 0,s['vmag']]))
def main():
 cat=json.loads((ROOT/'data/catalogue-v6_5.json').read_text())['stars']
 # Select all bright first40 plus fastest30, all main example anchors, and exceptional faint endpoint.
 hips={11767,32349,30438,71683,71681,27989,25336,24436,27366,25930,26311,26727,60718,61084,62434,59747,91262,69673,33165}
 selected={s['id']:s for s in cat[:40]+sorted(cat,key=lambda s:math.hypot(s['pmRaCosDecMasYr'] or 0,s['pmDecMasYr'] or 0),reverse=True)[:30]+[s for s in cat if s['hip'] in hips]}
 stars=list(selected.values());idx={s['id']:i for i,s in enumerate(stars)}
 dates=[(1900,1),(1901,7),(1925,3),(1950,10),(1972,1),(2000,1),(2016,12),(2017,1)]+[(2026,m) for m in range(1,13)]+[(2050,1),(2050,7),(2099,4),(2100,12)]
 locations=[('equator',0,0,0),('Florida',28.54,-81.38,30),('Madinah',24.47,39.61,600),('Reykjavik',64.15,-21.94,20),('Sydney',-33.86,151.21,50),('northPole',90,0,0),('southPole',-90,0,0),('dateLine',0,180,0)]
 flags=swe.FLG_MOSEPH|swe.FLG_EQUATORIAL|swe.FLG_NOGDEFL|swe.FLG_TOPOCTR
 vectorflags=swe.FLG_MOSEPH|swe.FLG_EQUATORIAL|swe.FLG_J2000|swe.FLG_HELCTR|swe.FLG_TRUEPOS|swe.FLG_NONUT
 rows=[];epochs=[];earth=[];motion=[];census=[]
 with tempfile.TemporaryDirectory() as d:
  source='\n'.join(as_sef(s) for s in cat)+'\n';Path(d,'sefstars.txt').write_text(source);swe.set_ephe_path(d)
  for di,(year,month) in enumerate(dates):
   jd=swe.julday(year,month,15,2.125);tt=jd+swe.deltat(jd);ms=round((jd-2440587.5)*86400000)
   epochs.append({'utcMs':ms,'jdUt1':jd,'jdTt':tt,'ttMinusUtcSeconds':(tt-jd)*86400,'dut1Seconds':0})
   ep,rf=swe.calc(tt,swe.EARTH,vectorflags|swe.FLG_XYZ|swe.FLG_SPEED);earth.append({'jdTt':tt,'positionAu':ep[:3],'velocityAuDay':ep[3:],'returnedFlags':rf})
   for si,s in enumerate(stars):
    x,_,rf=swe.fixstar2('H'+str(s['hygId']),tt,vectorflags);motion.append([di,si,x[0],x[1]])
   for li,(name,lat,lon,height) in enumerate(locations):
    swe.set_topo(lon,lat,height)
    for si,s in enumerate(stars):
     x,_,rf=swe.fixstar2('H'+str(s['hygId']),tt,flags)
     az,alt,_=swe.azalt(jd,swe.EQU2HOR,(lon,lat,height),0,10,x[:3]);rows.append([di,li,si,x[0],x[1],(az+180)%360,alt])
  # All8921 records receive independent proper-motion/aberration/parallax/axis checks at three epochs.
  for year in [1901,2026,2099]:
   jd=swe.julday(year,4,15,6.5);tt=jd+swe.deltat(jd);swe.set_topo(-81.38,28.54,30)
   epoch={'utcMs':round((jd-2440587.5)*86400000),'ttMinusUtcSeconds':(tt-jd)*86400,'dut1Seconds':0,'latDeg':28.54,'lonDeg':-81.38,'heightM':30}
   results=[]
   for s in cat:
    x,_,rf=swe.fixstar2('H'+str(s['hygId']),tt,flags);results.append([s['id'],x[0],x[1]])
   census.append({'observer':epoch,'rows':results})
 payload={'schema':'salah-real-sky/astrometric-oracle/1','oracle':'Swiss Ephemeris '+swe.version,'ephemeris':'Moshier analytic Earth, no downloaded ephemeris','catalogue':'Own authenticated HYG4.0 selections converted into a TEMPORARY sefstars file','temporaryInputSha256':hashlib.sha256(source.encode()).hexdigest(),'flags':flags,'flagsMeaning':'MOSEPH|EQUATORIAL|NOGDEFL|TOPOCTR','motionFlags':vectorflags,'coordinateCaveat':'HYG equinox/epoch2000; Swiss 2000 input transform vs runtime meanJ2000 may include small frame-bias differences; measured in residual','timeCaveat':'fixture UTC numerical field is constructed UT1 with explicitDUT1=0 and Swiss TT offset, not measured historic UTC or a future DUT1 forecast','stars':stars,'epochs':epochs,'locations':[{'name':n,'latDeg':a,'lonDeg':b,'heightM':h} for n,a,b,h in locations],'rows':rows,'motionRows':motion,'earth':earth,'census':census,'sourceURLs':['https://www.astro.com/swisseph/swephprg.htm','https://github.com/aloistr/swisseph/blob/master/ephe/sefstars.txt']}
 out=ROOT/'tests/fixtures/cp4-astrometry.json';out.write_text(json.dumps(payload,separators=(',',':'))+'\n');print(json.dumps({'selectedStars':len(stars),'epochs':len(epochs),'locations':len(locations),'horizontalCases':len(rows),'motionCases':len(motion),'wholeCatalogueCases':sum(len(x['rows']) for x in census),'fixtureBytes':out.stat().st_size},indent=2))
if __name__=='__main__':main()
