"""R0040 depictability and effective-gain arithmetic (research only; stdout only, no I/O).

Reproduces the numbers quoted in the R0040 work order from the stated relations and the prototype's parameter
values (tools/qa/precip_models.js, object P). python tools/qa/precip_r0040_calc.py
"""
import math

F, T = 265.0, 1 / 60           # focal length px (530 px, 90 deg), exposure s
GK = [(0.1, 0.27), (0.2, 0.72), (0.3, 1.17), (0.4, 1.62), (0.5, 2.06)]   # Gunn-Kinzer below 0.5 mm (recalled)


def vt(D):
    if D >= 0.5:
        return 9.65 - 10.3 * math.exp(-0.6 * D)                      # Atlas fit
    for (d0, v0), (d1, v1) in zip(GK, GK[1:]):
        if D <= d1:
            return v0 + (v1 - v0) * (D - d0) / (d1 - d0)
    return 0.27 * D / 0.1


def streak(D, z, cos_alt=0.71):
    a = D / 2000.0
    v = vt(D)
    return {'D_mm': D, 'z_m': z, 'v_ms': round(v, 2), 'width_px': round(F * D / 1000 / z, 3),
            'len_raw_px': round(F * v * T / z, 2), 'len_centre_px': round(F * v * T / z * cos_alt, 2),
            'contrast_pct': round(100 * 4 * F * a * a / (z * v * T), 3)}


print('# C.3 depictability (per-streak contrast is a fraction of (L_env - L_b); length per 1/60 s frame)')
for D, z in [(0.3, 1.0), (0.5, 1.0), (1.0, 1.0), (1.0, 3.0), (2.0, 1.0), (2.0, 3.0), (4.0, 1.0)]:
    print(streak(D, z))

# frustum of rows 8..300 over the full width: area at depth z = (W/F z)(rows/F z)
W, rows = 325, 292
print('\n# frustum factor K for rows 8-300: V = K (z2^3 - z1^3); prototype used 0.355 (rows 40-270)')
print({'K_rows_8_300': round(W * rows / F ** 2 / 3, 4), 'K_rows_40_270': round(W * 230 / F ** 2 / 3, 4), 'K_rows_100_232': round(W * 132 / F ** 2 / 3, 4)})

# mid-texture tile rescale (exactly as buildTiles in precip_models.js)
fams = {'drizzle 0.32': (30000, 5.7, 0.32), 'light 1.2': (8000, 4.1, 1.2), 'moderate 5': (8000, 4.1, 5), 'heavy 12': (8000, 4.1, 12),
        'showers 3 (convective)': (1400, 3.0, 3)}
TW, TH, CAP, K = 352, 320, 9000, 0.355
print('\n# M2/M5 mid-texture: strokes per tile, rescale factor = total/cap (per-stroke alpha x factor, capped 0.9)')
for name, (N0, a, R) in fams.items():
    L = a * R ** -0.21
    out = {}
    for zA, zB in [(1.5, 3), (3, 10)]:
        tot = 0.0
        D = 0.3
        while D < 6:
            N = N0 * math.exp(-L * D) * 0.1
            zr = min(zB, F * vt(D) * T / 3)
            if zr > zA:
                tot += N * K * (zr ** 3 - zA ** 3) * (TW * TH) / (W * rows)
            D += 0.1
        scale = tot / CAP if tot > CAP else 1.0
        out[f'{zA}-{zB} m'] = {'strokes_physical': round(tot), 'rescale': round(scale, 2), 'per_stroke_gain': round(100 * scale)}
    print(name, out)

print('\n# near-streak width floor: drawn width max(1, min(2.2, F D/z + 0.6)) px; energy factor vs a 1 px per-pixel streak')
for D, z in [(0.3, 1.0), (1.0, 1.0), (1.0, 0.5), (2.0, 1.0), (2.0, 0.7), (3.0, 0.7)]:
    w = max(1, min(2.2, F * D / 1000 / z + 0.6))
    print({'D_mm': D, 'z_m': z, 'drawn_width_px': round(w, 2), 'physical_width_px': round(F * D / 1000 / z, 2), 'energy_factor': round(w, 2)})

print('\n# Sun kernel: environment lift near the Sun = 0.55 * sunamt * (1 - cloud^2) * 255 codes x gaussian(120 px)')
for cloud in (0.0, 0.5, 0.85, 1.0):
    lift = 0.55 * 1.0 * (1 - cloud * cloud) * 255
    print({'cloud': cloud, 'lift_codes_at_sun': round(lift, 1), 'gain_if_env_minus_bg_5_codes': round((5 + lift) / 5, 1), 'at_240px': round(lift * math.exp(-240 ** 2 / (2 * 120 ** 2)), 1)})

print('\n# lean tan(phi) = u/v_t at D0 = 3.67/Lambda (Marshall-Palmer), eye-level factor 0.8 (recalled) vs 1.0')
for R in (1.2, 5, 12):
    L = 4.1 * R ** -0.21
    D0 = 3.67 / L
    for S in (2, 5, 10):
        print({'R': R, 'D0': round(D0, 2), 'v': round(vt(D0), 2), 'S': S, 'lean_k0.8': round(math.degrees(math.atan(0.8 * S / vt(D0))), 1), 'lean_k1.0': round(math.degrees(math.atan(S / vt(D0))), 1)})
