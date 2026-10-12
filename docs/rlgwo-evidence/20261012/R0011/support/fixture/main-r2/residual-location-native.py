"""Standard-library front door; Node uses the existing bundled Playwright, never installs it."""
import argparse
import json
import os
import subprocess
from pathlib import Path

HERE=Path(__file__).resolve().parent
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source-root',type=Path,required=True)
parser.add_argument('--source-ref',default='f0647b44e10c9ce4f80895b52861893c347512fd')
parser.add_argument('--group',choices=['r0011'],required=True)
parser.add_argument('--browser',choices=['chromium'],default='chromium')
parser.add_argument('--out',type=Path,required=True)
parser.add_argument('--only',action='append',default=[])
parser.add_argument('--executable')
parser.add_argument('--lease-authorized',action='store_true',help='Set only by root after the explicit capacity-one lease and fixture review')
parser.add_argument('--validate-only',action='store_true')
parser.add_argument('--list',action='store_true')
parser.add_argument('--continue-after-failure',action='store_true')
parser.add_argument('--node',default=r'C:\workspace\ai\cp9-integration-20261005\toolchain\node-v22.16.0-win-x64\node.exe')
parser.add_argument('--package-root',default=r'C:\Users\theis\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\node_modules')
args=parser.parse_args()
if os.path.lexists(args.out):parser.error('output identity is occupied; preserve existing path')
out=args.out.resolve()
if os.path.lexists(out):parser.error('resolved output identity is occupied; preserve existing path')
if not out.is_relative_to(HERE.parent):parser.error('output must stay in this worker directory')
if not (args.list or args.validate_only or args.lease_authorized):parser.error('root serial browser lease required; use --list/--validate-only without browser effects')
if os.path.lexists(out):parser.error('output identity became occupied; preserve existing path')
out.mkdir(parents=True,exist_ok=False)
options={'sourceRoot':str(args.source_root.resolve()),'sourceRef':args.source_ref,'group':args.group,'out':str(out),
         'only':args.only,'executable':args.executable,'leaseAuthorized':args.lease_authorized,'validateOnly':args.validate_only,'list':args.list,
         'stopOnFailure':not args.continue_after_failure,'packageRoot':args.package_root}
options_path=out/'launch-options.json'
if os.path.lexists(options_path):parser.error('launch options identity is occupied; preserve existing path')
with options_path.open('x',encoding='utf-8') as handle:handle.write(json.dumps(options,indent=2)+'\n')
raise SystemExit(subprocess.call([args.node,str(HERE/'residual-location-actions.cjs'),str(options_path)]))
