#!/bin/bash
# Estimate (not a _site measurement) of the GitHub Pages publishable payload: sum of git blob sizes,
# excluding the single `_config.yml` exclusion and any path with a component starting with '.' or '_'.
# Usage (inside the repository): pages_payload_estimate.sh <sha>...
for sha in "$@"; do
  git ls-tree -r -l "$sha" | awk -F'\t' -v sha="$sha" '{split($1,a," "); p=$2;
    if (p ~ /^docs\/rlgwo-execution\/20261014\/R000C\/native\//) next;
    n=split(p,c,"/"); for(i=1;i<=n;i++) if (c[i] ~ /^[._]/) next;
    s+=a[4]; f++} END{printf "%s files=%d bytes=%.3f GB\n", sha, f, s/1e9}'
done
