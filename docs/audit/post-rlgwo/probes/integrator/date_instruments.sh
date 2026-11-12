#!/bin/bash
# Post-RLGWO audit, integrator: run the red regression instruments against historical commits,
# read-only with respect to the repository. Each commit is extracted with `git archive` (excluding
# docs/, vendor/, plans/, moon/assets/, moon/file-data/ and offline.html) into OUT/snap/<sha>,
# the instruments run there with GIT_DIR pointing at the repository (two instruments `git show`
# accepted bytes), and the snapshot is deleted. No network. Usage:
#   date_instruments.sh <repo-root> <git-dir> <out-dir> <sha>...
REPO=$1; GD=$2; O=$3; shift 3
for sha in "$@"; do
  D=$O/snap/$sha; rm -rf "$D"; mkdir -p "$D"
  (cd "$REPO" && git archive --format=tar "$sha" -- . ":!docs" ":!vendor" ":!plans" ":!moon/assets" ":!moon/file-data" ":!offline.html") | tar -x -C "$D"
  (cd "$REPO" && git archive --format=tar "$sha" docs/*.md 2>/dev/null) | tar -x -C "$D" 2>/dev/null
  for t in r0001-date-sinks r0009-date-selection r0019-date-disclosure r0021-reveal r0022-baseline-balance r0022-lunar-consumers rlgwo-docs-contract; do
    if [ -f "$D/tests/$t.cjs" ]; then
      (cd "$D" && GIT_DIR="$GD" timeout 600 node tests/$t.cjs) > "$O/snap/${sha}_$t.log" 2>&1; rc=$?
      p=$(grep -cE '^PASS|"status": ?"PASS"' "$O/snap/${sha}_$t.log"); f=$(grep -cE '^FAIL|"status": ?"FAIL"' "$O/snap/${sha}_$t.log")
      echo "$sha $t rc=$rc pass=$p fail=$f"
    else echo "$sha $t absent"; fi
  done
  rm -rf "$D"
done
