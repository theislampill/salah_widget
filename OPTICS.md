# salah_widget — Atmospheric Optics Taxonomy

Every atmospheric phenomenon is classified by **physical family** and **gated by physical drivers before it
renders** — this is a truthfulness + optical-coherence reference, not a VFX catalogue. If an effect cannot be made
physically plausible inside a 2-D canvas/CSS widget, it is **removed from production or made debug-only** rather
than left as a pretty lie. Gate formulas live in `atmosphere()` (index.html); sky writes in `paint()`. The art is
"realism-adjacent": believable and physics-gated, never random, never decorative.

**Families:** molecular (Rayleigh) · aerosol/haze (Mie) · volumetric water/ice cloud · ice-crystal geometric
optics · precipitation · thermal/material cues · celestial · visual-only UI. These are **not** interchangeable
"glow effects."

Contract per phenomenon: **family · inputs · gate · shape · NOT-shape · off-conditions · prod/debug · verdict**.

Recipe suffixes below append to the existing configuration fragment after `#`.
The six force names are `halo`, `sundogs`, `pillar`, `anticrep`, `paraselene` and `lunarhalo`;
corona, earthshine, refraction and the crepuscular ray require controlled physical scene inputs.
Complete activation/motion recipes are in [DESIGN.md](DESIGN.md#url--hash--debug-parameters).

---

## Group 1 — Diffuse (participating media + thermal)

### Base sky / twilight — *production*
- **Family:** molecular (Rayleigh) gradient + aerosol (Mie) sun-bloom.
- **Inputs:** solar elevation `sm.altDeg`, screen sun pos, `skyLum(e)`, haze, `airDrift`, weather class (tint
  applied *after* the physical gradient).
- **Gate:** colour derived from **solar elevation only** (`physSky`/`skyLum`) — **no prayer-name palette**. Warm
  horizon `clamp((e+12)/11)·(1−clamp((e−1)/9))`; bloom `clamp((e+5)/11)·0.30`.
- **Shape:** smooth night→day 3-stop gradient; Mie bloom at the sun; warm Rayleigh band under the sun's azimuth;
  exposure breathes ±~9% via the slow air-mass drift.
- **NOT:** a flat prayer-keyed swatch; discrete rays in clear sky; warm glow at noon/deep night; a painted dawn.
- **Off:** warm/glow → 0 at high sun & deep night.  **Verdict:** already-correct.

### True dawn — *production (physical, not a layer)*
- **Family:** molecular/aerosol twilight (the base sky itself).  **It is NOT a painted overlay.**
- **Gate/shape:** the real `skyLum` astronomical→nautical→civil brightening + the warm horizon scatter at the
  sun's azimuth, plus the Fajr marker/time on the arc. Genuinely dark at Fajr depth (~−15…−18°).
- **NOT:** a horizontal "true-dawn band/strip" painted on the sky.  **Verdict:** already-correct (band removed).
- A diagnostic-only scalar `trueDawnTwilight` exists in qaState; it paints nothing.

### False dawn (zodiacal light) — *NOT rendered (future work)*
- **Family:** sunlight scattered by interplanetary dust along the ecliptic.
- **Status:** **disabled in production.** A generic CSS cone read as a lens-flare/godray slash and showed under a
  bright moon, so it was removed (fail-closed).  **Verdict:** removed.
- A faithful future implementation must use: projected ecliptic orientation (not a fixed diagonal), eastern
  pre-sunrise anchor, triangular/wedge falloff, strict dark-sky + low/no-moon + low-light-pollution + clear/haze
  gating, very low opacity, no foreground-crossing slash, and no effect on Fajr/UI state.

### Belt of Venus — *production*
- **Family:** anti-solar back-scatter (twilight).
- **Inputs:** `sm.altDeg`, anti-solar x (`--antix`), weather class.
- **Gate:** `max(0, 1−|e+4|/5) · (clear||cloud ? 1 : 0)` — peaks at e≈−4°, **off under overcast/precip/fog**
  (tightened this pass from a 0.25 fallback, which let a faint band bleed through solid cloud).
- **Shape:** faint pink band on the anti-solar horizon at civil twilight.  **NOT:** on the sun side; through a
  solid deck; saturated.  **Verdict:** gated-tighter (done).

### Clouds — *production*
- **Family:** volumetric water/ice bodies, approximated as canvas puff-clusters with a time-noise lifecycle.
- **Inputs:** eligible model/marked preview low/mid/high cover, wind, humidity, sun/moon dir + up-ness,
  `cloudBase` tint and a signed target/seed/explicit preview identity. The initial day contribution is captured
  once; ordinary day/month/year/zone/weather changes retain population.
- **Gate:** clear (`cov<0.02`) paints nothing; lit-top/shaded-base volume; sun-side silver-lining rim
  (`sl·max(0,sCos)·0.85`); moon rim is **physical-only** (`moonLit`); per-class transmittance attenuates *flux*,
  not colour; bounded top brightness; coverage eases (no reseed/slideshow). Travel/morph/wander use bounded
  monotonic visual elapsed at the preview rate. Old wind covers the preceding interval before new wind applies;
  empty decks still advance. Hidden/reduced state rebases/holds; gaps over two seconds discard suspended time.
  An explicit seek reconstructs with zero initial displacement. Rates are artistic, not measured advection.
- **NOT:** a scrolled static texture; a uniform grey blanket; pop-in on refresh; lamp-bright blobs; the moon
  showing through a heavy deck.  **Verdict:** keep (advection/continuity load-bearing).
- *Improved (2026-06-16):* overcast now reads as a leaden ceiling — the sky tint behind the deck was neutralised +
  strengthened (`WX.overcast`), the overcast `cloudBase` darkened, and high-coverage puff opacity raised (all
  overcast/coverage-gated; broken & clear unchanged, motion preserved, moon stays opaque). Final aesthetic dial is
  the maintainer's.

### Fog / haze / humidity — *production*
- **Family:** aerosol / water-droplet participating media.
- **Gate:** haze **desaturates** + softens (stars, Milky Way, `starBlur`, aerial perspective) and warms the
  night airglow dome (`nightness·(0.06 + 0.20·haze + 0.10·humid + 0.55·LPOLL)`); fog is a distinct low CSS band
  shown only under `data-fx=fog`.
- **NOT:** a second cloud deck; haze that *adds* saturation; decorative directional inscattering cones (those
  create fake godrays — only the gated crepuscular shafts may use a cone).  **Verdict:** keep.

### Heat / cold / material cues — *production*
- **Family:** thermal/material state.
- **Inputs:** apparent temperature `feels` (which already folds in humidity + wind), via `wxDrivers`.
- **Gate:** `heat=r(feelsC,27,40)`, `cold=r(feelsC,8,−8)` → `warm=0.20·heat`, `cool=0.22·cold`, `frost=0.5·cold`;
  soft-light, **sky only (z-index 0), never the prayer panel.**
- **NOT:** a strong cast; a shimmer wobble loop; tinting the panel; keyed to raw air temp.  **Off:** warm→0 below
  27 °C, cool/frost→0 above 8 °C.  **Verdict:** keep (feels-like already incorporates humidity/wind).

---

## Group 2 — Discrete optics (gated, registered to the visible sun/moon)

All discrete solar optics register to the **visible corner-sun** screen position (`--sunvx/--sunvy`), not the
arc-sun azimuth — a halo centred mid-screen away from the sun is a bug.

One shared **`moonLightEligible`** decision governs all atmospheric lunar consumers: beam, cloud rim, local
stellar wash, generic glow, corona, halo and paraselenae. Near-new fraction ≤0.02, zero horizon permission or
daylight disables that light, including forced `lunarhalo`/`paraselene`. This permission cutoff leaves the
opaque night PBR surface and its night-side **Earthshine** intact; it is not zero surface radiance. Stars,
glints and Milky Way are masked independently through twilight fade. Failed/pending texture decode remains
unavailable and cannot qualify the calendar-disc pixels.

### Crepuscular rays — *production*
- **Family:** geometric shadowing / Mie shafts through broken-deck gaps.
- **Gate:** `broken=clamp(1−|clMid−0.45|/0.42)`; `ray = min(0.5, clamp(e/8)·broken·(1−0.8·clLow)·clamp(0.3+0.7·
  humid)·directional·(fog?0.25:1))` — needs a **low sun + broken cloud + participating haze**; 0 in clear-dry and
  0 in solid overcast.
- **Shape:** soft radial shafts from the visible sun, fading from source.  **NOT:** a hard conic sticker; a single
  diagonal slash; a lens flare.  **Verdict:** keep.

### Anticrepuscular rays — *production + `&debugOptic=anticrep`*
- **Family:** the far end of the same shafts, converging by perspective at the antisolar point.
- **Gate:** `antiCrep = ray·0.5` (inherits every crepuscular gate; strictly fainter), at `--antix=100−sm.x`.
- **NOT:** brighter than crepuscular; centred on the sun; aurora/false-dawn-like.  **Verdict:** keep.

### 22° sun halo — *production + `&debugOptic=halo`*
- **Family:** ice-crystal refraction (cirrus).
- **Gate:** `cirrus=clamp((clHigh−.06)/.34)·clamp((.72−clHigh)/.42)·(1−clLow)·(1−0.55·clMid)`; `sunHalo=cirrus·
  sunUpO`.
- **Shape:** a discrete ring at the visible sun, **dark inner gap**, red-inner→blue-outer.  **NOT:** a filled
  glow; a saturated rainbow; a centred no-gap bloom.  **Off:** no cirrus, thick low/mid cloud, sun down.
  **Verdict:** keep (registered to visible sun).

### 22° moon halo — *production*
- **Family:** ice-crystal refraction around a bright moon.
- **Gate:** `lunarHalo = clamp((clHigh−.06)/.34)·clamp((.66−clHigh)/.42)·(1−clLow)·(1−0.7·clMid)·moonLume`.
- **NOT:** an aureole hugging the disc (that is the droplet corona); by day / new moon / thick cloud.  **Verdict:**
  keep. **`&debugOptic=lunarhalo`** forces the moon halo only with shared physical lunar eligibility (the sun
  `halo` key is unchanged). DESIGN supplies an eligible night positive and near-new negative.
  *Geometric limit (accepted by design):* the moon sits in the top-right pocket ~56 px from the top/right card edges,
  so a true-to-scale ring (r≈135 px) necessarily extends past them; the card's `overflow:hidden` clips it to a clean
  **partial arc**. A radius small enough to fit fully (≤~56 px) would collapse into a corona/aureole and break the
  "distinct 22° ring" contract, so the partial arc is kept — it reads as a coherent halo curving around the moon.

### Parhelia / sundogs (+ parhelic band) — *production + `&debugOptic=sundogs`*
- **Family:** plate-ice refraction; two spots flanking the sun at the **same elevation**, a low-sun phenomenon.
- **Gate:** `sunDogs = cirrus·sunUpO·clamp((12−e)/12)`.
- **NOT:** vertical; a full ring; saturated blobs; present at high sun.  **Verdict:** keep.

### Paraselenae / moondogs — *production + `&debugOptic=paraselene`*
- **Gate:** `moonParhelia = cirrus·moonLume·clamp((14−moonSky.alt)/16)` — rare; bright moon + cirrus + low moon.
- **Force:** `&debugOptic=paraselene` retains shared physical lunar eligibility; it grants no near-new/day light.
- **NOT:** vertical; a ring; rainbow.  **Verdict:** keep.

### Sun pillar — *production + `&debugOptic=pillar`*
- **Family:** reflection off oriented plate/column ice crystals (cirrus or cold diamond-dust).
- **Gate:** `D.cold · clamp((6−e)/8) · clamp((e+5)/7) · (0.45+0.55·cirrus)` — cold air (ice-crystal proxy) + a low
  sun; the 0.45 floor admits a diamond-dust pillar without cirrus (physically real in very cold air).
- **Shape:** a narrow **vertical** column through the low sun.  **NOT:** a diagonal beam; a crepuscular ray; false
  dawn.  **Verdict:** keep (cold-gated; defensible).

### Atmospheric refraction / low-sun flattening — *production*
- **Gate:** `--sunflat = 1 − 0.20·clamp((4−e)/8)·clamp((e+3)/4)` — only near the horizon, strongest at sunrise/set.
- **NOT:** applied at high sun; over-ovalised.  **Verdict:** keep.

### Aurora — *production (gated, simulated)*
- **Gate:** `|lat|≳55° · deep-dark · low cloud · (1−moon) · (1−LPOLL)` — a *simulated* presence (no Kp data), so
  it never shows at low latitude.  **NOT:** at low latitude; in bright twilight.  **Verdict:** keep (honestly
  labelled a simulation).

---

## Sun white-balance / tone-mapping (the corner-sun body)
Scene-referred radiance → attenuate → tone-map (not display-colour × a weather mute). Kasten–Young airmass +
Beer–Lambert + per-class cloud transmittance + CCT(elevation) blackbody → ACES. The nucleus clips to a defined
white body even through cloud; cloud desaturates toward **warm-white, never grey/purple**.  **Verdict:** keep.
*Honest limit:* headroom/constants are tuned for a pleasing clipped nucleus, not radiometric; baked per
gradient-stop in JS because CSS can't composite in linear light. Tone-map derivation lives in `atmosphere`;
`paint` writes its returned colour/transmittance outputs.

## Validation smoke matrix (screenshots / `qaState` / `tests/smoke.html`)
clear day (defined sun nucleus) · sunrise (low-left warm) · sunset (warm sky) · clear night (stars + twinkle) ·
bright-moon night (local star wash, opaque disc) · cloudy night (moonlit rim) · overcast (warm-white sun, **no
grey/purple blob**; **no Belt of Venus**) · fog/haze (desaturate, no fake cones) · rain & thunder (only with
marked preview/qualified synthetic evidence) · snow preview · dawn/twilight (**no painted band/cone**; bright moon → no false-dawn) ·
low-sun + cirrus (halo/sundogs ringing the **visible** sun) · debug-forced optics (`&debugOptic=…`, six names above).
Flag activation alone does not prove visible motion or correct optical pixels; use recorded physical
scene inputs for effects without a dedicated switch and a real-time 15–60 second watch for motion.
Add first neutral/reveal, pending/failed PBR, twilight star/glint/Milky Way interior/edge/exterior and daytime
no-hole controls; cloud signed target/day/wind/empty/seek/gap controls; default Liquid glass and optional High
contrast with actual fonts. These are native validation requirements, not results awarded by source checks.

## Truthfulness non-negotiables
Eligible Open-Meteo current remains a useful **model estimate** (≈); absent/expired current is unknown and
withdraws its weather inputs. Neither model amount/WMO code nor RainViewer palette/alpha establishes local
wet/dry/lightning, nearby precipitation or arrival. Selected live adapters therefore keep strong effects off;
unknown is not observed dry. Current amount is preceding-interval and forecast amount preceding-hour/stepped,
not instantaneous intensity/onset/ETA/probability. Marked previews and separately admitted synthetic wet/dry/
end/outage/expiry/target-generation controls remain useful QA; they do not establish live provider skill.
`qaState().wxTruth` exposes these distinct authorities and actual permissions. No random optics, decorative
diagonal slashes or physics claim without a gate.
