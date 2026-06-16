#!/usr/bin/env bash
# Salah Widget Installer for Linux/macOS
# Safe wizard: detects browsers/profiles, refuses legacy Tabliss profiles, downloads TablissNG release assets,
# and stages the Salah Widget preset for manual import into TablissNG.
#
# Usage:
#   bash install.sh
#   SALAH_WIDGET_PRESET_URL="https://raw.githubusercontent.com/YOU/REPO/main/presets/salah-widget.tablissng.json" bash install.sh
#
# Environment overrides:
#   SALAH_WIDGET_PRESET_URL  Raw URL to your TablissNG preset JSON
#   SALAH_INSTALL_SOURCE     github | store | ask
#   TABLISSNG_REPO           owner/repo for upstream TablissNG, default BookCatKid/TablissNG

set -Eeuo pipefail

TABLISSNG_REPO="${TABLISSNG_REPO:-BookCatKid/TablissNG}"
SALAH_INSTALL_SOURCE="${SALAH_INSTALL_SOURCE:-github}"
SALAH_WIDGET_PRESET_URL="${SALAH_WIDGET_PRESET_URL:-https://raw.githubusercontent.com/theislampill/salah_widget/main/presets/salah-widget.tablissng.json}"
NO_OPEN="${NO_OPEN:-0}"
DRY_RUN="${DRY_RUN:-0}"

CHROME_TABLISSNG_ID="dlaogejjiafeobgofajdlkkhjlignalk"
EDGE_TABLISSNG_ID="mkaphhbkcccpgkfaifhhdfckagnkcmhm"
CHROME_LEGACY_TABLISS_ID="hipekcciheckooncpjeljhnekcoolahp"
EDGE_LEGACY_TABLISS_ID="lklaendlmlfkaabeleddanafeinnenih"

CHROME_STORE_URL="https://chromewebstore.google.com/detail/tablissng/${CHROME_TABLISSNG_ID}"
FIREFOX_STORE_URL="https://addons.mozilla.org/en-US/firefox/addon/tablissng/"
EDGE_STORE_URL="https://microsoftedge.microsoft.com/addons/detail/tablissng/${EDGE_TABLISSNG_ID}"

WORK_ROOT="${TMPDIR:-/tmp}/salah-widget-installer"
DOWNLOAD_ROOT="${WORK_ROOT}/downloads"
PRESET_ROOT="${WORK_ROOT}/presets"
mkdir -p "$DOWNLOAD_ROOT" "$PRESET_ROOT"

say_section() { printf '\n== %s ==\n' "$1"; }
ok() { printf '[OK] %s\n' "$1"; }
warn() { printf '[WARN] %s\n' "$1" >&2; }
err() { printf '[ERROR] %s\n' "$1" >&2; }

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    err "Required command not found: $1"
    exit 1
  }
}

need_cmd curl

OS="$(uname -s)"
case "$OS" in
  Darwin) PLATFORM="mac" ;;
  Linux) PLATFORM="linux" ;;
  *) err "Unsupported OS for install.sh: $OS"; exit 1 ;;
esac

find_exe() {
  local candidates="$1"
  local IFS=';'
  for c in $candidates; do
    [ -n "$c" ] || continue
    if command -v "$c" >/dev/null 2>&1; then command -v "$c"; return 0; fi
    if [ -x "$c" ]; then printf '%s\n' "$c"; return 0; fi
  done
  return 1
}

open_url() {
  local exe="$1"
  local url="$2"
  if [ "$NO_OPEN" = "1" ]; then
    printf 'Open manually: %s\n' "$url"
    return 0
  fi
  if [ "$DRY_RUN" = "1" ]; then
    printf '[dry-run] Would open: %s\n' "$url"
    return 0
  fi

  if [ -n "$exe" ] && [ -x "$exe" ]; then
    "$exe" "$url" >/dev/null 2>&1 &
    return 0
  fi

  if [ "$PLATFORM" = "mac" ]; then
    open "$url" >/dev/null 2>&1 || printf 'Open manually: %s\n' "$url"
  else
    xdg-open "$url" >/dev/null 2>&1 || printf 'Open manually: %s\n' "$url"
  fi
}

