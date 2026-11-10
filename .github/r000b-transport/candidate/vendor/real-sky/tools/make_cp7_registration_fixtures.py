#!/usr/bin/env python3
"""Independent fixed-direction oracle; Swiss Ephemeris is installed verification software.
Artificial coordinate directions are TEST FIXTURES, not stars admitted to any sky catalogue.
Temporary zero-motion/zero-parallax fixed-star input is generated locally and not retained.
"""
import hashlib,json,math,tempfile
from pathlib import Path
import swisseph as swe
R=Path(__file__).resolve().parents[1]
def sef(i,ra,dec):
    hours=ra/15;h=int(hours);m=int((hours-h)*60);s=((hours-h)*60-m)*60;d=abs(dec);di=int(d);dm=int((d-di)*60);ds=((d-di)*60-dm)*60
    return ','.join(map(str,[f'Q{i:03d}',f'Q{i:03d}','2000',h,m,f'{s:.12f}',('-' if dec<0 else '+')+str(di),dm,f'{ds:.12f}',0,0,0,0,0]))
def separation(a,b):
    ra,de=a;rb,db=b;return math.degrees(math.acos(max(-1,min(1,math.sin(math.radians(de))*math.sin(math.radians(db))+math.cos(math.radians(de))*math.cos(math.radians(db))*math.cos(math.radians(ra-rb))))))
def main():
    directions=[{'id':f'axis-grid-{ra}-{de}','raDeg':ra,'decDeg':de,'kind':'synthetic-coordinate-test-only'} for ra in range(0,360,30) for de in [-80,-50,-20,0,20,50,80]]
    directions +=[{'id':f'pole-{de}','raDeg':0,'decDeg':de,'kind':'synthetic-coordinate-test-only'} for de in [-90,90]]
    asset=json.loads((R/'data/diffuse/hyg-residual-128x64.json').read_text());w,h=128,64;peaks=[]
    for index in sorted(range(w*h),key=lambda i:asset['values'][i],reverse=True):
        pos=((index%w+.5)*360/w,-90+(index//w+.5)*180/h)
        if all(separation(pos,p)>20 for p in peaks):
            peaks.append(pos);directions.append({'id':f'diagnostic-peak-cell-{index}','raDeg':pos[0],'decDeg':pos[1],'kind':'finite-catalogue-map-cell-not-survey-landmark','sourceValue':asset['values'][index]})
            if len(peaks)==8:break
    locations=[{'name':n,'latDeg':lat,'lonDeg':lon,'heightM':height} for n,lat,lon,height in [('equator',0,0,0),('Florida',28.54,-81.38,30),('Madinah',24.47,39.61,600),('Reykjavik',64.15,-21.94,20),('Sydney',-33.87,151.21,50),('northPole',90,0,0),('southPole',-90,0,0),('dateLine',0,180,0)]]
    epochs=[];rows=[];flags=swe.FLG_MOSEPH|swe.FLG_EQUATORIAL|swe.FLG_NOGDEFL|swe.FLG_TOPOCTR;returned=set()
    text='\n'.join(sef(i,s['raDeg'],s['decDeg']) for i,s in enumerate(directions))+'\n'
    with tempfile.TemporaryDirectory() as d:
        Path(d,'sefstars.txt').write_text(text);swe.set_ephe_path(d)
        for di,(year,month,day) in enumerate([(1900,1,15),(1950,7,15),(2000,1,15),(2026,1,15),(2026,4,15),(2026,7,15),(2026,10,4),(2099,1,15),(2100,12,15)]):
            jd=swe.julday(year,month,day,3);tt=jd+swe.deltat(jd);epochs.append({'utcMs':round((jd-2440587.5)*86400000),'dut1Seconds':0,'ttMinusUtcSeconds':(tt-jd)*86400})
            for li,loc in enumerate(locations):
                swe.set_topo(loc['lonDeg'],loc['latDeg'],loc['heightM'])
                for si,s in enumerate(directions):
                    x,_,rf=swe.fixstar2(f'Q{si:03d}',tt,flags);returned.add(rf);az,alt,_=swe.azalt(jd,swe.EQU2HOR,(loc['lonDeg'],loc['latDeg'],loc['heightM']),0,10,x[:3]);rows.append([di,li,si,(az+180)%360,alt])
    output={'schema':'salah-real-sky/cp7-direction-oracle/1','oracle':'Swiss Ephemeris '+swe.version,'ephemeris':'Moshier analytical Earth; no ephemeris download',
        'limitsDeclaredBeforeEvaluation':{'forwardHorizontalArcsec':5,'inverseJ2000Arcsec':5},'flags':flags,'returnedFlags':sorted(returned),
        'scope':'Fixed J2000 directions with zero proper motion/parallax; vacuum; matched supplied UT1/TT; solar deflection disabled. No survey astrometric calibration or real-weather refraction claim.',
        'timeCaveat':'Numerical UTC field represents constructed UT1 with DUT1=0 and supplied Swiss deltaT, not a measured historic/future UTC offset.',
        'temporaryFixedDirectionInputSha256':hashlib.sha256(text.encode()).hexdigest(),'directions':directions,'locations':locations,'epochs':epochs,'rows':rows,
        'sourceURL':'https://www.astro.com/swisseph/swephprg.htm','dependency':'External verification tool only; library, ephemeris files and third-party code are not redistributed'}
    (R/'tests/fixtures/cp7-directions.json').write_text(json.dumps(output,separators=(',',':'))+'\n')
    print(json.dumps({'directions':len(directions),'epochs':len(epochs),'locations':len(locations),'cases':len(rows),'limits':output['limitsDeclaredBeforeEvaluation']},indent=2))
if __name__=='__main__':main()
