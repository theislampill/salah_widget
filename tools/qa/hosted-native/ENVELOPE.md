# Private native capture envelope

`envelope.py` seals a stopped observation directory for one configured recipient
and opens a received envelope only after authenticating and verifying every
member. It requires Python 3.11 or later, POSIX descriptor/no-follow support and
OpenSSL CMS with AES-GCM support. The qualification controls use fresh temporary
RSA keys outside the repository and require real OpenSSL; they do not skip.

```sh
python tools/qa/hosted-native/envelope.py seal \
  --source /private/observations --out /private/sealed --certificate /private/recipient.crt
python tools/qa/hosted-native/envelope.py open \
  --source /private/received --out /private/opened \
  --certificate /private/recipient.crt --key /private/recipient.key
python -m unittest discover -s tools/qa/hosted-native -p test_envelope.py -v
```

The output path must not exist, including as an empty directory or symlink. Its
parent must exist, contain no symlink component and be outside the source. Both
operations reject an output inside their source. The selected certificate can be
PEM or DER and must contain one RSA3072 public key; the private key must match it
and be readable by OpenSSL without an interactive passphrase prompt. Certificate
identity is pinned by the caller, not derived from a public certification service.

## Public output and private contents

Sealing creates exactly `capture.p7m` and `envelope.json`. The public JSON has only
the schema, fixed cryptographic profile, certificate DER SHA-256, ciphertext byte
count and ciphertext SHA-256. It has no capture names, counts, plaintext hashes,
source identifiers, timestamps, measurements or images. Ciphertext length remains
visible; this transport does not provide traffic-size padding.

The authenticated plaintext is a stored ZIP: regular files under `files/` plus
`manifest.json`, which records each original relative path, byte count and
SHA-256. The payload namespace permits an original file named `manifest.json`.
Opening reproduces the original regular-file contents without the internal
manifest. Empty directories, source timestamps and source permissions are not
preserved. Opened directories have mode 700; opened files have mode 600.

Limits are 20,000 payload files, 1 GiB per file, 4 GiB aggregate payload and an
8 MiB manifest. Archive and ciphertext bounds additionally cover bounded headers.
ZIP64 central-directory offsets and end records are supported. Compression,
encryption within ZIP, data descriptors, unsupported extra records, archive
comments, symlinks, special files, path traversal, duplicate/case-aliased file
names and file/directory path collisions are rejected. Local and central ZIP
headers must agree and cover the archive without gaps or trailing contents.

## Cryptographic and release boundaries

The parser checks the **actual CMS bytes**, independently of the public JSON:

- Minimal definite DER with no trailing object or unsupported fields.
- AuthEnvelopedData version 0, one KeyTransRecipientInfo version 0, and exact
  issuer/serial agreement with the supplied recipient certificate.
- RSA3072, a 384-byte wrapped key, explicit OAEP SHA-256 and MGF1 SHA-256, and the
  omitted empty default OAEP label.
- `id-data` content, AES-256-GCM, a 12-byte nonce and a 16-byte authentication tag.
- No originator records or authenticated/unauthenticated attribute collections.

The definitions are [RFC 5083 section 2](https://www.rfc-editor.org/rfc/rfc5083)
and [RFC 5084 section 3.2](https://www.rfc-editor.org/rfc/rfc5084). This tool accepts
only that narrow profile, not every valid CMS or ZIP representation.

Opening snapshots the ciphertext into a mode 700 temporary directory, checks its
public identity and CMS profile, and decrypts there. OpenSSL implementations may
write tentative plaintext before their final authentication decision. Nothing is
parsed or extracted until OpenSSL succeeds. Member hashes and the exact member
population are then verified in that private directory. Only after all checks
succeed is the fresh output directory reserved exclusively and populated. A
normal error, timeout, interrupt or handled SIGTERM removes staging and any
partially published output created by that attempt. SIGKILL, power loss and
filesystem failure require external private-workspace cleanup; deletion is not a
claim of secure media erasure. Source captures are never deleted by the sealer.

Python hashes, copies and writes payloads in bounded chunks and inspects CMS with
an mmap rather than copying its encrypted content. OpenSSL's own DER CMS buffering
can use memory proportional to the capture size. The size limits are admission
bounds, not a guarantee that every machine has enough memory for a maximum-size
capture. Public success output is only `SEAL_OK` or `OPEN_OK`; failure output is
the bounded `ENVELOPE_REJECTED` marker and a nonzero status.

**Encryption does not authenticate the sender.** Anyone holding the public
certificate can construct a valid envelope. Authenticate the actual repository,
workflow commit, run and downloaded artifact before trusting its contents. Keep
the private key outside Git and Actions. The output parent, source producer and
OpenSSL installation are trusted local custody; a concurrent process with the
same account privileges is outside this protection boundary.

## Recovery and verification scope

This is a fresh reconstruction. The historical source body identified by
`cac290dedefb32f960e6f3a4231d5fba6f2f5a3c49b0f8fbbc0c23f266d36a74`
is unavailable and has not been recreated by claiming its hash.

The controls construct compliant and malicious envelopes independently with
OpenSSL, prove that algorithm/profile violations stop before generic decryption,
exercise actual authentication failures after metadata is rehashed, verify
private staging before member-hash acceptance, and test archive/path/boundary
failures. They qualify transport behavior. They do not qualify a browser run,
human observation, actual-recipient custody or workflow/artifact provenance.
