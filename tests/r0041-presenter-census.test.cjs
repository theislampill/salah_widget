'use strict';
// R0041 (issue 143): ONE authoritative Moon presenter. Source census of every writer of Moon-disc visibility and
// occlusion in the authored sources. A new writer, or a writer that bypasses the runtime-owned detail handle
// (window.SalahMoonDetail, moon/src/moon-native.mjs), fails this test until it is reviewed and listed here.
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const root=path.join(__dirname,'..');
const files=['src/native/index.html','real-sky/native-sky.css','real-sky/native-host-hooks.js',
 ...fs.readdirSync(path.join(root,'real-sky')).filter(f=>/^native-.*\.mjs$/.test(f)).map(f=>'real-sky/'+f),
 ...fs.readdirSync(path.join(root,'moon/src')).filter(f=>f.endsWith('.mjs')).map(f=>'moon/src/'+f)];
const PATTERNS=[
 ['detail-clear',/SalahMoonDetail\??\.clear\(|\bdetail\.clear\(\)|mark\.detail\.clear\(\)|\binner\.clear\(\)|\.clearFor\(/g],
 ['detail-canvas-visibility',/cv\.style\.visibility\s*=|visibility:'(?:visible|hidden)'/g],
 ['css-moon-hide',/\.moon\{visibility:hidden\}|\.mphoto,[^{]*\.moccluder[^{]*\{visibility:hidden/g],
 ['css-mask-disc',/\.moon-mask-disc(?:\.mask-on)?\{/g],
 ['reveal-class-write',/classList\.(?:toggle|remove|add)\(\s*"(?:moon-ready|mask-on)"/g],
];
// Reviewed writers: file -> pattern -> count. Owner of each, per R0041 section B.5a.
const REVIEWED={
 'moon/src/moon-native.mjs':{'detail-clear':3},            // fallback() (presenter-owned withdrawal), the handle's clear() pass-through and its owner-scoped clearFor()
 'moon/src/moon-detail.mjs':{'detail-canvas-visibility':4}, // initial hidden, clear(), compose() show, state read (pinned source)
 'real-sky/native-host.mjs':{'detail-clear':1},            // L90 sky withdrawal -> through the handle (the SVG Moon takes over; witnessed: 0 absent frames)
 'real-sky/native-preview-host.mjs':{'detail-clear':3},    // preview clear (clearFor('atmospheric-preview'); full clear when awaiting input or without clearFor) and the awaiting re-entry -> through the handle
 'real-sky/native-first-paint.mjs':{'css-moon-hide':1},    // head first paint: SVG Moon hidden while the head Moon is composed (startup route)
 'real-sky/native-sky.css':{'css-moon-hide':2},            // composed / preview-ready: SVG Moon hidden while the detail presents
 'src/native/index.html':{'css-moon-hide':1,'css-mask-disc':2,'reveal-class-write':3}, // .c:not(.moon-ready) .moon; mask transition; updateSkySurface (2) + beginSkyScene remove
};
test('R41-CENSUS: every Moon visibility/occlusion writer is reviewed and routed through the one presenter',()=>{
 const found={};
 for(const f of files){const p=path.join(root,f);if(!fs.existsSync(p))continue;const text=fs.readFileSync(p,'utf8');
  for(const [name,re] of PATTERNS){const n=(text.match(re)||[]).length;if(n){(found[f]??={})[name]=n;}}}
 assert.deepEqual(found,REVIEWED,'Moon presenter census changed: '+JSON.stringify(found));
});
test('R41-CENSUS: external hosts reach the detail only through the runtime-owned handle',()=>{
 for(const f of ['real-sky/native-host.mjs','real-sky/native-preview-host.mjs','src/native/index.html']){
  const text=fs.readFileSync(path.join(root,f),'utf8');assert.ok(!/startMoonDetail\(/.test(text),f+' constructs its own detail owner');}
 const native=fs.readFileSync(path.join(root,'moon/src/moon-native.mjs'),'utf8');
 assert.match(native,/window\.SalahMoonDetail=detail;/,'the runtime publishes its handle as the one presenter');
});
