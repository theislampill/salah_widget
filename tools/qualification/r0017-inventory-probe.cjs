#!/usr/bin/env node
'use strict';
// Read-only setup discriminator. No browser, driver, installation or product run.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const os = require('node:os');
const {spawn} = require('node:child_process');
const sha = b => crypto.createHash('sha256').update(b).digest('hex');
const options = {};
for (let i = 2; i < process.argv.length; i += 2) {
  if (!/^--[a-z-]+$/.test(process.argv[i]) || !process.argv[i + 1]) throw Error('Paired named arguments required');
  const key = process.argv[i].slice(2);
  if (Object.hasOwn(options, key)) throw Error('Duplicate argument: ' + key);
  options[key] = process.argv[i + 1];
}
const allowed = ['base-file', 'base-sha', 'engine', 'out', 'describe'];
if (Object.keys(options).some(k => !allowed.includes(k))) throw Error('Unknown option');
if (!['winps', 'pwsh'].includes(options.engine)) throw Error('Explicit engine winps or pwsh required');
if (!/^[a-f0-9]{64}$/.test(options['base-sha'] || '') || !options['base-file']) throw Error('Exact base source binding required');
const baseBytes = fs.readFileSync(options['base-file']);
if (sha(baseBytes) !== options['base-sha']) throw Error('BASE_SOURCE_MISMATCH before process acquisition');
const base = baseBytes.toString('utf8');
const begin = 'function processTree(pids){', end = '\nfunction sameProcess(';
if (base.split(begin).length !== 2 || base.split(end).length !== 2) throw Error('Unique original processTree boundaries required');
const fragment = base.slice(base.indexOf(begin), base.indexOf(end, base.indexOf(begin)));
let originalCall;
const original = new Function('execFileSync', 'fail', fragment + '\nreturn processTree;')((...args) => {
  if (originalCall) throw Error('Multiple original commands');
  originalCall = args;
  return '[]';
}, message => { throw Error(message); });
original([process.pid]);
if (originalCall?.[0] !== 'powershell.exe' || originalCall[2]?.timeout !== 5000) throw Error('Original query/deadline changed');
const originalArgs = originalCall[1];
if (JSON.stringify(originalArgs.slice(0, 4)) !== JSON.stringify(['-NoLogo', '-NoProfile', '-NonInteractive', '-Command'])) throw Error('Original command envelope changed');
const originalScript = originalArgs[4];
const query = '$all=@(Get-CimInstance Win32_Process);';
if (originalScript.split(query).length !== 2) throw Error('Unique original CIM query required');
// Markers distinguish entering PowerShell from the CIM call. They are a declared
// measurement change, never a replay of the earlier uninstrumented invocation.
const before = '[Console]::Error.WriteLine((@{stage="before-cim";version=$PSVersionTable.PSVersion.ToString();utc=[DateTimeOffset]::UtcNow.ToString("o")} | ConvertTo-Json -Compress)); [Console]::Error.Flush(); $r0017QueryClock=[Diagnostics.Stopwatch]::StartNew(); ';
const after = ' [Console]::Error.WriteLine((@{stage="after-cim";elapsedMs=$r0017QueryClock.Elapsed.TotalMilliseconds;count=$all.Count;utc=[DateTimeOffset]::UtcNow.ToString("o")} | ConvertTo-Json -Compress)); [Console]::Error.Flush(); ';
const script = originalScript.replace(query, before + query + after);
const plan = {
  schema: 'r0017-inventory-discriminator/v1', engine: options.engine,
  baseSha256: sha(baseBytes), processTreeSha256: sha(fragment),
  originalScriptSha256: sha(originalScript), markedScriptSha256: sha(script),
  seed: {pid: process.pid, kind: 'this owned diagnostic Node process'},
  queryDeadlineMs: 5000, cleanupDeadlineMs: 5000,
  queriesPlanned: 1, browserExecutions: 0, productExecutions: 0,
  limitations: ['One query by this diagnostic without diagnostic warmup; no cold-cache, universal speed or root-cause claim.', 'Markers add measurement work; previous invocations are not reclassified.', 'Separate jobs use different hosts; they are not a randomized performance comparison.']
};
if (options.describe) {
  if (options.describe !== 'yes') throw Error('describe must equal yes');
  console.log(JSON.stringify({...plan, status: 'DESCRIBED_ONLY_NO_PROCESS'}, null, 2));
} else {
  if (!options.out) throw Error('Fresh output path required');
  const out = path.resolve(options.out);
  if (fs.existsSync(out) && fs.readdirSync(out).length) throw Error('Refusing existing evidence');
  fs.mkdirSync(out, {recursive: true});
  const result = {...plan, status: 'STARTED', startedUtc: new Date().toISOString(),
    host: {platform: process.platform, arch: process.arch, release: os.release(), node: process.version,
      env: Object.fromEntries(['GITHUB_SHA', 'GITHUB_RUN_ID', 'GITHUB_RUN_ATTEMPT', 'RUNNER_NAME', 'RUNNER_OS', 'ImageVersion'].map(k => [k, process.env[k] || null]))},
    queryPid: null, queryAcquired: false, stdout: '', stderr: '', chunks: [], containment: {ok: false}, errors: []};
  const write = () => fs.writeFileSync(path.join(out, 'inventory-probe.json'), JSON.stringify(result, null, 2) + '\n');
  fs.writeFileSync(path.join(out, 'original-processTree.cjs'), fragment + '\n');
  fs.writeFileSync(path.join(out, 'original-query.ps1'), originalScript + '\n');
  fs.writeFileSync(path.join(out, 'marked-query.ps1'), script + '\n');
  fs.copyFileSync(__filename, path.join(out, 'inventory-probe.cjs'));
  write();
  (async () => {
    if (process.platform !== 'win32') throw Error('NATIVE_WINDOWS_REQUIRED; no process acquired');
    const executable = options.engine === 'winps'
      ? path.join(process.env.SystemRoot || 'C:\\Windows', 'System32', 'WindowsPowerShell', 'v1.0', 'powershell.exe')
      : path.join(process.env.ProgramFiles || 'C:\\Program Files', 'PowerShell', '7', 'pwsh.exe');
    result.executable = {path: executable, sha256: sha(fs.readFileSync(executable))};
    const started = performance.now();
    const child = spawn(executable, [...originalArgs.slice(0, 4), script], {windowsHide: true, stdio: ['ignore', 'pipe', 'pipe']});
    result.queryPid = child.pid ?? null;
    result.queryAcquired = Number.isInteger(child.pid);
    let closed = false, timer, cleanupTimer, killed = false, resolveTerminal;
    const stop = reason => {
      if (closed || killed) return;
      killed = true; clearTimeout(timer);
      const cleanupDeadline = performance.now() + 5000;
      const checkCleanup = () => {
        if (closed) return;
        const remaining = cleanupDeadline - performance.now();
        if (remaining > 0) { cleanupTimer = setTimeout(checkCleanup, remaining); return; }
        result.errors.push({stage: 'cleanup', error: 'Original process handle did not report close within5000ms after owned stop'}); resolveTerminal();
      };
      cleanupTimer = setTimeout(checkCleanup, Math.max(0, cleanupDeadline - performance.now()));
      result.stop = {reason, atMs: performance.now() - started, method: 'original spawned ChildProcess handle', requested: false};
      try { result.stop.requested = child.kill('SIGTERM'); } catch (e) { result.errors.push({stage: 'owned-stop', error: String(e)}); }
    };
    const terminal = new Promise(resolve => {
      resolveTerminal = resolve;
      child.on('error', e => { result.errors.push({stage: 'spawn', error: String(e)}); });
      child.once('exit', (code, signal) => { result.exit = {code, signal, observedMs: performance.now() - started}; });
      child.once('close', (code, signal) => {
        closed = true; clearTimeout(timer); clearTimeout(cleanupTimer);
        result.close = {code, signal, observedMs: performance.now() - started}; resolve();
      });
      for (const stream of ['stdout', 'stderr']) child[stream].on('data', bytes => {
        result.chunks.push({stream, observedMs: performance.now() - started, bytes: bytes.length});
        if (Buffer.byteLength(result[stream]) + bytes.length > 262144) { result.errors.push({stage: 'capture', error: stream + ' exceeds declared256KiB capture bound'}); stop('CAPTURE_BOUND_EXCEEDED'); }
        else result[stream] += bytes.toString('utf8');
      });
      timer = setTimeout(() => {
        result.queryDeadlineObservedMs = performance.now() - started;
        stop('QUERY_DEADLINE_5000MS');
      }, Math.max(0, 5000 - (performance.now() - started)));
    });
    await terminal;
    const noProcess = !result.queryAcquired && result.queryPid === null;
    result.containment = {ok: closed || noProcess, queryProcessClosed: closed, noProcessAcquired: noProcess,
      method: 'original handle exit/close event; the script launches no subordinate executable', broadKill: false};
    result.completedWithin5000ms = closed && !killed && result.close.code === 0 && result.close.observedMs < 5000;
    if (result.completedWithin5000ms) {
      try {
        const rows = JSON.parse(result.stdout.replace(/^\uFEFF/, ''));
        if (!Array.isArray(rows) || rows.some(r => !Number.isInteger(r.ProcessId) || !Number.isInteger(r.ParentProcessId) || typeof r.CreationDate !== 'string' || !Number.isFinite(Date.parse(r.CreationDate)))) throw Error('Invalid original process identity schema');
        result.rows = rows;
        result.seedObserved = rows.some(r => r.ProcessId === process.pid && /^node(?:\.exe)?$/i.test(r.Name));
        result.queryObserved = rows.some(r => r.ProcessId === child.pid && r.ParentProcessId === process.pid);
      } catch (e) { result.errors.push({stage: 'query-result', error: String(e)}); }
    }
    result.status = result.completedWithin5000ms && result.seedObserved && result.queryObserved && !result.errors.length && result.containment.ok
      ? 'CAPABILITY_OBSERVED_WITHIN_ORIGINAL_BOUND' : 'CAPABILITY_NOT_ESTABLISHED';
    result.finishedUtc = new Date().toISOString();
    write();
    // A contained negative is successful diagnostic collection, never a passing
    // capability or application result. The next serial job gates containment.
    process.exitCode = result.containment.ok ? 0 : 1;
    if (!closed && result.queryAcquired) { child.unref(); child.stdout.destroy(); child.stderr.destroy(); }
  })().catch(e => {
    result.errors.push({stage: 'setup', error: String(e.stack || e)});
    result.status = 'SETUP_CAPABILITY_ERROR';
    result.containment = {ok: !result.queryAcquired, noProcessAcquired: !result.queryAcquired};
    result.finishedUtc = new Date().toISOString(); write(); process.exitCode = 1;
  });
}
