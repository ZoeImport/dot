const {test}=require('node:test');
const assert=require('node:assert/strict');
const {compact,speed,render}=require('./statusline.cjs');
test('native context cache effort and PR render without model-name inference',()=>{
 const input={model:{display_name:'GPT-6.1-Sol'},context_window:{total_input_tokens:280000,context_window_size:1000000,used_percentage:28,current_usage:{input_tokens:10000,cache_read_input_tokens:270000}},prompt_cache:{hit_ratio:0.91},effort:{level:'high'},pr:{number:34}};
 assert.equal(render(input,42.5),'GPT-6.1-Sol | avg 42.5 tok/s | Ctx 280.0k/1M (28%) | Cache 91% | Effort high | PR #34');
});
test('speed is latest request output over API duration delta; unchanged updates retain it',()=>{
 let s=speed({cost:{total_api_duration_ms:2000},context_window:{total_output_tokens:100}},{api:0});assert.equal(s.rate,50);
 s=speed({cost:{total_api_duration_ms:3000},context_window:{total_output_tokens:200}},s);assert.equal(s.rate,200);
 assert.equal(speed({cost:{total_api_duration_ms:3000},context_window:{total_output_tokens:200}},s).rate,200);
});
test('unknown values do not fabricate usage, effort or PR',()=>{assert.equal(render({},undefined),'-- | avg -- tok/s | Ctx --/-- | Cache -- | Effort -- | PR --');assert.equal(compact(1000000),'1M');});
test('cache fallback includes fresh input plus cache writes and reads; MR is supported',()=>{
 assert.match(render({context_window:{current_usage:{input_tokens:10,cache_creation_input_tokens:10,cache_read_input_tokens:80}},pr:{number:9,kind:'mr'}},0),/Cache 80%.*MR #9/);
});

test('attaching mid-session does not divide latest output by all previous API time',()=>{assert.equal(speed({cost:{total_api_duration_ms:99000},context_window:{total_output_tokens:100}}).rate,undefined);});
test('model label follows native session data and strips control characters',()=>{
 assert.match(render({model:{id:'deepseek-v4.1-flash'}},undefined),/^deepseek-v4.1-flash \|/);
 assert(!render({model:{display_name:'bad\nname'}},undefined).includes('\n'));
});
