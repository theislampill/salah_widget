#!/usr/bin/env python3
"""Numerical acceptance of the recorded actual-widget CP8.2 scene matrix."""
import argparse,json
from pathlib import Path

def verify(path):
 rows=json.loads(path.read_text(encoding='utf-8'));by={r['scene']['name']:r for r in rows};checks=[]
 def check(name,ok):
  assert ok,name
  checks.append(name)
 check('fifteen unique native scenes',len(rows)==len(by)==15)
 for name,r in by.items():
  s=r['state'];p=s['sky']['last'];d=p['diffuseState'];m=s['qa']['moonTruth']
  check(name+': optional physical sky and usable prayer/PBR',not r['error'] and not r['pageErrors'] and s['prayerRows']==6 and s['sky']['status']=='ready' and s['syntheticPoints']==0 and m['surface']['status']=='pbr' and 'real-sky-composed' in s['classes'])
  check(name+': exact real source admitted',p['diffuseAsset']['mode']=='registered' and d['sourceSha256']=='69f3c6ede4a730e0ca4699f5943fca59d0b203f37c4dfc4b7e6927f063250446')
  check(name+': cloud authority not duplicated in worker',p['atmosphere']['cloudTransmission']==1 and d['budget']['afterCloud']==d['budget']['afterGas'] and p['composition']['cloudApplications']==1)
  check(name+': old total night floor replaced',d['nightBudget']['mode']=='nonstellar-residual-replaces-legacy-floor' and not d['nightBudget']['residual']['includesRegisteredStarlight'])
  check(name+': preview weather provenance explicit',s['native']['weather']['src']=='sim')
 for name in ['daylight','overcast-day']:
  p=by[name]['state']['sky']['last'];check(name+': bright sky suppresses contrast without deleting catalogue',p['physicalState']['sun']['altDeg']>60 and p['detectableSources']==0 and p['drawn']>0)
 p=by['twilight']['state']['sky']['last'];check('twilight fixture actually twilight',-8<p['physicalState']['sun']['altDeg']<-3)
 p=by['physical-full-moon']['state']['sky']['last'];check('physical full Moon above horizon',p['physicalState']['moon']['illuminatedFraction']>.99 and p['physicalState']['moon']['altDeg']>60)
 truth=by['clear-night']['state']['sky']['last']['physicalState']
 for name in ['calendar-full','calendar-gibbous','calendar-crescent','calendar-new-below']:
  check(name+': native preview does not substitute physical ephemeris',by[name]['state']['sky']['last']['physicalState']==truth)
 check('strict map support remains incomplete',by['strict-source-support']['state']['sky']['last']['diffuseState']['exposureComplete'] is False and by['strict-source-support']['state']['sky']['last']['diffuseState']['missingPixels']>0)
 check('admitted low visibility reaches aerosol assumption',by['fog-twilight']['state']['sky']['last']['atmosphere']['aerosolTau550']==.33)
 check('accepted local-light control reaches physical budget',by['urban-night']['state']['native']['lp']==1 and by['urban-night']['state']['sky']['last']['atmosphere']['lightPollutionCdM2']==.003)
 check('actual partial and overcast native cloud alpha present',by['partial-cloud-night']['state']['sky']['last']['composition']['meanCloudAlpha']>0 and by['overcast-day']['state']['sky']['last']['composition']['meanCloudAlpha']>0)
 return {'status':'PASS','sceneCount':len(rows),'checks':checks,'checkCount':len(checks),'pageErrors':0,'boundary':'Native Linux Chromium embedded-app evidence with controlled prayer/weather inputs. Source/geometry assumptions remain inherited.'}
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('results',type=Path);a.add_argument('--output',type=Path,required=True);x=a.parse_args();r=verify(x.results);x.output.write_text(json.dumps(r,indent=2));print('Native matrix PASS:',r['sceneCount'],'scenes;',r['checkCount'],'assertions')
