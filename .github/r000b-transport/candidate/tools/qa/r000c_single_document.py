"""Use the delivered prayer fixture's preparse-hook approach for the C wrapper.

Reuse the weather wrapper's ingress, native Response, private storage, clock and
read-only observer verbatim. Avoid replacing a live browser document. This is
an acquisition variant, not a claim about the cause of failed native recordings.
"""
import hashlib
import re


def sha(text):
    return hashlib.sha256(text.encode('utf8')).hexdigest()


def span(text, start, end):
    assert text.count(start) == 1 and text.count(end) == 1, (start, end)
    a, b = text.index(start), text.index(end)
    assert b > a
    return text[a:b]


def prepare(source_bytes, wrapper_bytes):
    source, wrapper = source_bytes.decode('utf8'), wrapper_bytes.decode('utf8')
    declarations = span(wrapper, '  const nativeFetch=', '  // Serialized as a separate, labeled classic script')
    bridge = span(wrapper, '  function installWeatherBridge(){', '  async function start(){').rstrip()
    shims = span(wrapper, '    // These hooks must exist before DOM parsing', '    const doc=new DOMParser()')
    policy = re.search(r'  const policy="([^"]+)";', wrapper).group(1)
    bridge_expression = '(' + bridge.strip() + ')();'
    setup = ('(function(){\n"use strict";\n' + declarations +
             '\nreport.sourceSha256=' + repr(hashlib.sha256(source_bytes).hexdigest()) + ';\n' +
             'report.documentMode="single-document-preparse";\n' + shims + '\n' +
             'report.bridgeSha256=' + repr(sha(bridge_expression)) + ';\n' +
             'report.state="loading";\n' +
             'window.addEventListener("error",e=>{report.consoleErrors.push(e.message);failure(e.message);});\n' +
             'window.addEventListener("unhandledrejection",e=>{report.consoleErrors.push(String(e.reason));failure(e.reason);});\n' +
             'document.addEventListener("securitypolicyviolation",e=>failure("Blocked unexpected resource: "+e.blockedURI));\n' +
             'document.addEventListener("DOMContentLoaded",()=>{try{verifyHooks();if(!window.SalahConfig||typeof window.qaState!=="function"||!window.__smokeWeather)throw Error("Widget/bridge missing");if(!report.error)report.state="ready";}catch(e){failure(e);}},{once:true});\n' +
             '})();')
    # Only the three known font links are removed, exactly as in the original wrapper.
    fonts = re.findall(r'<link\b[^>]*href="https://fonts\.(?:googleapis|gstatic)\.com[^>]*>', source)
    assert len(fonts) == 3, 'Known font resource anchors drifted'
    html = source
    for font in fonts:
        assert html.count(font) == 1
        html = html.replace(font, '', 1)
    assert html.count('<head>') == 1 and html.count('</body>') == 1
    html = html.replace('<head>', '<head><base href="/product/"><meta http-equiv="Content-Security-Policy" content="' + policy + '"><script id="r000c-test-preload">' + setup + '</script>', 1)
    html = html.replace('</body>', '<script id="r000c-weather-read-only-bridge">' + bridge_expression + '</script></body>', 1)
    bodies = lambda text: re.findall(r'<script\b[^>]*>([\s\S]*?)</script>', text, flags=re.I)
    original, observed = bodies(source), bodies(html)
    assert observed[1:-1] == original, 'A product script body changed'
    return html.encode('utf8'), {'schema': 'r000c-single-document-binding/v1',
        'sourceSha256': hashlib.sha256(source_bytes).hexdigest(), 'wrapperSha256': hashlib.sha256(wrapper_bytes).hexdigest(),
        'observedHtmlSha256': sha(html), 'preloadSha256': sha(setup), 'bridgeSha256': sha(bridge_expression),
        'productScriptBodySha256': [sha(s) for s in original], 'allProductScriptBodiesUnchanged': True,
        'declarationSpanSha256': sha(declarations), 'isolationSpanSha256': sha(shims),
        'suppressedKnownFontLinks': fonts, 'CSP': policy,
        'difference': 'Original controlled ingress/clock/storage and read-only observer inserted before/after product parsing. No DOMParser, document.open/write/close or live document replacement.'}
