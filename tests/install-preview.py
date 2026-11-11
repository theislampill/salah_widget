#!/usr/bin/env python3
"""Supplemental R0016 tests of actual Bash helpers and complete script entry.

Linux uses an independent network namespace, seccomp transport denial, a
read-only host filesystem, one writable fixture, command spies and snapshots.
Darwin uses native sandbox-exec with separately proved kernel denial controls.
The result distinguishes bootstrap failures, actual assertion failures, helper
extraction and full entry. Native host qualification requires that host's run.
"""
import argparse, ast, ctypes, ctypes.util, errno, gzip, hashlib, json, os, pathlib
import platform, re, secrets, select, shutil, stat, subprocess, sys, tempfile, time


def digest(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def sandbox_child(command):
    libname = ctypes.util.find_library("seccomp")
    if not libname:
        raise RuntimeError("libseccomp unavailable")
    lib = ctypes.CDLL(libname, use_errno=True)
    lib.seccomp_init.argtypes = [ctypes.c_uint32]
    lib.seccomp_init.restype = ctypes.c_void_p
    lib.seccomp_syscall_resolve_name.argtypes = [ctypes.c_char_p]
    lib.seccomp_syscall_resolve_name.restype = ctypes.c_int
    lib.seccomp_rule_add.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int, ctypes.c_uint]
    lib.seccomp_load.argtypes = [ctypes.c_void_p]
    lib.seccomp_release.argtypes = [ctypes.c_void_p]
    lib.seccomp_notify_fd.argtypes = [ctypes.c_void_p]
    class Data(ctypes.Structure):
        _fields_ = [('nr', ctypes.c_int), ('arch', ctypes.c_uint), ('ip', ctypes.c_ulonglong), ('args', ctypes.c_ulonglong * 6)]
    class Request(ctypes.Structure):
        _fields_ = [('id', ctypes.c_ulonglong), ('pid', ctypes.c_uint), ('flags', ctypes.c_uint), ('data', Data)]
    class Response(ctypes.Structure):
        _fields_ = [('id', ctypes.c_ulonglong), ('val', ctypes.c_longlong), ('error', ctypes.c_int), ('flags', ctypes.c_uint)]
    lib.seccomp_notify_receive.argtypes = [ctypes.c_int, ctypes.POINTER(Request)]
    lib.seccomp_notify_respond.argtypes = [ctypes.c_int, ctypes.POINTER(Response)]
    context = lib.seccomp_init(0x7FFF0000)
    if not context:
        raise RuntimeError("seccomp_init failed")
    names = {}
    try:
        for name in ("socket", "socketpair", "connect", "sendto", "sendmsg", "sendmmsg"):
            number = lib.seccomp_syscall_resolve_name(name.encode("ascii"))
            if number >= 0:
                names[number] = name
                if lib.seccomp_rule_add(context, 0x7FC00000, number, 0):
                    raise RuntimeError("seccomp notification rule failed: " + name)
        if lib.seccomp_load(context):
            raise RuntimeError("seccomp_load failed")
        listener = lib.seccomp_notify_fd(context)
        if listener < 0:
            raise RuntimeError("Independent syscall listener unavailable")
        child = os.fork()
        if child == 0:
            os.close(listener)
            os.execvpe(command[0], command, os.environ)
        while True:
            if select.select([listener], [], [], 0.05)[0]:
                request = Request()
                if lib.seccomp_notify_receive(listener, ctypes.byref(request)) == 0:
                    row = {'pid': request.pid, 'syscall': names.get(request.data.nr, request.data.nr), 'decision': 'DENIED_EPERM'}
                    with open(os.environ['R0016_TRANSPORT_LOG'], 'a', encoding='utf-8') as output:
                        output.write(json.dumps(row) + '\n')
                    response = Response(request.id, 0, -errno.EPERM, 0)
                    if lib.seccomp_notify_respond(listener, ctypes.byref(response)) != 0:
                        raise RuntimeError("Could not deny notified syscall")
            done, raw = os.waitpid(child, os.WNOHANG)
            if done:
                code = os.waitstatus_to_exitcode(raw)
                raise SystemExit(code if code >= 0 else 128 - code)
    finally:
        lib.seccomp_release(context)


def positive_child(source, harness, no_open):
    """Reuse only real normal/NoOpen cases; never run the entire old campaign."""
    tree = ast.parse(pathlib.Path(harness).read_text(encoding="utf-8"), filename=harness)
    prefix = []
    for node in tree.body:
        if isinstance(node, ast.For):
            break
        if (isinstance(node, ast.If) and isinstance(node.test, ast.Compare)
                and isinstance(node.test.left, ast.Name) and node.test.left.id == "__name__"):
            break
        prefix.append(node)
    functions = {n.name for n in prefix if isinstance(n, ast.FunctionDef)}
    if not {"terminal", "fixture", "run_pty"}.issubset(functions):
        raise RuntimeError("Existing normal-harness interface changed")
    if sys.platform == "darwin" and "browser_root" not in functions:
        raise RuntimeError("Native Apple profile-layout adapter absent from existing harness")
    sys.argv = [harness, source]
    namespace = {"__file__": harness, "__name__": "r0016_existing_harness"}
    try:
        exec(compile(ast.Module(body=prefix, type_ignores=[]), harness, "exec"), namespace)
        value = namespace["terminal"]("r0016-no-open" if no_open else "r0016-normal", no_open=no_open)
        print(json.dumps({"pass_": True, "observation": value}))
    except Exception as error:
        print(json.dumps({"pass_": False, "error": str(error)}))
        raise SystemExit(1)


if len(sys.argv) > 1 and sys.argv[1] == "--sandbox-child":
    sandbox_child(sys.argv[2:])
if len(sys.argv) > 1 and sys.argv[1] == "--positive-child":
    positive_child(sys.argv[2], sys.argv[3], sys.argv[4] == "1")
    raise SystemExit(0)

CLI = argparse.ArgumentParser(description=__doc__)
CLI.add_argument("source", type=pathlib.Path, help="Actual install.sh source file")
CLI.add_argument("--bash", default=os.environ.get("SALAH_TEST_BASH", "/bin/bash"),
                 help="Actual native Bash executable; defaults to SALAH_TEST_BASH or /bin/bash")
