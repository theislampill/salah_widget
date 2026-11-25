#!/usr/bin/env python3
"""Private native-observation transport: standard-library Python and OpenSSL.

This is a new implementation, not the unavailable historical envelope source.
Encryption does not authenticate its sender. Independently authenticate the
repository, workflow commit, run and downloaded artifact before opening it.

The deliberately narrow CMS profile follows RFC 5083 section 2 and RFC 5084
section 3.2: one issuer/serial RSA3072 recipient, explicit SHA256 OAEP/MGF1,
id-data, AES256-GCM with a 12-byte nonce and 16-byte tag, and no attributes.
https://www.rfc-editor.org/rfc/rfc5083
https://www.rfc-editor.org/rfc/rfc5084

Source producers must be stopped before sealing. Input/output parent directories
and the selected OpenSSL installation are trusted local custody. The tool does
not defend against a concurrent process with the same account privileges.
"""
import argparse
import base64
import hashlib
import json
import mmap
import os
from pathlib import Path
import re
import shutil
import signal
import stat
import struct
import subprocess
import sys
import tempfile
import unicodedata
import zipfile


PROFILE = "CMS-AuthEnvelopedData-RSA3072-OAEP-SHA256-MGF1-SHA256-AES256GCM"
MAX_FILES = 20_000
MAX_FILE_BYTES = 1 << 30
MAX_TOTAL_BYTES = 4 << 30
MAX_MANIFEST_BYTES = 8 << 20
MAX_PATH_BYTES = 1024
MAX_ARCHIVE_BYTES = MAX_TOTAL_BYTES + (64 << 20)
MAX_CMS_BYTES = MAX_ARCHIVE_BYTES + (1 << 20)
CHUNK = 1 << 20
MANIFEST = "manifest.json"
HEX256 = re.compile(r"[0-9a-f]{64}\Z")
AUTH_ENV = bytes.fromhex("2a864886f70d0109100117")
DATA = bytes.fromhex("2a864886f70d010701")
RSA = bytes.fromhex("2a864886f70d010101")
OAEP = bytes.fromhex("2a864886f70d010107")
MGF1 = bytes.fromhex("2a864886f70d010108")
SHA256 = bytes.fromhex("608648016503040201")
AES256_GCM = bytes.fromhex("60864801650304012e")


class Rejected(Exception):
    """Bounded public failure; never carries a private filename or child output."""


def require(condition, category):
    if not condition:
        raise Rejected(category)


class DER:
    """Definite, minimal DER reader with fixed-schema callers and zero-copy spans.

    Large encrypted OCTET STRING contents are never copied into Python memory.
    There is no recursive generic ASN.1 decoding or attacker-selected depth.
    """
    def __init__(self, data, start=0, end=None):
        self.data = data
        self.pos = start
        self.end = len(data) if end is None else end

    def take(self, tag):
        start = self.pos
        require(start + 2 <= self.end and self.data[start] == tag, "CMS structure")
        first = self.data[start + 1]
        cursor = start + 2
        if first < 128:
            size = first
        else:
            count = first & 127
            require(1 <= count <= 8 and cursor + count <= self.end, "DER length")
            require(self.data[cursor] != 0, "DER length")
            size = int.from_bytes(self.data[cursor:cursor + count], "big")
            require(size >= 128, "DER length")
            cursor += count
        require(size <= self.end - cursor, "DER length")
        self.pos = cursor + size
        return DER(self.data, cursor, self.pos)

    def done(self):
        require(self.pos == self.end, "unsupported structure")

    def value(self, maximum=65536):
        require(self.end - self.pos <= maximum, "DER field size")
        return bytes(self.data[self.pos:self.end])

    def oid(self, expected):
        require(self.take(6).value(32) == expected, "CMS algorithm")

    def integer(self, maximum=512):
        raw = self.take(2).value(maximum)
        require(raw and raw[0] < 128, "DER integer")
        require(len(raw) == 1 or raw[0] != 0 or raw[1] >= 128, "DER integer")
        return int.from_bytes(raw, "big")

    def encoded(self, tag):
        start = self.pos
        self.take(tag)
        require(self.pos - start <= 65536, "DER field size")
        return bytes(self.data[start:self.pos])


