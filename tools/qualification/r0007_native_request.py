#!/usr/bin/env python3
"""Select a finite R0007 hosted acquisition profile; never accept command text."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import r0007_native as native

REQUEST = "tests/rlgwo/R0007-native-request.json"
BARRIERS = ["NE07-recovery24", "NE07-recovery12", "NE07-dst-recovery24",
            "NE07-dst-recovery12", "NE07-mut-remove-next-dirty"]
FIREFOX_FAILED_HEALTHY = ["NE07-ordinary24", "NE07-recovery24", "NE07-equal-polar",
                        "NE07-spring24", "NE07-fall24", "NE07-dst-recovery12",
                        "NE07-wall-ordinary-control"]
MUTANTS = ["NE07-mut-hardcoded-fajr", "NE07-mut-name-order", "NE07-mut-lost-date",
           "NE07-mut-independent-label", "NE07-mut-ambiguous-epoch", "NE07-mut-remove-next-dirty",
           "NE07-mut-epoch-plus24", "NE07-mut-wall-spring", "NE07-mut-wall-fall"]


def plan_request(request, recipe):
    required = {"schema", "profile", "requestId", "reason"}
    if not isinstance(request, dict) or set(request) != required:
        raise ValueError("native request must contain only schema/profile/requestId/reason")
    if request["schema"] != "r0007-native-request/v1":
        raise ValueError("unsupported native request schema")
    if any(not isinstance(request[k], str) or not request[k].strip() or len(request[k]) > 1000
           for k in ("profile", "requestId", "reason")):
        raise ValueError("native request text fields must be nonempty bounded strings")
    profile = request["profile"]
    if profile == "full":
        engines, video_only = ["chromium", "firefox"], False
        requested = (recipe["execution"]["defaultCaseIds"]
                     + recipe["execution"]["conditionalPreservationCaseIds"]
                     + recipe["execution"]["mutationCaseIds"])
    elif profile == "firefox-video-diagnostic":
        engines, video_only = ["firefox"], True
        requested = ["NE07-ordinary24", "NE07-spring24", "NE07-recovery24"]
    elif profile == "firefox-affected":
        engines, video_only = ["firefox"], True
        requested = FIREFOX_FAILED_HEALTHY + MUTANTS
    elif profile == "firefox-reordered-timing":
        engines, video_only = ["firefox"], True
        requested = ["NE07-reordered24"]
    elif profile == "firefox-reordered-companions":
        engines, video_only = ["firefox"], True
        requested = ["NE07-mut-hardcoded-fajr", "NE07-mut-name-order",
                     "NE07-mut-lost-date", "NE07-mut-independent-label"]
    elif profile == "chromium-recovery":
        engines, video_only = ["chromium"], False
        requested = BARRIERS
    elif profile == "chromium-recovery-sec-only":
        engines, video_only = ["chromium"], False
        requested = BARRIERS + ["NE07-mut-dst-sec-only"]
    elif profile == "firefox-dst-sec-only":
        engines, video_only = ["firefox"], True
        requested = ["NE07-mut-dst-sec-only"]
    else:
        raise ValueError("unknown native request profile")
    selected = native.select_cases(recipe, requested)
    case_ids = [case["caseId"] for case in selected]
    arguments = [value for engine in engines for value in ("--engine", engine)] + ["--headed"]
    if video_only:
        arguments.append("--video-only")
    arguments += [value for case_id in case_ids for value in ("--case-id", case_id)]
    return {"profile": profile, "engines": engines, "videoOnly": video_only,
            "requestedCaseIds": requested, "selectedCaseIds": case_ids,
            "plannedCells": len(engines) * len(case_ids), "arguments": arguments}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--evidence-root", type=Path, required=True)
    args = parser.parse_args(argv)
    root, evidence = args.source_root.resolve(), args.evidence_root.resolve()
    if evidence.is_relative_to(root):
        parser.error("evidence-root must be outside source-root")
    evidence.mkdir(parents=True, exist_ok=True)
    receipt = {"schema": "r0007-native-request-selection/v1", "startedUtc": native.utc(),
               "nativeAcceptance": "NONE_SELECTION_ONLY", "launched": False}
    path = evidence / "request-selection.json"
    exit_code = 1
    try:
        identity = native.clean_identity(root)
        request_path = root / REQUEST
        if request_path.is_symlink():
            raise ValueError("native request cannot be a symlink")
        if request_path.exists():
            request_bytes = request_path.read_bytes()
            committed = native.subprocess.check_output(["git", "-C", str(root), "show", identity["commit"] + ":" + REQUEST])
            if request_bytes != committed:
                raise ValueError("native request differs from its committed bytes")
            request = json.loads(request_bytes)
            receipt["requestSha256"] = native.sha(request_path)
        else:
            request = {"schema": "r0007-native-request/v1", "profile": "full", "requestId": "legacy-no-request",
                       "reason": "Preserve the existing full selection when no request is committed."}
            receipt["requestSha256"] = None
        recipe = json.loads((root / native.DEFAULT_RECIPE).read_text(encoding="utf-8"))
        selection = plan_request(request, recipe)
        receipt.update(identity=identity, request=request, selection=selection,
                       selectorSha256=native.sha(Path(__file__)), status="PLANNED")
        native.write(path, receipt)
        receipt["launched"] = True
        native.write(path, receipt)
        exit_code = native.main(["--source-root", str(root), "--evidence-root", str(evidence), *selection["arguments"]])
        receipt["status"] = "COLLECTED_SOURCE_SCOPES_ONLY" if exit_code == 0 else "ACQUISITION_NOT_ACCEPTED"
    except Exception as error:
        receipt.update(status="FAILED", failure=repr(error))
    finally:
        receipt.update(exitCode=exit_code, finishedUtc=native.utc())
        native.write(path, receipt)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
