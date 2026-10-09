"""Harness-only AST-directed repair. No browser/CSP/production change."""
import ast
import re
from pathlib import Path

path = Path(__file__).parent / 'native-consumer-driver.py'
text = path.read_text(encoding='utf-8')
text = text.replace("'origin': origin, 'group': args.group", "'origin': args.origin, 'group': args.group")
text = text.replace('page.wait_for_function(', 'wait_predicate(page, ')
tree = ast.parse(text)
lines = text.splitlines(keepends=True)
starts = [0]
for line in lines:
    starts.append(starts[-1] + len(line))
changes = []
for call in ast.walk(tree):
    if not isinstance(call, ast.Call) or not call.args:
        continue
    is_evaluate = isinstance(call.func, ast.Attribute) and call.func.attr == 'evaluate'
    is_wait = isinstance(call.func, ast.Name) and call.func.id == 'wait_predicate'
    index = 1 if is_wait else 0
    if not (is_evaluate or is_wait) or len(call.args) <= index:
        continue
    arg = call.args[index]
    if isinstance(arg, ast.Constant) and isinstance(arg.value, str) and '=>' not in arg.value:
        start = starts[arg.lineno - 1] + arg.col_offset
        end = starts[arg.end_lineno - 1] + arg.end_col_offset
        changes.append((start, end, repr('() => (' + arg.value + ')')))
for start, end, replacement in sorted(changes, reverse=True):
    text = text[:start] + replacement + text[end:]
# Both alternatives are function predicates; no conditional bare-expression path.
text = text.replace("'document.getElementById(\"code\").value' if button == 'copy' else 'installCmd().cmd'", "'()=>document.getElementById(\"code\").value' if button == 'copy' else '()=>installCmd().cmd'")
ast.parse(text)
assert '.wait_for_function(' not in text
path.write_text(text, encoding='utf-8')
print('PASS harness-only function polling repair:', len(changes), 'literal predicates; CSP unchanged; browser NOT_RUN')
