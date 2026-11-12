#!/usr/bin/env python3
"""Inert execution of the real fixture setup prefix; no Windows or installer run.

A file created before its ancestor's private ACL can retain explicit access rules
that copy2 will not reproduce. Required owned parents must be protected before
any other fixture input is created. Actual Windows ACL equality is a native gate.
"""
import argparse, ast, copy, hashlib, json, pathlib, subprocess, tempfile, types


def run_prefix(source, root, platform, deny=False):
    tree=ast.parse(source.read_bytes(),filename=str(source))
    fn=copy.deepcopy(next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_case_impl'))
    cut=next(i for i,n in enumerate(fn.body) if isinstance(n,ast.If) and ast.unparse(n.test)=="scenario in ('readable', 'unreadable')")
    fn.body=fn.body[:cut]
    observed=[];results=[]
    def protect(case, host, modules, paths):
        expected=[root,case,case/'subject',case/'subject/temp',case/'host-home']
        assert paths==expected and all(p.is_dir() for p in paths)
        extras=sorted(str(p.relative_to(case)) for p in case.rglob('*') if p not in expected)
        observed.append(dict(extrasAtProtection=extras,paths=[str(p) for p in paths]))
        if deny:raise OSError('inert parent protection refusal')
    ns=dict(os=types.SimpleNamespace(name=platform,environ={}),ROOT=root,
        composition=types.SimpleNamespace(owned_environment=lambda env:{}),
        case_directory=lambda scenario:root/'c00',protect_parents=protect,
        subprocess=subprocess,RESULTS=results)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),str(source),'exec'),ns)
    result=ns['_case_impl']('ps51','inert-host','inert-modules','github')
    sentinel=root/'c00/host-home/existing-profile-sentinel.bin'
    return observed,results,result,sentinel


def verify(source):
    checks=[]
    def check(name,value,detail=None):checks.append(dict(name=name,pass_=bool(value),detail=detail))
    with tempfile.TemporaryDirectory(prefix='parent-order-') as td:
        base=pathlib.Path(td)
        for platform in ('nt','posix'):
            root=base/platform;root.mkdir()
            observations,results,result,sentinel=run_prefix(source,root,platform)
            check(platform+'-setup-completes',result is None and results==[])
            check(platform+'-sentinel-preserved',sentinel.is_file() and sentinel.read_bytes()==b'preserve owned USERPROFILE bytes\n')
            check(platform+'-all-input-parents-present',all((root/'c00/subject'/part).is_dir() for part in ('temp','local','roam','pf','pf86')))
            if platform=='nt':
                check('windows-only-required-parents-exist-at-protection',len(observations)==1 and observations[0]['extrasAtProtection']==[],observations)
            else:check('posix-no-native-acl-operation',observations==[])
        root=base/'denied';root.mkdir()
        observations,results,result,sentinel=run_prefix(source,root,'nt',True)
        check('protection-refusal-retains-bootstrap-failure',result is False and len(results)==1 and results[0]['classification']=='BOOTSTRAP_BLOCKED' and results[0]['observation']['installerExecuted'] is False)
        check('protection-refusal-prevents-input-creation',not sentinel.exists() and all(not (root/'c00/subject'/part).exists() for part in ('local','roam','pf','pf86')))
    return dict(schema='r0016-fixture-parent-order-check.v1',sourceSha256=hashlib.sha256(source.read_bytes()).hexdigest(),scope='Real setup-prefix execution with inert protection callback; no native ACL or product credit',checks=checks,passed=sum(c['pass_'] for c in checks),failed=sum(not c['pass_'] for c in checks))


def main():
    p=argparse.ArgumentParser();p.add_argument('source',type=pathlib.Path);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args()
    result=verify(a.source);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'passed':result['passed'],'failed':result['failed'],'source':result['sourceSha256']}));return int(result['failed']!=0)


if __name__=='__main__':raise SystemExit(main())
