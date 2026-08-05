#!/usr/bin/env node
'use strict';

// PreToolUse hook: 拦截 Read 图片文件。
// 主模型走 DeepSeek（纯文本），Read 图片时 Read 工具本身成功，但图片 block
// 发给纯文本模型会触发 API 400——没有 PostToolUseFailure 可兜底，只能在
// PreToolUse 拦下并引导改用 vision skill。
const fs = require('fs');
const path = require('path');

const IMAGE_EXT = /\.(png|jpe?g|gif|webp|bmp|ico|avif|tiff?)$/i;

let raw = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', d => { raw += d; });
process.stdin.on('end', () => {
  let data;
  try { data = JSON.parse(raw); } catch { process.exit(0); }
  if (data.tool_name !== 'Read') process.exit(0);
  const fp = String(data.tool_input?.file_path ?? '').trim();
  if (!fp || !IMAGE_EXT.test(fp)) process.exit(0);
  try {
    if (!fs.statSync(fp).isFile()) process.exit(0);
  } catch { process.exit(0); } // 文件不存在与读图无关

  const msg =
    `⚠️ ${path.basename(fp)} 是图片文件，而当前主模型为纯文本模型（DeepSeek），` +
    `直接 Read 会把图片 block 发给纯文本模型并触发 API 400（Read 工具本身会"成功"，所以不会报错提示，只能在这里拦）。\n` +
    `请改用 vision skill 处理这张图：\n` +
    `1. 调用 Skill(vision) 加载用法；\n` +
    `2. 按其中「本地图片用 data: URI」一节，把 ${fp} 转成 data: URI 传给 vision.py；\n` +
    `3. VISION_API_BASE / VISION_MODEL / VISION_API_KEY 按 skill 配置确认（key 由用户用环境变量设置，不要硬编码或读取明文）。`;

  console.log(JSON.stringify({
    hookSpecificOutput: {
      hookEventName: 'PreToolUse',
      additionalContext: msg,
    },
  }));
});
