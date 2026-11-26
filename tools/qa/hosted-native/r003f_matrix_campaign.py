"""Optional R003F matrix selection and actual source/preparation custody.

No browser is imported here. Receipts contain private paths and belong inside
capture. Original materialization and common preparation receipts are retained.
"""
import argparse
import errno
import ipaddress
import re
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys

from prepare import validate_prepared

HERE = Path(__file__).resolve().parent
MATERIALIZATION = '9081c7b85ce22650c6a0e352f241f57cec4e9342f900e1b2aea1c963cc7ae18f'
MATERIALIZER = '14520a0bf2cf2511b74f3663cf15a80706c8e768bfdf8dd884dd01754f81c8c4'
COMMON_PREPARER = '9f1a104ea49e263bee83dc6a82491830a4a105a751eb821ea8c4cefa0c68c114'
CATALOGUE_SHA256 = '8c92879dca590e494ce55a2c14e7c32dd12151b1ec86d5c5608fb5650b3f9b06'
PROTOCOL = 'R003F/matrix-preparation/1'
ENTRY_PROTOCOL = 'R003F/matrix-preparation-entry/1'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def regular(path):
    p = Path(path).absolute()
    if any(q.is_symlink() for q in (p, *p.parents)) or not p.is_file():
        raise ValueError('regular source or receipt required: '+str(p))
    return p


def record(path):
    p = regular(path)
    return {'path':str(p), 'sha256':sha(p)}


def load(path):
    return json.loads(regular(path).read_bytes())


def save(path, value):
    """Exclusive durable receipt; a failed attempt is never rewritten."""
    p = Path(path)
    with p.open('x') as stream:
        os.chmod(p, 0o600)
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n');stream.flush();os.fsync(stream.fileno())


def success(value, label):
    if (not isinstance(value,dict) or type(value.get('returncode')) is not int
            or value['returncode'] != 0 or value.get('timedOut') is not False
            or value.get('error') or ('retentionError' in value and value['retentionError'] is not None)):
        raise ValueError(label+' actual process did not succeed')


def catalogue():
    p=HERE/'r003f-matrix-catalogue.json'
    if sha(p)!=CATALOGUE_SHA256:raise ValueError('original catalogue source differs')
    return load(p)


def matrix_budget(cell, names):
    if cell['group']=='motion':raise ValueError('unsupported motion: actual media tool custody is not implemented')
    if cell['group'] in ('strap','buckle'):
        shots=4*cell['repeats']*len(names)
    elif cell['group']=='ineligible':shots=len(names)
    else:
        ordered=list(dict.fromkeys([n.split('-')[0] for n in names]+names))
        shots=7+2*len(ordered)+(len(names) if -2<cell['alt']<4 else 0)
        # Original optional hidden captures are allowed two settle/transport
        # intervals within the overhead, after the same original refined wait.
    native=max(1800,100*math.ceil((shots*152.5+max(400,20*shots))/100))
    intake=900 if len(names)==8 else 180
    preparation=1320
    lane=native+105  # current source check90, terminal custody15
    coordinator=60*math.ceil((preparation+lane+75+intake+60)/60)
    if coordinator>16200:raise ValueError('unsupported population budget exceeds the reviewed 270-minute coordinator ceiling')
    return {'shots':shots,'nativeSeconds':native,'sourceCheckSeconds':90,'laneSeconds':lane,
            'intakeSeconds':intake,'preparationSeconds':preparation,'namespaceOverheadSeconds':75,
            'coordinatorSeconds':coordinator,'workflowObservationMinutes':math.ceil(coordinator/60)+1}


