#!/usr/bin/env bash
# Salah Widget Installer for Linux/macOS
# Safe wizard: detects browsers/profiles, refuses legacy Tabliss profiles, downloads TablissNG release assets,
# and stages the Salah Widget preset for manual import into TablissNG.
#
# Usage:
#   bash install.sh
#   DRY_RUN=1 bash install.sh  # offline local discovery; no terminal, network or writes
#   SALAH_WIDGET_PRESET_URL="https://raw.githubusercontent.com/YOU/REPO/main/presets/salah-widget.tablissng.json" bash install.sh
#
# Environment overrides:
#   SALAH_WIDGET_HASH        Optional URL-hash config (lat=..&lon=..&method=..) baked into the widget iframe
#   SALAH_WIDGET_PRESET_URL  Raw URL to your TablissNG preset JSON
#   SALAH_INSTALL_SOURCE     github | store | ask
#   TABLISSNG_REPO           owner/repo for upstream TablissNG, default BookCatKid/TablissNG

set -Eeuo pipefail

TABLISSNG_REPO="${TABLISSNG_REPO:-BookCatKid/TablissNG}"
SALAH_INSTALL_SOURCE="${SALAH_INSTALL_SOURCE:-github}"
SALAH_WIDGET_PRESET_URL="${SALAH_WIDGET_PRESET_URL-https://raw.githubusercontent.com/theislampill/salah_widget/main/presets/salah-widget.tablissng.json}"
SALAH_WIDGET_HASH="${SALAH_WIDGET_HASH:-}"   # optional: the builder's config hash (e.g. lat=..&lon=..&method=..) baked into the preset's iframe so the user's settings carry through
NO_OPEN="${NO_OPEN:-0}"
DRY_RUN="${DRY_RUN:-0}"

CHROME_TABLISSNG_ID="dlaogejjiafeobgofajdlkkhjlignalk"
EDGE_TABLISSNG_ID="mkaphhbkcccpgkfaifhhdfckagnkcmhm"
CHROME_LEGACY_TABLISS_ID="hipekcciheckooncpjeljhnekcoolahp"
EDGE_LEGACY_TABLISS_ID="lklaendlmlfkaabeleddanafeinnenih"

CHROME_STORE_URL="https://chromewebstore.google.com/detail/tablissng/${CHROME_TABLISSNG_ID}"
FIREFOX_STORE_URL="https://addons.mozilla.org/en-US/firefox/addon/tablissng/"
EDGE_STORE_URL="https://microsoftedge.microsoft.com/addons/detail/tablissng/${EDGE_TABLISSNG_ID}"

# Roots are admitted once per attempt, after preview and human-selection gates.
# Scratch is transient; the manual-install bundle is deliberately retained.
WORK_ROOT=""; WORK_ID=""; DOWNLOAD_ROOT=""
BUNDLE_ROOT=""; BUNDLE_ID=""; PRESET_ROOT=""; TERMINAL_OPEN=0

say_section() { printf '\n== %s ==\n' "$1"; }
ok() { printf '[OK] %s\n' "$1" >&2; }
warn() { printf '[WARN] %s\n' "$1" >&2; }
err() { printf '[ERROR] %s\n' "$1" >&2; }

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    err "Required command not found: $1"
    exit 1
  }
}

OS="$(uname -s)"
case "$OS" in
  Darwin) PLATFORM="mac" ;;
  Linux) PLATFORM="linux" ;;
  *) err "Unsupported OS for install.sh: $OS"; exit 1 ;;
esac

case "$DRY_RUN:$NO_OPEN" in 0:0|0:1|1:0|1:1) ;; *) err "DRY_RUN and NO_OPEN must be 0 or 1."; exit 1 ;; esac
case "$SALAH_INSTALL_SOURCE" in github|store|ask) ;; *) err "SALAH_INSTALL_SOURCE must be github, store or ask."; exit 1 ;; esac
[ "$#" -eq 0 ] || { err "Unsupported arguments; use the documented environment overrides."; exit 1; }

acquire_terminal() {
  if ! { exec 3</dev/tty; } 2>/dev/null; then
    err "A readable controlling terminal is required. Run interactively, or use DRY_RUN=1 for an offline preview."
    return 1
  fi
  TERMINAL_OPEN=1
}

