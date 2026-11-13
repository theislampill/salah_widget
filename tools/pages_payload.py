"""R002B Pages payload instrument (ISM-BLD-003). Measures; never builds, deploys or changes Pages.

The generalised successor of tools/verify_r0017_pages_payload.py (which stays frozen to PR 62).
Every guard is an explicit exception, never `assert`, so `python -O` reaches the same verdict.

Verdicts (docs/state-contracts/R002B.md):
  within        measured regular-file bytes <= bound
  exceeds       measured regular-file bytes >  bound
  inconclusive  nothing measurable: expired artifact, failed/empty build, truncated or inconsistent
                stream. Never reported as `within`.
Exit codes: 0 within, 1 exceeds, 2 inconclusive, 3 instrument error (malformed input, symlink, CRC).

Measurement sources (authoritative, R002B section 4):
  site      a generated `_site` directory (M2, CI build with the pinned Pages builder)
  tar       an `artifact.tar` stream (M1 after extraction of the zip member)
  zip       the downloaded `github-pages` artifact zip, streamed: inflates the `artifact.tar`
            member and parses TAR headers without extracting files (M1, R0017's method)
  artifact  read-only GitHub API readback of a run's `github-pages` artifact. By default reads
            only the zip envelope (HTTP range requests over the central directory: a few KB). The
            full M1 stream (`--stream`, about the artifact's compressed size in transfer) needs the
            owner's explicit permission (R002B section 1, authorisation boundary).
Advisory only (never a verdict authority):
  project   git-tree projection of the published set at a commit under extra exclusions
  census    link and read census for a set of candidate exclusion prefixes
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import sys
import urllib.error
import urllib.request
import zlib

SCHEMA = "r002b-pages-payload/v1"
# R002B-DG1 documented conservative default: R0017's qualified bound under GitHub's documented
# "no larger than 1 GB" Pages limit. An owner decision may replace it; `--bound` carries it.
DEFAULT_BOUND = 1_000_000_000
BUILDER_IMAGE = "ghcr.io/actions/jekyll-build-pages:v1.0.13"
REPO = "theislampill/salah_widget"
# Paths the published site must keep under any exclusion (R002B section 3.3, G-06). GENERATED.json is the
# R0029 generated-output inventory, published at the root; a tree without it simply has no such path.
PROTECTED_FILES = ("index.html", "offline.html", "config.js", "builder.html", "GENERATED.json", "install.sh", "install.ps1",
                   "README.md", "DESIGN.md", "AGENTS.md", "OPTICS.md", "ARCHITECTURE.md", "HANDOFF.md",
                   "tests/widget-fixture.html")
PROTECTED_PREFIXES = ("v1/", "presets/", "real-sky/", "moon/")
EXIT = {"within": 0, "exceeds": 1, "inconclusive": 2}


class PayloadError(Exception):
    """The input is malformed or violates a guard; no verdict may be drawn (exit 3)."""


class Inconclusive(Exception):
    """Nothing measurable (expired, failed, truncated, inconsistent); never `within` (exit 2)."""


def verdict(total, bound):
    if not isinstance(bound, int) or isinstance(bound, bool) or bound <= 0:
        raise PayloadError(f"bound must be a positive integer, got {bound!r}")
    if total is None:
        return "inconclusive"
    if not isinstance(total, int) or isinstance(total, bool) or total < 0:
        raise PayloadError(f"measured total must be a non-negative integer, got {total!r}")
    return "within" if total <= bound else "exceeds"


def manifest(files):
    """files: iterable of (posix path, bytes). Same digest for every source, so M1 and M2 compare."""
    records = sorted(files)
    names = [name for name, _ in records]
    if len(set(names)) != len(names):
        raise Inconclusive("duplicate regular-file paths: counts are inconsistent")
    top = {}
    for name, size in records:
        key = name.split("/", 1)[0] if "/" in name else "(root files)"
        if name.startswith("docs/") and name.count("/") >= 2:
            key = "/".join(name.split("/")[:2])
            if name.count("/") >= 3 and key in ("docs/real-sky", "docs/state-contracts", "docs/moon"):
                key = "/".join(name.split("/")[:3])
        entry = top.setdefault(key, [0, 0])
        entry[0] += 1
        entry[1] += size
    return {
        "regularFiles": len(records),
        "regularFileBytes": sum(size for _, size in records),
        "pathSizeManifestSha256": hashlib.sha256(
            "".join(f"{size}  {name}\n" for name, size in records).encode()).hexdigest(),
        "topPrefixesBySize": [{"prefix": k, "files": v[0], "bytes": v[1]}
                              for k, v in sorted(top.items(), key=lambda kv: (-kv[1][1], kv[0]))[:25]],
    }


# --- M2: a generated _site directory ---------------------------------------------------------

def measure_site(site):
    site = Path(site)
    if not site.is_dir():
        raise Inconclusive(f"no _site directory at {site}: build failed or not run")
    files = []
    for path in sorted(site.rglob("*")):
        if path.is_symlink():
            raise PayloadError(f"symlink in _site: {path.relative_to(site).as_posix()}")
        if path.is_file():
            files.append((path.relative_to(site).as_posix(), path.stat().st_size))
    if not files:
        raise Inconclusive("_site contains no regular files: build failed or empty")
    return manifest(files)


def site_manifest_lines(site):
    site = Path(site)
    return "".join(f"{p.stat().st_size}  {p.relative_to(site).as_posix()}\n"
                   for p in sorted(site.rglob("*")) if p.is_file() and not p.is_symlink())


def compare_manifests(base_text, head_text, excludes, changed=()):
    """G-07 on real builds: published paths that disappear must all fall under the new excludes, and
    no protected path may disappear. A protected path may change size only when the candidate
    intentionally changed that source path (`changed`: `git diff --name-only BASE HEAD`); an unlisted
    resize still fails, and a removal fails even when listed."""
    changed = {c.strip() for c in changed if c.strip()}
    def parse(text):
        out = {}
        for line in text.splitlines():
            if line.strip():
                size, name = line.split("  ", 1)
                out[name] = int(size)
        return out
    before, after = parse(base_text), parse(head_text)
    removed = sorted(set(before) - set(after))
    outside = [p for p in removed if not any(p.startswith(e) for e in excludes)]
    protected_removed = [p for p in removed if p in PROTECTED_FILES or p.startswith(PROTECTED_PREFIXES)]
    protected_resized = sorted(p for p in after if p in before and before[p] != after[p]
                               and (p in PROTECTED_FILES or p.startswith(PROTECTED_PREFIXES)))
    # Declared changes exempt only resizes. A removal is never exempt: outside the exclusions it breaks
    # G-07, and a protected path must stay published (G-06) whatever the diff says.
    protected = protected_removed
    resized = [p for p in protected_resized if p not in changed]
    result = {"baseFiles": len(before), "headFiles": len(after), "removedFiles": len(removed),
              "removedBytes": sum(before[p] for p in removed), "addedPaths": sorted(set(after) - set(before)),
              "removedOutsideExcludes": outside, "protectedRemoved": protected, "protectedResized": resized,
              "intentionallyResizedProtected": sorted(p for p in protected_resized if p in changed),
              "declaredChangedPaths": len(changed)}
    result["onlyEvidenceRemoved"] = not outside and not protected and not resized
    return result


def protected_consumers(root, site):
    """Byte identity of runtime, v1/, presets, installers, root docs and the served test fixture."""
    root, site = Path(root), Path(site)
    tracked = [n for n in subprocess.check_output(["git", "ls-files", "-z"], cwd=root).decode().split("\0") if n]
    names = sorted(n for n in tracked if (n in PROTECTED_FILES or n.startswith(PROTECTED_PREFIXES))
                   and not any(part.startswith((".", "_")) for part in Path(n).parts)
                   and not n.startswith(("moon/src/", "moon/tests/")))
    mismatched, missing, files = [], [], {}
    for name in names:
        source, output = root / name, site / name
        if not output.is_file():
            missing.append(name)
            continue
        digest = hashlib.sha256(output.read_bytes()).hexdigest()
        if digest != hashlib.sha256(source.read_bytes()).hexdigest():
            mismatched.append(name)
        files[name] = {"bytes": output.stat().st_size, "sha256": digest}
    if missing or mismatched:
        raise PayloadError(f"protected consumers not byte-identical: missing={missing[:10]} "
                           f"mismatched={mismatched[:10]}")
    canonical = "".join(f"{v['sha256']}  {k}\n" for k, v in sorted(files.items()))
    return {"files": len(files), "setSha256": hashlib.sha256(canonical.encode()).hexdigest(),
            "allComparedByteIdentical": True}


# --- M1: TAR and zip streams ---------------------------------------------------------------

def _octal(field, what):
    if field and field[0] & 0x80:  # GNU base-256 numeric extension
        value = int.from_bytes(field, "big") & ~(0x80 << (8 * (len(field) - 1)))
        return value
    text = field.split(b"\0", 1)[0].strip()
    if not text:
        return 0
    try:
        return int(text, 8)
    except ValueError:
        raise PayloadError(f"malformed TAR {what} field {field!r}") from None


def _read_exact(stream, n):
    chunks, need = [], n
    while need:
        chunk = stream.read(need)
        if not chunk:
            break
        chunks.append(chunk)
        need -= len(chunk)
    return b"".join(chunks)


def _pax(data):
    records, i = {}, 0
    while i < len(data):
        space = data.find(b" ", i)
        if space < 0:
            raise PayloadError("malformed pax record")
        try:
            length = int(data[i:space])
        except ValueError:
            raise PayloadError("malformed pax record length") from None
        if length <= 0:
            raise PayloadError("malformed pax record length")
        record = data[space + 1:i + length - 1]
        key, _, value = record.partition(b"=")
        records[key.decode("utf-8", "replace")] = value.decode("utf-8", "replace")
        i += length
    return records


def is_protected(name):
    return ((name in PROTECTED_FILES or name.startswith(PROTECTED_PREFIXES))
            and not any(part.startswith((".", "_")) for part in name.split("/"))
            and not name.startswith(("moon/src/", "moon/tests/")))


def measure_tar(stream, hash_member=None):
    """Parse TAR headers from a byte stream; skip member data without storing it. Regular members for
    which hash_member(name) is true are SHA-256 hashed in passing (their bytes are never retained)."""
    hashes = {}
    files, dirs, others, consumed = [], 0, {}, 0
    long_name, pax, ended = None, {}, False
    while True:
        header = _read_exact(stream, 512)
        consumed += len(header)
        if not header:
            break
        if len(header) < 512:
            raise Inconclusive("TAR stream truncated inside a header")
        if header == b"\0" * 512:
            ended = True
            rest = stream.read(1 << 20)
            while rest:  # trailing zero blocks / record padding up to EOF
                if rest.strip(b"\0"):
                    raise Inconclusive("non-zero data after the TAR end-of-archive marker")
                consumed += len(rest)
                rest = stream.read(1 << 20)
            break
        stored = _octal(header[148:156], "checksum")
        if stored != sum(header[:148]) + 256 + sum(header[156:]):
            raise PayloadError(f"TAR header checksum mismatch at byte {consumed - 512}")
        kind = header[156:157]
        size = _octal(header[124:136], "size")
        if "size" in pax:
            size = int(pax["size"])
        padded = (size + 511) // 512 * 512
        if kind in (b"L", b"x", b"g"):
            data = _read_exact(stream, padded)
            consumed += len(data)
            if len(data) < padded:
                raise Inconclusive("TAR stream truncated inside an extended header")
            if kind == b"L":
                long_name = data[:size].split(b"\0", 1)[0].decode("utf-8", "replace")
            elif kind == b"x":
                pax = _pax(data[:size])
            continue
        name = header[0:100].split(b"\0", 1)[0].decode("utf-8", "replace")
        if header[257:263] == b"ustar\0":  # POSIX ustar prefix; GNU ("ustar  \0") reuses 345: for times
            prefix = header[345:500].split(b"\0", 1)[0].decode("utf-8", "replace")
            if prefix:
                name = prefix + "/" + name
        name = pax.get("path") or long_name or name
        long_name, pax = None, {}
        while name.startswith("./"):
            name = name[2:]
        name = name.rstrip("/") if kind == b"5" else name
        if kind in (b"1", b"2"):
            raise Inconclusive(f"link member {name!r}: served bytes cannot be attributed")
        skipped = 0
        hasher = (hashlib.sha256() if hash_member and kind in (b"0", b"\0", b"7") and name and hash_member(name)
                  else None)
        while skipped < padded:  # skip data without retaining it
            chunk = stream.read(min(1 << 20, padded - skipped))
            if hasher is not None and chunk and skipped < size:
                hasher.update(chunk[:size - skipped])
            if not chunk:
                raise Inconclusive(f"TAR stream truncated inside member {name!r}")
            skipped += len(chunk)
        consumed += skipped
        if hasher is not None:
            hashes[name] = {"bytes": size, "sha256": hasher.hexdigest()}
        if kind in (b"0", b"\0", b"7"):
            if name:
                files.append((name, size))
        elif kind == b"5":
            dirs += 1
        else:
            others[kind.decode("latin-1")] = others.get(kind.decode("latin-1"), 0) + 1
    if not ended:
        raise Inconclusive("TAR stream ended without an end-of-archive marker")
    if not files:
        raise Inconclusive("TAR stream contains no regular files")
    result = manifest(files)
    if hash_member:
        canonical = "".join(f"{v['sha256']}  {k}\n" for k, v in sorted(hashes.items()))
        result["memberHashes"] = {"files": len(hashes), "setSha256": hashlib.sha256(canonical.encode()).hexdigest(),
                                  "records": hashes}
    result.update({"tarContainerBytes": consumed, "directoryMembers": dirs, "otherMembers": others,
                   "memberIndexSha256": result["pathSizeManifestSha256"]})
    return result


class _Inflating:
    """File-like view of the first zip member's uncompressed bytes, read from a zip stream."""

    def __init__(self, stream):
        head = _read_exact(stream, 30)
        if len(head) < 30 or head[:4] != b"PK\x03\x04":
            raise PayloadError("not a zip stream (no local file header)")
        _, flags, method, _, _, crc, csize, usize, nlen, xlen = struct.unpack("<HHHHHIIIHH", head[4:30])
        self.name = _read_exact(stream, nlen).decode("utf-8", "replace")
        _read_exact(stream, xlen)
        if method not in (0, 8):
            raise PayloadError(f"unsupported zip compression method {method}")
        if method == 0 and flags & 8:
            raise Inconclusive("stored zip member with data descriptor: length unknown")
        self.stream, self.method, self.crc_expected = stream, method, None if flags & 8 else crc
        self.remaining = csize if not flags & 8 else None
        self.inflater = zlib.decompressobj(-15) if method == 8 else None
        self.header_bytes = 30 + nlen + xlen
        self.buffer, self.crc, self.compressed, self.uncompressed, self.done = b"", 0, self.header_bytes, 0, False
        self.usize_header = None if flags & 8 else usize

    def _fill(self):
        while not self.buffer and not self.done:
            want = 1 << 20 if self.remaining is None else min(1 << 20, self.remaining)
            chunk = self.stream.read(want) if want else b""
            if self.method == 0:
                if not chunk:
                    if self.remaining:
                        raise Inconclusive("zip stream truncated inside the stored member")
                    self.done = True
                    break
                self.remaining -= len(chunk)
                self.compressed += len(chunk)
                out = chunk
            else:
                if not chunk:
                    if not self.inflater.eof:
                        raise Inconclusive("zip stream truncated inside the deflated member")
                    self.done = True
                    break
                out = self.inflater.decompress(chunk)
                used = len(chunk) - len(self.inflater.unused_data)
                self.compressed += used
                if self.remaining is not None:
                    self.remaining -= used
                if self.inflater.eof:
                    self.done = True
            self.crc = zlib.crc32(out, self.crc)
            self.uncompressed += len(out)
            self.buffer = out

    def read(self, n=-1):
        self._fill()
        if n is None or n < 0:
            n = len(self.buffer)
        out, self.buffer = self.buffer[:n], self.buffer[n:]
        return out

    def finish(self):
        while not self.done:
            self.buffer = b""
            self._fill()
        if self.crc_expected is not None and self.crc != self.crc_expected:
            raise PayloadError("zip member CRC-32 mismatch")
        if self.usize_header is not None and self.uncompressed != self.usize_header:
            raise Inconclusive("zip member size disagrees with its header")
        return {"member": self.name, "memberCompressedBytes": self.compressed - self.header_bytes,
                "memberUncompressedBytes": self.uncompressed, "crc32": f"{self.crc:08x}"}


