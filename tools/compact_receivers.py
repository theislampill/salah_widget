"""Deterministic SMH1 encoding of the pinned V5 initial receiver binary.

This is a new lossy INITIAL representation. It keeps the original 540-grid
coverage, source-derived depth/normal/material/horizon terms, and no phase or
time. It does not alter the full renderer, its assets, or the V5 surface map.
Only the selected scalar precisions are supported. No I/O or dependencies.
"""
from collections import Counter
import hashlib
import heapq
import struct

_PARENT_SHA = '0c5e4be7808367211ab3a8fec8a8dcba76f6f9a69ebf5591dc76ed3e188b2444'
_DECODED_SHA = '25755b217ec6da7401740b3d4df06d23c917e4bfc447d5667938b7b960a69331'
_PAYLOAD_SHA = 'dc131b3858aa20ddc858ccf1058fdcba533ec70d98f5d3bb28d1afc77b307269'
_RECORD = struct.Struct('<fhhhHHHHH')
_N, _COUNT, _MASK_BYTES = 540, 196435, 36450
_WIDTHS = (8, 5, 5, 5, 5, 5, 8, 8)


def _sha(value):
    return hashlib.sha256(value).hexdigest()


def _scalar(values, bits, low, high):
    levels = (1 << bits) - 1
    return [max(0, min(levels, int((v-low)/(high-low)*levels+.5))) for v in values]


def _oct5(normal):
    x, y, z = normal
    length = abs(x)+abs(y)+abs(z)
    x, y, z = x/length, y/length, z/length
    if z < 0:
        x, y = ((1-abs(y))*(1 if x >= 0 else -1),
                (1-abs(x))*(1 if y >= 0 else -1))
    return tuple(max(0, min(31, int((v*.5+.5)*31+.5))) for v in (x, y))


def _paeth(a, b, c):
    p = a+b-c
    da, db, dc = abs(p-a), abs(p-b), abs(p-c)
    return a if da <= db and da <= dc else b if db <= dc else c


def _huffman(values, bits):
    queue, serial = [], 0
    for symbol, frequency in sorted(Counter(values).items()):
        heapq.heappush(queue, (frequency, serial, symbol))
        serial += 1
    while len(queue) > 1:
        a, b = heapq.heappop(queue), heapq.heappop(queue)
        heapq.heappush(queue, (a[0]+b[0], serial, (a[2], b[2])))
        serial += 1
    lengths = [0]*(1 << bits)

    def walk(node, depth):
        if isinstance(node, int):
            lengths[node] = max(1, depth)
        else:
            walk(node[0], depth+1)
            walk(node[1], depth+1)

    walk(queue[0][2], 0)
    if max(lengths) > 20:
        raise ValueError('Compact Huffman decoder depth')
    codes, code, previous = {}, 0, 0
    for length, symbol in sorted((length, symbol) for symbol, length in enumerate(lengths) if length):
        code <<= length-previous
        codes[symbol] = code, length
        code += 1
        previous = length
    encoded, accumulator, available = bytearray(), 0, 0
    for value in values:
        code, length = codes[value]
        accumulator = (accumulator << length) | code
        available += length
        while available >= 8:
            available -= 8
            encoded.append((accumulator >> available) & 255)
            accumulator &= (1 << available)-1
    if available:
        encoded.append((accumulator << (8-available)) & 255)
    return struct.pack('<BI', bits, len(encoded))+bytes(lengths)+bytes(encoded)


def compact_receivers(original_bytes):
    """Return (encoded_bytes, encoding_manifest), or reject an unpinned source.

    The native host must validate this manifest and decoded SHA, then pass the
    decoded bytes to its unchanged initial V5 consumer under the NEW decoded
    identity. Never admit them using the original receiver SHA.
    """
    if not isinstance(original_bytes, bytes) or len(original_bytes) != 3965156 or _sha(original_bytes) != _PARENT_SHA:
        raise ValueError('Compact receiver parent identity')
    if struct.unpack_from('<IH', original_bytes) != (0x31494d53, _N):
        raise ValueError('Compact receiver source shape')
    mask = original_bytes[6:6+_MASK_BYTES]
    indices = [i for i in range(_N*_N) if mask[i >> 3] & (1 << (i & 7))]
    rows = list(_RECORD.iter_unpack(original_bytes[6+_MASK_BYTES:]))
    if len(indices) != _COUNT or len(rows) != _COUNT:
        raise ValueError('Compact receiver source count')
    columns = list(zip(*rows))
    ranges = [(min(v), max(v)) for v in columns]
    depth = _scalar(columns[0], 8, *ranges[0])
    octahedral = [_oct5(row[1:4]) for row in rows]
    colour = [_scalar(columns[k+4], 5, *ranges[k+4]) for k in range(3)]
    horizons = [_scalar(columns[k+7], 8, 0, 65535) for k in range(2)]
    channels = [depth, [v[0] for v in octahedral], [v[1] for v in octahedral], colour[1],
                [(r-g) & 31 for r, g in zip(colour[0], colour[1])],
                [(b-g) & 31 for b, g in zip(colour[2], colour[1])], horizons[0],
                [(a+b-255) & 255 for a, b in zip(*horizons)]]
    streams = []
    for values, bits in zip(channels, _WIDTHS):
        dense, residuals, modulus = [0]*(_N*_N), [], (1 << bits)-1
        for i, value in zip(indices, values):
            y, x = divmod(i, _N)
            predicted = _paeth(dense[i-1] if x else 0, dense[i-_N] if y else 0,
                               dense[i-_N-1] if x and y else 0)
            residuals.append((value-predicted) & modulus)
            dense[i] = value
        streams.append(_huffman(residuals, bits))
    encoded = b'SMH1'+struct.pack('<HI', _N, _COUNT)+mask+b''.join(streams)
    if len(encoded) != 549170 or _sha(encoded) != _PAYLOAD_SHA:
        raise ValueError('Compact receiver deterministic encoding drift')
    fields = [{'field': 'depth', 'bits': 8, 'range': ranges[0]},
              {'field': 'oct0', 'bits': 5}, {'field': 'oct1', 'bits': 5}]
    fields.extend({'field': 'colour'+str(k), 'bits': 5, 'range': ranges[k+4]} for k in range(3))
    fields.extend({'field': 'horizon'+str(k), 'bits': 8, 'exact': False} for k in range(2))
    manifest = {'schema': 'moon-initial-compact/1', 'method': 'paeth-huffman',
                'parentReceiverSha256': _PARENT_SHA, 'size': _N, 'records': _COUNT,
                'bytes': len(encoded), 'sha256': _sha(encoded),
                'decodedSha256': _DECODED_SHA, 'fields': fields}
    return encoded, manifest
