#!/usr/bin/env python3
"""Acquire/authenticate one pinned candidate; NEVER admit it as a production sky.

Python 3.11+, standard library only. No GitHub credentials or writes required.
The real release asset has NOT been available to this continuation's runtime.
The structural parser was exercised on labelled artificial test inputs only.
"""
from __future__ import annotations
import argparse
import gzip
import hashlib
import io
import json
import math
import os
from pathlib import Path
import sys
import tempfile
from typing import TextIO
from urllib.request import Request, urlopen

SOURCE_URL = 'https://github.com/TuSKan/astrogo/releases/download/starmap-v2/starmap-o8-BVRI-total.txt.gz'
EXPECTED_FILENAME = 'starmap-o8-BVRI-total.txt.gz'
EXPECTED_BYTES = 17539524
EXPECTED_SHA256 = '69f3c6ede4a730e0ca4699f5943fca59d0b203f37c4dfc4b7e6927f063250446'
EXPECTED_ROWS = 786432
BANDS = ('B','V','R','I')

class SourceError(ValueError):
    """Candidate fails an explicit authentication or format requirement."""

def authenticate(path: str | Path, expected_bytes: int = EXPECTED_BYTES,
                 expected_sha256: str = EXPECTED_SHA256) -> dict:
    path = Path(path)
    actual_bytes = path.stat().st_size
    if actual_bytes != expected_bytes:
        raise SourceError(f'Wrong byte count: {actual_bytes}; expected {expected_bytes}')
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''):
            digest.update(chunk)
    actual_sha = digest.hexdigest()
    if actual_sha != expected_sha256:
        raise SourceError(f'SHA-256 mismatch: {actual_sha}; expected {expected_sha256}')
    return {'bytes': actual_bytes, 'sha256': actual_sha,
            'authentication': 'MATCHES_PINNED_GITHUB_RELEASE_DIGEST'}

def inspect_text(stream: TextIO, *, expected_rows: int = EXPECTED_ROWS) -> dict:
    """Validate the declared text format, with bounded memory and no unit guesses.

    expected_rows is adjustable ONLY for parser unit tests. verify() always uses
    the pinned full-sky count, size, and digest. This does not verify catalogue
    completeness, passband accuracy, rights, or independence from CP6 stars.
    """
    header: list[str] = []
    rows = 0
    stats = {b: {'minimum':math.inf,'maximum':0.0,'zeroCount':0} for b in BANDS}
    chars = 0
    for line in iter(lambda: stream.readline(4097), ''):
        chars += len(line)
        if len(line) > 4096 or chars > 100_000_000:
            raise SourceError('Input exceeds bounded decompressed-text limits')
        text = line.strip()
        if not text:
            continue
        if text.startswith('#'):
            header.append(text)
            continue
        fields = text.split()
        if len(fields) != 5:
            raise SourceError(f'Expected five columns at data row {rows}, got {len(fields)}')
        try:
            index = int(fields[0])
        except ValueError as exc:
            raise SourceError(f'Invalid pixel index at data row {rows}') from exc
        if index != rows:
            raise SourceError(f'Unexpected pixel index {index}; expected {rows}')
        rows += 1
        if rows > expected_rows:
            raise SourceError(f'Excess row count: more than {expected_rows}')
        for band, raw in zip(BANDS, fields[1:]):
            try:
                value = float(raw)
            except ValueError as exc:
                raise SourceError(f'Invalid {band} radiance at pixel {index}') from exc
            if not math.isfinite(value) or value < 0:
                raise SourceError(f'Nonfinite/negative {band} radiance at pixel {index}')
            st = stats[band]
            st['minimum'] = min(st['minimum'],value)
            st['maximum'] = max(st['maximum'],value)
            st['zeroCount'] += int(value == 0)
    if rows != expected_rows:
        raise SourceError(f'Wrong row count: {rows}; expected {expected_rows}')
    if '# bands: B V R I' not in header:
        raise SourceError('Missing or conflicting bands declaration; do not guess the column order')
    if '# grid: HEALPix order 8, NESTED, ICRS' not in header:
        raise SourceError('Missing or conflicting grid declaration; do not guess the frame/order')
    quantity = '# quantity: passband-averaged spectral radiance, W m^-2 sr^-1 nm^-1'
    if quantity not in header:
        raise SourceError('Missing or conflicting quantity declaration; do not guess band-integrated units')
    return {'rows':rows,'bands':stats,'header':header,'coordinateFrame':'ICRS',
            'sampling':'HEALPix order 8 NESTED','quantity':quantity[2:],
            'scientificallyAdmitted':False,
            'remainingGates':['map reuse/attribution terms','actual per-band calibration review',
                              'catalogue-overlap removal and uncertainty','independent map registration']}

def verify(path: str | Path) -> dict:
    """Verify exact release bytes before attempting decompression or decoding."""
    auth = authenticate(path)
    try:
        with gzip.open(path,'rt',encoding='utf-8',errors='strict') as stream:
            structural = inspect_text(stream)
    except (OSError,UnicodeError) as exc:
        raise SourceError(f'Cannot decode authenticated gzip: {exc}') from exc
    return {'status':'AUTHENTICATED_AND_STRUCTURALLY_CHECKED_NOT_ADMITTED',
            'filename':Path(path).name,'sourceUrl':SOURCE_URL,**auth,**structural}

def download(destination: str | Path) -> dict:
    """One bounded GET. Existing files are verified, never overwritten."""
    destination = Path(destination).resolve()
    if destination.exists():
        return verify(destination)
    destination.parent.mkdir(parents=True,exist_ok=True)
    temporary: Path | None = None
    try:
        request = Request(SOURCE_URL,headers={'User-Agent':'salah-real-sky-source-acquisition/1'})
        with urlopen(request,timeout=45) as response:
            with tempfile.NamedTemporaryFile(dir=destination.parent,prefix='.cp7-download-',
                                             suffix='.part',delete=False) as out:
                temporary = Path(out.name)
                count = 0
                while True:
                    block = response.read(1024*1024)
                    if not block:
                        break
                    count += len(block)
                    if count > EXPECTED_BYTES:
                        raise SourceError('Download exceeded the pinned asset byte count')
                    out.write(block)
        auth = authenticate(temporary)
        # Same-directory hard link publishes without overwriting an existing file.
        # If another process claimed destination, FileExistsError is intentional.
        os.link(temporary,destination)
        temporary.unlink();temporary = None
        return verify(destination)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path',nargs='?',default=EXPECTED_FILENAME)
    parser.add_argument('--download',action='store_true',help='Download pinned public asset; no overwrites')
    parser.add_argument('--report',type=Path,help='Write a NEW JSON report; existing files are not overwritten')
    args = parser.parse_args(argv)
    try:
        result = download(args.path) if args.download else verify(args.path)
    except Exception as exc:
        result = {'status':'BLOCKED','scientificallyAdmitted':False,'errorType':type(exc).__name__,
                  'detail':str(exc),'sourceUrl':SOURCE_URL,'expectedBytes':EXPECTED_BYTES,
                  'expectedSha256':EXPECTED_SHA256}
        code = 2
    else:
        code = 0
    encoded = json.dumps(result,indent=2,allow_nan=False)+'\n'
    if args.report:
        try:
            with args.report.open('x',encoding='utf-8') as out:
                out.write(encoded)
        except OSError as exc:
            print(f'Report not written: {exc}',file=sys.stderr)
            return 2
    print(encoded,end='')
    return code

if __name__ == '__main__':
    raise SystemExit(main())
