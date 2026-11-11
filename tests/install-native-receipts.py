#!/usr/bin/env python3
"""Collector controls: failures and missing observations must not become PASS."""
import importlib.util
import pathlib
import unittest

path = pathlib.Path(__file__).resolve().parents[1] / 'tools/qualification/installer_native.py'
spec = importlib.util.spec_from_file_location('installer_native', path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ReceiptControls(unittest.TestCase):
    def test_failed_result_cannot_be_overridden_by_other_truthy_field(self):
        self.assertFalse(module.passed({'results': [{'pass': False, 'detected': True}]}))

    def test_empty_missing_and_unobserved_rows_fail(self):
        for value in ({}, {'results': []}, {'results': [{}]}, {'results': [{'pass': 'true'}]}):
            self.assertFalse(module.passed(value))

    def test_actual_result_variants(self):
        for key in ('pass', 'pass_', 'detected'):
            self.assertTrue(module.passed({'results': [{key: True}]}))
            self.assertFalse(module.passed({'results': [{key: True}, {key: False}]}))

    def test_only_terminal_object_is_accepted(self):
        self.assertEqual(module.receipt('message\n{"results":[{"pass":true}]}\n')['results'], [{'pass': True}])
        with self.assertRaises(ValueError):
            module.receipt('{"results":[{"pass":true}]}\nunfinished output')


if __name__ == '__main__':
    unittest.main()
