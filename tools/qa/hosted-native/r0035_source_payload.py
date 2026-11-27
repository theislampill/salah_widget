"""Bounded raw-object custody for SOURCE-ONLY preparation, never native authority.

The original transport and CMS envelope are unchanged. This module contains no
private-key API: root opens each authenticated envelope through the original
reader and supplies its restored directory to the functions below.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import tempfile

PROTOCOL='r0035-source-preparation-envelope-set/1'
SHARD_PROTOCOL='r0035-source-preparation-object-shard/1'
MAX_SHARD_BYTES=96<<20
MAX_OBJECT_BYTES=94<<20  # Two MiB reserved for descriptors, maps and ZIP/CMS overhead.
MAX_UNIQUE_BYTES=768<<20
MAX_LOGICAL_BYTES=3<<30
MAX_FILES=12000
MAX_SHARDS=16
MAX_INDEX_BYTES=16<<20
MAX_INDEX_CIPHER_BYTES=18<<20
CHUNK=1<<20
HEX256=re.compile(r'[0-9a-f]{64}\Z')
HEX160=re.compile(r'[0-9a-f]{40}\Z')
ROLES=('harness','target','research','baseline','historical')
BINDING_KEYS={'repository','workflowPath','workflowRef','workflowCommit','workflowTree','runId','runAttempt',
              'targetCommit','targetTree','campaignSha256','contractSha256'}
WORKFLOW='.github/workflows/r0035-source-preparation.yml'
BRANCH='chatgpt/r0035-source-preparation-20261127'
REPOSITORY='theislampill/salah_widget'
TARGET='cc86ce71132be6cb7b93d20a6579dfb42cbc6f92'
TARGET_TREE='7ee18182b1c0729086798a59903046948e2e4431'
CAMPAIGN='63256ceaaa8d58c42956e9be5ff0101dd37100888d330e51162ff345a791ad99'
TRANSPORT_SHA256='6815cfdb68bea413a740d58e2ddf8e9d4c1185d65638274e8108e37637f3dbfe'
ENVELOPE_SHA256='50b3a4e388f608f7a824b53d3e320c6957f4c4b6f4be5053e69ce01c1dee21be'
CERTIFICATE_SHA256='3b5b260928024cc01499ae50559eb50a1b7529bb338a99ec7291d2b6514c72a9'


def need(value,message):
    if not value:raise ValueError(message)


def canonical(value):
    return (json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False)+'\n').encode()


def digest_bytes(value):return hashlib.sha256(value).hexdigest()


def load_json(raw):
    def pairs(rows):
        result={}
        for key,value in rows:
            need(key not in result,'duplicate JSON field');result[key]=value
        return result
    def invalid(value):raise ValueError('nonfinite JSON value')
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=invalid)


def safe_name(name):
    need(type(name) is str and bool(name) and len(name.encode())<=1024,'invalid logical path')
    need('\\' not in name and all(ord(c)>=32 and ord(c)!=127 for c in name),'unsafe logical path')
    p=PurePosixPath(name)
    need(not p.is_absolute() and str(p)==name and '..' not in p.parts and len(p.parts)<=64,'unsafe logical path')
    need(all(part not in ('','.','..') for part in p.parts),'unsafe logical path')
    return name


def literal(path):
    path=Path(path).absolute()
    need('..' not in path.parts and all(not p.is_symlink() for p in (path,*path.parents)),'aliased filesystem path')
    need(path.resolve()==path,'aliased filesystem path')
    return path


def token(info):return (info.st_dev,info.st_ino,stat.S_IFMT(info.st_mode),info.st_size,info.st_mtime_ns,info.st_ctime_ns)


def owned_directory(path):
    path=literal(path);info=path.stat()
    need(stat.S_ISDIR(info.st_mode) and info.st_uid==os.getuid() and info.st_mode&0o077==0,'private owned directory required')
    return path


def file_record(path,maximum=MAX_OBJECT_BYTES):
    path=literal(path);fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    try:
        info=os.fstat(fd);need(stat.S_ISREG(info.st_mode) and 0<=info.st_size<=maximum,'regular bounded file required')
        total=0;digest=hashlib.sha256()
        while True:
            block=os.read(fd,CHUNK)
            if not block:break
            total+=len(block);need(total<=info.st_size,'file changed while reading');digest.update(block)
        need(total==info.st_size and token(os.fstat(fd))==token(info) and token(path.stat())==token(info),'file changed while reading')
        return {'bytes':total,'sha256':digest.hexdigest()}
    finally:os.close(fd)


def tree_files(root):
    root=literal(root);need(root.is_dir(),'collection root missing');names=[];aliases=set()
    for current,dirs,files in os.walk(root,followlinks=False):
        for name in [*dirs,*files]:
            path=Path(current)/name;logical=safe_name(path.relative_to(root).as_posix())
            need(not path.is_symlink(),'symlink in collection')
            folded=logical.casefold();need(folded not in aliases,'case alias in collection');aliases.add(folded)
        for name in files:
            path=Path(current)/name;need(path.is_file(),'nonregular collection member');names.append(path.relative_to(root).as_posix())
    return sorted(names)


def inventory_collections(collections):
    need(type(collections) is list and bool(collections),'collections required')
    logical=[];objects={};sources={};aliases=set();total=0
    for collection in collections:
        need(set(collection)=={'prefix','root','names'},'collection fields differ')
        prefix=safe_name(collection['prefix']);root=literal(collection['root'])
        names=collection['names'] if collection['names'] is not None else tree_files(root)
        need(type(names) is list and names==sorted(set(names)),'declared source population differs')
        for name in names:
            safe_name(name);path=root/name;logical_path=safe_name(prefix+'/'+name)
            need(logical_path.casefold() not in aliases,'duplicate or aliased logical path');aliases.add(logical_path.casefold())
            before=token(path.lstat());value=file_record(path);need(token(path.lstat())==before,'source changed while inventoried')
            total+=value['bytes'];need(len(logical)<MAX_FILES and total<=MAX_LOGICAL_BYTES,'logical population limit')
            row={'path':logical_path,**value};logical.append(row)
            prior=objects.get(value['sha256']);need(prior is None or prior['bytes']==value['bytes'],'raw digest/size collision')
            objects[value['sha256']]={'sha256':value['sha256'],'bytes':value['bytes']}
            sources.setdefault(value['sha256'],{'path':str(path),'token':before,**value})
    need(logical and sum(r['bytes'] for r in objects.values())<=MAX_UNIQUE_BYTES,'unique population limit')
    return sorted(logical,key=lambda r:r['path']),[objects[k] for k in sorted(objects)],sources


def copy_checked(row,destination):
    path=literal(row['path']);need(token(path.lstat())==tuple(row['token']),'source changed before copy')
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK);output=None
    try:
        need(token(os.fstat(fd))==tuple(row['token']),'source changed before copy')
        output=os.open(literal(destination),os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        total=0;digest=hashlib.sha256()
        while True:
            block=os.read(fd,CHUNK)
            if not block:break
            total+=len(block);need(total<=row['bytes'],'source copy exceeded bound');digest.update(block)
            view=memoryview(block)
            while view:
                count=os.write(output,view);need(count>0,'short object write');view=view[count:]
        need(total==row['bytes'] and digest.hexdigest()==row['sha256'] and token(os.fstat(fd))==tuple(row['token'])
             and token(path.lstat())==tuple(row['token']),'source changed while copied')
        os.fsync(output)
    finally:
        if output is not None:os.close(output)
        os.close(fd)


def assign_shards(objects):
    need(type(objects) is list and 0<len(objects)<=MAX_FILES,'objects required')
    hashes=[r.get('sha256') for r in objects]
    need(all(type(h) is str and HEX256.fullmatch(h) for h in hashes) and hashes==sorted(set(hashes)),'unique ordered object hashes required')
    shards=[]
    for row in objects:
        need(type(row.get('bytes')) is int and 0<=row['bytes']<=MAX_OBJECT_BYTES,'raw object size limit')
        if not shards or shards[-1]['rawBytes']+row['bytes']>MAX_OBJECT_BYTES:
            need(len(shards)<MAX_SHARDS,'shard population limit')
            shards.append({'id':f'{len(shards):04d}','objectCount':0,'rawBytes':0})
        shard=shards[-1];row['shard']=shard['id'];shard['objectCount']+=1;shard['rawBytes']+=row['bytes']
    need(sum(r['rawBytes'] for r in shards)<=MAX_UNIQUE_BYTES,'unique population limit')
    return shards


def validate_binding(binding,expected=None):
    need(type(binding) is dict and set(binding)==BINDING_KEYS,'binding fields differ')
    need(binding['repository']==REPOSITORY and binding['workflowPath']==WORKFLOW
         and binding['workflowRef']==REPOSITORY+'/'+WORKFLOW+'@refs/heads/'+BRANCH,'source-only workflow identity differs')
    need(binding['targetCommit']==TARGET and binding['targetTree']==TARGET_TREE and binding['campaignSha256']==CAMPAIGN,'receiving identity differs')
    for name in ('workflowCommit','workflowTree'):
        need(type(binding[name]) is str and HEX160.fullmatch(binding[name]),'workflow Git identity required')
    need(type(binding['contractSha256']) is str and HEX256.fullmatch(binding['contractSha256']),'contract identity required')
    for name in ('runId','runAttempt'):
        need(type(binding[name]) is int and binding[name]>0,'positive actual run identity required')
    if expected is not None:need(binding==expected,'authenticated external binding differs')


def descriptor(binding,identities,shard_id,objects):
    return {'protocol':SHARD_PROTOCOL,'binding':binding,'sourceIdentities':identities,'id':shard_id,
            'objects':[{k:r[k] for k in ('sha256','bytes')} for r in objects if r['shard']==shard_id]}


def make_index(binding,identities,roots,logical,objects,shards):
    return {'protocol':PROTOCOL,'scope':'SOURCE_ONLY','nativeIsolationClaim':False,'nativeExecution':'NOT_RUN',
            'binding':binding,'sourceIdentities':identities,'logicalRoots':roots,'logicalFiles':logical,'objects':objects,'shards':shards,
            'totals':{'logicalFiles':len(logical),'logicalBytes':sum(r['bytes'] for r in logical),'objects':len(objects),
                      'uniqueBytes':sum(r['bytes'] for r in objects),'shards':len(shards)}}


def validate_index(index,expected_binding=None):
    need(type(index) is dict and set(index)=={'protocol','scope','nativeIsolationClaim','nativeExecution','binding',
         'sourceIdentities','logicalRoots','logicalFiles','objects','shards','totals'},'index fields differ')
    need(index['protocol']==PROTOCOL and index['scope']=='SOURCE_ONLY' and index['nativeIsolationClaim'] is False
         and index['nativeExecution']=='NOT_RUN','source-only authority differs')
    validate_binding(index['binding'],expected_binding)
    ids=index['sourceIdentities'];need(type(ids) is dict and set(ids)==set(ROLES),'source identity population differs')
    need(all(type(value) is str and HEX256.fullmatch(value) for value in ids.values()),'source identity digest required')
    roots=index['logicalRoots'];need(type(roots) is dict and set(roots)==set(ROLES)|{'task','records'},'logical root population differs')
    for value in roots.values():
        need(type(value) is str and PurePosixPath(value).is_absolute() and str(PurePosixPath(value))==value and '..' not in PurePosixPath(value).parts,'literal hosted logical root required')
    logical=index['logicalFiles'];objects=index['objects'];shards=index['shards']
    need(type(logical) is list and 0<len(logical)<=MAX_FILES and type(objects) is list and type(shards) is list,'index populations required')
    names=[];references={}
    for row in logical:
        need(type(row) is dict and set(row)=={'path','bytes','sha256'},'logical row fields differ');safe_name(row['path'])
        need(row['path'].startswith(('records/','task/capture/','task/work/prepared/','task/work/r0035-publish/',
                                     *['sources/'+role+'/' for role in ROLES])) or row['path']=='task/runtime.json','unknown source-only logical population')
        need(type(row['bytes']) is int and 0<=row['bytes']<=MAX_OBJECT_BYTES and type(row['sha256']) is str and HEX256.fullmatch(row['sha256']),'logical file identity invalid')
        names.append(row['path']);prior=references.get(row['sha256']);need(prior is None or prior==row['bytes'],'logical raw digest/size collision');references[row['sha256']]=row['bytes']
    need(names==sorted(set(names)) and len({n.casefold() for n in names})==len(names),'logical population unordered or aliased')
    need(not any('/'.join(name.split('/')[:i]) in set(names) for name in names for i in range(1,len(name.split('/')))),'logical file/directory collision')
    for row in objects:need(type(row) is dict and set(row)=={'sha256','bytes','shard'},'object row fields differ')
    expected_objects=[{'sha256':key,'bytes':references[key]} for key in sorted(references)]
    expected_shards=assign_shards(expected_objects);need(objects==expected_objects,'complete raw object/assignment population differs')
    need(len(shards)==len(expected_shards),'shard population differs')
    for row,expected in zip(shards,expected_shards):
        need(type(row) is dict and set(row)=={'id','objectCount','rawBytes','descriptorSha256','ciphertext','envelope','portableMappingSha256','stagedBytes'},'shard fields differ')
        need(all(row[k]==v and type(row[k]) is type(v) for k,v in expected.items()),'shard order/assignment differs')
        need(row['descriptorSha256']==digest_bytes(canonical(descriptor(index['binding'],ids,row['id'],objects))),'shard descriptor binding differs')
        for label,maximum in (('ciphertext',MAX_SHARD_BYTES),('envelope',4096)):
            rec=row[label];need(type(rec) is dict and set(rec)=={'bytes','sha256'} and type(rec['bytes']) is int and 0<rec['bytes']<=maximum
                 and type(rec['sha256']) is str and HEX256.fullmatch(rec['sha256']),'sealed file identity/limit differs')
        need(type(row['stagedBytes']) is int and row['rawBytes']<row['stagedBytes']<=MAX_SHARD_BYTES
             and type(row['portableMappingSha256']) is str and HEX256.fullmatch(row['portableMappingSha256']),'portable stage limit or identity differs')
    totals={'logicalFiles':len(logical),'logicalBytes':sum(r['bytes'] for r in logical),'objects':len(objects),
            'uniqueBytes':sum(r['bytes'] for r in objects),'shards':len(shards)}
    need(index['totals']==totals and all(type(v) is int for v in index['totals'].values()) and totals['logicalBytes']<=MAX_LOGICAL_BYTES,'complete totals differ')
    need(len(canonical(index))<=MAX_INDEX_BYTES,'index size limit');return index


def load_index(restored_index,expected_binding):
    root=owned_directory(restored_index);need(tree_files(root)==['index.json'] and sorted(p.name for p in root.iterdir())==['index.json'],'restored index population differs')
    record=file_record(root/'index.json',MAX_INDEX_BYTES)
    raw=(root/'index.json').read_bytes();need(digest_bytes(raw)==record['sha256'],'index changed while loaded')
    return validate_index(load_json(raw),expected_binding)


def validate_sealed_set(index,sealed_root):
    validate_index(index);root=owned_directory(sealed_root)
    expected=['index/capture.p7m','index/envelope.json']
    for row in index['shards']:
        for name,key in (('capture.p7m','ciphertext'),('envelope.json','envelope')):
            path='shards/'+row['id']+'/'+name;expected.append(path)
            need(file_record(root/path,MAX_SHARD_BYTES if key=='ciphertext' else 4096)==row[key],'sealed shard substituted or corrupted')
    need(tree_files(root)==sorted(expected),'complete sealed file population differs')
    file_record(root/'index/capture.p7m',MAX_INDEX_CIPHER_BYTES);file_record(root/'index/envelope.json',4096)
    # Empty extra directories are also outside the closed envelope-set population.
    dirs=sorted(str(Path(d,n).relative_to(root)) for d,ns,_ in os.walk(root) for n in ns)
    need(dirs==sorted(['index','shards',*['shards/'+r['id'] for r in index['shards']]]),'complete sealed directory population differs')
    return {'status':'COMPLETE_SEALED_SET','shards':len(index['shards'])}


def accept_shard(index,shard_id,restored_shard,object_root):
    validate_index(index);need(type(shard_id) is str and shard_id in [r['id'] for r in index['shards']],'unknown shard')
    root=owned_directory(restored_shard);output=owned_directory(object_root)
    need(not output.is_relative_to(root) and not root.is_relative_to(output),'overlapping shard/object roots')
    earlier=[r for r in index['objects'] if r['shard']<shard_id]
    need(tree_files(output)==sorted(r['sha256'] for r in earlier) and all(p.is_file() for p in output.iterdir()),'missing, duplicated or reordered shard acceptance')
    for row in earlier:need(file_record(output/row['sha256'])=={k:row[k] for k in ('bytes','sha256')},'previous accepted object changed')
    desc=descriptor(index['binding'],index['sourceIdentities'],shard_id,index['objects']);raw=canonical(desc)
    need(file_record(root/'shard.json',MAX_INDEX_BYTES)=={'bytes':len(raw),'sha256':digest_bytes(raw)} and (root/'shard.json').read_bytes()==raw,'restored shard descriptor differs')
    expected=['shard.json',*['objects/'+r['sha256'] for r in desc['objects']]]
    need(tree_files(root)==sorted(expected) and sorted(p.name for p in root.iterdir())==['objects','shard.json'],'restored shard population differs')
    need(all(p.is_file() and not p.is_symlink() for p in (root/'objects').iterdir()),'extra shard object directory')
    sources=[]
    for row in desc['objects']:
        path=root/'objects'/row['sha256'];before=token(path.lstat());need(file_record(path)==row,'restored raw object differs')
        sources.append({'path':str(path),'token':before,**row})
    # Full input validation precedes the first exclusive object write.
    for row in sources:copy_checked(row,output/row['sha256'])
    need(tree_files(output)==sorted([*[r['sha256'] for r in earlier],*[r['sha256'] for r in desc['objects']]]),'accepted object population differs')
    return {'status':'ACCEPTED','shard':shard_id,'objects':len(sources),'rawBytes':sum(r['bytes'] for r in sources)}


def inspect(index,object_root):
    validate_index(index);root=owned_directory(object_root)
    need(tree_files(root)==[r['sha256'] for r in index['objects']] and all(p.is_file() for p in root.iterdir()),'complete raw object population differs')
    for row in index['objects']:need(file_record(root/row['sha256'])=={k:row[k] for k in ('bytes','sha256')},'raw object hash/size differs')
    return {'protocol':PROTOCOL,'status':'COMPLETE_RAW_OBJECT_CUSTODY','nativeIsolationClaim':False,'nativeExecution':'NOT_RUN','totals':index['totals']}


def read_logical(index,object_root,path,maximum):
    safe_name(path);need(type(maximum) is int and 0<=maximum<=MAX_OBJECT_BYTES,'logical read bound required')
    rows=[r for r in index['logicalFiles'] if r['path']==path];need(len(rows)==1 and rows[0]['bytes']<=maximum,'logical member missing or exceeds read bound')
    row=rows[0];root=owned_directory(object_root);source=root/row['sha256']
    need(file_record(source,maximum)=={k:row[k] for k in ('bytes','sha256')},'logical object differs')
    raw=source.read_bytes();need(len(raw)==row['bytes'] and digest_bytes(raw)==row['sha256'],'logical object changed');return raw


def checked_transport():
    # Load only the exact original bytes, never an unrelated bytecode cache.
    import types
    here=Path(__file__).absolute().parent
    module=types.ModuleType('source_preparation_original_transport');module.__file__=str(here/'capture_transport.py')
    raw=(literal(module.__file__)).read_bytes();need(digest_bytes(raw)==TRANSPORT_SHA256,'original transport changed')
    need(file_record(here/'envelope.py')['sha256']==ENVELOPE_SHA256,'original envelope changed')
    exec(compile(raw,module.__file__,'exec'),module.__dict__);return module


def seal_collections(collections,binding,identities,logical_roots,sealed_root,temporary_parent,certificate):
    validate_binding(binding);output=literal(sealed_root);parent=owned_directory(temporary_parent)
    need(not output.exists() and output.parent.is_dir(),'fresh sealed set required')
    certificate=literal(certificate);need(file_record(certificate)['sha256']==CERTIFICATE_SHA256,'saved recipient certificate changed')
    logical,objects,sources=inventory_collections(collections);shards=assign_shards(objects)
    transport=checked_transport();envelope=transport.envelope()
    output.mkdir(mode=0o700);(output/'shards').mkdir(mode=0o700)
    for row in shards:
        with tempfile.TemporaryDirectory(prefix='source-shard-'+row['id']+'-',dir=parent) as directory:
            work=Path(directory);work.chmod(0o700);raw=work/'raw';raw.mkdir(mode=0o700);(raw/'objects').mkdir(mode=0o700)
            desc=descriptor(binding,identities,row['id'],objects);body=canonical(desc);(raw/'shard.json').write_bytes(body)
            for obj in desc['objects']:copy_checked(sources[obj['sha256']],raw/'objects'/obj['sha256'])
            stage=work/'portable';result=transport.execute('stage',raw,stage,protected_roots=[Path(__file__).absolute().parents[3]])
            staged_bytes=sum((stage/name).stat().st_size for name in tree_files(stage))
            need(staged_bytes<=MAX_SHARD_BYTES-(1<<20),'portable shard overhead exceeded reserve')
            destination=output/'shards'/row['id'];envelope.execute('seal',stage,destination,certificate)
            row.update(descriptorSha256=digest_bytes(body),portableMappingSha256=result['mappingSha256'],stagedBytes=staged_bytes,
                       ciphertext=file_record(destination/'capture.p7m',MAX_SHARD_BYTES),envelope=file_record(destination/'envelope.json',4096))
    after,after_objects,_=inventory_collections(collections)
    need(after==logical and after_objects==[{k:r[k] for k in ('sha256','bytes')} for r in objects],'complete logical population changed while sealed')
    index=validate_index(make_index(binding,identities,logical_roots,logical,objects,shards),binding)
    with tempfile.TemporaryDirectory(prefix='source-index-',dir=parent) as directory:
        work=Path(directory);work.chmod(0o700);raw=work/'raw';raw.mkdir(mode=0o700);(raw/'index.json').write_bytes(canonical(index))
        stage=work/'portable';transport.execute('stage',raw,stage,protected_roots=[Path(__file__).absolute().parents[3]])
        envelope.execute('seal',stage,output/'index',certificate)
        file_record(output/'index/capture.p7m',MAX_INDEX_CIPHER_BYTES)
    validate_sealed_set(index,output);return index


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('operation',choices=('inspect','accept-shard','validate-sealed'))
    parser.add_argument('--index',required=True,type=Path);parser.add_argument('--binding',required=True,type=Path)
    parser.add_argument('--objects',type=Path);parser.add_argument('--shard-id');parser.add_argument('--restored-shard',type=Path);parser.add_argument('--sealed',type=Path)
    args=parser.parse_args();os.umask(0o077)
    index=load_index(args.index,load_json(args.binding.read_bytes()))
    if args.operation=='inspect':result=inspect(index,args.objects)
    elif args.operation=='validate-sealed':result=validate_sealed_set(index,args.sealed)
    else:result=accept_shard(index,args.shard_id,args.restored_shard,args.objects)
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':main()
