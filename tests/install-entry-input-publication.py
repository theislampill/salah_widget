#!/usr/bin/env python3
"""Execute exact fixture-write AST slices under deterministic Windows text I/O.

This is an inert interleaving witness, not a Windows sharing-mode simulation or
an installer/native execution. Original native bytes and exceptions are separate.
"""
import argparse
import ast
import copy
import hashlib
import io
import json
from pathlib import Path
import tempfile
from unittest.mock import patch


def expression_tree(statements):
    return ast.fix_missing_locations(ast.Module(body=copy.deepcopy(statements), type_ignores=[]))


def metadata_writes(tree):
    result = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Expr) or not isinstance(node.value, ast.Call):
            continue
        call = node.value
        if not isinstance(call.func, ast.Attribute) or call.func.attr not in ('write_text', 'write_bytes'):
            continue
        target = call.func.value
        if (isinstance(target, ast.BinOp) and isinstance(target.op, ast.Div)
                and isinstance(target.left, ast.Name) and target.left.id == 'firefox'
                and isinstance(target.right, ast.Constant) and target.right.value == 'extensions.json'):
            result.append(node)
    assert len(result) == 2, 'Exact two maintained metadata creation sites required'
    return result


def ack_publication(tree):
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'invoke_pair')
    condition = ast.dump(ast.parse('ready.exists() and not ack.exists()', mode='eval').body)
    branch = next(node for node in ast.walk(function) if isinstance(node, ast.If)
                  and ast.dump(node.test) == condition)
    end = next(index for index, node in enumerate(branch.body) if isinstance(node, ast.Assign)
               and any(isinstance(target, ast.Subscript) and ast.unparse(target) == "receipt['originalReadyToken']"
                       for target in node.targets))
    start = next(index for index, node in enumerate(branch.body[:end])
                 if (isinstance(node, ast.Expr) and ast.unparse(node.value).startswith('ack.write_text('))
                 or (isinstance(node, ast.Assign) and ast.unparse(node.value).startswith('ack.with_name(')))
    return branch.body[start:end]


def verify(main, support):
    checks = []
    def check(name, passed, detail=None):
        checks.append(dict(name=name, passed=bool(passed), detail=detail))
    with tempfile.TemporaryDirectory(prefix='r16-input-publish-') as directory:
        root = Path(directory)
        def windows_write_text(path, data, encoding=None, errors=None, newline=None):
            # Explicit CRLF translation reproduces Windows Path.write_text's default.
            buffer = io.BytesIO()
            stream = io.TextIOWrapper(buffer, encoding=encoding or 'utf-8',
                                      errors=errors, newline='\r\n' if newline is None else newline)
            count = stream.write(data)
            stream.flush()
            path.write_bytes(buffer.getvalue())
            return count
        for index, statement in enumerate(metadata_writes(ast.parse(main.read_bytes()))):
            firefox = root / ('metadata-' + str(index))
            firefox.mkdir()
            with patch.object(Path, 'write_text', windows_write_text):
                exec(compile(expression_tree([statement]), str(main), 'exec'), dict(firefox=firefox))
            raw = (firefox / 'extensions.json').read_bytes()
            check('metadata-%s-exact-canonical-bytes' % index, raw == b'{"addons":[]}\n',
                  dict(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest()))
            check('metadata-%s-same-json-value' % index, json.loads(raw) == {'addons': []})
        ack = root / 'profile-ack'
        token = '12345\tabcdef0123456789'
        visibility = []
        def interleaved_write_text(path, data, encoding=None, errors=None, newline=None):
            with path.open('w', encoding=encoding or 'utf-8', errors=errors, newline=newline) as stream:
                midpoint = max(1, len(data) // 2)
                stream.write(data[:midpoint])
                stream.flush()
                visibility.append(dict(stage='during-write', ackVisible=ack.exists(),
                                       ackBytes=ack.read_bytes().hex() if ack.exists() else None))
                stream.write(data[midpoint:])
                stream.flush()
                visibility.append(dict(stage='before-close', ackVisible=ack.exists(),
                                       ackBytes=ack.read_bytes().hex() if ack.exists() else None))
            return len(data)
        publication = ack_publication(ast.parse(support.read_bytes()))
        with patch.object(Path, 'write_text', interleaved_write_text):
            exec(compile(expression_tree(publication), str(support), 'exec'), dict(ack=ack, token=token))
        check('ack-invisible-until-writer-closes', len(visibility) == 2 and all(not row['ackVisible'] for row in visibility), visibility)
        check('ack-final-exact-token', ack.read_bytes() == token.encode('utf-8'))
        check('ack-no-leftover-partial', not ack.with_name(ack.name + '.partial').exists())
    return dict(schema='r0016-input-publication-inert.v1',
                scope='Exact fixture AST slices; explicit Windows newline translation and deterministic reader interleaving. No native execution or native sharing-mode proof.',
                mainSha256=hashlib.sha256(main.read_bytes()).hexdigest(),
                supportSha256=hashlib.sha256(support.read_bytes()).hexdigest(), checks=checks,
                passed=sum(row['passed'] for row in checks), failed=sum(not row['passed'] for row in checks))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--main', type=Path, required=True)
    parser.add_argument('--support', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.main, args.support)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(passed=result['passed'], failed=result['failed'])))
    raise SystemExit(int(result['failed'] != 0))
