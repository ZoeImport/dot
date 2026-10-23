const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),os=require('node:os'),path=require('node:path'),cp=require('node:child_process');
const {configure,install}=require('./install.cjs');
function fixture(t){const home=fs.mkdtempSync(path.join(os.tmpdir(),'claude-config-test-'));t.after(()=>fs.rmSync(home,{recursive:true,force:true}));fs.mkdirSync(path.join(home,'.claude'));return home;}
test('merge preserves authentication, model, hooks and other per-model settings',()=>{
 const input={env:{ANTHROPIC_AUTH_TOKEN:'local-only'},model:'gpt-6.1-sol',hooks:{PreToolUse:[]},permissions:{defaultMode:'bypassPermissions'},modelSettings:{'gpt-6.1-sol':{effortLevel:'high',autoCompactWindow:475000}}};
 const output=configure(input);assert.deepEqual(output.env,input.env);assert.deepEqual(output.hooks,input.hooks);assert.deepEqual(output.permissions,input.permissions);assert.equal(output.model,input.model);assert.equal(output.modelSettings['gpt-6.1-sol'].effortLevel,'high');assert.equal(output.modelSettings['gpt-6.1-sol'].autoCompactWindow,400000);assert.equal(input.modelSettings['gpt-6.1-sol'].autoCompactWindow,475000);
});
test('installer is repeatable and never installs the public auth placeholders',t=>{
 const home=fixture(t),file=path.join(home,'.claude','settings.json');fs.writeFileSync(file,JSON.stringify({env:{ANTHROPIC_API_KEY:'local-only'},model:'my-model'}));
 install(home,__dirname,false);install(home,__dirname,false);const v=JSON.parse(fs.readFileSync(file));assert.equal(v.env.ANTHROPIC_API_KEY,'local-only');assert.equal(v.autoCompactWindow,400000);assert.equal(v.model,'my-model');assert.equal(fs.statSync(file).mode&0o777,0o600);assert(fs.existsSync(path.join(home,'.claude','statusline.cjs')));
});
test('CC Switch persistence modifies only statusline and compaction configuration',t=>{
 const home=fixture(t);fs.mkdirSync(path.join(home,'.cc-switch'));const db=path.join(home,'.cc-switch','cc-switch.db');
 const value={env:{ANTHROPIC_AUTH_TOKEN:'local-only'},modelPicker:{options:[{model:'custom',description:"user's model"}]},modelSettings:{custom:{effortLevel:'high',autoCompactWindow:1000000}}};
 const q=s=>"'"+s.replaceAll("'","''")+"'";
 cp.execFileSync('sqlite3',[db],{input:"CREATE TABLE settings(key TEXT PRIMARY KEY,value TEXT); CREATE TABLE providers(id TEXT,app_type TEXT,settings_config TEXT,meta TEXT); INSERT INTO settings VALUES('common_config_claude','{}'); INSERT INTO providers VALUES('p','claude',"+q(JSON.stringify(value))+",'{\"codexFastMode\":true}');"});
 install(home,__dirname,true);
 const rows=JSON.parse(cp.execFileSync('sqlite3',['-json',db,'SELECT * FROM providers'],{encoding:'utf8'}));const config=JSON.parse(rows[0].settings_config);assert.deepEqual(config.env,value.env);assert.deepEqual(config.modelPicker,value.modelPicker);assert.equal(config.modelSettings.custom.autoCompactWindow,400000);assert.equal(JSON.parse(rows[0].meta).codexFastMode,true);
 const common=JSON.parse(cp.execFileSync('sqlite3',[db,"select value from settings where key='common_config_claude'"],{encoding:'utf8'}));assert.equal(common.autoCompactWindow,400000);assert.equal(common.statusLine.command,'sh ~/.claude/statusline.sh');
});
test('malformed settings fail before replacing local configuration',t=>{
 const home=fixture(t),file=path.join(home,'.claude','settings.json');fs.writeFileSync(file,'{broken');assert.throws(()=>install(home,__dirname,false));assert.equal(fs.readFileSync(file,'utf8'),'{broken');
});
