# Portable private capture transport

This source-only adapter preserves a case-sensitive capture tree through the
existing strict envelope. It adds no native evidence or observation acceptance.
The envelope, its cryptography and its archive path rules remain unchanged.

## Design and authority

The chosen approach is a private staging directory containing `mapping.json`
and uniquely numbered lower-case files under `payload/`. Each mapping entry
binds an exact original relative path to one payload, its byte count and SHA-256.
The map also retains original directories, including empty directories. Original
logical names in the transport namespace occur only in this private map and,
after explicit restoration, in the restored private tree. Original file contents
remain byte-identical, including any paths already present inside those contents.
The complete staging directory must be encrypted
by the original envelope; neither the map nor payload files are public artifacts.

Changing envelope case-folding rules would remove an existing archive guard.
Renaming observation files would change the original recipes and their evidence
paths. Both alternatives are excluded by the task. The adapter therefore leaves
those boundaries intact and changes only the transport representation.

`capture_transport.py stage --source CAPTURE --out FRESH_STAGE --protect ROOT`
prepares a fresh private package. `capture_transport.py restore --source OPENED_STAGE
--out FRESH_CAPTURE --protect ROOT` restores a previously authenticated and opened
package. `--protect` is repeatable and required: the caller lists all source and
runtime roots that must never receive output. The adapter additionally protects
its own checkout and the input tree. It rejects symlinked ancestors and all
overlap with protected roots. Workflow integration must bind the actual runtime
and checkout roots rather than accept them from untrusted package metadata.

The original envelope is responsible for encryption, recipient/profile checks
and authenticated decryption. The adapter does not handle certificates or keys.
Opening an envelope does not authenticate its sender; the caller must still
authenticate the repository, exact workflow head, run and downloaded artifact.
Source controls use synthetic files and the existing ZIP functions only, with
no key operation or native execution.

## Integrity, population and limits

The versioned map has strict keys and duplicate-key rejection. Logical names
retain the envelope's individual path rules, including NFC, relative components,
length limits and rejection of separators, traversal and reserved names. Logical
uniqueness and file/directory conflicts are checked case-sensitively. Payload
names are a canonical consecutive numeric sequence and pass the unchanged
envelope's stricter case-folded population check.

The adapter retains at most 19,999 files, reserving one of the envelope's 20,000
members for the map; at most 20,000 directories; depth at most 64; and a map at
most 8 MiB. Each file remains at most 1 GiB. Payload bytes plus map bytes must
fit the original 4 GiB total ceiling. No population is silently truncated or
deduplicated. The map overhead may make a near-limit source inadmissible.

All copying is bounded and streaming. Each source file is opened relative to
held directory descriptors without following symlinks, checked before and after
reading, copied without transformation and read back by hash. A second complete
inventory checks identity and population stability, including empty directories.
The producer must already be stopped: these checks detect observed changes but
do not turn a mutable tree into an atomic snapshot against a concurrent process
with the same account privileges.

Restoration requires exactly the declared map and payload population, verifies
every payload, creates every logical directory and file exclusively, verifies
the complete restored tree and publishes only into a fresh private reservation.
Case-insensitive destinations that cannot represent the original population are
rejected; they never receive renamed or merged logical paths. The implementation
uses the same POSIX directory-descriptor environment as the existing envelope.

Private directories use mode 0700 and files 0600. File contents, exact logical
paths and empty-directory population are preserved; executable permission bits
and timestamps are not evidence claims. Failures clean only adapter-owned
temporary/output reservations, preserve the original input, and never overwrite
an existing destination. CLI output is a fixed success marker or a bounded error
category with no filename, exception text, file content or child log.
An inability to identify or remove an owned reservation is a failure, never a
successful cleanup claim. The enclosing private task must still clean its
private working area after an error or process termination.

## Integration remains separate

This packet changes no workflow or hosted route. A later independently reviewed
integration must stop producers, stage privately, seal the complete staged tree
with the unchanged envelope, and upload only the existing ciphertext and envelope
metadata. Its cleanup must remove the added plaintext staging directory. A seal
failure must retain a bounded non-content failure category for diagnosis without
publishing private filenames. No prior native sealing cause is inferred from a
source-level reproduction.

The acquisition/sealing deadline must cover staging and verification I/O in
addition to the unchanged envelope work; this packet provides bounds, not native
timing evidence. Offline intake must open the authenticated envelope first and
then restore the logical tree before applying original source/result verifiers.
