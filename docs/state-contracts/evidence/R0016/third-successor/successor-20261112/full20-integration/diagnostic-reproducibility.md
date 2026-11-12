# Historical diagnostic reproduction boundary

The unchanged `tools/qualification/installer_preview_windows_normal_profile_diagnostic.py`
is a historical calibration instrument for the exact inherited pins at immutable
commit `12904a880c38b749db2d7c79ec1e7cebde2e04e2`. Its pins and exact derivation
anchors deliberately remain unchanged in this proposal. Run `43216080799` and its
archived inherited/control bytes retain that reproduction boundary.

After applying the two full20 owner changes, running this historical diagnostic
against the new checkout must fail closed on its inherited outer/harness pins.
It is not a current full20 carrier. Reproduce its original run from the immutable
commit and retained inputs. Do not silently repin its source or reuse its old
derivation against the integrated harness. The diagnostic workflow watches its
own tool/workflow paths; neither path belongs to this candidate patch.

The current full20 carrier is the proposed
`installer_preview_windows_full_entry.py`, whose harness byte count and SHA-256
are updated together. All other source input pins remain unchanged.

The later PS5.1 calibration reports both warm20 and warm-json normal cases PASS.
The earlier warm20 failures remain adverse evidence. Their old/new variation,
including the differing AWSPowerShell path strings inside cache bytes reported by the independent
receiver, is unexplained by this candidate. No unique JSON necessity or
deterministic cache-fix claim follows. Any repeated product cache/input change
must fail the original unchanged full20 normal postcondition.
