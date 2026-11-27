#!/usr/bin/env bash
# Only run as the trusted init of a newly created network/PID namespace.
set -euo pipefail
test "$#" -ge 3
native_uid="$1"
native_gid="$2"
shift 2
test "$EUID" -eq 0
test "$native_uid" -gt 0
test "$native_gid" -gt 0
ip link set lo up
exec setpriv --reuid "$native_uid" --regid "$native_gid" --clear-groups \
  --bounding-set=-all --inh-caps=-all --ambient-caps=-all --no-new-privs \
  /usr/bin/env -i "$@"
