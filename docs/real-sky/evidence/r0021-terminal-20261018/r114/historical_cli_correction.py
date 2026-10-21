from pathlib import Path
import hashlib, json

o = Path(__file__).resolve().parent
build = o / 'reference-tools-r114/build'
plan = json.loads((build / 'PLAN.json').read_bytes())
assert not (build / 'moon_kernel_reference.wasm').exists()
plan['command'] = [plan['command'][0], 'build-exe', '-target', 'wasm32-freestanding',
                   '-O', 'ReleaseFast', '-fno-entry', '-rdynamic', '--import-symbols',
                   '--initial-memory=4194304', '--max-memory=536870912', '-fstrip',
                   '-femit-bin=' + str(build / 'moon_kernel_reference.wasm'),
                   '-cflags', '-O2', '-fno-fast-math', '-ffp-contract=off', '-fno-builtin',
                   '--', str(build / 'moon_kernel_reference.c')]
plan['compilerCliCorrection'] = {'priorExecution': 'reference-r114-execution.json',
    'reason': 'zig cc rejected --export-all before compilation; a no-output -### parser probe also rejected --allow-undefined. Use supported native Zig freestanding exports/imports options, independently listed by build-exe --help.',
    'noNumericalAttempt': True, 'noSourceOrRuleChange': True}
target = build / 'PLAN-r2.json'
assert not target.exists()
target.write_text(json.dumps(plan, indent=2) + '\n', encoding='utf-8')
digest = hashlib.sha256(target.read_bytes()).hexdigest()
wrapper = (o / 'run_reference_r114.py').read_text(encoding='utf-8')
wrapper = wrapper.replace("'PLAN.json'", "'PLAN-r2.json'").replace('d72aad68bc90751ab14b280d4fbab4ff62d1916df040d6cd2624a36262594c36', digest)
wrapper = wrapper.replace("'reference-r114-compile.log'", "'reference-r114b-compile.log'").replace("'reference-r114.log'", "'reference-r114b.log'").replace("'reference-r114-execution.json'", "'reference-r114b-execution.json'")
new_wrapper = o / 'run_reference_r114b.py'
assert not new_wrapper.exists()
new_wrapper.write_text(wrapper, encoding='utf-8', newline='\n')
print(json.dumps({'planSha256': digest, 'wrapperSha256': hashlib.sha256(new_wrapper.read_bytes()).hexdigest(), 'command': plan['command']}))