class _Hashing:
    """Pass-through reader that counts and SHA-256 hashes every byte read from the archive stream."""

    def __init__(self, stream):
        self.stream, self.sha, self.count = stream, hashlib.sha256(), 0

    def read(self, n=-1):
        data = self.stream.read(n)
        self.sha.update(data)
        self.count += len(data)
        return data


def measure_zip_stream(stream, hash_member=None):
    stream = _Hashing(stream)
    member = _Inflating(stream)
    if member.name != "artifact.tar":
        raise PayloadError(f"first zip member is {member.name!r}, not artifact.tar")
    result = measure_tar(member, hash_member)
    result["zipMember"] = member.finish()
    if result["zipMember"]["memberUncompressedBytes"] != result["tarContainerBytes"]:
        raise Inconclusive("TAR container bytes disagree with the inflated member size")
    while stream.read(1 << 20):  # drain data descriptor and central directory into the archive digest
        pass
    result["archive"] = {"bytes": stream.count, "sha256": stream.sha.hexdigest(),
                         "method": "counted and SHA-256 hashed in-stream over every byte received"}
    return result


# --- Zip envelope (central directory) through range reads ----------------------------------

def read_envelope(read_range, total):
    """read_range(start, length) -> bytes. Returns the zip central-directory entries."""
    if total < 22:
        raise PayloadError("zip shorter than an end-of-central-directory record")
    tail_len = min(total, 65557 + 20 + 56)
    tail = read_range(total - tail_len, tail_len)
    at = tail.rfind(b"PK\x05\x06")
    if at < 0:
        raise PayloadError("no end-of-central-directory record")
    entries_total, cd_size, cd_offset = struct.unpack("<HII", tail[at + 10:at + 20])
    if 0xFFFFFFFF in (cd_size, cd_offset) or entries_total == 0xFFFF:
        loc = tail.rfind(b"PK\x06\x07", 0, at)
        if loc < 0:
            raise PayloadError("zip64 sizes without a zip64 locator")
        (z64_offset,) = struct.unpack("<Q", tail[loc + 8:loc + 16])
        rec = read_range(z64_offset, 56)
        if rec[:4] != b"PK\x06\x06":
            raise PayloadError("bad zip64 end-of-central-directory record")
        entries_total, cd_size, cd_offset = struct.unpack("<QQQ", rec[32:56])
    cd = read_range(cd_offset, cd_size)
    entries, i = [], 0
    for _ in range(entries_total):
        if cd[i:i + 4] != b"PK\x01\x02":
            raise PayloadError("bad central-directory entry")
        method, _, _, crc, csize, usize, nlen, xlen, clen = struct.unpack("<HHHIIIHHH", cd[i + 10:i + 34])
        (offset,) = struct.unpack("<I", cd[i + 42:i + 46])
        name = cd[i + 46:i + 46 + nlen].decode("utf-8", "replace")
        extra = cd[i + 46 + nlen:i + 46 + nlen + xlen]
        j = 0
        while j + 4 <= len(extra):
            tag, length = struct.unpack("<HH", extra[j:j + 4])
            if tag == 1:
                values, k = list(struct.unpack(f"<{length // 8}Q", extra[j + 4:j + 4 + length // 8 * 8])), 0
                if usize == 0xFFFFFFFF:
                    usize, k = values[k], k + 1
                if csize == 0xFFFFFFFF:
                    csize, k = values[k], k + 1
                if offset == 0xFFFFFFFF:
                    offset = values[k]
            j += 4 + length
        entries.append({"name": name, "method": method, "compressedBytes": csize,
                        "uncompressedBytes": usize, "crc32": f"{crc:08x}", "localHeaderOffset": offset})
        i += 46 + nlen + xlen + clen
    return {"archiveBytes": total, "centralDirectoryBytes": cd_size, "entries": entries}


def envelope_bounds(env, member_count_estimate=None):
    """From the envelope alone: an upper bound and, given an estimated member count, an inferred lower
    bound on regular-file bytes. Never a `within` authority (the lower bound is not measured)."""
    tars = [e for e in env["entries"] if e["name"] == "artifact.tar"]
    if len(tars) != 1:
        raise Inconclusive("artifact zip does not hold exactly one artifact.tar")
    tar = tars[0]["uncompressedBytes"]
    out = {"tarContainerBytes": tar, "regularFileBytesUpperBound": tar - 1024,
           "upperBoundMethod": "TAR container bytes minus the two end-of-archive blocks"}
    if member_count_estimate is not None:
        # Per member: one 512-byte header, < 512 bytes of padding, and (names > 100 bytes) at most one
        # GNU long-name header plus its data block. 2,048 bytes/member over-covers every case R0017 met.
        out["regularFileBytesInferredLowerBound"] = tar - 10240 - 2048 * member_count_estimate
        out["lowerBoundMethod"] = (f"TAR bytes - 10240 record padding - 2048 x {member_count_estimate} "
                                   "estimated members (tree projection); INFERRED, not measured")
    return out


def envelope_verdict(bounds, bound):
    """`within` is sound from the envelope (regular bytes <= TAR bytes - 1024); `exceeds` is not,
    because the lower bound rests on an estimated member count. So: within, or inconclusive with an
    `inferredVerdict` stated separately."""
    verdict(0, bound)
    if bounds["regularFileBytesUpperBound"] <= bound:
        return {"verdict": "within", "verdictBasis": "envelope upper bound (TAR container) <= bound"}
    out = {"verdict": "inconclusive",
           "reason": "envelope only: regular-file bytes not measured (full stream not run); "
                     "the upper bound does not prove `within`"}
    lower = bounds.get("regularFileBytesInferredLowerBound")
    if lower is not None:
        out["inferredVerdict"] = verdict(max(lower, 0), bound)
    return out


# --- read-only GitHub API ------------------------------------------------------------------

class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def _token():
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        raise Inconclusive("no GH_TOKEN/GITHUB_TOKEN for the authenticated artifact readback")
    return token


def _api(path):
    req = urllib.request.Request(f"https://api.github.com/{path}", headers={
        "Authorization": f"Bearer {_token()}", "Accept": "application/vnd.github+json",
        "User-Agent": "pages-payload-instrument"})
    with urllib.request.urlopen(req, timeout=60) as response:
        return json.load(response)


def artifact_status(meta):
    """Admission of a listed artifact: expired, missing or non-Pages artifacts are inconclusive."""
    if not meta:
        raise Inconclusive("run has no github-pages artifact")
    if meta.get("expired"):
        raise Inconclusive(f"artifact {meta.get('id')} expired at {meta.get('expires_at')}")
    if meta.get("name") != "github-pages":
        raise Inconclusive(f"artifact {meta.get('id')} is {meta.get('name')!r}, not github-pages")
    return meta


def _signed_url(artifact_id):
    opener = urllib.request.build_opener(_NoRedirect)
    req = urllib.request.Request(f"https://api.github.com/repos/{REPO}/actions/artifacts/{artifact_id}/zip",
                                 headers={"Authorization": f"Bearer {_token()}", "User-Agent": "pages-payload-instrument"})
    try:
        opener.open(req, timeout=60)
    except urllib.error.HTTPError as error:
        if error.code in (301, 302, 303, 307, 308) and error.headers.get("Location"):
            return error.headers["Location"]
        if error.code == 410:
            raise Inconclusive("artifact gone (410): expired") from None
        raise
    raise PayloadError("artifact download did not redirect to signed storage")


def _range_reader(url):
    meta = {}

    def read_range(start, length):
        req = urllib.request.Request(url, headers={"Range": f"bytes={start}-{start + length - 1}",
                                                   "User-Agent": "pages-payload-instrument"})
        with urllib.request.urlopen(req, timeout=60) as response:
            if response.status != 206:
                raise PayloadError(f"storage ignored the range request (HTTP {response.status})")
            meta["contentRange"] = response.headers.get("Content-Range", "")
            meta["requestedBytes"] = meta.get("requestedBytes", 0) + length
            data = response.read()
        if len(data) != length:
            raise Inconclusive("short range read")
        return data
    return read_range, meta


def artifact_readback(run_id, stream=False):
    run = _api(f"repos/{REPO}/actions/runs/{run_id}")
    listing = _api(f"repos/{REPO}/actions/runs/{run_id}/artifacts")
    meta = artifact_status(next((a for a in listing.get("artifacts", []) if a.get("name") == "github-pages"), None))
    receipt = {"source": "deployed-artifact", "runId": run_id, "runName": run.get("name"),
               "event": run.get("event"), "conclusion": run.get("conclusion"),
               "sourceCommit": run.get("head_sha"), "headBranch": run.get("head_branch"),
               "artifact": {k: meta.get(k) for k in ("id", "name", "size_in_bytes", "digest", "created_at",
                                                     "expires_at")}}
    if run.get("conclusion") != "success":
        raise Inconclusive(f"run {run_id} concluded {run.get('conclusion')!r}")
    url = _signed_url(meta["id"])
    read_range, http = _range_reader(url)
    probe = read_range(0, 30)
    total = int(http["contentRange"].rsplit("/", 1)[1])
    if total != meta["size_in_bytes"]:
        raise Inconclusive("stored archive size disagrees with the API size_in_bytes")
    receipt["envelope"] = read_envelope(read_range, total)
    receipt["envelope"]["firstLocalHeaderIsZip"] = probe[:4] == b"PK\x03\x04"
    receipt["envelope"]["bytesTransferredByRangeReads"] = http["requestedBytes"]
    if stream:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "pages-payload-instrument"}),
                                    timeout=600) as response:
            measured = measure_zip_stream(response, is_protected)
        archive = measured["archive"]
        if archive["bytes"] != meta["size_in_bytes"]:
            raise PayloadError(f"streamed archive is {archive['bytes']} bytes, API size_in_bytes {meta['size_in_bytes']}")
        if meta.get("digest") and meta["digest"] != "sha256:" + archive["sha256"]:
            raise PayloadError(f"streamed archive sha256:{archive['sha256']} differs from API digest {meta['digest']}")
        entry = next(e for e in receipt["envelope"]["entries"] if e["name"] == "artifact.tar")
        if (measured["zipMember"]["crc32"], measured["tarContainerBytes"]) != (entry["crc32"],
                                                                              entry["uncompressedBytes"]):
            raise PayloadError("streamed artifact.tar disagrees with the central directory (CRC/size)")
        receipt["measured"] = measured
    return receipt


