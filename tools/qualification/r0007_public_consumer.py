#!/usr/bin/env python3
"""Observe original delivered R0007 HTML after explicit approval/merge/Pages gates.

Validation mode opens no network/browser. Acquisition uses fresh contexts,
controlled provider HTTP ingress and fixed pre-boot Date only. It never calls
product render/model or seeds product state. Pixels remain independently reviewed.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import platform
import re
import struct
import subprocess
import sys
import time
import urllib.error
import urllib.request
import zlib
from urllib.parse import parse_qs, unquote, urljoin, urlsplit

SITE = "https://theislampill.github.io/salah_widget/"
REQUIRED_FILES = {"index.html", "offline.html", "config.js", "moon/BUILD.json", "moon/asset-manifest.json",
                  "moon/initial-manifest.json", "moon/initial-compact-manifest.json", "moon/initial-source-association.json",
                  "real-sky/checkpoint.json"}
PROBE_PATH = "tools/qualification/r0007_public_consumer.py"
CASES_PATH = "tools/qualification/r0007_public_cases.json"
FONT_OBSERVER_PATH = "tools/cp9/r0007_font_observer.js"


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def safe_path(path):
    return isinstance(path, str) and path and ":" not in path and "\\" not in path and not any(ord(c) < 32 for c in path) and not PurePosixPath(path).is_absolute() and all(p not in {"", ".", ".."} for p in path.split("/"))


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise urllib.error.HTTPError(req.full_url, code, "unexpected served-file redirect refused", headers, fp)


def validate(request, cases, template=False):
    if request.get("schema") != "r0007-public-delivery-request/v1" or request.get("site") != SITE or request.get("issue") != 7:
        raise ValueError("request scope/site mismatch")
    if cases.get("schema") != "r0007-public-consumer-cases/v1":
        raise ValueError("public case schema mismatch")
    ids = [c["caseId"] for c in cases["cases"]]
    if len(ids) != len(set(ids)) or not set(cases["requiredCaseIds"]).issubset(ids):
        raise ValueError("case population invalid")
    for c in cases["cases"]:
        if not re.fullmatch(r"[A-Za-z0-9_-]+", c["caseId"]) or c["entry"] not in {"index.html", "offline.html"} or c["mode"] not in {"ready", "missing", "recovery"}:
            raise ValueError("case path/mode invalid")
        if "timeScale" in c["hash"] or "simTime=23%3A00" not in c["hash"] or c["epoch"] != "2026-09-07T23:00:00Z":
            raise ValueError("case must retain its declared frozen native-clock input")
    if not REQUIRED_FILES.issubset(request.get("expectedFiles", {})):
        raise ValueError("required served file population incomplete")
    for path, record in request["expectedFiles"].items():
        if not safe_path(path):
            raise ValueError("unsafe served path")
        if not template and (not re.fullmatch(r"[0-9a-f]{64}", record.get("sha256", "")) or not isinstance(record.get("bytes"), int) or record["bytes"] <= 0):
            raise ValueError("served file identity is unbound: " + path)
    if template:
        return {"status": "PREPARED_TEMPLATE_NOT_EXECUTABLE", "requiredCaseCount": len(cases["requiredCaseIds"]), "network": False}
    if request.get("status") != "READY_AFTER_APPROVAL_MERGE_AND_PAGES_READBACK":
        raise ValueError("explicit post-approval/merge/Pages request is absent")
    approval, merge, pages = request["ownerApproval"], request["merge"], request["pages"]
    for value in [approval["headSha"], approval["baseSha"], approval["treeSha"], approval["baseTreeSha"], merge["mainSha"], merge["treeSha"], pages["sourceSha"]]:
        if not re.fullmatch(r"[0-9a-f]{40}", value):
            raise ValueError("approval/merge/Pages identity is unbound")
    if approval.get("status") != "APPROVED_EXACT_CANDIDATE" or merge.get("status") != "MERGED_VERIFIED" or pages.get("status") != "SUCCESS_VERIFIED_EXTERNALLY":
        raise ValueError("approval/merge/Pages status is not ready")
    if approval["treeSha"] != merge["treeSha"] or pages["sourceSha"] != merge["mainSha"]:
        raise ValueError("qualified tree or Pages source differs from the approved merged candidate")
    if merge.get("method") != "merge":
        raise ValueError("only the expressly planned two-parent merge topology is qualified")
    if not all(isinstance(x, str) and x and x != "UNBOUND" for x in [approval.get("receipt"), merge.get("receipt"), pages.get("receipt")]):
        raise ValueError("externally verified gate receipts are missing")
    if not isinstance(pages.get("runId"), int) or pages["runId"] <= 0:
        raise ValueError("Pages run identity missing")
    if not re.fullmatch(r"[0-9a-f]{64}", request.get("fontObserverSha256", "")):
        raise ValueError("font observer identity is unbound")
    return {"status": "REQUEST_STRUCTURALLY_BOUND_EXTERNAL_AUTHORITY_NOT_RECREATED", "requiredCaseCount": len(cases["requiredCaseIds"]), "network": False}


def git_bytes(root, revision, path):
    return subprocess.check_output(["git", "-C", str(root), "cat-file", "blob", revision + ":" + path])


def verify_git(request, root, require_fetch_head):
    approval, merge = request["ownerApproval"], request["merge"]
    merged, head, base = merge["mainSha"], approval["headSha"], approval["baseSha"]
    if merge.get("method") != "merge" or len({merged, head, base}) != 3:
        raise ValueError("request is not the agreed distinct two-parent merge")
    def read(*args):
        return subprocess.check_output(["git", "-C", str(root), *args], text=True, stderr=subprocess.STDOUT).strip()
    for revision in [base, head, merged]:
        if read("cat-file", "-t", revision) != "commit":
            raise ValueError("approved/merged object is not a commit")
    trees = {revision: read("rev-parse", revision + "^{tree}") for revision in [base, head, merged]}
    if trees[base] != approval["baseTreeSha"] or trees[head] != approval["treeSha"] or trees[merged] != merge["treeSha"] or trees[head] != trees[merged]:
        raise ValueError("actual approved base/head/merged trees differ from recorded identities")
    ancestry = subprocess.run(["git", "-C", str(root), "merge-base", "--is-ancestor", base, head], capture_output=True)
    if ancestry.returncode != 0:
        raise ValueError("approved base is not proven ancestor of approved head; require complete immutable history")
    parents = read("show", "-s", "--format=%P", merged).split()
    if parents != [base, head]:
        raise ValueError("actual merge parents are not ordered [approved base, approved head]")
    if require_fetch_head and read("rev-parse", "FETCH_HEAD") != merged:
        raise ValueError("freshly fetched main moved from requested merge; reconcile before delivery acceptance")
    for path, expected in request["expectedFiles"].items():
        content = git_bytes(root, merged, path)
        if len(content) != expected["bytes"] or sha(content) != expected["sha256"]:
            raise ValueError("expected served identity differs from merged Git bytes: " + path)
    if (sha(git_bytes(root, merged, PROBE_PATH)) != request["probeSha256"] or sha(git_bytes(root, merged, CASES_PATH)) != request["casesSha256"]
        or sha(git_bytes(root, merged, FONT_OBSERVER_PATH)) != request["fontObserverSha256"]):
        raise ValueError("delivery probe/cases/font observer are not the reviewed merged versions")
    return {"base": {"sha": base, "tree": trees[base]}, "head": {"sha": head, "tree": trees[head]},
            "merged": {"sha": merged, "tree": trees[merged], "parents": parents}, "baseAncestorOfHead": True,
            "externalApprovalAuthority": "RECEIPT_REQUIRED_NOT_MECHANICALLY_RECREATED"}


def served_readback(request, output):
    receipts = []
    for path, expected in request["expectedFiles"].items():
        url = SITE if path == "index.html" else urljoin(SITE, path)
        row = {"path": path, "url": url, "startedUtc": now(), "expected": expected}
        dump(output / "served-readback.json", {"status": "IN_PROGRESS", "files": receipts, "active": row})
        req = urllib.request.Request(url, headers={"Cache-Control": "no-cache", "Accept-Encoding": "identity", "User-Agent": "R0007-delivered-consumer-readback"})
        with urllib.request.build_opener(NoRedirect()).open(req, timeout=45) as response:
            if response.geturl() != url or response.status != 200:
                raise ValueError("unexpected redirect/status for served file: " + path)
            digest, length = hashlib.sha256(), 0
            while chunk := response.read(1024 * 1024):
                digest.update(chunk)
                length += len(chunk)
                if length > expected["bytes"]:
                    raise ValueError("served file exceeds qualified byte length: " + path)
            row.update(status=response.status, finalUrl=response.geturl(), headers=dict(response.headers), bytes=length, sha256=digest.hexdigest())
        row["matchesQualifiedTree"] = row["bytes"] == expected["bytes"] and row["sha256"] == expected["sha256"]
        row["finishedUtc"] = now()
        receipts.append(row)
        dump(output / "served-readback.json", {"status": "HASHES_RECORDED", "files": receipts})
        if not row["matchesQualifiedTree"]:
            raise ValueError("served bytes differ from qualified merged tree: " + path)
    return receipts


INIT = r"""(() => {
 const NativeDate=Date, epoch=__EPOCH__;
 window.Date=class extends NativeDate {constructor(...args){super(...(args.length?args:[epoch]));}static now(){return epoch;}};
 const P=window.__r0007PublicDelivery={snapshots:[],events:[],started:performance.now()};
 const copy=x=>JSON.parse(JSON.stringify(x,(_,v)=>typeof v==='number'&&!Number.isFinite(v)?{finite:false,value:null}:v));
 const dom=selector=>{const e=document.querySelector(selector);if(!e)return {unavailable:true};const r=e.getBoundingClientRect();return {text:e.textContent,html:e.innerHTML,tagName:e.tagName.toLowerCase(),geometry:{x:r.x,y:r.y,width:r.width,height:r.height}};};
 const fontReceipts=new WeakMap();
 const authoredFontLink=e=>e?.tagName==='LINK'&&e.rel==='stylesheet'&&(()=>{try{const u=new URL(e.href);return u.origin==='https://fonts.googleapis.com'&&u.pathname==='/css2';}catch{return false;}})();
 for(const type of ['load','error'])window.addEventListener(type,event=>{
  if(authoredFontLink(event.target)&&event.isTrusted){const receipt={type,isTrusted:event.isTrusted,href:event.target.href,at:performance.now(),mediaAtEvent:event.target.media};fontReceipts.set(event.target,receipt);P.events.push({type:'authored-font-link-terminal',receipt});}
 },true);
 P.fontState=()=>{
  const links=[...document.querySelectorAll('link[rel="stylesheet"]')].filter(authoredFontLink).map(link=>({href:link.href,media:link.media,disabled:link.disabled,sheetPresent:!!link.sheet,receipt:fontReceipts.get(link)||null}));
  const cssReady=links.length===1&&links.every(x=>x.receipt?.isTrusted&&(x.receipt.type==='error'||x.receipt.type==='load'&&!x.disabled&&x.media==='all'&&x.sheetPresent));
  return {links,cssReady,fontStatus:document.fonts.status,fontObserver:window.__r0007FontSettlement?.read()||null,faces:[...document.fonts].map(f=>({family:f.family,style:f.style,weight:f.weight,status:f.status}))};
 };
 P.receipt=()=>copy(window.qaState().render);
 P.geometry=()=>Object.fromEntries(['.c','.nt','.left','.times','.arc'].map(x=>[x,dom(x).geometry||null]));
 P.awaitTypography=async()=>{
  const before=P.fontState();if(!before.cssReady)throw Error('authored font stylesheet is not terminal/applied');
  const promiseStartedAt=performance.now();P.geometry();let timeout;
  try{await Promise.race([document.fonts.ready,new Promise((_,reject)=>{timeout=setTimeout(()=>reject(Error('native font readiness timeout')),15000);})]);}finally{clearTimeout(timeout);}
  const after=P.fontState();if(!after.cssReady||after.fontStatus!=='loaded')throw Error('native font readiness changed before settlement');
  return {readyPromiseFulfilled:true,fontStatus:after.fontStatus,dirtyState:'not-exposed',promiseStartedAt,promiseSettledAt:performance.now(),fontState:after};
 };
 P.observeStable=async()=>{
  const observations=[];let prior=null,consecutive=0;const deadline=performance.now()+10000;
  while(performance.now()<deadline){await new Promise((resolve,reject)=>{const timer=setTimeout(()=>reject(Error('native rAF observation timeout')),1500);requestAnimationFrame(()=>{clearTimeout(timer);resolve();});});
   const render=P.receipt(),geometry=P.geometry(),fonts=P.fontState();
   const observation={render,geometry,fontState:fonts};observations.push(observation);
   const admitted=fonts.cssReady&&fonts.fontStatus==='loaded'&&fonts.fontObserver?.settled&&render;
   const signature=JSON.stringify(observation);consecutive=admitted&&signature===prior?consecutive+1:1;prior=signature;
   if(admitted&&consecutive>=3)return {settled:true,dirtyState:'not-exposed',observations:observations.slice(-3),scope:'Unchanged actual receipt/geometry/fonts and deferred typed font-event receipts across three native rAF callbacks; no private loop/dirty proof'};
  }throw Error('observable native receipt/geometry did not settle');
 };
 P.sample=stage=>{
  if(typeof window.qaState!=='function')return null;
  const before={href:document.querySelector('.mphoto')?.getAttribute('href'),classes:document.querySelector('.c')?.className};
  try{
   const q=window.qaState(),s={stage,observedAt:performance.now(),wallUtcMs:Date.now(),render:copy(q.render),cache:copy(q.cache),currentDay:q.cache?.prayerDate,timezone:q.render?.zone,
    dom:Object.fromEntries(['.c','.nt','.left','.times','.arc','#ce','#ah','.buckle','.d'].map(x=>[x,dom(x)])),
    rows:[...document.querySelectorAll('.times .p')].map(e=>({key:e.dataset.prayerKey,on:e.classList.contains('on'),clock:e.querySelector('.tm')?.textContent,classes:e.className})),
    fonts:{status:document.fonts.status,settlement:window.__r0007FontSettlement?.read()||null,faces:[...document.fonts].map(f=>({family:f.family,status:f.status}))},
    diagnosticSurface:{before,after:{href:document.querySelector('.mphoto')?.getAttribute('href'),classes:document.querySelector('.c')?.className}}};
   P.snapshots.push(s);return s;
  }catch(e){P.events.push({type:'observation-error',message:String(e),at:performance.now()});return null;}
 };
 const watch=()=>{P.sample('dom-ready');const observer=new MutationObserver(()=>P.sample('actual-prayer-dom-mutation'));for(const s of ['.nt','.left','.times']){const e=document.querySelector(s);if(e)observer.observe(e,{childList:true,subtree:true,characterData:true});}};
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',watch,{once:true});else watch();
})();"""


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def artifact_file(path, root):
    path, root = Path(path), Path(root).resolve()
    if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(root) or path.stat().st_size == 0:
        raise ValueError("required artifact missing, empty or outside owned output: " + path.name)
    return {"path": path.resolve().relative_to(root).as_posix(), "bytes": path.stat().st_size, "sha256": sha(path.read_bytes())}


def verify_png(path, root):
    receipt = artifact_file(path, root)
    data = Path(path).read_bytes()
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("required screenshot is not PNG")
    offset, pixels, ihdr, ended = 8, b"", None, False
    while offset < len(data):
        if offset + 12 > len(data): raise ValueError("truncated PNG chunk")
        size = struct.unpack(">I", data[offset:offset+4])[0]
        kind = data[offset+4:offset+8]; end = offset + 12 + size
        if end > len(data): raise ValueError("truncated PNG payload")
        body = data[offset+8:offset+8+size]
        if zlib.crc32(kind + body) & 0xffffffff != struct.unpack(">I", data[end-4:end])[0]: raise ValueError("PNG chunk checksum mismatch")
        if kind == b"IHDR":
            if ihdr is not None or size != 13: raise ValueError("invalid PNG header")
            ihdr = struct.unpack(">IIBBBBB", body)
        elif kind == b"IDAT": pixels += body
        elif kind == b"IEND":
            if size or end != len(data): raise ValueError("invalid PNG termination")
            ended = True
        offset = end
    if not ended or ihdr is None or ihdr[:2] != (370, 570) or ihdr[2] != 8 or ihdr[3] not in {2, 6} or ihdr[4:] != (0, 0, 0):
        raise ValueError("PNG is incomplete or differs from native screenshot viewport/encoding")
    channels = 3 if ihdr[3] == 2 else 4
    if len(zlib.decompress(pixels)) != 570 * (1 + 370 * channels): raise ValueError("PNG scanline population incomplete")
    return {**receipt, "width": 370, "height": 570, "structuralCheck": "PNG_CHUNKS_CRC_AND_SCANLINES_VERIFIED", "pixelMeaning": "INDEPENDENT_REVIEW_REQUIRED"}


def verify_webm(path, root):
    receipt = artifact_file(path, root); data = Path(path).read_bytes()
    def vint(offset, identity=False):
        if offset >= len(data) or data[offset] == 0: raise ValueError("truncated/invalid WebM integer")
        width, mask = 1, 0x80
        while not data[offset] & mask: width += 1; mask >>= 1
        if width > (4 if identity else 8) or offset + width > len(data): raise ValueError("truncated WebM integer")
        value = int.from_bytes(data[offset:offset+width], "big")
        if not identity: value &= (1 << (7 * width)) - 1
        return value, offset + width, not identity and value == (1 << (7 * width)) - 1
    def element(offset, limit):
        identity, offset, _ = vint(offset, True); size, offset, unknown = vint(offset)
        end = limit if unknown else offset + size
        if end > limit: raise ValueError("truncated WebM element")
        return identity, offset, end, unknown
    identity, start, end, unknown = element(0, len(data))
    if identity != 0x1a45dfa3 or unknown: raise ValueError("missing complete WebM EBML header")
    pos, doctype = start, None
    while pos < end:
        key, a, b, unk = element(pos, end)
        if unk: raise ValueError("invalid EBML header size")
        if key == 0x4282: doctype = data[a:b]
        pos = b
    if doctype != b"webm": raise ValueError("recording is not WebM")
    key, start, end, _ = element(end, len(data))
    if key != 0x18538067 or end != len(data): raise ValueError("incomplete WebM segment")
    pos, tracks, blocks = start, False, 0
    while pos < end:
        key, a, b, _ = element(pos, end)
        if key == 0x1654ae6b: tracks = b > a
        if key == 0x1f43b675:
            child = a
            while child < b:
                sub, c, d, _ = element(child, b)
                if sub == 0xa3 and d - c > 4: blocks += 1
                child = d
        pos = b
    if not tracks or blocks == 0: raise ValueError("WebM lacks tracks or nonempty recorded blocks")
    return {**receipt, "recordedBlockCount": blocks, "structuralCheck": "WEBM_ELEMENT_BOUNDS_TRACKS_AND_BLOCKS_VERIFIED", "frameDecodeAndPixels": "INDEPENDENT_REVIEW_REQUIRED"}


def settle_typography(page, trace, stage):
    page.wait_for_function("() => {const p=window.__r0007PublicDelivery,f=p?.fontState();return !!(f?.cssReady)}", polling=100)
    fonts = page.evaluate("() => window.__r0007PublicDelivery.awaitTypography()")
    if not fonts or fonts.get("readyPromiseFulfilled") is not True or fonts.get("fontStatus") != "loaded": raise AssertionError("native font readiness promise not established")
    page.wait_for_function("() => {const f=window.__r0007PublicDelivery.fontState();return !!(f.cssReady&&f.fontStatus==='loaded'&&f.fontObserver?.settled)}", polling=100)
    stable = page.evaluate("() => window.__r0007PublicDelivery.observeStable()")
    if not stable or stable.get("settled") is not True or stable.get("dirtyState") != "not-exposed" or len(stable.get("observations", [])) < 3:
        raise AssertionError("observable native receipt/geometry settlement missing")
    observations = stable["observations"][-3:]
    if len({canonical(o) for o in observations}) != 1 or any(not o.get("fontState", {}).get("fontObserver", {}).get("settled") for o in observations):
        raise AssertionError("stable observations lack unchanged deferred font-event settlement")
    trace.setdefault("setupObservations", []).append({"stage": stage, "typography": fonts, "stability": stable,
             "privateDirtyState": "not-exposed", "recoveryClaim": "EVENTUAL_ONLY_NOT_EXCLUSIVE_WAKEUP_CAUSALITY"})


def verify_acquisition_artifacts(trace, case, output):
    if not trace.get("observationExportVerified") or not trace.get("ownedCleanupReturned"):
        raise ValueError("complete observation export and owned closure are required")
    observations = trace.get("observations", {})
    final_fonts = observations.get("fontState", {})
    if (observations.get("fontSettlement", {}).get("settled") is not True or not final_fonts.get("cssReady")
        or final_fonts.get("fontStatus") != "loaded" or final_fonts.get("fontObserver", {}).get("settled") is not True):
        raise ValueError("final actual font-event export is unsettled")
    export = artifact_file(output / "observation-export.json", output)
    if canonical(json.loads((output / "observation-export.json").read_text())) != canonical(observations):
        raise ValueError("actual observation export differs from retained trace")
    if not observations.get("snapshots") or any(e.get("type") == "observation-error" for e in observations.get("events", [])):
        raise ValueError("actual observation population missing or contains observer errors")
    wanted = ["unavailable"] if case["mode"] == "missing" else ["unavailable", "actual-completed-consumer"] if case["mode"] == "recovery" else ["actual-completed-consumer"]
    if [c["name"] for c in trace["checkpoints"]] != wanted: raise ValueError("required checkpoint population incomplete")
    inventory = []
    for checkpoint in trace["checkpoints"]:
        name, snapshot = checkpoint["name"], checkpoint["snapshot"]
        if snapshot.get("fonts", {}).get("settlement", {}).get("settled") is not True:
            raise ValueError("checkpoint lacks actual deferred typed font-event settlement")
        if not any(canonical(s) == canonical(snapshot) for s in observations["snapshots"]): raise ValueError("checkpoint absent from actual observation export")
        presentation_path = output / (name + "-presentation.json")
        artifact_file(presentation_path, output)
        presentation = json.loads(presentation_path.read_text())
        image = verify_png(output / (name + ".png"), output)
        geometry = {selector: snapshot["dom"].get(selector, {}).get("geometry") for selector in [".c", ".nt", ".left", ".times", ".arc"]}
        if (presentation.get("renderReceiptStableAcrossScreenshot") is not True or presentation.get("geometryStableAcrossScreenshot") is not True
            or presentation.get("snapshotSha256") != sha(canonical(snapshot).encode()) or presentation.get("beforeReceipt") != snapshot["render"]
            or presentation.get("afterReceipt") != snapshot["render"] or presentation.get("screenshotSha256") != image["sha256"]
            or presentation.get("beforeGeometry") != geometry or presentation.get("afterGeometry") != geometry):
            raise ValueError("screenshot/presentation/actual receipt binding mismatch")
        terminal_fonts = presentation.get("fontStateAfterScreenshot", {})
        if not terminal_fonts.get("cssReady") or terminal_fonts.get("fontStatus") != "loaded" or terminal_fonts.get("fontObserver", {}).get("settled") is not True:
            raise ValueError("font lifecycle unsettled after final screenshot geometry")
        inventory.append({"checkpoint": name, "screenshot": image, "presentation": artifact_file(presentation_path, output)})
    identity = json.loads((output / "browser-identity.json").read_text())
    if identity.get("engine") != trace["engine"] or not identity.get("version") or not re.fullmatch(r"[0-9a-f]{64}", identity.get("executableSha256", "")):
        raise ValueError("actual browser identity incomplete")
    if not trace.get("ownedVideoPath") or not trace.get("videoSdkPathReturnedAfterClosure"): raise ValueError("owned SDK video path not returned after closure")
    video = verify_webm(trace["ownedVideoPath"], output)
    return {"checkpoints": inventory, "video": video, "observationExport": export, "browserIdentity": artifact_file(output / "browser-identity.json", output),
            "claim": "Complete structural acquisition evidence; independent pixel/playback review remains required"}


def assert_expected(snapshot, expected):
    if snapshot is None:
        raise AssertionError("no actual completed-render observation")
    for key, wanted in expected.get("equals", {}).items():
        actual = snapshot
        for part in key.split("/"):
            actual = actual[part]
        if actual != wanted:
            raise AssertionError(key + ": expected " + repr(wanted) + ", observed " + repr(actual))
    for field, mapping in [("contains", lambda a, b: b in a), ("regex", lambda a, b: re.fullmatch(b, a) is not None)]:
        for key, wanted in expected.get(field, {}).items():
            actual = snapshot
            for part in key.split("/"):
                actual = actual[part]
            if not mapping(actual, wanted):
                raise AssertionError(field + " actual consumer mismatch: " + key)
    for key, bounds in expected.get("numberRange", {}).items():
        actual = snapshot
        for part in key.split("/"):
            actual = actual[part]
        if isinstance(actual, bool) or not isinstance(actual, (float, int)) or not math.isfinite(actual) or not bounds[0] <= actual <= bounds[1]:
            raise AssertionError("actual consumer outside range: " + key)
    if len(snapshot["rows"]) != 6 or len({r["key"] for r in snapshot["rows"]}) != 6:
        raise AssertionError("actual timetable is not six distinct admitted event rows")
    if any(x in snapshot["dom"][s]["text"] for s in [".nt", ".left", ".times"] for x in ["NaN", "Infinity", "undefined"]):
        raise AssertionError("invalid visible prayer text")


def original_response(route, row, trace):
    """Transport original allowlisted bytes without permitting a redirect hop."""
    response = None
    row["transport"] = "BUFFERED_ROUTE_FETCH_MAX_REDIRECTS_0_ORIGINAL_RESPONSE_FULFILL"
    try:
        response = route.fetch(max_redirects=0, timeout=45000)
        row["actualStatus"] = response.status
        if 300 <= response.status < 400:
            row["policy"] = "BLOCKED_ALLOWLISTED_REDIRECT_NO_HOP"
            trace["blocked"].append(row)
            route.abort()
            return
        route.fulfill(response=response)
        row["originalResponseFulfilled"] = True
    except Exception as error:
        row["policy"] = "ORIGINAL_ALLOWLISTED_TRANSPORT_FAILED"
        row["failure"] = repr(error)
        trace["blocked"].append(row)
        try: route.abort()
        except Exception: pass
    finally:
        if response is not None:
            try:
                response.dispose()
                row["responseDisposeReturned"] = True
            except Exception as error:
                row["responseDisposeFailure"] = repr(error)
                trace["blocked"].append(row)
        row["finishedAtMonotonic"] = time.monotonic()


def acquire_case(playwright, engine, case, request, output, headed, font_observer_source=None):
    output.mkdir(parents=True, exist_ok=False)
    dump(output / "case-input.json", case)
    trace = {"caseId": case["caseId"], "engine": engine, "status": "STARTED", "startedUtc": now(), "network": [], "blocked": [],
             "pageErrors": [], "checkpoints": [], "firstPresentationClaim": "NOT_MADE", "liveProviderIncidenceClaim": "NOT_MADE",
             "custody": {"launchAttempted": False, "launchHandleReturned": False, "stages": [], "closeCalls": []},
             "transportClaim": "Original served bytes buffered through no-redirect route.fetch; native ingress timing is changed"}
    browser = context = page = video = None
    pending = []
    responses = []
    try:
        if not font_observer_source or sha(font_observer_source.encode()) != request["fontObserverSha256"]:
            raise ValueError("actual local font observer bytes differ from explicit request")
        trace["fontObserverSha256"] = request["fontObserverSha256"]
        family = getattr(playwright, engine)
        executable = os.environ.get("SALAH_BROWSER_EXECUTABLE") or family.executable_path
        options = {"headless": not headed, "executable_path": executable}
        if engine == "chromium":
            options.update(chromium_sandbox=True, args=["--disable-dev-shm-usage"])
        trace["custody"]["launchAttempted"] = True
        trace["custody"]["stages"].append({"stage": "launch-entered", "atUtc": now()})
        dump(output / "trace.json", trace)
        browser = family.launch(**options)
        trace["custody"]["launchHandleReturned"] = True
        trace["custody"]["stages"].append({"stage": "launch-handle-returned", "atUtc": now()})
        dump(output / "browser-identity.json", {"engine": engine, "version": browser.version, "headless": not headed,
             "executable": executable, "executableSha256": sha(Path(executable).read_bytes()), "os": platform.system(), "release": platform.release()})
        context = browser.new_context(viewport={"width": 370, "height": 570}, device_scale_factor=1, timezone_id="UTC",
                                      permissions=[], accept_downloads=False, service_workers="block", record_video_dir=str(output / "video"), record_video_size={"width": 370, "height": 570})
        trace["custody"]["stages"].append({"stage": "context-handle-returned", "atUtc": now()})
        epoch = int(datetime.fromisoformat(case["epoch"].replace("Z", "+00:00")).timestamp() * 1000)
        # One script guarantees early observer installation before our public
        # observation code; ordering across multiple init_scripts is undefined.
        context.add_init_script(font_observer_source + "\n" + INIT.replace("__EPOCH__", str(epoch)))

        def route_request(route):
            req = route.request
            url = urlsplit(req.url)
            row = {"url": req.url, "method": req.method, "resourceType": req.resource_type, "atMonotonic": time.monotonic()}
            trace["network"].append(row)
            if req.method not in {"GET", "HEAD"}:
                row["policy"] = "BLOCKED_METHOD"; trace["blocked"].append(row); route.abort(); return
            if url.scheme == "https" and url.hostname == "api.aladhan.com" and re.fullmatch(r"/v1/timings/(07|08)-09-2026", url.path):
                query = parse_qs(url.query)
                if any(query.get(k) != [v] for k, v in {"latitude": "40.71", "longitude": "-74.01", "method": "2", "school": "0"}.items()):
                    row["policy"] = "BLOCKED_UNEXPECTED_PROVIDER_INPUT"; trace["blocked"].append(row); route.abort(); return
                tomorrow = url.path.endswith("08-09-2026")
                if tomorrow and case["mode"] in {"missing", "recovery"}:
                    row["policy"] = "CONTROLLED_NEXT_RESPONSE_HELD_BEFORE_HEADERS"; pending.append((route, row)); return
                row["policy"] = "CONTROLLED_PROVIDER_HTTP_RESPONSE_NO_PROVIDER_CONTACT"
                route.fulfill(status=200, content_type="application/json", headers={"Access-Control-Allow-Origin": "*"}, body=json.dumps(case["tomorrowPayload"] if tomorrow else case["todayPayload"]))
                return
            if url.scheme == "https" and ((url.hostname == "api.open-meteo.com" and url.path == "/v1/forecast") or (url.hostname == "api.rainviewer.com" and url.path == "/public/weather-maps.json")):
                row["policy"] = "CONTROLLED_WEATHER_RADAR_OFFLINE_NO_PROVIDER_CONTACT"; route.abort("internetdisconnected"); return
            site = urlsplit(SITE)
            if url.scheme == "https" and url.netloc == site.netloc and url.path.startswith(site.path) and ".." not in unquote(url.path).split("/"):
                row["policy"] = "ACTUAL_PUBLIC_SITE_BYTES_UNMODIFIED"; original_response(route, row, trace); return
            if url.scheme == "https" and ((url.netloc == "fonts.googleapis.com" and url.path == "/css2" and req.resource_type == "stylesheet") or (url.netloc == "fonts.gstatic.com" and url.path.startswith("/s/") and req.resource_type == "font")):
                row["policy"] = "ACTUAL_NATIVE_FONT_FETCH"; original_response(route, row, trace); return
            if url.scheme == "https" and url.netloc == site.netloc and url.path == "/favicon.ico":
                row["policy"] = "STANDARD_FAVICON_NOT_A_RUNTIME_DELIVERY_CLAIM"; original_response(route, row, trace); return
            row["policy"] = "BLOCKED_UNRECOGNIZED_EXTERNAL_REQUEST"; trace["blocked"].append(row); route.abort()

        context.route("**/*", route_request)
        def refuse_socket(socket):
            trace["blocked"].append({"url": socket.url, "policy": "BLOCKED_UNRECOGNIZED_WEBSOCKET"})
            socket.close(code=1008, reason="No websocket admitted by controlled R0007 delivery probe")
        context.route_web_socket("**/*", refuse_socket)
        page = context.new_page()
        video = page.video
        trace["custody"]["stages"].append({"stage": "page-and-video-handles-returned", "atUtc": now()})
        page.set_default_timeout(15000)
        page.on("pageerror", lambda error: trace["pageErrors"].append(str(error)))
        page.on("response", lambda response: responses.append(response))
        url = (SITE if case["entry"] == "index.html" else urljoin(SITE, case["entry"])) + case["hash"]
        response = page.goto(url, wait_until="domcontentloaded", timeout=90000)
        if response is None or response.status != 200 or sha(response.body()) != request["expectedFiles"][case["entry"]]["sha256"]:
            raise AssertionError("actual public navigation source bytes differ from qualified tree")
        page.wait_for_function("() => {const p=window.__r0007PublicDelivery,s=p?.sample('current-readiness');return !!(s?.cache?.prayerLoaded&&s.render&&s.rows.length===6)}", polling=100)

        def capture(name, expected):
            snapshot = page.evaluate("name=>window.__r0007PublicDelivery.sample(name)", name)
            assert_expected(snapshot, expected)
            before = page.evaluate("() => window.__r0007PublicDelivery.receipt()")
            before_geometry = page.evaluate("() => window.__r0007PublicDelivery.geometry()")
            page.screenshot(path=str(output / (name + ".png")))
            after = page.evaluate("() => window.__r0007PublicDelivery.receipt()")
            after_geometry = page.evaluate("() => window.__r0007PublicDelivery.geometry()")
            final_fonts = page.evaluate("() => window.__r0007PublicDelivery.fontState()")
            expected_geometry = {selector: snapshot["dom"].get(selector, {}).get("geometry") for selector in [".c", ".nt", ".left", ".times", ".arc"]}
            image = verify_png(output / (name + ".png"), output)
            presentation = {"renderReceiptStableAcrossScreenshot": before == after == snapshot["render"],
                 "geometryStableAcrossScreenshot": before_geometry == after_geometry == expected_geometry,
                 "beforeReceipt": before, "afterReceipt": after, "beforeGeometry": before_geometry, "afterGeometry": after_geometry,
                 "snapshotSha256": sha(canonical(snapshot).encode()), "screenshotSha256": image["sha256"],
                 "fontStateAfterScreenshot": final_fonts,
                 "claim": "Actual checkpoint receipt/geometry binding; independent pixels and playback pending; no earliest-frame assertion"}
            dump(output / (name + "-presentation.json"), presentation)
            if not presentation["renderReceiptStableAcrossScreenshot"] or not presentation["geometryStableAcrossScreenshot"]:
                raise AssertionError("actual receipt or geometry changed between checkpoint and screenshot")
            trace["checkpoints"].append({"name": name, "snapshot": snapshot})

        if case["mode"] in {"missing", "recovery"}:
            deadline = time.monotonic() + 10
            while not pending and time.monotonic() < deadline:
                page.wait_for_timeout(25)
            if not pending:
                raise AssertionError("expected next-day ingress request was not observed")
            settle_typography(page, trace, "unavailable-before-any-release")
            capture("unavailable", case["expectedUnavailable"])
        if case["mode"] == "recovery":
            for route, row in list(pending):
                row["releasedAtMonotonic"] = time.monotonic()
                route.fulfill(status=200, content_type="application/json", headers={"Access-Control-Allow-Origin": "*"}, body=json.dumps(case["tomorrowPayload"]))
            pending.clear()
        if case["mode"] != "missing":
            page.wait_for_function("() => !!window.__r0007PublicDelivery.sample('tomorrow-admission-readiness')?.cache?.tomorrowLoaded", polling=100)
            # Observe native scheduling; never render, advance time, or assign data.
            page.wait_for_timeout(250)
            settle_typography(page, trace, "eventual-completed-consumer")
            capture("actual-completed-consumer", case["expectedFinal"])
        for r in responses:
            if urlsplit(r.url).path == urlsplit(SITE).path + "config.js":
                content = r.body()
                trace["actualConfigResponse"] = {"url": r.url, "bytes": len(content), "sha256": sha(content)}
        if case["entry"] == "index.html" and trace.get("actualConfigResponse", {}).get("sha256") != request["expectedFiles"]["config.js"]["sha256"]:
            raise AssertionError("actual consumed public config bytes differ from qualified tree")
        if trace["blocked"] or trace["pageErrors"]:
            raise AssertionError("blocked unknown request or page error; inspect original trace")
        page.wait_for_timeout(1000)
        trace["nativePresentationTailMs"] = 1000
        trace["assertionPredicatesMet"] = True
    except Exception as error:
        trace.update(status="FAILED_OR_UNVERIFIED", failure=repr(error))
    finally:
        if page:
            try:
                trace["observations"] = page.evaluate("() => {const p=window.__r0007PublicDelivery;return {snapshots:p.snapshots,events:p.events,started:p.started,fontState:p.fontState(),fontSettlement:window.__r0007FontSettlement.read()}}")
                trace["diagnosticSurfaceChanges"] = sum(s["diagnosticSurface"]["before"] != s["diagnosticSurface"]["after"] for s in trace["observations"]["snapshots"])
                dump(output / "observation-export.json", trace["observations"])
                artifact_file(output / "observation-export.json", output)
                trace["observationExportVerified"] = True
                if not trace.get("assertionPredicatesMet"):
                    page.screenshot(path=str(output / "failure.png"))
            except Exception as error:
                trace["exportFailure"] = repr(error)
        for route, row in pending:
            try:
                row["cleanup"] = "HELD_INGRESS_ABORTED_ON_CONTEXT_DISPOSAL"; route.abort()
            except Exception:
                pass
        cleanup_errors = []
        for label, owned in [("context", context), ("browser", browser)]:
            if owned is None: continue
            call = {"owner": label, "enteredUtc": now(), "returned": False}
            trace["custody"]["closeCalls"].append(call)
            try:
                owned.close()
                call.update(returned=True, returnedUtc=now())
            except Exception as error:
                call["failure"] = repr(error)
                cleanup_errors.append({"owner": label, "error": repr(error)})
        unknown_launch = trace["custody"]["launchAttempted"] and not trace["custody"]["launchHandleReturned"]
        trace["ownedCleanupReturned"] = not cleanup_errors and not unknown_launch
        trace["custody"]["status"] = "UNKNOWN_LAUNCH_CUSTODY_STOP_LATER_ACQUISITIONS" if unknown_launch else "OWNED_CLOSE_CALLS_RETURNED" if trace["ownedCleanupReturned"] else "OWNED_CLOSE_FAILED_STOP_LATER_ACQUISITIONS"
        trace["cleanupEvidence"] = "Owned SDK close calls; no independent OS process census claimed"
        if cleanup_errors:
            trace.update(cleanupFailures=cleanup_errors, status="FAILED_OR_UNVERIFIED")
        if video is not None and trace["ownedCleanupReturned"]:
            try:
                trace["ownedVideoPath"] = str(video.path())
                trace["videoSdkPathReturnedAfterClosure"] = True
            except Exception as error:
                trace["videoExportFailure"] = repr(error)
        trace["status"] = "FAILED_OR_UNVERIFIED"
        if trace.get("assertionPredicatesMet"):
            try:
                trace["artifactInventory"] = verify_acquisition_artifacts(trace, case, output)
                trace["status"] = "ASSERTIONS_MET_INDEPENDENT_PIXELS_PENDING"
            except Exception as error:
                trace["acquisitionVerificationFailure"] = repr(error)
        if trace["blocked"] or trace["pageErrors"]:
            trace["status"] = "FAILED_OR_UNVERIFIED"
        trace["finishedUtc"] = now()
        dump(output / "trace.json", trace)
    return trace


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--request", type=Path, required=True)
    p.add_argument("--cases", type=Path, required=True)
    p.add_argument("--font-observer", type=Path, required=True)
    p.add_argument("--repository-root", type=Path)
    p.add_argument("--output", type=Path)
    p.add_argument("--engine", choices=["chromium", "firefox"], action="append")
    p.add_argument("--case-id", action="append")
    p.add_argument("--headed", action="store_true")
    p.add_argument("--require-fetch-head", action="store_true")
    p.add_argument("--validate-only", action="store_true")
    p.add_argument("--template", action="store_true", help="Structural preparation only; never permits acquisition")
    args = p.parse_args(argv)
    request = json.loads(args.request.read_text(encoding="utf-8"))
    cases = json.loads(args.cases.read_text(encoding="utf-8"))
    validation = validate(request, cases, args.template)
    font_observer_bytes = args.font_observer.read_bytes()
    font_observer_source = font_observer_bytes.decode("utf-8")
    if (sha(Path(__file__).read_bytes()) != request["probeSha256"] or sha(args.cases.read_bytes()) != request["casesSha256"]
        or sha(font_observer_bytes) != request["fontObserverSha256"] or sha(font_observer_source.encode()) != request["fontObserverSha256"]):
        raise ValueError("probe/case/font observer bytes differ from explicit request")
    if args.validate_only:
        print(json.dumps(validation)); return 0
    if args.template or args.repository_root is None or args.output is None:
        p.error("acquisition requires bound request, repository-root and output")
    root, output = args.repository_root.resolve(), args.output.resolve()
    if output.is_relative_to(root) or output.exists():
        p.error("output must be a fresh directory outside repository-root")
    engines = args.engine or ["chromium", "firefox"]
    if len(engines) != len(set(engines)) or len(engines) > 1 and os.environ.get("SALAH_BROWSER_EXECUTABLE"):
        p.error("engines must be unique; an explicit executable requires a single engine")
    ids = args.case_id or cases["requiredCaseIds"]
    selected = [c for c in cases["cases"] if c["caseId"] in ids]
    if set(ids) != {c["caseId"] for c in selected}:
        p.error("unknown/empty public case selection")
    output.mkdir(parents=True)
    summary = {"schema": "r0007-public-delivery-acquisition/v1", "status": "PARTIAL", "startedUtc": now(), "results": [],
               "request": request, "probeSha256": request["probeSha256"], "casesSha256": request["casesSha256"], "fontObserverSha256": request["fontObserverSha256"],
               "claim": "Affected public consumer assertions only; pixels, Pages binding and whole-owner certificate remain separate"}
    exit_code = 1
    try:
        summary["gitBinding"] = verify_git(request, root, args.require_fetch_head)
        summary["servedFiles"] = served_readback(request, output)
        from playwright.sync_api import sync_playwright
        stopped = False
        with sync_playwright() as playwright:
            for engine in engines:
                for case in selected:
                    if stopped:
                        summary["results"].append({"engine": engine, "caseId": case["caseId"], "status": "UNATTEMPTED_OWNED_CLEANUP_UNVERIFIED"}); continue
                    result = acquire_case(playwright, engine, case, request, output / engine / case["caseId"], args.headed, font_observer_source)
                    summary["results"].append({"engine": engine, "caseId": case["caseId"], "status": result["status"]})
                    stopped = not result.get("ownedCleanupReturned")
                    dump(output / "summary.json", summary)
        # Recheck the affected source/config after acquisition; the original file
        # population's full readback remains retained without repeated large copies.
        final_request = {**request, "expectedFiles": {k: v for k, v in request["expectedFiles"].items() if k in {"index.html", "config.js"}}}
        after = output / "after"; after.mkdir()
        summary["servedFilesAfter"] = served_readback(final_request, after)
        summary["requiredPopulationObserved"] = set(engines) == {"chromium", "firefox"} and set(cases["requiredCaseIds"]).issubset(ids)
        exit_code = 0 if all(r["status"] == "ASSERTIONS_MET_INDEPENDENT_PIXELS_PENDING" for r in summary["results"]) else 1
    except Exception as error:
        summary["failure"] = repr(error)
    summary.update(exitCode=exit_code, finishedUtc=now())
    dump(output / "summary.json", summary)
    print("R0007_PUBLIC_RESULT " + json.dumps({"status": "PARTIAL_INDEPENDENT_PIXELS_REQUIRED", "exitCode": exit_code,
          "mergedMainSha": request["merge"]["mainSha"], "results": summary["results"], "certificateOrIssueClosure": "NOT_PERFORMED"}))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
