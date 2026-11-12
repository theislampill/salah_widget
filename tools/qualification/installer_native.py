#!/usr/bin/env python3
"""Run only source-bound installer fixtures; retain every terminal observation.

The installer itself is never invoked here without its disposable entry harness.
Native platform facts come from the current host, not from fixture labels.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import stat
import subprocess
import sys
import tempfile


def receipt(text):
    """Host messages may precede exactly one terminal JSON object."""
    decoder = json.JSONDecoder()
    for offset, char in enumerate(text):
        if char != "{":
            continue
        try:
            value, end = decoder.raw_decode(text[offset:])
        except ValueError:
            continue
        if not text[offset + end:].strip() and isinstance(value, dict):
            return value
    raise ValueError("no terminal structured receipt")


def passed(value):
    rows = value.get("results")
    if not isinstance(rows, list) or not rows:
        return False
    for row in rows:
        if not isinstance(row, dict):
            return False
        flags = [row[key] for key in ("pass_", "pass", "detected") if key in row]
        if not flags or not all(flag is True for flag in flags):
            return False
    return True


def path_identity(path):
    path = Path(path)
    info = path.lstat()
    return {"path": str(path), "physical": str(path.resolve()), "device": info.st_dev,
            "inode": info.st_ino, "uid": info.st_uid, "gid": info.st_gid,
            "mode": oct(stat.S_IMODE(info.st_mode)), "symlink": path.is_symlink()}


def native_fact(command):
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=20)
        return {"command": command, "exit": result.returncode, "stdout": result.stdout, "stderr": result.stderr}
    except (OSError, subprocess.TimeoutExpired) as error:
        return {"command": command, "exit": None, "error": str(error)}


def copy_fixtures(parsed, out, name, temporary_parent):
    """Preserve primary and explicitly reported auxiliary disposable roots."""
    primary = parsed.get("fixture") or parsed.get("fixtureRoot")
    candidates = ([primary] if primary else []) + parsed.get("auxiliaryFixtures", [])
    if len(candidates) > 16:
        raise ValueError("too many fixture roots")
    parent = Path(temporary_parent).resolve()
    copied = []
    for number, candidate in enumerate(candidates):
        path = Path(candidate)
        resolved = path.resolve()
        if not path.is_absolute() or path.is_symlink() or resolved == parent or not resolved.is_relative_to(parent):
            raise ValueError("reported fixture is outside the disposable temporary parent")
        if not path.is_dir():
            raise ValueError("reported fixture root is missing")
        destination = out / (name + ("-fixture" if number == 0 else f"-fixture-{number}"))
        shutil.copytree(path, destination, symlinks=True)
        copied.append({"original": str(path), "archive_directory": destination.name})
    return copied


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-os", choices=("Linux", "Darwin", "Windows"), required=True)
    parser.add_argument("--phase", choices=("r0013", "r0015", "r0016"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    env = dict(os.environ)
    report = {"schema": "installer-native-v1", "status": "INCOMPLETE",
              "phase": args.phase, "host": {"system": platform.system(),
              "platform": platform.platform(), "python": sys.version,
              "image_version": env.get("ImageVersion", env.get("IMAGEVERSION"))}, "commands": []}
    report["commit"] = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    report["tree"] = subprocess.check_output(["git", "rev-parse", "HEAD^{tree}"], cwd=root, text=True).strip()
    report["source_hashes"] = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in [root / "install.sh", root / "install.ps1",
                                        *sorted((root / "tests").glob("install*"))]
                              if p.is_file()}

    def save():
        (out / "result.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    def run(name, command):
        started = dt.datetime.now(dt.timezone.utc).isoformat()
        try:
            result = subprocess.run(command, cwd=root, env=env, capture_output=True, timeout=240)
            stdout = result.stdout.decode("utf-8-sig", errors="replace")
            stderr = result.stderr.decode("utf-8-sig", errors="replace")
            code = result.returncode
            try:
                parsed = receipt(stdout)
                good = code == 0 and passed(parsed)
            except ValueError as error:
                parsed = {"parse_error": str(error)}
                good = False
        except (OSError, subprocess.TimeoutExpired) as error:
            stdout, stderr, code, parsed, good = "", str(error), None, {}, False
        (out / (name + ".stdout.txt")).write_text(stdout, encoding="utf-8")
        (out / (name + ".stderr.txt")).write_text(stderr, encoding="utf-8")
        try:
            archived = copy_fixtures(parsed, out, name, tempfile.gettempdir())
        except (OSError, ValueError) as error:
            archived = []
            parsed["fixture_copy_error"] = str(error)
            good = False
        (out / (name + ".json")).write_text(json.dumps(parsed, indent=2) + "\n", encoding="utf-8")
        report["commands"].append({"name": name, "command": command, "started": started,
                                   "finished": dt.datetime.now(dt.timezone.utc).isoformat(),
                                   "exit": code, "passed": good, "archived_fixtures": archived})
        save()
        print(f"{name}: {'PASS' if good else 'FAIL'} (exit {code})", flush=True)

    save()
    if platform.system() != args.expected_os:
        report["gate_error"] = "actual host does not match required native platform"
        save()
        return 1
    if args.expected_os in ("Linux", "Darwin"):
        shell = "/bin/bash"
        version = subprocess.check_output([shell, "--version"], text=True).splitlines()[0]
        report["host"]["bash"] = version
        report["host"]["uid"] = os.getuid()
        report["host"]["gid"] = os.getgid()
        report["host"]["groups"] = os.getgroups()
        report["host"]["native_tools"] = {name: shutil.which(name) for name in ("bash", "python3", "stat", "id", "mktemp", "find", "sort", "curl", "uname", "df", "sandbox-exec", "log", "dtruss")}
        fixture_parent = Path(tempfile.gettempdir()).resolve()
        report["host"]["parent_identities"] = [path_identity(path) for path in (root, out.parent, Path(env.get("TMPDIR", "/tmp")), fixture_parent, Path(env["HOME"]))]
        report["host"]["fixture_parent"] = str(fixture_parent)
        facts = {"uname": native_fact(["/usr/bin/uname", "-a"]), "filesystem_mount": native_fact(["df", "-P", str(out)]),
                 "fixture_filesystem_mount": native_fact(["df", "-P", str(fixture_parent)])}
        if args.expected_os == "Darwin":
            facts["sw_vers"] = native_fact(["/usr/bin/sw_vers"])
            facts["native_stat"] = native_fact(["/usr/bin/stat", "-f", "%d:%i:%u:%g:%Lp", str(out)])
            mount_lines = facts["filesystem_mount"].get("stdout", "").splitlines()
            device = mount_lines[-1].split()[0] if len(mount_lines) > 1 else ""
            facts["filesystem_volume"] = native_fact(["/usr/sbin/diskutil", "info", "-plist", device]) if device.startswith("/dev/") else {"exit": None, "error": "native mount device unavailable"}
            fixture_lines = facts["fixture_filesystem_mount"].get("stdout", "").splitlines()
            fixture_device = fixture_lines[-1].split()[0] if len(fixture_lines) > 1 else ""
            facts["fixture_filesystem_volume"] = native_fact(["/usr/sbin/diskutil", "info", "-plist", fixture_device]) if fixture_device.startswith("/dev/") else {"exit": None, "error": "native fixture mount device unavailable"}
        else:
            facts["native_stat"] = native_fact(["stat", "-c", "%d:%i:%u:%g:%a", str(out)])
            facts["filesystem_volume"] = native_fact(["stat", "-f", "-c", "%T", str(out)])
            facts["fixture_filesystem_volume"] = native_fact(["stat", "-f", "-c", "%T", str(fixture_parent)])
        report["host"]["acquisition"] = facts
        if any(fact["exit"] != 0 for fact in facts.values()):
            report["gate_error"] = "native acquisition facts incomplete; not a product test result"
            save()
            return 1
        if args.expected_os == "Darwin" and "version 3.2." not in version:
            report["gate_error"] = "Apple /bin/bash 3.2 required"
            save()
            return 1
        env["SALAH_TEST_BASH"] = shell
        for test in ("install-bash.py", "install-entry-bash.py", "install-discovery.py", "install-detectors.py"):
            run(test[:-3], [sys.executable, str(root / "tests" / test), str(root / "install.sh")])
        run("install-discovery-mutations", [sys.executable, str(root / "tests/install-discovery-mutations.py"), str(root / "install.sh")])
        run("install-original-mutations", [sys.executable, str(root / "tests/install-mutations.py"), str(root / "install.sh")])
        run("install-builder", ["node", str(root / "tests/install-builder.cjs")])
        if args.phase in ("r0015", "r0016"):
            run("install-staging-native", [sys.executable, str(root / "tests/install-staging-native.py"), str(root / "install.sh")])
        if args.expected_os == "Linux" and args.phase in ("r0015", "r0016"):
            run("install-linux-owner", [sys.executable, str(root / "tests/install-linux-owner.py"), str(root / "install.sh")])
        if args.phase == "r0016":
            run("install-preview", [sys.executable, str(root / "tests/install-preview.py"), str(root / "install.sh")])
    else:
        hosts = [("ps51", str(Path(env["SYSTEMROOT"]) / "System32/WindowsPowerShell/v1.0/powershell.exe")),
                 ("ps7", env["INSTALL_TEST_PS7"])]
        for name, executable in hosts:
            version = subprocess.check_output([executable, "-NoProfile", "-Command", "$PSVersionTable.PSVersion.ToString()"], text=True).strip()
            report["host"][name] = {"executable": executable, "version": version}
            if (name == "ps51" and not version.startswith("5.1.")) or (name == "ps7" and version != "7.6.6"):
                report["gate_error"] = "required PowerShell version unavailable"
                save()
                return 1
            files = ["install-host-bootstrap.ps1", "install-powershell.ps1", "install-powershell-guards.ps1", "install-discovery.ps1"]
            if args.phase in ("r0015", "r0016"):
                files.append("install-powershell-transactions.ps1")
            if args.phase == "r0016":
                files.append("install-preview.ps1")
            for test in files:
                command = [executable, "-NoProfile", "-File", str(root / "tests" / test), "-SourceFile", str(root / "install.ps1")]
                if test == "install-powershell-transactions.ps1":
                    command.extend(["-PresetFile", str(root / "presets/salah-widget.tablissng.json")])
                if test == "install-host-bootstrap.ps1":
                    command.extend(["-OutputRoot", tempfile.gettempdir()])
                run(name + "-" + test[:-4], command)
            run(name + "-discovery-mutations", [sys.executable, str(root / "tests/install-discovery-mutations.py"), str(root / "install.ps1"), executable])
        run("install-entry-native", [sys.executable, str(root / "tests/install-entry-native.py"), str(root / "install.ps1")])
    report["status"] = "PASS" if report["commands"] and all(x["passed"] for x in report["commands"]) else "FAIL"
    save()
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
