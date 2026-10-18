"""Generated entry ownership/order controls, not browser timing qualification."""
import hashlib
import re
import unittest
from pathlib import Path

R=Path(__file__).resolve().parents[2]

class NativeEntryOrder(unittest.TestCase):
 def test_complete_initial_producer_group_follows_markup_in_both_entries(self):
  host=(R/'moon/moon-host.js').read_text(encoding='utf-8')
  boundary='window.SalahMoonRuntime.installWorkerSource('
  self.assertEqual(host.count(boundary),1)
  initial,refinement=host.split(boundary);refinement=boundary+refinement
  for name in ['index.html','offline.html']:
   with self.subTest(entry=name):
    text=(R/name).read_text(encoding='utf-8')
    scripts=list(re.finditer(r'<script\b([^>]*)>([\s\S]*?)</script>',text))
    def unique(predicate):
     matches=[s for s in scripts if predicate(s)]
     self.assertEqual(len(matches),1)
     return matches[0]
    preview=unique(lambda s:'id="native-first-paint-code"' in s[1])
    moon=unique(lambda s:'id="moon-initial-code"' in s[1])
    native=unique(lambda s:s[2].startswith('\n"use strict";\n// ---- config:'))
    full=unique(lambda s:'id="moon-refinement-code"' in s[1])
    config_body=(R/'config.js').read_text(encoding='utf-8').replace('</script','<\\/script')
    config=unique(lambda s:'src="config.js"' in s[1]) if name=='index.html' else unique(lambda s:s[2]==config_body)
    # The native settings/neutral card must exist before the unchanged heavy
    # producers run. This offers raster work without a delay/readiness wrapper.
    self.assertLess(text.index('id="setClose"'),config.start())
    self.assertLess(config.start(),preview.start())
    self.assertLess(preview.start(),moon.start())
    self.assertLess(moon.start(),native.start())
    self.assertLess(native.start(),full.start())
    self.assertEqual(scripts[scripts.index(config)+1],preview)
    self.assertEqual(scripts[scripts.index(preview)+1],moon)
    self.assertEqual(scripts[scripts.index(moon)+1],native)
    self.assertEqual(scripts[scripts.index(native)+1],full)
    pin=re.search(r'data-sha256="([0-9a-f]{64})"',preview[1])[1]
    self.assertEqual(hashlib.sha256(preview[2].encode()).hexdigest(),pin)
    self.assertTrue(moon[2].endswith(initial.replace('</script','<\\/script')))
    self.assertEqual(full[2],refinement.replace('</script','<\\/script'))
    if name=='offline.html':
     self.assertEqual(config[2],(R/'config.js').read_text(encoding='utf-8').replace('</script','<\\/script'))
    self.assertIn('class="c sky-pending sky-initializing"',text[:config.start()])

if __name__=='__main__':unittest.main()
