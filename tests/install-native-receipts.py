#!/usr/bin/env python3
"""Collector controls: failures and missing observations must not become PASS."""
import importlib.util
import pathlib
import tempfile
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

    def test_primary_and_imported_entry_raw_fixtures_are_retained(self):
        with tempfile.TemporaryDirectory(prefix='salah-collector-control-') as directory:
            root=pathlib.Path(directory)
            primary=root/'primary'; auxiliary=root/'entry'; out=root/'out'
            for path in (primary,auxiliary,out): path.mkdir()
            (primary/'result.txt').write_text('primary')
            (auxiliary/'entry-output.txt').write_text('actual entry observation')
            rows=module.copy_fixtures({'fixtureRoot':str(primary),'auxiliaryFixtures':[str(auxiliary)]},out,'case',root)
            self.assertEqual(len(rows),2)
            self.assertEqual((out/'case-fixture-1/entry-output.txt').read_text(),'actual entry observation')
            with self.assertRaises(ValueError):
                module.copy_fixtures({'fixture':str(root.parent)},out,'outside',root)
            self.assertFalse((out/'outside-fixture').exists())


if __name__ == '__main__':
    unittest.main()
