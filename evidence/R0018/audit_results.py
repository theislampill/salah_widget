"""Reconcile original R0018 receipts without modifying their verdicts."""
from pathlib import Path
import hashlib,json,sys
from PIL import Image,ImageChops,ImageDraw
from run_matrix import cases

OUT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,value):p.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def name(stage,engine,c):
    return '-'.join([stage,engine,c['scene'],c['view'],'dpr'+str(c['dpr']),c['date'],c['appearance']]+(['white'] if c['stress'] else []))
def baseline_path(engine,c):
    p=OUT/'matrix'/name('red',engine,c)
    # Explicit replacement identities; never select whichever run happened to pass.
    if engine=='chromium' and c['view']=='constrained' and c['dpr']==2:
        if c['date']=='long' or c['appearance']=='contrast':p=p.with_name(p.name+'-r2')
    return p
def geometry(s):
    return {'geometry':s['geometry'],'viewport':s['viewport'],'card':s['card'],
            'dates':[s['ce'],s['ah']], 'rows':[{'text':r['text'],'className':r['className'],'rect':r['rect'],
            'texts':[{k:t[k] for k in ['text','rect','font','fontFamily','fontWeight']} for t in r['texts']]} for r in s['rows']]}

def differences(before,after,path=''):
    if isinstance(before,dict) and isinstance(after,dict):
        return [d for key in sorted(set(before)|set(after)) for d in differences(before.get(key),after.get(key),path+'/'+key)]
    if isinstance(before,list) and isinstance(after,list) and len(before)==len(after):
        return [d for i,(a,b) in enumerate(zip(before,after)) for d in differences(a,b,path+'/'+str(i))]
    return [] if before==after else [{'path':path,'baseline':before,'candidate':after}]

