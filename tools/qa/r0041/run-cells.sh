#!/usr/bin/env bash
# R0041 witness matrix runner (recipe; NOT part of the node glob). Runs witness.cjs for every (DPR, motion) pair with
# the listed engines IN PARALLEL (each engine has its own isolated servers and proxy from iso.cjs; each writes its own
# JSON, so there is no shared preview server and no write race). Waits for all before returning.
# Usage: run-cells.sh <repoRoot> <outPrefix> <route> <startISO> <runs> "<dprs>" "<motions>" "<engines>"
#   e.g. run-cells.sh . /tmp/x natural 2026-11-24T16:30:00Z 3 "1 2" "reduce full" "chromium firefox webkit"
set -u
root=$1; out=$2; route=$3; start=$4; runs=$5; dprs=$6; motions=$7; engines=$8
here=$(cd "$(dirname "$0")" && pwd)
for d in $dprs; do for m in $motions; do
  for e in $engines; do
    node "$here/witness.cjs" "$root" "$out-$e.json" "$e" "$d" "$m" "$route" "$start" "$runs" > "$out-$e-$d-$m-$route.log" 2>&1 &
  done
  wait
done; done
grep -h "isolation allowed\|Error" "$out"-*-"$route".log | sort | uniq -c