# --- advisory projection and census ----------------------------------------------------------

def _git(root, *args):
    return subprocess.check_output(["git", *args], cwd=root)


def config_excludes(text):
    out, inside = [], False
    for line in text.splitlines():
        stripped = line.split("#", 1)[0].rstrip()
        if not stripped.strip():
            continue
        if re.match(r"^exclude\s*:", stripped):
            inside = True
            continue
        if inside and stripped.lstrip().startswith("- "):
            out.append(stripped.strip()[2:].strip().strip("'\""))
        elif not stripped.startswith((" ", "\t", "-")):
            inside = False
    return out


def jekyll_excluded(path, excludes):
    """Mirror of Jekyll 3.10 EntryFilter for plain prefixes: a string start_with? match (not a path
    component match), plus Jekyll's skip of any path component starting with '.' or '_'."""
    if any(part.startswith((".", "_")) for part in path.split("/")):
        return True
    return any(path.startswith(e) for e in excludes)


def project_listing(listing, excludes):
    """listing: [(path, size)]. Returns the advisory published projection and what it removes."""
    kept, removed, collateral = [], [], []
    for path, size in listing:
        if jekyll_excluded(path, excludes):
            if not any(part.startswith((".", "_")) for part in path.split("/")):
                removed.append((path, size))
                if not any(path == e.rstrip("/") or path.startswith(e.rstrip("/") + "/") for e in excludes):
                    collateral.append(path)
        else:
            kept.append((path, size))
    protected_hit = sorted(p for p, _ in removed if p in PROTECTED_FILES or p.startswith(PROTECTED_PREFIXES))
    return {"projectedFiles": len(kept), "projectedBytes": sum(s for _, s in kept),
            "removedFiles": len(removed), "removedBytes": sum(s for _, s in removed),
            "removedPathsNotUnderADirectoryPrefix": collateral[:50],
            "protectedPathsRemoved": protected_hit,
            "removedManifestSha256": hashlib.sha256(
                "".join(f"{s}  {p}\n" for p, s in sorted(removed)).encode()).hexdigest()}