def main():
    rows=[];mutants=[];pairs=OUT/'comparisons';pairs.mkdir(exist_ok=True)
    control=OUT/'geometry-firefox-noon-desktop-dpr1/results.json'
    assert sha(control)=='3dbfb70367978287e2d58a28df651d822e111c8cd1a20544877fb17098eb4ba8'
    control_data=read(control)
    assert control_data['status']=='PASS_SCOPED' and control_data['geometryControl']['allGeometryExact']
    for engine in ['chromium','firefox']:
        for c in cases():
            old=baseline_path(engine,c);new=OUT/'matrix'/name('green',engine,c)
            if not (old/'results.json').is_file() or not (new/'results.json').is_file():continue
            b,a=read(old/'results.json'),read(new/'results.json')
            semantic_red=bool(b.get('failures')) and all(n.startswith('text-') and (n.endswith('-opacity1') or n.endswith('-intended-contrast')) for n in b['failures'])
            assert semantic_red if c['appearance']=='default' else b['status']=='PASS_SCOPED',(old,b.get('failures'))
            assert a['status']=='PASS_SCOPED',(new,a.get('failures'))
            drift=differences(geometry(b['before']),geometry(a['before']));exact=not drift
            # Retain every cross-load discrepancy. This is not a numerical tolerance
            # or omission: a separately reviewed exact-rule reversal supplies the
            # bounded no-CSS-movement evidence in the settled native page.
            if drift:assert engine=='firefox' and all(d['path']=='/geometry/.cn/rect/y' for d in drift),(old,new,drift)
            # Early RED collectors did not expose this later-added field. Do not
            # invent a baseline value or silently label it an exact comparison.
            box_comparison=[]
            for old_row,new_row in zip(b['before']['rows'],a['before']['rows']):
                if 'boxStyle' in old_row:
                    assert old_row['boxStyle']==new_row['boxStyle'],'Recorded row box style changed'
                    box_comparison.append('EXACT_RECORDED_PAIR')
                else:box_comparison.append('RED_FIELD_ABSENT_SOURCE_GUARD_AND_SAME_PAGE_CONTROL')
            assert b['sourceRuntime']['treeSha256']=='5ff3fdf5a13cd3a798addfef972ed9a2c865f87cce531a23847015dcdc8a7d46'
            assert a['sourceRuntime']['treeSha256']=='67fd9c8f122100506bef93473a1e335b8b441ac7bf55f540c099d2e34e5c970c'
            assert b['runtimeUnchanged'] and a['runtimeUnchanged']
            oldim=Image.open(old/'card.png').convert('RGB');newim=Image.open(new/'card.png').convert('RGB');second=Image.open(new/'card-2.png').convert('RGB')
            sheet=Image.new('RGB',(oldim.width*3,oldim.height+26),'#111827');d=ImageDraw.Draw(sheet)
            for i,(label,im) in enumerate([('original baseline',oldim),('candidate visible pair 1',newim),('candidate visible pair 2',second)]):d.text((i*im.width+8,5),label,fill='white');sheet.paste(im,(i*im.width,26))
            sheet.save(pairs/(new.name+'.png'))
            row={'id':new.name,'case':c,'engine':engine,'baseline':old.relative_to(OUT).as_posix(),'candidate':new.relative_to(OUT).as_posix(),'baselineReceiptSha256':sha(old/'results.json'),'candidateReceiptSha256':sha(new/'results.json'),'baselineDisposition':'EXPECTED_SEMANTIC_RED' if semantic_red else 'OPTIONAL_CONTRAST_HEALTHY_CONTROL','candidateStatus':a['status'],'geometryFontsStringsClassesExact':exact,'crossLoadGeometryDifferences':drift,'geometryDisposition':'EXACT_CROSS_LOAD' if exact else 'RETAINED_DIFFERENCE_WITH_REVIEWED_SAME_PAGE_RULE_CONTROL','minIntendedContrast':min(t['minimumIntendedContrast'] for t in a['texts']),'opacity1':all(t['ancestorOpacity']==1 for t in a['texts']),'comparison':(pairs/(new.name+'.png')).relative_to(OUT).as_posix()}
            rows.append(row)
            row['rowBoxStyleEvidence']=box_comparison
        for mutant in ['default-past','default-base','default-on']:
            path=OUT/'matrix'/f'mutant-{engine}-noon-desktop-dpr1-compact-default-white-{mutant}'
            if not (path/'results.json').is_file():continue
            r=read(path/'results.json');assert r['status']=='FAIL'
            checks={c['name']:c['pass'] for c in r['checks']};expected=[]
            for t in r['texts']:
                prefix=f"text-{t['row']}-{t['textIndex']}"
                if mutant=='default-past' and 'past' in t['className'].split():expected.append(prefix+'-opacity1')
                if mutant=='default-base' and 'on' not in t['className'].split():expected.append(prefix+'-intended-contrast')
                if mutant=='default-on' and 'on' in t['className'].split():expected.append(prefix+'-intended-contrast')
            assert expected and all(checks.get(n) is False for n in expected),(path,expected,r['failures'])
            assert all(n.startswith('text-') and (n.endswith('-opacity1') or n.endswith('-intended-contrast')) for n in r['failures'])
            mutants.append({'engine':engine,'mutation':mutant,'result':path.relative_to(OUT).as_posix(),'receiptSha256':sha(path/'results.json'),'expectedReachedFailures':expected,'actualFailures':r['failures'],'disposition':'REACHED_SEMANTIC_LOSS','healthyControl':f'matrix/green-{engine}-noon-constrained-dpr2-compact-default-white'})
    geometry_review={'exactCrossLoad':sum(r['geometryFontsStringsClassesExact'] for r in rows),'retainedCrossLoadDifferences':sum(not r['geometryFontsStringsClassesExact'] for r in rows),'control':control.relative_to(OUT).as_posix(),'controlSha256':sha(control),'controlStatus':'PASS_SCOPED','unchangedFontWatchFitOwnerSha256':'556aae1bb95ddd3e71ee49cc7ee9eba51f9cbc5ecb27402aa7da3e4da2424f59','limitation':'Exact original and candidate CSS rules cause no geometry movement in the settled same native page; precise historical boot-time cause remains unestablished. No tolerance or .cn exclusion.'}
    value={'schema':'r0018-qualification-index/2','cases':rows,'mutants':mutants,'complete':len(rows)==38 and len(mutants)==6,'allGeometryExact':all(r['geometryFontsStringsClassesExact'] for r in rows),'geometryReconciliation':geometry_review,'minimumIntendedContrast':min((r['minIntendedContrast'] for r in rows),default=None),'scope':'Intended foreground versus each independently captured native hidden background; original antialias/shadow changed-pixel maxima remain diagnostics. Native screenshots require separate visual review. Historical unpinned date is not this controlled baseline.'}
    write(OUT/'qualification-index.json',value)
    print(json.dumps({k:v for k,v in value.items() if k not in ['cases','mutants']}))
    if '--complete' in sys.argv:
        assert value['complete'],'Required native cases or controls still absent'
        assert geometry_review['exactCrossLoad']==29 and geometry_review['retainedCrossLoadDifferences']==9,'Unexpected geometry population requires fresh reconciliation'

if __name__=='__main__':main()
