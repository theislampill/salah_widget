"""Pure source-bound F1 control helpers; no browser or astronomical clock."""
import base64
import hashlib
import re

def sha(data):return hashlib.sha256(data).hexdigest()
def validate_binding(identity,entry,expected_runtime,expected_entry):
 for name,value in [("runtime",expected_runtime),("entry",expected_entry)]:
  if not isinstance(value,str) or not re.fullmatch(r"[0-9a-f]{64}",value):raise ValueError("Explicit expected "+name+" SHA256 required")
 if identity.get("treeSha256")!=expected_runtime:raise ValueError("Expected runtime SHA256 does not match actual candidate")
 if sha(entry)!=expected_entry:raise ValueError("Expected entry SHA256 does not match actual candidate")

def entry_boundaries(entry):
 """Derive byte positions from actual generated source; never close a script."""
 tags=list(re.finditer(rb'<script\b[^>]*\bid\s*=\s*([\x22\x27])moon-initial-code\1[^>]*>',entry,re.I))
 if len(tags)!=1:raise ValueError("Unique actual Moon initial script required")
 opening=tags[0];start=opening.end();end=entry.find(b"</script>",start)
 if end<0:raise ValueError("Actual Moon initial closing tag missing")
 content=entry[start:end]
 receivers=list(re.finditer(rb'\bconst text=atob\("([A-Za-z0-9+/]+={0,2})"\),packed=new Uint8Array\(text\.length\);',content))
 if len(receivers)!=1:raise ValueError("Unique actual compact receiver literal required")
 match=receivers[0];encoded=match.group(1)
 try:receiver=base64.b64decode(encoded,validate=True)
 except ValueError as error:raise ValueError("Actual compact receiver literal is malformed") from error
 if len(encoded)<4 or base64.b64encode(receiver)!=encoded:raise ValueError("Actual compact receiver literal is not canonical")
 payload_start=start+match.start(1);payload_end=start+match.end(1)
 # Retain the previously sealed diagnostic's127 received base64 characters;
 # this is an interior transfer boundary, not a readiness/latency threshold.
 interior=payload_start+min(127,len(encoded)-1)
 if not payload_start<interior<payload_end:raise ValueError("Compact hold must be strictly inside the receiver")
 marker=b"\nboot();\n</script>"
 if entry.count(marker)!=1:raise ValueError("Unique actual native core completion marker required")
 core_cut=entry.index(marker);card=entry.find(b'<div class="c')
 if not opening.start()<interior<end<card<core_cut:raise ValueError("Actual head/card/native-core ownership order changed; re-review required")
 return {"schema":"actual-entry-first-paint-boundaries/1","entryBytes":len(entry),"entrySha256":sha(entry),
  "compactHead":{"cutByte":interior,"scriptStartByte":opening.start(),"scriptContentStartByte":start,"scriptContentEndByte":end,"scriptEndByteExclusive":end+9,"scriptBytes":len(content),"scriptSha256":sha(content),"scriptPrefixBytes":interior-start,"scriptPrefixSha256":sha(entry[start:interior]),"payloadStartByte":payload_start,"payloadEndByte":payload_end,"base64Characters":len(encoded),"receiverBytes":len(receiver),"receiverSha256":sha(receiver),"prefixSha256":sha(entry[:interior]),"suffixSha256":sha(entry[interior:]),"boundaryKind":"actual-compact-receiver-string-interior; no synthetic script completion"},
  "nativeCore":{"cutByte":core_cut,"marker":marker.decode(),"cardStartByte":card,"prefixSha256":sha(entry[:core_cut]),"suffixSha256":sha(entry[core_cut:]),"boundaryKind":"actual-native-core-script-unfinished-after-card-markup"}}

def original_case_checks(case,before,after,hidden=None):
 """Preserve the original five actual-entry oracle terms without reinterpretation."""
 checks={"actualCoreHeld":before["readyState"]=="loading" and not before["mainDeclared"] and not before["hostPresent"] and not before["previewPresent"],
  "validInitialScene":before["headStyle"] and before["hasBackground"] and before["headError"] is None and before["headAgeMs"]<30000}
 if case=="age":checks["ageBoundaryReached"]=after["headAgeMs"]>=35000 and after["at"]-before["at"]>=34000
 if case=="hidden-resume":checks["hiddenWithdrawal"]=not hidden["headStyle"]
 if case=="continuity":checks["validInitialContinuity"]=after["headStyle"] and after["styleSha256"]==before["styleSha256"]
 else:checks["revokedCssWithdrawn"]=not after["headStyle"]
 return checks

def recovery_checks(after_release,final,errors):
 return {"coreRecovery":after_release["mainDeclared"] and after_release["settings"] and len(after_release["prayerRows"])==6,
  "currentRecovery":final["moon"]["current"] and not final["headStyle"],"noPageErrors":not errors}

def lifecycle_audit(case,before,after):
 """Diagnostic custody never substitutes a live scene or an earlier timing origin."""
 old=before.get("headLifecycle");new=after.get("headLifecycle")
 if not isinstance(old,dict) or not isinstance(new,dict):return {"status":"UNKNOWN_OWNER_DIAGNOSTICS","checks":{},"reason":"Read-only lifecycle owner state missing; no metadata qualification"}
 checks={"originalSnapshotRetained":bool(old.get("snapshot")) and old.get("snapshot")==new.get("snapshot"),
  "originalFirstAdmissionRetained":bool(old.get("firstAdmission")) and old.get("firstAdmission")==new.get("firstAdmission")}
 if case=="continuity":checks["validHeadStillActive"]=new.get("active") is True and new.get("status")=="published"
 else:
  checks["revokedHeadInactive"]=new.get("active") is False and new.get("status")=="withdrawn"
  checks["oldValueAndMoonUnusable"]=after.get("headValuePresent") is False and after.get("headMoonPresent") is False
 return {"status":"PASS_DIAGNOSTIC_CUSTODY" if all(checks.values()) else "FAIL_DIAGNOSTIC_CUSTODY","checks":checks}


def compact_head_checks(boundary,before,after,transport):
 """Received actual prefix and unreleased suffix; availability is observed only."""
 snapshots=(before,after)
 return {"actualCompactHeaderHeld":all(s.get("readyState")=="loading" and s.get("initialReceiverPresent") is False and s.get("moonRuntimePresent") is False for s in snapshots),
  "actualReceivedScriptPrefixBound":all(s.get("compactScriptPresent") is True and s.get("compactScriptPrefixBytes")==boundary["scriptPrefixBytes"] and s.get("compactScriptPrefixSha256")==boundary["scriptPrefixSha256"] for s in snapshots),
  "unreleasedActualEntrySuffix":transport.get("singleActualEntryRequest") is True and transport.get("prefixFlushed") is True and transport.get("prefixBytes")==boundary["cutByte"] and transport.get("prefixSha256")==boundary["prefixSha256"] and transport.get("suffixReleased") is False and transport.get("holdExpired") is False}
