// Cross-platform runner: no Unix shell glob expansion or npm dependency installation.
import fs from 'node:fs';import path from 'node:path';import {fileURLToPath} from 'node:url';import {spawnSync} from 'node:child_process';
const root=path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const tests=fs.readdirSync(path.join(root,'tests')).filter(f=>f.endsWith('.test.mjs')).sort().map(f=>path.join('tests',f));
const r=spawnSync(process.execPath,['--test',...tests],{cwd:root,stdio:'inherit'});process.exit(r.status??1);