copy_text() {
  local text="$1"
  if [ "$PLATFORM" = "mac" ] && command -v pbcopy >/dev/null 2>&1; then
    printf '%s' "$text" | pbcopy && return 0
  fi
  if command -v wl-copy >/dev/null 2>&1; then
    printf '%s' "$text" | wl-copy && return 0
  fi
  if command -v xclip >/dev/null 2>&1; then
    printf '%s' "$text" | xclip -selection clipboard && return 0
  fi
  if command -v xsel >/dev/null 2>&1; then
    printf '%s' "$text" | xsel --clipboard --input && return 0
  fi
  return 1
}

sanitize() {
  printf '%s' "$1" | sed 's/[^A-Za-z0-9._-]/_/g'
}

has_id_dir() {
  local profile="$1"
  local ids_csv="$2"
  local IFS=','
  for id in $ids_csv; do
    [ -n "$id" ] || continue
    if [ -d "$profile/Extensions/$id" ]; then
      return 0
    fi
  done
  return 1
}

chromium_profiles() {
  local user_data="$1"
  [ -d "$user_data" ] || return 0
  find "$user_data" -maxdepth 1 -type d \( -name "Default" -o -name "Profile *" \) 2>/dev/null | sort
}

firefox_profiles() {
  local profiles_root="$1"
  [ -d "$profiles_root" ] || return 0
  find "$profiles_root" -maxdepth 1 -type d 2>/dev/null | sort
}

firefox_status() {
  local profile="$1"
  local file="$profile/extensions.json"
  if [ ! -f "$file" ]; then
    printf '0|0|'
    return 0
  fi

  if command -v python3 >/dev/null 2>&1; then
    python3 - "$file" <<'PY'
import json, re, sys
path = sys.argv[1]
has_new = False
has_old = False
matches = []
try:
    data = json.load(open(path, encoding="utf-8"))
except Exception:
    print("0|0|")
    raise SystemExit
for addon in data.get("addons", []):
    parts = []
    for key in ("id", "name"):
        if addon.get(key):
            parts.append(str(addon.get(key)))
    loc = addon.get("defaultLocale") or {}
    if loc.get("name"):
        parts.append(str(loc.get("name")))
    hay = " ".join(parts)
    if re.search(r"\bTablissNG\b|tablissng", hay, re.I):
        has_new = True
        matches.append(hay)
    elif re.search(r"\bTabliss\b", hay, re.I) and not re.search(r"NG|tablissng", hay, re.I):
        has_old = True
        matches.append(hay)
print(("1" if has_new else "0") + "|" + ("1" if has_old else "0") + "|" + "; ".join(matches))
PY
  else
    # Coarse fallback if python3 is unavailable.
    if grep -qi 'TablissNG\|tablissng' "$file"; then
      printf '1|0|TablissNG'
    elif grep -qi 'Tabliss' "$file"; then
      printf '0|1|Tabliss'
    else
      printf '0|0|'
    fi
  fi
}

