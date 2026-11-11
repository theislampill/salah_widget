"""Pure-helper checks for tools/qa/run_r000f_native.py (no browser, no Playwright import, no network)."""
import importlib.util, unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location('run_r000f_native', Path(__file__).resolve().parents[1] / 'tools/qa/run_r000f_native.py')
D = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(D)
B = 'http://127.0.0.1:8000/'


class Helpers(unittest.TestCase):
    def test_preview_navigation_needs_cachebuster(self):
        self.assertTrue(D.is_preview_nav(B + '?r=0#lat=1&lon=2'))
        self.assertFalse(D.is_preview_nav('about:blank'))
        self.assertFalse(D.is_preview_nav(B + 'index.html#lat=1'))

    def test_fragment_and_params(self):
        u = B + '?r=3#local=1&method=4&units=f'
        self.assertEqual(D.fragment(u), 'local=1&method=4&units=f')
        self.assertEqual(D.hash_params(u), {'local': '1', 'method': '4', 'units': 'f'})
        self.assertIsNone(D.fragment(None))

    def test_nav_delta_counts_only_preview_urls_after_start(self):
        log = [B + '?r=0#a=1', 'about:blank', B + '?r=1#a=2', B + '?r=2#a=2']
        self.assertEqual(D.nav_delta(log, 1), [B + '?r=1#a=2', B + '?r=2#a=2'])
        self.assertEqual(D.nav_delta(log, 4), [])

    def test_distinct_outputs_collapses_consecutive_duplicates(self):
        self.assertEqual(D.distinct_outputs(['2', '21', '21', '21.5']), ['2', '21', '21.5'])
        self.assertEqual(D.distinct_outputs(['a', 'b', 'a']), ['a', 'b', 'a'])   # A→B→A is two real changes

    def test_absolute_and_ledger(self):
        self.assertEqual(D.rparam(B + '?r=7#x'), '7')
        self.assertIsNone(D.rparam('about:blank'))
        assigned = D.absolute([B + '?r=0#a', '?r=1#b', None, B + '?r=2#c'], B)
        self.assertEqual(assigned, [B + '?r=0#a', B + '?r=1#b', B + '?r=2#c'])
        led = D.ledger_summary(assigned, [B + '?r=0', B + '?r=2'], [B + '?r=0#a'])
        self.assertEqual(led['assignedNotRequested'], ['1'])   # same-task duplicate the engine never requested
        self.assertEqual(led['requestedNotCommitted'], ['2'])  # superseded before commit

    def test_compare_boxes(self):
        a = {'#pv': {'x': 0, 'y': 0, 'w': 325, 'h': 530}, '#copy': {'x': 1, 'y': 1, 'w': 10, 'h': 10}}
        b = {'#pv': {'x': 0.3, 'y': 0, 'w': 325, 'h': 530}, '#copy': {'x': 1, 'y': 9, 'w': 10, 'h': 10}, '#new': None}
        self.assertEqual(sorted(D.compare_boxes(a, b)), ['#copy'])
        self.assertEqual(D.compare_boxes(a, dict(a)), {})

    def test_builder_constants_exact_from_served_builder(self):
        text = (Path(__file__).resolve().parents[1] / 'builder.html').read_text(encoding='utf-8')
        k = D.builder_constants(text)
        self.assertEqual(k['REFUSED'], 'Enter a valid latitude and longitude first.')
        self.assertIn('self-configuring', k['INVALID_NOTE_LOCAL'])
        self.assertIn('last valid location', k['INVALID_NOTE'])
        self.assertEqual(D.builder_constants('<script>const X=1;</script>'),
                         {'REFUSED': None, 'INVALID_NOTE': None, 'INVALID_NOTE_LOCAL': None})   # main: cell must fail


if __name__ == '__main__':
    unittest.main()
