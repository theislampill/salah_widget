"""Scratch-only prototype patches (never product): C1 = consistent lead direction + presence-preserving swap;
lead-only = mutant that flips only the lead. Applied to copies under proto/<variant>/moon/src."""
import sys
root, variant = sys.argv[1], sys.argv[2]
def edit(path, pairs):
    s = open(path, encoding='utf-8').read()
    for a, b in pairs:
        assert s.count(a) == 1, (path, a[:60])
        s = s.replace(a, b)
    open(path, 'w', encoding='utf-8', newline='\n').write(s)
prec = root + '/moon/src/moon-precision.mjs'
nat = root + '/moon/src/moon-native.mjs'
LEAD_OLD = "nativeAlpha+(s.waxing?-1:1)*(2*PHASE_POSITION_BUDGET/s.maximumPhaseDiameter)*(1-1e-9)"
# d: +1 alpha falling, -1 rising, 0 dead band; supplied by the native owner as s.phaseDirection.
LEAD_NEW = "nativeAlpha-(s.phaseDirection??(s.waxing?1:-1))*(2*PHASE_POSITION_BUDGET/s.maximumPhaseDiameter)*(1-1e-9)"
SCENE_OLD = "mode:'calendar-canonical',fraction,waxing:s.waxing,"
SCENE_NEW = "mode:'calendar-canonical',fraction,waxing:s.waxing,leadDirection:moving?(s.phaseDirection??(s.waxing?1:-1)):0,"
DRIFT_OLD = "s.phaseDiameter/2*(Math.acos(2*s.fraction-1)-Math.acos(2*record.scene.fraction-1))*(s.waxing?-1:1)"
DRIFT_NEW = "(d=>d===0?s.phaseDiameter/2*Math.abs(Math.acos(2*s.fraction-1)-Math.acos(2*record.scene.fraction-1)):s.phaseDiameter/2*(Math.acos(2*s.fraction-1)-Math.acos(2*record.scene.fraction-1))*(-d))(record.scene.leadDirection??(s.waxing?1:-1))"
if variant in ('c1', 'lead-only'):
    edit(prec, [(LEAD_OLD, LEAD_NEW), (SCENE_OLD, SCENE_NEW)])
if variant == 'c1':
    edit(nat, [(DRIFT_OLD, DRIFT_NEW),
        # presence-preserving swap: on a same-scope geometry expiry, keep the presented detail pixels until the
        # successor is adopted and composed in this same task; full fallback only if no successor is adopted.
        ("  if(accepted&&!presentation(s))fallback('lunar geometry exceeded unchanged display bound');\n  initialPresentation(s,now);",
         "  if(accepted&&!presentation(s)){const keep=sameScope(accepted,s);accepted=null;upperBytes=null;calendarBytes=null;textureUp=null;status.quality='pending';status.visibleSource='awaiting-terrain';status.reason='lunar geometry exceeded unchanged display bound';\n   initialPresentation(s,now);\n   if(accepted){try{window.SalahRealSky?.compose();}catch(error){note(error);}}else{fallback('lunar geometry exceeded unchanged display bound');}\n   if(!keep&&accepted){/* scope changes never reach here: clear() ran above */}\n  }else initialPresentation(s,now);")])
print('patched', variant)
