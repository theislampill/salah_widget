import sys,subprocess,re,json,collections
rev=sys.argv[1]
out=subprocess.run(['git','ls-tree','-r','-l',rev],capture_output=True,text=True,encoding='utf-8').stdout
GEN={'index.html','offline.html','config.js','builder.html','real-sky/native-worker.js','real-sky/native-sky.js','real-sky/native-data.js','real-sky/native-sky.css','moon/moon-worker.js','moon/moon-host.js','moon/assets/initial-compact.bin','moon/initial-compact-manifest.json','moon/BUILD.json'}
def cls(p):
    if p.startswith('v1/'): return 'frozen-v1'
    if p in GEN or p.startswith(('real-sky/core/','real-sky/notices/','moon/file-data/')): return 'generated'
    if p.startswith(('docs/rlgwo-execution/','docs/state-contracts/evidence/','docs/real-sky/evidence/','docs/moon/evidence/','docs/real-sky/archive/','docs/audit/','docs/v1/','plans/','docs/moon/donor/')): return 'retained-historical-evidence'
    if p.startswith(('tests/','moon/tests/')): return 'tests'
    if p.startswith(('tools/','.github/','moon/tools/')): return 'tooling'
    if p.startswith(('vendor/','moon/assets/','presets/')) or p in {'moon/moon_kernel.wasm','moon/asset-manifest.json','moon/initial-manifest.json','moon/initial-source-association.json','real-sky/checkpoint.json'}: return 'vendored-or-data'
    return 'authored-source-or-docs'
c=collections.Counter();s=collections.Counter();ex=collections.defaultdict(list)
for line in out.splitlines():
    meta,path=line.split('\t',1); size=int(meta.split()[3]) if meta.split()[3]!='-' else 0
    k=cls(path);c[k]+=1;s[k]+=size
    if len(ex[k])<400: ex[k].append(path)
for k in sorted(c,key=lambda k:-s[k]): print(f'{k}\t{c[k]}\t{s[k]}\t{s[k]/1e6:.1f}MB')
print('TOTAL',sum(c.values()),sum(s.values()))
auth=[p for p in ex['authored-source-or-docs']]
print('authored sample:',len(auth),auth[:200])
