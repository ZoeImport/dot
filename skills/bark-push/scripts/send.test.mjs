import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync, mkdirSync, writeFileSync, readFileSync, rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join, dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {spawnSync} from 'node:child_process';
import {createDecipheriv} from 'node:crypto';

test('Bash sender encrypts correctly and rejects invalid inputs without sending', () => {
  const root = mkdtempSync(join(tmpdir(), 'bark-push-test-'));
  try {
    const config = join(root, 'config');
    const bin = join(root, 'bin');
    mkdirSync(config, {mode: 0o700});
    mkdirSync(bin);
    writeFileSync(join(config, 'device-key'), 'test-device', {mode: 0o600});
    writeFileSync(join(config, 'encryption-key'), '0123456789abcdef', {mode: 0o600});
    const log = join(root, 'request.json');
    const mock = join(root, 'mock.mjs');
    writeFileSync(mock, `
      import fs from 'node:fs';
      const args = process.argv.slice(2);
      const config = fs.readFileSync(0, 'utf8');
      if (config !== 'url = "https://api.day.app/test-device"\\n') process.exit(90);
      const data = args.filter((arg, i) => args[i-1] === '--data-urlencode');
      const fields = Object.fromEntries(data.map(s => [s.slice(0,s.indexOf('=')),s.slice(s.indexOf('=')+1)]));
      fs.writeFileSync(process.env.MOCK_BARK_LOG, JSON.stringify(fields));
      if (process.env.MOCK_BARK_EXIT) process.exit(Number(process.env.MOCK_BARK_EXIT));
      process.stdout.write(process.env.MOCK_BARK_RESPONSE || '{"code":200}');
    `);
    writeFileSync(join(bin, 'curl'), `#!/usr/bin/env bash\nexec '${process.execPath}' '${mock}' "$@"\n`, {mode: 0o700});
    const sender = join(dirname(fileURLToPath(import.meta.url)), 'send.sh');
    const invoke = (input, extra = {}, args = []) => spawnSync('bash', [sender, ...args], {
      input,
      encoding: 'utf8',
      timeout: 10000,
      env: {...process.env, PATH: `${bin}:${process.env.PATH}`, BARK_CONFIG_DIR: config, MOCK_BARK_LOG: log, ...extra},
    });
    const payload = {title: '测试', body: '中文 "引号"\n换行与 $() `字符` 🫡'};
    const first = invoke(JSON.stringify(payload));
    assert.equal(first.status, 0, first.stderr);
    assert.match(first.stdout, /接口已接受/);
    assert.ok(!first.stdout.includes(payload.body));
    const wire = JSON.parse(readFileSync(log, 'utf8'));
    assert.deepEqual(Object.keys(wire).sort(), ['ciphertext', 'iv']);
    assert.match(wire.iv, /^[A-Za-z0-9+/]{16}$/);
    assert.ok(!wire.ciphertext.includes('\n'));
    const decipher = createDecipheriv('aes-128-cbc', Buffer.from('0123456789abcdef'), Buffer.from(wire.iv));
    const plaintext = Buffer.concat([decipher.update(Buffer.from(wire.ciphertext, 'base64')), decipher.final()]);
    assert.deepEqual(JSON.parse(plaintext), {sound: 'birdsong', group: 'codex', ttl: 600, ...payload});
    assert.equal(invoke(JSON.stringify(payload)).status, 0);
    assert.notEqual(JSON.parse(readFileSync(log, 'utf8')).iv, wire.iv);

    for (const input of ['invalid JSON', '{"body":42}', '{"body":"ok","unknown":1}', JSON.stringify({body: '字'.repeat(1000)})]) {
      rmSync(log, {force: true});
      assert.notEqual(invoke(input).status, 0);
      assert.throws(() => readFileSync(log));
    }
    writeFileSync(join(config, 'encryption-key'), '123456789012345¥');
    assert.notEqual(invoke(JSON.stringify(payload)).status, 0);
    assert.throws(() => readFileSync(log));
    writeFileSync(join(config, 'encryption-key'), '0123456789abcdef');
    assert.notEqual(invoke(JSON.stringify(payload), {MOCK_BARK_RESPONSE: '{"code":400}'}).status, 0);
    assert.notEqual(invoke(JSON.stringify(payload), {MOCK_BARK_RESPONSE: 'not JSON'}).status, 0);
    const timeout = invoke(JSON.stringify(payload), {MOCK_BARK_EXIT: '28'});
    assert.notEqual(timeout.status, 0);
    assert.match(timeout.stderr, /不要自动重发/);
    rmSync(log);
    assert.equal(invoke('', {}, ['--check']).status, 0);
    assert.throws(() => readFileSync(log));
    assert.notEqual(invoke('', {BARK_CONFIG_DIR: join(root, 'missing')}, ['--check']).status, 0);
  } finally {
    rmSync(root, {recursive: true, force: true});
  }
});
