"""Focused preservation comparison, using an already-installed Playwright + Pillow.

Only a disposable Pages-shaped copy is served/mutated. Provider responses are
fixtures, not live science evidence. Fonts are fetched once into --output/fonts,
then replayed identically for both paths with their hashes in the receipt.
"""
import argparse
from datetime import datetime, timezone
import hashlib
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import platform
from pathlib import Path
import re
import shutil
import tempfile
import threading
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parents[1]
FONT_CSS = "https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400..700&family=Inter:wght@400;500;600&display=swap"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36"
SETTINGS = {"v": 1, "lat": 24.47, "lon": 39.61, "tz": "Asia/Riyadh", "label": "Madinah", "method": "4", "school": "0", "time": "24", "datefmt": "YYYY-MM-DD", "units": "c", "lp": 0, "seed": 1, "source": "manual", "savedAt": 1791345600000}
ROOT_KEY = "salah_widget:config:v1"
V1_KEY = "salah_widget:v1:config:v1"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def fonts(output):
    directory = output / "fonts"
    directory.mkdir(exist_ok=True)
    entries = {}
    def acquire(url):
        file = directory / sha(url.encode())
        if not file.exists():
            with urlopen(Request(url, headers={"User-Agent": USER_AGENT}), timeout=30) as r:
                file.write_bytes(r.read())
        entries[url] = file
        return file.read_bytes()
    css = acquire(FONT_CSS)
    for url in set(re.findall(r"url\((https://[^)]+)\)", css.decode())):
        acquire(url)
    return entries


def fixture(url, night):
    host = urlsplit(url).hostname
    if host == "api.aladhan.com":
        day = int(urlsplit(url).path.rstrip("/").split("/")[-1].split("-")[0])
        return {"code": 200, "data": {"timings": {"Fajr": "05:00", "Sunrise": "06:15", "Dhuhr": "12:15", "Asr": "15:40", "Maghrib": "18:15", "Sunset": "18:15", "Isha": "19:45"}, "meta": {"timezone": "Asia/Riyadh"}, "date": {"gregorian": {"day": str(day), "month": {"number": 10, "en": "October"}, "year": "2026"}, "hijri": {"day": str(day + 17), "month": {"number": 4, "en": "Rabi al-Thani"}, "year": "1448"}}}}
    if host == "api.open-meteo.com":
        return {"elevation": 620, "current": {"weather_code": 2, "temperature_2m": 28, "apparent_temperature": 28, "relative_humidity_2m": 45, "dew_point_2m": 14, "wind_speed_10m": 2, "wind_direction_10m": 45, "wind_gusts_10m": 3, "cloud_cover": 30, "cloud_cover_low": 5, "cloud_cover_mid": 20, "cloud_cover_high": 15, "precipitation": 0, "rain": 0, "showers": 0, "snowfall": 0, "visibility": 30000, "is_day": 0 if night else 1}}
    if host == "api.rainviewer.com":
        return {"host": "https://tilecache.rainviewer.com", "radar": {"past": []}}
    if host == "get.geojs.io":
        return {"latitude": "24.47", "longitude": "39.61", "city": "Madinah", "country": "Saudi Arabia", "country_code": "SA", "timezone": "Asia/Riyadh"}
    if host == "ipinfo.io":
        return {"loc": "24.47,39.61", "city": "Madinah", "country": "SA", "timezone": "Asia/Riyadh"}
    if host == "nominatim.openstreetmap.org":
        return [{"lat": "24.47", "lon": "39.61", "class": "place", "address": {"city": "Madinah", "country": "Saudi Arabia", "country_code": "sa"}}]
    raise AssertionError("Unplanned external request: " + url)


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass


