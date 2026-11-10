import sys,json,os
from pathlib import Path
os.environ['SALAH_BROWSER_EXECUTABLE']=r'C:\Users\theis\AppData\Local\ms-playwright\chromium-1223\chrome-win64\chrome.exe'
sys.path.insert(0,r'C:\Users\theis\.codex\worktrees\cp9-moon-v5-integration\salah_widget\tools\cp9')
from browser_runtime import launch_browser
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
 b=launch_browser(p);q=b.new_page();r=q.evaluate('''()=>{const c=document.createElement('canvas'),x=c.getContext('2d'),rows=[];for(let k=0;k<4;k++){c.width=c.height=300;const a=new Uint8ClampedArray(300*300*4);for(let i=0;i<a.length;i+=4){a[i]=(i/4)%255;a[i+1]=32;a[i+2]=65;a[i+3]=(i/4)%256;}x.putImageData(new ImageData(a,300,300),0,0);const before=c.toDataURL(),first=x.getImageData(0,0,300,300).data,after=c.toDataURL(),d=document.createElement('canvas');d.width=d.height=300;const y=d.getContext('2d');y.putImageData(new ImageData(a,300,300),0,0);const expected=y.getImageData(0,0,300,300).data;let opaque=0,edges=0,alpha=0;for(let i=0;i<a.length;i++){if(first[i]!==expected[i]){if(i%4===3)alpha++;else if(a[i-i%4+3]===255)opaque++;else edges++;}}rows.push({k,pngUnchanged:before===after,opaque,edges,alpha});}return rows;}''');b.close()
print(json.dumps(r,indent=2));Path(__file__).with_suffix('.json').write_text(json.dumps(r,indent=2)+'\n')