declare -a CONFIGS=()
if [ "$PLATFORM" = "mac" ]; then
  CONFIGS+=("chrome|Google Chrome|chromium|$HOME/Library/Application Support/Google/Chrome|/Applications/Google Chrome.app/Contents/MacOS/Google Chrome;google-chrome;chrome|$CHROME_TABLISSNG_ID|$CHROME_LEGACY_TABLISS_ID|$CHROME_STORE_URL|chrome://extensions/|chrome://newtab/")
  CONFIGS+=("edge|Microsoft Edge|chromium|$HOME/Library/Application Support/Microsoft Edge|/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge;microsoft-edge|$EDGE_TABLISSNG_ID,$CHROME_TABLISSNG_ID|$EDGE_LEGACY_TABLISS_ID,$CHROME_LEGACY_TABLISS_ID|$EDGE_STORE_URL|edge://extensions/|edge://newtab/")
  CONFIGS+=("brave|Brave|chromium|$HOME/Library/Application Support/BraveSoftware/Brave-Browser|/Applications/Brave Browser.app/Contents/MacOS/Brave Browser;brave-browser|$CHROME_TABLISSNG_ID|$CHROME_LEGACY_TABLISS_ID|$CHROME_STORE_URL|brave://extensions/|brave://newtab/")
  CONFIGS+=("chromium|Chromium|chromium|$HOME/Library/Application Support/Chromium|/Applications/Chromium.app/Contents/MacOS/Chromium;chromium|$CHROME_TABLISSNG_ID|$CHROME_LEGACY_TABLISS_ID|$CHROME_STORE_URL|chrome://extensions/|chrome://newtab/")
  CONFIGS+=("firefox|Firefox|firefox|$HOME/Library/Application Support/Firefox/Profiles|/Applications/Firefox.app/Contents/MacOS/firefox;firefox|| |$FIREFOX_STORE_URL|about:addons|about:newtab")
  CONFIGS+=("librewolf|LibreWolf|firefox|$HOME/Library/Application Support/LibreWolf/Profiles|/Applications/LibreWolf.app/Contents/MacOS/librewolf;librewolf|| |$FIREFOX_STORE_URL|about:addons|about:newtab")
else
  CONFIGS+=("chrome|Google Chrome|chromium|$HOME/.config/google-chrome|google-chrome;google-chrome-stable;chrome|$CHROME_TABLISSNG_ID|$CHROME_LEGACY_TABLISS_ID|$CHROME_STORE_URL|chrome://extensions/|chrome://newtab/")
  CONFIGS+=("edge|Microsoft Edge|chromium|$HOME/.config/microsoft-edge|microsoft-edge;microsoft-edge-stable|$EDGE_TABLISSNG_ID,$CHROME_TABLISSNG_ID|$EDGE_LEGACY_TABLISS_ID,$CHROME_LEGACY_TABLISS_ID|$EDGE_STORE_URL|edge://extensions/|edge://newtab/")
  CONFIGS+=("brave|Brave|chromium|$HOME/.config/BraveSoftware/Brave-Browser|brave-browser;brave|$CHROME_TABLISSNG_ID|$CHROME_LEGACY_TABLISS_ID|$CHROME_STORE_URL|brave://extensions/|brave://newtab/")
  CONFIGS+=("chromium|Chromium|chromium|$HOME/.config/chromium|chromium;chromium-browser|$CHROME_TABLISSNG_ID|$CHROME_LEGACY_TABLISS_ID|$CHROME_STORE_URL|chrome://extensions/|chrome://newtab/")
  CONFIGS+=("firefox|Firefox|firefox|$HOME/.mozilla/firefox|firefox|| |$FIREFOX_STORE_URL|about:addons|about:newtab")
  CONFIGS+=("librewolf|LibreWolf|firefox|$HOME/.librewolf|librewolf|| |$FIREFOX_STORE_URL|about:addons|about:newtab")
fi

declare -a TARGETS=()