def setup_browser(browser, font_files, origin, *, night=False, dpr=1, seed=True, denied=False):
    context = browser.new_context(viewport={"width": 390, "height": 600}, device_scale_factor=dpr,
        timezone_id="Asia/Riyadh", locale="en-US", reduced_motion="reduce", color_scheme="light",
        geolocation={"latitude": 21.4225, "longitude": 39.8262, "accuracy": 10})
    if not denied:
        context.grant_permissions(["geolocation"], origin=origin)
    if seed:
        context.add_init_script("if(location.protocol === 'http:' && !localStorage.getItem(" + json.dumps(ROOT_KEY) + ")) localStorage.setItem(" + json.dumps(ROOT_KEY) + "," + json.dumps(json.dumps(SETTINGS)) + ");")
    requests, errors, failed = [], [], []
    def route(r):
        url = r.request.url
        requests.append(url)
        if url.startswith(origin + "/"):
            r.continue_()
        elif url in font_files:
            r.fulfill(body=font_files[url].read_bytes(), content_type="text/css" if url == FONT_CSS else "font/woff2", headers={"Access-Control-Allow-Origin": "*"})
        else:
            r.fulfill(json=fixture(url, night), headers={"Access-Control-Allow-Origin": "*"})
    context.route("**/*", route)
    context.on("page", lambda page: page.on("pageerror", lambda error: errors.append(str(error))))
    context.on("requestfailed", lambda request: failed.append({"url": request.url, "failure": request.failure}))
    context.on("response", lambda r: failed.append({"url": r.url, "status": r.status}) if r.status >= 400 else None)
    page = context.new_page()
    if denied:
        session = context.new_cdp_session(page)
        session.send("Browser.setPermission", {"permission": {"name": "geolocation"}, "setting": "denied", "origin": origin})
    instant = datetime(2026, 10, 7, 20 if night else 9, 30, tzinfo=timezone.utc)
    page.clock.install(time=instant)
    page.clock.pause_at(instant)
    return context, page, requests, errors, failed


def loaded(page, url):
    page.goto(url, wait_until="load")
    frame = page.frames[1]
    frame.wait_for_function("typeof qaState === 'function' && qaState().cache.prayerLoaded && qaState().cache.tomorrowLoaded", polling=100)
    frame.evaluate("document.fonts.ready")
    page.clock.run_for(3500)
    assert frame.locator(".times .p b").all_text_contents() == ["Fajr", "Sunrise", "Dhuhr", "Asr", "Maghrib", "Isha"]
    assert "2026-10-07" in frame.locator("#ce").inner_text()
    assert "1448" in frame.locator("#ah").inner_text()
    return frame


def snapshot(page, frame, output, name):
    path = output / (name + ".png")
    page.locator("iframe").screenshot(path=path, animations="disabled")
    return {"screenshot": path.name, "sha256": sha(path.read_bytes()), "qa": frame.evaluate("qaState()"),
        "geometry": frame.evaluate("() => {const box=s=>{const r=document.querySelector(s).getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height,bottom:r.bottom}}; return {innerWidth,innerHeight,dpr:devicePixelRatio,card:box('.c'),footer:box('.d'),header:box('.h'),scrollWidth:document.documentElement.scrollWidth,scrollHeight:document.documentElement.scrollHeight};}"),
        "rows": frame.locator(".times").inner_text(), "countdown": frame.locator(".left").inner_text(),
        "fonts": frame.evaluate("[...document.fonts].filter(f=>f.status==='loaded').map(f=>({family:f.family,weight:f.weight,status:f.status}))")}


