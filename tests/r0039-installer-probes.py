"""R0039 (issue 106) hosted discriminators R39-07 (B1, real compiler custody) and R39-08 (B2, end to end).

Hosted-only native recipe (registered as an exclusion with this recipe in tests/regression-population.json):
it runs on GitHub windows-2022 / windows-2025 through .github/workflows/r0039-installer-probes.yml, whose TEMP
ancestry the installer admits. Fixtures only: every installer write is redirected under --fixture-parent, release
metadata and downloads are fixture spies, Read-Host is the host's own, nothing is installed and no browser runs.
install.ps1 is read, never modified.

    python tests/r0039-installer-probes.py --host-name ps51|ps7 --host-exe <exe> --source install.ps1
        --preset presets/salah-widget.tablissng.json --fixture-parent <fresh dir> --output <receipt.json>

Exit 0 when both rows read MET, 1 when either row is a FINDING or a GAP (the receipt says which and why).
"""
import argparse
import json
import os
import subprocess
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
B1 = ROOT / "tests" / "r0039-b1-helper-type-reuse.ps1"
B2 = ROOT / "tests" / "r0039-b2-entry.ps1"


def run(argv, env, stdin_text=None, timeout=600):
    p = subprocess.run(argv, env=env, input=stdin_text, capture_output=True, text=True, timeout=timeout,
                       stdin=None if stdin_text is not None else subprocess.DEVNULL)
    out = p.stdout
    start = out.find("{")
    parsed = None
    if start >= 0:
        try:
            parsed = json.loads(out[start:])
        except ValueError:
            parsed = None
    return {"exit": p.returncode, "result": parsed, "stdoutHead": out[:start].strip() if start >= 0 else out[-2000:],
            "stderrTail": p.stderr[-2000:]}


def fresh(parent, label):
    d = Path(parent) / ("r0039-" + label + "-" + uuid.uuid4().hex[:8])
    d.mkdir()
    return d


def main():
    ap = argparse.ArgumentParser()
    for name in ("--host-name", "--host-exe", "--source", "--preset", "--fixture-parent", "--output"):
        ap.add_argument(name, required=True)
    a = ap.parse_args()
    source = str(Path(a.source).resolve())
    base = dict(os.environ)
    cases = {}

    # B1: real compiler custody (the row), plus fixture-compiler and single-load controls.
    for mode in ("file", "iex"):
        for compiler, order in (("real", "S1,S2"), ("fixture", "S1,S2")):
            tmp = fresh(a.fixture_parent, "b1")
            env = dict(base, TEMP=str(tmp), TMP=str(tmp), R0039_B1_SOURCE=source, R0039_B1_MODE=mode,
                       R0039_B1_COMPILER=compiler, R0039_B1_ORDER=order)
            argv = [a.host_exe, "-NoProfile", "-NonInteractive"]
            argv += ["-File", str(B1)] if mode == "file" else ["-Command", "Invoke-Expression ([IO.File]::ReadAllText('%s'))" % B1]
            cases["b1-%s-%s" % (mode, compiler)] = run(argv, env)
    tmp = fresh(a.fixture_parent, "b1")
    cases["b1-control-S2"] = run([a.host_exe, "-NoProfile", "-NonInteractive", "-File", str(B1)],
                                 dict(base, TEMP=str(tmp), TMP=str(tmp), R0039_B1_SOURCE=source, R0039_B1_MODE="file",
                                      R0039_B1_COMPILER="real", R0039_B1_ORDER="S2"))

    # B2: (i) -NonInteractive; (ii) redirected input 'all' then end of input.
    for label, extra, stdin_text in (("b2-i-noninteractive", ["-NonInteractive"], None), ("b2-ii-ended-input", [], "all\n")):
        fx = fresh(a.fixture_parent, "b2")
        env = dict(base, R0039_B2_SOURCE=source, R0039_B2_PRESET=str(Path(a.preset).resolve()), R0039_B2_FIXTURE=str(fx))
        cases[label] = run([a.host_exe, "-NoProfile"] + extra + ["-File", str(B2)], env, stdin_text)

    def outcome(key):
        r = cases[key]["result"] or {}
        return r.get("outcome")

    # R39-07 verdict.
    real = [outcome("b1-file-real"), outcome("b1-iex-real")]
    control = outcome("b1-control-S2")
    if all(o == "reuse-confirmed: second call observed S1" for o in real) and control == "single-load control: observed S2":
        r07 = ("MET", "real custody: S1 observed after the S2 call in -File and iex; single-load control observed S2")
    elif any(o == "no-reuse: second call observed S2" for o in real):
        r07 = ("FINDING", "real custody did not reuse the loaded type; contradicts the workstation B1 result")
    else:
        r07 = ("GAP", "real custody inconclusive (for example TEMP ancestry refused) or control failed: %r / %r" % (real, control))

    # R39-08 verdict.
    i = cases["b2-i-noninteractive"]["result"] or {}
    ii = cases["b2-ii-ended-input"]["result"] or {}
    i_ok = (i.get("entryExit") == "terminating-error" and "NonInteractive" in (i.get("entryError") or "")
            and not i.get("events") and i.get("createdEntryCount") == 0)
    ii_ok = (ii.get("handoffReached") is True and ii.get("storeOpenCount") == 0 and ii.get("fallbackWarning") is False
             and ii.get("entryExit") == 0 and ii.get("retainedBundleUnderFixtureHome") is True
             and any(str(e).startswith("metadata:") for e in ii.get("events", []))
             and any(str(e).startswith("download:https://example.invalid/tabliss-chromium.zip") for e in ii.get("events", [])))
    if i_ok and ii_ok:
        r08 = ("MET", "(i) stops at the selection prompt with no effect; (ii) hand-off reached, ended input acknowledged, no store fallback, exit 0, bundle retained in the fixture")
    elif ii.get("handoffReached") and ii.get("storeOpenedAfterHandoff"):
        r08 = ("FINDING", "store page opened after a hand-off under ended input: the registry hypothesis is reachable")
    elif i.get("events") or i.get("createdEntryCount"):
        r08 = ("FINDING", "-NonInteractive run produced an effect before stopping")
    else:
        r08 = ("GAP", "hand-off not reached or harness did not complete (see case results)")

    receipt = {"schema": "r0039-installer-probes/1", "hostName": a.host_name, "runner": base.get("ImageOS") or base.get("RUNNER_NAME"),
               "rows": {"R39-07": {"verdict": r07[0], "reason": r07[1]}, "R39-08": {"verdict": r08[0], "reason": r08[1]}},
               "cases": cases}
    Path(a.output).write_text(json.dumps(receipt, indent=1) + "\n", encoding="utf-8")
    print("R39-07 %s: %s" % r07)
    print("R39-08 %s: %s" % r08)
    return 0 if r07[0] == "MET" and r08[0] == "MET" else 1


if __name__ == "__main__":
    sys.exit(main())
