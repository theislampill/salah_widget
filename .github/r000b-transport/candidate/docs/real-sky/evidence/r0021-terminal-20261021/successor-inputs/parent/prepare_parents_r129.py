"""Two identified acquisition fixes; retain actual installed extension and UI import."""
from pathlib import Path
import ast,hashlib,json,shutil
P=Path(__file__).resolve().parent;O=P.parent
H=O/'parent-tools-r129';assert not H.exists()
shutil.copytree(O/'parent-tools-r125',H,ignore=shutil.ignore_patterns('__pycache__'))
def change(text,old,new):
 assert text.count(old)==1,old
 return text.replace(old,new)
p=H/'tools/cp9/celestial_startup_check.py';s=p.read_text(encoding='utf-8')
old="    await parent.screenshot(path=str(a.out/'parent-import.png'))"
new="""    # Tabliss's source batches configuration writes for 1000ms. Attachment
    # is not persistence. Read only the two imported widget keys before closing.
    expected={'tabliss/config/'+k:preset[k] for k in ['widget/orpul7IDXSSP','data/orpul7IDXSSP']}
    persisted=[];deadline=time.monotonic()+15
    while True:
     stored=await parent.evaluate('(keys)=>chrome.storage.sync.get(keys)',list(expected))
     persisted.append({'atUtcMs':time.time()*1000,'stored':stored,'matches':stored==expected})
     report['parentPreparation']['storagePersistence']=persisted;save()
     if stored==expected:break
     if time.monotonic()>deadline:raise TimeoutError('Actual imported Tabliss sync configuration not persisted within15s')
     await asyncio.sleep(.1)
    await parent.screenshot(path=str(a.out/'parent-import.png'))"""
s=change(s,old,new)
# Fresh-page persistence is independently read back in the real parent.
s=change(s,"   report['runs'].append(run_record);save()","   if a.entry=='extension':run_record['parentStoredConfig']=await page.evaluate('(keys)=>chrome.storage.sync.get(keys)',list(expected))\n   report['runs'].append(run_record);save()\n   if a.entry=='extension':assert run_record['parentStoredConfig']==expected,'Fresh parent lost imported configuration'")
ast.parse(s);p.write_text(s,encoding='utf-8',newline='\n')

p=P/'firefox_actual_widget_r129.py';s=(P/'firefox_actual_widget_r125.py').read_text(encoding='utf-8')
s=s.replace('firefox-actual-widget-r125','firefox-actual-widget-r129').replace('integrated-r30-owner-callbacks','integrated-r31-file-transport').replace('3e18b2fa83d0cbfce0a4360d789f7927aef5c064f963e8c18acb430507995821','1b6586d8921a99780b2cefff95821ad90bf39571ef074ccffe4234ec8aa7f02b')
start=s.index('   def compositor_shot(name):');end=s.index('   enter_widget()\n   def ready_state',start)
existing=s[start:end]
# Reuse precisely the already supported Capture.sys.mjs readback. Its initial
# calls are in the parent, so expected identity comes from that current context.
shot=existing.replace('   def compositor_shot(name):','   def shot(name):').replace("    client.call('WebDriver:SwitchToFrame',{'id':None});client.call('Marionette:SetContext',{'value':'chrome'})", "    expected=client.call('WebDriver:GetCurrentURL')['value']\n    client.call('Marionette:SetContext',{'value':'chrome'})").replace("     expected=report['parentUrl']['value']\n",'').replace("client.call('Marionette:SetContext',{'value':'content'});enter_widget()","client.call('Marionette:SetContext',{'value':'content'})")
shot=shot.replace("     report.setdefault('compositorReadbacks',[]).append({'name':name,**result})", "     report.setdefault('compositorReadbacks',[]).append({'name':name,**result})\n     assert result.get('geometryValid'),'Original compositor pixels/geometry unavailable'")
old_start=s.index('   def shot(name):');old_end=s.index('   preset_path=',old_start)
s=s[:old_start]+shot+s[old_end:]
start=s.index('   def compositor_shot(name):');end=s.index('   enter_widget()\n   def ready_state',start)
s=s[:start]+"   def compositor_shot(name):\n    client.call('WebDriver:SwitchToFrame',{'id':None});shot(name);enter_widget()\n"+s[end:]
assert 'WebDriver:TakeScreenshot' not in s
ast.parse(s);p.write_text(s,encoding='utf-8',newline='\n')

p=O/'run_parents_r129.py';s=(O/'run_visual_parent_r125_r126.py').read_text(encoding='utf-8')
s=s.replace('integrated-r30-owner-callbacks','integrated-r31-file-transport').replace('visual-parent-r125-r126','parents-r129').replace('3e18b2fa83d0cbfce0a4360d789f7927aef5c064f963e8c18acb430507995821','1b6586d8921a99780b2cefff95821ad90bf39571ef074ccffe4234ec8aa7f02b').replace('parent-tools-r125','parent-tools-r129').replace('firefox_actual_widget_r125.py','firefox_actual_widget_r129.py').replace('firefox-actual-widget-r125','firefox-actual-widget-r129')
lines=s.splitlines(keepends=True)
lines=[line for line in lines if not line.startswith("  ('firefox-") and not line.startswith("  ('chromium-twilight'")]
s=''.join(lines).replace("('chromium-cloud-parent','chromium','partial','extension',1,'parent-new-tab','parent-tools-r129'),", "('chromium-cloud-parent','chromium','partial','extension',1,'parent-new-tab','parent-tools-r129')]:")
s=s.replace("'No repeats remain; each named case once.","'Authorized successor; corrected import-persistence/readback only. Each named case once.")
s=s.replace("'Five missing ordinary conditions and two actual-parent sequences with one Ccloud overlap; r119 source unchanged. Twilight10:58Z source arithmetic gives UI solar elevation -6.139996 degrees and moonShow0.627999; actual returned state/pixels still required; no natural whole-day claim.'","'Actual installed C/F parents; C native storage commit barrier, F existing original compositor route. Current r127 runtime; no cold S1 or uninterrupted pixels claim.'")
s=s.replace("paths=[Path(__file__),", "paths=[Path(__file__),O/'parent/prepare_parents_r129.py',")
ast.parse(s);p.write_text(s,encoding='utf-8',newline='\n')
print('r129 acquisition candidates prepared; no native execution')
