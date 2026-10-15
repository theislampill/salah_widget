def capture(page,args,out,result,errors):
    result['before']=page.evaluate(INSPECT)
    page.screenshot(path=str(out/'full.png'))
    page.evaluate('window.__appearanceFixture.setTextHidden(true)')
    page.evaluate('() => new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')
    result['hidden']=page.evaluate(INSPECT);page.screenshot(path=str(out/'text-hidden.png'))
    page.evaluate('window.__appearanceFixture.setTextHidden(false)')
    page.evaluate('() => new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')
    result['restored']=page.evaluate(INSPECT);page.screenshot(path=str(out/'restored.png'))
    page.evaluate('window.__appearanceFixture.setTextHidden(true)')
    page.evaluate('() => new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')
    result['hidden2']=page.evaluate(INSPECT);page.screenshot(path=str(out/'text-hidden-2.png'))
    page.evaluate('window.__appearanceFixture.setTextHidden(false)')
    page.evaluate('() => new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')
    result['final']=page.evaluate(INSPECT)
    full=Image.open(out/'full.png').convert('RGB');hidden=Image.open(out/'text-hidden.png').convert('RGB');restored=Image.open(out/'restored.png').convert('RGB');hidden2=Image.open(out/'text-hidden-2.png').convert('RGB')
    tests=[];text_results=[]
    for i,row in enumerate(result['before']['rows']):
        for k,t in enumerate(row['texts']):
            r=t['rect'];box=(math.floor(r['x']*args.dpr),math.floor(r['y']*args.dpr),math.ceil((r['x']+r['width'])*args.dpr),math.ceil((r['y']+r['height'])*args.dpr))
            fg=tuple(map(float,re.findall(r'[\d.]+',t['color'])[:3]));a=full.crop(box);b=hidden.crop(box);a2=restored.crop(box);b2=hidden2.crop(box)
            for name,im in [('text',a),('background',b),('text-2',a2),('background-2',b2)]:im.save(out/f'{name}-{i}-{k}.png')
            pixels=lambda im:list(im.get_flattened_data()) if hasattr(im,'get_flattened_data') else list(im.getdata())
            px=pixels(b);minimum=min(ratio(fg,c) for c in px);minimum2=min(ratio(fg,c) for c in pixels(b2))
            opacity=math.prod(v['opacity'] for v in t['chain'])
            changed=[ratio(x,y) for x,y in zip(pixels(a),px) if max(abs(x[c]-y[c]) for c in range(3))>=8]
            changed2=[ratio(x,y) for x,y in zip(pixels(a2),pixels(b2)) if max(abs(x[c]-y[c]) for c in range(3))>=8]
            entry={'row':i,'textIndex':k,'text':t['text'],'className':row['className'],'rect':r,'box':box,'foreground':fg,'ancestorOpacity':opacity,'minimumIntendedContrast':min(minimum,minimum2),'pairIntendedContrasts':[minimum,minimum2],'changedPixelCount':len(changed),'secondChangedPixelCount':len(changed2),'maxChangedPixelContrastDiagnostic':max(changed) if changed else None,'secondMaxChangedPixelContrastDiagnostic':max(changed2) if changed2 else None,'visiblePairDifferenceDiagnostic':difference(a,a2),'hiddenPairDifferenceDiagnostic':difference(b,b2)}
            text_results.append(entry)
            tests.extend([{'name':f'text-{i}-{k}-opacity1','pass':opacity==1},{'name':f'text-{i}-{k}-intended-contrast','pass':minimum>=4.5 and minimum2>=4.5},{'name':f'text-{i}-{k}-visible-pixels','pass':bool(changed) and bool(changed2)}])
    card=result['before']['card'];box=(round(card['x']*args.dpr),round(card['y']*args.dpr),round((card['x']+card['width'])*args.dpr),round((card['y']+card['height'])*args.dpr))
    full.crop(box).save(out/'card.png');hidden.crop(box).save(out/'card-text-hidden.png');restored.crop(box).save(out/'card-2.png');hidden2.crop(box).save(out/'card-text-hidden-2.png')
    pair_difference=ImageChops.difference(full,hidden);mask=ImageDraw.Draw(pair_difference)
    for t in text_results:
        x0,y0,x1,y1=t['box'];mask.rectangle((x0,y0,x1-1,y1-1),fill=(0,0,0))
    # Shadows may extend outside glyph rectangles; they are deliberately
    # diagnostics, not intended-colour contrast or a geometry tolerance.
    result['textHiddenOutsideRectDifferenceDiagnostic']=pair_difference.crop(box).getbbox()
    result['wholeRestoredDifferenceDiagnostic']=difference(full,restored)
    result['wholeHiddenDifferenceDiagnostic']=difference(hidden,hidden2)
    states=[result[k] for k in ['before','hidden','restored','hidden2','final']]
    equal=lambda key:all(s[key]==states[0][key] for s in states)
    tests.extend([{'name':'card325x530','pass':card['width']==325 and card['height']==530},{'name':'actual-viewport-dpr','pass':result['before']['viewport']=={'width':args.width,'height':args.height,'dpr':args.dpr}},{'name':'twelve-text-rects','pass':len(text_results)==12},{'name':'same-native-geometry','pass':equal('geometry')},{'name':'same-text-style-font-rectangles','pass':equal('rows') and equal('fonts') and equal('cardClasses')},{'name':'same-clock-native-scene-and-visible-canvas-pixels','pass':equal('scene')},{'name':'native-renderer-valid-through-pairs','pass':all(renderer_valid(s) for s in states)},{'name':'no-blocked-runtime-fetch','pass':all(not s['unexpectedFetch'] for s in states)},{'name':'text-restored','pass':result['final']['textHidden'] is False},{'name':'no-page-errors','pass':not errors}])
    result.update(texts=text_results,checks=tests,status='PASS_SCOPED' if all(t['pass'] for t in tests) else 'FAIL',failures=[t['name'] for t in tests if not t['pass']])
