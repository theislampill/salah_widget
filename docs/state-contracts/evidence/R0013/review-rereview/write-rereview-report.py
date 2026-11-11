from pathlib import Path
import json,hashlib,datetime
root=Path('/workspace/scratch/b8359a7e27bf'); report=root/'recovery/r0013-review'; repo=root/'r0013'; recovery=root/'recovery'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
files=['install.sh','install.ps1','tests/install-discovery.py','tests/install-discovery.ps1','tests/install-discovery-mutations.py','tests/install-bash.py','tests/install-entry-bash.py','tests/install-entry-native.py','tests/install-entry.ps1','tests/install-mutations.py','tests/install-detectors.py','tests/install-builder.cjs','tests/install-native-receipts.py','tools/qualification/installer_native.py','.github/workflows/installer-native.yml','docs/state-contracts/R0013.md','docs/state-contracts/installer-coordination/PLAN.md','README.md']
hashes={name:sha(repo/name) for name in files}
receipt_names=['r0013-source-freeze-2.json','r0013-bash-final3.json','r0013-powershell-final3.json','r0013-bash-discovery-mutants-final3.json','r0013-powershell-discovery-mutants-final3.json','r0013-discovery-root-final.json','r0013-instrument-entry.json','r0013-instrument-mutants.json','r0013-mutation-oracle-regression.json','r0013-instrument-source.json','r0013-reconciliation/receipt.json']
evidence={name:sha(recovery/name) for name in receipt_names}
for name in ['preliminary-review.json','independent-rereview.json','strict-grammar-corpus.json','strict-grammar-result.json','parser-edge-repaired.json','delta-review-probes.py','strict-grammar-probe.ps1']:
 evidence['r0013-review/'+name]=sha(report/name)