CLI.add_argument("--out", type=pathlib.Path, help="Existing parent for retained evidence")
CLI.add_argument("--normal-harness", type=pathlib.Path, help="Existing install-entry-bash.py")
CLI.add_argument("--suites", default="all", choices=("all", "bootstrap", "helpers", "entry", "normal", "mutants"))
ARGS = CLI.parse_args()
ORIGINAL = ARGS.source.resolve()
SOURCE_BYTES = ORIGINAL.read_bytes()
SOURCE_SHA = hashlib.sha256(SOURCE_BYTES).hexdigest()
HOST = platform.system()
ROOT = pathlib.Path(tempfile.mkdtemp(prefix="r0016-preview-", dir=ARGS.out)).resolve()
ROOT.chmod(0o700)
FROZEN = ROOT / "source.sh"
FROZEN.write_bytes(SOURCE_BYTES)
HARNESS = (ARGS.normal_harness or ORIGINAL.parent / "tests/install-entry-bash.py").resolve()
RESULTS = []
ACQUISITION = {}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def snapshot(root, held_readers=None):
    rows = []
    for path in sorted(root.rglob("*")):
        info = path.lstat()
        content_hash = None
        if path.is_file() and not path.is_symlink():
            reader = (held_readers or {}).get(path)
            if reader is None:
                content_hash = digest(path)
            else:
                held = os.fstat(reader)
                require((info.st_dev, info.st_ino) == (held.st_dev, held.st_ino),
                        "Installer replaced the unreadable metadata identity")
                os.lseek(reader, 0, os.SEEK_SET)
                value = hashlib.sha256()
                while True:
                    block = os.read(reader, 65536)
                    if not block:
                        break
                    value.update(block)
                content_hash = value.hexdigest()
        rows.append({
            "path": str(path.relative_to(root)), "mode": stat.S_IMODE(info.st_mode),
            "kind": "link" if path.is_symlink() else "directory" if path.is_dir() else "file",
            "sha256": content_hash,
            "link": os.readlink(path) if path.is_symlink() else None,
        })
    return rows


DENIALS = r"""
record() { printf '%s\t%s\n' "$1" "$2" >> "$R0016_EVENTS"; }
deny_effect() { record "$1" "$*"; printf '[fixture] denied effect: %s\n' "$1" >&2; return 97; }
command() {
  if [ "$1" = -v ]; then
    case "$2" in
      google-chrome|google-chrome-stable|chrome|microsoft-edge|microsoft-edge-stable|brave-browser|brave|chromium|chromium-browser|firefox|librewolf) return 1 ;;
    esac
  fi
  builtin command "$@"
}
[() {
  if builtin [ "$#" = 3 ] && builtin [ "$1" = -x ]; then
    case "$2" in /Applications/*) return 1 ;; esac
  fi
  builtin [ "$@"
}
mkdir() { deny_effect mkdir "$@"; }
mktemp() { deny_effect mktemp "$@"; }
rm() { deny_effect remove "$@"; }
cp() { deny_effect copy "$@"; }
mv() { deny_effect move "$@"; }
chmod() { deny_effect chmod "$@"; }
chown() { deny_effect chown "$@"; }
touch() { deny_effect touch "$@"; }
ln() { deny_effect link "$@"; }
tee() { deny_effect write "$@"; }
truncate() { deny_effect truncate "$@"; }
dd() { deny_effect write "$@"; }
unzip() { deny_effect extract "$@"; }
tar() { deny_effect extract "$@"; }
curl() { deny_effect network "$@"; }
wget() { deny_effect network "$@"; }
pbcopy() { deny_effect clipboard "$@"; }
wl-copy() { deny_effect clipboard "$@"; }
xclip() { deny_effect clipboard "$@"; }
xsel() { deny_effect clipboard "$@"; }
open() { deny_effect open "$@"; }
xdg-open() { deny_effect open "$@"; }
printf '%s\t%s\n' "$$" "$R0016_NONCE" >> "$R0016_READY"
"""
READINESS_LINE = 'printf \'%s\\t%s\\n\' "$$" "$R0016_NONCE" >> "$R0016_READY"\n'


def darwin_profile(root):
    """A concrete policy whose enforcement must pass native bootstrap probes."""
    allowed = str(ROOT.resolve())
    if any(character in allowed for character in ('"', "\\", "\n", "\r")):
        raise RuntimeError("Unsupported native sandbox fixture path")
    profile = root / "sandbox.sb"
    profile.write_text(
        '(version 1)\n'
        '(allow default)\n'
        '(deny network*)\n'
        '(deny file-write*)\n'
        '(allow file-write* (subpath "' + allowed + '"))\n'
        '(allow file-write-data (literal "/dev/null") (literal "/dev/tty")\n'
        '  (literal "/dev/ptmx") (regex #"^/dev/ttys[0-9]+$"))\n'
        '(deny process-exec (literal "/usr/bin/open") (literal "/usr/bin/pbcopy")\n'
        '  (literal "/usr/bin/osascript"))\n',
        encoding="utf-8")
    return profile


def acquire_host(root, env):
    """Capture host capability facts separately from all installer subjects."""
    control = root / "host-acquisition"
    control.mkdir(mode=0o700)
    for name in ("home", "tmp"):
        (control / name).mkdir(mode=0o700)
    environment = dict(env, HOME=str(control / "home"), TMPDIR=str(control / "tmp"))
    environment.pop("BASH_ENV", None)
    run = subprocess.run([ARGS.bash, "--version"], env=environment,
                         capture_output=True, text=True, timeout=10)
    (control / "bash-version.stdout.txt").write_text(run.stdout)
    (control / "bash-version.stderr.txt").write_text(run.stderr)
    require(run.returncode == 0 and run.stdout.splitlines(),
            "BOOTSTRAP: selected Bash version could not be acquired")
    data = {"system": HOST, "kernel": platform.release(), "architecture": platform.machine(),
            "pythonExecutable": sys.executable, "pythonVersion": platform.python_version(),
            "bashRequested": ARGS.bash, "bashVersion": run.stdout.splitlines()[0],
            "uid": os.getuid(), "gid": os.getgid(), "fixturePhysicalPath": str(ROOT),
            "nativeMacOSVersion": platform.mac_ver()[0] if HOST == "Darwin" else None,
            "acquisitionRoot": str(control)}
    if HOST == "Darwin":
        sandbox = pathlib.Path("/usr/bin/sandbox-exec")
        require(sandbox.is_file() and os.access(sandbox, os.X_OK),
                "BOOTSTRAP: native /usr/bin/sandbox-exec unavailable; no uncontained fallback")
        data["sandboxExecutable"] = str(sandbox)
        data["sandboxExecutableSha256"] = digest(sandbox)
        manual = next((path for path in (
            pathlib.Path("/usr/share/man/man1/sandbox-exec.1"),
            pathlib.Path("/usr/share/man/man1/sandbox-exec.1.gz"))
            if path.is_file()), None)
        if manual:
            raw = manual.read_bytes()
            text = gzip.decompress(raw) if manual.suffix == ".gz" else raw
            require(len(text) <= 262144, "BOOTSTRAP: unexpectedly large native manual")
            retained = control / "sandbox-exec.native-manual.txt"
            retained.write_bytes(text)
            data["nativeManual"] = {"status": "ACQUIRED", "path": str(manual),
                                    "sha256": hashlib.sha256(raw).hexdigest(),
                                    "retained": str(retained)}
        else:
            data["nativeManual"] = {
                "status": "ACQUISITION_GAP",
                "reason": "Native sandbox-exec manual not found at standard installed paths; runtime controls remain mandatory."}
        data["transportObservation"] = (
            "Native kernel-denial controls plus command events; no independent per-syscall attempt trace.")
    else:
        data["transportObservation"] = "Independent seccomp notification denial and attempt records."
    (control / "acquisition.json").write_text(json.dumps(data, indent=2) + "\n")
    ACQUISITION.update(data)
    return data


