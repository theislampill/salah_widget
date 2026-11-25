#!/usr/bin/env bash
# Acquisition only: dependency downloads complete before isolated source work.
set -euo pipefail
umask 077
test "$#" -eq 4
native_task="$1"
native_research="$2"
native_baseline="$3"
native_historical="$4"
native_tools="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
test -d "$native_task/capture"
test "$(git -C "$native_research" rev-parse HEAD)" = 55d1b3edb66d2c35679707120b01ee1d3455e4a3
test "$(git -C "$native_baseline" rev-parse HEAD)" = df644ef60156b67b5c487395176369bcec7a0d7b
test "$(git -C "$native_historical" rev-parse HEAD)" = 4029d2f67f5a880c8ad889443bb7557d96022c45
test -z "$(git -C "$native_research" status --porcelain)"
test -z "$(git -C "$native_baseline" status --porcelain)"
test -z "$(git -C "$native_historical" status --porcelain)"
# Qualify the runner's actual OpenSSL CMS and Python behavior before capture.
python3 -m unittest discover -s "$native_tools" -p test_envelope.py -v
native_engine="$(python3 -c 'import json,sys; x=json.load(open(sys.argv[1])); assert x["schemaVersion"]==1 and x["engine"] in ("chromium","firefox","webkit"); print(x["engine"])' "$native_tools/campaign.json")"
mkdir "$native_task/node" "$native_task/temporary" "$native_task/cache" "$native_task/config" "$native_task/runtime" "$native_task/work"
cp "$native_tools/node/package.json" "$native_tools/node/package-lock.json" "$native_task/node/"
npm ci --prefix "$native_task/node" --ignore-scripts --no-audit --no-fund --omit=optional
python3 -m venv "$native_task/python"
"$native_task/python/bin/python" -m pip install --disable-pip-version-check --require-hashes --only-binary=:all: -r "$native_tools/requirements.txt"
native_engines=(chromium)
if [ "$native_engine" != chromium ]; then native_engines+=("$native_engine"); fi
PLAYWRIGHT_BROWSERS_PATH="$native_task/node-browsers" node "$native_task/node/node_modules/playwright/cli.js" install --with-deps "${native_engines[@]}"
PLAYWRIGHT_BROWSERS_PATH="$native_task/python-browsers" "$native_task/python/bin/python" -m playwright install "$native_engine"
python3 "$native_tools/identities.py" --task "$native_task" --research "$native_research" --baseline "$native_baseline" --historical "$native_historical" --node "$(command -v node)" --python "$native_task/python/bin/python" --engine "$native_engine"
