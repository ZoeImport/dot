import fs from 'node:fs';

try {
  const mode = process.argv[2];
  if (mode === 'check-config') {
    const dir = process.argv[3];
    for (const file of [dir, `${dir}/device-key`, `${dir}/encryption-key`]) {
      const stat = fs.statSync(file);
      if ((stat.mode & 0o077) !== 0) throw new Error('配置目录需为 700，凭据文件需为 600');
    }
    const device = fs.readFileSync(`${dir}/device-key`, 'utf8').replace(/\r?\n$/, '');
    const key = fs.readFileSync(`${dir}/encryption-key`, 'utf8').replace(/\r?\n$/, '');
    if (!/^[A-Za-z0-9_-]+$/.test(device)) throw new Error('device-key 格式无效');
    if (Buffer.byteLength(key, 'utf8') !== 16 || /[\r\n\x00]/.test(key)) {
      throw new Error('encryption-key 必须为恰好 16 字节，不含换行或 NUL');
    }
  } else if (mode === 'payload') {
    const raw = fs.readFileSync(0);
    if (raw.length > 2048) throw new Error('JSON 载荷超过 2048 字节，请缩短消息');
    let value;
    try { value = JSON.parse(raw.toString('utf8')); }
    catch { throw new Error('标准输入必须是有效 JSON'); }
    if (!value || typeof value !== 'object' || Array.isArray(value)) throw new Error('载荷必须是 JSON 对象');
    const allowed = new Set(['title', 'body', 'sound', 'group', 'ttl']);
    for (const [key, item] of Object.entries(value)) {
      if (!allowed.has(key)) throw new Error('载荷含不支持的字段');
      if (key === 'ttl') {
        if (!Number.isInteger(item) || item < 0 || item > 2592000) throw new Error('ttl 必须为 0 至 2592000 的整数');
      } else if (typeof item !== 'string') throw new Error('通知文本字段必须是字符串');
    }
    if (!value.body?.trim() && !value.title?.trim()) throw new Error('title 或 body 至少有一项非空');
    const json = JSON.stringify({sound: 'birdsong', group: 'codex', ttl: 600, ...value});
    if (Buffer.byteLength(json) > 2048) throw new Error('含默认参数的 JSON 超过 2048 字节，请缩短消息');
    process.stdout.write(json);
  } else if (mode === 'response') {
    let value;
    try { value = JSON.parse(fs.readFileSync(0, 'utf8')); }
    catch { throw new Error('Bark 返回无效 JSON；送达状态未知，不要自动重发'); }
    if (value.code !== 200) throw new Error('Bark 拒绝请求；未确认送达');
    console.log('Bark 接口已接受（code=200）；手机送达与解密仍需确认。');
  } else throw new Error('不支持的协议操作');
} catch (error) {
  if (error.code === 'ENOENT') console.error('缺少本地 Bark 配置：请提供 device-key 和 encryption-key。');
  else if (error.code) console.error('无法读取本地 Bark 配置，请检查权限和路径。');
  else console.error(error.message);
  process.exitCode = 1;
}