def sha256_identifier(reader):
    algorithm = reader.take(0x30)
    algorithm.oid(SHA256)
    # OpenSSL emits NULL parameters. Absent parameters are also defined for
    # SHA-256 AlgorithmIdentifier; no other parameter is supported.
    if algorithm.pos != algorithm.end:
        algorithm.take(5).done()
    algorithm.done()


def inspect_cms(path, recipient):
    """Reject substitution/trailing fields BEFORE invoking a generic decryptor."""
    with path.open("rb") as stream, mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ) as body:
        whole = DER(body)
        content = whole.take(0x30)
        whole.done()
        content.oid(AUTH_ENV)
        explicit = content.take(0xa0)
        content.done()
        envelope = explicit.take(0x30)
        explicit.done()
        require(envelope.integer() == 0, "CMS version")
        recipients = envelope.take(0x31)
        transport = recipients.take(0x30)
        recipients.done()  # Exactly one key-transport recipient; no alternatives.
        require(transport.integer() == 0, "recipient version")
        identity = transport.take(0x30)
        require(identity.encoded(0x30) == recipient["issuer"], "recipient identity")
        require(identity.integer() == recipient["serial"], "recipient identity")
        identity.done()
        algorithm = transport.take(0x30)
        algorithm.oid(OAEP)
        parameters = algorithm.take(0x30)
        algorithm.done()
        digest = parameters.take(0xa0)
        sha256_identifier(digest)
        digest.done()
        mask = parameters.take(0xa1)
        mask_algorithm = mask.take(0x30)
        mask.done()
        mask_algorithm.oid(MGF1)
        sha256_identifier(mask_algorithm)
        mask_algorithm.done()
        # pSpecified is the empty default and therefore omitted in DER.
        parameters.done()
        wrapped_key = transport.take(4)
        require(wrapped_key.end - wrapped_key.pos == 384, "RSA3072 wrapped key size")
        transport.done()
        encrypted = envelope.take(0x30)
        encrypted.oid(DATA)
        cipher = encrypted.take(0x30)
        cipher.oid(AES256_GCM)
        gcm = cipher.take(0x30)
        cipher.done()
        nonce = gcm.take(4)
        require(nonce.end - nonce.pos == 12, "GCM nonce")
        require(gcm.integer() == 16, "GCM tag length")
        gcm.done()
        ciphertext = encrypted.take(0x80)
        require(0 < ciphertext.end - ciphertext.pos <= MAX_ARCHIVE_BYTES, "ciphertext size")
        encrypted.done()
        tag = envelope.take(4)
        require(tag.end - tag.pos == 16, "GCM tag length")
        envelope.done()


def openssl(*args, input_bytes=None):
    try:
        result = subprocess.run(["openssl", *map(str, args)], input=input_bytes,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                timeout=300, check=False)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise Rejected("OpenSSL unavailable or timed out") from error
    require(result.returncode == 0, "OpenSSL rejected input")
    return result.stdout


def no_symlink_path(path):
    path = Path(os.path.abspath(path))
    for component in [*reversed(path.parents), path]:
        try:
            require(not stat.S_ISLNK(component.lstat().st_mode), "symlink path")
        except FileNotFoundError:
            pass
    return path


def open_regular(path):
    # O_NONBLOCK avoids waiting if a regular-file check races a FIFO replacement.
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        require(stat.S_ISREG(os.fstat(descriptor).st_mode), "nonregular input")
        return os.fdopen(descriptor, "rb")
    except BaseException:
        os.close(descriptor)
        raise


def read_bounded(path, maximum):
    with open_regular(path) as stream:
        require(os.fstat(stream.fileno()).st_size <= maximum, "input size")
        data = stream.read(maximum + 1)
    require(len(data) <= maximum, "input size")
    return data