add_target() {
  local key="$1" label="$2" family="$3" profile_name="$4" profile_path="$5" exe="$6" has_new="$7" has_old="$8" matches="$9" store="${10}" manager="${11}" newtab="${12}"
  local idx=$(( ${#TARGETS[@]} + 1 ))
  TARGETS+=("$idx|$key|$label|$family|$profile_name|$profile_path|$exe|$has_new|$has_old|$matches|$store|$manager|$newtab")
}

detect_targets() {
  local cfg key label family user_data exes newids oldids store manager newtab exe profiles status has_new has_old matches p pname
  for cfg in "${CONFIGS[@]}"; do
    IFS='|' read -r key label family user_data exes newids oldids store manager newtab <<< "$cfg"
    exe="$(find_exe "$exes" || true)"

    if [ "$family" = "chromium" ]; then
      mapfile -t profiles < <(chromium_profiles "$user_data")
      if [ "${#profiles[@]}" -eq 0 ] && { [ -n "$exe" ] || [ -d "$user_data" ]; }; then
        add_target "$key" "$label" "$family" "(no profile detected)" "" "$exe" "0" "0" "" "$store" "$manager" "$newtab"
      fi
      for p in "${profiles[@]}"; do
        pname="$(basename "$p")"
        has_new=0; has_old=0; matches=""
        if has_id_dir "$p" "$newids"; then has_new=1; matches="${matches}TablissNG-id; "; fi
        if has_id_dir "$p" "$oldids"; then has_old=1; matches="${matches}legacy-Tabliss-id; "; fi
        add_target "$key" "$label" "$family" "$pname" "$p" "$exe" "$has_new" "$has_old" "$matches" "$store" "$manager" "$newtab"
      done
    else
      mapfile -t profiles < <(firefox_profiles "$user_data")
      if [ "${#profiles[@]}" -eq 0 ] && { [ -n "$exe" ] || [ -d "$user_data" ]; }; then
        add_target "$key" "$label" "$family" "(no profile detected)" "" "$exe" "0" "0" "" "$store" "$manager" "$newtab"
      fi
      for p in "${profiles[@]}"; do
        pname="$(basename "$p")"
        status="$(firefox_status "$p")"
        IFS='|' read -r has_new has_old matches <<< "$status"
        add_target "$key" "$label" "$family" "$pname" "$p" "$exe" "$has_new" "$has_old" "$matches" "$store" "$manager" "$newtab"
      done
    fi
  done
}

select_asset() {
  local family="$1"
  need_cmd python3
  python3 - "$TABLISSNG_REPO" "$family" <<'PY'
import json, re, sys, urllib.request
repo, family = sys.argv[1], sys.argv[2]
url = f"https://api.github.com/repos/{repo}/releases/latest"
req = urllib.request.Request(url, headers={
    "Accept": "application/vnd.github+json",
    "User-Agent": "salah-widget-installer",
})
with urllib.request.urlopen(req, timeout=30) as r:
    data = json.load(r)
assets = data.get("assets") or []
def pick(cands):
    for a in cands:
        if a:
            print(data.get("tag_name","latest") + "\t" + a.get("name","asset") + "\t" + a.get("browser_download_url",""))
            return
    raise SystemExit(f"No safe {family} asset found in latest release {data.get('tag_name')}")
if family == "firefox":
    c1 = [a for a in assets if re.search(r"\.xpi$", a.get("name",""), re.I) and re.search(r"signed|firefox", a.get("name",""), re.I) and not re.search(r"unsigned|source", a.get("name",""), re.I)]
    c2 = [a for a in assets if re.search(r"\.xpi$", a.get("name",""), re.I) and not re.search(r"unsigned|source", a.get("name",""), re.I)]
    c3 = [a for a in assets if re.search(r"firefox.*\.zip$", a.get("name",""), re.I) and not re.search(r"unsigned|source", a.get("name",""), re.I)]
    pick(c1 + c2 + c3)
elif family == "chromium":
    c1 = [a for a in assets if re.search(r"chrom(e|ium).*\.zip$", a.get("name",""), re.I) and not re.search(r"firefox|safari|source", a.get("name",""), re.I)]
    c2 = [a for a in assets if re.search(r"tabliss.*\.zip$", a.get("name",""), re.I) and not re.search(r"firefox|safari|source", a.get("name",""), re.I)]
    pick(c1 + c2)
else:
    raise SystemExit(f"Unsupported family: {family}")
PY
}

download_tablissng_asset() {
  local family="$1"
  local line tag name url tag_s name_s dest
  line="$(select_asset "$family")"
  IFS=$'\t' read -r tag name url <<< "$line"
  tag_s="$(sanitize "$tag")"
  name_s="$(sanitize "$name")"
  mkdir -p "$DOWNLOAD_ROOT/$tag_s"
  dest="$DOWNLOAD_ROOT/$tag_s/$name_s"
  if [ -f "$dest" ]; then
    ok "Already downloaded $name"
    printf '%s\n' "$dest"
    return 0
  fi
  printf 'Downloading %s\n  %s\n' "$name" "$url" >&2
  if [ "$DRY_RUN" = "1" ]; then
    printf '[dry-run] Would download to %s\n' "$dest" >&2
    printf '%s\n' "$dest"
    return 0
  fi
  curl -fL "$url" -o "$dest"
  printf '%s\n' "$dest"
}

expand_chromium_asset() {
  local zip_path="$1"
  need_cmd unzip
  local leaf extract manifest
  leaf="$(basename "$zip_path" .zip)"
  extract="$(dirname "$zip_path")/${leaf}-unpacked"
  rm -rf "$extract"
  mkdir -p "$extract"
  unzip -q "$zip_path" -d "$extract"
  manifest="$(find "$extract" -name manifest.json -not -path '*/__MACOSX/*' | sort | head -n 1 || true)"
  if [ -z "$manifest" ]; then
    err "Downloaded Chromium asset did not contain manifest.json: $zip_path"
    return 1
  fi
  dirname "$manifest"
}

download_preset() {
  local dest="$PRESET_ROOT/salah-widget.tablissng.json"
  if [ -z "$SALAH_WIDGET_PRESET_URL" ]; then
    warn "No preset URL configured. Set SALAH_WIDGET_PRESET_URL."
    return 1
  fi
  printf 'Downloading Salah Widget preset:\n  %s\n' "$SALAH_WIDGET_PRESET_URL" >&2
  if [ "$DRY_RUN" = "1" ]; then
    printf '[dry-run] Would download to %s\n' "$dest" >&2
    printf '%s\n' "$dest"
    return 0
  fi
  if ! curl -fL "$SALAH_WIDGET_PRESET_URL" -o "$dest"; then
    warn "Could not download preset. Configure SALAH_WIDGET_PRESET_URL after publishing the preset JSON."
    return 1
  fi
  if command -v python3 >/dev/null 2>&1; then
    if python3 -m json.tool "$dest" >/dev/null 2>&1; then
      ok "Preset JSON is parseable: $dest" >&2
    else
      warn "Downloaded preset is not parseable JSON. Check it before publishing."
    fi
  fi
  printf '%s\n' "$dest"
}

install_tablissng() {
  local family="$1" label="$2" exe="$3" store="$4" manager="$5"
  local source="$SALAH_INSTALL_SOURCE"
  if [ "$source" = "ask" ]; then
    printf '\nInstall source for %s:\n  1) GitHub latest release/manual install\n  2) Official browser store page\n' "$label"
    read -r -p "Choose [1/2] (default 1): " source_choice
    [ "$source_choice" = "2" ] && source="store" || source="github"
  fi

  if [ "$source" = "store" ]; then
    say_section "Open official store page for $label"
    printf '%s\n' "$store"
    open_url "$exe" "$store"
    read -r -p "Press Enter after TablissNG is installed: " _
    return 0
  fi

  say_section "Download TablissNG from GitHub latest release for $label"
  local asset path
  if ! path="$(download_tablissng_asset "$family")"; then
    warn "GitHub release download failed; falling back to store page."
    open_url "$exe" "$store"
    read -r -p "Press Enter after TablissNG is installed: " _
    return 0
  fi

  if [ "$family" = "chromium" ]; then
    local unpacked
    unpacked="$(expand_chromium_asset "$path")"
    printf '\nChromium-family install steps:\n'
    printf '  1. Open Extensions.\n'
    printf '  2. Enable Developer mode.\n'
    printf '  3. Click Load unpacked.\n'
    printf '  4. Select this folder:\n     %s\n' "$unpacked"
    copy_text "$unpacked" && ok "Copied unpacked extension folder path to clipboard."
    open_url "$exe" "$manager"
  else
    printf '\nFirefox-family install steps:\n'
    printf '  1. Open Add-ons Manager.\n'
    printf '  2. Click the gear icon.\n'
    printf '  3. Click Install Add-on From File.\n'
    printf '  4. Select this file:\n     %s\n' "$path"
    copy_text "$path" && ok "Copied XPI path to clipboard."
    open_url "$exe" "$manager"
  fi
  read -r -p "Press Enter after TablissNG is installed: " _
}

show_import_instructions() {
  local label="$1" profile_name="$2" exe="$3" newtab="$4" preset="$5"
  say_section "Import Salah Widget preset for $label / $profile_name"
  if [ -n "$preset" ] && [ -f "$preset" ]; then
    printf 'Preset file:\n  %s\n' "$preset"
    copy_text "$preset" && ok "Copied the preset file path to clipboard."
  else
    warn "Preset file is not available yet."
  fi
  cat <<'TEXT'

Manual import path:
  1. Open a new tab controlled by TablissNG.
  2. Open TablissNG settings.
  3. Use Import/Restore settings.
  4. Select the preset JSON file above.

This wizard does not directly write into browser extension storage.
That avoids corrupting profiles and avoids touching legacy Tabliss.
TEXT
  open_url "$exe" "$newtab"
}

printf '\nSalah Widget Installer\n\n'
cat <<'TEXT'
This wizard can:
- detect supported browsers/profiles
- check for TablissNG
- safely refuse to modify legacy Tabliss profiles
- download the right TablissNG build from GitHub latest release when needed
- guide the browser-required install step
- stage the Salah Widget preset for import

It will not silently force-install extensions or write directly into extension storage.
TEXT

say_section "Detecting browsers"
detect_targets

if [ "${#TARGETS[@]}" -eq 0 ]; then
  err "No supported browser profiles or installs were detected."
  exit 1
fi

for t in "${TARGETS[@]}"; do
  IFS='|' read -r idx key label family profile_name profile_path exe has_new has_old matches store manager newtab <<< "$t"
  if [ "$has_old" = "1" ]; then
    status="legacy Tabliss detected: SKIP"
  elif [ "$has_new" = "1" ]; then
    status="TablissNG detected"
  else
    status="TablissNG not detected"
  fi
  printf '[%s] %s / %s — %s\n' "$idx" "$label" "$profile_name" "$status"
done

printf '\n'
read -r -p "Select target numbers separated by commas, or 'all' (default all): " selection
selection="${selection:-all}"

selected_csv=","
if [ "$selection" != "all" ]; then
  selected_csv=",${selection//[[:space:]]/},"
fi

preset_file=""

for t in "${TARGETS[@]}"; do
  IFS='|' read -r idx key label family profile_name profile_path exe has_new has_old matches store manager newtab <<< "$t"
  if [ "$selection" != "all" ] && [[ "$selected_csv" != *",$idx,"* ]]; then
    continue
  fi

  say_section "$label / $profile_name"

  if [ "$has_old" = "1" ]; then
    warn "Legacy Tabliss detected in this profile. Refusing to touch this browser/profile."
    [ -n "$matches" ] && printf 'Matches: %s\n' "$matches"
    continue
  fi

  if [ "$has_new" != "1" ]; then
    install_tablissng "$family" "$label" "$exe" "$store" "$manager"
  else
    ok "TablissNG already appears to be installed."
  fi

  if [ -z "$preset_file" ]; then
    preset_file="$(download_preset || true)"
  fi
  show_import_instructions "$label" "$profile_name" "$exe" "$newtab" "$preset_file"
done

say_section "Done"
printf 'Downloads and presets were staged in:\n  %s\n\n' "$WORK_ROOT"
printf 'Review this script before publishing it. The preset URL should point at your real raw JSON file.\n'
