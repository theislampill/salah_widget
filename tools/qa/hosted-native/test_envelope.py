#!/usr/bin/env python3
"""Real-OpenSSL envelope controls; keys and observations stay in temporary storage.

The fixtures are built with the standard library and OpenSSL independently of
envelope.py. These controls qualify this transport, not observation provenance.
"""
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import stat
import struct
import subprocess
import sys
import tempfile
import unittest
import warnings
import zipfile


SCRIPT = Path(__file__).with_name("envelope.py")
PROFILE = "CMS-AuthEnvelopedData-RSA3072-OAEP-SHA256-MGF1-SHA256-AES256GCM"
MANIFEST = "manifest.json"
OPENSSL = shutil.which("openssl")


def run(*args, **kwargs):
    return subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          timeout=45, check=False, **kwargs)


def openssl(*args, **kwargs):
    result = run(OPENSSL, *args, **kwargs)
    if result.returncode:
        raise RuntimeError("test fixture OpenSSL failed: " + result.stderr.decode())
    return result.stdout


def zip_blob(members, manifest=None, compression=zipfile.ZIP_STORED):
    """Independent fixture; explicit external attributes make regularity testable."""
    if manifest is None:
        manifest = {"schema": "salah-native-capture/1", "files": [
            {"path": name, "size": len(body), "sha256": hashlib.sha256(body).hexdigest()}
            for name, body in members]}
    stream = io.BytesIO()
    with warnings.catch_warnings(), zipfile.ZipFile(stream, "w") as archive:
        warnings.simplefilter("ignore", UserWarning)
        for name, body in [("files/" + n, b) for n, b in members] + [
                (MANIFEST, json.dumps(manifest).encode())]:
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = (stat.S_IFREG | 0o600) << 16
            info.compress_type = compression
            archive.writestr(info, body)
    return stream.getvalue()


def fixture_der_tree(data):
    """Small test-only codec for mutating a known-good OpenSSL fixture."""
    def node(start):
        tag, length = data[start:start + 2]
        cursor = start + 2
        if length & 128:
            count = length & 127
            length = int.from_bytes(data[cursor:cursor + count], "big")
            cursor += count
        end = cursor + length
        if tag & 32:
            value = []
            while cursor < end:
                child, cursor = node(cursor)
                value.append(child)
        else:
            value = data[cursor:end]
        return [tag, value], end
    return node(0)[0]