findings=[
 {'id':'R13-REV-01','severity':'Important','original':'PowerShell permissive malformed JSON admits known absence and reaches staging/manual handoff','disposition':'RESOLVED in inspected source and supplemental local engineering evidence; native Windows qualification pending','source':'install.ps1 Test-StrictJson and Get-FirefoxExtensionStatus','evidence':['independent-rereview.json','parser-edge-repaired.json','strict-grammar-result.json','../r0013-powershell-final3.json','../r0013-powershell-discovery-mutants-final3.json'],'reason':'Contiguous strict token grammar validates before ConvertFrom-Json; malformed commas/comments/quotes/bare keys and incomplete structures become unknown/metadata-malformed. Independent actual main now exits1 with prompt only; healthy main still reaches stage/asset/preset/handoff. Actual strict helper agrees with 81 independent grammar expectations.'},
 {'id':'R13-REV-02','severity':'Important','original':'Duplicate inventory/property keys collapse legacy evidence in Bash and PowerShell','disposition':'RESOLVED in inspected source and supplemental local engineering evidence; applicable native qualification pending','source':'install.sh firefox_status unique_object/parse_constant; install.ps1 Test-StrictJson decoded HashSet keys','evidence':['independent-rereview.json','parser-edge-repaired.json','../r0013-bash-discovery-mutants-final3.json','../r0013-powershell-discovery-mutants-final3.json'],'reason':'Bash rejects repeated decoded dictionary keys and non-JSON constants before conversion; PS decodes string escapes and rejects OrdinalIgnoreCase key duplicates per object before conversion. Same original duplicate payload now stops actual Bash full file exit1/effects0/unchanged subject and PS actual main exit1/prompt only. Empty healthy controls remain useful; scoped repeated keys in different objects remain valid.'},
 {'id':'R13-REV-03','severity':'Important','original':'Native acquisition and per-entry pre-top-level readiness evidence missing','disposition':'RESOLVED as a source/instrument defect; actual native receipt qualification remains OPEN','source':'tests/install-entry-bash.py require_ready/fixture/bootstrap_negative; tests/install-discovery.py whole_entry; tools/qualification/installer_native.py acquisition','evidence':['../r0013-instrument-entry.json','../r0013-discovery-root-final.json','../r0013-instrument-source.json'],'reason':'Nonce is emitted only after all BASH_ENV interception definitions and checked by PID/nonce on every preview/terminal/discovery complete entry. Missing-nonce discriminator rejects qualification despite healthy preview. Snapshot/fixture records contain uid/gid/dev/inode/mode. Collector records actual host/tool/parent facts and separately describes output and effective tempfile parent mounts/volumes; acquisition failure is a gate error. Later bounded followup repaired initially omitted discovery entry checks and fixture-volume characterization.'},
 {'id':'R13-REV-04','severity':'Important','original':'Original Bash mutation driver can credit an unrelated failing row','disposition':'RESOLVED in inspected Bash mutation instrument and local discriminator evidence','source':'tests/install-mutations.py Bash expected/control map and exact name-set checks; tests/install-bash.py filter','evidence':['../r0013-instrument-mutants.json','../r0013-mutation-oracle-regression.json'],'reason':'For each mutation the exact healthy source must pass the adverse and paired control; mutant must fail exactly the named adverse row and preserve its healthy peer. Eight current mutant files and underlying receipts independently hash-match. Unchanged-source discriminator shows old false green on wrong-owner-home and repaired driver refuses credit with healthy baseline. The full wrong-owner fixture failure remains visible, not removed.'}
]
remaining=[
 'Bind this source-hash review to the final immutable candidate commit/tree, accepted parent da12688033c9481a3fea12e6aeed68b23a385694 and complete source/test/evidence manifest. Working review checkout remains dbf3370f39d569936ae74ad795638525b53ccd98 with frozen modifications; this report is not a Git-tree verdict.',
 'Run and inspect actual native Apple /bin/bash3.2 complete detector matrix, acquisition/readiness receipts, pipe/PTY normal/default/indices/dedup/source/store/fallback/NO_OPEN/refusal and path/retention joins. Disabled mapfile or Linux Bash5.2 is not Apple execution.',
 'Run and inspect native Windows PowerShell5.1 and supported7.6.6 on exact candidate bytes: strict parser/discovery/builders/selection/preview/normal entry plus applicable ASCII, ParseFile/UTF8ParseInput, selector object/path/caller and adverse encoding/comma controls. Linux PowerShell7.6.6 evidence is supplemental.',
 'Reconcile required original native parse-valid stdin/mapfile/cache and detector subshell/read-r/empty-array mutants with healthy controls, expected failed named rows, genuine native host/tool/file identities, and preserved RED evidence.',
 'Integrate all12 original parent rows,7 hierarchical residual child rows and14 ES13 rows into the current whole-contract ledger. Reuse unchanged earned proof at explicit scope; do not replace original residuals with the November discovery slice.',
 'Complete the planned docs-only update pinning both Bash reviewed-file and Windows examples to the newly qualified exact R13 source commit. Preserve R14 host/byte/policy instructions, terminal/EOF/path limits, manual import/dashboard semantics, configured preset/cache guidance, and builder agreement. Review final rendered/copied commands and public bytes.',
 'Preserve actual R0015 artifact-admission/custody and R0016 preview interfaces; do not conflate interface proof with entire issue completion. The local wrong-owner-home fixture has an invalid /tmp foreign-owner premise and remains25/26; actual foreign-UID proof is still a separate native interface gate.',
 'Complete own-branch publication/readback and nonclosing Implements#19 PR, exact-source native receipts and current independent binding. Follow parent governance; this review grants no merge authority.',
 'Verify all required campaign predecessor ordering or approved disjointness and the exact owner approval before merge. Then verify actual main/PR/integration state and final raw/Pages/rendered/copy delivery bytes and scope binding.',
 'Publish/read back the whole-owner certificate only after all required rows are earned; deliberate completed issue closure and formal lifecycle/currentness gates remain parent-owned.'
]
base=json.loads((recovery/'r0013_contract_matrix.json').read_text())
coverage=[]
for group in ['originalRows','residualChildRows','amendmentRows']:
 for r in base[group]:
  rid=r['id']
  if rid in ['19-05','R0013-A01','R0013-A03','R0013-A04','ES13-13']:
   status='Native host/evidence gate OPEN; revised source and local instruments reviewed'
  elif rid in ['19-09','19-12','R0013-A05','R0013-A06','R0013-A07']:
   status='Source/document engineering reviewed; final pins/rendered/public delivery OPEN'
  elif rid in ['19-08','19-11']:
   status='Preserved source and narrow builder controls reviewed; final exact delivery rebinding OPEN'
  elif rid=='ES13-14':
   status='Full denominator retained; integrated final ledger/certificate/closure OPEN'
  else:
   status='Local/static candidate evidence reviewed without new unresolved defect; applicable native/delivery rebinding OPEN'
  coverage.append({'id':rid,'parent':r.get('parent'),'requirement':r['requirement'],'reviewScope':status})
