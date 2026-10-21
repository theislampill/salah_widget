"""Owned browser native markers only; no page timer/privacy preference override."""
from pathlib import Path
import ast,asyncio,datetime,hashlib,json,socket,time
import psutil
O=Path(__file__).resolve().parents[1]
MAX_PROFILE_BYTES=268435456
source=O/'parent/firefox_actual_widget_r9.py'
assert hashlib.sha256(source.read_bytes()).hexdigest()=='6e96a3a6eee2b8d2fb54d0ff04828c7103101c9375a1c9cad640efaeb00646e4'
node=next(n for n in ast.parse(source.read_text()).body if isinstance(n,ast.ClassDef)and n.name=='Client')
log=[];exec(compile(ast.Module(body=[node],type_ignores=[]),str(source),'exec'))

class DeadlineClient(Client):
 def __init__(self,sock,deadline):self.deadline=deadline;super().__init__(sock)
 def call(self,name,params=None):
  remaining=self.deadline-time.monotonic()
  if remaining<=0:raise TimeoutError('Native profiler operation deadline')
  self.sock.settimeout(min(20,remaining))
  return super().call(name,params)
 def read(self):
  def receive(count):
   remaining=self.deadline-time.monotonic()
   if remaining<=0:raise TimeoutError('Native profiler operation deadline')
   self.sock.settimeout(min(20,remaining));value=self.sock.recv(count)
   if not value:raise EOFError('Profiler connection closed')
   return value
  prefix=b''
  while True:
   c=receive(1)
   if c==b':':break
   prefix+=c;assert len(prefix)<=10,'Invalid protocol prefix'
  size=int(prefix);assert 0<size<20000000,'Invalid protocol payload length'
  value=b''
  while len(value)<size:value+=receive(min(size-len(value),65536))
  return json.loads(value)

class NativeProfiler:
 def __init__(self,engine):self.engine=engine;self.client=None;self.cdp=None;self.active=False;self.attach={}
 def chrome_async(self,js):return self.client.call('WebDriver:ExecuteAsyncScript',{'script':js,'args':[],'newSandbox':True,'sandbox':'default','scriptTimeout':20000,'line':1,'filename':'r0021-cost-native-profile'})['value']
 async def connect(self):
  processes=psutil.Process().children(recursive=True);commands=[{'pid':p.pid,'created':p.create_time(),'exe':p.exe(),'cmdline':p.cmdline()}for p in processes]
  roots={Path(r['cmdline'][r['cmdline'].index('-profile')+1])for r in commands if '-profile'in r['cmdline']and Path(r['exe']).name=='firefox.exe'}
  assert len(roots)==1,'Ambiguous owned Firefox profile';path=next(iter(roots))/'MarionetteActivePort';deadline=time.monotonic()+8
  while not path.is_file():
   if time.monotonic()>deadline:raise TimeoutError('Owned Marionette port missing')
   await asyncio.sleep(.1)
  port=int(path.read_text().strip());assert 0<port<65536
  listeners=[{'pid':p.pid,'address':list(c.laddr)}for p in processes for c in p.net_connections(kind='tcp')if c.status=='LISTEN']
  assert any(x['address']in [['127.0.0.1',port],['::1',port]]for x in listeners),'Unowned profiler port'
  self.attach={'ownedProcesses':commands,'ownedListeners':listeners,'activePortFile':str(path),'activePortSha256':hashlib.sha256(path.read_bytes()).hexdigest(),'port':port}
  sock=socket.create_connection(('127.0.0.1',port),timeout=5);self.client=DeadlineClient(sock,self.deadline);self.attach['hello']=self.client.hello
  self.attach['session']=self.client.call('WebDriver:NewSession',{'capabilities':{'alwaysMatch':{'acceptInsecureCerts':False,'timeouts':{'script':20000}}}})
  self.client.call('Marionette:SetContext',{'value':'chrome'})
 async def start(self,ctx,page):
  assert not self.active
  self.deadline=time.monotonic()+30
  if self.engine=='firefox':
   if self.client is None:await self.connect()
   self.client.deadline=self.deadline
   self.client.call('Marionette:SetContext',{'value':'content'})
   handles=self.client.call('WebDriver:GetWindowHandles');assert len(handles)==1,'Ambiguous owned cost page'
   self.client.call('WebDriver:SwitchToWindow',{'handle':handles[0],'focus':False})
   self.client.call('Marionette:SetContext',{'value':'chrome'})
   r=self.chrome_async("const done=arguments[arguments.length-1];Services.profiler.StartProfiler(4194304,1000,['nostacksampling'],['GeckoMain']).then(()=>done({active:Services.profiler.IsActive(),config:Services.profiler.activeConfiguration}),e=>done({error:String(e)}));")
   assert r['active'];self.active=True;return r
  self.cdp=await ctx.new_cdp_session(page);self.buffer=[];self.cdp.on('Tracing.bufferUsage',lambda e:self.buffer.append(e))
  r=await self.cdp.send('Tracing.start',{'categories':'blink.user_timing','transferMode':'ReturnAsStream','bufferUsageReportingInterval':1000});self.active=True;return r
 async def stop(self,path):
  assert self.active
  assert not path.exists(),'Preserve existing native profile, including failed partial output'
  if self.engine=='firefox':
   self.client.deadline=time.monotonic()+30
   r=self.chrome_async("const done=arguments[arguments.length-1];Services.profiler.dumpProfileToFileAsync("+json.dumps(str(path))+").then(()=>done({ok:true}),e=>done({error:String(e)}));");assert r['ok']
   r['profileBytes']=path.stat().st_size;assert r['profileBytes']<=MAX_PROFILE_BYTES,'Native profile byte budget exceeded'
   r['stop']=self.chrome_async("const done=arguments[arguments.length-1];Services.profiler.StopProfiler().then(()=>done({active:Services.profiler.IsActive()}),e=>done({error:String(e)}));");assert r['stop'].get('active')is False
  else:
   deadline=time.monotonic()+30
   async def send(method,args=None):
    remaining=deadline-time.monotonic()
    if remaining<=0:raise TimeoutError('Native profiler stop/drain deadline')
    return await asyncio.wait_for(self.cdp.send(method,args),remaining)
   future=asyncio.get_running_loop().create_future();self.cdp.once('Tracing.tracingComplete',lambda e:future.set_result(e)if not future.done()else None);await send('Tracing.end');r=await asyncio.wait_for(future,max(.001,min(20,deadline-time.monotonic())));assert r.get('stream')
   total=0
   with path.open('w',encoding='utf-8')as f:
    while True:
     part=await send('IO.read',{'handle':r['stream'],'size':1048576});assert not part.get('base64Encoded');total+=len(part['data'].encode('utf-8'));assert total<=MAX_PROFILE_BYTES,'Native profile byte budget exceeded';f.write(part['data'])
     if part.get('eof'):break
   await send('IO.close',{'handle':r['stream']});r.update(bufferUsage=self.buffer,profileBytes=total);await asyncio.wait_for(self.cdp.detach(),max(.001,deadline-time.monotonic()));self.cdp=None
  self.active=False;return r
 async def close(self):
  result={'activeAtClose':self.active}
  if self.client:
   self.client.deadline=time.monotonic()+15
   try:
    if self.active:result['emergencyStop']=self.chrome_async("const done=arguments[arguments.length-1];Services.profiler.StopProfiler().then(()=>done({active:Services.profiler.IsActive()}));")
    result['deleteSession']=self.client.call('WebDriver:DeleteSession')
   finally:self.client.sock.close();self.client=None
  result['commands']=log;return result
