#!/usr/bin/env python3
"""Optional independent Sun/Moon fixture generation. Requires pyswisseph, not runtime.
Moshier analytic ephemeris, geometric mean-of-date coordinates, explicit matched TT/UT1.
These source directions are for the background model, not CP4 stellar accuracy claims.
"""
import json,math,swisseph as swe
from pathlib import Path
R=Path(__file__).resolve().parents[1]
acceptance={'sunDirectionDeg':.05,'moonDirectionDeg':.15,'lunarPhaseDeg':.2,'lunarDistanceKm':1500}
locations=[('Florida',28.54,-81.38,0),('Madinah',24.47,39.61,600),('Reykjavik',64.15,-21.94,20),('Sydney',-33.86,151.21,50),('northPole',90,0,0),('southPole',-90,180,0)]
flags=swe.FLG_MOSEPH|swe.FLG_EQUATORIAL|swe.FLG_TOPOCTR|swe.FLG_NONUT|swe.FLG_TRUEPOS
rows=[]
for year in [2020,2026,2035]:
 for month in range(1,13):
  for day in [1,8,15,22]:
   for hour in [0,6,12,18]:
    jd=swe.julday(year,month,day,hour);tt=jd+swe.deltat(jd)
    phase=swe.pheno(tt,swe.MOON,swe.FLG_MOSEPH|swe.FLG_TRUEPOS)
    for name,lat,lon,height in locations:
     swe.set_topo(lon,lat,height)
     observer={'utcMs':round((jd-2440587.5)*86400000),'ttMinusUtcSeconds':(tt-jd)*86400,'dut1Seconds':0,'latDeg':lat,'lonDeg':lon,'heightM':height}
     # Sidtime0 with zero nutation supplies a separately implemented mean sidereal angle.
     lst=(swe.sidtime0(jd,23.4393,0)*15+lon)%360
     def body(bodyid):
      x,rf=swe.calc(tt,bodyid,flags);ra,de,dist=x[:3];H=math.radians(lst-ra);dec=math.radians(de);p=math.radians(lat)
      up=math.sin(dec)*math.sin(p)+math.cos(dec)*math.cos(H)*math.cos(p)
      east=-math.cos(dec)*math.sin(H);north=math.sin(dec)*math.cos(p)-math.cos(dec)*math.cos(H)*math.sin(p)
      return {'raDeg':ra,'decDeg':de,'altDeg':math.degrees(math.asin(max(-1,min(1,up)))),'azDeg':math.degrees(math.atan2(east,north))%360,'distanceKm':dist*149597870.7,'returnedFlags':rf}
     rows.append({'observer':observer,'site':name,'sun':body(swe.SUN),'moon':body(swe.MOON),'moonPhaseDeg':phase[0]})
payload={'schema':'salah-real-sky/cp6-illumination-oracle/1','oracle':'Swiss Ephemeris '+swe.version,'ephemeris':'Moshier, no downloaded external ephemeris','flags':'MOSEPH|EQUATORIAL|TOPOCTR|NONUT|TRUEPOS','acceptanceSetBeforeComparison':acceptance,'scope':'2020,2026,2035; 12 months/year; four days/month; four UT1 times/day; six sites including poles. Refraction and eclipses excluded. Matched explicit TT/UT1, not a future clock prediction.','rows':rows}
(R/'tests/fixtures/cp6-illumination.json').write_text(json.dumps(payload,separators=(',',':'))+'\n')
print(json.dumps({'observerCases':len(rows),'bodies':len(rows)*2,'acceptance':acceptance},indent=2))
