"""Re-execute the three accepted mutations with unchanged actual-source test oracles."""
import argparse, hashlib, json, os, re, subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent/'A01'
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('--node',required=True);a=p.parse_args()
    OUT.mkdir(exist_ok=False)
    source=(ROOT/'index.html').read_bytes();text=source.decode()
    mutations=[
      ('body','stage="body"; wxAttemptState(op,a,"body");','stage="body"; wxAttemptState(op,a,"body"); if(a.timer!=null){clearTimeout(a.timer);a.timer=null;}',
       'R000D weather body is busy at 9999ms and released at 10000ms'),
      ('owner','finally{ finishAttempt(op,a); if(finishRequest(op)) wxBusy=false; }','finally{ finishAttempt(op,a); finishRequest(op); wxBusy=false; }',
       'R0003 weather obsolete error/finally cannot release successor'),
      ('image','a.timer=setTimeout(()=>finish(null,"image timeout"),Math.max(0,a.deadlineAt-_RAFNOW()));','a.timer=null; // MUTANT: Image deadline omitted.',
       'R000D radar image deadline detaches handlers and retained callbacks cannot install')]
    receipt={'sourceSha256':sha(source),'nodeVersion':subprocess.check_output([a.node,'--version'],text=True).strip(),
             'oracleSha256':sha((ROOT/'tests/r000d-weather.test.cjs').read_bytes()),'outerWatchdogSeconds':30,'runs':[],'mutations':[]}
    def run(name,src,pattern=None):
        env=os.environ.copy();env.update(SALAH_WEATHER_SOURCE=str(src),SALAH_CONFIG_SOURCE=str(ROOT/'config.js'))
        cmd=[a.node,'--test','--test-reporter=tap','--test-concurrency=1']
        if pattern:cmd+=['--test-name-pattern',pattern]
        cmd+=[str(ROOT/'tests/r000d-weather.test.cjs')]
        proc=subprocess.run(cmd,env=env,capture_output=True,timeout=30)
        (OUT/(name+'.stdout.tap')).write_bytes(proc.stdout);(OUT/(name+'.stderr.txt')).write_bytes(proc.stderr)
        counts={k:int(v) for k,v in re.findall(r'^# (tests|pass|fail|cancelled|skipped|todo) (\d+)',proc.stdout.decode(),re.M)}
        row=dict(name=name,command=cmd,exitCode=proc.returncode,counts=counts,sourceSha256=sha(src.read_bytes()),stdoutSha256=sha(proc.stdout),stderrSha256=sha(proc.stderr))
        receipt['runs'].append(row);return row,proc.stdout.decode()
    baseline,_=run('healthy-all',ROOT/'index.html')
    assert baseline['counts']['pass']==24 and baseline['counts']['fail']==0
    for name,before,after,witness in mutations:
        assert text.count(before)==1,(name,'source anchor')
        dest=OUT/(name+'-mutant.html');dest.write_text(text.replace(before,after),encoding='utf-8',newline='')
        red,raw=run(name+'-red',dest,re.escape(witness))
        assert red['exitCode']==1 and red['counts']['fail']==1 and red['counts']['cancelled']==0
        assert 'ERR_ASSERTION' in raw and witness in raw and 'SyntaxError' not in raw
        healthy,_=run(name+'-paired-healthy',dest,'control: healthy weather|control: manifest 9999ms|control: ordinary')
        assert healthy['exitCode']==0 and healthy['counts']['pass']==6 and healthy['counts']['fail']==0
        receipt['mutations'].append(dict(name=name,before=before,after=after,witness=witness,originalSha256=sha(source),mutatedSha256=sha(dest.read_bytes()),semanticRed=True))
    receipt['status']='THREE_REACHED_SEMANTIC_MUTANTS_AND_HEALTHY_CONTROLS'
    (OUT/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':receipt['status'],'runs':len(receipt['runs'])}))
if __name__=='__main__':main()
