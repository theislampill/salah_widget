#!/usr/bin/env python3
"""Selected-route tool custody. Synthetic capability is source control, not native evidence."""
from __future__ import annotations

import hashlib
import argparse
import json
import math
import os
from pathlib import Path
import re
import selectors
import signal
import stat
import subprocess
import sys
import time

MODE = 'bfcache-witness'
PROTOCOL = 'r002f-bfcache-tools/1'
HERE = Path(__file__).resolve().parent
RUNTIME_PATH_KEYS = {'node', 'python', 'modules', 'playwright', 'pngjs'}
RUNTIME_KEYS = RUNTIME_PATH_KEYS | {'engine'}
ENV = {'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8', 'LC_ALL': 'C.UTF-8', 'TZ': 'UTC'}
FIXTURE = 'r002f-bfcache-decode-control'
FIXTURE_SHA256 = '8a827c5b5b787601a0154aaa375cb5eb15b12dc0dd509c9d2a8d1207c9abd783'
FIXTURE_RGB_SHA256 = 'e5f5c7df1e30ec7a5a792461c92295b3ab1a281e2f753b9376c20faa4447bd78'


def need(ok, message):
    if not ok:
        raise ValueError(message)


def selected(campaign):
    need(type(campaign) is dict, 'campaign object required')
    if campaign.get('r002fRoute', 'offscreen') != MODE:
        return False
    need(campaign.get('workOrders') == ['R002F'] and campaign.get('engine') == 'chromium',
         'bfcache requires only Chromium R002F')
    opts = campaign.get('r002f')
    need(type(opts) is dict and opts.get('enabled') is True and type(opts.get('dpr')) is int
         and opts['dpr'] == 1 and type(opts.get('rounds')) is int and opts['rounds'] == 1
         and opts.get('section') == 'all', 'bfcache requires one DPR1 all-section pair')
    for name in ('evidenceRetention', 'r0035Stages', 'r0035Costs', 'r0035Psf'):
        need(campaign.get(name, False) is False, 'incompatible bfcache control: ' + name)
    need(campaign.get('r003fHarness', 'published') == 'published'
         and campaign.get('r003fMatrix') is None and campaign.get('r0040Mode', 'options') == 'options',
         'bfcache cannot combine supplemental routes')
    need(campaign.get('r0035', {'guard': 'default', 'scope': 'all', 'mode': 'both'})
         == {'guard': 'default', 'scope': 'all', 'mode': 'both'}, 'unselected star controls differ')
    return True


def runtime_schema(runtime):
    need(type(runtime) is dict and set(runtime) == RUNTIME_KEYS
         and runtime['engine'] == 'chromium'
         and all(type(runtime[k]) is str and Path(runtime[k]).is_absolute() and '..' not in Path(runtime[k]).parts
                 for k in RUNTIME_PATH_KEYS), 'the unchanged six-key runtime schema with Chromium is required')
    return runtime


def system_path(literal):
    pending = list(literal.parts[1:]); current = Path('/'); links = []
    while pending:
        part = pending.pop(0)
        if part in ('', '.'):
            continue
        if part == '..':
            current = current.parent; continue
        candidate = current / part
        if candidate.is_symlink():
            target = os.readlink(candidate)
            links.append({'path': str(candidate), 'target': target})
            need(len(links) <= 40, 'system symlink loop or excessive resolution')
            parsed = Path(target)
            if parsed.is_absolute(): current = Path('/')
            pending = list(parsed.parts[1:] if parsed.is_absolute() else parsed.parts) + pending
        else:
            candidate.lstat(); current = candidate
    return current, links