def fixture(name, population="known", route="github"):
    root = ROOT / name
    subject, home, temp = root / "subject", root / "subject/home", root / "subject/tmp"
    for path in (root, subject, home, temp):
        path.mkdir(mode=0o700)
    if HOST == "Darwin":
        chrome = home / "Library/Application Support/Google/Chrome/Default"
        firefox = home / "Library/Application Support/Firefox/Profiles"
    else:
        chrome = home / ".config/google-chrome/Default"
        firefox = home / ".mozilla/firefox"
    if population not in ("none", "unknown-only", "malformed-only", "missing-metadata", "unreadable-only", "no-parser-only"):
        chrome.mkdir(parents=True)
    if population in ("legacy", "mixed-legacy"):
        (chrome / "Extensions/hipekcciheckooncpjeljhnekcoolahp").mkdir(parents=True)
    elif population == "installed":
        (chrome / "Extensions/dlaogejjiafeobgofajdlkkhjlignalk").mkdir(parents=True)
    if population not in ("none", "legacy", "installed"):
        unknown = population in ("unknown-only", "malformed-only", "missing-metadata", "mixed-unknown", "unreadable-only", "no-parser-only", "mixed-no-parser")
        profile = firefox / ("r0016-unknown" if unknown else "r0016-known")
        profile.mkdir(parents=True)
        if population != "missing-metadata":
            content = ('{"addons":42}' if population in ("unknown-only", "mixed-unknown")
                       else "{not-json" if population == "malformed-only" else '{"addons":[]}')
            (profile / "extensions.json").write_text(content, encoding="utf-8")
    old = temp / "salah-widget-installer/downloads/v-fixture"
    old.mkdir(parents=True)
    (old / "asset.zip").write_bytes(b"invalid cached ZIP must remain identical\n")
    (old / "asset.xpi").write_bytes(b"invalid cached XPI must remain identical\n")
    (old / "asset-unpacked").mkdir()
    (old / "asset-unpacked/marker").write_bytes(b"keep old unpacked\n")
    retained = home / "salah-widget-install.existing/presets"
    retained.mkdir(parents=True)
    (retained / "preset.json").write_text('{"sentinel":"keep","input":"#local=1"}')
    (root / "bootstrap.sh").write_text(DENIALS, encoding="ascii")
    env = {
        "PATH": "/usr/bin:/bin", "LANG": "en_US.UTF-8" if HOST == "Darwin" else "C.UTF-8",
        "HOME": str(home), "TMPDIR": str(temp), "SALAH_TEST_BASH": ARGS.bash,
        "BASH_ENV": str(root / "bootstrap.sh"), "PYTHONDONTWRITEBYTECODE": "1",
        "DRY_RUN": "1", "NO_OPEN": "0", "SALAH_INSTALL_SOURCE": route,
        "TABLISSNG_REPO": "fixture/repo", "SALAH_WIDGET_PRESET_URL": "https://example.invalid/preset",
        "SALAH_WIDGET_HASH": "lat=24.47&lon=39.61&label=Fixture%20City&method=4",
        "R0016_EVENTS": str(root / "events.txt"), "R0016_READY": str(root / "ready.txt"),
        "R0016_NONCE": secrets.token_hex(16),
        "R0016_TRANSPORT_LOG": str(root / "network.jsonl"),
    }
    return root, subject, env


def sandbox_run(command, root, env, timeout=30):
    if HOST == "Linux":
        for name in ("unshare", "bwrap"):
            if not shutil.which(name):
                raise RuntimeError("Containment prerequisite absent: " + name)
        args = [shutil.which("unshare"), "--user", "--map-root-user", "--net",
                shutil.which("bwrap"), "--die-with-parent", "--ro-bind", "/", "/",
                "--bind", str(ROOT), str(ROOT), "--proc", "/proc", "--dev", "/dev",
                "--chdir", str(root), "--clearenv"]
        if env.get("R0016_UNREADABLE_FILE"):
            args += ["--cap-drop", "ALL"]
        for key, value in env.items():
            args += ["--setenv", key, value]
        args += [sys.executable, str(pathlib.Path(__file__).resolve()), "--sandbox-child"] + command
    elif HOST == "Darwin":
        sandbox = pathlib.Path("/usr/bin/sandbox-exec")
        if not sandbox.exists():
            raise RuntimeError("Native macOS sandbox-exec absent; no unsandboxed fallback")
        args = [str(sandbox), "-f", str(darwin_profile(root))] + command
    else:
        raise RuntimeError("Unsupported native Bash fixture platform: " + HOST)
    run = subprocess.run(args, env=env, capture_output=True, text=True,
                         stdin=subprocess.DEVNULL, start_new_session=True, timeout=timeout)
    (root / "stdout.txt").write_text(run.stdout)
    (root / "stderr.txt").write_text(run.stderr)
    return run


def transport_attempts(root):
    if HOST == "Darwin":
        return None  # Native enforcement is probed; Linux syscall telemetry is not available here.
    path = root / "network.jsonl"
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []


