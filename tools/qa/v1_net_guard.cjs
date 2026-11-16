'use strict';
// R0036 V1 browser verification (issue 103, owner decision 2026-11-16): process-side network isolation for the Node
// driver. install() must run before any other module opens a connection. Every outbound attempt is classified; only
// loopback (127.0.0.0/8, ::1, "localhost") is allowed. A non-loopback attempt is refused BEFORE any socket is opened
// or any name is resolved, and is logged. Proxy variables are removed so no proxy is consulted.
const net=require('node:net'),tls=require('node:tls'),dns=require('node:dns'),http=require('node:http'),https=require('node:https');
const state={installed:false,refused:[],allowed:0,proxyVarsRemoved:[]};
const PROXY_VARS=['HTTP_PROXY','HTTPS_PROXY','ALL_PROXY','http_proxy','https_proxy','all_proxy','NO_PROXY','no_proxy','NODE_USE_ENV_PROXY'];
function isLoopback(host){
  if(host==null||host==='')return true;                                   // no host: a local pipe / unix socket path
  const h=String(host).replace(/^\[|\]$/g,'').toLowerCase();
  if(h==='localhost'||h==='::1')return true;
  if(net.isIPv4(h))return h.split('.')[0]==='127';
  if(h.startsWith('::ffff:'))return isLoopback(h.slice(7));
  return false;
}
function refuse(kind,target){const e=new Error('R0036 network isolation: refused non-loopback '+kind+' to '+target);e.code='ER0036_ISOLATED';
  state.refused.push({kind,target:String(target),at:Date.now()});return e;}
function targetOf(args){
  const a=args[0];
  if(Array.isArray(a))return targetOf(a);                                  // net internals pass [options, cb]
  if(a&&typeof a==='object'){if(a.path)return {host:null,label:'pipe:'+a.path};return {host:a.host??a.hostname??'localhost',label:(a.host??a.hostname??'localhost')+':'+a.port};}
  if(typeof a==='number')return {host:typeof args[1]==='string'?args[1]:'localhost',label:(typeof args[1]==='string'?args[1]:'localhost')+':'+a};
  if(typeof a==='string'&&!/^\d+$/.test(a))return {host:null,label:'pipe:'+a};
  return {host:'localhost',label:'localhost'};
}
function install(){
  if(state.installed)return state;
  for(const k of PROXY_VARS)if(k in process.env){delete process.env[k];state.proxyVarsRemoved.push(k);}
  const connect=net.Socket.prototype.connect;
  net.Socket.prototype.connect=function(...args){const t=targetOf(args);
    if(!isLoopback(t.host)){const e=refuse('socket',t.label);process.nextTick(()=>this.destroy(e));return this;}
    state.allowed++;return connect.apply(this,args);};
  const tlsConnect=tls.connect;
  tls.connect=function(...args){const t=targetOf(args);if(!isLoopback(t.host))throw refuse('tls',t.label);return tlsConnect.apply(this,args);};
  const lookup=dns.lookup;
  dns.lookup=function(host,...rest){if(!isLoopback(host)){const cb=rest.find(x=>typeof x==='function');const e=refuse('dns',host);if(cb)process.nextTick(()=>cb(e));return;}return lookup.call(this,host,...rest);};
  const plookup=dns.promises.lookup;
  dns.promises.lookup=function(host,...rest){if(!isLoopback(host))return Promise.reject(refuse('dns',host));return plookup.call(this,host,...rest);};
  for(const [name,mod] of [['http',http],['https',https]])for(const fn of ['request','get']){const orig=mod[fn];
    mod[fn]=function(input,...rest){let host;try{host=typeof input==='string'||input instanceof URL?new URL(String(input)).hostname:(input&&(input.hostname??input.host))||'localhost';}catch{host='?';}
      if(!isLoopback(host))throw refuse(name,String(input&&input.href||input&&input.host||input));return orig.call(this,input,...rest);};}
  if(typeof globalThis.fetch==='function'){const f=globalThis.fetch;globalThis.fetch=function(input,init){let u;try{u=new URL(String(input&&input.url||input));}catch{return Promise.reject(refuse('fetch',String(input)));}
    if(!isLoopback(u.hostname))return Promise.reject(refuse('fetch',u.href));return f.call(this,input,init);};}
  if(typeof globalThis.WebSocket==='function'){const W=globalThis.WebSocket;globalThis.WebSocket=function(url,...rest){const u=new URL(String(url));if(!isLoopback(u.hostname))throw refuse('websocket',u.href);return new W(url,...rest);};}
  state.installed=true;return state;
}
module.exports={install,isLoopback,state};