def matrix_controls(value, harness, selected, engine, dpr):
    if harness!='corrected-matrix':
        if value is not None:raise ValueError('matrix selector requires corrected-matrix harness')
        return None
    if selected!=['R003F'] or engine not in ('chromium','firefox','webkit') or type(dpr) is not int or dpr not in (1,2):
        raise ValueError('matrix requires only selected R003F and an original engine/DPR')
    if not isinstance(value,dict) or set(value)!= {'id','variant'} or any(not isinstance(x,str) for x in value.values()):
        raise ValueError('matrix selector requires exactly id and variant strings')
    c=catalogue();population=next(p for p in c['populations'] if p['engine']==engine and p['dpr']==dpr)
    matches=[x for x in population['cells'] if x['id']==value['id']]
    if len(matches)!=1 or value['variant'] not in [*c['variants'],'all']:raise ValueError('unknown original matrix cell or variant')
    cell=matches[0]
    if engine=='webkit' and cell['gpu']=='software':raise ValueError('unsupported WebKit software trace custody')
    names=c['variants'] if value['variant']=='all' else [value['variant']]
    return {'selection':dict(value),'cell':cell,'names':names,'budget':matrix_budget(cell,names)}


def verify_pins(expected):
    p=HERE/'r003f-matrix-central-pins.json'
    if sha(p)!=expected:raise ValueError('matrix central manifest digest differs')
    pins=load(p)
    if pins.get('protocol')!='R003F/matrix-central-source/1':raise ValueError('matrix central source protocol differs')
    for name,digest in pins['files'].items():
        if sha(regular(HERE/name))!=digest:raise ValueError('matrix central source differs: '+name)
    return record(p)


CAP_FIELDS = ('CapInh', 'CapPrm', 'CapEff', 'CapBnd', 'CapAmb')


def validate_original_snapshot(snapshot, outer_netns):
    if len(snapshot['uids']) != 3 or min(snapshot['uids']) <= 0 or len(set(snapshot['uids'])) != 1:
        raise ValueError('nonroot real/effective/saved UID required')
    if len(snapshot['gids']) != 3 or min(snapshot['gids']) <= 0 or len(set(snapshot['gids'])) != 1:
        raise ValueError('nonroot real/effective/saved GID required')
    if snapshot['groups']:
        raise ValueError('supplementary groups retained')
    if not outer_netns or snapshot['netns'] == outer_netns:
        raise ValueError('fresh network namespace required')
    links = snapshot['links']
    if len(links) != 1 or links[0]['ifname'] != 'lo' or not {'LOOPBACK', 'UP'} <= set(links[0]['flags']):
        raise ValueError('only an active loopback interface is allowed')
    for route in snapshot['routes4'] + snapshot['routes6']:
        dst = route.get('dst')
        if route.get('dev') != 'lo' or route.get('gateway') or dst in (None, 'default'):
            raise ValueError('non-loopback route')
        network = ipaddress.ip_network(dst, strict=False)
        if not network.is_loopback and str(network) != 'ff00::/8':
            raise ValueError('external destination route')
    for name in CAP_FIELDS:
        if int(snapshot['status'][name], 16) != 0:
            raise ValueError('retained capability ' + name)
    if snapshot['status'].get('NoNewPrivs') != '1':
        raise ValueError('no-new-privileges missing')
    if snapshot['externalSocketErrno'] not in (errno.ENETUNREACH, errno.EHOSTUNREACH):
        raise ValueError('external socket was not refused by routing boundary')


