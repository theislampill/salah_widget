"""R0027 (issue #69): bounded fitted-spectrum retention over the immutable CP9 input.

`vendor/real-sky/src/spectral.mjs` memoizes Planck fits per exact B-V in the private
module Map `sfFitCache` with an unconditional insertion, so continuously varying twilight
B-V grows it without bound. This transform changes RETENTION ONLY: at most 12,000 exact
fits per module realm, evicting the oldest retained key (FIFO, Map insertion order) just
before a new key is inserted at capacity. Hits never reorder. Keys, fit iterations,
tables, Planck arithmetic, domain/fallback logic, the outer `sfCache` admission rule and
the frozen returned samples are untouched; only the two whitelisted spans below change.

Vendor bytes stay immutable; build_native.py applies this while copying the core, so the
generated core and bundles inherit it and are never hand-edited. Unexpected input digest
or anchor shape fails closed with an R0027 diagnostic; nothing is written. A new
scientific version must be reconciled here explicitly, never silently patched.
"""
import hashlib

SOURCE_SHA256 = '565517270e1cb313e72875409b93199e38237c7b74ed1b452a52ccd6b889120b'
OUTPUT_SHA256 = '4fcda07d1fc5a210d7d748a4c33518ed3068dbbf25eacf7415fa10abaad14489'
INTRODUCED_IDENTIFIERS = ('sfFitCacheLimit',)
BEFORE_DECLARATION = 'sfCache=new Map(),sfFitCache=new Map();'
AFTER_DECLARATION = ('sfCache=new Map(),sfFitCache=new Map(),sfFitCacheLimit=12000;\n'
                     '// R0027 retention (authored in tools/native_core_spectral_cache.py): at most sfFitCacheLimit exact-B-V fits per\n'
                     '// module realm; FIFO eviction of the oldest key before a new insertion at capacity. Values are unchanged.')
BEFORE_INSERTION = 'fit={samples:blackbodyShape(T),temperatureProxyK:T};sfFitCache.set(bv,fit);return fit;'
AFTER_INSERTION = ('fit={samples:blackbodyShape(T),temperatureProxyK:T};'
                   'if(sfFitCache.size>=sfFitCacheLimit)sfFitCache.delete(sfFitCache.keys().next().value);'
                   'sfFitCache.set(bv,fit);return fit;')
SPANS = ((BEFORE_DECLARATION, AFTER_DECLARATION), (BEFORE_INSERTION, AFTER_INSERTION))


def apply_spans(text: str) -> str:
    for before, after in SPANS:
        if text.count(before) != 1:
            raise ValueError('R0027 spectral anchor must occur exactly once: ' + before[:48])
        if after in text:
            raise ValueError('R0027 spectral anchor already transformed: ' + before[:48])
    for before, after in SPANS:
        text = text.replace(before, after, 1)
    return text


def bound_spectral_cache(source: bytes) -> bytes:
    if hashlib.sha256(source).hexdigest() != SOURCE_SHA256:
        raise ValueError('R0027 spectral source drift: reconcile the authored retention transform')
    out = apply_spans(source.decode('utf-8')).encode('utf-8')
    if hashlib.sha256(out).hexdigest() != OUTPUT_SHA256:
        raise ValueError('R0027 spectral output digest mismatch: the whitelisted delta changed')
    return out
