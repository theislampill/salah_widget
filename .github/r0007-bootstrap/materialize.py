#!/usr/bin/env python3
"""Reconstruct a hash-bound R0007 tree; optionally upload blobs, never refs.

Run only inside the disposable seed checkout. Dry mode requires no token or
network. The explicit upload mode permits only POST /git/blobs in this repo.
"""
from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request

REPOSITORY = "theislampill/salah_widget"
BRANCH = "pro/r0007-explicit-next-event-state-20261106"
SEED_FILES = {".github/workflows/r0007-materialize.yml", ".github/r0007-bootstrap/materialize.py",
              ".github/r0007-bootstrap/manifest.json", ".github/r0007-bootstrap/source.patch"}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise urllib.error.HTTPError(req.full_url, code, "redirect refused", headers, fp)


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def dump(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def safe_path(value):
    return (isinstance(value, str) and value and "\\" not in value and not PurePosixPath(value).is_absolute()
            and not any(ord(char) < 32 or ord(char) == 127 for char in value)
            and not any(p in {"", ".", "..", ".git"} for p in value.split("/")))


def child_env():
    # The builder and Git subprocesses have no need for our API upload token.
    result = os.environ.copy()
    result.pop("R0007_UPLOAD_TOKEN", None)
    result["GIT_LITERAL_PATHSPECS"] = "1"
    return result


def git(root, *args, env=None, binary=False):
    return subprocess.check_output(["git", "-C", str(root), *args], env=env or child_env(), text=not binary)


def command(root, argv, evidence, label, env):
    record = {"label": label, "command": argv, "startedUtc": now(), "exitCode": None}
    dump(evidence / (label + ".json"), record)
    with (evidence / (label + ".log")).open("wb") as log:
        try:
            result = subprocess.run(argv, cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT)
            record["exitCode"] = result.returncode
        except Exception as error:
            record["failure"] = repr(error)
    record["finishedUtc"] = now()
    record["logSha256"] = digest((evidence / (label + ".log")).read_bytes())
    dump(evidence / (label + ".json"), record)
    if record["exitCode"] != 0:
        raise RuntimeError(label + " did not exit0; inspect retained producer record")


def upload_blob(content, token, expected, evidence, ordinal):
    record = {"path": expected["path"], "expectedBlobSha": expected["blobSha"], "bytes": len(content),
              "startedUtc": now(), "status": "UPLOAD_STARTED", "refUpdated": False}
    receipt = evidence / (f"upload-{ordinal:03d}.json")
    dump(receipt, record)
    body = json.dumps({"content": base64.b64encode(content).decode("ascii"), "encoding": "base64"}).encode("utf-8")
    request = urllib.request.Request("https://api.github.com/repos/" + REPOSITORY + "/git/blobs", data=body, method="POST",
                                     headers={"Authorization": "Bearer " + token, "Accept": "application/vnd.github+json",
                                              "Content-Type": "application/json", "X-GitHub-Api-Version": "2022-11-28",
                                              "User-Agent": "r0007-owned-materialization"})
    try:
        # No retry or alternate endpoint after an uncertain transport result.
        with urllib.request.build_opener(NoRedirect()).open(request, timeout=180) as response:
            result = json.loads(response.read())
            record["httpStatus"] = response.status
        record["observedBlobSha"] = result.get("sha")
        if result.get("sha") != expected["blobSha"]:
            raise ValueError("uploaded blob identity mismatch")
        record["status"] = "VERIFIED_BLOB_STORED_NO_REF_UPDATE"
    except urllib.error.HTTPError as error:
        record.update(status="HTTP_ERROR_STOPPED", httpStatus=error.code)
        raise RuntimeError("GitHub blob upload refused with HTTP " + str(error.code)) from None
    except Exception as error:
        record.update(status="UPLOAD_UNVERIFIED_STOPPED", failure=type(error).__name__)
        raise
    finally:
        record["finishedUtc"] = now()
        dump(receipt, record)
    return record


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--evidence-root", type=Path, required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--upload-blobs", action="store_true")
    args = parser.parse_args(argv)
    root, evidence = args.source_root.resolve(), args.evidence_root.resolve()
    if evidence.is_relative_to(root):
        parser.error("evidence-root must be outside the disposable source checkout")
    evidence.mkdir(parents=True, exist_ok=True)
    run = Path(tempfile.mkdtemp(prefix="attempt-", dir=evidence))
    summary = {"schema": "r0007-materialization/v1", "status": "STARTED", "startedUtc": now(), "refUpdated": False,
               "uploads": [], "workflowBlobsForConnector": [], "nativeAcceptance": "NONE_MATERIALIZATION_ONLY"}
    exit_code = 1
    try:
        manifest_path = args.manifest.resolve()
        if manifest_path != root / ".github/r0007-bootstrap/manifest.json":
            raise ValueError("manifest must be the exact reviewed seed path")
        raw = manifest_path.read_bytes()
        manifest = json.loads(raw)
        expected_manifest = os.environ.get("R0007_EXPECTED_MANIFEST_SHA256")
        if args.upload_blobs and (not expected_manifest or digest(raw) != expected_manifest):
            raise ValueError("workflow's manifest digest is absent or mismatched")
        if manifest.get("schema") != "r0007-materialization-input/v1" or manifest.get("repository") != REPOSITORY or manifest.get("branch") != BRANCH:
            raise ValueError("manifest scope mismatch")
        for key in ("baseCommit", "baseTree", "targetCommit", "targetTree"):
            if not re.fullmatch(r"[0-9a-f]{40}", manifest.get(key, "")):
                raise ValueError("invalid immutable " + key)
        if digest(Path(__file__).read_bytes()) != manifest["materializerSha256"]:
            raise ValueError("materializer bytes differ from reviewed manifest")
        patch = manifest_path.parent / "source.patch"
        if digest(patch.read_bytes()) != manifest["patchSha256"] or patch.stat().st_size != manifest["patchBytes"]:
            raise ValueError("source patch identity mismatch")
        changes = manifest["changes"]
        paths = [c["path"] for c in changes]
        if not paths or len(paths) != len(set(paths)) or any(not safe_path(p) or p in SEED_FILES for p in paths):
            raise ValueError("invalid, duplicate or seed-overlapping changed paths")
        for change in changes:
            after = change["after"]
            if after is not None and (after["mode"] not in {"100644", "100755"} or not re.fullmatch(r"[0-9a-f]{40}", after["blobSha"]) or not re.fullmatch(r"[0-9a-f]{64}", after["sha256"])):
                raise ValueError("unsupported candidate entry")
        summary.update(baseCommit=manifest["baseCommit"], expectedTargetCommit=manifest["targetCommit"], expectedTargetTree=manifest["targetTree"],
                       manifestSha256=digest(raw), changedPaths=paths, dryRun=args.dry_run, runId=os.environ.get("GITHUB_RUN_ID"),
                       runAttempt=os.environ.get("GITHUB_RUN_ATTEMPT"), branch=BRANCH)
        dump(run / "summary.json", summary)
        head = git(root, "rev-parse", "HEAD").strip()
        summary["seedCommit"] = head
        if git(root, "rev-parse", manifest["baseCommit"] + "^{tree}").strip() != manifest["baseTree"]:
            raise ValueError("base tree mismatch")
        if head != manifest["baseCommit"]:
            parents = git(root, "show", "-s", "--format=%P", "HEAD").split()
            seed_delta = set(filter(None, git(root, "diff", "--no-renames", "--name-only", "-z", manifest["baseCommit"], "HEAD").split("\0")))
            if parents != [manifest["baseCommit"]] or seed_delta != SEED_FILES:
                raise ValueError("seed is not exact base plus the four reviewed bootstrap files")
        elif args.upload_blobs:
            raise ValueError("upload requires an actual seed commit; base checkout is dry-only")
        dirty = git(root, "diff", "--name-only").strip() or git(root, "diff", "--cached", "--name-only").strip()
        untracked = set(git(root, "ls-files", "--others", "--exclude-standard").splitlines())
        if dirty or untracked - SEED_FILES:
            raise ValueError("disposable checkout has unrelated dirty/untracked state")
        if args.upload_blobs and (os.environ.get("GITHUB_REPOSITORY") != REPOSITORY or os.environ.get("GITHUB_REF") != "refs/heads/" + BRANCH or os.environ.get("GITHUB_EVENT_NAME") != "push"):
            raise ValueError("upload mode is restricted to the exact owned push workflow")
        index_env = child_env()
        index_env["GIT_INDEX_FILE"] = str(run / "candidate.index")
        command(root, ["git", "read-tree", manifest["baseCommit"]], run, "01-read-base-index", index_env)
        command(root, ["git", "update-index", "--refresh"], run, "01b-refresh-base-index-stat", index_env)
        command(root, ["git", "apply", "--check", "--index", str(patch)], run, "02-check-patch", index_env)
        command(root, ["git", "apply", "--index", str(patch)], run, "03-apply-patch", index_env)
        command(root, [sys.executable, "tools/build_native.py"], run, "04-real-native-builder", index_env)
        command(root, ["git", "add", "-A", "--", *paths], run, "05-stage-explicit-candidate-paths", index_env)
        unstaged = git(root, "diff", "--name-only", env=index_env).strip()
        extras = set(git(root, "ls-files", "--others", "--exclude-standard", env=index_env).splitlines()) - SEED_FILES
        if unstaged or extras:
            raise ValueError("builder/patch left unplanned tracked or untracked changes")
        tree = git(root, "write-tree", env=index_env).strip()
        summary["observedTargetTree"] = tree
        if tree != manifest["targetTree"]:
            raise ValueError("actual builder candidate tree differs from immutable target")
        for change in changes:
            after = change["after"]
            row = git(root, "ls-files", "--stage", "--", change["path"], env=index_env).strip()
            if after is None:
                if row:
                    raise ValueError("deleted entry survived in candidate index")
            else:
                if not row or row.split()[:2] != [after["mode"], after["blobSha"]]:
                    raise ValueError("candidate mode/blob differs: " + change["path"])
                content = git(root, "cat-file", "blob", after["blobSha"], binary=True)
                if len(content) != after["bytes"] or digest(content) != after["sha256"]:
                    raise ValueError("candidate bytes differ: " + change["path"])
        summary["status"] = "EXACT_TREE_RECONSTRUCTED_NO_REF_UPDATE"
        dump(run / "summary.json", summary)
        if args.upload_blobs:
            token = os.environ.get("R0007_UPLOAD_TOKEN")
            if not token:
                raise ValueError("job token unavailable; no upload attempted")
            candidates = []
            for change in changes:
                if change["after"] is None:
                    continue
                entry = {"path": change["path"], **change["after"]}
                if change["path"].startswith(".github/workflows/"):
                    summary["workflowBlobsForConnector"].append(entry)
                else:
                    candidates.append(entry)
            # Prove large-blob API transport first, without moving any ref.
            for ordinal, entry in enumerate(sorted(candidates, key=lambda e: (-e["bytes"], e["path"])), 1):
                content = git(root, "cat-file", "blob", entry["blobSha"], binary=True)
                summary["uploads"].append(upload_blob(content, token, entry, run, ordinal))
                dump(run / "summary.json", summary)
            summary["status"] = "BLOBS_VERIFIED_CONNECTOR_FINALIZATION_REQUIRED"
        exit_code = 0
    except Exception as error:
        summary.update(status="STOPPED_NO_REF_UPDATE", failure=repr(error))
    summary.update(finishedUtc=now(), exitCode=exit_code)
    dump(run / "summary.json", summary)
    # This short line is deliberately safe to retrieve from workflow job logs.
    print("R0007_MATERIALIZATION_RESULT " + json.dumps({"status": summary["status"], "exitCode": exit_code,
          "seedCommit": summary.get("seedCommit"), "targetTree": summary.get("observedTargetTree"),
          "verifiedBlobCount": len(summary["uploads"]), "workflowBlobCount": len(summary["workflowBlobsForConnector"]),
          "refUpdated": False, "nativeAcceptance": "NONE"}), flush=True)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
