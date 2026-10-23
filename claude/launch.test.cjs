const {test}=require('node:test'),assert=require('node:assert/strict');
const {plan}=require('./launch.cjs');
test('exact verified model IDs declare distinct native engine windows',()=>{
 for(const [model,size] of [['gpt-6.1-sol',475000],['gpt-6-astra',258400],['deepseek-v4.1-flash',1000000]]){
  const p=plan(['--model',model],{}, {}, {});assert.equal(p.env.CLAUDE_CODE_MAX_CONTEXT_TOKENS,String(size));assert(!p.args.includes('--plugin-dir'));
 }
 assert.equal(plan(['--model','gpt-5.1-sol'],{}, {}, {}).limit,undefined);
});
test('CLI model and mode override defaults; aliases resolve actual provider models',()=>{
 const live={model:'gpt-6.1-sol',env:{ANTHROPIC_DEFAULT_HAIKU_MODEL:'deepseek-v4.1-flash'}};
 assert.equal(plan(['--model=haiku'],live,{},{}).limit,1000000);
 assert.deepEqual(plan(['--permission-mode','manual'],live,{},{}).args,['--model','gpt-6.1-sol','--permission-mode','manual']);
 assert.equal(plan([],live,{},{}).env.CLAUDE_CODE_MAX_CONTEXT_TOKENS,'475000');
});
test('CC Switch owns auth when its profile is loaded; direct CLI environment is preserved otherwise',()=>{
 const environment={ANTHROPIC_API_KEY:'stale-key',ANTHROPIC_AUTH_TOKEN:'stale-auth',PATH:'/usr/bin'};
 const withProfile=plan([],{model:'gpt-6.1-sol'},{env:{}},environment);
 assert.equal(withProfile.env.ANTHROPIC_API_KEY,undefined);assert.equal(withProfile.env.ANTHROPIC_AUTH_TOKEN,undefined);assert.equal(withProfile.env.PATH,'/usr/bin');
 assert.equal(plan([],{}, {}, environment).env.ANTHROPIC_API_KEY,'stale-key');
});
test('resume does not assume the saved session uses the current default model',()=>{
 assert.equal(plan(['--resume','example'],{model:'gpt-6.1-sol'}, {}, {}).limit,undefined);
 assert.equal(plan(['--resume','example','--model','gpt-6-astra'],{model:'gpt-6.1-sol'}, {}, {}).limit,258400);
});
test('aggregate model IDs keep their real model window, including native 1M markers',()=>{
 assert.equal(plan(['--model','ccs-claude-jxmedia--gpt-6.1-sol'],{}, {}, {}).limit,475000);
 assert.equal(plan(['--model','ccs-claude-official--deepseek-flash[1M]'],{}, {}, {}).limit,1000000);
});
test('native default Sonnet role resolves without inheriting its implicit 1M marker',()=>{
 const live={env:{ANTHROPIC_DEFAULT_SONNET_MODEL:'ccs-claude-jxmedia--gpt-6.1-sol'}};
 const p=plan([],live,{},{});assert.equal(p.limit,475000);assert(p.args.includes('ccs-claude-jxmedia--gpt-6.1-sol'));
});
test('aggregate native picker is preserved instead of overwritten by the default provider list',t=>{
 const fs=require('node:fs'),os=require('node:os'),path=require('node:path'),cp=require('node:child_process');
 const {providerProfile}=require('./launch.cjs');
 const home=fs.mkdtempSync(path.join(os.tmpdir(),'claude-stack-test-'));t.after(()=>fs.rmSync(home,{recursive:true,force:true}));
 fs.mkdirSync(path.join(home,'.claude'));fs.mkdirSync(path.join(home,'.cc-switch'));
 const options=[{model:'ccs-claude-jxmedia--gpt-6.1-sol',description:'gpt · 200K'},{model:'ccs-claude-official--deepseek-flash[1M]',description:'Official flash · 1M'}];
 fs.writeFileSync(path.join(home,'.claude','settings.json'),JSON.stringify({modelPicker:{options},env:{ANTHROPIC_AUTH_TOKEN:'local-only'}}));
 fs.writeFileSync(path.join(home,'.cc-switch','live-state.json'),JSON.stringify({apps:{claude:{mode:'proxy',proxy_route:'jx',stack:{enabled:true,members:['jx'],keys:{jxmedia:'jx'}}}}}));
 const db=path.join(home,'.cc-switch','cc-switch.db'),source={modelPicker:{options:[{model:'gpt-6.1-sol',description:'Coding and everyday work'}]}};
 cp.execFileSync('sqlite3',[db],{input:"CREATE TABLE providers(id TEXT,is_current INTEGER,settings_config TEXT,app_type TEXT); INSERT INTO providers VALUES('jx',1,'"+JSON.stringify(source)+"','claude');"});
 const p=providerProfile(home);assert.equal(p.modelPicker.options.length,2);assert.equal(p.modelPicker.options[1].model,options[1].model);assert.equal(p.modelPicker.options[0].description,'Coding and everyday work');assert.equal(p.env.ANTHROPIC_AUTH_TOKEN,undefined);assert.equal(p.env.ANTHROPIC_DEFAULT_MODEL,options[0].model);
});