def fixture_der_bytes(node):
    tag, value = node
    body = b"".join(map(fixture_der_bytes, value)) if isinstance(value, list) else value
    length = len(body)
    if length < 128:
        encoded = bytes([length])
    else:
        raw = length.to_bytes((length.bit_length() + 7) // 8, "big")
        encoded = bytes([128 | len(raw)]) + raw
    return bytes([tag]) + encoded + body


class EnvelopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not OPENSSL:
            raise RuntimeError("OpenSSL is required; these controls must not skip")
        cls.keys = tempfile.TemporaryDirectory(prefix="native-envelope-test-keys-")
        cls.keydir = Path(cls.keys.name)
        for label, bits in (("recipient", 3072), ("other", 3072), ("weak", 2048)):
            openssl("req", "-x509", "-newkey", "rsa:" + str(bits), "-nodes",
                    "-keyout", str(cls.keydir / (label + ".key")),
                    "-out", str(cls.keydir / (label + ".crt")), "-days", "1",
                    "-subj", "/CN=Envelope control " + label, "-sha256")
        cls.cert = cls.keydir / "recipient.crt"
        cls.key = cls.keydir / "recipient.key"
        cls.fingerprint = hashlib.sha256(openssl(
            "x509", "-in", str(cls.cert), "-outform", "DER")).hexdigest()

    @classmethod
    def tearDownClass(cls):
        cls.keys.cleanup()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="native-envelope-control-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "private"
        self.source.mkdir(mode=0o700)
        (self.source / "nested").mkdir(mode=0o700)
        (self.source / "nested" / "private-observation-name.txt").write_bytes(
            b"OWNER_PRIVATE_CANARY\x00\xff\n")
        (self.source / "empty.bin").write_bytes(b"")
        self.sealed = self.root / "sealed"
        self.output = self.root / "opened"

    def cli(self, operation, source=None, out=None, cert=None, key=None, env=None):
        args = [sys.executable, str(SCRIPT), operation,
                "--source", str(source or (self.source if operation == "seal" else self.sealed)),
                "--out", str(out or (self.sealed if operation == "seal" else self.output)),
                "--certificate", str(cert or self.cert)]
        if operation == "open":
            args += ["--key", str(key or self.key)]
        return run(*args, env=env)

    def seal(self):
        result = self.cli("seal")
        self.assertEqual(result.returncode, 0, result.stderr.decode())
        return result

    def rehash(self):
        path = self.sealed / "capture.p7m"
        metadata = json.loads((self.sealed / "envelope.json").read_text())
        metadata["ciphertext_size"] = path.stat().st_size
        metadata["ciphertext_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        (self.sealed / "envelope.json").write_text(json.dumps(metadata))

    def independent_envelope(self, plaintext=None, cipher="aes-256-gcm",
                             oaep="sha256", mgf="sha256", recipients=None):
        if plaintext is None:
            plaintext = zip_blob([("safe.txt", b"independent fixture")])
        if self.sealed.exists():
            shutil.rmtree(self.sealed)
        self.sealed.mkdir(mode=0o700)
        clear = self.root / "fixture.zip"
        clear.write_bytes(plaintext)
        args = ["cms", "-encrypt", "-binary", "-outform", "DER", "-" + cipher,
                "-in", str(clear), "-out", str(self.sealed / "capture.p7m")]
        for cert in (recipients or [self.cert]):
            args += ["-recip", str(cert), "-keyopt", "rsa_padding_mode:oaep",
                     "-keyopt", "rsa_oaep_md:" + oaep,
                     "-keyopt", "rsa_mgf1_md:" + mgf]
        openssl(*args)
        (self.sealed / "envelope.json").write_text(json.dumps({
            "schema": "salah-native-envelope/1", "profile": PROFILE,
            "recipient_sha256": self.fingerprint,
            "ciphertext_size": 0, "ciphertext_sha256": "0" * 64}))
        self.rehash()
        return plaintext

    def assert_rejected(self, operation="open", **kwargs):
        before = set(self.root.iterdir())
        result = self.cli(operation, **kwargs)
        self.assertNotEqual(result.returncode, 0, "unsafe input was accepted")
        expected_out = kwargs.get("out", self.output if operation == "open" else self.sealed)
        if expected_out not in before:
            self.assertFalse(expected_out.exists(), "failed operation released output")
        self.assertEqual(set(self.root.iterdir()), before, "failed operation left staging files")
        self.assertNotIn(b"OWNER_PRIVATE_CANARY", result.stdout + result.stderr)
        self.assertNotIn(b"private-observation-name", result.stdout + result.stderr)

    def assert_rejected_before_decrypt(self, **kwargs):
        observer = self.root / "predecrypt-observer"
        observer.mkdir()
        marker = observer / "decrypt-called"
        wrapper = observer / "openssl"
        wrapper.write_text("#!" + sys.executable + "\n" +
            "import pathlib, subprocess, sys\n" +
            "args=sys.argv[1:]\n" +
            "if args[:2] == ['cms','-decrypt']:\n" +
            " pathlib.Path(" + repr(str(marker)) + ").touch()\n" +
            "sys.exit(subprocess.run([" + repr(OPENSSL) + "]+args).returncode)\n")
        wrapper.chmod(0o700)
        env = dict(os.environ, PATH=str(observer) + os.pathsep + os.environ["PATH"])
        try:
            self.assert_rejected(env=env, **kwargs)
            self.assertFalse(marker.exists(), "unsupported CMS reached generic decryption")
        finally:
            shutil.rmtree(observer)

    def test_roundtrip_is_exact_and_public_metadata_has_no_capture_identity(self):
        self.seal()
        self.assertEqual({p.name for p in self.sealed.iterdir()},
                         {"capture.p7m", "envelope.json"})
        metadata = json.loads((self.sealed / "envelope.json").read_text())
        self.assertEqual(set(metadata), {"schema", "profile", "recipient_sha256",
                                        "ciphertext_size", "ciphertext_sha256"})
        public = (self.sealed / "envelope.json").read_bytes()
        for path in self.source.rglob("*"):
            if path.is_file():
                self.assertNotIn(path.name.encode(), public)
                self.assertNotIn(hashlib.sha256(path.read_bytes()).hexdigest().encode(), public)
        self.assertNotIn(b"OWNER_PRIVATE_CANARY", public)
        self.assertEqual(self.cli("open").returncode, 0)
        actual = {p.relative_to(self.output).as_posix(): p.read_bytes()
                  for p in self.output.rglob("*") if p.is_file()}
        self.assertEqual(actual, {"empty.bin": b"",
                                 "nested/private-observation-name.txt": b"OWNER_PRIVATE_CANARY\x00\xff\n"})
        for path in [self.output, *self.output.rglob("*")]:
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o700 if path.is_dir() else 0o600)

    def test_independent_valid_cms_is_accepted(self):
        self.independent_envelope()
        result = self.cli("open")
        self.assertEqual(result.returncode, 0, result.stderr.decode())
        self.assertEqual((self.output / "safe.txt").read_bytes(), b"independent fixture")

    def test_empty_source_roundtrips(self):
        shutil.rmtree(self.source)
        self.source.mkdir()
        self.seal()
        self.assertEqual(self.cli("open").returncode, 0)
        self.assertEqual(list(self.output.iterdir()), [])

    def test_unicode_member_and_private_manifest_filename_roundtrip(self):
        (self.source / "manifest.json").write_bytes(b"source-owned manifest")
        (self.source / "صلاة.txt").write_bytes("صلاة".encode())
        self.seal()
        self.assertEqual(self.cli("open").returncode, 0)
        self.assertEqual((self.output / "manifest.json").read_bytes(), b"source-owned manifest")
        self.assertEqual((self.output / "صلاة.txt").read_text(), "صلاة")

    def test_stored_zip64_directory_and_offset_records_are_supported(self):
        # Force ordinary ZIP64 encoding with small real files, keeping the
        # production decoder and every encoded offset/length unmodified.
        original_limit = zipfile.ZIP64_LIMIT
        try:
            zipfile.ZIP64_LIMIT = 1024
            body = zip_blob([("small-" + str(i), b"x" * 200) for i in range(5)])
        finally:
            zipfile.ZIP64_LIMIT = original_limit
        self.assertIn(b"PK\x06\x06", body)
        with zipfile.ZipFile(io.BytesIO(body)) as archive:
            self.assertTrue(any(info.extra for info in archive.infolist()))
        self.independent_envelope(body)
        result = self.cli("open")
        self.assertEqual(result.returncode, 0, result.stderr.decode())
        self.assertEqual(len(list(self.output.iterdir())), 5)

    def test_cbc_with_forged_gcm_metadata_is_rejected(self):
        plaintext = self.independent_envelope(cipher="aes-256-cbc")
        decoded = openssl("cms", "-decrypt", "-binary", "-inform", "DER",
                          "-in", str(self.sealed / "capture.p7m"),
                          "-recip", str(self.cert), "-inkey", str(self.key))
        self.assertEqual(decoded, plaintext, "CBC fixture must actually decrypt")
        self.assert_rejected_before_decrypt()

    def test_sha1_mgf_with_forged_metadata_is_rejected(self):
        self.independent_envelope(mgf="sha1")
        self.assert_rejected_before_decrypt()

    def test_sha1_oaep_is_rejected(self):
        self.independent_envelope(oaep="sha1")
        self.assert_rejected_before_decrypt()

    def test_multiple_recipients_are_rejected(self):
        self.independent_envelope(recipients=[self.cert, self.keydir / "other.crt"])
        self.assert_rejected_before_decrypt()

    def test_profile_fields_are_checked_before_generic_decryption(self):
        mutations = (
            ("wrapped-key-size", (1, 0, 1, 0, 3), [4, b"x" * 383]),
            ("auth-version", (1, 0, 0), [2, b"\x01"]),
            ("recipient-version", (1, 0, 1, 0, 0), [2, b"\x01"]),
            ("nonce-size", (1, 0, 2, 1, 1, 0), [4, b"x" * 11]),
            ("declared-tag-size", (1, 0, 2, 1, 1, 1), [2, b"\x0c"]),
            ("actual-tag-size", (1, 0, 3), [4, b"x" * 15]),
            ("content-type", (1, 0, 2, 0), [6, bytes.fromhex("2a864886f70d010702")]),
        )
        for label, path, replacement in mutations:
            with self.subTest(mutation=label):
                self.independent_envelope()
                cms = self.sealed / "capture.p7m"
                tree = fixture_der_tree(cms.read_bytes())
                parent = tree
                for index in path[:-1]:
                    parent = parent[1][index]
                parent[1][path[-1]] = replacement
                cms.write_bytes(fixture_der_bytes(tree))
                self.rehash()
                self.assert_rejected_before_decrypt()

    def test_nonminimal_or_indefinite_der_lengths_are_rejected(self):
        for kind in ("nonminimal", "indefinite"):
            with self.subTest(kind=kind):
                self.independent_envelope()
                path = self.sealed / "capture.p7m"
                data = path.read_bytes()
                count = data[1] & 127
                self.assertGreaterEqual(data[1], 128)
                if kind == "nonminimal":
                    data = data[:1] + bytes([data[1] + 1]) + b"\x00" + data[2:]
                else:
                    data = data[:1] + b"\x80" + data[2 + count:] + b"\x00\x00"
                path.write_bytes(data)
                self.rehash()
                self.assert_rejected_before_decrypt()

    def test_unsupported_cms_attributes_are_rejected(self):
        self.independent_envelope()
        path = self.sealed / "capture.p7m"
        tree = fixture_der_tree(path.read_bytes())
        tree[1][1][1][0][1].append([0xa2, []])
        path.write_bytes(fixture_der_bytes(tree))
        self.rehash()
        self.assert_rejected_before_decrypt()

    def test_different_actual_recipient_with_forged_metadata_is_rejected(self):
        self.independent_envelope(recipients=[self.keydir / "other.crt"])
        self.assert_rejected(key=self.keydir / "other.key")

    def test_wrong_private_key_is_rejected(self):
        self.independent_envelope()
        self.assert_rejected(key=self.keydir / "other.key")

    def test_rsa2048_recipient_is_rejected_before_sealing(self):
        self.assert_rejected("seal", cert=self.keydir / "weak.crt")

    def test_trailing_der_with_rehashed_metadata_is_rejected(self):
        self.independent_envelope()
        with (self.sealed / "capture.p7m").open("ab") as stream:
            stream.write(b"\x05\x00")
        self.rehash()
        self.assert_rejected()

    def test_corrupt_tag_with_rehashed_metadata_is_rejected(self):
        self.independent_envelope()
        path = self.sealed / "capture.p7m"
        body = bytearray(path.read_bytes())
        body[-1] ^= 1  # Independent fixture ends with the 16-byte mac OCTET STRING.
        path.write_bytes(body)
        self.rehash()
        self.assert_rejected()

    def test_decrypted_plaintext_stays_private_until_member_verification(self):
        manifest = {"schema": "salah-native-capture/1", "files": [
            {"path": "safe", "size": 7, "sha256": "0" * 64}]}
        self.independent_envelope(zip_blob([("safe", b"payload")], manifest))
        observer = self.root / "observer"
        observer.mkdir()
        report = observer / "report.json"
        report.write_text("{}")
        wrapper = observer / "openssl"
        wrapper.write_text("#!" + sys.executable + "\n" +
            "import json, os, pathlib, stat, subprocess, sys\n" +
            "args=sys.argv[1:]\n" +
            "result=subprocess.run([" + repr(OPENSSL) + "]+args)\n" +
            "if 'cms' in args and '-decrypt' in args:\n" +
            " p=pathlib.Path(args[args.index('-out')+1])\n" +
            " data={'mode': stat.S_IMODE(p.parent.stat().st_mode), " +
            "'bytes': p.stat().st_size if p.exists() else 0, " +
            "'released': pathlib.Path(" + repr(str(self.output)) + ").exists()}\n" +
            " pathlib.Path(" + repr(str(report)) + ").write_text(json.dumps(data))\n" +
            "sys.exit(result.returncode)\n")
        wrapper.chmod(0o700)
        env = dict(os.environ, PATH=str(observer) + os.pathsep + os.environ["PATH"])
        self.assert_rejected(env=env)
        observed = json.loads(report.read_text())
        self.assertEqual(observed["mode"], 0o700)
        self.assertGreater(observed["bytes"], 0, "control must observe real decrypted plaintext")
        self.assertFalse(observed["released"])

    def test_ciphertext_hash_mismatch_is_rejected(self):
        self.independent_envelope()
        path = self.sealed / "envelope.json"
        metadata = json.loads(path.read_text())
        metadata["ciphertext_sha256"] = "0" * 64
        path.write_text(json.dumps(metadata))
        self.assert_rejected()

    def test_duplicate_or_extra_public_metadata_fields_are_rejected(self):
        for mutation in ("duplicate", "private_field"):
            with self.subTest(mutation=mutation):
                self.independent_envelope()
                path = self.sealed / "envelope.json"
                text = path.read_text()
                addition = ('"schema":"salah-native-envelope/1",' if mutation == "duplicate"
                            else '"private_filename":"private-observation-name.txt",')
                path.write_text("{" + addition + text[1:])
                self.assert_rejected()

    def test_extra_or_symlink_public_files_are_rejected(self):
        self.independent_envelope()
        (self.sealed / "unexpected.txt").write_text("extra")
        self.assert_rejected()
        (self.sealed / "unexpected.txt").unlink()
        path = self.sealed / "capture.p7m"
        moved = self.root / "ciphertext.bin"
        path.rename(moved)
        path.symlink_to(moved)
        self.assert_rejected()

    def test_source_symlinks_are_rejected(self):
        for kind in ("file", "directory", "dangling"):
            with self.subTest(kind=kind):
                link = self.source / "link"
                target = {"file": self.source / "empty.bin", "directory": self.root,
                          "dangling": self.root / "absent"}[kind]
                link.symlink_to(target)
                self.assert_rejected("seal")
                link.unlink()

    def test_source_fifo_is_rejected_without_blocking(self):
        os.mkfifo(self.source / "pipe")
        self.assert_rejected("seal")

    def test_output_must_be_fresh_and_outside_source(self):
        self.sealed.mkdir()
        (self.sealed / "sentinel").write_text("preserve")
        self.assert_rejected("seal")
        self.assertEqual((self.sealed / "sentinel").read_text(), "preserve")
        self.assert_rejected("seal", out=self.source / "nested" / "output")
        self.assert_rejected("seal", out=self.source)
        shutil.rmtree(self.sealed)
        self.seal()
        self.output.mkdir()
        (self.output / "sentinel").write_text("preserve")
        self.assert_rejected()
        self.assertEqual((self.output / "sentinel").read_text(), "preserve")
        self.assert_rejected(out=self.sealed / "inside")

    def test_output_symlink_and_symlink_parent_are_rejected(self):
        self.sealed.symlink_to(self.root / "absent")
        self.assert_rejected("seal")
        self.sealed.unlink()
        alias = self.root / "alias"
        alias.symlink_to(self.source, target_is_directory=True)
        self.assert_rejected("seal", out=alias / "new")

    def test_unsafe_archive_paths_are_rejected(self):
        for path in ("../escape", "/absolute", "C:/drive", "a/../b", "a//b",
                     "a\\b", "./a", "a/", "a\x00b", "CON", "trailing."):
            with self.subTest(path=repr(path)):
                self.independent_envelope(zip_blob([(path, b"payload")]))
                self.assert_rejected()

    def test_duplicate_archive_paths_and_case_aliases_are_rejected(self):
        for names in (("same", "same"), ("Name", "name"), ("a", "a/b")):
            with self.subTest(names=names):
                self.independent_envelope(zip_blob([(name, b"payload") for name in names]))
                self.assert_rejected()

    def test_archive_symlink_is_rejected(self):
        data = bytearray(zip_blob([("link", b"target")]))
        central = data.index(b"PK\x01\x02")
        struct.pack_into("<I", data, central + 38, (stat.S_IFLNK | 0o777) << 16)
        self.independent_envelope(data)
        self.assert_rejected()

    def test_manifest_population_size_and_hash_must_match(self):
        for change in ("missing", "extra", "size", "hash", "duplicate", "bool_size"):
            with self.subTest(change=change):
                row = {"path": "safe", "size": 7, "sha256": hashlib.sha256(b"payload").hexdigest()}
                manifest = {"schema": "salah-native-capture/1", "files": [row]}
                if change == "missing":
                    manifest["files"] = []
                elif change == "extra":
                    manifest["files"].append(dict(row, path="other"))
                elif change == "size":
                    row["size"] = 8
                elif change == "hash":
                    row["sha256"] = "0" * 64
                elif change == "duplicate":
                    manifest["files"].append(dict(row))
                elif change == "bool_size":
                    row["size"] = True
                self.independent_envelope(zip_blob([("safe", b"payload")], manifest))
                self.assert_rejected()

    def test_unlisted_archive_member_is_rejected(self):
        body = io.BytesIO(zip_blob([("safe", b"payload")]))
        with zipfile.ZipFile(body, "a") as archive:
            archive.writestr("extra", b"unlisted")
        self.independent_envelope(body.getvalue())
        self.assert_rejected()

    def test_compressed_archive_bomb_is_rejected(self):
        self.independent_envelope(zip_blob([("bomb", b"0" * 2_000_000)],
                                          compression=zipfile.ZIP_DEFLATED))
        self.assert_rejected()

    def test_archive_count_bomb_is_rejected(self):
        body = zip_blob([("item-" + str(i), b"") for i in range(20001)])
        self.independent_envelope(body)
        self.assert_rejected()

    def test_archive_declared_size_bomb_is_rejected(self):
        body = bytearray(zip_blob([("huge", b"payload")]))
        central = body.index(b"PK\x01\x02")
        struct.pack_into("<I", body, central + 24, 1_073_741_825)
        self.independent_envelope(body)
        self.assert_rejected()

    def test_manifest_aggregate_size_bomb_is_rejected(self):
        # Exercise the real cumulative guard without allocating multi-GiB data.
        # Each member is independently within the reduced budget; their sum is not.
        import envelope
        path = self.root / "sum.zip"
        path.write_bytes(zip_blob([("first", b"123456"), ("second", b"abcdef")]))
        limit = envelope.MAX_TOTAL_BYTES
        try:
            envelope.MAX_TOTAL_BYTES = 10
            with self.assertRaises(envelope.Rejected):
                envelope.extract_verified(path, self.output)
        finally:
            envelope.MAX_TOTAL_BYTES = limit
        self.assertFalse(self.output.exists())

    def test_oversize_source_member_is_rejected_before_reading(self):
        with (self.source / "sparse-huge").open("wb") as stream:
            stream.truncate(1_073_741_825)
        self.assert_rejected("seal")

    def test_archive_trailer_is_rejected(self):
        self.independent_envelope(zip_blob([("safe", b"payload")]) + b"trailer")
        self.assert_rejected()

    def test_archive_local_header_mismatch_is_rejected(self):
        body = bytearray(zip_blob([("safe", b"payload")]))
        body[30] ^= 1  # Local filename differs from central-directory filename.
        self.independent_envelope(body)
        self.assert_rejected()


if __name__ == "__main__":
    unittest.main(verbosity=2)
