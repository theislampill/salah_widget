"""Standard-library front door; Node uses the existing bundled Playwright, never installs it."""
import argparse
import json
import subprocess
import hashlib
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source-root',type=Path,required=True)
parser.add_argument('--source-ref',default='rlgwo-weather-info-01')
parser.add_argument('--group',choices=['r0010'],required=True)
parser.add_argument('--browser',choices=['chromium'],default='chromium')
parser.add_argument('--out',type=Path,required=True)
parser.add_argument('--only',action='append',default=[])
parser.add_argument('--executable')
parser.add_argument('--lease-authorized',action='store_true',help='Set only by root after the explicit capacity-one lease and fixture review')
parser.add_argument('--lease-id',help='Actual ACTIVE root capacity-one R0010 lease bound to this Python driver')
parser.add_argument('--validate-only',action='store_true')
parser.add_argument('--list',action='store_true')
parser.add_argument('--continue-after-failure',action='store_true')
parser.add_argument('--node',default=r'C:\workspace\ai\cp9-integration-20261005\toolchain\node-v22.16.0-win-x64\node.exe')
parser.add_argument('--package-root',default=r'C:\Users\theis\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\node_modules')
args=parser.parse_args()
out=args.out.resolve()
run=HERE.parents[2]
if not (out.is_relative_to(HERE.parent) or out.is_relative_to(run/'evidence/R0010')):parser.error('output must stay private or in root-owned R0010 evidence')
if out.exists():parser.error('output exists; preserve prior attempt and choose a fresh directory')
if not (args.list or args.validate_only) and not args.executable:parser.error('an explicit existing browser executable is required')
if not (args.list or args.validate_only or args.lease_authorized):parser.error('root serial browser lease required; use --list/--validate-only without browser effects')
out.mkdir(parents=True,exist_ok=True)
options={'sourceRoot':str(args.source_root.resolve()),'sourceRef':args.source_ref,'group':args.group,'out':str(out),
         'only':args.only,'executable':args.executable,'leaseId':args.lease_id,
         'pythonEnvironment':{'version':sys.version,'executable':sys.executable,'sha256':hashlib.sha256(Path(sys.executable).read_bytes()).hexdigest()},'leaseAuthorized':args.lease_authorized,'validateOnly':args.validate_only,'list':args.list,
         'stopOnFailure':not args.continue_after_failure,'packageRoot':args.package_root}
options_path=out/'launch-options.json'
options_path.write_text(json.dumps(options,indent=2)+'\n',encoding='utf-8')
raise SystemExit(subprocess.call([args.node,str(HERE/'residual-location-actions.cjs'),str(options_path)]))
