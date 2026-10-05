"""Explicit cross-platform browser selection. Never silently replace a requested engine."""
import os,shutil,platform
from pathlib import Path

def browser_options():
 family=os.environ.get('SALAH_BROWSER','chromium').strip().lower()
 if family not in {'chromium','firefox','webkit'}:raise ValueError('SALAH_BROWSER must be chromium, firefox or webkit')
 options={'headless':True}
 explicit=os.environ.get('SALAH_BROWSER_EXECUTABLE')
 if explicit:
  p=Path(explicit).expanduser()
  if not p.is_file():raise FileNotFoundError('Requested browser executable does not exist: '+str(p))
  options['executable_path']=str(p.resolve())
 elif family=='chromium':
  found=shutil.which('chromium') or shutil.which('chromium-browser')
  if found:options['executable_path']=found
 if family=='chromium':options['args']=['--no-sandbox','--disable-dev-shm-usage']
 return family,options

def launch_browser(playwright):
 family,options=browser_options()
 return getattr(playwright,family).launch(**options)

def browser_identity(browser):
 return {'family':os.environ.get('SALAH_BROWSER','chromium'),'version':browser.version,'os':platform.system(),'machine':platform.machine(),'executable':os.environ.get('SALAH_BROWSER_EXECUTABLE') or 'explicit system chromium if available; otherwise Playwright managed engine'}