def original_isolation(isolation_path):
    """Validate the original preparation namespace, never the current lane's namespace.

    The receipt binds its full browser-control body; the retained sibling report
    must be identical. These pure checks add no native evidence or socket probe.
    """
    p=regular(isolation_path);receipt=load(p)
    if receipt.get('protocol')!='salah-hosted-native-isolation/1' or receipt.get('passed') is not True or receipt.get('error'):
        raise ValueError('original preparation isolation did not succeed')
    kernel=receipt.get('kernel',{})
    if (not isinstance(kernel,dict) or any(not isinstance(kernel.get(k),list) or
            any(type(v) is not int for v in kernel[k]) for k in ('uids','gids'))
            or type(receipt.get('uid')) is not int or receipt['uid']<=0
            or kernel.get('uids')!=[receipt['uid']]*3
            or receipt.get('netns')!=kernel.get('netns')
            or any(not isinstance(receipt.get(k),str) or re.fullmatch(r'net:\[\d+\]',receipt[k]) is None for k in ('netns','outerNetns'))):
        raise ValueError('original preparation UID or namespace identity differs')
    validate_original_snapshot(kernel,receipt['outerNetns'])
    success(receipt.get('browserProcess'),'original browser boundary')
    browser=receipt.get('browserControl',{})
    if (not isinstance(browser,dict) or browser.get('protocol')!='salah-hosted-browser-boundary/1'
            or browser.get('passed') is not True or browser.get('error') or browser.get('chromiumSandbox') is not True
            or type(browser.get('uid')) is not int or browser['uid']!=receipt['uid'] or browser.get('netns')!=receipt['netns']
            or browser.get('postNegativePage')!='fresh-page-same-browser'
            or type(browser.get('loopbackRequests')) is not int or browser['loopbackRequests']<2
            or not isinstance(browser.get('externalNavigationError'),str)
            or re.search(r'ERR_(NETWORK|ADDRESS)_UNREACHABLE|ERR_INTERNET_DISCONNECTED',browser['externalNavigationError']) is None
            or not isinstance(browser.get('processes'),list) or not browser['processes']):
        raise ValueError('original browser boundary evidence is incomplete or rebound')
    for process in browser['processes']:
        if (not isinstance(process,dict) or not isinstance(process.get('exe'),str) or not Path(process['exe']).is_absolute()
                or not isinstance(process.get('sha256'),str) or re.fullmatch(r'[0-9a-f]{64}',process['sha256']) is None
                or not isinstance(process.get('cmdline'),list) or not process['cmdline']
                or any(not isinstance(x,str) or x.startswith('--no-sandbox') for x in process['cmdline'])):
            raise ValueError('original browser executable or sandbox evidence differs')
    if load(p.parent/'browser.json')!=browser:
        raise ValueError('original browser report differs from the isolation-bound body')
    for name in ('browser.stdout','browser.stderr'):regular(p.parent/name)
    return receipt


def common_custody(prepared_path, process_path, context_path, native=False):
    prepared=validate_prepared(Path(prepared_path))
    process,context=load(process_path),load(context_path);success(process,'common preparation')
    if context.get('protocol') not in ('source-only-common-preparation-execution/1','hosted-common-preparation-execution/1'):
        raise ValueError('actual common preparation context required')
    argv=context.get('argv',[])
    if (len(argv)!=10 or argv[1]!=str(Path(context['cwd'])/'prepare.py')
            or sha(regular(argv[1]))!=COMMON_PREPARER or context.get('sourceSha256')!=COMMON_PREPARER
            or type(context.get('timeoutSeconds')) is not int or context['timeoutSeconds']!=900):
        raise ValueError('actual common source, argv or cwd differs')
    expected=[argv[0],argv[1],'--research',prepared['sources']['research']['root'],
              '--baseline',prepared['sources']['baseline']['root'],'--historical',prepared['sources']['historical']['root'],
              '--out',str(Path(prepared_path).absolute().parent.parent)]
    if argv!=expected:raise ValueError('actual common inputs differ from current preparation')
    hosted=context['protocol']=='hosted-common-preparation-execution/1'
    if native and not hosted:
        raise ValueError('native common preparation was not isolated by hosted execution')
    if context.get('nativeIsolationClaim') is not hosted:
        raise ValueError('common preparation protocol and native claim disagree')
    if hosted:
        isolation=context.get('isolation',{})
        expected=Path(process_path).absolute().parent/'isolation/preparation/receipt.json'
        if (not isinstance(isolation,dict) or isolation.get('path')!=str(expected)
                or record(expected)!=isolation):
            raise ValueError('original common preparation isolation receipt differs')
        original_isolation(expected)
    return prepared,{'prepared':record(prepared_path),'process':record(process_path),'context':record(context_path)}


def prepare_argv(python, inputs):
    return [str(python),str(HERE/'r003f_matrix_campaign.py'),'prepare',*[x for k in
        ('prepared','common-process','common-context','out','receipts','node','pins-sha256') for x in ('--'+k,str(inputs[k]))]]


