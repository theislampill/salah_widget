"""Own one sidecar descriptor per recorder, preserving original receipt semantics."""
from pathlib import Path
import hashlib,json,shutil
O=Path(__file__).resolve().parent
src=O/'capture-driver';dst=O/'capture-driver-r130';assert not dst.exists()
shutil.copytree(src,dst)
p=dst/'lib/coreBundle.js';s=p.read_text(encoding='utf-8')
old="""          if (seq === 1) fs.mkdirSync(folder, {recursive: true});
          fs.appendFileSync(this._outputFile + '.frames.jsonl', JSON.stringify(record) + '\\n');
          fs.writeFileSync(path.join(folder,file), frame);"""
new="""          if (seq === 1) {
            fs.mkdirSync(folder, {recursive: true});
            this._salahSourceFd = fs.openSync(this._outputFile + '.frames.jsonl', 'ax');
          }
          try {
            fs.appendFileSync(this._salahSourceFd, JSON.stringify(record) + '\\n');
            fs.writeFileSync(path.join(folder,file), frame);
          } catch (error) {
            this._closeSalahSource();
            throw error;
          }"""
assert s.count(old)==1;s=s.replace(old,new)
needle="""      writeFrame(frame, timestamp) {
        if (process.env.SALAH_CAPTURE_NATIVE_FRAMES === '1') {"""
replacement="""      _closeSalahSource() {
        this._salahSourceClosed = true;
        if (this._salahSourceFd !== undefined) {
          const fd = this._salahSourceFd;
          this._salahSourceFd = undefined;
          require('node:fs').closeSync(fd);
        }
      }
      writeFrame(frame, timestamp) {
        if (process.env.SALAH_CAPTURE_NATIVE_FRAMES === '1' && !this._salahSourceClosed) {"""
assert s.count(needle)==1;s=s.replace(needle,replacement)
start=s.index('      async _stop() {',s.index('      _closeSalahSource()'))
end=s.index('\n    };',start)
body=s[start:end]
assert body.count('async _stop()')==1 and body.endswith('      }')
wrapped=body.replace('      async _stop() {','      async _stop() {\n        try {',1)
wrapped=wrapped[:-7]+"        } finally {\n          this._closeSalahSource();\n        }\n      }"
s=s[:start]+wrapped+s[end:]
p.write_text(s,encoding='utf-8',newline='\n')
receipt={'schema':'r0021-source-sidecar-correction/v1','cause':'r126 failed syscall open while appendFileSync reopened the frame sidecar. Windows underlying errno UNKNOWN remains unexplained. Keep one owned descriptor to remove that repeated operation; do not retry writes or manufacture frames.','priorSha256':hashlib.sha256((src/'lib/coreBundle.js').read_bytes()).hexdigest(),'candidateSha256':hashlib.sha256(p.read_bytes()).hexdigest(),'scope':'Original JPEG bytes, source timestamp, receipt timestamp, sequence and append-before-JPEG ordering unchanged. Close descriptor on stop/launch-error/write-error. New separate driver copy; original untouched.'}
(O/'intake/source-recorder-r130.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
print(json.dumps(receipt))
