"""Controls for source-calendar expectations, independent of widget model code."""
import ast
import copy
from datetime import datetime, timedelta
from pathlib import Path
import unittest

source=Path(__file__).resolve().parents[2]/'tools/cp9/geography_entry_check.py'
tree=ast.parse(source.read_text(encoding='utf-8'));scope={'datetime':datetime,'timedelta':timedelta}
for node in tree.body:
    if isinstance(node,ast.FunctionDef) and node.name=='prayer_checks':
        exec(compile(ast.Module(body=[node],type_ignores=[]),str(source),'exec'),scope)
check=scope['prayer_checks']

class GeographicTimetableOracle(unittest.TestCase):
    def test_tomorrow_fajr_is_promoted_and_yesterday_value_is_rejected(self):
        today={'Fajr':'04:00 (CEST)','Sunrise':'07:26 (CEST)','Dhuhr':'12:32 (CEST)','Asr':'14:39 (CEST)','Maghrib':'17:35 (CEST)','Isha':'20:48 (CEST)'}
        tomorrow={**today,'Fajr':'04:04 (CEST)'};days={'08-10-2026':{'timings':today},'09-10-2026':{'timings':tomorrow}}
        state={'rows':[{'key':k,'time':('04:04' if k=='Fajr' else v[:5])} for k,v in today.items()],
               'render':{'timetableDate':'08-10-2026','timetable':today,'nextKey':'Fajr','nextDate':'09-10-2026','nextTime':'04:04 (CEST)'}}
        self.assertTrue(all(check(state,days,{'localClock':'21:18'},'08-10-2026').values()))
        wrong=copy.deepcopy(state);wrong['rows'][0]['time']='04:00'
        self.assertFalse(check(wrong,days,{'localClock':'21:18'},'08-10-2026')['prayerRecord'])
        wrong=copy.deepcopy(state);wrong['render']['nextDate']='08-10-2026'
        self.assertFalse(check(wrong,days,{'localClock':'21:18'},'08-10-2026')['nextSourceRecord'])

    def test_event_is_current_at_its_exact_minute_and_next_moves_forward(self):
        timings={'Fajr':'06:18','Sunrise':'07:22','Dhuhr':'13:13','Asr':'16:35','Maghrib':'19:03','Isha':'20:08'}
        state={'rows':[{'key':k,'time':v} for k,v in timings.items()], 'render':{'timetableDate':'08-10-2026','timetable':timings,'nextKey':'Sunrise','nextDate':'08-10-2026','nextTime':'07:22'}}
        self.assertTrue(all(check(state,{'08-10-2026':{'timings':timings}},{'localClock':'06:18'},'08-10-2026').values()))
        state['render']['nextKey']='Fajr'
        self.assertFalse(check(state,{'08-10-2026':{'timings':timings}},{'localClock':'06:18'},'08-10-2026')['nextSourceRecord'])