def source_closure(root,node):
    code='const s=require(process.argv[1]);process.stdout.write(JSON.stringify(s.admitClosure(process.argv[2],process.argv[3])));'
    result=subprocess.run([str(node),'-e',code,str(HERE/'r003f_matrix_support.cjs'),str(root),MATERIALIZATION],
                          capture_output=True,text=True,timeout=30)
    if result.returncode:raise ValueError('actual matrix closure rejected: '+result.stderr)
    return json.loads(result.stdout)


def prepare(inputs):
    receipts=Path(inputs['receipts']);receipts.mkdir(mode=0o700)
    row={'protocol':PROTOCOL,'status':'INCOMPLETE','nativeExecution':'NOT_RUN','inputs':inputs,
         'returncode':None,'timedOut':False,'retentionError':None}
    try:
        row['central']=verify_pins(inputs['pins-sha256'])
        prepared,row['common']=common_custody(inputs['prepared'],inputs['common-process'],inputs['common-context'])
        if sha(HERE/'r003f_matrix_materialize.cjs')!=MATERIALIZER:raise ValueError('reviewed materializer differs')
        argv=[inputs['node'],str(HERE/'r003f_matrix_materialize.cjs'),'--source',prepared['sources']['research']['root'],'--out',inputs['out']]
        row.update(argv=argv,cwd=str(HERE),timeoutSeconds=60,materializerSha256=MATERIALIZER)
        with (receipts/'materializer.stdout').open('xb') as stdout,(receipts/'materializer.stderr').open('xb') as stderr:
            try:
                child=subprocess.run(argv,cwd=HERE,stdout=stdout,stderr=stderr,timeout=60,check=False)
                row['returncode']=child.returncode
            except subprocess.TimeoutExpired:row['timedOut']=True
        success(row,'matrix materializer')
        row['harness']=source_closure(inputs['out'],inputs['node'])
        row['materialization']=record(Path(inputs['out'])/'materialization.json')
        row['status']='PREPARED'
    except (OSError,ValueError,KeyError,TypeError,subprocess.SubprocessError) as error:
        row['error']=str(error)
    save(receipts/'process.json',row)
    return row


def admit(entry_path,expected_pins,*,native=False):
    central=verify_pins(expected_pins)
    entry=load(entry_path);success(entry,'matrix preparation entry')
    if entry.get('protocol')!=ENTRY_PROTOCOL or entry.get('cwd')!=str(HERE) or entry.get('timeoutSeconds')!=180:
        raise ValueError('matrix actual outer entry identity differs')
    child_path=entry.get('process');child=load(child_path);success(child,'matrix materializer')
    inputs=child['inputs']
    if (child.get('protocol')!=PROTOCOL or child.get('status')!='PREPARED' or child.get('nativeExecution')!='NOT_RUN'
            or inputs['pins-sha256']!=expected_pins or entry['argv']!=prepare_argv(entry['argv'][0],inputs)
            or child_path!=str(Path(inputs['receipts'])/'process.json') or child.get('central')!=central
            or child.get('cwd')!=str(HERE) or child.get('timeoutSeconds')!=60 or child.get('materializerSha256')!=MATERIALIZER):
        raise ValueError('matrix outer/child source, argv or custody differs')
    prepared,common=common_custody(inputs['prepared'],inputs['common-process'],inputs['common-context'],native)
    expected=[inputs['node'],str(HERE/'r003f_matrix_materialize.cjs'),'--source',prepared['sources']['research']['root'],'--out',inputs['out']]
    if child.get('argv')!=expected or child.get('common')!=common:raise ValueError('matrix child or current common source differs')
    harness=source_closure(inputs['out'],inputs['node'])
    if child.get('harness')!=harness or child.get('materialization')!=record(Path(inputs['out'])/'materialization.json'):
        raise ValueError('matrix materialization identity differs')
    return {'status':'PASS','protocol':'R003F/matrix-admission/1','root':inputs['out'],
            'entry':record(entry_path),'child':record(child_path),'central':central,'common':common,
            'harness':harness,'runtime':prepared['trees']['r003f']['root'],
            'research':prepared['sources']['research']['root'],'node':inputs['node'],'python':entry['argv'][0]}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('prepare','admit'))
    for name in ('prepared','common-process','common-context','out','receipts','node','pins-sha256','entry','engine','dpr','id','variant'):p.add_argument('--'+name)
    p.add_argument('--native',action='store_true');a=p.parse_args();os.umask(0o077)
    try:
        if a.action=='prepare':
            names=('prepared','common-process','common-context','out','receipts','node','pins-sha256')
            inputs={k:getattr(a,k.replace('-','_')) for k in names}
            if any(v is None for v in inputs.values()):raise ValueError('complete preparation inputs required')
            value=prepare(inputs);code=0 if value['status']=='PREPARED' else 2
        else:
            value=admit(a.entry,a.pins_sha256,native=a.native);code=0
            if any(x is not None for x in (a.engine,a.dpr,a.id,a.variant)):
                value['matrix']=matrix_controls({'id':a.id,'variant':a.variant},'corrected-matrix',['R003F'],a.engine,int(a.dpr))
        print(json.dumps(value));return code
    except (OSError,ValueError,KeyError,TypeError,subprocess.SubprocessError) as error:
        print(json.dumps({'status':'INCOMPLETE','error':str(error)}));return 2



