#!/usr/bin/env node
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const cp = require('node:child_process');
const compactWindow = 400000;
const statusLine = { type: 'command', command: 'sh ~/.claude/statusline.sh' };
function configure(current) {
  const updated = { ...current, statusLine, autoCompactEnabled: true, autoCompactWindow: compactWindow };
  // Per-model thresholds override the global threshold in the same settings file.
  if (current.modelSettings) updated.modelSettings = Object.fromEntries(Object.entries(current.modelSettings).map(([id, value]) =>
    [id, value.autoCompactWindow === undefined ? value : { ...value, autoCompactWindow: compactWindow }]));
  return updated;
}
function sqlText(value) { return "'" + value.replaceAll("'", "''") + "'"; }
function writeJSON(file, value) {
  const temp = file + '.' + process.pid + '.tmp';
  fs.writeFileSync(temp, JSON.stringify(value, null, 2) + '\n', {mode:0o600});
  fs.renameSync(temp, file);
}
function install(home = os.homedir(), source = __dirname, useCCSwitch = true) {
  const dir = path.join(home,'.claude'), file = path.join(dir,'settings.json');
  const current = fs.existsSync(file) ? JSON.parse(fs.readFileSync(file,'utf8')) : {};
  const database = path.join(home,'.cc-switch','cc-switch.db');
  let commonRows = [], providerRows = [];
  const sqlite = args => JSON.parse(cp.execFileSync('sqlite3',['-readonly','-json',database,...args],{encoding:'utf8'}));
  if (useCCSwitch && fs.existsSync(database)) {
    commonRows = sqlite(["SELECT value FROM settings WHERE key='common_config_claude'"]);
    providerRows = sqlite(["SELECT id,settings_config FROM providers WHERE app_type='claude'"]);
    // Parse before writing anything: malformed source configuration must not be replaced.
    commonRows.forEach(row => JSON.parse(row.value));
    providerRows.forEach(row => JSON.parse(row.settings_config));
  }
  fs.mkdirSync(dir,{recursive:true,mode:0o700});
  const backups = path.join(dir,'backups');
  fs.mkdirSync(backups,{recursive:true,mode:0o700});
  const backup = fs.mkdtempSync(path.join(backups,'native-statusline-'));
  fs.chmodSync(backup,0o700);
  if (fs.existsSync(file)) { fs.copyFileSync(file,path.join(backup,'settings.json')); fs.chmodSync(path.join(backup,'settings.json'),0o600); }
  if (commonRows.length || providerRows.length) writeJSON(path.join(backup,'cc-switch-model-settings.json'),{commonRows,providerRows});
  for (const name of ['statusline.cjs','statusline.sh']) {
    const target=path.join(dir,name);
    if (fs.existsSync(target)) { fs.copyFileSync(target,path.join(backup,name)); fs.chmodSync(path.join(backup,name),0o600); }
    fs.copyFileSync(path.join(source,'statusline',name),target); fs.chmodSync(target,0o700);
  }
  if (useCCSwitch && fs.existsSync(database)) {
    const common = configure(commonRows.length ? JSON.parse(commonRows[0].value) : {});
    const statements = ["INSERT OR REPLACE INTO settings(key,value) VALUES('common_config_claude',"+sqlText(JSON.stringify(common))+");"];
    for (const row of providerRows) {
      const original=JSON.parse(row.settings_config);
      // Provider data keeps its auth, endpoints, labels, metadata and all other fields.
      const updated=configure(original);
      statements.push('UPDATE providers SET settings_config='+sqlText(JSON.stringify(updated))+' WHERE app_type=\'claude\' AND id='+sqlText(row.id)+';');
    }
    cp.execFileSync('sqlite3',['-cmd','.timeout 5000',database],{input:'BEGIN IMMEDIATE;\n'+statements.join('\n')+'\nCOMMIT;\n',encoding:'utf8',stdio:['pipe','pipe','pipe']});
  }
  if(fs.existsSync(path.join(dir,'launch.cjs'))) { fs.copyFileSync(path.join(dir,'launch.cjs'),path.join(backup,'launch.cjs')); fs.chmodSync(path.join(backup,'launch.cjs'),0o600); }
  fs.copyFileSync(path.join(source,'launch.cjs'),path.join(dir,'launch.cjs'));
  fs.chmodSync(path.join(dir,'launch.cjs'),0o700);
  if(fs.existsSync(path.join(dir,'deepseek-channel.cjs'))) { fs.copyFileSync(path.join(dir,'deepseek-channel.cjs'),path.join(backup,'deepseek-channel.cjs')); fs.chmodSync(path.join(backup,'deepseek-channel.cjs'),0o600); }
  fs.copyFileSync(path.join(source,'deepseek-channel.cjs'),path.join(dir,'deepseek-channel.cjs'));
  fs.chmodSync(path.join(dir,'deepseek-channel.cjs'),0o700);
  const functions=path.join(home,'.config','fish','functions');
  if(fs.existsSync(path.join(home,'.config','fish'))) {
    fs.mkdirSync(functions,{recursive:true});
    const target=path.join(functions,'claude.fish');
    if(fs.existsSync(target)) { fs.copyFileSync(target,path.join(backup,'claude.fish')); fs.chmodSync(path.join(backup,'claude.fish'),0o600); }
    fs.writeFileSync(target,'function claude --description "Claude Code with provider model configuration"\n    node "$HOME/.claude/launch.cjs" $argv\nend\n');
    const channelFunction=path.join(functions,'deepseek-channel.fish');
    if(fs.existsSync(channelFunction)) { fs.copyFileSync(channelFunction,path.join(backup,'deepseek-channel.fish')); fs.chmodSync(path.join(backup,'deepseek-channel.fish'),0o600); }
    fs.writeFileSync(channelFunction,'function deepseek-channel --description "Select only the DeepSeek upstream"\n    node "$HOME/.claude/deepseek-channel.cjs" $argv\nend\n');
  }
  writeJSON(file,configure(current));
  return {settings:file,backup,ccSwitch:useCCSwitch && fs.existsSync(database)};
}
module.exports = {configure,install};
if (require.main === module) {
  const allowed = new Set(['--no-cc-switch']);
  if(process.argv.slice(2).some(arg=>!allowed.has(arg))) { process.stderr.write('Usage: node claude/install.cjs [--no-cc-switch]\n'); process.exit(1); }
  try { const result=install(os.homedir(),__dirname,!process.argv.includes('--no-cc-switch')); console.log('Installed native statusline and 400k auto-compaction. Restart Claude Code.'); console.log('Backup: '+result.backup); console.log('CC Switch persistence: '+(result.ccSwitch?'updated':'not used')); }
  catch { console.error('Install failed. Check JSON validity, filesystem access and sqlite3 availability. No credential values are printed.'); process.exitCode=1; }
}
