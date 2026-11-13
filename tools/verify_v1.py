#!/usr/bin/env python3
"""Verify the frozen V1 payload; never generates or repairs it. Python stdlib only."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

MANIFEST_SHA256 = "aa4bfcbc54f838e93d8ab41e58845efd753fcea80e8ebef3a784acf304e6a4cb"
CHECKOUT_ATTRIBUTES = b"# Preserve frozen payload bytes on every checkout.\n* -text\n"
# Jekyll reads the first of these that exists (yml, then yaml, then toml) unless told otherwise.
JEKYLL_CONFIG_NAMES = ("_config.yml", "_config.yaml", "_config.toml")
# Reviewed root Jekyll configurations: SHA-256 of the configuration file -> repository-relative review evidence.
# A digest is admitted only together with evidence that every V1 public file (v1/index.html, v1/config.js,
# v1/VERSION.json, v1/MANIFEST.sha256) was present and byte-identical in a built or deployed site produced
# from exactly that configuration. Static reasoning about `exclude` is not a review. The verifier checks that
# the digest is listed and that its evidence is JSON naming each V1 public file with the tree's SHA-256 (and
# byte count, where given); whether the evidence is otherwise adequate (that it really measures a site built
# from that configuration) is a reviewer judgement (docs/state-contracts/R0037.md, "Admitting a Jekyll
# configuration"). To admit a later configuration, add one entry with its evidence in the same change that edits
# the configuration.
REVIEWED_JEKYLL_CONFIGS = {
    # _config.yml blob 0700f748 (R0017, 02ab7a93): measured deployed Pages artifact of merge 06772824.
    "0f846f7efb27c391c66dffc66913f3eb452d5769e13170db64c2d0cd32a3e5c8":
        "docs/state-contracts/evidence/R0037/config-0f846f7e/deployed-pages-payload.json",
    # _config.yml with the R002B evidence-tree exclusions (owner decision DG-2(a), issue 92): build-equivalent
    # Jekyll build of b891b985 in hosted run 43368101308, protected consumers byte-identical.
    "e11bdd3d0dbe981f1ae6de2537e4353421dbc2e4b79f051e59242f1d01506a24":
        "docs/state-contracts/evidence/R002B/config-e11bdd3d/ci-build-pages-payload.json",
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pages_config(repo):
    """Return (errors, note) for the root Jekyll configuration; an inclusion preflight, never a deployment check."""
    if (repo / ".nojekyll").exists():
        return [], ".nojekyll present (Jekyll processing off)"
    present = [name for name in JEKYLL_CONFIG_NAMES if (repo / name).exists()]
    if len(present) > 1:
        return ["More than one Jekyll configuration file (ambiguous build input): " + ", ".join(present)], None
    if not present:
        return [], "no Jekyll configuration file"
    name = present[0]
    h = digest(repo / name)
    evidence = REVIEWED_JEKYLL_CONFIGS.get(h)
    if evidence is None:
        return [f"Jekyll configuration {name} {h} has no recorded V1 inclusion review"], None
    if not (repo / evidence).is_file():
        return [f"Jekyll configuration {name} {h} review evidence missing: {evidence}"], None
    try:
        listed = evidence_v1_files(json.loads((repo / evidence).read_text(encoding="utf-8")))
    except (ValueError, UnicodeDecodeError):
        return [f"Jekyll configuration {name} {h} review evidence is not JSON: {evidence}"], None
    errors = []
    for path in V1_PUBLIC_FILES:
        b = (repo / path).read_bytes()
        record = listed.get(path)
        if (not isinstance(record, dict) or record.get("sha256") != hashlib.sha256(b).hexdigest()
                or record.get("bytes", len(b)) != len(b)):
            errors.append(f"Jekyll configuration {name} {h} review evidence {evidence} does not list {path} "
                          "with the tree's SHA-256")
    if errors:
        return errors, None
    return [], f"reviewed Jekyll configuration {name} {h}"


V1_PUBLIC_FILES = ("v1/index.html", "v1/config.js", "v1/VERSION.json", "v1/MANIFEST.sha256")


def evidence_v1_files(node, found=None):
    """Collect {path: record} for the V1 public files from a JSON receipt: either an object keyed by the path
    (as R0017's protectedConsumers) or list items carrying "path". The first record seen for a path wins."""
    found = {} if found is None else found
    if isinstance(node, dict):
        if isinstance(node.get("path"), str) and node["path"] in V1_PUBLIC_FILES:
            found.setdefault(node["path"], node)
        for key, value in node.items():
            if key in V1_PUBLIC_FILES and isinstance(value, dict):
                found.setdefault(key, value)
            evidence_v1_files(value, found)
    elif isinstance(node, list):
        for item in node:
            evidence_v1_files(item, found)
    return found


def verify(repo, check_root=False, check_pages=False, notes=None):
    v1 = repo / "v1"
    errors = []
    manifest = v1 / "MANIFEST.sha256"
    if not manifest.is_file() or digest(manifest) != MANIFEST_SHA256:
        return ["MANIFEST.sha256 differs from the reviewed preservation manifest"]
    expected = {}
    for line in manifest.read_text(encoding="ascii").splitlines():
        h, name = line.split("  ", 1)
        if name not in {"index.html", "config.js", "VERSION.json"} or name in expected:
            return ["Unexpected or duplicate manifest path"]
        expected[name] = h
    for name, h in expected.items():
        p = v1 / name
        if not p.is_file() or p.is_symlink() or digest(p) != h:
            errors.append(f"Frozen payload changed or missing: v1/{name}")
    actual = {p.relative_to(v1).as_posix() for p in v1.rglob("*") if p.is_file()}
    extras = actual - set(expected) - {"MANIFEST.sha256", ".gitattributes"}
    if extras:
        errors.append("Unmanifested V1 files: " + ", ".join(sorted(extras)))
    attrs = v1 / ".gitattributes"
    # .gitattributes is checkout protection, intentionally not a Pages payload.
    if not attrs.is_file() or attrs.read_bytes() != CHECKOUT_ATTRIBUTES:
        errors.append("V1 checkout byte-preservation attributes changed")
    if errors:
        return errors
    version = json.loads((v1 / "VERSION.json").read_text(encoding="utf-8"))
    for p in version["payload"]:
        if digest(repo / p["v1Path"]) != p["sha256"]:
            errors.append("VERSION payload digest mismatch: " + p["v1Path"])
        if check_root and digest(repo / p["sourcePath"]) != p["sourceSha256"]:
            errors.append("Root differs from preserved production: " + p["sourcePath"])
    if check_pages:
        # Bounded check for the inspected branch/main-root Pages configuration.
        # This is an inclusion preflight, not a claim that a deployment ran.
        found, note = pages_config(repo)
        errors.extend(found)
        if note and notes is not None:
            notes.append(note)
        for name in expected:
            if (v1 / name).read_bytes().startswith(b"---"):
                errors.append("Unexpected front matter: " + name)
    return errors


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    p.add_argument("--check-root", action="store_true", help="Only before root overhaul: assert the two root runtime files still equal production")
    p.add_argument("--check-pages", action="store_true", help="Check static-file inclusion prerequisites for the inspected main/root Pages source")
    p.add_argument("--negative-control", action="store_true", help="Prove tampering fails, in a disposable copy")
    args = p.parse_args()
    notes = []
    errors = verify(args.repo, args.check_root, args.check_pages, notes)
    if errors:
        for error in errors:
            print("FAIL:", error)
        return 1
    print("PASS: frozen V1 payload and anchored manifest")
    if args.check_root:
        print("PASS: root index.html and config.js match pinned production bytes")
    if args.check_pages:
        print("PASS: plain static V1 files; " + "; ".join(notes) + "; inclusion preflight only; deployment not checked")
    if args.negative_control:
        with tempfile.TemporaryDirectory(prefix="salah-v1-tamper-") as tmp:
            root = Path(tmp)
            shutil.copytree(args.repo / "v1", root / "v1")
            target = root / "v1" / "index.html"
            target.write_bytes(target.read_bytes() + b"\n<!-- deliberate tamper -->\n")
            found = verify(root)
            if found != ["Frozen payload changed or missing: v1/index.html"]:
                raise SystemExit("FAIL: negative control did not identify changed index.html")
            print("PASS: disposable tamper rejected: " + found[0])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