def tree_listing(root, commit):
    rows = []
    for record in _git(root, "ls-tree", "-r", "-l", "-z", commit).decode("utf-8", "replace").split("\0"):
        if not record:
            continue
        meta, path = record.split("\t", 1)
        _, kind, _, size = meta.split()
        if kind == "blob":
            rows.append((path, int(size)))
    return rows


def project(root, commit, extra):
    config = _git(root, "show", f"{commit}:_config.yml").decode() if _has(root, commit, "_config.yml") else ""
    base = config_excludes(config)
    listing = tree_listing(root, commit)
    current = project_listing(listing, base)
    candidate = project_listing(listing, base + list(extra))
    return {"advisory": True, "commit": _git(root, "rev-parse", commit).decode().strip(),
            "method": "git blob sizes under Jekyll's '.'/'_' skip and _config.yml string-prefix excludes; "
                      "Markdown rendering and generated files are not modelled (R0017 calibration: 0.898 GB "
                      "estimate vs 897,967,831 measured bytes at PR 62)",
            "configExcludes": base, "extraExcludes": list(extra),
            "current": current, "withExtraExcludes": candidate}


def published_set(root, commit):
    config = _git(root, "show", f"{commit}:_config.yml").decode() if _has(root, commit, "_config.yml") else ""
    excludes = config_excludes(config)
    return excludes, {p: s for p, s in tree_listing(root, commit) if not jekyll_excluded(p, excludes)}