def evidence(root, subject, before, env, run, held_readers=None):
    events = (root / "events.txt").read_text().splitlines() if (root / "events.txt").exists() else []
    ready_path = pathlib.Path(env["R0016_READY"])
    ready = [line.split("\t") for line in ready_path.read_text().splitlines()] if ready_path.exists() else []
    valid = bool(ready) and all(len(row) == 2 and row[0].isdigit()
                               and row[1] == env["R0016_NONCE"] for row in ready)
    processes = sorted({row[0] for row in ready if len(row) == 2 and row[0].isdigit()})
    after = snapshot(subject, held_readers)
    (root / "snapshot-before.json").write_text(json.dumps(before, indent=2))
    (root / "snapshot-after.json").write_text(json.dumps(after, indent=2))
    return {"exit": run.returncode, "bootstrapReady": valid, "bootstrapProcesses": processes,
            "events": events, "transportAttempts": transport_attempts(root),
            "snapshotUnchanged": before == after, "fixture": str(root),
            "stdout": str(root / "stdout.txt"), "stderr": str(root / "stderr.txt")}


def no_effects(value):
    require(value["bootstrapReady"], "BOOTSTRAP: pre-entry denials did not load")
    require(not value["events"], "Installer reached forbidden effects: " + repr(value["events"]))
    require(not value["transportAttempts"], "Installer attempted transport: " + repr(value["transportAttempts"]))
    require(value["snapshotUnchanged"], "Installer changed subject names/modes/bytes/links")


