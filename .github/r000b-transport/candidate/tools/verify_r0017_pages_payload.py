"""Measure the actual R0017 Pages output; never builds or deploys the widget."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess

APPROVED = "7fb3dd33b5efb2a8d8a187bd5e2a5901b900fce6"
BASE = "763a460e98dc23c7f0e95bf346274f1685b3c654"
RUNTIME = "5ff3fdf5a13cd3a798addfef972ed9a2c865f87cce531a23847015dcdc8a7d46"
EVIDENCE = "2f9a5b82cd83e3ae7b994f110b58efc92bbb46a6"
EXCLUDED = "docs/rlgwo-execution/20261014/R000C/native"
IMAGE = "ghcr.io/actions/jekyll-build-pages:v1.0.13"
IMAGE_DIGEST = "sha256:6791ebfd912185ed59bfb5fb102664fa872496b79f87ff8b9cfba292a7345041"
ALLOWED = {
    "_config.yml", ".github/workflows/r0017-pages-payload.yml",
    "tools/verify_r0017_pages_payload.py",
    "docs/rlgwo-execution/20261014/R000C/README.md",
    "docs/rlgwo-execution/20261014/R0017_READINESS.md",
}


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def verify(root, site, receipt):
    def git(*args):
        return subprocess.check_output(["git", *args], cwd=root).decode().strip()

    head = git("rev-parse", "HEAD")
    subprocess.run(["git", "merge-base", "--is-ancestor", APPROVED, head], cwd=root, check=True)
    changes = git("diff", "--name-only", APPROVED, head).splitlines()
    assert set(changes) <= ALLOWED, changes
    receipt.update({"sourceCommit": head, "sourceTree": git("rev-parse", "HEAD^{tree}"),
                    "approvedImplementation": APPROVED, "reviewedBase": BASE,
                    "additionalChangedPaths": changes})
    config = (root / "_config.yml").read_text()
    exclusions = [line.strip()[2:] for line in config.splitlines() if line.strip().startswith("- ")]
    assert exclusions == [EXCLUDED]
    digests = json.loads(subprocess.check_output(
        ["docker", "image", "inspect", IMAGE, "--format", "{{json .RepoDigests}}"], text=True))
    assert any(value.endswith("@" + IMAGE_DIGEST) for value in digests), digests
    receipt["build"] = {
        "action": "actions/jekyll-build-pages@44a6e6beabd48582f863aeeb6cb2151cc1716697",
        "image": IMAGE, "imageDigest": IMAGE_DIGEST,
        "configSha256": sha(root / "_config.yml"),
        "inputs": {"source": "./", "destination": "./_site", "future": False,
                   "build_revision": head, "verbose": False},
        "environment": "JEKYLL_ENV=production; same github-pages v232 / Jekyll 3.10.0 image as active legacy Pages build",
        "workflowRunId": os.environ.get("GITHUB_RUN_ID"),
    }
    tracked = git("ls-files", "-z").split("\0")
    tracked = [name for name in tracked if name]
    excluded = [name for name in tracked if name.startswith(EXCLUDED + "/")]
    assert excluded and not (site / EXCLUDED).exists()
    assert git("rev-parse", head + ":" + EXCLUDED) == "2f452a4ba3cbe353f25327a39d2f026d53838b16"
    receipt["excluded"] = [{
        "path": EXCLUDED, "reason": "Historical R000C raw PNG/JPEG/video/JSON/XZ records; no runtime or test resource",
        "files": len(excluded), "sourceBytes": sum((root / name).stat().st_size for name in excluded),
        "unchangedGitTree": git("rev-parse", head + ":" + EXCLUDED),
        "immutableCommit": EVIDENCE,
        "immutableTreeUrl": f"https://github.com/theislampill/salah_widget/tree/{EVIDENCE}/{EXCLUDED}",
        "resolver": "docs/rlgwo-execution/20261014/R000C/README.md#native-evidence",
    }]
    module_spec = importlib.util.spec_from_file_location("runtime_identity", root / "tools/cp9/runtime_identity.py")
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    runtime = module.runtime_identity(root)
    assert runtime["treeSha256"] == RUNTIME and len(runtime["files"]) == 135
    protected = set(runtime["files"])
    protected.update(name for name in tracked if name.startswith(("v1/", "tests/", "presets/"))
                     and not any(part.startswith(".") for part in Path(name).parts))
    protected.update(name for name in ["install.sh", "install.ps1", "README.md", "DESIGN.md", "AGENTS.md", "HANDOFF.md",
                                      "docs/V1_PRESERVATION.md", "docs/rlgwo-execution/20261014/R000C/README.md",
                                      "docs/rlgwo-execution/20261014/R0017_READINESS.md"] if (root / name).is_file())
    identities = {}
    for name in sorted(protected):
        source, output = root / name, site / name
        assert output.is_file() and not output.is_symlink(), name
        actual = sha(output)
        assert actual == sha(source), name
        identities[name] = {"bytes": output.stat().st_size, "sha256": actual}
    all_files = []
    for path in site.rglob("*"):
        assert not path.is_symlink(), str(path)
        if path.is_file():
            all_files.append((path.relative_to(site).as_posix(), path.stat().st_size))
    assert all_files
    assert not any(name.endswith("/R0017_EVIDENCE.zip") for name, _ in all_files)
    total = sum(size for _, size in all_files)
    receipt["output"] = {"regularFiles": len(all_files), "regularFileBytes": total, "limitBytes": 1_000_000_000,
                         "measurement": "Complete generated _site, including generated HTML/CSS and all static files; not Git-tree or compressed-archive size",
                         "pathSizeManifestSha256": hashlib.sha256("".join(f"{size}  {name}\n" for name, size in sorted(all_files)).encode()).hexdigest()}
    receipt["protectedConsumers"] = {"runtimeSha256": RUNTIME, "runtimeFiles": 135,
                                     "allComparedByteIdentical": True, "files": identities}
    receipt["references"] = {"changedDocument": "docs/rlgwo-execution/20261014/R000C/README.md",
                             "historicalRawPathsResolveAtImmutableCommit": EVIDENCE,
                             "rawEvidenceOrCertificatesRewritten": False,
                             "directLinksIntoExcludedPrefixBeforeChange": 0,
                             "runtimeDependenciesOnExcludedPrefix": 0}
    assert EVIDENCE in (root / "docs/rlgwo-execution/20261014/R000C/README.md").read_text()
    assert total <= 1_000_000_000, total
    receipt["status"] = "PASS"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--site", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    result = {"schema": "r0017-build-equivalent-pages-payload/v1", "status": "FAIL"}
    try:
        verify(root, (root / args.site).resolve(), result)
    except Exception as error:
        result["error"] = f"{type(error).__name__}: {error}"
        raise
    finally:
        Path(args.out).write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps({key: result[key] for key in ["status", "sourceCommit", "output", "error"] if key in result}))
