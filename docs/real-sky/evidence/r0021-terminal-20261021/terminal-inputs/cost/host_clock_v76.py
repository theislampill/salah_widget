"""One validated high-resolution monotonic family for host event observations."""
import math,time
def validate_clock(value):
 assert isinstance(value,dict)and set(value)=={'api','implementation','resolutionSeconds','monotonic','adjustable'},'Missing/mixed host observation clock metadata'
 assert value['api']=='time.perf_counter'and value['implementation']=='QueryPerformanceCounter()','Unqualified host observation clock family'
 assert value['monotonic']is True and value['adjustable']is False,'Host observation clock must be monotonic/nonadjustable'
 r=value['resolutionSeconds']
 assert isinstance(r,(int,float))and not isinstance(r,bool)and math.isfinite(r)and 0<r<=1e-6,'Unqualified host observation clock resolution'
 return value
def clock_info():
 info=time.get_clock_info('perf_counter')
 return validate_clock({'api':'time.perf_counter','implementation':info.implementation,'resolutionSeconds':info.resolution,'monotonic':info.monotonic,'adjustable':info.adjustable})