def darwin_denial_readback(root, process_id, env):
    """Acquire only native denial messages attributable to this owned probe PID."""
    log = pathlib.Path("/usr/bin/log")
    host_control = root / "native-log-control"
    for path in (host_control, host_control / "home", host_control / "tmp"):
        path.mkdir(mode=0o700, exist_ok=True)
    host_env = dict(env, HOME=str(host_control / "home"), TMPDIR=str(host_control / "tmp"))
    host_env.pop("BASH_ENV", None)
    result = {"status": "ACQUISITION_GAP", "processId": process_id, "matches": [],
              "scope": "targeted native denial readback; not a complete process-tree syscall trace",
              "hostControlRoot": str(host_control)}
    if not log.is_file():
        result["reason"] = "Native /usr/bin/log unavailable"
    else:
        predicate = ('subsystem == "com.apple.sandbox.reporting" OR process == "sandboxd" OR '
                     '(eventMessage CONTAINS[c] "Sandbox:" AND eventMessage CONTAINS[c] "network")')
        command = [str(log), "show", "--style", "json", "--last", "10s", "--predicate", predicate]
        result["command"] = command
        attempts = []
        for attempt in range(2):
            try:
                run = subprocess.run(command, env=host_env, capture_output=True, text=True, timeout=8)
                attempts.append({"exit": run.returncode, "stdoutBytes": len(run.stdout.encode()),
                                 "stderr": run.stderr[:2000]})
                if run.returncode:
                    result["reason"] = "Native log readback refused or unavailable"
                    break
                if len(run.stdout) > 4 * 1024 * 1024:
                    result["reason"] = "Bounded native log readback exceeded 4 MiB"
                    break
                rows = json.loads(run.stdout)
                if not isinstance(rows, list):
                    raise ValueError("Expected native JSON event array")
                for row in rows:
                    message = row.get("eventMessage", "") if isinstance(row, dict) else ""
                    if not isinstance(message, str):
                        continue
                    if (re.search(r"(?<!\d)" + str(process_id) + r"(?!\d)", message)
                            and re.search(r"deny.*network|network.*deny|network-outbound", message, re.I)):
                        result["matches"].append({key: row.get(key) for key in
                                                  ("timestamp", "processID", "processImagePath", "eventMessage")})
                if result["matches"]:
                    result["status"] = "OBSERVED"
                    break
                result["reason"] = "No attributable network-denial report found within the bounded native readback"
            except (OSError, subprocess.TimeoutExpired, ValueError) as error:
                result["reason"] = "Native log acquisition failed: " + str(error)
                break
            if attempt == 0:
                time.sleep(0.25)
        result["attempts"] = attempts
    (root / "native-denial-readback.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def check(name, kind, body):
    try:
        RESULTS.append({"case": name, "kind": kind, "pass_": True,
                        "classification": "PASS", "observation": body()})
    except Exception as error:
        blocked = isinstance(error, (RuntimeError, subprocess.TimeoutExpired, FileNotFoundError)) or str(error).startswith("BOOTSTRAP:")
        RESULTS.append({"case": name, "kind": kind, "pass_": False,
                        "classification": "BOOTSTRAP_BLOCKED" if blocked else "PRODUCT_ASSERTION_FAILED",
                        "error": str(error)})


def bootstrap():
    root, subject, env = fixture("containment-control", "none")
    acquisition = acquire_host(root, env)
    outside = pathlib.Path(tempfile.mkdtemp(prefix="r0016-outside-control-", dir=ROOT.parent)).resolve()
    outside.chmod(0o700)
    (outside / "sentinel").write_text("host-created outside-fixture control must remain unchanged")
    outside_before = snapshot(outside)
    kernel = root / "kernel-probe"
    kernel.mkdir(mode=0o700)
    kernel_env = dict(env, R0016_TRANSPORT_LOG=str(kernel / "network.jsonl"))
    probe = r"""
import errno,json,os,pathlib,socket,sys
result={"processId":os.getpid(),"outsideWrites":[],"transports":[]}
pathlib.Path(sys.argv[2]).write_text("allowed control write")
result["insideWriteAllowed"]=pathlib.Path(sys.argv[2]).read_text()=="allowed control write"
for name in ("new-file","sentinel"):
 path=pathlib.Path(sys.argv[1])/name
 try:
  path.write_text("must be denied");row={"name":name,"denied":False}
 except OSError as e:
  row={"name":name,"denied":e.errno in (errno.EROFS,errno.EACCES,errno.EPERM),"errno":e.errno}
 result["outsideWrites"].append(row)
for label,kind in (("TCP",socket.SOCK_STREAM),("UDP",socket.SOCK_DGRAM)):
 s=None
 try:
  s=socket.socket(socket.AF_INET,kind)
  if label=="TCP":s.connect(("127.0.0.1",9))
  else:s.sendto(b"r0016-contained-negative-control",("127.0.0.1",9))
  row={"transport":label,"denied":False}
 except OSError as e:
  row={"transport":label,"denied":e.errno in (errno.EPERM,errno.EACCES),"errno":e.errno}
 finally:
  if s is not None:s.close()
 result["transports"].append(row)
print(json.dumps(result))
"""
    command = [ARGS.bash, "--noprofile", "--norc", "-c", 'exec "$@"', "r0016-descendant-probe",
               sys.executable, "-c", probe, str(outside), str(kernel / "allowed-write")]
    run = sandbox_run(command, kernel, kernel_env)
    require(run.returncode == 0, "BOOTSTRAP: containment probe failed: " + run.stderr)
    observed = json.loads(run.stdout)
    require(observed.get("insideWriteAllowed") and
            all(row["denied"] for row in observed.get("outsideWrites", [])) and
            len(observed.get("outsideWrites", [])) == 2 and
            all(row["denied"] for row in observed.get("transports", [])) and
            len(observed.get("transports", [])) == 2,
            "BOOTSTRAP: independent denial not established: " + repr(observed))
    require(snapshot(outside) == outside_before, "BOOTSTRAP: outside write unexpectedly succeeded")
    if HOST == 'Linux':
        require(len(transport_attempts(kernel)) >= 2, "BOOTSTRAP: independent syscall denials were not recorded")
        observed["nativeDenialReadback"] = {"status": "NOT_APPLICABLE_LINUX"}
    else:
        observed["nativeDenialReadback"] = darwin_denial_readback(kernel, observed["processId"], env)
        terminal = root / "terminal-probe"
        terminal.mkdir(mode=0o700)
        terminal_probe = r"""
import json,os,pty
pid,fd=pty.fork()
if pid==0:
 try:
  terminal=os.open("/dev/tty",os.O_RDWR)
  os.write(terminal,b"native terminal control\n")
  os.close(terminal)
  os._exit(0)
 except OSError:
  os._exit(77)
done,status=os.waitpid(pid,0)
os.close(fd)
code=os.waitstatus_to_exitcode(status)
print(json.dumps({"controllingTerminalAllowed":code==0,"childExit":code}))
"""
        terminal_run = sandbox_run([sys.executable, "-c", terminal_probe], terminal, env)
        require(terminal_run.returncode == 0, "BOOTSTRAP: native terminal capability probe failed: " + terminal_run.stderr)
        terminal_observed = json.loads(terminal_run.stdout)
        require(terminal_observed.get("controllingTerminalAllowed"),
                "BOOTSTRAP: native policy did not permit owned terminal I/O")
        observed["terminalControl"] = terminal_observed
    command_root = root / "command-probe"
    command_root.mkdir(mode=0o700)
    command_env = dict(env, R0016_EVENTS=str(command_root / "events.txt"),
                       R0016_READY=str(command_root / "ready.txt"),
                       R0016_TRANSPORT_LOG=str(command_root / "network.jsonl"))
    before = snapshot(subject)
    run = sandbox_run([ARGS.bash, "--noprofile", "--norc", "-c",
                       'mkdir "$HOME/denied"; [ "$?" -eq 97 ]'], command_root, command_env)
    require(run.returncode == 0, "BOOTSTRAP: command denial control failed")
    command_observed = evidence(command_root, subject, before, command_env, run)
    require(command_observed["bootstrapReady"] and command_observed["events"]
            and command_observed["snapshotUnchanged"] and not (subject / "home/denied").exists(),
            "BOOTSTRAP: command denial lacks readiness/event/post-state controls")
    negatives = []
    require(DENIALS.count(READINESS_LINE) == 1, "BOOTSTRAP: readiness marker drift")
    for mode in ("missing", "wrong"):
        control, controlled_subject, control_env = fixture("readiness-" + mode, "none")
        replacement = "" if mode == "missing" else READINESS_LINE.replace('"$R0016_NONCE"', '"wrong-nonce"')
        pathlib.Path(control_env["BASH_ENV"]).write_text(DENIALS.replace(READINESS_LINE, replacement, 1))
        before = snapshot(controlled_subject)
        run = sandbox_run([ARGS.bash, "--noprofile", "--norc", "-c", ":"], control, control_env)
        value = evidence(control, controlled_subject, before, control_env, run)
        require(run.returncode == 0 and value["snapshotUnchanged"] and not value["events"]
                and not value["transportAttempts"], "BOOTSTRAP: readiness discriminator had unrelated failure")
        try:
            no_effects(value)
        except AssertionError as error:
            require(str(error).startswith("BOOTSTRAP:"), "BOOTSTRAP: wrong readiness discriminator classification")
            negatives.append({"mode": mode, "detected": True, "qualification": "BOOTSTRAP_BLOCKED",
                              "fixture": str(control)})
        else:
            raise RuntimeError("Missing/wrong readiness nonce was accepted")
    observed.update(platform=HOST, commandDenialObserved=True, readinessNegativeControls=negatives,
                    outsideControl=str(outside), hostAcquisition=acquisition)
    (root / "bootstrap-observation.json").write_text(json.dumps(observed, indent=2) + "\n")
    return observed


def preview(name, source=FROZEN, population="known", route="github", expected_failure=False,
            missing_preset=False, invalid=False, malformed_boolean=False, arguments=None,
            pipe=False):
    root, subject, env = fixture(name, population, route)
    if missing_preset:
        env["SALAH_WIDGET_PRESET_URL"] = ""
    if invalid:
        env["SALAH_INSTALL_SOURCE"] = "invalid"
    if malformed_boolean:
        env["DRY_RUN"] = "invalid"
    if population in ("no-parser-only", "mixed-no-parser"):
        # The external parser lookup is the sole adapted boundary. The actual
        # fallback detector and complete preview caller still execute.
        bootstrap = pathlib.Path(env["BASH_ENV"])
        text = bootstrap.read_text()
        anchor = '    case "$2" in\n'
        require(text.count(anchor) == 1, "BOOTSTRAP: parser lookup anchor drift")
        bootstrap.write_text(text.replace(anchor, anchor + '      python3) return 1 ;;\n', 1))
    held_readers = {}
    locked = None
    if population == "unreadable-only":
        metadata = list(subject.rglob("extensions.json"))
        require(len(metadata) == 1, "BOOTSTRAP: unreadable metadata fixture is ambiguous")
        locked = metadata[0]
        descriptor = os.open(locked, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        held_readers[locked] = descriptor
        os.fchmod(descriptor, 0)
        env["R0016_UNREADABLE_FILE"] = str(locked)
        env["R0016_READ_REFUSAL"] = str(root / "read-refusal.txt")
        with pathlib.Path(env["BASH_ENV"]).open("a") as stream:
            stream.write('\nif ( : < "$R0016_UNREADABLE_FILE" ) 2>/dev/null; then exit 86; fi\n'
                         'printf "%s\\n" "$R0016_NONCE" > "$R0016_READ_REFUSAL"\n')
    if pipe:
        command = [ARGS.bash, "--noprofile", "--norc", "-c",
                   'set -o pipefail; cat -- "$1" | "$2" --noprofile --norc -s',
                   "r0016-pipe", str(source), ARGS.bash]
    else:
        command = [ARGS.bash, "--noprofile", "--norc", str(source)] + (arguments or [])
    try:
        before = snapshot(subject, held_readers)
        run = sandbox_run(command, root, env)
        observed = evidence(root, subject, before, env, run, held_readers)
        if locked:
            marker = pathlib.Path(env["R0016_READ_REFUSAL"])
            require(marker.exists() and marker.read_text().strip() == env["R0016_NONCE"],
                    "BOOTSTRAP: actual contained process could read the mode000 metadata")
            observed["unreadableMetadata"] = {"path": str(locked), "readRefusedBeforeSource": True,
                "snapshotReader": "parent-held read-only descriptor; not inherited by subject",
                "modeDuringSource": "000", "harnessRestoredModeAfterSource": "600"}
    finally:
        # The parent retains the original owned inode, never chmods a path the
        # subject could replace, and restores readability only after it exits so
        # evidence collection does not require privileged traversal.
        for descriptor in held_readers.values():
            os.fchmod(descriptor, 0o600)
            os.close(descriptor)
    if pipe:
        require(len(observed["bootstrapProcesses"]) >= 2,
                "BOOTSTRAP: complete pipe lacked outer and installer Bash readiness")
    direct_pid = re.search(r"__R0016_DIRECT_TRANSPORT_PID__(\d+)", run.stderr)
    if HOST == "Darwin" and direct_pid:
        native = darwin_denial_readback(root, int(direct_pid[1]), env)
        observed["targetedNativeTransportEvidence"] = native
        if native["status"] != "OBSERVED":
            (root / "observation.json").write_text(json.dumps(observed, indent=2))
            raise RuntimeError("Native direct-transport attempt telemetry unavailable; no egress is insufficient")
        observed["transportAttempts"] = native["matches"]
    (root / "observation.json").write_text(json.dumps(observed, indent=2))
    no_effects(observed)
    text = run.stdout + run.stderr
    require((run.returncode != 0) == expected_failure, "Wrong preview/refusal exit: " + text)
    require(not re.search(r"Press Enter|Select target numbers|Choose \[1/2\]", text), "Preview requested terminal input")
    require(not re.search(r"\[OK\].*Copied|Validated manual-install files retained|Staging directory:", text),
            "Preview claimed copied or staged artifact")
    if not expected_failure:
        require("Preview only" in text and "no changes made" in text, "Missing honest preview completion")
        require("replaces your current TablissNG dashboard" in text, "Missing replacement warning")
        if route == "ask" and population != "installed":
            require("source unresolved" in text.lower(), "Preview silently resolved ask source")
        if route == "github" and population != "installed":
            require("unresolved" in text.lower(), "Preview silently resolved release/path")
    else:
        require("Preview only; no changes made" not in text, "Refused preview claimed successful plan")
    if missing_preset:
        require("No preset URL configured" in text, "Explicit empty preset silently replaced")
    if population in ("mixed-unknown", "mixed-no-parser"):
        require(not re.search(r"Would prepare[^\n]*r0016-unknown", text), "Unknown target became eligible plan")
        require("Would prepare Google Chrome" in text, "Held target suppressed eligible peer")
    if population in ("unknown-only", "malformed-only", "missing-metadata", "mixed-unknown", "unreadable-only", "no-parser-only", "mixed-no-parser"):
        require(re.search(r"unknown|held", text, flags=re.I), "Unknown discovery lacks explicit held/unknown diagnosis")
        require(not re.search(r"Traceback|TypeError|JSONDecodeError", text), "Parser crash substituted for an explicit held target")
        require(not re.search(r"Would prepare[^\n]*r0016-unknown", text), "Unknown discovery produced an eligible plan")
    observed["entryScope"] = "complete source piped to native Bash" if pipe else "complete source file in native Bash"
    return observed


def interrupted_preview(name, mode):
    """Deliver a real failure/signal after the actual EXIT/INT/TERM traps exist."""
    root, subject, env = fixture(name)
    env["R0016_INTERRUPT_MODE"] = mode
    env["R0016_INTERRUPT_RECEIPT"] = str(root / "interrupt-boundary.txt")
    with pathlib.Path(env["BASH_ENV"]).open("a") as stream:
        stream.write(r'''
r0016_interrupt_boundary() {
  if builtin [ "$1" = detect_targets ]; then
    builtin trap - DEBUG
    { printf '%s\t%s\n' "$$" "$R0016_NONCE"; builtin trap -p EXIT INT TERM; } > "$R0016_INTERRUPT_RECEIPT"
    case "$R0016_INTERRUPT_MODE" in
      failure) exit 97 ;;
      INT|TERM) builtin kill -s "$R0016_INTERRUPT_MODE" "$$" ;;
      *) exit 98 ;;
    esac
  fi
}
trap 'r0016_interrupt_boundary "$BASH_COMMAND"' DEBUG
''')
    before = snapshot(subject)
    run = sandbox_run([ARGS.bash, "--noprofile", "--norc", str(FROZEN)], root, env)
    observed = evidence(root, subject, before, env, run)
    boundary = pathlib.Path(env["R0016_INTERRUPT_RECEIPT"])
    require(boundary.exists(), "BOOTSTRAP: actual post-trap interruption boundary was not reached")
    lines = boundary.read_text().splitlines()
    require(lines and lines[0].split("\t")[1:] == [env["R0016_NONCE"]], "BOOTSTRAP: interruption nonce differs")
    traps = "\n".join(lines[1:])
    require("finish_installer" in traps and "exit 130" in traps and "exit 143" in traps,
            "BOOTSTRAP: actual source exit/signal traps were not installed")
    no_effects(observed)
    require(run.returncode == {"failure": 97, "INT": 130, "TERM": 143}[mode],
            "Actual interrupted preview used the wrong exit status")
    require("Preview only; no changes made" not in run.stdout and "[OK]" not in run.stdout,
            "Interrupted preview claimed completed installation or preview")
    observed.update(interruption=mode, sourceTraps=traps, entryScope="complete actual source, interrupted after trap registration")
    (root / "observation.json").write_text(json.dumps(observed, indent=2))
    return observed


HELPERS = [
    ("initialize", "initialize_staging", "failure"),
    ("metadata", "select_asset chromium", "failure"),
    ("cached-download", "download_tablissng_asset chromium", "failure"),
    ("validate", 'validate_asset "$DOWNLOAD_ROOT/v-fixture/asset.zip"', "failure"),
    ("cached-extract", 'expand_chromium_asset "$DOWNLOAD_ROOT/v-fixture/asset.zip"', "failure"),
    ("retain", 'retain_asset "$DOWNLOAD_ROOT/v-fixture/asset.zip"', "failure"),
    ("cached-preset", "download_preset", "failure"),
    ("copy-false", 'copy_text "fixture"', "failure"),
    ("open", 'open_url "" "https://example.invalid/manual"', "diagnostic"),
    ("install-ask", 'install_tablissng chromium Fixture "" "https://example.invalid/store" "chrome://extensions/"', "failure"),
    ("import", 'show_import_instructions Fixture profile "" "chrome://newtab/" "$PRESET_ROOT/salah-widget.tablissng.json"', "failure"),
    ("cleanup", "cleanup_staging", "empty-success"),
]


def helper(name, call, contract, source=FROZEN):
    root, subject, env = fixture("helper-" + name, "known", "ask")
    work, bundle = subject / "current-work", subject / "current-bundle"
    for path in (work, bundle, work / "downloads", work / "downloads/v-fixture", bundle / "presets"):
        path.mkdir(mode=0o700)
    (work / "downloads/v-fixture/asset.zip").write_bytes(b"malformed existing archive")
    (bundle / "presets/salah-widget.tablissng.json").write_bytes(b"malformed existing preset")
    text = pathlib.Path(source).read_text(encoding="utf-8")
    marker = "printf '\\nSalah Widget Installer\\n\\n'"
    if text.count(marker) != 1:
        raise RuntimeError("Helper extraction boundary changed")
    env.update(R0016_WORK=str(work), R0016_BUNDLE=str(bundle), R0016_RETURN=str(root / "return.txt"))
    driver = root / "helper.sh"
    driver.write_text(text[:text.index(marker)] + r"""
WORK_ROOT="$R0016_WORK"; BUNDLE_ROOT="$R0016_BUNDLE"
WORK_ID="$(path_identity "$WORK_ROOT")"; BUNDLE_ID="$(path_identity "$BUNDLE_ROOT")"
DOWNLOAD_ROOT="$WORK_ROOT/downloads"; PRESET_ROOT="$BUNDLE_ROOT/presets"
status=0
""" + call + r""" > "$R0016_RETURN" || status=$?
printf '__R0016_STATUS__%s\n' "$status"
""")
    before = snapshot(subject)
    run = sandbox_run([ARGS.bash, "--noprofile", "--norc", str(driver)], root, env)
    observed = evidence(root, subject, before, env, run)
    returned = (root / "return.txt").read_text() if (root / "return.txt").exists() else None
    match = re.search(r"__R0016_STATUS__(\d+)", run.stdout)
    observed.update(returned=returned, helperStatus=int(match[1]) if match else None)
    (root / "observation.json").write_text(json.dumps(observed, indent=2))
    no_effects(observed)
    require(run.returncode == 0 and match is not None, "Helper probe did not complete: " + run.stderr)
    if contract == "failure":
        require(observed["helperStatus"] != 0, "Suppressed helper reported success")
        require(returned == "", "Suppressed helper returned success-stream value: " + repr(returned))
    elif contract == "empty-success":
        require(observed["helperStatus"] == 0 and returned == "", "Suppressed cleanup was not empty no-op")
    else:
        require(observed["helperStatus"] == 0 and "Would open" in returned, "Suppressed open diagnostic missing")
    return observed


def normal(name, source=FROZEN, no_open=False):
    if HOST not in ("Linux", "Darwin"):
        raise RuntimeError("Actual native Bash platform adapter unavailable")
    if not HARNESS.is_file():
        raise RuntimeError("Existing normal entry harness absent: " + str(HARNESS))
    root, subject, env = fixture(name, "none")
    workspace = root / "normal-work"
    workspace.mkdir(mode=0o700)
    env["TMPDIR"] = str(workspace)
    env.pop("BASH_ENV", None)
    run = sandbox_run([sys.executable, str(pathlib.Path(__file__).resolve()), "--positive-child",
                       str(source), str(HARNESS), "1" if no_open else "0"], root, env, timeout=60)
    try:
        parsed = json.loads(run.stdout)
    except ValueError:
        raise RuntimeError("Normal harness did not return JSON: " + run.stderr + run.stdout)
    attempts = transport_attempts(root)
    if attempts is not None:
        require(all(row['decision'] == 'DENIED_EPERM' for row in attempts), "Normal transport escaped containment")
    require(run.returncode == 0 and parsed.get("pass_"), "Actual normal/NoOpen failed: " + repr(parsed))
    return {"reusedHarness": str(HARNESS), "harnessSha256": digest(HARNESS),
            "nativeScope": HOST + " contained real pipe/PTY caller", "observation": parsed["observation"],
            "deniedTransportAttempts": attempts}


def mutation(name, old, new, mode, selected_helper=None, expected_boundary=None):
    text = SOURCE_BYTES.decode("utf-8")
    if text.count(old) != 1:
        raise RuntimeError("Mutation anchor drift: " + name)
    path = ROOT / ("mutant-" + name + ".sh")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    syntax = subprocess.run([ARGS.bash, "-n", str(path)], capture_output=True, text=True)
    require(syntax.returncode == 0, "BOOTSTRAP: mutant syntax failed: " + syntax.stderr)
    try:
        if mode == "entry":
            preview("mutant-" + name, source=path)
        else:
            helper("mutant-" + name, selected_helper[0], selected_helper[1], path)
    except AssertionError as error:
        require(not str(error).startswith("BOOTSTRAP:"), "BOOTSTRAP: mutant only failed startup")
        reason = str(error)
    else:
        raise AssertionError("Mutant survived its actual effect/result oracle")
    if expected_boundary is not None:
        require(expected_boundary in reason, "Mutant failed outside its required effect boundary: " + reason)
    positive = normal("mutant-positive-" + name, source=path, no_open=True)
    return {"syntaxExit": 0, "detected": True, "reason": reason,
            "mutantSha256": digest(path), "normalPositive": positive}


try:
    boot = bootstrap()
except Exception as error:
    RESULTS.append({"case": "pre-entry independent containment", "kind": "bootstrap",
                    "pass_": False, "classification": "BOOTSTRAP_BLOCKED", "error": str(error)})
else:
    RESULTS.append({"case": "pre-entry independent containment", "kind": "bootstrap",
                    "pass_": True, "classification": "PASS", "observation": boot})
    if ARGS.suites in ("all", "helpers"):
        for name, call, contract in HELPERS:
            check("direct helper " + name, "helper", lambda n=name, c=call, r=contract: helper(n, c, r))
    if ARGS.suites in ("all", "entry"):
        for route in ("github", "store", "ask"):
            check("whole-entry " + route, "entry", lambda r=route: preview("entry-" + r, route=r))
        check("whole-entry advertised pipe", "entry", lambda: preview("entry-pipe", pipe=True))
        for population in ("installed", "mixed-legacy", "mixed-unknown"):
            check("whole-entry " + population, "interface" if population == "mixed-unknown" else "entry",
                  lambda p=population: preview("entry-" + p, population=p))
        for population in ("none", "legacy", "unknown-only", "malformed-only", "missing-metadata"):
            check("whole-entry refusal " + population, "interface" if "only" in population or population == "missing-metadata" else "entry",
                  lambda p=population: preview("entry-" + p, population=p, expected_failure=True))
        check("whole-entry missing preset", "entry", lambda: preview("entry-missing-preset", missing_preset=True))
        check("whole-entry invalid source", "entry", lambda: preview("entry-invalid-source", invalid=True, expected_failure=True))
        check("whole-entry invalid boolean", "entry", lambda: preview("entry-invalid-boolean", malformed_boolean=True, expected_failure=True))
        check("whole-entry invalid argument", "entry", lambda: preview("entry-invalid-argument", arguments=["--invalid"], expected_failure=True))
        for population in ("unreadable-only", "no-parser-only", "mixed-no-parser"):
            check("whole-entry " + population, "interface",
                  lambda p=population: preview("entry-" + p, population=p, expected_failure=p != "mixed-no-parser"))
        for mode in ("failure", "INT", "TERM"):
            check("whole-entry post-trap " + mode, "entry",
                  lambda m=mode: interrupted_preview("entry-post-trap-" + m, m))
    if ARGS.suites in ("all", "normal"):
        check("normal actual caller", "normal", lambda: normal("normal"))
        check("NoOpen retains normal effects", "normal", lambda: normal("no-open", no_open=True))
    if ARGS.suites in ("all", "mutants"):
        dry_assignment = 'DRY_RUN="$' + '{DRY_RUN:-0}"'
        check("mutant eager initialization", "mutation", lambda: mutation(
            "eager", dry_assignment,
            dry_assignment + '\nif [ "$DRY_RUN" = 1 ]; then mkdir -p "$TMPDIR/eager-mutant"; fi', "entry"))
        check("mutant preview cleanup", "mutation", lambda: mutation(
            "cleanup", "cleanup_staging() {",
            'cleanup_staging() {\n  if [ "$DRY_RUN" = 1 ]; then rm -rf "$TMPDIR/salah-widget-installer"; fi', "entry"))
        check("mutant cached path return", "mutation", lambda: mutation(
            "cached-path", "download_tablissng_asset() {",
            'download_tablissng_asset() {\n  if [ "$DRY_RUN" = 1 ]; then printf "%s\\n" "$DOWNLOAD_ROOT/v-fixture/asset.zip"; return 0; fi',
            "helper", ("download_tablissng_asset chromium", "failure")))
        check("mutant suppressed copy success", "mutation", lambda: mutation(
            "copy-success", 'if [ "$DRY_RUN" = 1 ]; then warn "[dry-run] Clipboard copy suppressed."; return 1; fi',
            'if [ "$DRY_RUN" = 1 ]; then warn "[dry-run] Clipboard copy suppressed."; return 0; fi',
            "helper", ('copy_text "fixture"', "failure")))
        check("mutant clipboard attempt during preview", "mutation", lambda: mutation(
            "copy-effect", 'if [ "$DRY_RUN" = 1 ]; then warn "[dry-run] Clipboard copy suppressed."; return 1; fi',
            '# Controlled mutant: clipboard preview guard omitted.',
            "helper", ('copy_text "fixture"', "failure"), expected_boundary="clipboard"))
        direct_transport = r"""
if [ "$DRY_RUN" = 1 ]; then
  python3 - <<'R0016_DIRECT_TRANSPORT'
import os, socket, sys
print("__R0016_DIRECT_TRANSPORT_PID__" + str(os.getpid()), file=sys.stderr)
try:
    with socket.socket() as connection:
        connection.connect(("127.0.0.1", 9))
except OSError:
    pass
R0016_DIRECT_TRANSPORT
fi
"""
        check("mutant swallowed direct transport", "mutation", lambda: mutation(
            "direct-transport", dry_assignment, dry_assignment + direct_transport, "entry"))
unchanged = ORIGINAL.read_bytes() == SOURCE_BYTES
if not unchanged:
    RESULTS.append({"case": "source remained stable", "kind": "bootstrap", "pass_": False,
                    "classification": "BOOTSTRAP_BLOCKED", "error": "Source changed during qualification"})
report = {
    "schema": "r0016-preview-bash.v1", "source": str(ORIGINAL), "sourceSha256": SOURCE_SHA,
    "sourceUnchanged": unchanged, "fixture": str(ROOT), "testSha256": digest(__file__),
    "host": {"system": HOST, "kernel": platform.release(), "bash": ARGS.bash},
    "hostAcquisition": ACQUISITION,
    "nativeMacOSQualification": "THIS_NATIVE_RUN_ONLY" if HOST == "Darwin" else "NOT_RUN_ON_APPLE",
    "results": RESULTS, "R0015BashHelperInventory": "Bound to unchanged Bash production source; PowerShell transaction helpers are qualified separately",
    "pass_": all(row["pass_"] for row in RESULTS),
    "classification": ("BOOTSTRAP_BLOCKED" if any(row["classification"] == "BOOTSTRAP_BLOCKED" for row in RESULTS)
                       else "PRODUCT_ASSERTION_FAILED" if any(not row["pass_"] for row in RESULTS) else "PASS"),
    "counts": {classification: sum(row["classification"] == classification for row in RESULTS)
               for classification in ("PASS", "PRODUCT_ASSERTION_FAILED", "BOOTSTRAP_BLOCKED")},
    "limits": [
        "Helper extraction is separate from actual whole file entry.",
        "Host startup activity is distinct from installer subject effects.",
        "No real browser installation/import, signature or reboot-persistence claim.",
        "Only actual Darwin execution can qualify the native macOS adapter; Linux is not Apple proof.",
        "Darwin native log readback is a targeted capability probe, not complete process-tree attempt tracing.",
        "Darwin transportAttempts=null means no independent per-syscall trace, never zero attempted calls.",
    ],
}
(ROOT / "results.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
raise SystemExit(2 if any(r["classification"] == "BOOTSTRAP_BLOCKED" for r in RESULTS)
                 else 1 if any(not r["pass_"] for r in RESULTS) else 0)