read_answer() {
  local answer_variable="$1" answer_prompt="$2"
  printf '%s' "$answer_prompt" >&2
  if ! read -r -u 3 "$answer_variable"; then
    err "Terminal input ended; manual actions remain pending."
    return 1
  fi
}

# Native stat forms are intentionally explicit; unknown ownership fails closed.
path_identity() {
  if [ "$PLATFORM" = "mac" ]; then stat -f '%d:%i:%u:%Lp' "$1"
  else stat -c '%d:%i:%u:%a' -- "$1"; fi
}

trusted_parent() {
  local path="$1" kind="$2" current=/ rest part fields dev inode owner mode uid
  case "$path" in /*) ;; *) err "Staging parent must be an absolute path: $path"; return 1 ;; esac
  case "$path" in *$'\n'*|*$'\r'*) err "Staging parent contains an unsupported newline."; return 1 ;; esac
  while [ "$path" != / ] && [[ "$path" = */ ]]; do path="${path%/}"; done
  uid="$(id -u)" || return 1
  rest="${path#/}"
  # Inspect every supplied component, including ancestors that could rename it.
  while :; do
    [ -d "$current" ] && [ ! -L "$current" ] || { err "Untrusted staging ancestor: $current"; return 1; }
    fields="$(path_identity "$current")" || return 1
    IFS=: read -r dev inode owner mode <<< "$fields"
    case "$mode" in ''|*[!0-7]*) err "Cannot establish permissions: $current"; return 1 ;; esac
    [ "$owner" = 0 ] || [ "$owner" = "$uid" ] || { err "Untrusted ancestor owner: $current"; return 1; }
    if (( (8#$mode & 0022) != 0 )); then
      [ "$owner" = 0 ] && (( (8#$mode & 01000) != 0 )) || { err "Writable staging ancestor: $current"; return 1; }
    fi
    [ -n "$rest" ] || break
    part="${rest%%/*}"
    case "$part" in ''|.|..) err "Noncanonical staging parent: $path"; return 1 ;; esac
    if [ "$current" = / ]; then current="/$part"; else current="$current/$part"; fi
    if [[ "$rest" = */* ]]; then rest="${rest#*/}"; else rest=""; fi
  done
  if [ "$kind" = home ] || [ "$owner" != 0 ] || (( (8#$mode & 01000) == 0 )); then
    [ "$owner" = "$uid" ] && [ -O "$path" ] && (( (8#$mode & 0022) == 0 )) || {
      err "Use a private, owned staging parent (or root-owned sticky /tmp for scratch): $path"; return 1;
    }
  fi
  [ "$(cd "$path" && pwd -P)" = "$path" ] || { err "Staging parent must resolve physically to itself: $path"; return 1; }
  printf '%s\n' "$path"
}

verify_root() {
  local root="$1" identity="$2" fields dev inode owner mode
  [ -n "$root" ] && [ "$root" != / ] && [ -n "$identity" ] && [ -d "$root" ] && [ ! -L "$root" ] && [ -O "$root" ] || {
    err "Private staging root is unavailable or changed: $root"; return 1;
  }
  [ "$(cd "$root" && pwd -P)" = "$root" ] || return 1
  fields="$(path_identity "$root")" || return 1
  IFS=: read -r dev inode owner mode <<< "$fields"
  [ "$fields" = "$identity" ] && [ "$owner" = "$(id -u)" ] && [ "$mode" = 700 ] || {
    err "Private staging ownership/mode/identity changed: $root"; return 1;
  }
}

guard_owned_path() {
  local root="$1" identity="$2" path="$3" kind="$4" rest current part
  verify_root "$root" "$identity" || return 1
  case "$path" in "$root"/*) rest="${path#"$root"/}" ;; *) err "Path escapes private root: $path"; return 1 ;; esac
  current="$root"
  while :; do
    part="${rest%%/*}"
    case "$part" in ''|.|..) err "Invalid staged path component: $path"; return 1 ;; esac
    current="$current/$part"
    [ ! -L "$current" ] || { err "Symlink in staged path: $current"; return 1; }
    if [[ "$rest" = */* ]]; then
      [ -d "$current" ] || { err "Missing staged parent: $current"; return 1; }
      rest="${rest#*/}"
    else
      if [ -e "$current" ]; then
        if [ "$kind" = dir ]; then [ -d "$current" ] || return 1
        else [ -f "$current" ] || return 1; fi
      fi
      break
    fi
  done
  [ "$(cd "$(dirname "$path")" && pwd -P)" = "$(dirname "$path")" ] || return 1
}

initialize_staging() {
  [ "$DRY_RUN" = 0 ] || { err "Offline preview does not create staging."; return 1; }
  [ -z "$WORK_ROOT" ] || { verify_root "$WORK_ROOT" "$WORK_ID" && verify_root "$BUNDLE_ROOT" "$BUNDLE_ID"; return; }
  local temp_parent home_parent created
  need_cmd curl; need_cmd python3; need_cmd stat; need_cmd id; need_cmd mktemp
  temp_parent="$(trusted_parent "${TMPDIR:-/tmp}" temp)" || return 1
  home_parent="$(trusted_parent "$HOME" home)" || return 1
  created="$(umask 077; mktemp -d "$temp_parent/salah-widget-download.XXXXXXXX")" || return 1
  WORK_ROOT="$created"; WORK_ID="$(path_identity "$created")" || return 1
  verify_root "$WORK_ROOT" "$WORK_ID" || return 1
  created="$(umask 077; mktemp -d "$home_parent/salah-widget-install.XXXXXXXX")" || return 1
  BUNDLE_ROOT="$created"; BUNDLE_ID="$(path_identity "$created")" || return 1
  verify_root "$BUNDLE_ROOT" "$BUNDLE_ID" || return 1
  DOWNLOAD_ROOT="$WORK_ROOT/downloads"; PRESET_ROOT="$BUNDLE_ROOT/presets"
  guard_owned_path "$WORK_ROOT" "$WORK_ID" "$DOWNLOAD_ROOT" dir || return 1
  guard_owned_path "$BUNDLE_ROOT" "$BUNDLE_ID" "$PRESET_ROOT" dir || return 1
  (umask 077; mkdir "$DOWNLOAD_ROOT" "$PRESET_ROOT") || return 1
}

cleanup_staging() {
  [ "$DRY_RUN" = 0 ] && [ -n "$WORK_ROOT" ] || return 0
  if verify_root "$WORK_ROOT" "$WORK_ID"; then rm -rf -- "$WORK_ROOT"
  else warn "Scratch cleanup skipped; inspect this changed path manually: $WORK_ROOT"; fi
}

finish_installer() {
  local status=$?
  if [ "$TERMINAL_OPEN" = 1 ]; then exec 3<&-; fi
  cleanup_staging || warn "Scratch cleanup failed: $WORK_ROOT"
  if [ "$status" -ne 0 ] && [ -n "$BUNDLE_ROOT" ]; then warn "Partial bundle retained; manual actions remain pending: $BUNDLE_ROOT"; fi
  return "$status"
}
trap finish_installer EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

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
  if [ "$DRY_RUN" = 1 ]; then warn "[dry-run] Clipboard copy suppressed."; return 1; fi
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
  find "$profiles_root" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | sort
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
TARGET_COUNT=0

add_target() {
  local key="$1" label="$2" family="$3" profile_name="$4" profile_path="$5" exe="$6" has_new="$7" has_old="$8" matches="$9" store="${10}" manager="${11}" newtab="${12}"
  TARGET_COUNT=$(( ${TARGET_COUNT:-0} + 1 ))
  local idx="$TARGET_COUNT"
  TARGETS+=("$idx|$key|$label|$family|$profile_name|$profile_path|$exe|$has_new|$has_old|$matches|$store|$manager|$newtab")
}

detect_targets() {
  local cfg key label family user_data exes newids oldids store manager newtab exe profiles profile_count status has_new has_old matches p pname
  for cfg in "${CONFIGS[@]}"; do
    IFS='|' read -r key label family user_data exes newids oldids store manager newtab <<< "$cfg"
    exe="$(find_exe "$exes" || true)"

    if [ "$family" = "chromium" ]; then
      profiles=(); profile_count=0
      while IFS= read -r p || [ -n "$p" ]; do profiles+=("$p"); profile_count=$((profile_count + 1)); done < <(chromium_profiles "$user_data")
      if [ "$profile_count" -eq 0 ] && { [ -n "$exe" ] || [ -d "$user_data" ]; }; then
        add_target "$key" "$label" "$family" "(no profile detected)" "" "$exe" "0" "0" "" "$store" "$manager" "$newtab"
      fi
      [ "$profile_count" -gt 0 ] || continue
      for p in "${profiles[@]}"; do
        pname="$(basename "$p")"
        has_new=0; has_old=0; matches=""
        if has_id_dir "$p" "$newids"; then has_new=1; matches="${matches}TablissNG-id; "; fi
        if has_id_dir "$p" "$oldids"; then has_old=1; matches="${matches}legacy-Tabliss-id; "; fi
        add_target "$key" "$label" "$family" "$pname" "$p" "$exe" "$has_new" "$has_old" "$matches" "$store" "$manager" "$newtab"
      done
    else
      profiles=(); profile_count=0
      while IFS= read -r p || [ -n "$p" ]; do profiles+=("$p"); profile_count=$((profile_count + 1)); done < <(firefox_profiles "$user_data")
      if [ "$profile_count" -eq 0 ] && { [ -n "$exe" ] || [ -d "$user_data" ]; }; then
        add_target "$key" "$label" "$family" "(no profile detected)" "" "$exe" "0" "0" "" "$store" "$manager" "$newtab"
      fi
      [ "$profile_count" -gt 0 ] || continue
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
  [ "$DRY_RUN" = 0 ] || { err "Offline preview leaves release assets unresolved."; return 1; }
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
  [ "$DRY_RUN" = 0 ] || { err "Offline preview does not return download/cache paths."; return 1; }
  verify_root "$WORK_ROOT" "$WORK_ID" || return 1
  local line tag name url tag_s name_s dest dest_dir partial
  line="$(select_asset "$family")" || return 1
  IFS=$'\t' read -r tag name url <<< "$line"
  [ -n "$tag" ] && [ -n "$name" ] && [ -n "$url" ] || { err "Incomplete release asset record."; return 1; }
  tag_s="$(sanitize "$tag")"
  name_s="$(sanitize "$name")"
  case "$tag_s:$name_s" in :*|*:|.:*|..:*|*:.|*:..) err "Invalid release path component."; return 1 ;; esac
  dest_dir="$DOWNLOAD_ROOT/$tag_s"
  guard_owned_path "$WORK_ROOT" "$WORK_ID" "$dest_dir" dir || return 1
  [ -d "$dest_dir" ] || (umask 077; mkdir "$dest_dir") || return 1
  dest="$dest_dir/$name_s"
  guard_owned_path "$WORK_ROOT" "$WORK_ID" "$dest" file || return 1
  if [ -f "$dest" ]; then
    validate_asset "$dest" || return 1
    ok "Already downloaded $name"
    printf '%s\n' "$dest"
    return 0
  fi
  printf 'Downloading %s\n  %s\n' "$name" "$url" >&2
  partial="$(umask 077; mktemp "$dest_dir/.asset.XXXXXXXX")" || return 1
  guard_owned_path "$WORK_ROOT" "$WORK_ID" "$partial" file || return 1
  curl -fL "$url" -o "$partial" || return 1
  validate_asset "$partial" || return 1
  guard_owned_path "$WORK_ROOT" "$WORK_ID" "$dest" file || return 1
  mv -- "$partial" "$dest" || return 1
  printf '%s\n' "$dest"
}

validate_asset() {
  [ "$DRY_RUN" = 0 ] || return 1
  [ -f "$1" ] && [ ! -L "$1" ] && [ -s "$1" ] || return 1
  python3 - "$1" <<'PY'
import sys, zipfile
try:
    with zipfile.ZipFile(sys.argv[1]) as archive:
        if not archive.infolist() or archive.testzip() is not None:
            raise ValueError("empty/corrupt archive")
except (OSError, ValueError, zipfile.BadZipFile) as error:
    raise SystemExit("Invalid extension archive: " + str(error))
PY
}

retain_asset() {
  [ "$DRY_RUN" = 0 ] || { err "Offline preview does not retain asset paths."; return 1; }
  guard_owned_path "$WORK_ROOT" "$WORK_ID" "$1" file || return 1
  [ -f "$1" ] || return 1
  local dest="$BUNDLE_ROOT/$(basename "$1")" partial
  guard_owned_path "$BUNDLE_ROOT" "$BUNDLE_ID" "$dest" file || return 1
  if [ ! -f "$dest" ]; then
    partial="$(umask 077; mktemp "$BUNDLE_ROOT/.asset.XXXXXXXX")" || return 1
    guard_owned_path "$BUNDLE_ROOT" "$BUNDLE_ID" "$partial" file || return 1
    cp -- "$1" "$partial" || return 1
    validate_asset "$partial" || return 1
    guard_owned_path "$BUNDLE_ROOT" "$BUNDLE_ID" "$dest" file || return 1
    mv -- "$partial" "$dest" || return 1
  fi
  printf '%s\n' "$dest"
}

expand_chromium_asset() {
  [ "$DRY_RUN" = 0 ] || { err "Offline preview does not extract assets."; return 1; }
  local zip_path="$1"
  guard_owned_path "$WORK_ROOT" "$WORK_ID" "$zip_path" file || return 1
  [ -f "$zip_path" ] || return 1
  verify_root "$BUNDLE_ROOT" "$BUNDLE_ID" || return 1
  local leaf extract
  leaf="$(basename "$zip_path" .zip)"
  extract="$(umask 077; mktemp -d "$BUNDLE_ROOT/${leaf}-unpacked.XXXXXXXX")" || return 1
  guard_owned_path "$BUNDLE_ROOT" "$BUNDLE_ID" "$extract" dir || return 1
  # Inspect every member before extracting anything. Links and ambiguous paths
  # are refused; files are created exclusively in the new private child.
  python3 - "$zip_path" "$extract" <<'PY'
import json, os, pathlib, shutil, stat, sys, zipfile
archive_path, destination = sys.argv[1:]
os.umask(0o077)
root = pathlib.Path(destination)
try:
    with zipfile.ZipFile(archive_path) as archive:
        members = []; seen = set()
        for member in archive.infolist():
            name = member.orig_filename
            parts = name.rstrip('/').split('/')
            mode = member.external_attr >> 16
            if (not name or '\x00' in name or '\\' in name or name.startswith('/')
                    or any(p in ('', '.', '..') or ':' in p for p in parts)
                    or stat.S_IFMT(mode) not in (0, stat.S_IFREG, stat.S_IFDIR)):
                raise ValueError("unsafe archive member: " + repr(name))
            key = '/'.join(parts)
            if key in seen: raise ValueError("duplicate archive member: " + key)
            seen.add(key); members.append((member, parts))
        for member, parts in members:
            target = root.joinpath(*parts)
            if member.is_dir(): target.mkdir(mode=0o700, parents=True, exist_ok=True)
            else:
                target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
                with archive.open(member) as source, target.open('xb') as output:
                    shutil.copyfileobj(source, output)
        manifests = sorted(p for p in root.rglob('manifest.json') if '__MACOSX' not in p.parts)
        if not manifests: raise ValueError("missing manifest.json")
        with manifests[0].open(encoding='utf-8') as source:
            manifest = json.load(source)
        if not isinstance(manifest, dict): raise ValueError("invalid manifest.json")
        print(manifests[0].parent)
except (OSError, ValueError, zipfile.BadZipFile) as error:
    raise SystemExit("Archive extraction refused; partial bundle retained: " + str(error))
PY
}

download_preset() {
  [ "$DRY_RUN" = 0 ] || { err "Offline preview does not stage or return preset paths."; return 1; }
  local partial
  local dest="$PRESET_ROOT/salah-widget.tablissng.json"
  guard_owned_path "$BUNDLE_ROOT" "$BUNDLE_ID" "$dest" file || return 1
  if [ -z "$SALAH_WIDGET_PRESET_URL" ]; then
    warn "No preset URL configured. Set SALAH_WIDGET_PRESET_URL."
    return 1
  fi
  printf 'Downloading Salah Widget preset:\n  %s\n' "$SALAH_WIDGET_PRESET_URL" >&2
  partial="$(umask 077; mktemp "$PRESET_ROOT/.preset.XXXXXXXX")" || return 1
  guard_owned_path "$BUNDLE_ROOT" "$BUNDLE_ID" "$partial" file || return 1
  if ! curl -fL "$SALAH_WIDGET_PRESET_URL" -o "$partial"; then
    warn "Could not download preset. Configure SALAH_WIDGET_PRESET_URL after publishing the preset JSON."
    return 1
  fi
  guard_owned_path "$BUNDLE_ROOT" "$BUNDLE_ID" "$partial" file || return 1
  python3 - "$partial" "$SALAH_WIDGET_HASH" <<'PY'
import json, pathlib, sys
path = pathlib.Path(sys.argv[1])
raw = path.read_text(encoding='utf-8')
if sys.argv[2]: raw = raw.replace('local=1', sys.argv[2])
json.loads(raw)
path.write_text(raw, encoding='utf-8')
PY
  [ "$?" -eq 0 ] || { err "Preset JSON/configuration validation failed; partial file retained."; return 1; }
  guard_owned_path "$BUNDLE_ROOT" "$BUNDLE_ID" "$dest" file || return 1
  mv -- "$partial" "$dest" || return 1
  ok "Preset JSON validated: $dest"
  printf '%s\n' "$dest"
}

install_tablissng() {
  [ "$DRY_RUN" = 0 ] || { warn "[dry-run] Installation actions suppressed; release and paths unresolved."; return 1; }
  local family="$1" label="$2" exe="$3" store="$4" manager="$5"
  local source="$SALAH_INSTALL_SOURCE" source_choice acknowledgment
  if [ "$source" = "ask" ]; then
    printf '\nInstall source for %s:\n  1) GitHub latest release/manual install\n  2) Official browser store page\n' "$label"
    read_answer source_choice "Choose [1/2] (default 1): " || return 1
    case "$source_choice" in ''|1|2) ;; *) err "Invalid install source choice."; return 1 ;; esac
    [ "$source_choice" = "2" ] && source="store" || source="github"
  fi

  if [ "$source" = "store" ]; then
    say_section "Open official store page for $label"
    printf '%s\n' "$store"
    open_url "$exe" "$store"
    read_answer acknowledgment "Press Enter after the browser step (installation remains manual): " || return 1
    return 0
  fi

  say_section "Download TablissNG from GitHub latest release for $label"
  local asset path
  if ! path="$(download_tablissng_asset "$family")"; then
    warn "GitHub release download failed; falling back to store page."
    open_url "$exe" "$store"
    read_answer acknowledgment "Press Enter after the browser step (installation remains manual): " || return 1
    return 0
  fi

  if [ "$family" = "chromium" ]; then
    local unpacked
    unpacked="$(expand_chromium_asset "$path")" || return 1
    printf '\nChromium-family install steps:\n'
    printf '  1. Open Extensions.\n'
    printf '  2. Enable Developer mode.\n'
    printf '  3. Click Load unpacked.\n'
    printf '  4. Select this folder:\n     %s\n' "$unpacked"
    printf 'Keep this directory while the unpacked extension is installed.\n'
    copy_text "$unpacked" && ok "Copied unpacked extension folder path to clipboard."
    open_url "$exe" "$manager"
  else
    path="$(retain_asset "$path")" || return 1
    printf '\nFirefox-family install steps:\n'
    printf '  1. Open Add-ons Manager.\n'
    printf '  2. Click the gear icon.\n'
    printf '  3. Click Install Add-on From File.\n'
    printf '  4. Select this file:\n     %s\n' "$path"
    copy_text "$path" && ok "Copied XPI path to clipboard."
    open_url "$exe" "$manager"
  fi
  ASSET_STAGED=1
  read_answer acknowledgment "Press Enter after the browser step (installation remains manual): " || return 1
}

show_import_instructions() {
  [ "$DRY_RUN" = 0 ] || { warn "[dry-run] Import actions suppressed; no artifact resolved."; return 1; }
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
  warn "Importing the preset replaces your current TablissNG dashboard."
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

if [ "$TARGET_COUNT" -eq 0 ]; then
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

# Local discovery only: skip terminal acquisition, root creation and all helpers
# that return artifacts. Remote facts and random paths stay unresolved.
if [ "$DRY_RUN" = 1 ]; then
  say_section "Offline preview"
  eligible_count=0
  for t in "${TARGETS[@]}"; do
    IFS='|' read -r idx key label family profile_name profile_path exe has_new has_old matches store manager newtab <<< "$t"
    if [ "$has_old" = 1 ]; then warn "Legacy Tabliss: refusing $label / $profile_name."; continue; fi
    eligible_count=$((eligible_count + 1))
    printf 'Would prepare %s / %s.\n' "$label" "$profile_name"
    if [ "$has_new" != 1 ]; then
      case "$SALAH_INSTALL_SOURCE" in
        ask) printf 'Install source unresolved: GitHub manual route or official store page.\n' ;;
        store) printf 'Would open official store: %s\n' "$store" ;;
        github) printf 'Would resolve/download GitHub release; release/version/path unresolved until execution.\n' ;;
      esac
    fi
    if [ -n "$SALAH_WIDGET_PRESET_URL" ]; then printf 'Would stage the configured preset and guide manual import; path unresolved until execution.\n'
    else warn "No preset URL configured; preset import cannot be prepared."; fi
    printf 'Would offer clipboard paths and open the browser manual installation/import pages.\n'
  done
  warn "Importing the preset replaces your current TablissNG dashboard."
  [ "$eligible_count" -gt 0 ] || { err "No eligible target; preview made no changes."; exit 1; }
  printf 'Preview only; no changes made. No network requests were made.\n'
  exit 0
fi

acquire_terminal || exit 1
printf '\n'
read_answer selection "Select target numbers separated by commas, or 'all' (default all): " || exit 1
selection="${selection:-all}"
selection="${selection//[[:space:]]/}"

selected_csv=","
if [ "$selection" != "all" ]; then
  case "$selection" in ''|,*|*,|*,,*) err "Invalid target selection: $selection"; exit 1 ;; esac
  IFS=',' read -r -a wanted <<< "$selection"
  for token in "${wanted[@]}"; do
    [[ "$token" =~ ^[0-9]+$ ]] || { err "Invalid target number: $token"; exit 1; }
    found=0
    for t in "${TARGETS[@]}"; do
      IFS='|' read -r idx key label family profile_name profile_path exe has_new has_old matches store manager newtab <<< "$t"
      [ "$token" != "$idx" ] || found=1
    done
    [ "$found" = 1 ] || { err "Unknown target number: $token"; exit 1; }
    case "$selected_csv" in *",$token,"*) ;; *) selected_csv="${selected_csv}${token}," ;; esac
  done