def published_diff(root, base, head):
    """Advisory G-07 projection: published-path diff between two commits under each one's own
    _config.yml. `removedOutsideNewExcludes` must be empty and `protectedPathsRemoved` must be empty."""
    base_ex, before = published_set(root, base)
    head_ex, after = published_set(root, head)
    new = [e for e in head_ex if e not in base_ex]
    removed = sorted(set(before) - set(after))
    outside = [p for p in removed if not any(p.startswith(e) for e in new)]
    protected = [p for p in removed if p in PROTECTED_FILES or p.startswith(PROTECTED_PREFIXES)]
    changed_protected = sorted(p for p in after if p in before and p != "_config.yml"
                               and (p in PROTECTED_FILES or p.startswith(PROTECTED_PREFIXES))
                               and before[p] != after[p])
    return {"advisory": True, "base": _git(root, "rev-parse", base).decode().strip(),
            "head": _git(root, "rev-parse", head).decode().strip(), "newExcludes": new,
            "basePublished": {"files": len(before), "bytes": sum(before.values())},
            "headPublished": {"files": len(after), "bytes": sum(after.values())},
            "removedFiles": len(removed), "removedBytes": sum(before[p] for p in removed),
            "addedPaths": sorted(set(after) - set(before)),
            "removedOutsideNewExcludes": outside, "protectedPathsRemoved": protected,
            "protectedPathsWithChangedSize": changed_protected}


