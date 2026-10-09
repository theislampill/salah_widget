import ast,pathlib
base=pathlib.Path(__file__).parent
fixture=(base/'native-radio-fixture.cjs').read_text(encoding='utf-8')
before="mode:embedMode,focus:document.activeElement.id,buttons:"
assert fixture.count(before)==1
fixture=fixture.replace(before,"mode:embedMode,focus:document.activeElement.id,scroll:{x:scrollX,y:scrollY},buttons:")
(base/'native-radio-fixture-v2.cjs').write_text(fixture,encoding='utf-8')
driver=(base/'radio_keyboard_check.py').read_text(encoding='utf-8')
driver=driver.replace('native-radio-fixture.cjs','native-radio-fixture-v2.cjs')
before="selected(after,mode,True);assert after['revision']==before['revision']+1,key+' updates once';return after"
after="""selected(after,mode,True);assert after['revision']==before['revision']+1,key+' updates once'
        if key.startswith('Arrow'):assert after['scroll']==before['scroll'],key+' must prevent native document scrolling'
        return after"""
assert driver.count(before)==1;driver=driver.replace(before,after)
before="for key in ['Enter','Space']:change(key,'local')"
after="""for mode in ['local','portable']:
         page.locator('#mode-'+mode).focus()
         for key in ['Enter','Space']:change(key,mode)"""
assert driver.count(before)==1;driver=driver.replace(before,after)
before="before=snap('before click');page.locator('#mode-portable').click();after=snap('click portable');selected(after,'portable');assert after['revision']==before['revision']+1"
after="""before=snap('before click');page.locator('#mode-local').click();after=snap('click local');selected(after,'local');assert after['revision']==before['revision']+1
        before=snap('clicked local before Tab');page.keyboard.press('Tab');after=snap('clicked local Tab exit');assert after['focus'] not in ['mode-portable','mode-local'];assert after['revision']==before['revision'];selected(after,'local')
        page.keyboard.press('Shift+Tab');after=snap('clicked local Shift+Tab entry');selected(after,'local',True);assert after['revision']==before['revision']"""
assert driver.count(before)==1;driver=driver.replace(before,after)
ast.parse(driver)
(base/'radio_keyboard_check_v2.py').write_text(driver,encoding='utf-8')
print('V2 prepared and AST validated only; no browser/server launched. V1 driver and fixture preserved for receipt hash custody.')
