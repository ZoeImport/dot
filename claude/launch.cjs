#!/usr/bin/env node
const fs=require('node:fs'),os=require('node:os'),path=require('node:path'),cp=require('node:child_process');
// Verified Codex OAuth effective defaults; not the larger public API limits.
const windows=Object.freeze({'gpt-6.1-sol':475000,'gpt-6-astra':258400,'deepseek-v4.1-flash':1000000,'deepseek-flash':1000000});
function selectedModel(args,live,profile={}) {
  let model=live.model || profile.model || live.env?.ANTHROPIC_MODEL || profile.env?.ANTHROPIC_DEFAULT_MODEL || live.env?.ANTHROPIC_DEFAULT_MODEL;
  for(let i=0;i<args.length;i++){
    if(args[i]==='--')break;
    if((args[i]==='--model'||args[i]==='-m')&&args[i+1])model=args[++i];
    else if(args[i].startsWith('--model='))model=args[i].slice(8);
  }
  const role={opus:'ANTHROPIC_DEFAULT_OPUS_MODEL',fable:'ANTHROPIC_DEFAULT_FABLE_MODEL',sonnet:'ANTHROPIC_DEFAULT_SONNET_MODEL',haiku:'ANTHROPIC_DEFAULT_HAIKU_MODEL'}[model];
  return role ? profile.env?.[role] || live.env?.[role] || model : model;
}
function plan(args,live,profile={},environment=process.env) {
  const model=selectedModel(args,live,profile),env={...environment};
  if(Object.keys(profile).length) for(const key of ['ANTHROPIC_API_KEY','ANTHROPIC_AUTH_TOKEN','ANTHROPIC_BASE_URL','ANTHROPIC_MODEL'])delete env[key];
  const explicitModel=args.some(a=>a==='--model'||a==='-m'||a.startsWith('--model='));
  const resume=args.some(a=>['--resume','-r','--continue','-c'].includes(a)||a.startsWith('--resume='));
  const limit=resume && !explicitModel ? undefined : windows[model];
  if(resume && !explicitModel)delete env.CLAUDE_CODE_MAX_CONTEXT_TOKENS;
  if(limit)env.CLAUDE_CODE_MAX_CONTEXT_TOKENS=String(limit);
  const explicit=args.some(a=>a==='--permission-mode'||a.startsWith('--permission-mode=')||a==='--dangerously-skip-permissions');
  return {env,args:explicit?args:['--permission-mode','bypassPermissions',...args],model,limit};
}
function providerProfile(home) {
  const db=path.join(home,'.cc-switch','cc-switch.db');
  if(!fs.existsSync(db))return {};
  const rows=JSON.parse(cp.execFileSync('sqlite3',['-readonly','-json',db,"SELECT id,is_current,settings_config FROM providers WHERE app_type='claude'"],{encoding:'utf8'}));
  let state={};try{state=JSON.parse(fs.readFileSync(path.join(home,'.cc-switch','live-state.json'),'utf8'));}catch{}
  const route=state.apps?.claude;
  const row=route?.mode==='proxy' ? rows.find(r=>r.id===route.proxy_route) : rows.find(r=>r.is_current===1);
  if(!row)return {};
  const source=JSON.parse(row.settings_config);
  // Auth stays in CC Switch's live settings; the overlay carries models only.
  const env=Object.fromEntries(Object.entries(source.env||{}).filter(([k])=>/^ANTHROPIC_DEFAULT_.*MODEL(?:_NAME|_DESCRIPTION)?$/.test(k)));
  return {...(source.modelPicker?{modelPicker:source.modelPicker}:{}),...(source.modelSettings?{modelSettings:source.modelSettings}:{}),env};
}
function launch(args=process.argv.slice(2),home=os.homedir()) {
  const file=path.join(home,'.claude','settings.json');
  const live=fs.existsSync(file)?JSON.parse(fs.readFileSync(file,'utf8')):{};
  const profile=providerProfile(home);
  const request=plan(args,live,profile);
  if(Object.keys(profile).length){
    const overlay=path.join(home,'.claude','provider-models.generated.json'),temp=overlay+'.'+process.pid;
    fs.writeFileSync(temp,JSON.stringify(profile,null,2)+'\n',{mode:0o600});fs.renameSync(temp,overlay);
    request.args=['--settings',overlay,...request.args];
  }
  const child=cp.spawn('claude',request.args,{stdio:'inherit',env:request.env});
  // Terminal signals reach the child in the same foreground group already.
  process.on('SIGINT',()=>{});
  process.on('SIGTERM',()=>{child.kill('SIGTERM');});
  child.on('error',()=>{console.error('Cannot start Claude Code. Ensure claude and sqlite3 are installed.');process.exitCode=1;});
  child.on('exit',(code,signal)=>{process.exitCode=code ?? (signal?1:0);});
}
module.exports={windows,selectedModel,plan,providerProfile};
if(require.main===module){try{launch();}catch{console.error('Claude model setup failed. Check local settings and CC Switch availability.');process.exitCode=1;}}
