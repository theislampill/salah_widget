#!/bin/bash
# usage: run_one.sh <label> <system|v22>
S="<REDACTED:SCRATCH>"
L=$1; MODE=$2; O="$S/out/$L"; rm -rf "$O"; mkdir -p "$O" "$S/tmp/$L"
export TMP="$(cygpath -w "$S/tmp/$L")" TEMP="$(cygpath -w "$S/tmp/$L")" TMPDIR="$(cygpath -w "$S/tmp/$L")"
[ "$MODE" = v22 ] && export PATH="$S/node/node-v22.16.0-win-x64:$PATH"
cd "$S/clone"
{ echo "label=$L mode=$MODE"; echo "head=$(git rev-parse HEAD)"; echo "which_node=$(command -v node)"; echo "node_version=$(node --version)"; echo "python=$(python --version 2>&1)"; echo "TMP=$TMP"; date -u +%FT%TZ; } > "$O/env.txt"
python tools/cp9/run_scientific_regressions.py --output "$(cygpath -w "$O/runner")" > "$O/stdout.txt" 2> "$O/stderr.txt"; echo $? > "$O/exit.txt"
date -u +%FT%TZ >> "$O/env.txt"; git status --porcelain > "$O/clone-status-after.txt"
cat "$O/env.txt" "$O/stdout.txt" "$O/exit.txt"
