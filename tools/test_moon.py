#!/usr/bin/env python3
"""Fast, offline Moon component tests. Does not rerun the expensive V5 research campaign."""
import argparse,json,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
a=argparse.ArgumentParser();a.add_argument('--output',type=Path,required=True);a.add_argument('--node',default='node');args=a.parse_args();args.output.mkdir(parents=True,exist_ok=True)
cmd=[args.node,'--test',*map(str,sorted((R/'moon/tests').glob('*.test.cjs')))];r=subprocess.run(cmd,cwd=R,capture_output=True);(args.output/'moon-node.tap').write_bytes(r.stdout+r.stderr)
record={'command':cmd,'exitCode':r.returncode,'scope':'Moon runtime components and small real-data terrain run, not complete native browser qualification'};(args.output/'receipt.json').write_text(json.dumps(record,indent=2)+'\n');print(r.stdout.decode(errors='replace')[-1500:]);sys.exit(r.returncode)