def make_lane(control, admission, out, engine, dpr, node, modules, pngjs, pins_sha256):
    """Canonical matrix-only command; 'all' omits the original variant option."""
    identifier=f'r003f-matrix-{engine}-dpr{dpr}'
    target=Path(out)/identifier;evidence=Path(out)/(identifier+'-driver')
    selection={**control['selection'],'engine':engine,'dpr':dpr}
    admission=admission or {'status':'INCOMPLETE','reason':'matrix preparation is missing'}
    budget=control['budget']
    row={'id':identifier,'workOrder':'R003F','engine':engine,'dpr':dpr,'cwd':admission.get('research',''),
         'env':{'NODE_PATH':str(modules)},'output':str(target),'stdout':str(Path(out)/(identifier+'.stdout')),
         'stderr':str(Path(out)/(identifier+'.stderr')),'timeoutSeconds':budget['laneSeconds'],
         'postCaptureCheckSeconds':budget['intakeSeconds'],'result':{'kind':'r003f-matrix','path':str(target/'summary.json'),
             'driverPath':str(evidence/'driver.json'),'selection':selection,'materialization':MATERIALIZATION},
         'exitStatuses':{'0':'REQUIRES_MATRIX_INTAKE','2':'INCOMPLETE','3':'ISOLATION FAIL','4':'ANDON','86':'ISOLATION FAIL'},
         'dependsOn':[],'stopScopeOnAndon':'R003F','stopAllOnExit':[3,86],'preparation':admission,'argv':[],
         'matrixObservation':{'protocol':'R003F/matrix-observation/1','instrumented':True,'nativeSeconds':budget['nativeSeconds'],
              'overhead':'Host source checks before acquisition and terminal custody afterward; original capture retention unchanged. No added frame listener, pixel copy or per-frame fsync.'}}
    if admission.get('status')=='PASS':
        original=list(map(str,[node,Path(admission['root'])/'tools/qa/r003f_matrix.cjs','--root',admission['runtime'],
              '--out',target,'--engine',engine,'--dpr',dpr,'--id',selection['id'],'--playwright',Path(modules)/'playwright',
              '--pngjs',pngjs,'--materialization-sha256',MATERIALIZATION]))
        if selection['variant']!='all':original+=['--variant',selection['variant']]
        row['matrixObservation']['originalArgv']=original
        row['argv']=[str(node),str(HERE/'r003f_matrix_entry.cjs'),'--entry',admission['entry']['path'],
                     '--pins-sha256',pins_sha256,'--evidence',str(evidence),'--engine',engine,'--dpr',str(dpr),
                     '--id',selection['id'],'--variant',selection['variant'],'--native-seconds',str(budget['nativeSeconds']),'--',*original[1:]]
    return row

if __name__=='__main__':raise SystemExit(main())
