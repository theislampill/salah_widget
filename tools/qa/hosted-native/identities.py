"""Record acquired source/package/browser identities privately before observation."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('task', 'research', 'baseline', 'historical', 'node', 'python', 'engine'):
        parser.add_argument('--'+key, required=True)
    args = parser.parse_args(); task = Path(args.task)
    sources = {}
    for name in ('research', 'baseline', 'historical'):
        root = getattr(args, name)
        read = lambda *cmd: subprocess.check_output(['git', '-C', root, *cmd], text=True).strip()
        sources[name] = {'commit': read('rev-parse', 'HEAD'), 'tree': read('rev-parse', 'HEAD^{tree}'),
                         'clean': not read('status', '--porcelain')}
        if not sources[name]['clean']: raise ValueError('source checkout is not clean')
    modules = task/'node'/'node_modules'
    runtime = {'node': str(Path(args.node).resolve()), 'python': str(Path(args.python).absolute()),
               'modules': str(modules), 'playwright': str(modules/'playwright'), 'pngjs': str(modules/'pngjs'),
               'engine': args.engine}
    if subprocess.check_output([args.node, '--version'], text=True).strip() != 'v24.14.0':
        raise ValueError('unexpected Node runtime version')
    if not subprocess.check_output([args.python, '--version'], text=True).startswith('Python 3.11.'):
        raise ValueError('unexpected Python runtime version')
    node_packages = {name: json.loads((modules/name/'package.json').read_text())['version']
                     for name in ('playwright', 'playwright-core', 'pngjs')}
    if node_packages != {'playwright':'1.62.1','playwright-core':'1.62.1','pngjs':'7.0.0'}:
        raise ValueError('unexpected Node dependency version')
    wheels = json.loads(subprocess.check_output([args.python, '-m', 'pip', 'list', '--format=json', '--disable-pip-version-check'], text=True))
    expected = {'playwright':'1.57.0','pyee':'13.0.0','greenlet':'3.2.4','typing_extensions':'4.15.0'}
    actual = {x['name'].lower().replace('-','_'):x['version'] for x in wheels}
    if any(actual.get(k) != v for k,v in expected.items()): raise ValueError('unexpected Python dependency version')
    # The lock-file identities and installed driver descriptors are separate from
    # executable digests. All actual binaries used by live controls are recorded too.
    files = {}
    for base in (task/'node-browsers', task/'python-browsers'):
        for path in sorted(base.rglob('*')):
            if path.is_file() and not path.is_symlink() and os.access(path, os.X_OK):
                files[str(path.relative_to(task))] = {'size':path.stat().st_size, 'sha256':digest(path)}
    descriptors = {}
    node_descriptor = modules/'playwright-core'/'browsers.json'
    descriptors['node'] = {'sha256':digest(node_descriptor), 'body':json.loads(node_descriptor.read_text())}
    py_location = subprocess.check_output([args.python, '-c', 'import pathlib,playwright; print(pathlib.Path(playwright.__file__).parent)'], text=True).strip()
    py_descriptor = Path(py_location)/'driver'/'package'/'browsers.json'
    descriptors['python'] = {'sha256':digest(py_descriptor), 'body':json.loads(py_descriptor.read_text())}
    report = {'protocol':'salah-hosted-native-acquisition/1', 'sources':sources, 'runtime':runtime,
              'nodeVersion':subprocess.check_output([args.node,'--version'],text=True).strip(),
              'pythonVersion':subprocess.check_output([args.python,'--version'],text=True).strip(),
              'nodePackages':node_packages, 'pythonPackages':wheels, 'browserDescriptors':descriptors,
              'browserExecutables':files, 'locks':{p:digest(Path(__file__).parent/p)
                for p in ('requirements.txt','node/package.json','node/package-lock.json')}}
    (task/'runtime.json').write_text(json.dumps(runtime,indent=2)+'\n')
    (task/'capture'/'acquisition-identity.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__ == '__main__': main()