def recipient_certificate(path, staging):
    raw = read_bounded(no_symlink_path(path), 128 << 10)
    if raw.lstrip().startswith(b"-----BEGIN CERTIFICATE-----"):
        match = re.fullmatch(rb"\s*-----BEGIN CERTIFICATE-----\s+([A-Za-z0-9+/=\s]+)"
                             rb"-----END CERTIFICATE-----\s*", raw)
        require(match is not None, "certificate format")
        try:
            der = base64.b64decode(re.sub(rb"\s", b"", match[1]), validate=True)
        except ValueError as error:
            raise Rejected("certificate format") from error
    else:
        der = raw
    root = DER(der)
    certificate = root.take(0x30)
    root.done()
    tbs = certificate.take(0x30)
    if tbs.data[tbs.pos] == 0xa0:
        version = tbs.take(0xa0)
        require(version.integer() in (1, 2), "certificate version")
        version.done()
    serial = tbs.integer()
    require(serial > 0, "certificate serial")
    tbs.take(0x30)  # OpenSSL validates the full certificate below.
    issuer = tbs.encoded(0x30)
    tbs.take(0x30)  # validity
    tbs.take(0x30)  # subject
    spki_der = tbs.encoded(0x30)
    spki_root = DER(spki_der)
    spki = spki_root.take(0x30)
    spki_root.done()
    algorithm = spki.take(0x30)
    algorithm.oid(RSA)
    algorithm.take(5).done()
    algorithm.done()
    bits = spki.take(3).value(1024)
    spki.done()
    require(bits and bits[0] == 0, "RSA public key")
    key_root = DER(bits[1:])
    key = key_root.take(0x30)
    key_root.done()
    modulus = key.integer()
    exponent = key.integer(16)
    key.done()
    require(modulus.bit_length() == 3072 and modulus & 1, "RSA3072 required")
    require(exponent >= 65537 and exponent & 1, "RSA exponent")
    pem = openssl("x509", "-inform", "DER", "-outform", "PEM", input_bytes=der)
    snapshot = staging / "recipient.crt"
    snapshot.write_bytes(pem)
    snapshot.chmod(0o600)
    return {"issuer": issuer, "serial": serial, "spki": spki_der,
            "sha256": hashlib.sha256(der).hexdigest(), "path": snapshot}


def safe_name(name):
    require(type(name) is str and bool(name), "archive path")
    require(unicodedata.normalize("NFC", name) == name, "archive path")
    require(len(name.encode("utf-8")) <= MAX_PATH_BYTES, "archive path length")
    require(not any(ord(c) < 32 or ord(c) == 127 or c in "\\:" for c in name), "archive path")
    parts = name.split("/")
    for part in parts:
        require(part not in ("", ".", "..") and not part.endswith((".", " ")), "archive path")
        require(len(part.encode("utf-8")) <= 255, "archive component length")
        stem = part.split(".", 1)[0].upper()
        require(stem not in {"CON", "PRN", "AUX", "NUL", *["COM" + str(i) for i in range(1, 10)],
                             *["LPT" + str(i) for i in range(1, 10)]}, "archive path")
    return name


def distinct_paths(names):
    files = set()
    directories = set()
    for name in names:
        folded = safe_name(name).casefold()
        require(folded not in files and folded not in directories, "duplicate archive path")
        parts = folded.split("/")
        for i in range(1, len(parts)):
            parent = "/".join(parts[:i])
            require(parent not in files, "overlapping archive paths")
            directories.add(parent)
        files.add(folded)


def source_files(descriptor, prefix=""):
    for name in sorted(os.listdir(descriptor)):
        relative = safe_name(prefix + name)
        info = os.stat(name, dir_fd=descriptor, follow_symlinks=False)
        if stat.S_ISDIR(info.st_mode):
            child = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                            dir_fd=descriptor)
            try:
                yield from source_files(child, relative + "/")
            finally:
                os.close(child)
        else:
            require(stat.S_ISREG(info.st_mode), "nonregular source")
            child = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                            dir_fd=descriptor)
            try:
                current = os.fstat(child)
                require(stat.S_ISREG(current.st_mode), "nonregular source")
                require((info.st_dev, info.st_ino) == (current.st_dev, current.st_ino), "source changed")
                yield relative, child, current
            finally:
                os.close(child)


def zip_info(name, size):
    info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    info.create_system = 3
    info.external_attr = (stat.S_IFREG | 0o600) << 16
    info.compress_type = zipfile.ZIP_STORED
    info.file_size = size
    return info


