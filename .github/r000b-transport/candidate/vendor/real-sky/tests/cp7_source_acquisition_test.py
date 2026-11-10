"""Acquisition guards only. Tiny artificial fixtures are NOT a scientific sky."""
import hashlib
import io
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import cp7_acquire_source as s

HEADER = '''# bands: B V R I
# grid: HEALPix order 8, NESTED, ICRS
# quantity: passband-averaged spectral radiance, W m^-2 sr^-1 nm^-1
'''

class SourceAcquisitionTests(unittest.TestCase):
    def test_pinned_source_identity(self):
        self.assertEqual(s.EXPECTED_BYTES,17539524)
        self.assertEqual(s.EXPECTED_SHA256,'69f3c6ede4a730e0ca4699f5943fca59d0b203f37c4dfc4b7e6927f063250446')
        self.assertEqual(s.EXPECTED_ROWS,786432)
    def test_missing_input_is_not_admitted(self):
        with self.assertRaises(FileNotFoundError): s.verify('/not-present/starmap.txt.gz')
    def test_wrong_bytes_rejected_before_decode(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'fake.gz';p.write_bytes(b'not a sky')
            with self.assertRaisesRegex(s.SourceError,'byte count'): s.verify(p)
    def test_matching_hash_local_guard(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'x';p.write_bytes(b'fixture')
            self.assertEqual(s.authenticate(p,7,hashlib.sha256(b'fixture').hexdigest())['bytes'],7)
    def test_wrong_hash_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'x';p.write_bytes(b'fixture')
            with self.assertRaisesRegex(s.SourceError,'SHA-256'): s.authenticate(p,7,'0'*64)
    def test_ordered_numeric_fixture(self):
        r=s.inspect_text(io.StringIO(HEADER+'0 1e-9 2e-9 3e-9 4e-9\n1 2e-9 3e-9 4e-9 5e-9\n'),expected_rows=2)
        self.assertEqual(r['rows'],2);self.assertEqual(r['coordinateFrame'],'ICRS')
        self.assertFalse(r['scientificallyAdmitted'])
        self.assertEqual(r['bands']['V']['maximum'],3e-9)
    def test_missing_row(self):
        with self.assertRaisesRegex(s.SourceError,'row count'): s.inspect_text(io.StringIO(HEADER+'0 1 2 3 4\n'),expected_rows=2)
    def test_duplicate_or_out_of_order_index(self):
        for index in ['0','2','-1']:
            with self.subTest(index=index),self.assertRaisesRegex(s.SourceError,'pixel index'):
                s.inspect_text(io.StringIO(HEADER+'0 1 2 3 4\n'+index+' 1 2 3 4\n'),expected_rows=2)
    def test_invalid_radiance(self):
        for x in ['nan','inf','-1','bad']:
            with self.subTest(x=x),self.assertRaises(s.SourceError): s.inspect_text(io.StringIO(HEADER+f'0 {x} 1 1 1\n'),expected_rows=1)
    def test_wrong_band_order(self):
        with self.assertRaisesRegex(s.SourceError,'bands'): s.inspect_text(io.StringIO(HEADER.replace('B V R I','V B R I')+'0 1 1 1 1\n'),expected_rows=1)
    def test_wrong_coordinate_system(self):
        with self.assertRaisesRegex(s.SourceError,'grid'): s.inspect_text(io.StringIO(HEADER.replace('ICRS','Galactic')+'0 1 1 1 1\n'),expected_rows=1)
    def test_ambiguous_units_rejected(self):
        with self.assertRaisesRegex(s.SourceError,'quantity'): s.inspect_text(io.StringIO(HEADER.replace(' nm^-1','')+'0 1 1 1 1\n'),expected_rows=1)
    def test_missing_zeroes_not_reinterpreted(self):
        r=s.inspect_text(io.StringIO(HEADER+'0 0 1 1 1\n'),expected_rows=1)
        self.assertEqual(r['bands']['B']['zeroCount'],1)
        self.assertFalse(r['scientificallyAdmitted'])
    def test_extra_column_rejected(self):
        with self.assertRaisesRegex(s.SourceError,'columns'): s.inspect_text(io.StringIO(HEADER+'0 1 2 3 4 5\n'),expected_rows=1)
    def test_missing_header_not_guessed(self):
        with self.assertRaises(s.SourceError): s.inspect_text(io.StringIO('0 1 2 3 4\n'),expected_rows=1)
    def test_extra_row_not_ignored(self):
        with self.assertRaisesRegex(s.SourceError,'row count'): s.inspect_text(io.StringIO(HEADER+'0 1 1 1 1\n1 2 2 2 2\n'),expected_rows=1)

if __name__=='__main__': unittest.main()
