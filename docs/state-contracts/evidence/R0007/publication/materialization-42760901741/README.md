# Second actual materialization failure

Run `42760901741`, attempt 1, on seed `3b2d09c` rebuilt the exact `9d24fb4` target tree `0f0385b5`. Its first 81,702,660-byte offline blob then received HTTP 422 using an 82,904,481-byte UTF-8 JSON request. Zero uploads were verified; the reviewed blob-only job performed no ref update. The ZIP was received and checked against GitHub artifact `13737692102`, SHA-256 `2c3867d3dfc131d85972cdb35d038abaa2bebb548f8f0175ddd821a2e9df8d60`.

The original archive contains `attempt-nqvq8786/summary.json`, `upload-001.json`, exact producer records/logs and the candidate index. `receipt.json` maps its bytes and members. `andon-report.md` and `andon-evidence.json` are retained byte for byte from the bounded direct diagnosis; their original analysis-relative paths refer to the acquisition workspace.

The API-side cause remains unknown. The receipt preserves metadata for a 240-byte JSON response without arbitrary response text. An ordinary Git pack continuation is in preparation and requires separate review. The proposal supplies no evidence of successful publication or native qualification.
