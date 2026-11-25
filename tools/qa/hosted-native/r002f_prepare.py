#!/usr/bin/env python3
"""Materialize the reviewed R002F combined arm into fresh disposable directories.

Inputs are read-only. Canonical builders and the existing six-preimage research
materializer retain their guards. Generated entries and the complete generated
inventories are compared with the published identities before native use.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

BASE_COMMIT = "df644ef60156b67b5c487395176369bcec7a0d7b"
RESEARCH_COMMIT = "55d1b3edb66d2c35679707120b01ee1d3455e4a3"
BASE_INDEX = "88411488017ea590e6b4c5a21adc143977c0907089eabb80b0cbe8f0ba18a8a1"
COMBINED_INDEX = "55a8bdbc7b7ab5cb53ede3b58c0ef1e4101c7c89bc6936860bd4bc5f3acb8fe2"
BASE_INVENTORY = "cbce31ba3a018b99e4259c192902442db421b2d8b8b65e48e143acf19bcaf4f2"
COMBINED_INVENTORY = "69f819a9cce8b4fb82fc8977d64c71bdf0f071eec40972d0cf99df830250c481"
PATCH = "a310e13f6c92439cdc30224a5ec6b6a2170804e2a58a9640965ccb7bad7879d7"
TOOL_PINS = {
    "tools/build_native.py": "a48e43cfb6d3d4af0553e89cf808096825bc039d4fb9375e5cca1a9435e63832",
    "tools/build_moon.py": "1561c5d2fbfd6cad5d0196106631404bdfa997c5458d411a8ddfcacb9e13b9f0",
    "tools/generated_outputs.py": "2c3a1f1ece39ab6eca74e247681ce9accc3bdcf949dc6ff2dd07fdf8ddcc850d",
    "tools/verify_v1.py": "48eff560af5cfcbef37e275f7f9cc7d13b101e87c56d68b84ec9d84da8594950",
    "tools/qa/r002f-transaction/materialize.cjs": "b1d80a1a83933097f78fa6f30738794dd5d1677a0e4d9f02b54d87e384f2fa74",
    "tools/qa/r002f-transaction/preview-stage.js": "ab19d1ec14bf162b38519d5bddd58ca3fa88778607ce5942a5ae062d5a39f000",
    "tools/qa/r002f-transaction/detail-stage.js": "be7c571d2afa6c26ff75ad7c48f51aa4e38614a16bab1fa4dc9443268877e20f",
    "tools/qa/r002f_a2_architecture.cjs": "386cd4c7573fb91e4070d4306560a33bba8a7dfc2d4a0e6be22943ef4f81caeb",
    "tools/qa/r002f_a2_quarantine.cjs": "7efce81d525ceed636d4dcb8fd9b83c872f8dd6ed6b5633f505fb15c6898250c",
}
ROOT_FILES = ("index.html", "offline.html", "config.js", "builder.html", "GENERATED.json", "_config.yml")
PREFIXES = ("src/native", "real-sky", "moon", "vendor/real-sky", "v1")
EXTRA_FILES = (
    "docs/state-contracts/evidence/R002B/config-e11bdd3d/ci-build-pages-payload.json",
    "tests/r0002-ordinary.json",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def require_sha(root: Path, relative: str, expected: str) -> None:
    target = root / relative
    require(target.is_file() and not target.is_symlink() and sha(target) == expected,
            "unadmitted source identity: " + relative)


def inventory_paths(root: Path) -> list[str]:
    selected = set(ROOT_FILES + EXTRA_FILES)
    for prefix in PREFIXES:
        folder = root / prefix
        require(folder.is_dir() and not folder.is_symlink(), "missing build input: " + prefix)
        for current, dirs, files in os.walk(folder):
            dirs[:] = sorted(name for name in dirs if name not in {"__pycache__", "node_modules", ".git"})
            for name in dirs + files:
                item = Path(current) / name
                require(not item.is_symlink(), "symlink build input: " + item.relative_to(root).as_posix())
            selected.update((Path(current) / name).relative_to(root).as_posix() for name in files
                            if not name.endswith((".pyc", ".pyo")))
    selected.update(p.relative_to(root).as_posix() for p in (root / "tools").glob("*.py"))
    return sorted(selected)


def file_manifest(root: Path, paths: list[str]) -> list[dict]:
    result = []
    for name in paths:
        target = root / name
        require(target.is_file() and not target.is_symlink(), "missing regular input: " + name)
        result.append({"path": name, "bytes": target.stat().st_size, "sha256": sha(target)})
    return result


def copy_inputs(source: Path, destination: Path, manifest: list[dict]) -> None:
    destination.mkdir(mode=0o700)
    for entry in manifest:
        relative = entry["path"]
        dst = destination / relative
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source / relative, dst)
        require(sha(dst) == entry["sha256"], "copied input identity differs: " + relative)


def command(argv: list[str], cwd: Path, output: Path, label: str) -> str:
    stdout, stderr = output / (label + ".stdout"), output / (label + ".stderr")
    # Direct child writes survive TimeoutExpired and outer interruption. run()
    # retains its timeout kill/wait behavior; exclusive logs preserve an earlier
    # attempt if a caller accidentally reuses a label.
    with stdout.open("x", encoding="utf-8") as out, stderr.open("x", encoding="utf-8") as err:
        stdout.chmod(0o600)
        stderr.chmod(0o600)
        result = subprocess.run(argv, cwd=cwd, stdout=out, stderr=err, text=True, timeout=180)
    require(result.returncode == 0, "command failed: " + label)
    return stdout.read_text(encoding="utf-8")


def build_arm(root: Path, output: Path, arm: str, python: str) -> dict:
    expected_index = BASE_INDEX if arm == "baseline" else COMBINED_INDEX
    expected_inventory = BASE_INVENTORY if arm == "baseline" else COMBINED_INVENTORY
    runs = []
    for run in (1, 2):
        text = command([python, "tools/build_native.py"], root, output, f"{arm}-build-{run}")
        parsed = json.loads(text)
        require(parsed.get("phase") == "published" and parsed.get("indexSha256") == expected_index,
                "canonical build identity differs: " + arm)
        require_sha(root, "index.html", expected_index)
        require_sha(root, "GENERATED.json", expected_inventory)
        if run == 2:
            require(parsed.get("written") == 0 and parsed.get("removed") == 0 and parsed.get("unchanged") == 117,
                    "canonical second build is not stable: " + arm)
        runs.append(parsed)
    command([python, "tools/verify_v1.py", "--negative-control", "--check-pages"], root, output, arm + "-v1")
    generated = json.loads((root / "GENERATED.json").read_text(encoding="utf-8"))
    for relative, entry in generated["files"].items():
        require_sha(root, relative, entry["sha256"])
    return {"path": arm, "indexSha256": expected_index, "inventorySha256": expected_inventory,
            "builds": runs, "v1": "PASS with disposable tamper negative control and Pages inclusion preflight"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--research", required=True, type=Path)
    parser.add_argument("--baseline", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--node", default="node")
    args = parser.parse_args(argv)
    research, baseline, out = (p.resolve() for p in (args.research, args.baseline, args.out))
    require(not out.exists(), "output directory must be fresh")
    require(not out.is_relative_to(baseline) and not out.is_relative_to(research), "output must be outside source inputs")
    for root in (baseline, research):
        require_sha(root, "index.html", BASE_INDEX)
        require_sha(root, "GENERATED.json", BASE_INVENTORY)
    for relative, expected in TOOL_PINS.items():
        require_sha(research, relative, expected)
        if "/qa/" not in relative:
            require_sha(baseline, relative, expected)
    manifest = file_manifest(baseline, inventory_paths(baseline))
    require(file_manifest(research, [entry["path"] for entry in manifest]) == manifest,
            "research product/build inputs differ from the admitted main baseline")
    tool_manifest = file_manifest(research, sorted(TOOL_PINS))
    out.mkdir(parents=True, mode=0o700)
    receipt = {"protocol": "r002f-hosted-build/1", "status": "INCOMPLETE",
               "baseProvenance": BASE_COMMIT, "researchProvenance": RESEARCH_COMMIT,
               "identityScope": "content-verified build inputs; commit custody belongs to acquisition",
               "wrapperSha256": sha(Path(__file__)), "python": sys.version,
               "inputs": manifest, "researchTools": tool_manifest, "arms": {}}
    try:
        for arm in ("baseline", "candidate"):
            copy_inputs(baseline, out / arm, manifest)
        command([args.node, str(research / "tools/qa/r002f-transaction/materialize.cjs"),
                 str(out / "patch"), "--combined"], research, out, "materialize")
        patch_manifest = json.loads((out / "patch/manifest.json").read_text(encoding="utf-8"))
        require(patch_manifest.get("patch") == PATCH, "unadmitted combined patch manifest")
        require_sha(out / "patch", "transaction.patch", PATCH)
        for entry in patch_manifest["files"]:
            require_sha(out / "candidate", entry["file"], entry["original"])
        command(["git", "apply", "--check", str(out / "patch/transaction.patch")], out / "candidate", out, "patch-check")
        command(["git", "apply", str(out / "patch/transaction.patch")], out / "candidate", out, "patch-apply")
        for entry in patch_manifest["files"]:
            require_sha(out / "candidate", entry["file"], entry["candidate"])
        receipt["patch"] = patch_manifest
        for arm in ("baseline", "candidate"):
            receipt["arms"][arm] = build_arm(out / arm, out, arm, sys.executable)
        require(file_manifest(baseline, [entry["path"] for entry in manifest]) == manifest, "baseline input was mutated")
        require(file_manifest(research, [entry["path"] for entry in manifest]) == manifest, "research input was mutated")
        require(file_manifest(research, sorted(TOOL_PINS)) == tool_manifest, "research tools were mutated")
        receipt["status"] = "PASS"
    except Exception as error:
        receipt["error"] = str(error)
    finally:
        (out / "build-result.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print("R002F_BUILD " + receipt["status"])
    return 0 if receipt["status"] == "PASS" else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError) as error:
        print("R002F_BUILD INCOMPLETE: " + str(error), file=sys.stderr)
        raise SystemExit(2)
