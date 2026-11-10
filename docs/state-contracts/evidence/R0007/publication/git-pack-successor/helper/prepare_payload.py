#!/usr/bin/env python3
"""Prepare four small seed files from an explicit clean committed R0007 target.

Reads Git objects only. Output must be outside the candidate checkout. This
does not build, contact GitHub, create a commit, or update a ref.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

REPOSITORY = "theislampill/salah_widget"
BRANCH = "pro/r0007-explicit-next-event-state-20261106"
DEFAULT_BASE = "eebba178172f96b3ffe5ab3845bc0fffd57c6e1b"
DEFAULT_ANCESTORS = ["3b2d09c748f71dc77806882f62f7339cbd18f19c",
                     "19004279805604ef5e41292ffd4e9f442e1321f2", DEFAULT_BASE]
GENERATED = {"index.html", "offline.html", "moon/BUILD.json"}
SEED_FILES = {".github/workflows/r0007-materialize.yml", ".github/r0007-bootstrap/materialize.py",
              ".github/r0007-bootstrap/manifest.json", ".github/r0007-bootstrap/source.patch"}
TARGET_WORKFLOWS = {".github/workflows/r0007-native.yml", ".github/workflows/r0007-public-delivery.yml"}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def git(root, *args, binary=False):
    return subprocess.check_output(["git", "-C", str(root), *args], text=not binary,
                                   env={**os.environ, "GIT_LITERAL_PATHSPECS": "1"})


def entry(root, commit, path):
    row = git(root, "ls-tree", commit, "--", path).strip()
    if not row:
        return None
    prefix, observed = row.split("\t", 1)
    mode, kind, blob = prefix.split()
    if observed != path or kind != "blob" or mode not in {"100644", "100755"}:
        raise ValueError("unsupported changed entry: " + path)
    content = git(root, "cat-file", "blob", blob, binary=True)
    return {"mode": mode, "blobSha": blob, "bytes": len(content), "sha256": sha(content)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--base", default=DEFAULT_BASE)
    parser.add_argument("--seed-ancestor", action="append", help="Explicit immutable seed ancestry, immediate parent first; exactly three entries")
    parser.add_argument("--target", required=True, help="Full immutable commit SHA; must be the clean source HEAD")
    parser.add_argument("--output", type=Path, required=True, help="Fresh output directory outside source-root")
    args = parser.parse_args()
    root, output = args.source_root.resolve(), args.output.resolve()
    seed_ancestors = args.seed_ancestor if args.seed_ancestor is not None else DEFAULT_ANCESTORS
    if len(seed_ancestors) != 3 or len(set(seed_ancestors)) != 3 or seed_ancestors[-1] != args.base:
        parser.error("seed ancestry must contain exactly two prior seeds followed by original base")
    seed_parent = seed_ancestors[0]
    if output.is_relative_to(root) or output.exists():
        parser.error("output must be a fresh directory outside source-root")
    if any(not re.fullmatch(r"[0-9a-f]{40}", v) for v in [args.base, args.target, *seed_ancestors]):
        parser.error("base, target and seed-parent must be full immutable SHA values")
    if git(root, "rev-parse", "HEAD").strip() != args.target or git(root, "status", "--porcelain", "--untracked-files=normal").strip():
        parser.error("final source must have clean HEAD equal to target; do not bind an unfinished corrective tree")
    if git(root, "branch", "--show-current").strip() != BRANCH:
        parser.error("source must be on the commissioned R0007 branch")
    if subprocess.run(["git", "-C", str(root), "merge-base", "--is-ancestor", args.base, args.target]).returncode:
        parser.error("base is not an ancestor of target")
    try:
        for index, commit in enumerate(seed_ancestors):
            if git(root, "cat-file", "-t", commit).strip() != "commit":
                parser.error("seed ancestor must identify an available immutable local commit")
            if index < len(seed_ancestors) - 1:
                parents = git(root, "show", "-s", "--format=%P", commit).split()
                seed_delta = set(filter(None, git(root, "diff", "--no-renames", "--name-only", "-z", args.base, commit).split("\0")))
                if parents != [seed_ancestors[index + 1]] or seed_delta != SEED_FILES:
                    parser.error("seed ancestry must preserve each exact parent and four-file cumulative delta")
    except subprocess.CalledProcessError:
        parser.error("seed-parent must identify an available immutable local commit")
    for p in SEED_FILES:
        if entry(root, args.base, p) is not None or entry(root, args.target, p) is not None:
            parser.error("reserved seed path already exists: " + p)
    paths = git(root, "diff", "--name-only", "--no-renames", "-z", args.base, args.target).split("\0")
    paths = sorted(p for p in paths if p)
    if not paths:
        parser.error("candidate has no changes")
    if {p for p in paths if p.startswith(".github/workflows/")} != TARGET_WORKFLOWS:
        parser.error("target must change exactly the two commissioned workflow paths")
    changes = [{"path": p, "before": entry(root, args.base, p), "after": entry(root, args.target, p)} for p in paths]
    patch_paths = [p for p in paths if p not in GENERATED]
    patch = git(root, "diff", "--binary", "--full-index", "--no-renames", args.base, args.target, "--", *patch_paths, binary=True)
    materializer = (Path(__file__).parent / "templates/materialize.py").read_bytes()
    manifest = {"schema": "r0007-pack-input/v1", "repository": REPOSITORY, "branch": BRANCH,
                "baseCommit": args.base, "baseTree": git(root, "rev-parse", args.base + "^{tree}").strip(),
                "expectedSeedParent": seed_parent, "seedAncestors": seed_ancestors,
                "targetCommit": args.target, "targetTree": git(root, "rev-parse", args.target + "^{tree}").strip(),
                "patchFile": ".github/r0007-bootstrap/source.patch", "patchSha256": sha(patch), "patchBytes": len(patch),
                "materializerSha256": sha(materializer), "builderCommand": ["python3", "tools/build_native.py"],
                "generatedPaths": sorted(GENERATED), "patchPaths": patch_paths, "changes": changes,
                "seedFilesExcludedFromCandidate": sorted(SEED_FILES), "refUpdatesAllowed": ["refs/heads/" + BRANCH],
                "finalizationPaths": sorted(SEED_FILES | TARGET_WORKFLOWS),
                "preparedUtc": datetime.now(timezone.utc).isoformat()}
    manifest_bytes = (json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode()
    workflow = (Path(__file__).parent / "templates/r0007-materialize.yml").read_text()
    if workflow.count("__MANIFEST_SHA256__") != 1:
        raise ValueError("workflow digest placeholder is not unique")
    files = {".github/workflows/r0007-materialize.yml": workflow.replace("__MANIFEST_SHA256__", sha(manifest_bytes)).encode(),
             ".github/r0007-bootstrap/materialize.py": materializer,
             ".github/r0007-bootstrap/manifest.json": manifest_bytes,
             ".github/r0007-bootstrap/source.patch": patch}
    output.mkdir(parents=True)
    for relative, content in files.items():
        p = output / relative
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(content)
    preparation = {"baseCommit": args.base, "expectedSeedParent": seed_parent, "seedAncestors": seed_ancestors,
                   "targetCommit": args.target, "targetTree": manifest["targetTree"],
                   "seedOnlyFiles": [{"path": p, "mode": "100644", "bytes": len(b), "sha256": sha(b)} for p, b in sorted(files.items())],
                   "patchBytes": len(patch), "expectedChangedPathCount": len(changes), "effectsPerformed": "LOCAL_PREPARATION_ONLY"}
    (output / "preparation.json").write_text(json.dumps(preparation, indent=2) + "\n")
    print(json.dumps(preparation, indent=2))


if __name__ == "__main__":
    main()
