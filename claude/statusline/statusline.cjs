const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const crypto = require('node:crypto');
const finite = n => typeof n === 'number' && Number.isFinite(n) && n >= 0;
function compact(n) {
  if (!finite(n)) return '--';
  if (n >= 1e6) return (n / 1e6).toFixed(2).replace(/\.?0+$/, '') + 'M';
  return n >= 1000 ? (n / 1000).toFixed(1) + 'k' : String(Math.round(n));
}
function speed(input, previous = {}) {
  const api = input.cost?.total_api_duration_ms;
  const output = input.context_window?.current_usage?.output_tokens ?? input.context_window?.total_output_tokens;
  if (!finite(api) || !finite(output)) return { ...previous, rate: undefined };
  if (api === previous.api) return previous;
  if (!finite(previous.api)) return { api };
  const duration = api >= (previous.api ?? 0) ? api - (previous.api ?? 0) : api;
  return { api, rate: duration > 0 ? output * 1000 / duration : undefined };
}
function render(input, rate) {
  const c = input.context_window || {}, u = c.current_usage;
  const tokens = finite(c.total_input_tokens) ? c.total_input_tokens : u ? (u.input_tokens || 0) + (u.cache_creation_input_tokens || 0) + (u.cache_read_input_tokens || 0) : undefined;
  const percentage = finite(c.used_percentage) ? c.used_percentage : finite(tokens) && c.context_window_size > 0 ? 100 * tokens / c.context_window_size : undefined;
  let ratio = input.prompt_cache?.hit_ratio;
  if (!finite(ratio) && u) {
    const total = (u.input_tokens || 0) + (u.cache_creation_input_tokens || 0) + (u.cache_read_input_tokens || 0);
    if (total > 0) ratio = (u.cache_read_input_tokens || 0) / total;
  }
  const effort = ['low','medium','high','xhigh','max'].includes(input.effort?.level) ? input.effort.level : '--';
  const pr = Number.isInteger(input.pr?.number) && input.pr.number > 0 ? (input.pr.kind === 'mr' ? 'MR #' : 'PR #') + input.pr.number : 'PR --';
  const rawModel = String(input.model?.display_name || input.model?.id || '--').replace(/[\x00-\x1f\x7f-\x9f\u202a-\u202e\u2066-\u2069]/g, '').slice(0,200);
  const stackModel = rawModel.match(/^ccs-claude-([a-z0-9-]+)--(.+?)(?:\[1m\])?$/i);
  const model = (stackModel ? stackModel[2] + ' (' + stackModel[1] + ')' : rawModel).slice(0,80);
  return [
    model,
    'avg ' + (finite(rate) ? rate.toFixed(1) : '--') + ' tok/s',
    'Ctx ' + compact(tokens) + '/' + compact(c.context_window_size) + (finite(percentage) ? ' (' + Math.round(percentage) + '%)' : ''),
    'Cache ' + (finite(ratio) && ratio <= 1 ? Math.round(ratio * 100) + '%' : '--'),
    'Effort ' + effort,
    pr,
  ].join(' | ');
}
function main() {
  const input = JSON.parse(fs.readFileSync(0,'utf8'));
  const dir = path.join(os.homedir(), '.cache', 'claude-native-statusline');
  fs.mkdirSync(dir, {recursive:true, mode:0o700});
  const id = crypto.createHash('sha256').update(String(input.session_id || input.transcript_path || 'unknown')).digest('hex');
  const file = path.join(dir, id + '.json');
  let previous = {};
  try { const st=fs.statSync(file); if(st.size <= 4096)previous=JSON.parse(fs.readFileSync(file,'utf8')); } catch {}
  const current = speed(input, previous);
  if (current !== previous) {
    const temp = file + '.' + process.pid;
    fs.writeFileSync(temp, JSON.stringify(current), {mode:0o600});
    fs.renameSync(temp, file);
  }
  process.stdout.write(render(input,current.rate) + '\n');
}
module.exports = { compact, speed, render };
if (require.main === module) {
  try { main(); } catch { process.stdout.write('-- | avg -- tok/s | Ctx --/-- | Cache -- | Effort -- | PR --\n'); }
}
