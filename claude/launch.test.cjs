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
 assert.deepEqual(plan(['--permission-mode','manual'],live,{},{}).args,['--permission-mode','manual']);
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
