"""Stream existing Pages artifact headers; retain no site payload/archive."""
import hashlib, io, json, pathlib, subprocess, tarfile, urllib.error, urllib.parse, urllib.request, zlib

B = pathlib.Path(__file__).resolve().parent
metadata = json.loads((B/'existing-pages-artifact.json').read_text(encoding='utf-8'))
entry = metadata['archiveEntries'][0]
assert entry['name'] == 'artifact.tar' and entry['compressionMethod'] == 8
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl): return None
token = subprocess.check_output(['gh','auth','token'],text=True).strip()
req = urllib.request.Request('https://api.github.com/repos/theislampill/salah_widget/actions/artifacts/11925399040/zip',headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','User-Agent':'R0017-size-preflight'})
try:
    with urllib.request.build_opener(NoRedirect()).open(req,timeout=30): raise RuntimeError('Expected artifact redirect')
except urllib.error.HTTPError as e:
    if e.code != 302: raise RuntimeError('Artifact redirect HTTP '+str(e.code)) from None
    signed = e.headers['Location']
del token, req
host = urllib.parse.urlparse(signed).hostname
assert signed.startswith('https://') and (host.endswith('.blob.core.windows.net') or host.endswith('.githubusercontent.com'))
start = entry['dataOffset']; compressed_size = entry['compressedBytes']
req = urllib.request.Request(signed,headers={'Range':f'bytes={start}-{start+compressed_size-1}','User-Agent':'R0017-size-preflight'})
response = urllib.request.urlopen(req,timeout=60)
assert response.status == 206
assert response.headers['Content-Range'] == f'bytes {start}-{start+compressed_size-1}/{metadata["artifact"]["size_in_bytes"]}'
del signed, req

class Inflated(io.RawIOBase):
    def __init__(self):
        self.dec=zlib.decompressobj(-15); self.buf=b''; self.compressed=0; self.total=0; self.crc=0
        self.digest=hashlib.sha256(); self.input_digest=hashlib.sha256(); self.done=False
    def readable(self): return True
    def readinto(self,b):
        while not self.buf and not self.done:
            raw=response.read(1024*1024)
            if raw:
                self.compressed+=len(raw); self.input_digest.update(raw)
                assert self.compressed<=compressed_size
                data=self.dec.decompress(raw)
            else:
                data=self.dec.flush(); self.done=True
                assert self.dec.eof and not self.dec.unused_data
            self.total+=len(data); assert self.total<=entry['uncompressedBytes']
            self.crc=zlib.crc32(data,self.crc); self.digest.update(data); self.buf+=data
        n=min(len(b),len(self.buf)); b[:n]=self.buf[:n]; self.buf=self.buf[n:]; return n

reader=Inflated(); buffered=io.BufferedReader(reader,buffer_size=1024*1024)
members=[]
with tarfile.open(fileobj=buffered,mode='r|') as tar:
    for m in tar:
        name=m.name
        while name.startswith('./'): name=name[2:]
        assert not name.startswith('/') and '..' not in pathlib.PurePosixPath(name).parts
        members.append({'path':name,'bytes':m.size,'kind':'file' if m.isfile() else 'directory' if m.isdir() else 'symlink' if m.issym() else 'hardlink' if m.islnk() else 'other'})
        if len(members)%5000==0: print(json.dumps({'membersRead':len(members),'compressedBytesRead':reader.compressed}),flush=True)
while buffered.read(1024*1024): pass
response.close()
assert reader.compressed == compressed_size and reader.total == entry['uncompressedBytes']
assert f'{reader.crc:08x}' == entry['crc32']
regular=[m for m in members if m['kind']=='file']
assert len({m['path'] for m in regular}) == len(regular)
index_path=B/'existing-pages-member-index.json'
index_path.write_text(json.dumps({'artifactId':11925399040,'sourceCommit':'763a460e98dc23c7f0e95bf346274f1685b3c654','members':members},indent=2)+'\n',encoding='utf-8')
out={'schema':'r0017-existing-pages-payload-size/v1','artifactId':11925399040,'sourceCommit':'763a460e98dc23c7f0e95bf346274f1685b3c654','workflowRun':38631069804,
     'method':'Read-only HTTP range streaming and DEFLATE/TAR header parsing; no payload extraction, no browser operation and no retained large archive. TAR CRC32 and byte counts verified against ZIP central directory.',
     'compressedArtifactBytes':metadata['artifact']['size_in_bytes'],'compressedTarBytes':reader.compressed,'tarContainerBytes':reader.total,
     'tarSha256':reader.digest.hexdigest(),'compressedTarSha256':reader.input_digest.hexdigest(),'tarCrc32':f'{reader.crc:08x}',
     'regularFileCount':len(regular),'regularFilePayloadBytes':sum(m['bytes'] for m in regular),'directoryCount':sum(m['kind']=='directory' for m in members),
     'otherEntries':[m for m in members if m['kind'] not in ['file','directory']],
     'memberIndexSha256':hashlib.sha256(index_path.read_bytes()).hexdigest(),
     'limits':'Measured existing successful main artifact, not a candidate build/deployment. TAR container bytes and compressed artifact bytes are not published regular-file payload bytes.'}
(B/'existing-pages-payload.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print(json.dumps(out),flush=True)
