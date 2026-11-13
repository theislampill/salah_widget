"""R0039 (issue 106) A2: Bash release-asset tier characterisation and parity with PowerShell.

`install.sh` `select_asset` runs an embedded Python program against the GitHub
`/releases/latest` metadata. The repository's Bash suites replace `select_asset`
with stubs, so its tiers were untested. This test extracts that exact program
from `install.sh`, replaces `urllib.request.urlopen` in-process with fixture
metadata (no network, no files written), and checks it against the ten selector
rows of `tests/install-powershell-routes.ps1` (six selections, four refusals),
which are parsed from that file so the two cannot drift apart silently.

Parity relation (issue 106 section 3.3): for each row, either both installers
select an asset with the same `name`, or both refuse. Refusal message text is
NOT part of the relation; the two installers word their refusals differently.

There is no RED: this is a characterisation test. Its discriminator is the
tier-reorder mutant below, which must disagree with the PowerShell rows.
The URL-scheme row records current Bash behaviour (no https requirement on the
download URL; PowerShell's `Download-Asset` refuses non-https). It documents a
divergence; it is not an endorsement.
"""
import contextlib
import io
import json
import os
import re
import sys
import unittest
import urllib.request
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
INSTALL_SH = Path(os.environ.get("R0039_INSTALL_SH", ROOT / "install.sh"))
ROUTES_PS1 = ROOT / "tests" / "install-powershell-routes.ps1"

PROGRAM_RE = re.compile(
    r"select_asset\(\) \{.*?printf '%s\\n' '(import json, re, sys, urllib\.request.*?)'\)\n\}", re.S)


def extract_program(text):
    matches = PROGRAM_RE.findall(text)
    if len(matches) != 1:
        raise AssertionError("expected exactly one select_asset program, found %d" % len(matches))
    # Undo the shell single-quote escaping ('"'"' inside a single-quoted word is one ').
    return matches[0].replace("'\"'\"'", "'")


def _ps_names(body):
    return re.findall(r"'([^']*)'", body)


def parse_powershell_rows(text):
    """Return (selections, refusals) from the two selector loops of the routes test."""
    blocks = {}
    for m in re.finditer(r"foreach \(\$row in @\(\n((?:[^\n]*\n)*?)\)\) \{\n\s*\$family=\$row\[0\]; \$names=\$row\[1\]; \$(\w+)=\$row\[2\]", text):
        if m.group(2) in blocks:
            raise AssertionError("duplicate selector loop: " + m.group(2))
        blocks[m.group(2)] = m.group(1)
    if set(blocks) != {"expected", "expectedReason"}:
        raise AssertionError("PowerShell selector rows not found in tests/install-powershell-routes.ps1")
    selections = []
    for m in re.finditer(r"@\('(\w+)',\s*@\(([^)]*)\),\s*'([^']*)'\)", blocks["expected"]):
        selections.append((m.group(1), _ps_names(m.group(2)), m.group(3)))
    refusals = []
    for m in re.finditer(r"@\('(\w+)',\s*@\(([^)]*)\),", blocks["expectedReason"]):
        refusals.append((m.group(1), _ps_names(m.group(2)), None))
    return selections, refusals


class _Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def run_program(program, family, names, url_prefix="https://example.invalid/"):
    """Run the extracted program once. Returns (outcome, selected_name, url, calls)."""
    payload = json.dumps({"tag_name": "v-fixture", "assets": [
        {"name": n, "browser_download_url": url_prefix + n} for n in names]}).encode()
    calls = []

    def fake_urlopen(req, timeout=None):
        calls.append({"url": req.full_url, "timeout": timeout})
        return _Response(payload)

    out = io.StringIO()
    outcome = "selected"
    saved_argv = sys.argv
    sys.argv = ["-", "fixture/repo", family]
    try:
        with mock.patch.object(urllib.request, "urlopen", fake_urlopen), contextlib.redirect_stdout(out):
            try:
                exec(compile(program, "select_asset", "exec"), {"__name__": "__main__"})
            except SystemExit as exc:
                # A refusal: raise SystemExit(message) exits non-zero. Message text is not compared.
                outcome = "refused" if exc.code not in (None, 0) else "exit-0"
    finally:
        sys.argv = saved_argv
    line = out.getvalue().strip()
    if outcome == "selected" and not line:
        outcome = "no-output"
    fields = line.split("\t") if line else []
    name = fields[1] if len(fields) == 3 else None
    url = fields[2] if len(fields) == 3 else None
    return outcome, name, url, calls


def agrees(program, row):
    family, names, expected = row
    outcome, name, _, _ = run_program(program, family, names)
    if expected is None:
        return outcome == "refused" and name is None
    return outcome == "selected" and name == expected


class BashSelectAssetTiers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.program = extract_program(INSTALL_SH.read_text(encoding="utf-8"))
        cls.selections, cls.refusals = parse_powershell_rows(ROUTES_PS1.read_text(encoding="utf-8"))

    def test_powershell_rows_are_the_ten_rows(self):
        self.assertEqual(len(self.selections), 6)
        self.assertEqual(len(self.refusals), 4)
        self.assertIn(("safari", ["tabliss-chromium.zip"], None), self.refusals)
        self.assertIn(("chromium", [], None), self.refusals)

    def test_selection_rows_parity(self):
        for family, names, expected in self.selections:
            with self.subTest(family=family, names=names):
                outcome, name, url, _ = run_program(self.program, family, names)
                self.assertEqual(outcome, "selected")
                self.assertEqual(name, expected)
                self.assertEqual(url, "https://example.invalid/" + expected)

    def test_refusal_rows_parity(self):
        for family, names, _ in self.refusals:
            with self.subTest(family=family, names=names):
                outcome, name, _, _ = run_program(self.program, family, names)
                self.assertEqual(outcome, "refused")
                self.assertIsNone(name)

    def test_metadata_fetched_once_per_call_with_timeout(self):
        # Bash re-fetches /releases/latest on every select_asset call (no per-run cache), timeout 30 s.
        for _ in range(2):
            _, _, _, calls = run_program(self.program, "chromium", ["tabliss-chromium.zip"])
            self.assertEqual(calls, [{"url": "https://api.github.com/repos/fixture/repo/releases/latest", "timeout": 30}])

    def test_url_scheme_row_documents_current_bash_behaviour(self):
        # Current Bash selects a non-https download URL unchanged; PowerShell Download-Asset refuses it.
        outcome, name, url, _ = run_program(self.program, "chromium", ["tabliss-chromium.zip"], "http://example.invalid/")
        self.assertEqual((outcome, name, url), ("selected", "tabliss-chromium.zip", "http://example.invalid/tabliss-chromium.zip"))

    def test_tier_reorder_mutant_is_detected(self):
        mutant = self.program.replace("pick(c1 + c2 + c3)", "pick(c3 + c2 + c1)").replace("pick(c1 + c2)", "pick(c2 + c1)")
        self.assertNotEqual(mutant, self.program, "mutation sites not found")
        disagreements = [row for row in self.selections + self.refusals if not agrees(mutant, row)]
        self.assertGreater(len(disagreements), 0, "tier-reorder mutant survived the parity rows")


if __name__ == "__main__":
    unittest.main(verbosity=2)
