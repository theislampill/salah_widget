#!/usr/bin/env python3
"""Reconstruct a hash-bound R0007 tree; optionally publish one bounded Git ref.

Run only inside the disposable seed checkout. Dry mode requires no token or
network. Publication mode is locked to the commissioned repository/ref.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tempfile

REPOSITORY = "theislampill/salah_widget"
BRANCH = "pro/r0007-explicit-next-event-state-20261106"
REMOTE = "https://github.com/theislampill/salah_widget.git"
REF = "refs/heads/" + BRANCH
SEED_FILES = {".github/workflows/r0007-materialize.yml", ".github/r0007-bootstrap/materialize.py",
              ".github/r0007-bootstrap/manifest.json", ".github/r0007-bootstrap/source.patch"}
TARGET_WORKFLOWS = {".github/workflows/r0007-native.yml", ".github/workflows/r0007-public-delivery.yml"}
FINALIZATION_PATHS = SEED_FILES | TARGET_WORKFLOWS


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
    # Controlled children must not inherit independent Git diagnostic sinks.
    # Token-free children stay token-free; the push credential is added later.
    result = {key: value for key, value in os.environ.items()
              if not key.startswith("GIT_TRACE") and key != "GIT_CURL_VERBOSE"}
    result.pop("R0007_UPLOAD_TOKEN", None)
    result.pop("R0007_PUSH_TOKEN", None)
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


def validate_seed_chain(root, head, manifest, upload):
    chain = manifest.get("seedAncestors")
    base = manifest["baseCommit"]
    if (not isinstance(chain, list) or len(chain) != 3 or len(set(chain)) != 3
            or any(not isinstance(v, str) or not re.fullmatch(r"[0-9a-f]{40}", v) for v in chain)
            or chain[-1] != base or chain[0] != manifest["expectedSeedParent"]):
        raise ValueError("seed ancestry must bind exactly two prior seeds and original base")
    if git(root, "rev-parse", base + "^{tree}").strip() != manifest["baseTree"]:
        raise ValueError("base tree mismatch")
    for index, commit in enumerate(chain):
        if git(root, "cat-file", "-t", commit).strip() != "commit":
            raise ValueError("seed ancestor is not an immutable commit")
        if index < len(chain) - 1:
            parents = git(root, "show", "-s", "--format=%P", commit).split()
            delta = set(filter(None, git(root, "diff", "--no-renames", "--name-only", "-z", base, commit).split("\0")))
            if parents != [chain[index + 1]] or delta != SEED_FILES:
                raise ValueError("prior seed ancestry or cumulative bootstrap delta differs")
    if head == base:
        if upload:
            raise ValueError("base checkout cannot publish")
        return
    parents = git(root, "show", "-s", "--format=%P", head).split()
    delta = set(filter(None, git(root, "diff", "--no-renames", "--name-only", "-z", base, head).split("\0")))
    if parents != [chain[0]] or delta != SEED_FILES:
        raise ValueError("executing seed parent or cumulative bootstrap delta differs")


def tree_entries(root, tree):
    rows = git(root, "ls-tree", "-r", "-z", tree, binary=True).split(b"\0")
    result = {}
    for row in rows:
        if not row:
            continue
        prefix, raw_path = row.split(b"\t", 1)
        mode, kind, sha = prefix.decode("ascii").split()
        path = raw_path.decode("utf-8")
        result[path] = (mode, kind, sha)
    return result


def build_intermediate(root, target_tree, seed, evidence):
    target = tree_entries(root, target_tree)
    seed_entries = tree_entries(root, seed)
    preserved = {p: entry for p, entry in seed_entries.items() if p.startswith(".github/workflows/") or p in SEED_FILES}
    if not SEED_FILES <= preserved.keys() or any(not safe_path(p) or entry[0] != "100644" or entry[1] != "blob"
                                               for p, entry in preserved.items()):
        raise ValueError("seed workflow/bootstrap entries are not supported regular files")
    expected = {p: entry for p, entry in target.items() if not p.startswith(".github/workflows/") and p not in SEED_FILES}
    expected.update(preserved)
    index_env = child_env()
    index_env["GIT_INDEX_FILE"] = str(Path(evidence) / "intermediate.index")
    git(root, "read-tree", target_tree, env=index_env)
    for path in sorted(p for p in target if p.startswith(".github/workflows/") or p in SEED_FILES):
        git(root, "update-index", "--force-remove", "--", path, env=index_env)
    for path, (mode, _kind, sha) in sorted(preserved.items()):
        git(root, "update-index", "--add", "--cacheinfo", mode, sha, path, env=index_env)
    tree = git(root, "write-tree", env=index_env).strip()
    if tree_entries(root, tree) != expected:
        raise ValueError("intermediate tree differs from exact target/seed equation")
    delta = set(filter(None, git(root, "diff", "--no-renames", "--name-only", "-z", target_tree, tree).split("\0")))
    if delta != FINALIZATION_PATHS:
        raise ValueError("connector finalization is not the exact six-path delta")
    workflow_tree = git(root, "rev-parse", seed + ":.github/workflows").strip()
    if git(root, "rev-parse", tree + ":.github/workflows").strip() != workflow_tree:
        raise ValueError("intermediate changed the seed workflow subtree")
    result = {"intermediateTree": tree, "seedWorkflowTree": workflow_tree,
              "finalizationPaths": sorted(delta), "intermediateState": "EXACT_TARGET_PRODUCT_WITH_SEED_WORKFLOWS"}
    dump(Path(evidence) / "intermediate-tree.json", result)
    return result


def guard_script(intent_path, receipt_path):
    expected_digest = digest(Path(intent_path).read_bytes())
    return "#!" + sys.executable + "\n" + '''import hashlib,json,os,re,sys
from pathlib import Path
INTENT = Path(''' + repr(str(intent_path)) + ''')
RECEIPT = Path(''' + repr(str(receipt_path)) + ''')
EXPECTED_DIGEST = ''' + repr(expected_digest) + '''
REMOTE = ''' + repr(REMOTE) + '''
REF = ''' + repr(REF) + '''
def finish(reason, accepted=False):
    result = {'schema':'r0007-pack-guard/v1','status':'ACCEPTED' if accepted else 'REFUSED','reason':reason}
    try:
        fd = os.open(RECEIPT, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd,'w') as stream:
            stream.write(json.dumps(result)+'\\n')
    except FileExistsError:
        sys.exit(1)
    sys.exit(0 if accepted else 1)
try:
    raw = INTENT.read_bytes()
    if hashlib.sha256(raw).hexdigest() != EXPECTED_DIGEST:
        finish('INTENT_CHANGED')
    intent = json.loads(raw)
    if intent.get('remote') != REMOTE or intent.get('ref') != REF:
        finish('INTENT_SCOPE_MISMATCH')
    if any(not isinstance(intent.get(k),str) or not re.fullmatch('[0-9a-f]{40}',intent[k])
           for k in ['expectedRemote','newCommit']):
        finish('INVALID_INTENT_IDENTITY')
    if len(sys.argv) != 3 or sys.argv[1:] != [REMOTE,REMOTE]:
        finish('REMOTE_MISMATCH')
    raw_input = sys.stdin.buffer.read(4097)
    if len(raw_input) > 4096:
        finish('INPUT_TOO_LONG')
    lines = raw_input.decode('ascii').splitlines()
    if len(lines) != 1:
        finish('UPDATE_COUNT_MISMATCH')
    fields = lines[0].split()
    if len(fields) != 4:
        finish('INVALID_UPDATE')
    if fields[0] != intent['newCommit'] or fields[1] != intent['newCommit']:
        finish('NEW_ID_MISMATCH')
    if fields[2] != REF:
        finish('REF_MISMATCH')
    if fields[3] != intent['expectedRemote']:
        finish('OLD_ID_MISMATCH')
    finish('EXACT_SINGLE_UPDATE', True)
except Exception:
    finish('GUARD_EXCEPTION')
'''


def askpass_script():
    username_prompt = "Username for '" + REMOTE + "':"
    password_prompt = "Password for '" + REMOTE.replace("https://", "https://x-access-token@", 1) + "':"
    return "#!" + sys.executable + "\n" + '''import os,sys
prompt = sys.argv[1].strip() if len(sys.argv) == 2 else ''
if prompt == ''' + repr(username_prompt) + ''':
    print('x-access-token')
elif prompt == ''' + repr(password_prompt) + ''':
    token = os.environ.get('R0007_PUSH_TOKEN')
    if not token:
        sys.exit(1)
    print(token)
else:
    sys.exit(1)
'''


def private_write(path, content, mode=0o600):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
    with os.fdopen(fd, "wb") as stream:
        stream.write(content)


def remote_head(root):
    result = subprocess.run(["git", "-C", str(root), "ls-remote", "--exit-code", "--heads", REMOTE, REF],
                            env=child_env(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
    if result.returncode != 0:
        return None
    lines = result.stdout.decode("ascii", errors="strict").splitlines()
    if len(lines) != 1:
        return None
    parts = lines[0].split()
    if len(parts) != 2 or parts[1] != REF or not re.fullmatch(r"[0-9a-f]{40}", parts[0]):
        return None
    return parts[0]


def publish_intermediate(root, intermediate_commit, expected_seed, evidence, token):
    root, evidence = Path(root).resolve(), Path(evidence).resolve()
    receipt = evidence / "push-result.json"
    if receipt.exists():
        return {"status": "PUSH_UNCERTAIN", "refUpdated": None, "reason": "EXISTING_PUBLICATION_RECEIPT"}
    record = {"schema": "r0007-pack-publication/v1", "status": "REFUSED_BEFORE_PUSH", "refUpdated": False,
              "expectedRemote": expected_seed, "newCommit": intermediate_commit, "ref": REF,
              "startedUtc": now(), "pushAttempts": 0}
    dump(receipt, record)
    askpass = None
    started = False
    try:
        if any(not isinstance(v, str) or not re.fullmatch(r"[0-9a-f]{40}", v) for v in [intermediate_commit, expected_seed]):
            raise ValueError("invalid immutable publication identity")
        if not token or git(root, "cat-file", "-t", intermediate_commit).strip() != "commit":
            raise ValueError("publication credential or commit unavailable")
        if git(root, "show", "-s", "--format=%P", intermediate_commit).split() != [expected_seed]:
            raise ValueError("intermediate is not a single forward child of expected seed")
        # Read names only: existing auth values must never reach captured diagnostics.
        keys = git(root, "config", "--includes", "--name-only", "--list").lower().splitlines()
        if any(k == "core.hookspath" or k.startswith("credential.") or k.startswith("trace2.")
               or (k.startswith("url.") and (k.endswith(".insteadof") or k.endswith(".pushinsteadof")))
               or (k.startswith("http.") and k.endswith("extraheader")) for k in keys):
            raise ValueError("existing hook, rewrite, credential or diagnostic configuration requires review")
        tls = subprocess.run(["git", "-C", str(root), "config", "--get-urlmatch", "http.sslVerify", REMOTE],
                             env=child_env(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if tls.returncode not in (0, 1) or (tls.returncode == 0 and tls.stdout.strip().lower() not in (b"true", b"yes", b"on", b"1")):
            raise ValueError("TLS verification configuration requires review")
        if os.environ.get("GIT_SSL_NO_VERIFY", "").lower() not in ("", "0", "false", "no"):
            raise ValueError("TLS verification environment requires review")
        git_dir = Path(git(root, "rev-parse", "--absolute-git-dir").strip()).resolve()
        hooks = git_dir / "hooks"
        hook = hooks / "pre-push"
        if hooks.is_symlink() or hook.exists() or hook.is_symlink():
            raise ValueError("existing pre-push gate requires review")
        observed = remote_head(root)
        record["preflightRemote"] = observed
        if observed != expected_seed:
            raise ValueError("remote head differs from exact executing seed")
        private = evidence / "push-private"
        private.mkdir(mode=0o700)
        intent_path, guard_receipt = private / "intent.json", private / "guard-receipt.json"
        intent = {"schema": "r0007-pack-push-intent/v1", "remote": REMOTE, "ref": REF,
                  "expectedRemote": expected_seed, "newCommit": intermediate_commit}
        private_write(intent_path, (json.dumps(intent, sort_keys=True) + "\n").encode())
        guard = guard_script(intent_path, guard_receipt).encode()
        private_write(private / "pre-push", guard, 0o700)
        hooks.mkdir(exist_ok=True)
        private_write(hook, guard, 0o700)
        askpass = private / "askpass"
        private_write(askpass, askpass_script().encode(), 0o700)
        record.update(intentSha256=digest(intent_path.read_bytes()), guardSha256=digest(guard), status="PUSH_UNCERTAIN",
                      refUpdated=None, pushAttempts=1)
        dump(receipt, record)
        push_env = child_env()
        push_env.update(R0007_PUSH_TOKEN=token, GIT_ASKPASS=str(askpass), GIT_TERMINAL_PROMPT="0", LC_ALL="C")
        argv = ["git", "-C", str(root), "-c", "credential.useHttpPath=true", "-c", "http.followRedirects=false",
                "push", "--porcelain", "--no-follow-tags", "--recurse-submodules=no", REMOTE,
                intermediate_commit + ":" + REF]
        started = True
        try:
            pushed = subprocess.run(argv, env=push_env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=600)
            record.update(pushExitCode=pushed.returncode, stdoutBytes=len(pushed.stdout), stdoutSha256=digest(pushed.stdout),
                          stderrBytes=len(pushed.stderr), stderrSha256=digest(pushed.stderr))
        except subprocess.TimeoutExpired:
            record["failureClass"] = "TIMEOUT"
            pushed = None
        except Exception:
            record["failureClass"] = "PUSH_PROCESS_EXCEPTION"
            pushed = None
        finally:
            push_env.pop("R0007_PUSH_TOKEN", None)
        dump(receipt, record)
        try:
            observed = remote_head(root)
            record["readbackRemote"] = observed
        except Exception:
            observed = None
            record["readbackClass"] = "UNAVAILABLE"
        guard_result = json.loads(guard_receipt.read_bytes()) if guard_receipt.exists() else {}
        record["guardAccepted"] = guard_result.get("status") == "ACCEPTED"
        if pushed is not None and pushed.returncode == 0 and observed == intermediate_commit and record["guardAccepted"]:
            record.update(status="REMOTE_REF_VERIFIED_INTERMEDIATE", refUpdated=True)
    except Exception:
        record.update(status="PUSH_UNCERTAIN" if started else "REFUSED_BEFORE_PUSH", refUpdated=None if started else False,
                      failureClass="PUBLICATION_EXCEPTION" if started else "PREFLIGHT_REFUSAL")
    finally:
        if askpass is not None:
            try:
                askpass.unlink(missing_ok=True)
                record["askpassRemoved"] = True
            except OSError:
                record["askpassRemoved"] = False
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
    mode.add_argument("--publish-branch", action="store_true")
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
        if args.publish_branch and (not expected_manifest or digest(raw) != expected_manifest):
            raise ValueError("workflow's manifest digest is absent or mismatched")
        if manifest.get("schema") != "r0007-pack-input/v1" or manifest.get("repository") != REPOSITORY or manifest.get("branch") != BRANCH:
            raise ValueError("manifest scope mismatch")
        for key in ("baseCommit", "baseTree", "targetCommit", "targetTree", "expectedSeedParent"):
            if not re.fullmatch(r"[0-9a-f]{40}", manifest.get(key, "")):
                raise ValueError("invalid immutable " + key)
        if digest(Path(__file__).read_bytes()) != manifest["materializerSha256"]:
            raise ValueError("materializer bytes differ from reviewed manifest")
        patch = manifest_path.parent / "source.patch"
        if digest(patch.read_bytes()) != manifest["patchSha256"] or patch.stat().st_size != manifest["patchBytes"]:
            raise ValueError("source patch identity mismatch")
        if manifest.get("finalizationPaths") != sorted(FINALIZATION_PATHS) or manifest.get("refUpdatesAllowed") != [REF]:
            raise ValueError("publication effect/finalization scope mismatch")
        changes = manifest["changes"]
        paths = [c["path"] for c in changes]
        if not paths or len(paths) != len(set(paths)) or any(not safe_path(p) or p in SEED_FILES for p in paths):
            raise ValueError("invalid, duplicate or seed-overlapping changed paths")
        for change in changes:
            after = change["after"]
            if after is not None and (after["mode"] not in {"100644", "100755"} or not re.fullmatch(r"[0-9a-f]{40}", after["blobSha"]) or not re.fullmatch(r"[0-9a-f]{64}", after["sha256"])):
                raise ValueError("unsupported candidate entry")
        summary.update(baseCommit=manifest["baseCommit"], expectedSeedParent=manifest["expectedSeedParent"],
                       expectedTargetCommit=manifest["targetCommit"], expectedTargetTree=manifest["targetTree"],
                       manifestSha256=digest(raw), seedAncestors=manifest["seedAncestors"], finalizationPaths=manifest["finalizationPaths"], changedPaths=paths, dryRun=args.dry_run, runId=os.environ.get("GITHUB_RUN_ID"),
                       runAttempt=os.environ.get("GITHUB_RUN_ATTEMPT"), branch=BRANCH)
        dump(run / "summary.json", summary)
        head = git(root, "rev-parse", "HEAD").strip()
        summary["seedCommit"] = head
        if git(root, "rev-parse", manifest["baseCommit"] + "^{tree}").strip() != manifest["baseTree"]:
            raise ValueError("base tree mismatch")
        validate_seed_chain(root, head, manifest, args.publish_branch)
        dirty = git(root, "diff", "--name-only").strip() or git(root, "diff", "--cached", "--name-only").strip()
        untracked = set(git(root, "ls-files", "--others", "--exclude-standard").splitlines())
        if dirty or untracked - SEED_FILES:
            raise ValueError("disposable checkout has unrelated dirty/untracked state")
        if args.publish_branch and (os.environ.get("GITHUB_REPOSITORY") != REPOSITORY or os.environ.get("GITHUB_REF") != "refs/heads/" + BRANCH or os.environ.get("GITHUB_EVENT_NAME") != "push"):
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
        summary["workflowBlobsForConnector"] = [{"path": change["path"], **change["after"]}
                                                for change in changes
                                                if change["path"] in TARGET_WORKFLOWS and change["after"] is not None]
        if len(summary["workflowBlobsForConnector"]) != 2:
            raise ValueError("two final workflow blobs must be present")
        summary["status"] = "EXACT_TREE_RECONSTRUCTED_NO_REF_UPDATE"
        dump(run / "summary.json", summary)
        if head != manifest["baseCommit"]:
            intermediate = build_intermediate(root, tree, head, run)
            summary.update(intermediate)
        else:
            summary["intermediateState"] = "DRY_BASE_TARGET_ONLY"
        if args.publish_branch:
            if os.environ.get("GITHUB_SHA") != head or os.environ.get("GITHUB_RUN_ATTEMPT") != "1":
                raise ValueError("publication requires exact executing seed and first run attempt")
            token = os.environ.get("R0007_UPLOAD_TOKEN")
            if not token:
                raise ValueError("job token unavailable; no publication attempted")
            commit_env = child_env()
            commit_env.update(GIT_AUTHOR_NAME="R0007 materialization", GIT_AUTHOR_EMAIL="r0007@users.noreply.github.com",
                              GIT_COMMITTER_NAME="R0007 materialization", GIT_COMMITTER_EMAIL="r0007@users.noreply.github.com")
            message = ("R0007: stage exact product objects for connector finalization\n\nTarget tree: " + tree
                       + "\n\nCo-Authored-By: ChatGPT <noreply@openai.com>\n")
            intermediate_commit = subprocess.check_output(
                ["git", "-C", str(root), "commit-tree", summary["intermediateTree"], "-p", head],
                input=message.encode("utf-8"), env=commit_env).decode("ascii").strip()
            summary.update(intermediateCommit=intermediate_commit, status="PUBLICATION_MAY_START", refUpdated=None)
            dump(run / "summary.json", summary)
            publication = publish_intermediate(root, intermediate_commit, head, run, token)
            summary.update(publication=publication, refUpdated=publication["refUpdated"])
            if publication["status"] != "REMOTE_REF_VERIFIED_INTERMEDIATE":
                raise RuntimeError("Git publication not verified; inspect structured outcome")
            summary["status"] = "INTERMEDIATE_VERIFIED_CONNECTOR_FINALIZATION_REQUIRED"
        else:
            summary["status"] = "DRY_RECONSTRUCTION_VERIFIED"
        exit_code = 0
    except Exception as error:
        summary.update(status="STOPPED_PUBLICATION_NOT_VERIFIED", failure=type(error).__name__)
    summary.update(finishedUtc=now(), exitCode=exit_code)
    dump(run / "summary.json", summary)
    # This short line is deliberately safe to retrieve from workflow job logs.
    print("R0007_MATERIALIZATION_RESULT " + json.dumps({"status": summary["status"], "exitCode": exit_code,
          "seedCommit": summary.get("seedCommit"), "targetTree": summary.get("observedTargetTree"),
          "verifiedBlobCount": len(summary["uploads"]), "workflowBlobCount": len(summary["workflowBlobsForConnector"]),
          "refUpdated": summary["refUpdated"], "intermediateCommit": summary.get("intermediateCommit"), "nativeAcceptance": "NONE"}), flush=True)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
