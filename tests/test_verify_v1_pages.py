#!/usr/bin/env python3
"""R0037: `tools/verify_v1.py --check-pages` reviewed-configuration contract (rows R37-02..R37-09).

Every case runs the real verifier CLI against a disposable copy under the temporary directory; the repository is
never written. VERIFY_V1_UNDER_TEST may name another verifier file (used only by the scratch mutation runner).
Python standard library only. Run: python tests/test_verify_v1_pages.py
"""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
VERIFIER = Path(os.environ.get("VERIFY_V1_UNDER_TEST", ROOT / "tools" / "verify_v1.py"))
CURRENT_DIGEST = "0f846f7efb27c391c66dffc66913f3eb452d5769e13170db64c2d0cd32a3e5c8"
EVIDENCE = "docs/state-contracts/evidence/R0037/config-0f846f7e/deployed-pages-payload.json"


class CheckPages(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="salah-v1-pages-")
        self.repo = Path(self._tmp.name)
        shutil.copytree(ROOT / "v1", self.repo / "v1")
        shutil.copy2(ROOT / "_config.yml", self.repo / "_config.yml")
        (self.repo / EVIDENCE).parent.mkdir(parents=True)
        shutil.copy2(ROOT / EVIDENCE, self.repo / EVIDENCE)

    def tearDown(self):
        self._tmp.cleanup()

    def run_verifier(self, *flags):
        r = subprocess.run([sys.executable, str(VERIFIER), "--repo", str(self.repo), *flags],
                           capture_output=True, text=True, timeout=60)
        return r.returncode, r.stdout.splitlines()

    def assert_fail(self, expected, *flags):
        code, lines = self.run_verifier("--check-pages", *flags)
        self.assertEqual(code, 1, lines)
        self.assertEqual(lines, ["FAIL: " + e for e in expected])

    # R37-02: the reviewed current configuration passes, and the PASS text claims no deployment.
    def test_reviewed_current_configuration_passes(self):
        code, lines = self.run_verifier("--check-pages")
        self.assertEqual(code, 0, lines)
        self.assertEqual(lines, ["PASS: frozen V1 payload and anchored manifest",
                                 "PASS: plain static V1 files; reviewed Jekyll configuration _config.yml "
                                 + CURRENT_DIGEST + "; inclusion preflight only; deployment not checked"])
        self.assertNotRegex("\n".join(lines), re.compile(r"deploy(ed|ment) (ran|pending|passed|verified)", re.I))

    # R37-03b: an admitted digest whose recorded evidence is missing fails, naming the path.
    def test_missing_review_evidence_fails(self):
        (self.repo / EVIDENCE).unlink()
        self.assert_fail([f"Jekyll configuration _config.yml {CURRENT_DIGEST} review evidence missing: {EVIDENCE}"])

    # R0037 review hardening: the admitted evidence must list every V1 public file with the tree's SHA-256.
    def evidence_json(self):
        return json.loads((self.repo / EVIDENCE).read_text(encoding="utf-8"))

    def write_evidence(self, data):
        (self.repo / EVIDENCE).write_text(json.dumps(data), encoding="utf-8")

    def expect_unlisted(self, path):
        return (f"Jekyll configuration _config.yml {CURRENT_DIGEST} review evidence {EVIDENCE} does not list {path} "
                "with the tree's SHA-256")

    def test_evidence_without_a_v1_file_fails(self):
        data = self.evidence_json()
        del data["protectedConsumers"]["v1/VERSION.json"]
        self.write_evidence(data)
        self.assert_fail([self.expect_unlisted("v1/VERSION.json")])

    def test_evidence_with_a_different_v1_hash_fails(self):
        data = self.evidence_json()
        data["protectedConsumers"]["v1/config.js"]["sha256"] = "0" * 64
        self.write_evidence(data)
        self.assert_fail([self.expect_unlisted("v1/config.js")])

    def test_evidence_with_a_different_v1_size_fails(self):
        data = self.evidence_json()
        data["protectedConsumers"]["v1/MANIFEST.sha256"]["bytes"] += 1
        self.write_evidence(data)
        self.assert_fail([self.expect_unlisted("v1/MANIFEST.sha256")])

    def test_evidence_naming_no_v1_file_fails_for_each(self):
        self.write_evidence({"protectedConsumers": {}})
        self.assert_fail([self.expect_unlisted(p) for p in
                          ("v1/index.html", "v1/config.js", "v1/VERSION.json", "v1/MANIFEST.sha256")])

    def test_evidence_not_json_fails(self):
        (self.repo / EVIDENCE).write_bytes(b"not json")
        self.assert_fail([f"Jekyll configuration _config.yml {CURRENT_DIGEST} review evidence is not JSON: {EVIDENCE}"])

    def test_list_shaped_evidence_passes(self):
        files = [{"path": p, "sha256": hashlib.sha256((self.repo / p).read_bytes()).hexdigest()}
                 for p in ("v1/index.html", "v1/config.js", "v1/VERSION.json", "v1/MANIFEST.sha256")]
        self.write_evidence({"site": {"files": files}})
        code, lines = self.run_verifier("--check-pages")
        self.assertEqual(code, 0, lines)

    # R37-04: one appended comment byte makes the configuration unreviewed; the new digest is named.
    def test_unreviewed_configuration_fails(self):
        cfg = self.repo / "_config.yml"
        cfg.write_bytes(cfg.read_bytes() + b"#")
        h = hashlib.sha256(cfg.read_bytes()).hexdigest()
        self.assertNotEqual(h, CURRENT_DIGEST)
        self.assert_fail([f"Jekyll configuration _config.yml {h} has no recorded V1 inclusion review"])

    # R37-05: a configuration that excludes V1 is unreviewed and fails.
    def test_v1_exclusion_fails(self):
        cfg = self.repo / "_config.yml"
        cfg.write_text("exclude:\n  - v1\n", encoding="utf-8", newline="\n")
        code, lines = self.run_verifier("--check-pages")
        self.assertEqual(code, 1)
        self.assertEqual(len(lines), 1)
        self.assertRegex(lines[0], r"^FAIL: Jekyll configuration _config\.yml [0-9a-f]{64} has no recorded V1 inclusion review$")

    # R37-06: an alternative or duplicate configuration file fails.
    def test_duplicate_yaml_configuration_fails(self):
        (self.repo / "_config.yaml").write_text("exclude: [v1]\n", encoding="utf-8")
        self.assert_fail(["More than one Jekyll configuration file (ambiguous build input): _config.yml, _config.yaml"])

    def test_duplicate_toml_configuration_fails(self):
        (self.repo / "_config.toml").write_text("exclude = [\"v1\"]\n", encoding="utf-8")
        self.assert_fail(["More than one Jekyll configuration file (ambiguous build input): _config.yml, _config.toml"])

    def test_alternative_yaml_configuration_alone_fails(self):
        (self.repo / "_config.yml").unlink()
        (self.repo / "_config.yaml").write_text("exclude: [v1]\n", encoding="utf-8")
        code, lines = self.run_verifier("--check-pages")
        self.assertEqual(code, 1)
        self.assertRegex(lines[0], r"^FAIL: Jekyll configuration _config\.yaml [0-9a-f]{64} has no recorded V1 inclusion review$")

    # R37-07: the existing PASS paths are kept; front matter still fails (payload FAIL first, as before).
    def test_no_configuration_passes(self):
        (self.repo / "_config.yml").unlink()
        code, lines = self.run_verifier("--check-pages")
        self.assertEqual(code, 0, lines)
        self.assertEqual(lines[1], "PASS: plain static V1 files; no Jekyll configuration file; "
                                   "inclusion preflight only; deployment not checked")

    def test_nojekyll_with_unreviewed_configuration_passes(self):
        (self.repo / "_config.yml").write_text("exclude: [v1]\n", encoding="utf-8")
        (self.repo / ".nojekyll").write_bytes(b"")
        code, lines = self.run_verifier("--check-pages")
        self.assertEqual(code, 0, lines)
        self.assertIn(".nojekyll present", lines[1])

    def test_front_matter_in_payload_fails_on_payload_first(self):
        target = self.repo / "v1" / "config.js"
        target.write_bytes(b"---\n---\n" + target.read_bytes())
        self.assert_fail(["Frozen payload changed or missing: v1/config.js"])

    # R37-09: payload verification and the default mode are unchanged; --check-pages is not consulted by default.
    def test_default_mode_ignores_configuration(self):
        (self.repo / "_config.yml").write_text("exclude: [v1]\n", encoding="utf-8")
        code, lines = self.run_verifier()
        self.assertEqual((code, lines), (0, ["PASS: frozen V1 payload and anchored manifest"]))

    def test_negative_control_unchanged(self):
        code, lines = self.run_verifier("--negative-control")
        self.assertEqual(code, 0, lines)
        self.assertEqual(lines[-1], "PASS: disposable tamper rejected: Frozen payload changed or missing: v1/index.html")


if __name__ == "__main__":
    unittest.main(verbosity=2)
