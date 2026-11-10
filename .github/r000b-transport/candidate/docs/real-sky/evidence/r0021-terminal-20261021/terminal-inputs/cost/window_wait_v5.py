"""Keep host timer early-wake allowance outside the fixed native sample window."""
import asyncio,math,time

def parameters(seconds,resolution):
 if seconds not in (5,15):raise ValueError('Only the declared warmup and observation windows')
 if not math.isfinite(resolution)or not 0<resolution<=.025:raise ValueError('Unsupported host event-loop clock resolution')
 # asyncio's timer queue can run a timer one clock resolution early, and its
 # GetTickCount64 scheduling origin is itself quantized. Reserve both terms.
 # Samples are still selected using exact native [start,start+5s/15s) bounds.
 return {'nominalSeconds':seconds,'hostResolutionSeconds':resolution,'headroomSeconds':2*resolution,'requestedSleepSeconds':seconds+2*resolution}

async def wait_window(seconds,*,sleep=asyncio.sleep,clock=time.perf_counter,resolution=None):
 info=time.get_clock_info('monotonic')
 p=parameters(seconds,info.resolution if resolution is None else resolution)
 start=clock();await sleep(p['requestedSleepSeconds']);elapsed=clock()-start
 if not math.isfinite(elapsed)or elapsed<seconds:raise RuntimeError('Host wait returned before fixed window completed')
 return {**p,'actualQpcElapsedSeconds':elapsed,'hostClockImplementation':info.implementation,
         'selection':'Native first5s/full15s unchanged; extra endpoint headroom never adds samples.'}

def validate_wait(value,seconds):
 expected=parameters(seconds,time.get_clock_info('monotonic').resolution)
 if any(value.get(k)!=v for k,v in expected.items()):raise ValueError('Host wait parameters changed')
 elapsed=value.get('actualQpcElapsedSeconds')
 if not isinstance(elapsed,(int,float))or not math.isfinite(elapsed)or not seconds<=elapsed<=seconds+.25:raise ValueError('Host wait outside unchanged boundary budget')
 if value.get('hostClockImplementation')!=time.get_clock_info('monotonic').implementation:raise ValueError('Host clock changed')