artifact={'schema':'r0013-independent-engineering-rereview/1','reviewer':'/root/r0013_review','capturedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'authority':'Ordinary independent engineering review; no audit-assess/lifecycle, readiness, merge or closure authority','disposition':'No unresolved Critical/Important/Minor engineering finding identified in inspected changed source and local evidence. Four prior Important findings resolved at the stated source/local scope. Candidate may advance to parent-owned native qualification; whole contract NOT complete.','sourceHashes':hashes,'freezeNote':'Freeze2 installers unchanged; subsequent parent-owned discovery readiness and effective-temp-volume instrument deltas separately hashed here. Final candidate tree not yet supplied.','baselineCommit':'dbf3370f39d569936ae74ad795638525b53ccd98','baselineTree':'a29866be1f9f05e7c11e6cd51570d888bdcc0e80','reconciledParent':'da12688033c9481a3fea12e6aeed68b23a385694','findings':findings,'newCriticalFindings':[],'newImportantFindings':[],'newMinorFindings':[],'evidenceHashes':evidence,'independentChecks':json.loads((report/'independent-rereview.json').read_text()),'reviewedReceiptSummary':{'BashDiscovery':'final3 76/76; later root final76/76 adds per-entry readiness observations','PowerShellDiscovery':'final3 68/68; Linux7.6.6 only','BashDiscoveryMutants':'12 named mutants plus exact-source paired controls; actual mutant file hashes and receipt source hashes match','PowerShellDiscoveryMutants':'11 named mutants plus exact-source paired controls; actual mutant file hashes and receipt source hashes match','BashOriginalEntry':'24/24 including missing-readiness negative control','BashOriginalMutants':'8/8; actual files/underlying receipt identities, exact adverse rows and healthy controls checked','UnchangedSourceOracle':'old falsely credits unrelated wrong-owner failure; repaired returns detected=false with healthy source pass'},'declinedToJudge':['Actual Apple or Windows runtime/filesystem behavior until candidate native receipts arrive.','Final candidate commit/tree/currentness until supplied and independently rebound.','Public rendering/copied commands/raw delivery, own PR state, merge, completed issue closure: not executed by reviewer and not supplied in final form.','Formal governor/lifecycle acceptance: absent formal routed envelope and explicitly outside delegated authority.','Dedicated native foreign-UID custody result, and whole R0015/R0016 owner readiness: separate interface-owner evidence still required.'],'remainingContractGates':remaining,'fullDenominatorCoverage':coverage,'mutationPolicy':'No product/source/index/branch/governor/remote writes. Probe artifacts are attributed under recovery/r0013-review; disposable complete-entry fixtures under owned /tmp roots. Existing RED reports retained unchanged.'}
(report/'rereview.json').write_text(json.dumps(artifact,indent=2)+'\n')
md='''# R0013 independent engineering rereview

Reviewer: `/root/r0013_review`. Ordinary attributed engineering review, with no lifecycle, merge or closure authority.

**Engineering disposition:** no unresolved Critical, Important or Minor finding was identified in the inspected repair and local evidence. The four prior Important findings are resolved at the source/instrument scope below. **The whole R0013 contract remains incomplete:** actual Apple and Windows qualification, immutable candidate binding, final documentation and delivery, integration authorization, and closure gates remain open.

## Inspected source binding

| Source | SHA256 |
| --- | --- |
'''
for name in ['install.sh','install.ps1','tests/install-discovery.py','tests/install-entry-bash.py','tests/install-mutations.py','tools/qualification/installer_native.py']:
 md+=f'| `{name}` | `{hashes[name]}` |\n'
md+='''
The installers match `r0013-source-freeze-2.json`. The later discovery readiness and temporary-filesystem acquisition corrections are bound independently above. The companion JSON records every reviewed source/test/document hash and evidence hash. The review checkout remains based on `dbf3370f39d569936ae74ad795638525b53ccd98`; the parent reconciliation receipt establishes unchanged installer/builder ancestry at accepted main `da12688033c9481a3fea12e6aeed68b23a385694` and the clean README weather-line merge. The final publication commit and tree have not yet been supplied. This report therefore binds inspected bytes, not an unseen candidate tree.

## Finding dispositions

'''
for f in findings:
 md+=f"### {f['id']} — {f['severity']}, resolved within stated scope\n\n**Original finding:** {f['original']}.\n\n{f['reason']}\n\n**Disposition:** {f['disposition']}.\n\n"
md+='''## Independent repair checks

The independent probes reuse the original finding payloads and actual source consumers. Source hashes were checked before and after all runs and did not change. These runs used Linux Bash5.2 and PowerShell7.6.6; they do not establish native Apple or Windows behavior.

| Check | Observation |
| --- | --- |
| Actual PowerShell strict validator versus independent standard JSON parser expectations | 81/81 agree:25 valid and56 invalid. Cases cover nesting/frame closure, separators, whitespace, numeric forms, string escapes, duplicate decoded/case-folded keys and valid repeated keys in distinct object scopes. |
| Original PowerShell parser edge probe | All9 expected dispositions: malformed grammar and ambiguous/root-array metadata held; healthy supported inventory remains eligible. The unrelated version field does not override the documented supported structural contract. |
| Same actual PowerShell main-body probe used for original RED | Valid-empty exits0 and reaches staging, asset/preset, clipboard and manual handoff spies. Legacy, malformed bare-key and duplicate-inventory cases exit1 with the prompt spy only; no installation action occurs. |
| Same actual Bash complete-file PTY probe used for original RED | Valid-empty exits0 with19 intercepted/contained effects. Legacy and duplicate-inventory exit1 with0 effects and unchanged subject snapshots. Every run has its own validated readiness nonce and native fixture identity record. |

All browser profile bytes stayed unchanged. The PowerShell probe executes actual main-body bytes with fixture configuration and external-boundary spies; the Bash probe executes the actual full file through its pipe/PTY harness. The initial invalid `/workspace` positive fixture is preserved in the preliminary evidence and earns no rejection credit; repaired Bash probes use the trusted owned `/tmp` fixture parent.

## Reviewed local receipts and causal checks

| Receipt | Reviewed result |
| --- | --- |
| `r0013-bash-final3.json` and later `r0013-discovery-root-final.json` | 76/76 each. The later receipt includes readiness/acquisition for every discovery complete-entry row. |
| `r0013-powershell-final3.json` | 68/68, supplemental Linux PowerShell7.6.6. |
| `r0013-bash-discovery-mutants-final3.json` | 12 intended mutants detected plus exact-source controls. |
| `r0013-powershell-discovery-mutants-final3.json` | 11 intended mutants detected plus exact-source controls. |
| `r0013-instrument-entry.json` | 24/24, including missing-nonce qualification rejection. |
| `r0013-instrument-mutants.json` | 8/8 original Bash mutants with named adverse and paired healthy controls. |
| `r0013-mutation-oracle-regression.json` | Identical candidate bytes receive false mutation credit from the old runner and correctly receive no credit from the repaired runner. |

For all31 mutant entries I inspected the referenced actual mutant files and underlying JSON receipts: hashes match, receipt source hashes match, the named adverse rows fail, and the paired positive controls pass. The strict grammar and duplicate guards are consequently tested through their actual parser and main callers. This review does not rely solely on aggregate PASS labels.

The earlier local helper25/26 result remains an honest fixture limitation: its `wrong-owner-home` case treats `/tmp` as foreign-owned, whereas this host's `/tmp` has the current UID. It is neither a product success nor evidence of a product custody failure. The corrected mutation oracle prevents that unrelated failure from satisfying another mutation. A native foreign-UID custody proof is still required at the R0015 interface.

## Preserved contract scope

The earlier full review remains part of this report. All five Bash target-record reads consume the appended knowledge fields; preview, pre-staging eligibility and dispatch derive one guard with legacy precedence. PowerShell builders retain knowledge/reason/evidence/source and actual main rechecks the same derived eligibility before effects. No-Python Firefox heuristics remain unknown while retaining conservative hints, and an independent Chromium peer stays useful. Delimiter/newline handling preserves record identity or explicitly excludes unsupported paths. Original FD3 input, path-only stdout, per-attempt staging/cache and R0014 selector mechanisms remain preserved at the reviewed interface scope.

The companion JSON retains all12 original parent rows,7 hierarchical residual children and14 ES13 rows with their remaining qualification scope. It does not count child rows as separate owner duties or treat the discovery slice as owner completion.

## Remaining whole-contract gates

'''
for r in remaining:md+='- '+r+'\n'
md+='''
## Declined judgments

I decline a native Apple/Windows runtime verdict because no candidate native receipt has been supplied. I decline a final tree/currentness verdict until the parent supplies the publication snapshot. I decline public rendering/copied-command/delivery, PR integration, owner approval, certificate or closure judgments because these are not final or executed in this review. Formal governor/lifecycle acceptance and whole R0015/R0016 readiness remain outside this delegated role.

The reviewer made no source, index, branch, governor or remote changes. The original RED evidence and preliminary report are preserved; this report supersedes their engineering finding dispositions only at the exact scopes stated above.
'''
(report/'rereview.md').write_text(md)
print(json.dumps({'report':str(report/'rereview.json'),'sha256':sha(report/'rereview.json'),'markdown':str(report/'rereview.md'),'markdownSha256':sha(report/'rereview.md'),'sourceHashes':{k:hashes[k] for k in ['install.sh','install.ps1']}}))
