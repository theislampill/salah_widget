"""Evaluate only the build's receiver-pin and bootstrap expressions, without a build."""
import ast
import base64
import hashlib
import json
import math
from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve()
moon = root / 'moon'
initial = (moon / 'assets/initial-receivers.bin').read_bytes()
compact = (moon / 'assets/initial-compact.bin').read_bytes()
initial_pin = json.loads((moon / 'initial-manifest.json').read_bytes())
encoding = json.loads((moon / 'initial-compact-manifest.json').read_bytes())
sha = lambda data: hashlib.sha256(data).hexdigest()
assert sha(initial) == initial_pin['sha256'] == encoding['parentReceiverSha256']
assert sha(compact) == encoding['sha256']
tree = ast.parse((root / 'tools/build_moon.py').read_bytes())
builds = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'build_moon']
assert len(builds) == 1, 'Unique authored build_moon owner required'
build = builds[0]
profile = next(n.value for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'PROFILE' for t in n.targets))
pin = [n for n in build.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'decoded_pin' for t in n.targets)]
update = [n for n in build.body if isinstance(n, ast.Expr) and isinstance(n.value, ast.Call) and isinstance(n.value.func, ast.Attribute) and isinstance(n.value.func.value, ast.Name) and n.value.func.value.id == 'decoded_pin' and n.value.func.attr == 'update']
boot = [n.value for n in build.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'initial_boot' for t in n.targets)]
assert len(pin) == len(update) == len(boot) == 1, 'Unique authored construction boundaries required'
# These are repository source expressions, not an imported/executed builder.
# No write helpers, build functions, network, worker or terrain inputs are exposed.
scope = {'__builtins__': {}, 'base64': base64, 'json': json, 'math': math,
         'moon': moon, 'initial': initial, 'compact': compact, 'encoding': encoding,
         'initial_pin': initial_pin, 'sha': sha}
exec(compile(ast.Module(body=pin + update, type_ignores=[]), '<receiver-pin>', 'exec'), scope)
text = eval(compile(ast.Expression(boot[0]), '<initial-bootstrap>', 'eval'), scope)
print(json.dumps({'pin': scope['decoded_pin'], 'profile': ast.literal_eval(profile), 'bootstrap': text}))