def published_source_digest(root, commit):
    """Identity of the Jekyll *input* that reaches the site: sha256 over sorted "<blob sha>  <path>"
    records of every tracked blob the commit's own _config.yml does not exclude (plus _config.yml
    itself, which steers the build). Two commits with the same digest feed the pinned builder the same
    published source, so a hosted measurement of one binds to the other (R002B section 7)."""
    config = _git(root, "show", f"{commit}:_config.yml").decode() if _has(root, commit, "_config.yml") else ""
    excludes = config_excludes(config)
    records = []
    for record in _git(root, "ls-tree", "-r", "-z", commit).decode("utf-8", "replace").split("\0"):
        if not record:
            continue
        meta, path = record.split("\t", 1)
        _, kind, sha1 = meta.split()
        if kind == "blob" and (path == "_config.yml" or not jekyll_excluded(path, excludes)):
            records.append(f"{sha1}  {path}\n")
    records.sort()
    return {"commit": _git(root, "rev-parse", commit).decode().strip(),
            "tree": _git(root, "rev-parse", f"{commit}^{{tree}}").decode().strip(),
            "configExcludes": excludes, "publishedSourceFiles": len(records),
            "publishedSourceSha256": hashlib.sha256("".join(records).encode()).hexdigest()}


def _has(root, commit, path):
    return subprocess.run(["git", "cat-file", "-e", f"{commit}:{path}"], cwd=root,
                          capture_output=True).returncode == 0


LINK_RE = re.compile(r"\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)|(?:href|src)\s*=\s*[\"']([^\"']+)[\"']")
IO_RE = re.compile(r"https?://theislampill\.github\.io/salah_widget/[^\s)\]>\"'`]*")
GH_RE = re.compile(r"https?://github\.com/theislampill/salah_widget/(?:blob|tree|raw)/([^/\s)\]>\"'`]+)/"
                   r"([^\s)\]>\"'`#?]*)")
RAW_RE = re.compile(r"https?://raw\.githubusercontent\.com/theislampill/salah_widget/([^/\s)\]>\"'`]+)/"
                    r"([^\s)\]>\"'`#?]*)")


def _under(path, prefixes):
    return any(path == p or path.startswith(p.rstrip("/") + "/") for p in prefixes)


