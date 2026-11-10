"""Matched live fixture with an explicit, source-owned clear-mask allocation delta."""
import math
from analyse_cost_v3 import MOON_GEOMETRY,geometry,validate_state

SHARED_CANVASES={
 'moon':[('owner.canvas',300,300)],
 'moonDetail':[('owner.cloudCv',110,111),('owner.cv',110,111)],
 'sky':[('owner.foreground.canvas',325,530),('owner.foreground.cloud',325,183),('owner.foreground.moon',325,183)]}
SOLAR_CANVAS=('owner.foreground.solar',325,530)

def expected_geometry(side):
 assert side in ('A','B'),'Unknown source side'
 return {k:sorted(v+([SOLAR_CANVAS]if k=='sky'and side=='A'else[]))for k,v in SHARED_CANVASES.items()}

def match_geometry(reference,state,side):
 # The reference always comes from baseline A. Its clear mask still allocates
 # a full-size PNG canvas. Exact r17 B returns a resource-free opaque gradient.
 # Check complete inventories, not an intersection that could hide omissions.
 assert geometry(reference)==expected_geometry('A'),'Baseline named canvas inventory/geometry'
 assert geometry(state)==expected_geometry(side),'Source-specific named canvas inventory/geometry'

def match_state(reference,s,required,side):
 validate_state(s,required)
 for key in ['lat','lon','timeScale','paused','weather','tz','camera']:
  assert s['native'][key]==reference['native'][key],'Matched native '+key
 assert s['moon']['accepted']['profile']==reference['moon']['accepted']['profile'],'Matched Moon profile'
 scene=s['moon']['accepted']['scene'];other=reference['moon']['accepted']['scene']
 for key in MOON_GEOMETRY+['waxing']:
  assert scene[key]==other[key],'Matched Moon '+key
 match_geometry(reference,s,side)
 assert s['sky']['last']['catalogue']==reference['sky']['last']['catalogue'],'Matched catalogue'
 for key in ['zone','currentKey','nextKey','timetableDate','nextDate']:
  assert s['prayer']['render'][key]==reference['prayer']['render'][key],'Matched prayer '+key
 phase_error=scene['phaseDisplayDiameter']/2*abs(math.acos(2*s['moon']['currentNativeFraction']-1)-math.acos(2*reference['moon']['currentNativeFraction']-1))
 assert phase_error<=.0416,'Matched phase displacement beyond .0416 device px'
 return {'phasePositionDifferencePx':phase_error,'utcDifferenceMs':s['native']['utcMs']-reference['native']['utcMs'],
         'geometryPolicy':'Exact shared canvases; A retains325x530solar, clear-r17 B has none. All omissions/additions/resizes fail.'}
