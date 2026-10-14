"""Read existing Pages artifact ZIP metadata with bounded HTTP range requests."""
import json,subprocess,urllib.request,urllib.error,urllib.parse,struct,pathlib,hashlib
B=pathlib.Path(__file__).resolve().parent
REPO='theislampill/salah_widget';ID=11925399040
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,req,fp,code,msg,headers,newurl):return None
token=subprocess.check_output(['gh','auth','token'],text=True).strip()
req=urllib.request.Request(f'https://api.github.com/repos/{REPO}/actions/artifacts/{ID}/zip',headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','User-Agent':'R0017-packaging-preflight'})
try:
 with urllib.request.build_opener(NoRedirect()).open(req,timeout=30) as r:raise RuntimeError('Expected authenticated artifact redirect')
except urllib.error.HTTPError as e:
 if e.code!=302:raise RuntimeError(f'Artifact redirect HTTP {e.code}') from None
 signed=e.headers['Location']
del token,req
host=urllib.parse.urlparse(signed).hostname
assert signed.startswith('https://') and (host.endswith('.blob.core.windows.net') or host.endswith('.githubusercontent.com'))
requests=[]
def get_range(spec):
 q=urllib.request.Request(signed,headers={'Range':'bytes='+spec,'User-Agent':'R0017-packaging-preflight'})
 with urllib.request.urlopen(q,timeout=30) as r:
  if r.status!=206:raise RuntimeError(f'Range not honored: HTTP {r.status}')
  data=r.read(2_000_001)
  assert len(data)<=2_000_000
  requests.append({'range':spec,'status':r.status,'contentRange':r.headers.get('Content-Range'),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
  return data
metadata=json.loads(subprocess.check_output(['gh','api',f'repos/{REPO}/actions/artifacts/{ID}'],text=True))
total=metadata['size_in_bytes']
tail=get_range(f'{total-65557}-{total-1}');i=tail.rfind(b'PK\x05\x06');assert i>=0
sig,disk,cd_disk,on_disk,count,cd_bytes,cd_offset,comment=struct.unpack_from('<4s4H2LH',tail,i)
assert disk==cd_disk==0 and count==on_disk and count<65535 and cd_bytes<2_000_000
directory=get_range(f'{cd_offset}-{cd_offset+cd_bytes-1}')
entries=[];pos=0
while pos<len(directory):
 assert directory[pos:pos+4]==b'PK\x01\x02'
 f=struct.unpack_from('<4s6H3L5H2L',directory,pos)
 n,e,c=f[10:13];name=directory[pos+46:pos+46+n].decode('utf-8');size=f[9];compressed=f[8];method=f[4];offset=f[16]
 entries.append({'name':name,'uncompressedBytes':size,'compressedBytes':compressed,'compressionMethod':method,'crc32':f'{f[7]:08x}','localHeaderOffset':offset})
 pos+=46+n+e+c
assert len(entries)==count
for entry in entries:
 h=get_range(f'{entry["localHeaderOffset"]}-{entry["localHeaderOffset"]+29}')
 assert h[:4]==b'PK\x03\x04'
 n,e=struct.unpack_from('<HH',h,26);start=entry['localHeaderOffset']+30+n+e
 prefix=get_range(f'{start}-{start+511}');entry['firstBytesHex']=prefix[:16].hex();entry['dataOffset']=start
 if entry['compressionMethod']==0:entry['firstTarMember']=prefix[:100].split(b'\0')[0].decode('utf-8','replace')
out={'schema':'r0017-existing-pages-artifact-inspection/v1','artifact':metadata,'method':'Authenticated GitHub artifact redirect followed without forwarding Authorization; bounded range reads of ZIP central directory and local headers only. Signed URL/token not retained.','archiveEntries':entries,'rangeRequests':requests,'totalBytesRead':sum(x['bytes'] for x in requests),'limits':'ZIP sizes describe packaging, not the sum of published site file bytes. No candidate deployment or full artifact download performed.'}
(B/'existing-pages-artifact.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'artifactId':ID,'apiArtifactBytes':metadata['size_in_bytes'],'entries':entries,'totalBytesRead':out['totalBytesRead']}))