def compare(output, a, b):
    im1, im2 = Image.open(output / a).convert("RGB"), Image.open(output / b).convert("RGB")
    diff = ImageChops.difference(im1, im2)
    raw = diff.tobytes()
    changed = sum(any(raw[i:i+3]) for i in range(0, len(raw), 3))
    maximum = max(raw)
    return {"changedPixels": changed, "totalPixels": im1.width * im1.height, "maxChannelDelta": maximum, "pixelExact": changed == 0}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--chromium", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    font_files = fonts(output)
    receipt = {"status": "INCOMPLETE", "platform": platform.platform(), "python": platform.python_version(), "testSha256": sha(Path(__file__).read_bytes()), "payloadHashes": {name:sha((REPO / name).read_bytes()) for name in ("index.html", "config.js", "v1/index.html", "v1/config.js")}, "fixtureNotice": "Controlled provider fixtures, emulated browser clock/location/permissions, replayed fonts; not live provider or real GPS evidence", "clockDay": "2026-10-07T09:30:00Z", "clockNight": "2026-10-07T20:30:00Z", "settings": SETTINGS, "viewport": [390, 600], "reducedMotion": "reduce", "fontHashes": {u:sha(f.read_bytes()) for u,f in font_files.items()}, "captures": {}, "checks": {}}
    with tempfile.TemporaryDirectory(prefix="salah-v1-browser-") as tmp, sync_playwright() as pw:
        site = Path(tmp) / "salah_widget"
        site.mkdir()
        for name in ("index.html", "config.js"):
            shutil.copyfile(REPO / name, site / name)
        shutil.copytree(REPO / "v1", site / "v1")
        for name, src in (("root", "/salah_widget/#local=1"), ("v1", "/salah_widget/v1/#local=1")):
            # The user iframe, with only origin/path localized. Same body for both.
            html = '<!doctype html><html><head><meta charset="utf-8"><title>Preservation comparison</title></head><body>\n<iframe\n  title="Prayer Times"\n  referrerpolicy="no-referrer"\n  allow="geolocation"\n  src="' + src + '"\n  style="width:330px;height:534px;border:0;border-radius:28px;overflow:hidden"\n  scrolling="no">\n</iframe>\n</body></html>\n'
            (Path(tmp) / (name + ".html")).write_text(html, encoding="utf-8")
            (output / (name + "-iframe.html")).write_text(html, encoding="utf-8")
        server = ThreadingHTTPServer(("127.0.0.1", 0), lambda *a, **kw: Handler(*a, directory=tmp, **kw))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        origin = f"http://127.0.0.1:{server.server_port}"
        browser = pw.chromium.launch(executable_path=str(args.chromium), headless=True, chromium_sandbox=True)
        receipt["browser"] = browser.version
        try:
            for night, dpr in ((False, 1), (True, 1), (False, 2)):
                scene = ("night" if night else "day") + f"-dpr{dpr}"
                for version in ("root", "v1"):
                    c, page, requests, errors, failed = setup_browser(browser, font_files, origin, night=night, dpr=dpr)
                    f = loaded(page, origin + "/" + version + ".html")
                    name = version + "-" + scene
                    result = snapshot(page, f, output, name)
                    result["localRequests"] = [u.replace(origin, "") for u in requests if u.startswith(origin)]
                    assert result["geometry"]["card"]["width"] == 325
                    assert result["geometry"]["card"]["height"] == 530
                    assert result["geometry"]["footer"]["bottom"] <= 534
                    assert result["fonts"], "Font fixture did not load"
                    config_path = "/salah_widget/" + ("v1/" if version == "v1" else "") + "config.js"
                    assert config_path in result["localRequests"]
                    if version == "v1":
                        assert "/salah_widget/config.js" not in result["localRequests"]
                    before = f.locator(".left").inner_text()
                    # The deployed countdown displays hours/minutes, not seconds.
                    page.clock.fast_forward(61000)
                    assert before != f.locator(".left").inner_text(), "Countdown is frozen"
                    result["countdownAfter61Seconds"] = f.locator(".left").inner_text()
                    assert not errors and not failed, (errors, failed)
                    result["errors"], result["failedRequests"] = errors, failed
                    receipt["captures"][name] = result
                    c.close()
                comparison = compare(output, "root-" + scene + ".png", "v1-" + scene + ".png")
                receipt["checks"]["comparison-" + scene] = comparison
                assert comparison["pixelExact"], comparison
                print("PASS: exact iframe comparison " + scene, flush=True)

            # Fresh #local=1 => coarse location; then browser-granted/denied GPS paths.
            for version in ("root", "v1"):
                for denied in (False, True):
                    c, page, requests, errors, failed = setup_browser(browser, font_files, origin, seed=False, denied=denied)
                    f = loaded(page, origin + "/" + version + ".html")
                    assert f.evaluate("qaState().config.autoDetectStatus") == "ok"
                    f.locator(".buckle").click(force=True)
                    page.clock.run_for(100)
                    f.locator("#set-pin").click(force=True)
                    f.wait_for_function("!document.querySelector('#set-status').textContent.includes('Requesting')", polling=100)
                    status = f.locator("#set-status").inner_text()
                    assert ("unavailable" in status) if denied else ("Using your precise location" in status), status
                    if denied:
                        f.locator("#set-label").fill("Manual after denial")
                        f.locator("#set-lat").fill("24.47")
                        f.locator("#set-lon").fill("39.61")
                    f.locator("#setClose").click(force=True)
                    page.clock.run_for(1500)
                    saved = f.evaluate("SalahConfig.loadLocal()")
                    assert saved and (saved["label"] == "Manual after denial" if denied else saved["lat"] == 21.4225)
                    if version == "v1":
                        assert f.evaluate("localStorage.getItem('salah_widget:config:v1')") is None
                    page.reload(wait_until="load")
                    f = page.frames[1]
                    f.wait_for_function("typeof qaState==='function' && qaState().cache.prayerLoaded", polling=100)
                    page.clock.run_for(1500)
                    assert f.evaluate("SalahConfig.loadLocal().label") == saved["label"]
                    assert not errors and not failed, (errors, failed)
                    receipt["checks"][version + ("-geo-denied" if denied else "-geo-granted")] = {"status": status, "saved": saved, "reload": True, "errors": errors}
                    c.close()
            print("PASS: root/V1 coarse location, granted/denied GPS, manual recovery, settings reload", flush=True)

            c, page, requests, errors, failed = setup_browser(browser, font_files, origin)
            f = loaded(page, origin + "/v1.html")
            original_root = f.evaluate("localStorage.getItem('salah_widget:config:v1')")
            f.locator(".buckle").click(force=True)
            page.clock.run_for(100)
            f.locator("#set-label").fill("V1 saved independently")
            f.locator("#set-time").select_option("12")
            receipt["captures"]["v1-settings"] = snapshot(page, f, output, "v1-settings")
            f.locator("#setClose").click(force=True)
            page.clock.run_for(1500)
            assert f.evaluate("localStorage.getItem('salah_widget:config:v1')") == original_root
            assert f.evaluate("SalahConfig.loadLocal().time") == "12"
            f.evaluate("localStorage.setItem('salah_widget:config:v1',JSON.stringify({v:99,label:'Future root schema'}))")
            page.reload(wait_until="load")
            f = page.frames[1]
            f.wait_for_function("typeof qaState==='function' && qaState().cache.prayerLoaded", polling=100)
            assert f.evaluate("SalahConfig.loadLocal().label") == "V1 saved independently"
            keys = f.evaluate("Object.keys(localStorage)")
            assert any(k.startswith("salah_widget:v1:prayer:") for k in keys)
            assert any(k.startswith("salah_widget:v1:weather:") for k in keys)
            assert not any(k.startswith(("salah:", "salahwx:")) for k in keys)
            assert not errors and not failed, (errors, failed)
            receipt["checks"]["storage-isolation"] = {"rootUnchangedByV1Save": True, "futureRootSchemaIgnored": True, "keys": keys}
            c.close()

            # Destructive dependency control is confined to the temporary served copy.
            (site / "config.js").write_text("throw new Error('ROOT CONFIG REPLACED CONTROL');", encoding="utf-8")
            (site / "index.html").write_text("<!doctype html>ROOT REPLACED CONTROL", encoding="utf-8")
            c, page, requests, errors, failed = setup_browser(browser, font_files, origin)
            f = loaded(page, origin + "/v1.html")
            receipt["captures"]["v1-root-replaced"] = snapshot(page, f, output, "v1-root-replaced")
            isolated = compare(output, "v1-day-dpr1.png", "v1-root-replaced.png")
            assert isolated["pixelExact"] and not errors and not failed, (isolated, errors, failed)
            assert origin + "/salah_widget/config.js" not in requests
            receipt["checks"]["root-replacement-isolation"] = isolated
            c.close()
            receipt["status"] = "PASS"
            print("PASS: V1 storage isolation and disposable root index/config replacement", flush=True)
        finally:
            browser.close()
            server.shutdown()
            (output / "browser-results.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print("PASS: all focused preservation browser checks", flush=True)


if __name__ == "__main__":
    main()