def file_record(value, *, system=False, limit=1 << 30):
    literal = Path(value).absolute()
    if system:
        target, symlinks = system_path(literal)
    else:
        need(not any(p.is_symlink() for p in (literal, *literal.parents)), 'symlink path refused')
        target = literal; symlinks = []
    fd = os.open(target, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        before = os.fstat(fd)
        need(stat.S_ISREG(before.st_mode) and 0 <= before.st_size <= limit,
             'bounded regular file required')
        need(system or before.st_nlink == 1, 'aliased file refused')
        h = hashlib.sha256(); count = 0
        while chunk := os.read(fd, 1024 * 1024):
            count += len(chunk); need(count <= limit, 'file grew beyond bound'); h.update(chunk)
        after = os.fstat(fd)
        fields = ('st_dev', 'st_ino', 'st_mode', 'st_nlink', 'st_size', 'st_mtime_ns', 'st_ctime_ns')
        need(all(getattr(before, k) == getattr(after, k) for k in fields)
             and count == before.st_size and os.stat(target, follow_symlinks=False).st_ino == before.st_ino,
             'file changed during descriptor read')
        if system:
            need(system_path(literal) == (target, symlinks), 'system symlink chain changed')
        return {'path': str(literal), 'resolvedPath': str(target), 'bytes': count, 'sha256': h.hexdigest(),
                'device': str(before.st_dev), 'inode': str(before.st_ino), 'links': before.st_nlink,
                'mode': stat.S_IMODE(before.st_mode), 'uid': before.st_uid,
                'mtimeNs': str(before.st_mtime_ns), 'ctimeNs': str(before.st_ctime_ns),
                'system': system, 'symlinks': symlinks}
    finally:
        os.close(fd)


def require_record(row):
    need(type(row) is dict and file_record(row['path'], system=row.get('system', False)) == row,
         'current file identity differs')
    return row


def load(path):
    row = file_record(path, limit=8*1024*1024)
    value = json.loads(Path(row['path']).read_bytes()); require_record(row)
    return value


def save(path, value):
    data = (json.dumps(value, indent=2, allow_nan=False)+'\n').encode()
    need(len(data) <= 8*1024*1024, 'receipt metadata bound exceeded')
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(data); stream.flush(); os.fsync(stream.fileno())
    return file_record(path)


def current_records(value):
    """Every embedded descriptor is current; repeated records must agree, not mask drift."""
    seen = {}
    def visit(item):
        if type(item) is dict:
            if {'path', 'resolvedPath', 'sha256', 'inode', 'mtimeNs', 'ctimeNs', 'system'} <= set(item):
                if item['path'] in seen:
                    need(seen[item['path']] == item, 'conflicting file identity in receipt')
                else:
                    require_record(item); seen[item['path']] = item
            else:
                for child in item.values(): visit(child)
        elif type(item) is list:
            for child in item: visit(child)
    visit(value)
    return len(seen)


def file_tree(root, *, max_files=4096, max_bytes=1024**3):
    root = Path(root).absolute()
    need(root.is_dir() and not any(p.is_symlink() for p in (root, *root.parents)), 'regular package root required')
    rows = {}; total = 0
    for directory, dirs, files in os.walk(root, followlinks=False):
        for name in dirs:
            need(not (Path(directory)/name).is_symlink(), 'symlink directory in package')
        for name in sorted(files):
            path = Path(directory)/name
            need(len(rows) < max_files, 'package population file bound exceeded')
            row = file_record(path); total += row['bytes']; need(total <= max_bytes, 'package byte bound exceeded')
            rows[path.relative_to(root).as_posix()] = row
    return dict(sorted(rows.items()))


def decoder_argv(executable, file):
    return [str(executable), '-v', 'error', '-i', str(file), '-fps_mode', 'passthrough',
            '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-']


def probe_argv(executable, file):
    return [str(executable), '-v', 'error', '-show_entries',
            'stream=index,codec_type,codec_name,width,height,r_frame_rate,avg_frame_rate,time_base:format=format_name,duration',
            '-of', 'json', str(file)]


def admit_metadata(body):
    streams = body.get('streams') if type(body) is dict else None
    need(type(streams) is list and len(streams) == 1 and type(streams[0]) is dict,
         'exactly one original video stream required')
    stream = streams[0]
    want = {'codec_type': 'video', 'codec_name': 'vp8', 'width': 326, 'height': 530,
            'r_frame_rate': '25/1', 'avg_frame_rate': '25/1'}
    need(all(stream.get(k) == v and type(stream.get(k)) is type(v) for k, v in want.items()),
         'actual stream metadata differs from unchanged original arithmetic')
    need(type(stream.get('time_base')) is str and bool(stream['time_base']), 'stream time base missing')
    duration = body.get('format', {}).get('duration')
    try:
        seconds = float(duration)
    except (ValueError, TypeError):
        raise ValueError('stream duration missing')
    need(math.isfinite(seconds) and seconds > 0, 'stream duration invalid')
    return stream


def mapped_files(pid):
    raw=Path('/proc',str(pid),'maps').read_bytes();need(len(raw)<=2*1024**2,'actual process mappings bound exceeded')
    paths=set()
    for line in raw.decode().splitlines():
        match=re.fullmatch(r'[\da-f]+-[\da-f]+\s+\S+\s+[\da-f]+\s+[\da-f]+:[\da-f]+\s+(\d+)\s*(.*)',line)
        need(match is not None,'unrecognized actual file mapping')
        inode,literal=match.groups()
        if inode=='0' or not literal or literal.startswith('['):continue
        literal=re.sub(r'\\([0-7]{3})',lambda m:chr(int(m.group(1),8)),literal)
        need(literal.startswith('/') and not literal.endswith(' (deleted)'),'unresolved actual file mapping')
        paths.add(literal)
    return sorted(paths)


def run_bounded(argv, directory, label, timeout, *, max_stdout=1 << 20, max_stderr=1 << 20, env=None, mapping_rows=None, cwd=None, output_owner=None):
    """Actual child, capped retained streams and group teardown; no inferred success."""
    directory = Path(directory)
    need(directory.is_dir() and not directory.is_symlink(), 'existing private command directory required')
    need(type(label) is str and label and label.replace('-', '').replace('_', '').isalnum(), 'command label')
    need(timeout > 0 and max_stdout > 0 and max_stderr > 0, 'positive process bounds required')
    need(output_owner is None or (type(output_owner) is tuple and len(output_owner) == 2
         and all(type(value) is int and value > 0 for value in output_owner) and os.geteuid() == 0),
         'only a root controller may retain streams as its nonroot caller')
    paths = {key: directory / (label + '.' + key) for key in ('stdout', 'stderr')}
    streams = {}; proc = None; started = time.monotonic(); selector = selectors.DefaultSelector()
    command_cwd=directory if cwd is None else Path(cwd)
    record = {'argv': list(map(str, argv)), 'cwd': str(command_cwd), 'timeoutSeconds': timeout,
              'returncode': None, 'timedOut': False, 'overflow': False, 'complete': False,
              'observedBytes': {'stdout': 0, 'stderr': 0}, 'retainedBytes': {'stdout': 0, 'stderr': 0},
              'maxBytes': {'stdout': max_stdout, 'stderr': max_stderr}, 'signals': []}
    terminated = None; killed = False
    allowed={};seen=set()
    if mapping_rows is not None:
        current_records(mapping_rows);allowed={row['resolvedPath']:row for row in mapping_rows}
        record.update(mappingSnapshots=0,mappedPaths=[],mappingErrors=[],mappingsComplete=False)
    def snapshot():
        if mapping_rows is None:return
        try:
            if proc.poll() is not None:return
            paths=mapped_files(proc.pid)
            # A reaped/terminal child no longer has mappings. This does not
            # excuse an empty live population or the absence of an earlier sample.
            if not paths and proc.poll() is not None:return
            need(paths,'empty actual mapped-file population')
            record['mappingSnapshots']+=1
            for literal in paths:
                resolved=str(system_path(Path(literal))[0]);need(resolved in allowed,'unexpected mapped dependency: '+literal);seen.add(resolved)
        except (FileNotFoundError,ProcessLookupError):pass
        except (OSError,ValueError) as error:
            record['mappingErrors'].append(str(error));record['error']='actual process mapping custody incomplete'
    def group_signal(sig):
        try:
            os.killpg(proc.pid, sig)
            record['signals'].append(signal.Signals(sig).name)
        except ProcessLookupError:
            pass
    try:
        for key, path in paths.items():
            if output_owner is None:
                fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            else:
                # The owned PID-namespace controller must leave even abruptly
                # interrupted prefixes readable by the original private owner.
                old_uid, old_gid = os.geteuid(), os.getegid()
                try:
                    os.setegid(output_owner[1]); os.seteuid(output_owner[0])
                    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
                finally:
                    os.seteuid(old_uid); os.setegid(old_gid)
            streams[key] = os.fdopen(fd, 'wb')
        proc = subprocess.Popen(record['argv'], cwd=command_cwd, env=ENV if env is None else env,
                                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                start_new_session=True)
        record['pid'] = proc.pid
        snapshot()
        for key in ('stdout', 'stderr'):
            pipe = getattr(proc, key); os.set_blocking(pipe.fileno(), False); selector.register(pipe, selectors.EVENT_READ, key)
        while selector.get_map() or proc.poll() is None:
            now = time.monotonic()
            if now - started >= timeout and terminated is None:
                record['timedOut'] = True
            snapshot()
            if (record['timedOut'] or record['overflow'] or record.get('error')) and terminated is None:
                group_signal(signal.SIGTERM); terminated = now
            if terminated is not None and now - terminated >= 2 and not killed:
                group_signal(signal.SIGKILL); killed = True
            for item, _ in selector.select(0.02):
                data = os.read(item.fileobj.fileno(), 65536)
                if not data:
                    selector.unregister(item.fileobj); item.fileobj.close(); continue
                key = item.data; record['observedBytes'][key] += len(data)
                available = max(0, record['maxBytes'][key] - record['retainedBytes'][key])
                kept = data[:available]; streams[key].write(kept); record['retainedBytes'][key] += len(kept)
                if len(kept) != len(data): record['overflow'] = True
        record['returncode'] = proc.wait()
        # A leader can return while descendants still hold the process group.
        try:
            os.killpg(proc.pid, 0); record['groupStopped'] = False
            group_signal(signal.SIGKILL)
        except ProcessLookupError:
            record['groupStopped'] = True
        if mapping_rows is not None:
            record['mappedPaths']=sorted(seen)
            try:
                need(record['mappingSnapshots']>0 and seen and not record['mappingErrors'],'complete actual mapping snapshot absent')
                for resolved in seen:require_record(allowed[resolved])
                record['mappingsComplete']=True
            except (OSError,ValueError) as error:record['error']=str(error)
        record['complete'] = record['returncode'] == 0 and not record['timedOut'] and not record['overflow'] and record['groupStopped'] and not record.get('error')
    except BaseException:
        if proc is not None:
            group_signal(signal.SIGKILL); proc.wait()
        raise
    finally:
        selector.close()
        for stream in streams.values(): stream.flush(); os.fsync(stream.fileno()); stream.close()
        record['elapsedSeconds'] = time.monotonic() - started
    record['streams'] = {key: file_record(path) for key, path in paths.items()}
    return record


def admit_fixture(directory=None):
    root = HERE / 'fixtures' if directory is None else Path(directory)
    manifest = file_record(root / (FIXTURE + '.json'), limit=65536)
    body = json.loads(Path(manifest['path']).read_bytes())
    need(body.get('protocol') == 'r002f-bfcache-decode-fixture/1' and body.get('scope') == 'SOURCE_CONTROL_ONLY'
         and body.get('file') == FIXTURE + '.webm' and body.get('width') == 326
         and body.get('height') == 530 and body.get('frames') == 2 and body.get('fps') == 25
         and body.get('sha256') == FIXTURE_SHA256 and body.get('expectedDecodedBytes') == 1036680
         and body.get('expectedDecodedSha256') == FIXTURE_RGB_SHA256
         and body.get('generatorIsNotHostedRuntimeAuthority') is True, 'synthetic fixture contract differs')
    data = file_record(root / body['file'], limit=65536)
    need(data['sha256'] == FIXTURE_SHA256 and data['bytes'] == body.get('bytes'), 'synthetic fixture bytes differ')
    require_record(manifest)
    return {**body, 'manifestRecord': manifest, 'fileRecord': data}


def run_fixture(ffmpeg, ffprobe, directory, *, execute=run_bounded, mapping_rows=None):
    fixture = admit_fixture(); target = Path(directory); file = fixture['fileRecord']['path']
    options={} if mapping_rows is None else {'mapping_rows':mapping_rows}
    probe = execute(probe_argv(ffprobe, file), target, 'fixture-probe', 20, max_stdout=65536, max_stderr=65536,**options)
    probe_record = save(target/'fixture-probe-process.json', probe)
    need(probe.get('complete') is True and probe.get('returncode') == 0, 'synthetic probe did not complete')
    require_record(probe['streams']['stdout']); require_record(probe['streams']['stderr'])
    metadata = load(probe['streams']['stdout']['path'])
    admit_metadata(metadata)
    decoded = execute(decoder_argv(ffmpeg, file), target, 'fixture-decode', 30,
                      max_stdout=1036681, max_stderr=65536,**options)
    decode_record = save(target/'fixture-decode-process.json', decoded)
    need(decoded.get('complete') is True and decoded.get('returncode') == 0,
         'original decoder argv unsupported or incomplete')
    output = file_record(decoded['streams']['stdout']['path'], limit=1036681)
    require_record(decoded['streams']['stdout']); require_record(decoded['streams']['stderr'])
    need(output['bytes'] == 1036680 and output['sha256'] == FIXTURE_RGB_SHA256,
         'synthetic decoder bytes/count/trailing frame differ')
    if mapping_rows is not None:
        need(probe.get('mappingsComplete') is True and decoded.get('mappingsComplete') is True,
             'source capability actual mapped dependency population incomplete')
    require_record(fixture['manifestRecord']); require_record(fixture['fileRecord'])
    return {'protocol': 'r002f-bfcache-source-capability/1', 'scope': 'SOURCE_CONTROL_ONLY',
            'status': 'COMPLETE', 'fixture': fixture, 'metadata': metadata, 'probe': probe,
            'decode': decoded, 'decoded': output, 'nativeObservation': False,
            'processRecords': {'probe': probe_record, 'decode': decode_record}}


def parse_ldd(text):
    """Resolve only complete ldd lines. The caller separately verifies ELF metadata."""
    found = set()
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if re.fullmatch(r'linux-(?:vdso|gate)\.so\.\d+ \(0x[0-9a-f]+\)', line):
            continue
        match = re.fullmatch(r'(?:\S+ => )?(/\S+) \(0x[0-9a-f]+\)', line)
        need(match is not None, 'missing or unrecognized ELF dependency: ' + line)
        found.add(match.group(1))
    return sorted(found)


def parse_elf(text):
    need('ELF Header:' in text, 'ELF metadata required')
    interpreters = re.findall(r'\[Requesting program interpreter: ([^\]]+)\]', text)
    need(len(interpreters) <= 1, 'ambiguous ELF interpreter')
    interpreter = interpreters[0] if interpreters else None
    need(interpreter is None or (interpreter.startswith('/') and '..' not in Path(interpreter).parts),
         'absolute ELF interpreter required')
    needed = re.findall(r'\(NEEDED\).*Shared library: \[([^\]]+)\]', text)
    need(all(name and '/' not in name and name not in ('.', '..') for name in needed), 'unsafe ELF library name')
    return {'interpreter': interpreter, 'needed': sorted(set(needed))}


def mapping_data(root=Path('/')):
    """Declared dynamic-loader/locale data, not permission for arbitrary mapped code."""
    root=Path(root);names=[root/'etc/ld.so.cache']
    archive=root/'usr/lib/locale/locale-archive'
    if archive.exists():names.append(archive)
    for locale in ('C.utf8','C.UTF-8'):
        folder=root/'usr/lib/locale'/locale
        if folder.exists():
            for directory,dirs,files in os.walk(folder,followlinks=False):
                need(not any((Path(directory)/name).is_symlink() for name in dirs),'unexpected locale directory alias')
                names.extend(Path(directory)/name for name in sorted(files))
    return [file_record(file,system=True) for file in sorted(set(names))]


def elf_closure(executables, directory, *, execute=run_bounded):
    """ldd resolves the transitive loader graph; readelf verifies every resolved object's NEEDED set."""
    commands = []; files = {}; metadata = {}; resolutions = {}; total = 0; started = time.monotonic()
    def command(argv, label):
        need(time.monotonic()-started < 90, 'ELF identity/dependency aggregate ceiling reached')
        got = execute(argv, directory, label, min(10, 90-(time.monotonic()-started)), max_stdout=1024*1024, max_stderr=65536)
        commands.append(got); need(got['complete'], 'ELF resolution process incomplete')
        require_record(got['streams']['stdout']); return Path(got['streams']['stdout']['path']).read_text()
    for index, executable in enumerate(executables):
        paths = parse_ldd(command(['/usr/bin/ldd', executable], 'ldd-'+str(index)))
        need(paths, 'dynamic executable has no resolved dependency population')
        resolutions[executable] = paths
    queue = list(executables) + [p for paths in resolutions.values() for p in paths]
    for literal in dict.fromkeys(queue):
        row = file_record(literal, system=True)
        if row['resolvedPath'] in files:
            # Keep each legitimate literal link chain even when targets coincide.
            files[row['resolvedPath']]['aliases'].append(row); continue
        need(len(files) < 512, 'dependency file ceiling reached'); total += row['bytes']
        need(total <= 1024**3, 'dependency hash input ceiling reached')
        meta = parse_elf(command(['/usr/bin/readelf', '-h', '-l', '-d', '--wide', row['resolvedPath']], 'elf-'+str(len(files))))
        files[row['resolvedPath']] = {'identity': row, 'aliases': []}; metadata[row['resolvedPath']] = meta
    by_name = {Path(p).name for p in queue} | {Path(p).name for p in files}
    for resolved, meta in metadata.items():
        need(set(meta['needed']) <= by_name, 'unresolved transitive ELF library: '+resolved)
        if meta['interpreter']:
            interpreter = file_record(meta['interpreter'], system=True)
            need(interpreter['resolvedPath'] in files, 'ELF interpreter missing from resolved closure')
            files[interpreter['resolvedPath']]['aliases'].append(interpreter)
    return {'protocol': 'r002f-bfcache-elf-closure/1', 'files': files, 'metadata': metadata,
            'resolutions': resolutions, 'bytesHashed': total, 'commands': commands,
            'scope': 'transitive resolved ELF objects; observed native mappings are checked separately'}


def acquired_runtime(task, directory):
    task = Path(task).absolute(); runtime_path = task/'runtime.json'; acquisition_path = task/'capture/acquisition-identity.json'
    runtime = runtime_schema(load(runtime_path)); acquisition = load(acquisition_path); modules = task/'node/node_modules'
    need(acquisition.get('protocol') == 'salah-hosted-native-acquisition/1' and acquisition.get('runtime') == runtime,
         'original acquisition/runtime disagree')
    need(runtime['modules'] == str(modules) and runtime['playwright'] == str(modules/'playwright')
         and runtime['pngjs'] == str(modules/'pngjs'), 'literal task runtime paths differ')
    expected = {'playwright': '1.62.1', 'playwright-core': '1.62.1', 'pngjs': '7.0.0'}
    need(acquisition.get('nodePackages') == expected, 'acquired package versions differ')
    packages = {}
    for name, version in expected.items():
        need(load(modules/name/'package.json')['version'] == version, 'installed package version differs')
        packages[name] = file_tree(modules/name)
    descriptor_path = modules/'playwright-core/browsers.json'; descriptor = load(descriptor_path)
    need(acquisition['browserDescriptors']['node'] == {'sha256': file_record(descriptor_path)['sha256'], 'body': descriptor},
         'acquired browser descriptor differs')
    api = {'lib/coreBundle.js': '9393fa79e1c67c74edc26b610d65a4f7ed73d345a762465cc88340a33a2454ac',
           'types/types.d.ts': '6c688250f2b7061cec3a17ab8797671137b653f8c4e81a6df3190cb112a7579a'}
    for name, digest in api.items():
        need(packages['playwright-core'][name]['sha256'] == digest, 'reviewed Playwright API differs')
    for name in ('node/package.json', 'node/package-lock.json'):
        need(acquisition['locks'][name] == file_record(HERE/name)['sha256'] == file_record(task/name)['sha256'],
             'actual acquired lock differs')
    executable_process = run_bounded([runtime['node'], '-e', 'console.log(require(process.argv[1]).chromium.executablePath())',
                                      runtime['playwright']], directory, 'managed-chromium-path', 10,
                                     env={**ENV, 'PLAYWRIGHT_BROWSERS_PATH': str(task/'node-browsers')})
    need(executable_process['complete'], 'managed executable source query incomplete')
    executable = Path(executable_process['streams']['stdout']['path']).read_text().strip()
    recorder_descriptor = [r for r in descriptor['browsers'] if r['name'] == 'ffmpeg']
    need(len(recorder_descriptor) == 1 and str(recorder_descriptor[0]['revision']) == '1011', 'managed recorder revision differs')
    recorder = str(task/'node-browsers/ffmpeg-1011/ffmpeg-linux'); managed = {}
    for name, literal in (('chromium', executable), ('recorder', recorder)):
        relative = Path(literal).relative_to(task).as_posix(); row = file_record(literal)
        need(acquisition['browserExecutables'].get(relative) == {'size': row['bytes'], 'sha256': row['sha256']},
             'managed executable differs from acquired bytes'); managed[name] = row
    need(managed['recorder']['sha256'] == '460d44f3416005662f528d4b92e7b94ace924e8a0288106d3803b73c56eaadc8',
         'reviewed recorder bytes differ')
    return {'runtime': runtime, 'runtimeRecord': file_record(runtime_path), 'acquisition': file_record(acquisition_path),
            'packages': packages, 'descriptor': file_record(descriptor_path), 'managed': managed,
            'node': file_record(runtime['node'], system=True), 'python': file_record(runtime['python'], system=True),
            'executableQuery': executable_process}


def acquire(task):
    # Selected-only shell call. No browser import beyond a source executablePath query; no browser launch.
    from r002f_bfcache_central import source_identity
    import r002f_bfcache_system as system
    import runner_environment
    task = Path(task).absolute(); campaign_path = HERE/'campaign.json'
    need(selected(load(campaign_path)), 'unselected route must not acquire bfcache tools')
    folder = task/'capture/r002f-bfcache-tools'; need(not folder.exists(), 'tool receipt/output already exists')
    folder.mkdir(mode=0o700); result = {'protocol': PROTOCOL, 'status': 'INCOMPLETE', 'task': str(task),
        'scope': 'SELECTED_ROUTE_HOSTED_TOOL_ACQUISITION', 'nativeObservation': False, 'commands': []}
    started = time.monotonic()
    def deadline(signum, frame): raise TimeoutError('180-second selected tool acquisition ceiling reached')
    previous = signal.signal(signal.SIGALRM, deadline); signal.setitimer(signal.ITIMER_REAL, 180)
    try:
        result['campaign'] = file_record(campaign_path); result['sources'] = source_identity()
        result['runnerEnvironment'] = runner_environment.current(task)
        result['provision'] = system.provision(task, folder, started+180)
        need(result['provision']['status'] == 'COMPLETE', 'actual selected system provision incomplete')
        result['provisionAdmission'] = system.current(result['provision'], task, folder)
        result['acquired'] = acquired_runtime(task, folder)
        literals = {'decoder': '/usr/bin/ffmpeg', 'probe': '/usr/bin/ffprobe', 'xvfb': '/usr/bin/Xvfb',
                    'dpkgQuery': '/usr/bin/dpkg-query', 'ldd': '/usr/bin/ldd', 'readelf': '/usr/bin/readelf'}
        result['tools'] = {name: file_record(literal, system=True) for name, literal in literals.items()}
        package = run_bounded(['/usr/bin/dpkg-query', '-W', '-f=${Package}\t${Status}\t${Version}\t${Architecture}\n',
                               'ffmpeg', 'xvfb', 'binutils', 'libc-bin', 'dpkg'], folder, 'packages', 5)
        result['commands'].append(package); need(package['complete'], 'installed tool package query failed')
        text = Path(package['streams']['stdout']['path']).read_text(); rows = [r.split('\t') for r in text.splitlines()]
        need(len(rows) == 5 and {r[0] for r in rows if len(r) == 4} == {'ffmpeg','xvfb','binutils','libc-bin','dpkg'}
             and all(r[1] == 'install ok installed' and r[2] and r[3] for r in rows), 'installed tool package status differs')
        result['installedPackages'] = rows
        for name in ('decoder', 'probe'):
            version = run_bounded([literals[name], '-version'], folder, name+'-version', 5, max_stdout=65536, max_stderr=65536)
            result['commands'].append(version); need(version['complete'], 'actual tool version query failed')
        result['closure'] = elf_closure([literals['decoder'], literals['probe']], folder)
        result['mappingData'] = mapping_data()
        need(len(result['closure']['files'])+len(result['mappingData'])<=512
             and result['closure']['bytesHashed']+sum(r['bytes'] for r in result['mappingData'])<=1024**3,
             'complete decoder dependency/data ceiling reached')
        mapping_rows=result['mappingData']+[row['identity'] for row in result['closure']['files'].values()]
        result['capability'] = run_fixture(literals['decoder'], literals['probe'], folder,mapping_rows=mapping_rows)
        current_records(result)
        for name, files in result['acquired']['packages'].items():
            need(file_tree(Path(result['acquired']['runtime']['modules'])/name) == files, 'installed package population changed')
        need(source_identity() == result['sources'], 'tool acquisition source changed')
        need(runner_environment.current(task) == result['runnerEnvironment'], 'selected runner environment changed')
        need(system.current(result['provision'], task, folder) == result['provisionAdmission'], 'selected system provision changed')
        result['status'] = 'COMPLETE'
    except Exception as error:
        result['error'] = type(error).__name__+': '+str(error)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0); signal.signal(signal.SIGALRM, previous)
        result['elapsedSeconds'] = time.monotonic()-started
        save(folder/'receipt.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--task', required=True)
    args = parser.parse_args(); result = acquire(args.task)
    print(json.dumps({'protocol': PROTOCOL, 'status': result['status'], 'error': result.get('error')}))
    return 0 if result['status'] == 'COMPLETE' else 2


if __name__ == '__main__': sys.exit(main())