def create_archive(source, target):
    files = []
    total = 0
    descriptor = os.open(source, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        with zipfile.ZipFile(target, "x", compression=zipfile.ZIP_STORED, allowZip64=True) as archive:
            for name, child, before in source_files(descriptor):
                require(len(files) < MAX_FILES and before.st_size <= MAX_FILE_BYTES, "source bounds")
                total += before.st_size
                require(total <= MAX_TOTAL_BYTES, "source total size")
                digest = hashlib.sha256()
                size = 0
                with archive.open(zip_info("files/" + name, before.st_size), "w") as member:
                    while True:
                        chunk = os.read(child, CHUNK)
                        if not chunk:
                            break
                        size += len(chunk)
                        require(size <= before.st_size, "source changed")
                        digest.update(chunk)
                        member.write(chunk)
                after = os.fstat(child)
                require(size == before.st_size and
                        (before.st_size, before.st_mtime_ns, before.st_ctime_ns) ==
                        (after.st_size, after.st_mtime_ns, after.st_ctime_ns), "source changed")
                files.append({"path": name, "size": size, "sha256": digest.hexdigest()})
            distinct_paths(row["path"] for row in files)
            manifest = json.dumps({"schema": "salah-native-capture/1", "files": files},
                                  ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode()
            require(len(manifest) <= MAX_MANIFEST_BYTES, "manifest size")
            archive.writestr(zip_info(MANIFEST, len(manifest)), manifest)
    finally:
        os.close(descriptor)
    target.chmod(0o600)
    require(target.stat().st_size <= MAX_ARCHIVE_BYTES, "archive size")


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON key")
        result[key] = value
    return result


def load_json(data):
    try:
        return json.loads(data, object_pairs_hook=unique_object,
                          parse_constant=lambda value: (_ for _ in ()).throw(Rejected("JSON constant")))
    except (ValueError, UnicodeError, RecursionError) as error:
        raise Rejected("JSON format") from error


def archive_directory(stream, size):
    """Bound central-directory allocation before Python's ZIP decoder sees it."""
    require(22 <= size <= MAX_ARCHIVE_BYTES, "archive size")
    stream.seek(size - 22)
    fields = struct.unpack("<4s4H2IH", stream.read(22))
    signature, disk, directory_disk, on_disk, count, length, offset, comment = fields
    require(signature == b"PK\x05\x06" and disk == directory_disk == comment == 0,
            "archive end record")
    require(on_disk == count and count <= MAX_FILES + 1, "archive member count")
    end = size - 22
    if size >= 98:
        stream.seek(size - 42)
        locator = stream.read(20)
        if locator[:4] == b"PK\x06\x07":
            _, record_disk, record_offset, disks = struct.unpack("<4sIQI", locator)
            require(record_disk == 0 and disks == 1 and record_offset == size - 98,
                    "ZIP64 locator")
            stream.seek(record_offset)
            values = struct.unpack("<4sQ2H2I4Q", stream.read(56))
            sig, record_size, made, needed, d1, d2, n1, n2, length64, offset64 = values
            require(sig == b"PK\x06\x06" and record_size == 44 and needed == 45,
                    "ZIP64 record")
            require(d1 == d2 == 0 and n1 == n2 == count, "ZIP64 member count")
            require(length == min(length64, 0xffffffff) and offset == min(offset64, 0xffffffff),
                    "ZIP64 disagreement")
            length, offset, end = length64, offset64, record_offset
    require(1 <= count <= MAX_FILES + 1 and length <= (48 << 20), "archive directory bounds")
    require(offset + length == end and offset > 0, "archive directory position")
    return count, offset


def verify_archive_headers(stream, infos, directory_offset):
    next_header = 0
    for info in infos:
        require(info.header_offset == next_header, "archive gaps or overlapping members")
        require(info.orig_filename == info.filename and not info.is_dir(), "archive member name")
        safe_name(info.filename)
        require(info.create_system == 3 and stat.S_ISREG(info.external_attr >> 16), "archive member type")
        require(info.compress_type == zipfile.ZIP_STORED and info.flag_bits in (0, 0x800),
                "unsupported ZIP encoding")
        require(info.compress_size == info.file_size, "stored member size")
        require(info.comment == b"", "ZIP comment")
        if info.extra:
            require(len(info.extra) == 12, "ZIP extra field")
            kind, length, offset = struct.unpack("<HHQ", info.extra)
            require(kind == 1 and length == 8 and offset == info.header_offset, "ZIP64 offset")
        stream.seek(next_header)
        header = stream.read(30)
        require(len(header) == 30, "ZIP local header")
        values = struct.unpack("<4s5H3I2H", header)
        signature, version, flags, compression, clock, date, crc, compressed, size, namesize, extra = values
        require(signature == b"PK\x03\x04" and version == 20 and extra == 0, "ZIP local header")
        require((flags, compression, crc, compressed, size) ==
                (info.flag_bits, 0, info.CRC, info.compress_size, info.file_size), "ZIP header disagreement")
        name = stream.read(namesize)
        expected = info.filename.encode("utf-8" if flags == 0x800 else "ascii")
        require(name == expected, "ZIP filename disagreement")
        next_header += 30 + namesize + size
        require(next_header <= directory_offset, "ZIP member bounds")
    require(next_header == directory_offset, "archive trailing content")


def extract_verified(archive_path, target):
    with archive_path.open("rb") as stream:
        count, offset = archive_directory(stream, archive_path.stat().st_size)
        with zipfile.ZipFile(stream, "r") as archive:
            infos = archive.infolist()
            require(len(infos) == count, "archive member count")
            verify_archive_headers(stream, infos, offset)
            names = [info.filename for info in infos]
            distinct_paths(names)
            require(names.count(MANIFEST) == 1, "private manifest missing")
            by_name = {info.filename: info for info in infos}
            require(by_name[MANIFEST].file_size <= MAX_MANIFEST_BYTES, "manifest size")
            manifest = load_json(archive.read(MANIFEST))
            require(type(manifest) is dict and set(manifest) == {"schema", "files"} and
                    manifest["schema"] == "salah-native-capture/1" and type(manifest["files"]) is list,
                    "private manifest format")
            rows = manifest["files"]
            require(len(rows) <= MAX_FILES, "archive member count")
            expected = {MANIFEST}
            total = 0
            private_names = []
            for row in rows:
                require(type(row) is dict and set(row) == {"path", "size", "sha256"}, "manifest member")
                name = safe_name(row["path"])
                require(type(row["size"]) is int and 0 <= row["size"] <= MAX_FILE_BYTES,
                        "manifest member size")
                require(type(row["sha256"]) is str and HEX256.fullmatch(row["sha256"]), "manifest hash")
                total += row["size"]
                require(total <= MAX_TOTAL_BYTES, "archive total size")
                private_names.append(name)
                expected.add("files/" + name)
                require("files/" + name in by_name and by_name["files/" + name].file_size == row["size"],
                        "manifest size or population")
            distinct_paths(private_names)
            require(expected == set(names), "manifest population")
            target.mkdir(mode=0o700)
            for row in rows:
                destination = target.joinpath(*row["path"].split("/"))
                destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
                digest = hashlib.sha256()
                size = 0
                with archive.open("files/" + row["path"], "r") as member, destination.open("xb") as output:
                    while True:
                        chunk = member.read(CHUNK)
                        if not chunk:
                            break
                        size += len(chunk)
                        require(size <= row["size"], "expanded member size")
                        digest.update(chunk)
                        output.write(chunk)
                destination.chmod(0o600)
                require(size == row["size"] and digest.hexdigest() == row["sha256"], "private member integrity")


def digest_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(CHUNK):
            digest.update(chunk)
    return digest.hexdigest()


def snapshot_ciphertext(source, target):
    total = 0
    with open_regular(source) as stream, target.open("xb") as output:
        require(0 < os.fstat(stream.fileno()).st_size <= MAX_CMS_BYTES, "ciphertext size")
        while chunk := stream.read(CHUNK):
            total += len(chunk)
            require(total <= MAX_CMS_BYTES, "ciphertext size")
            output.write(chunk)
    target.chmod(0o600)


def publish(staged, output):
    # Exclusive reservation prevents replacing even an empty existing directory.
    # All plaintext files have already authenticated and passed exact verification
    # before this directory becomes visible. Cleanup only our own reservation.
    output.mkdir(mode=0o700)
    try:
        for child in staged.iterdir():
            child.rename(output / child.name)
    except BaseException:
        shutil.rmtree(output)
        raise


def execute(operation, source, output, certificate, key=None):
    source = no_symlink_path(source)
    output = no_symlink_path(output)
    require(source.is_dir() and output.parent.is_dir(), "directory input")
    require(not output.exists() and not output.is_symlink(), "output exists")
    require(not output.is_relative_to(source), "output inside source")
    with tempfile.TemporaryDirectory(prefix=".native-envelope-", dir=output.parent) as temporary:
        staging = Path(temporary)
        staging.chmod(0o700)
        recipient = recipient_certificate(certificate, staging)
        result = staging / "result"
        archive = staging / "private.zip"
        if operation == "seal":
            create_archive(source, archive)
            result.mkdir(mode=0o700)
            ciphertext = result / "capture.p7m"
            openssl("cms", "-encrypt", "-binary", "-outform", "DER", "-aes-256-gcm",
                    "-in", archive, "-out", ciphertext, "-recip", recipient["path"],
                    "-keyopt", "rsa_padding_mode:oaep", "-keyopt", "rsa_oaep_md:sha256",
                    "-keyopt", "rsa_mgf1_md:sha256")
            require(0 < ciphertext.stat().st_size <= MAX_CMS_BYTES, "ciphertext size")
            inspect_cms(ciphertext, recipient)
            metadata = {"schema": "salah-native-envelope/1", "profile": PROFILE,
                        "recipient_sha256": recipient["sha256"],
                        "ciphertext_size": ciphertext.stat().st_size,
                        "ciphertext_sha256": digest_file(ciphertext)}
            (result / "envelope.json").write_text(json.dumps(metadata, sort_keys=True, indent=2) + "\n")
            for item in result.iterdir():
                item.chmod(0o600)
        else:
            require(set(os.listdir(source)) == {"capture.p7m", "envelope.json"}, "public file population")
            metadata = load_json(read_bounded(source / "envelope.json", 4096))
            require(type(metadata) is dict and set(metadata) == {
                "schema", "profile", "recipient_sha256", "ciphertext_size", "ciphertext_sha256"},
                "public metadata fields")
            require(metadata["schema"] == "salah-native-envelope/1" and metadata["profile"] == PROFILE and
                    metadata["recipient_sha256"] == recipient["sha256"], "public metadata profile")
            require(type(metadata["ciphertext_size"]) is int and 0 < metadata["ciphertext_size"] <= MAX_CMS_BYTES,
                    "ciphertext size")
            require(type(metadata["ciphertext_sha256"]) is str and HEX256.fullmatch(metadata["ciphertext_sha256"]),
                    "ciphertext hash format")
            ciphertext = staging / "capture.p7m"
            snapshot_ciphertext(source / "capture.p7m", ciphertext)
            require(ciphertext.stat().st_size == metadata["ciphertext_size"] and
                    digest_file(ciphertext) == metadata["ciphertext_sha256"], "ciphertext identity")
            inspect_cms(ciphertext, recipient)
            private_key = no_symlink_path(key)
            with open_regular(private_key) as key_file:
                require(os.fstat(key_file.fileno()).st_size <= (128 << 10), "private key size")
            public_key = openssl("pkey", "-in", private_key, "-passin", "pass:", "-pubout", "-outform", "DER")
            require(public_key == recipient["spki"], "private key mismatch")
            # OpenSSL may write unauthenticated tentative plaintext here. Never
            # parse, extract or publish it until the process reports success.
            openssl("cms", "-decrypt", "-binary", "-inform", "DER", "-in", ciphertext,
                    "-recip", recipient["path"], "-inkey", private_key, "-passin", "pass:", "-out", archive)
            archive.chmod(0o600)
            extract_verified(archive, result)
        publish(result, output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="operation", required=True)
    for operation in ("seal", "open"):
        command = commands.add_parser(operation)
        for option in ("source", "out", "certificate"):
            command.add_argument("--" + option, required=True, type=Path)
        if operation == "open":
            command.add_argument("--key", required=True, type=Path)
    arguments = parser.parse_args()
    # This command owns its process. Private files keep restrictive modes even
    # before chmod or when OpenSSL creates tentative output itself.
    os.umask(0o077)
    signal.signal(signal.SIGTERM, lambda signum, frame: (_ for _ in ()).throw(KeyboardInterrupt()))
    try:
        execute(arguments.operation, arguments.source, arguments.out,
                arguments.certificate, getattr(arguments, "key", None))
    except (Rejected, OSError, ValueError, UnicodeError, IndexError, struct.error,
            zipfile.BadZipFile, zipfile.LargeZipFile, RuntimeError, KeyboardInterrupt):
        print("ENVELOPE_REJECTED", file=sys.stderr)
        return 1
    print("SEAL_OK" if arguments.operation == "seal" else "OPEN_OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
