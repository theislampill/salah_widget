"""Small source-only payload controls; no private key, builder or browser."""
import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest

import r0035_source_payload as subject


class PayloadControls(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.source=self.root/'source';self.source.mkdir(mode=0o700)
        (self.source/'a').write_bytes(b'alpha');(self.source/'b').write_bytes(b'alpha');(self.source/'c').write_bytes(b'beta')
        self.collections=[{'prefix':'records','root':self.source,'names':None}]
        self.binding={'repository':'theislampill/salah_widget','workflowPath':'.github/workflows/r0035-source-preparation.yml',
            'workflowRef':'theislampill/salah_widget/.github/workflows/r0035-source-preparation.yml@refs/heads/chatgpt/r0035-source-preparation-20261127',
            'workflowCommit':'1'*40,'workflowTree':'2'*40,'runId':123,'runAttempt':1,
            'targetCommit':'cc86ce71132be6cb7b93d20a6579dfb42cbc6f92','targetTree':'7ee18182b1c0729086798a59903046948e2e4431',
            'campaignSha256':'63256ceaaa8d58c42956e9be5ff0101dd37100888d330e51162ff345a791ad99','contractSha256':'3'*64}
        self.identities={name:'4'*64 for name in ('harness','target','research','baseline','historical')}
        self.roots={name:'/host/'+name for name in ('harness','target','research','baseline','historical','task','records')}

    def index(self):
        rows,objects,_=subject.inventory_collections(self.collections)
        shards=subject.assign_shards(objects)
        for row in shards:
            row.update(ciphertext={'bytes':100,'sha256':'5'*64},envelope={'bytes':100,'sha256':'6'*64},
                       portableMappingSha256='7'*64,stagedBytes=row['rawBytes']+1000)
            row['descriptorSha256']=subject.digest_bytes(subject.canonical(subject.descriptor(self.binding,self.identities,row['id'],objects)))
        return subject.make_index(self.binding,self.identities,self.roots,rows,objects,shards)

    def restored(self,index,shard_id='0000'):
        folder=self.root/('restored-'+shard_id);folder.mkdir(mode=0o700);(folder/'objects').mkdir(mode=0o700)
        desc=subject.descriptor(index['binding'],index['sourceIdentities'],shard_id,index['objects'])
        (folder/'shard.json').write_bytes(subject.canonical(desc))
        for row in desc['objects']:
            data=b'alpha' if row['sha256']==hashlib.sha256(b'alpha').hexdigest() else b'beta'
            (folder/'objects'/row['sha256']).write_bytes(data)
        return folder

    def test_logical_files_deduplicate_only_identical_raw_bodies(self):
        index=self.index();subject.validate_index(index,self.binding)
        self.assertEqual(index['totals'],{'logicalFiles':3,'logicalBytes':14,'objects':2,'uniqueBytes':9,'shards':1})

    def test_wrong_receiving_or_workflow_binding_refuses(self):
        for key,value in [('targetCommit','0'*40),('workflowCommit','0'*40),('runAttempt',2)]:
            index=self.index();index['binding'][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):subject.validate_index(index,self.binding)

    def test_source_only_authority_cannot_be_promoted(self):
        for key,value in [('nativeIsolationClaim',True),('nativeExecution','OBSERVED'),('scope','NATIVE')]:
            index=self.index();index[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):subject.validate_index(index,self.binding)

    def test_missing_duplicate_extra_reordered_logical_rows_refuse(self):
        for change in ('missing','duplicate','extra','reordered'):
            index=self.index()
            if change=='missing':index['logicalFiles'].pop()
            elif change=='duplicate':index['logicalFiles'].append(copy.deepcopy(index['logicalFiles'][0]))
            elif change=='extra':index['logicalFiles'].append({**index['logicalFiles'][0],'path':'records/extra'})
            else:index['logicalFiles'].reverse()
            with self.subTest(change=change),self.assertRaises(ValueError):subject.validate_index(index,self.binding)

    def test_unknown_fields_and_duplicate_json_keys_refuse(self):
        index=self.index();index['ignored']=True
        with self.assertRaises(ValueError):subject.validate_index(index,self.binding)
        with self.assertRaises(ValueError):subject.load_json(b'{"a":1,"a":2}')

    def test_unsafe_and_case_alias_paths_refuse(self):
        for path in ('../outside','/absolute','records/../escape','records//a','records/./a','records\\a'):
            with self.subTest(path=path),self.assertRaises(ValueError):subject.safe_name(path)
        (self.source/'A').write_bytes(b'alias')
        with self.assertRaises(ValueError):subject.inventory_collections(self.collections)

    def test_symlink_or_nonregular_input_refuses(self):
        (self.source/'link').symlink_to('a')
        with self.assertRaises(ValueError):subject.inventory_collections(self.collections)

    def test_declared_source_duplicate_paths_refuse(self):
        with self.assertRaises(ValueError):subject.inventory_collections([{'prefix':'sources/test','root':self.source,'names':['a','a']}])

    def test_object_hash_size_duplicate_extra_or_assignment_refuses(self):
        for change in ('hash','size','duplicate','extra','assignment'):
            index=self.index()
            if change=='hash':index['objects'][0]['sha256']='0'*64
            elif change=='size':index['objects'][0]['bytes']+=1
            elif change=='duplicate':index['objects'].append(copy.deepcopy(index['objects'][0]))
            elif change=='extra':index['objects'].append({'sha256':'f'*64,'bytes':1,'shard':'0000'})
            else:index['objects'][0]['shard']='0001'
            with self.subTest(change=change),self.assertRaises(ValueError):subject.validate_index(index,self.binding)

    def test_integer_limits_reject_bools_and_oversize_objects(self):
        index=self.index();index['objects'][0]['bytes']=True
        with self.assertRaises(ValueError):subject.validate_index(index,self.binding)
        with self.assertRaises(ValueError):subject.assign_shards([{'sha256':'a'*64,'bytes':subject.MAX_OBJECT_BYTES+1}])

    def test_deterministic_shard_split_and_exact_raw_bound(self):
        rows=[{'sha256':str(i)*64,'bytes':subject.MAX_OBJECT_BYTES//2+1} for i in range(3)]
        shards=subject.assign_shards(rows)
        self.assertEqual([r['id'] for r in shards],['0000','0001','0002'])
        self.assertTrue(all(row['rawBytes']<=subject.MAX_OBJECT_BYTES for row in shards))

    def test_missing_or_reordered_shards_refuse(self):
        for change in ('missing','duplicate','id'):
            index=self.index()
            if change=='missing':index['shards']=[]
            elif change=='duplicate':index['shards'].append(copy.deepcopy(index['shards'][0]))
            else:index['shards'][0]['id']='0001'
            with self.subTest(change=change),self.assertRaises(ValueError):subject.validate_index(index,self.binding)

    def test_actual_shard_copy_and_complete_object_readback(self):
        index=self.index();folder=self.restored(index);out=self.root/'objects';out.mkdir(mode=0o700)
        receipt=subject.accept_shard(index,'0000',folder,out)
        self.assertEqual(receipt['status'],'ACCEPTED')
        self.assertEqual(subject.inspect(index,out)['status'],'COMPLETE_RAW_OBJECT_CUSTODY')
        self.assertEqual(subject.read_logical(index,out,'records/a',10),b'alpha')

    def test_extra_restored_shard_member_refuses(self):
        index=self.index();folder=self.restored(index);(folder/'extra').write_bytes(b'x')
        out=self.root/'objects';out.mkdir(mode=0o700)
        with self.assertRaises(ValueError):subject.accept_shard(index,'0000',folder,out)

    def test_duplicate_acceptance_refuses(self):
        index=self.index();folder=self.restored(index);out=self.root/'objects';out.mkdir(mode=0o700)
        subject.accept_shard(index,'0000',folder,out)
        with self.assertRaises(ValueError):subject.accept_shard(index,'0000',folder,out)

    def test_wrong_shard_descriptor_binding_refuses(self):
        index=self.index();folder=self.restored(index);body=json.loads((folder/'shard.json').read_bytes());body['binding']['runId']=99
        (folder/'shard.json').write_bytes(subject.canonical(body));out=self.root/'objects';out.mkdir(mode=0o700)
        with self.assertRaises(ValueError):subject.accept_shard(index,'0000',folder,out)

    def test_corrupted_raw_body_refuses_without_acceptance(self):
        index=self.index();folder=self.restored(index);next((folder/'objects').iterdir()).write_bytes(b'bad')
        out=self.root/'objects';out.mkdir(mode=0o700)
        with self.assertRaises(ValueError):subject.accept_shard(index,'0000',folder,out)
        self.assertEqual(list(out.iterdir()),[])

    def test_missing_extra_and_mutated_restored_object_refuse(self):
        index=self.index();folder=self.restored(index);out=self.root/'objects';out.mkdir(mode=0o700);subject.accept_shard(index,'0000',folder,out)
        chosen=next(out.iterdir());original=chosen.read_bytes();chosen.unlink()
        with self.assertRaises(ValueError):subject.inspect(index,out)
        chosen.write_bytes(original);extra=out/('f'*64);extra.write_bytes(b'x')
        with self.assertRaises(ValueError):subject.inspect(index,out)
        extra.unlink();chosen.write_bytes(b'changed')
        with self.assertRaises(ValueError):subject.inspect(index,out)

    def test_logical_read_bound_and_unknown_path_refuse(self):
        index=self.index();folder=self.restored(index);out=self.root/'objects';out.mkdir(mode=0o700);subject.accept_shard(index,'0000',folder,out)
        with self.assertRaises(ValueError):subject.read_logical(index,out,'records/a',1)
        with self.assertRaises(ValueError):subject.read_logical(index,out,'unknown',10)

    def test_input_mutation_after_inventory_refuses(self):
        _,_,sources=subject.inventory_collections(self.collections);row=next(iter(sources.values()))
        Path(row['path']).write_bytes(b'changed');destination=self.root/'copy'
        with self.assertRaises(ValueError):subject.copy_checked(row,destination)

    def test_index_restored_population_is_closed(self):
        index=self.index();folder=self.root/'index';folder.mkdir(mode=0o700);(folder/'index.json').write_bytes(subject.canonical(index))
        self.assertEqual(subject.load_index(folder,self.binding),index)
        (folder/'extra').write_text('x')
        with self.assertRaises(ValueError):subject.load_index(folder,self.binding)

    def test_sealed_population_and_exact_ciphertexts_are_checked(self):
        index=self.index();sealed=self.root/'sealed';sealed.mkdir(mode=0o700)
        for name in ('index','shards/0000'):
            path=sealed/name;path.mkdir(mode=0o700,parents=True);(path/'capture.p7m').write_bytes(b'synthetic');(path/'envelope.json').write_bytes(b'{}')
        row=index['shards'][0];row['ciphertext']=subject.file_record(sealed/'shards/0000/capture.p7m');row['envelope']=subject.file_record(sealed/'shards/0000/envelope.json')
        subject.validate_sealed_set(index,sealed)
        (sealed/'shards/0000/capture.p7m').write_bytes(b'substitution')
        with self.assertRaises(ValueError):subject.validate_sealed_set(index,sealed)
        (sealed/'extra').write_bytes(b'extra')
        with self.assertRaises(ValueError):subject.validate_sealed_set(index,sealed)


if __name__=='__main__':unittest.main()