def census_text(texts, prefixes):
    """texts: iterable of (source id, text). Counts external links into the prefixes by host/ref."""
    io_all = io_hit = gh_hit_main = gh_hit_pinned = raw_hit_main = raw_hit_pinned = gh_all = 0
    other_refs, hits = {}, []
    commit_ref = re.compile(r"^[0-9a-f]{7,40}$")
    for source, text in texts:
        for url in IO_RE.findall(text or ""):
            io_all += 1
            rel = url.split("/salah_widget/", 1)[1].split("#", 1)[0].split("?", 1)[0]
            if _under(rel, prefixes):
                io_hit += 1
                hits.append({"source": source, "url": url})
        for ref, rel in GH_RE.findall(text or ""):
            gh_all += 1
            if _under(rel, prefixes):
                if commit_ref.match(ref):
                    gh_hit_pinned += 1
                elif ref == "main":
                    gh_hit_main += 1
                    hits.append({"source": source, "ref": ref, "path": rel})
                else:
                    other_refs[ref] = other_refs.get(ref, 0) + 1
        for ref, rel in RAW_RE.findall(text or ""):
            if _under(rel, prefixes):
                if commit_ref.match(ref):
                    raw_hit_pinned += 1
                elif ref == "main":
                    raw_hit_main += 1
                    hits.append({"source": source, "ref": ref, "path": rel, "raw": True})
                else:
                    other_refs[ref] = other_refs.get(ref, 0) + 1
    return {"githubIoUrls": io_all, "githubIoUrlsIntoPrefixes": io_hit,
            "githubComBlobTreeRawUrls": gh_all,
            "githubComUrlsIntoPrefixesPinnedToCommit": gh_hit_pinned,
            "githubComUrlsIntoPrefixesOnMain": gh_hit_main,
            "rawUrlsIntoPrefixesPinnedToCommit": raw_hit_pinned, "rawUrlsIntoPrefixesOnMain": raw_hit_main,
            "urlsIntoPrefixesOnOtherRefs": other_refs, "breakingHits": hits[:200]}


def _blobs(root, commit, paths):
    """Read many blobs at a commit through one `git cat-file --batch` process."""
    proc = subprocess.Popen(["git", "cat-file", "--batch"], cwd=root, stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE)
    out = {}
    try:
        for path in paths:
            proc.stdin.write(f"{commit}:{path}\n".encode())
            proc.stdin.flush()
            header = proc.stdout.readline().split()
            if len(header) < 3:
                raise PayloadError(f"git cat-file failed for {path}")
            data = _read_exact(proc.stdout, int(header[2]))
            proc.stdout.readline()
            out[path] = data.decode("utf-8", "replace")
    finally:
        proc.stdin.close()
        proc.wait()
    return out


def census_repo(root, commit, prefixes):
    """Relative Markdown/HTML links from tracked .md/.html files outside the prefixes into them, plus
    string reads of the prefixes from tests/, tools/ and runtime sources (option b's move risk)."""
    paths = [p for p, _ in tree_listing(root, commit)]
    readers = ("tests/", "tools/", "src/", "real-sky/", "moon/src/", ".github/")
    wanted = [p for p in paths if not _under(p, prefixes) and (p.endswith((".md", ".html")) or p.startswith(readers))]
    blobs = _blobs(root, commit, wanted)
    relative, by_file, reads, io_links, every, mentions = 0, {}, [], 0, [], 0
    for path in paths:
        if _under(path, prefixes) or not path.endswith((".md", ".html")):
            continue
        text = blobs[path]
        mentions += sum(text.count(p) for p in prefixes)
        io_links += sum(1 for u in IO_RE.findall(text)
                        if _under(u.split("/salah_widget/", 1)[1].split("#", 1)[0], prefixes))
        base = path.rsplit("/", 1)[0] if "/" in path else ""
        for a, b in LINK_RE.findall(text):
            target = (a or b).split("#", 1)[0].split("?", 1)[0]
            if not target or re.match(r"^[a-z][a-z0-9+.-]*:", target, re.I) or target.startswith("/"):
                continue
            parts = []
            for part in (base + "/" + target if base else target).split("/"):
                if part in ("", "."):
                    continue
                if part == "..":
                    if parts:
                        parts.pop()
                    continue
                parts.append(part)
            if _under("/".join(parts), prefixes):
                relative += 1
                by_file[path] = by_file.get(path, 0) + 1
                every.append({"file": path, "target": "/".join(parts)})
    for path in paths:
        if not path.startswith(readers) or _under(path, prefixes):
            continue
        text = blobs[path]
        for p in prefixes:
            if p in text:
                reads.append({"file": path, "prefix": p, "occurrences": text.count(p)})
    return {"relativeLinksIntoPrefixes": relative, "filesWithRelativeLinks": len(by_file),
            "relativeLinksByFile": dict(sorted(by_file.items(), key=lambda kv: -kv[1])),
            "relativeLinks": every,
            "githubIoUrlsIntoPrefixesInRepo": io_links,
            "literalPrefixMentionsInMarkdownAndHtml": mentions,
            "codeAndTestReadsOfPrefixes": reads}


# --- CLI ---------------------------------------------------------------------------------------

