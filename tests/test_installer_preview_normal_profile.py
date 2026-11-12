#!/usr/bin/env python3
"""Inert corruption controls for the native normal-cache evidence receiver.

These exercise byte and process-association admission, never a native installer.
"""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "normal_profile", ROOT / "tools/qualification/installer_preview_windows_normal_profile_diagnostic.py")
DIAG = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DIAG)


class CacheReceiving(unittest.TestCase):
    def receiver(self):
        function = getattr(DIAG, "receive_cache_bytes", None)
        self.assertTrue(callable(function), "The diagnostic must bind retained cache bytes to the observed inventory")
        return function

    def row(self):
        return {"role": "analysisCache", "path": ".", "kind": "file", "bytes": 3,
                "sha256": "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"}

    def test_exact_bytes_are_received(self):
        self.assertEqual(self.receiver()(b"abc", [self.row()]), self.row())

    def test_same_length_corruption_is_refused(self):
        with self.assertRaises(ValueError):
            self.receiver()(b"abd", [self.row()])

    def test_missing_or_wrong_length_capture_is_refused(self):
        receiver = self.receiver()
        for raw in (None, b"ab", b"abcd"):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                receiver(raw, [self.row()])

    def test_absent_cache_cannot_gain_invented_bytes(self):
        row = {"role": "analysisCache", "path": ".", "kind": "absent", "bytes": None, "sha256": None}
        receiver = self.receiver()
        self.assertEqual(receiver(None, [row]), row)
        with self.assertRaises(ValueError):
            receiver(b"", [row])

    def test_duplicate_missing_or_untyped_cache_row_is_refused(self):
        receiver = self.receiver()
        bad = dict(self.row(), bytes=True)
        for rows in ([], [self.row(), self.row()], [bad]):
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                receiver(b"abc", rows)


