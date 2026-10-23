const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs'), os = require('node:os'), path = require('node:path'), http = require('node:http');
const {save, target, authorized, handle} = require('./deepseek-channel.cjs');
const listen = server => new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const close = server => new Promise(resolve => {server.closeAllConnections(); server.close(resolve);});
test('malformed private settings never appear in CLI error output', () => {
  const home=fs.mkdtempSync(path.join(os.tmpdir(),'deepseek-private-error-'));
  try {
    fs.mkdirSync(path.join(home,'.claude'));
    fs.writeFileSync(path.join(home,'.claude','settings.json'),'{"key":"private-key-test" BROKEN');
    const result=require('node:child_process').spawnSync(process.execPath,[path.join(__dirname,'deepseek-channel.cjs'),'serve'],{encoding:'utf8',env:{...process.env,HOME:home}});
    assert.equal(result.status,1);assert(!result.stderr.includes('private-key-test'));assert.match(result.stderr,/setup failed/);
  } finally {fs.rmSync(home,{recursive:true,force:true});}
});
test('only exact DeepSeek model selects official; GPT and unrelated names retain jxmedia', () => {
  for (const model of ['gpt-6-astra','gpt-6.1-sol','deepseek-v4-pro','claude-haiku-4-5']) assert.equal(target(model,'official'),'jxmedia');
  assert.equal(target('deepseek-v4.1-flash','official'),'official');
  assert.equal(target('deepseek-v4.1-flash[1M]','official'),'official');
  assert.equal(target('deepseek-v4.1-flash','jxmedia'),'jxmedia');
  assert.equal(authorized({authorization:'Bearer secret'},'secret'),true);
  assert.equal(authorized({'x-api-key':'wrong'},'secret'),false);
});
test('manual changes are read per request; streaming and credentials remain isolated', async () => {
  const home = fs.mkdtempSync(path.join(os.tmpdir(),'deepseek-channel-test-'));
  for (const name of ['.claude','.cc-switch']) fs.mkdirSync(path.join(home,name));
  const captured = [];
  const upstream = http.createServer(async (request,response) => {
    const chunks=[]; for await (const chunk of request) chunks.push(chunk);
    captured.push({body:JSON.parse(Buffer.concat(chunks)),headers:request.headers});
    response.writeHead(200,{'content-type':'text/event-stream'});
    response.write('event: message_start\ndata: {}\n\n');
    response.end('event: message_stop\ndata: {}\n\n');
  });
  await listen(upstream);
  const upstreamURL = 'http://127.0.0.1:'+upstream.address().port;
  const routeFile = path.join(home,'.cc-switch','live-state.json');
  fs.writeFileSync(routeFile,JSON.stringify({apps:{claude:{mode:'proxy',proxy_route:'jx'}}}));
  fs.writeFileSync(path.join(home,'.claude','settings.json'),JSON.stringify({env:{ANTHROPIC_BASE_URL:upstreamURL,ANTHROPIC_AUTH_TOKEN:'local-secret'}}));
  const change = channel => save(home,{channel,port:15722,jxmedia:'jx',official:'ds'});
  change('jxmedia');
  const destinations=[];
  const router = http.createServer((request,response) => void handle(request,response,home,()=> 'official-secret',(url,options,callback)=>{
    destinations.push(url.href); return http.request(upstreamURL,options,callback);
  }));
  await listen(router);
  const url='http://127.0.0.1:'+router.address().port+'/v1/messages';
  const call = (model,token='local-secret') => fetch(url,{method:'POST',headers:{authorization:'Bearer '+token,'x-api-key':'stale-key','content-type':'application/json'},body:JSON.stringify({model,max_tokens:16,stream:true,messages:[{role:'user',content:'hi'}]})});
  try {
    const jx=await call('deepseek-v4.1-flash'); assert.equal(jx.status,200); assert.match(await jx.text(),/message_stop/);
    change('official');
    const ds=await call('deepseek-v4.1-flash'); assert.equal(ds.status,200); await ds.text();
    const gpt=await call('gpt-6.1-sol'); assert.equal(gpt.status,200); await gpt.text();
    change('jxmedia'); const back=await call('deepseek-v4.1-flash'); await back.text();
    assert.deepEqual(captured.map(r=>r.body.model),['deepseek-v4.1-flash','deepseek-flash','gpt-6.1-sol','deepseek-v4.1-flash']);
    assert.equal(destinations[1],'https://api.deepseek.com/anthropic/v1/messages');
    assert.equal(captured[1].headers['x-api-key'],'official-secret'); assert.equal(captured[1].headers.authorization,undefined);
    for(const i of [0,2,3]) {assert.equal(captured[i].headers.authorization,'Bearer local-secret');assert.equal(captured[i].headers['x-api-key'],undefined);}
    assert.equal((await call('gpt-6.1-sol','bad')).status,401);
    fs.writeFileSync(routeFile,JSON.stringify({apps:{claude:{mode:'proxy',proxy_route:'ds'}}}));
    assert.equal((await call('gpt-6.1-sol')).status,503);
    assert.equal(captured.length,4);
  } finally {await close(router);await close(upstream);fs.rmSync(home,{recursive:true,force:true});}
});