def _emit(receipt, out):
    text = json.dumps(receipt, indent=2, sort_keys=False) + "\n"
    if out:
        Path(out).write_text(text, encoding="utf-8")
    summary = {k: receipt.get(k) for k in ("schema", "source", "verdict", "bound", "error")}
    measured = receipt.get("measured") or {}
    summary.update({k: measured.get(k) for k in ("regularFiles", "regularFileBytes", "tarContainerBytes")
                    if k in measured})
    print(json.dumps(summary))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="mode", required=True)
    for mode in ("site", "tar", "zip", "artifact"):
        p = sub.add_parser(mode)
        p.add_argument("--bound", type=int, default=DEFAULT_BOUND)
        p.add_argument("--out")
        p.add_argument("--commit", help="source commit the measurement binds (receipt identity)")
        if mode == "site":
            p.add_argument("--site", required=True)
            p.add_argument("--root", help="repository root: also check protected consumers byte-identical")
            p.add_argument("--manifest-out", help="also write the '<bytes>  <path>' manifest (for G-07)")
        elif mode in ("tar", "zip"):
            p.add_argument("--file", required=True, help="path, or - for stdin")
        else:
            p.add_argument("--run-id", required=True, type=int)
            p.add_argument("--stream", action="store_true",
                           help="full M1 stream of the artifact (owner permission required: large transfer)")
            p.add_argument("--member-estimate", type=int)
    p = sub.add_parser("project")
    p.add_argument("--commit", default="HEAD")
    p.add_argument("--exclude", action="append", default=[])
    p.add_argument("--out")
    p = sub.add_parser("compare-sites")
    p.add_argument("--base-manifest", required=True)
    p.add_argument("--head-manifest", required=True)
    p.add_argument("--exclude", action="append", required=True)
    p.add_argument("--changed-from", help="file listing the candidate's intentionally changed paths "
                                           "(git diff --name-only BASE HEAD), one per line")
    p.add_argument("--out")
    p = sub.add_parser("source-digest")
    p.add_argument("--commit", default="HEAD")
    p.add_argument("--out")
    p = sub.add_parser("published-diff")
    p.add_argument("--base", required=True)
    p.add_argument("--head", default="HEAD")
    p.add_argument("--out")
    p = sub.add_parser("census")
    p.add_argument("--commit", default="HEAD")
    p.add_argument("--prefix", action="append", required=True)
    p.add_argument("--texts-jsonl", action="append", default=[],
                   help="JSON lines with html_url/url and body fields (read-only gh api --paginate dump)")
    p.add_argument("--out")
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[1]

    if args.mode == "compare-sites":
        receipt = {"schema": SCHEMA + "#compare-sites", **compare_manifests(
            Path(args.base_manifest).read_text(encoding="utf-8"),
            Path(args.head_manifest).read_text(encoding="utf-8"), args.exclude,
            Path(args.changed_from).read_text(encoding="utf-8").splitlines() if args.changed_from else ())}
        text = json.dumps(receipt, indent=2) + "\n"
        if args.out:
            Path(args.out).write_text(text, encoding="utf-8")
        print(json.dumps({k: receipt[k] for k in ("removedFiles", "onlyEvidenceRemoved")}))
        return 0 if receipt["onlyEvidenceRemoved"] else 1
    if args.mode in ("project", "census", "published-diff", "source-digest"):
        if args.mode == "source-digest":
            receipt = {"schema": SCHEMA + "#source-digest", **published_source_digest(root, args.commit)}
        elif args.mode == "project":
            receipt = {"schema": SCHEMA + "#projection", **project(root, args.commit, args.exclude)}
        elif args.mode == "published-diff":
            receipt = {"schema": SCHEMA + "#published-diff", **published_diff(root, args.base, args.head)}
        else:
            texts = []
            for name in args.texts_jsonl:
                for line in Path(name).read_text(encoding="utf-8").splitlines():
                    if line.strip():
                        row = json.loads(line)
                        texts.append((row.get("html_url") or row.get("url") or "?", row.get("body") or ""))
            receipt = {"schema": SCHEMA + "#census", "advisory": True,
                       "commit": _git(root, "rev-parse", args.commit).decode().strip(), "prefixes": args.prefix,
                       "repository": census_repo(root, args.commit, args.prefix),
                       "issueAndCommentTexts": {"records": len(texts), **census_text(texts, args.prefix)}}
        text = json.dumps(receipt, indent=2) + "\n"
        if args.out:
            Path(args.out).write_text(text, encoding="utf-8")
        else:
            sys.stdout.write(text)
        return 0

    receipt = {"schema": SCHEMA, "source": {"site": "ci-build", "artifact": "deployed-artifact"}.get(
        args.mode, f"{args.mode}-stream"), "bound": args.bound, "builderImage": BUILDER_IMAGE,
        "builderImageRepoDigests": os.environ.get("PAGES_BUILDER_DIGESTS"),
        "sourceCommit": args.commit, "workflowRunId": os.environ.get("GITHUB_RUN_ID"),
        "verdict": "inconclusive"}
    try:
        verdict(0, args.bound)  # validate the bound before measuring
        if args.mode == "site":
            receipt["measured"] = measure_site(args.site)
            if args.manifest_out:
                Path(args.manifest_out).write_text(site_manifest_lines(args.site), encoding="utf-8")
            if args.root:
                receipt["protectedConsumers"] = protected_consumers(args.root, args.site)
        elif args.mode in ("tar", "zip"):
            def measure(stream, _m=measure_tar if args.mode == "tar" else measure_zip_stream):
                return _m(stream, is_protected)
            if args.file == "-":
                receipt["measured"] = measure(sys.stdin.buffer)
            else:
                with open(args.file, "rb") as stream:
                    receipt["measured"] = measure(stream)
        else:
            back = artifact_readback(args.run_id, stream=args.stream)
            receipt.update({k: v for k, v in back.items() if k != "measured"})
            receipt["source"] = "deployed-artifact"
            receipt["sourceCommit"] = back["sourceCommit"]
            if args.commit and args.commit != back["sourceCommit"]:
                raise Inconclusive("artifact belongs to another commit: receipt cannot be reused")
            receipt["bounds"] = envelope_bounds(back["envelope"], args.member_estimate)
            if "measured" in back:
                receipt["measured"] = back["measured"]
            else:
                decided = envelope_verdict(receipt["bounds"], args.bound)
                receipt.update(decided)
                if decided["verdict"] == "within":
                    _emit(receipt, args.out)
                    return EXIT["within"]
                raise Inconclusive(decided["reason"])
        receipt["verdict"] = verdict(receipt["measured"]["regularFileBytes"], args.bound)
        receipt["verdictBasis"] = "measured regular-file bytes"
    except Inconclusive as error:
        receipt["verdict"] = "inconclusive"
        receipt["reason"] = str(error)
    except (PayloadError, OSError, ValueError, zlib.error, urllib.error.URLError,
            subprocess.CalledProcessError) as error:
        receipt["verdict"] = "error"
        receipt["error"] = f"{type(error).__name__}: {error}"
        _emit(receipt, args.out)
        return 3
    _emit(receipt, args.out)
    return EXIT[receipt["verdict"]]


if __name__ == "__main__":
    sys.exit(main())
