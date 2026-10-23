#!/usr/bin/env node
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const cp = require('node:child_process');
const http = require('node:http');
const https = require('node:https');
const crypto = require('node:crypto');
const {pipeline} = require('node:stream');
const channels = new Set(['jxmedia', 'official']);
const configPath = home => path.join(home, '.claude', 'deepseek-channel.json');
const readJSON = file => JSON.parse(fs.readFileSync(file, 'utf8'));
function save(home, value) {
  const file = configPath(home), temp = file + '.' + process.pid;
  fs.writeFileSync(temp, JSON.stringify(value, null, 2) + '\n', {mode:0o600});
  fs.renameSync(temp, file);
}
function config(home) {
  const value = readJSON(configPath(home));
  if (!channels.has(value.channel) || !Number.isInteger(value.port) || value.port < 1024 || value.port > 65535 || !value.jxmedia || !value.official) throw Error('Invalid channel configuration');
  return value;
}
function context(home) {
  const settings = readJSON(path.join(home, '.claude', 'settings.json'));
  const route = readJSON(path.join(home, '.cc-switch', 'live-state.json')).apps?.claude;
  const current = config(home);
  const base = new URL(settings.env?.ANTHROPIC_BASE_URL);
  if (route?.mode !== 'proxy' || route.proxy_route !== current.jxmedia || route.stack?.enabled || base.protocol !== 'http:' || base.hostname !== '127.0.0.1' || Number(base.port) === current.port) throw Error('Keep CC Switch routed to the original jxmedia provider');
  const token = settings.env?.ANTHROPIC_AUTH_TOKEN || settings.env?.ANTHROPIC_API_KEY;
  if (!token) throw Error('CC Switch local authentication is missing');
  return {current, base, token};
}
function authorized(headers, token) {
  const supplied = headers.authorization?.replace(/^Bearer /i, '') || headers['x-api-key'] || '';
  const left = Buffer.from(supplied), right = Buffer.from(token);
  return left.length === right.length && crypto.timingSafeEqual(left, right);
}
function target(model, channel) {
  return channel === 'official' && model?.replace(/\[1m\]$/i, '') === 'deepseek-v4.1-flash' ? 'official' : 'jxmedia';
}
function officialProvider(home, id) {
  // A single keyed lookup per official request; credentials stay in the existing private DB.
  const rows = JSON.parse(cp.execFileSync('sqlite3', ['-readonly', '-json', path.join(home, '.cc-switch', 'cc-switch.db'), "SELECT settings_config FROM providers WHERE app_type='claude' AND id='" + id.replaceAll("'", "''") + "'"], {encoding:'utf8', timeout:5000, maxBuffer:1024*1024}));
  const env = JSON.parse(rows[0]?.settings_config || '{}').env || {};
  if (env.ANTHROPIC_BASE_URL?.replace(/\/$/, '') !== 'https://api.deepseek.com/anthropic' || !env.ANTHROPIC_API_KEY) throw Error('Official DeepSeek API key/provider is unavailable');
  return env.ANTHROPIC_API_KEY;
}
function reply(response, status, message) {
  if (response.headersSent) return response.destroy();
  response.writeHead(status, {'content-type':'application/json'});
  response.end(JSON.stringify({type:'error', error:{type:'api_error', message}}));
}
async function handle(request, response, home, lookup = officialProvider, transport = (url, options, callback) => (url.protocol === 'https:' ? https : http).request(url, options, callback)) {
  let stage = 'configuration';
  try {
    const {current, base, token} = context(home);
    if (!authorized(request.headers, token)) return reply(response, 401, 'Local proxy authentication required');
    if (request.url === '/__deepseek_channel_health' && request.method === 'GET') {
      response.writeHead(200, {'x-deepseek-channel-router':'1'});
      return response.end('ok');
    }
    if (!['/v1/messages', '/v1/messages/count_tokens', '/v1/models'].includes(request.url?.split('?')[0]) || !['GET','POST'].includes(request.method)) return reply(response, 404, 'Unsupported proxy path');
    if (request.headers.origin) return reply(response, 403, 'Browser requests are not supported');
    stage = 'request';
    const chunks = []; let size = 0;
    for await (const chunk of request) {
      size += chunk.length;
      if (size > 32*1024*1024) return reply(response, 413, 'Request exceeds 32 MiB');
      chunks.push(chunk);
    }
    let body = Buffer.concat(chunks);
    const parsed = body.length ? JSON.parse(body) : {};
    const channel = target(parsed.model, current.channel);
    const destination = channel === 'official' ? new URL('https://api.deepseek.com/anthropic' + request.url) : new URL(request.url, base);
    const headers = {...request.headers};
    for (const key of ['host','connection','content-length','transfer-encoding','authorization','x-api-key','proxy-authorization']) delete headers[key];
    if (channel === 'official') {
      stage = 'official provider';
      headers['x-api-key'] = lookup(home, current.official);
      parsed.model = 'deepseek-flash';
      body = Buffer.from(JSON.stringify(parsed));
    } else headers.authorization = 'Bearer ' + token;
    if (body.length) headers['content-length'] = body.length;
    stage = 'upstream';
    const upstream = transport(destination, {method:request.method, headers}, incoming => {
      const responseHeaders = {...incoming.headers};
      for (const key of ['connection','transfer-encoding']) delete responseHeaders[key];
      response.writeHead(incoming.statusCode, responseHeaders);
      // Streaming retains backpressure; closing the terminal cancels the upstream call.
      pipeline(incoming, response, () => {});
    });
    response.on('close', () => upstream.destroy());
    upstream.setTimeout(600000, () => upstream.destroy(Error('timeout')));
    upstream.on('error', () => reply(response, 502, 'DeepSeek channel upstream failed; no automatic fallback'));
    upstream.end(body);
  } catch {
    reply(response, stage === 'request' ? 400 : 503, 'DeepSeek channel failed at ' + stage + '; check local provider configuration');
  }
}
function serve(home) {
  const {current} = context(home);
  const server = http.createServer((request, response) => { void handle(request, response, home); });
  server.maxConnections = 32;
  server.requestTimeout = 60000;
  server.headersTimeout = 15000;
  server.listen(current.port, '127.0.0.1');
  server.on('error', error => { console.error('DeepSeek local router: ' + error.code); process.exitCode = 1; });
  return server;
}
async function ensure(home) {
  const {current, token} = context(home);
  const probe = () => new Promise(resolve => {
    const request = http.get({host:'127.0.0.1', port:current.port, path:'/__deepseek_channel_health', headers:{authorization:'Bearer '+token}, timeout:1000}, response => {
      const own = response.headers['x-deepseek-channel-router'] === '1';
      response.resume(); resolve(own);
    });
    request.on('timeout', () => request.destroy()); request.on('error', () => resolve(false));
  });
  if (await probe()) return current;
  const child = cp.spawn(process.execPath, [__filename, 'serve'], {detached:true, stdio:'ignore', env:{...process.env, HOME:home}});
  child.unref();
  for (let attempt=0; attempt<20; attempt++) {
    await new Promise(resolve => setTimeout(resolve, 100));
    if (await probe()) return current;
  }
  throw Error('Local DeepSeek router did not start; port may be occupied');
}
async function main(args, home) {
  if (args[0] === 'serve') return serve(home);
  if (args[0] === 'configure' && args.length === 3) {
    save(home, {channel:'jxmedia', port:15722, jxmedia:args[1], official:args[2]});
    context(home);
  } else if (channels.has(args[0]) && args.length === 1) save(home, {...config(home), channel:args[0]});
  else if (args.length && !(args.length === 1 && args[0] === 'status')) throw Error('Usage: deepseek-channel [jxmedia|official|status]');
  console.log('DeepSeek channel: ' + config(home).channel + ' (GPT unchanged)');
}
module.exports = {configPath, save, config, context, authorized, target, handle, serve, ensure};
if (require.main === module) main(process.argv.slice(2), os.homedir()).catch(error => {console.error(error.message); process.exitCode=1;});