fi

eligible_count=0
for t in "${TARGETS[@]}"; do
  IFS='|' read -r idx key label family profile_name profile_path exe has_new has_old matches store manager newtab <<< "$t"
  if { [ "$selection" = all ] || [[ "$selected_csv" = *",$idx,"* ]]; } && [ "$has_old" != 1 ]; then eligible_count=$((eligible_count + 1)); fi
done
[ "$eligible_count" -gt 0 ] || { err "No eligible target selected; legacy Tabliss profiles are refused."; exit 1; }
initialize_staging || { err "Automatic staging is unavailable on this ownership boundary; use the reviewed manual browser-install/import route."; exit 1; }
preset_file=""; ASSET_STAGED=0

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
    install_tablissng "$family" "$label" "$exe" "$store" "$manager" || exit 1
  else
    ok "TablissNG already appears to be installed."
  fi

  if [ -z "$preset_file" ]; then
    if ! preset_file="$(download_preset)"; then warn "Preset staging failed; manual import remains pending."; fi
  fi
  show_import_instructions "$label" "$profile_name" "$exe" "$newtab" "$preset_file"
done

say_section "Manual action pending"
if [ -n "$preset_file" ] || [ "$ASSET_STAGED" = 1 ]; then
  printf 'Validated manual-install files retained in:\n  %s\n' "$BUNDLE_ROOT"
  printf 'Keep unpacked extension directories while installed. Preset/XPI removal after import/install is optional and manual.\n'
else
  err "No files were staged; browser installation/import remain manual and unresolved."
  exit 1
fi
