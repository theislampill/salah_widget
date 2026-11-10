"""Keep v5 native cost analysis, additionally require the repaired host clock."""
from analyse_cost_v5 import analyse as original_analyse
from host_clock_v76 import validate_clock
def analyse(out,record):
 result=original_analyse(out,record)
 try:validate_clock(record.get('hostObservationClock'))
 except (AssertionError,TypeError,ValueError)as error:
  result['globalReasons'].append('Host observation clock: '+str(error));result['status']='INCOMPLETE'
  for window in result.get('windows',{}).values():
   for scope in window.get('scopes',{}).values():
    scope['rawComparisonStatus']=scope['status'];scope['status']='INCOMPLETE';scope.setdefault('reasons',[]).append('Invalid host observation clock metadata');scope.setdefault('reasonCodes',[]).append('GLOBAL')
  for scope in result.get('combinedOwners',{}).values():
   scope['rawComparisonStatus']=scope['status'];scope.update(status='INCOMPLETE',first5='INCOMPLETE',full15='INCOMPLETE',basis='Invalid host observation clock metadata; raw numerical comparisons retained.')
 result['hostObservationClock']=record.get('hostObservationClock')
 return result
