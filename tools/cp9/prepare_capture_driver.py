"""Make an isolated copy of an existing Playwright driver that retains native
video source frames and their receipt timestamps. Never modifies the installed
driver. No app getter, layout query, new screenshot client or trace throttling."""
import argparse,hashlib,json,shutil
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('destination',type=Path);a=p.parse_args()
source=a.source.resolve();dest=a.destination.resolve()
if dest.exists() or dest==source or source in dest.parents:raise ValueError('Require a fresh separate output directory')
bundle=source/'lib/coreBundle.js';original=bundle.read_bytes();text=original.decode()
anchor='      writeFrame(frame, timestamp) {\n'
if text.count(anchor)!=1:raise ValueError('Unsupported driver recorder')
patch="""        if (process.env.SALAH_CAPTURE_NATIVE_FRAMES === '1') {
          const fs = require('node:fs'), path = require('node:path');
          const seq = this._salahSeq = (this._salahSeq || 0) + 1;
          const folder = this._outputFile + '.frames', file = String(seq).padStart(6,'0') + '.jpeg';
          const record = {seq, sourceTimeSeconds: timestamp, receiptUtcMs: Date.now(), file, bytes: frame.length};
          if (seq === 1) fs.mkdirSync(folder, {recursive: true});
          fs.appendFileSync(this._outputFile + '.frames.jsonl', JSON.stringify(record) + '\\n');
          fs.writeFileSync(path.join(folder,file), frame);
        }
"""
shutil.copytree(source,dest);(dest/'lib/coreBundle.js').write_text(text.replace(anchor,anchor+patch),encoding='utf-8',newline='\n')
receipt={'purpose':'Raw frames already received by the video recorder, before its 25fps resampling; capture receipt is an upper bound on visible time, never application publication. Firefox source clock is monotonic rather than Unix UTC.','sourceBundleSha256':hashlib.sha256(original).hexdigest(),'modifiedBundleSha256':hashlib.sha256((dest/'lib/coreBundle.js').read_bytes()).hexdigest(),'patch':patch,'source':str(source),'destination':str(dest)}
(dest/'SOURCE_FRAME_RECEIPT.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt))