class WarmContextReceiving(unittest.TestCase):
    def receiver(self):
        function = getattr(DIAG, "receive_warm_context", None)
        self.assertTrue(callable(function), "The diagnostic must associate its source-free command proof")
        return function

    def evidence(self):
        nonce = "0123456789abcdef0123456789abcdef"
        assembly = {"path": "C:\\runtime\\utility.dll", "bytes": 3,
                    "sha256": "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"}
        receipt = {"pid": 1234, "nonce": nonce, "environment": {
            "INSTALL_FIXTURE_NORMAL": "0", "INSTALL_NATIVE_UTILITY": "C:\\runtime\\Utility.psd1",
            "PSModuleAnalysisCachePath": "C:\\fixture\\analysis-cache"}}
        context = {"schema": "r0016-source-free-json-context.v1", "pid": 1234, "nonce": nonce,
                   "normal": "0", "command": "ConvertFrom-Json", "commandType": "Cmdlet",
                   "module": "Microsoft.PowerShell.Utility", "nativeUtility": "C:\\runtime\\Utility.psd1",
                   "analysisCachePath": "C:\\fixture\\analysis-cache", "parsedMarker": "source-free",
                   "parsedValue": 16, "assemblyPath": assembly["path"], "assemblyBytes": 3,
                   "assemblySha256": assembly["sha256"], "moduleSearchPath": "C:\\runtime\\Modules"}
        observation = {"device": 1, "inode": 42, "mode": 33188, "bytes": 3,
                       "mtimeNs": 10, "ctimeNs": 9, "attributes": 32, "links": 1}
        binding = {"childFact": dict(assembly), "parentFact": dict(assembly), "matches": True, "error": None,
                   "nativeFileIdentity": {"rawPath": assembly["path"], "canonicalPath": assembly["path"],
                       "resolvedRawPath": assembly["path"], "resolvedCanonicalPath": assembly["path"],
                       "resolutionMatches": True, "sameFile": True, "stable": True, "contentMatches": True,
                       "rawReadbackFact": dict(assembly), "canonicalReadbackFact": dict(assembly),
                       "observations": {key: dict(observation) for key in
                           ("rawBefore", "canonicalBefore", "rawAfter", "canonicalAfter")}}}
        return context, receipt, binding

    def encode(self, context):
        return b"R0016 independent host startup control\r\nR0016_WARM_JSON_CONTEXT " + json.dumps(context).encode() + b"\r\n"

    def test_matching_native_command_context_is_received(self):
        context, receipt, assembly = self.evidence()
        self.assertEqual(self.receiver()(self.encode(context), receipt, assembly), context)

    def test_process_command_cache_and_assembly_corruptions_are_refused(self):
        receiver = self.receiver()
        context, receipt, assembly = self.evidence()
        changes = {"pid": 4321, "nonce": "f" * 32, "normal": "1", "command": "Write-Host",
                   "commandType": "Function", "module": "Other", "nativeUtility": "C:\\other.psd1",
                   "analysisCachePath": "C:\\other-cache", "parsedMarker": "installer", "parsedValue": True,
                   "assemblyPath": "C:\\other.dll", "assemblyBytes": True, "assemblySha256": "0" * 64}
        for field, value in changes.items():
            altered = dict(context, **{field: value})
            with self.subTest(field=field), self.assertRaises(ValueError):
                receiver(self.encode(altered), receipt, assembly)

    def test_missing_duplicate_or_replayed_context_is_refused(self):
        receiver = self.receiver()
        context, receipt, assembly = self.evidence()
        for raw in (b"", self.encode(context) * 2, self.encode(context).replace(b'"pid": 1234', b'"pid": 1234, "pid": 1234')):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                receiver(raw, receipt, assembly)

    def test_original_failure_cannot_be_relabelled(self):
        self.assertEqual(DIAG.original_status([{"pass_": False}], "FAIL", "FAIL", 1), "FAIL")
        with self.assertRaises(ValueError):
            DIAG.original_status([{"pass_": False}], "PASS", "PASS", 0)

    def test_raw_and_canonical_spelling_need_full_native_identity(self):
        context, receipt, binding = self.evidence()
        context["assemblyPath"] = "C:\\Runtime\\utility.dll"
        binding["childFact"]["path"] = context["assemblyPath"]
        binding["nativeFileIdentity"]["rawPath"] = context["assemblyPath"]
        self.assertEqual(self.receiver()(self.encode(context), receipt, binding), context)
        for field in ("sameFile", "stable", "contentMatches", "resolutionMatches"):
            altered = json.loads(json.dumps(binding))
            altered["nativeFileIdentity"][field] = False
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.receiver()(self.encode(context), receipt, altered)
        for field, value in (("inode", 43), ("mtimeNs", 11), ("bytes", 4)):
            altered = json.loads(json.dumps(binding))
            altered["nativeFileIdentity"]["observations"]["canonicalAfter"][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.receiver()(self.encode(context), receipt, altered)

    def test_actual_owned_file_binding_preserves_raw_spelling_and_rejects_hash_mismatch(self):
        receiver = getattr(DIAG, "receive_native_assembly", None)
        self.assertTrue(callable(receiver), "Use the existing native same-file receiver")
        role = "tests/install-entry-driver-diagnostic.py"
        driver = DIAG.load_pinned(ROOT / role, DIAG.INPUTS[role], "warm_context_test_driver")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            (root / "sub").mkdir()
            target = root / "utility.dll"
            target.write_bytes(b"abc")
            raw_path = str(root / "sub" / ".." / "utility.dll")
            context = {"assemblyPath": raw_path, "assemblyBytes": 3, "assemblySha256": DIAG.digest(b"abc")}
            journal = root / "binding.json"
            result = receiver(driver, context, journal)
            self.assertEqual(result["childFact"]["path"], raw_path)
            self.assertEqual(result["parentFact"]["path"], str(target))
            self.assertTrue(result["matches"])
            self.assertEqual(json.loads(journal.read_text())["comparisons"], [result])
            with self.assertRaises(AssertionError):
                receiver(driver, dict(context, assemblySha256="0" * 64), journal)
            self.assertFalse(json.loads(journal.read_text())["comparisons"][0]["matches"])


if __name__ == "__main__":
    unittest.main()
