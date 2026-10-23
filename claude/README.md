# Claude Code 快速配置

本目录提供原生 `statusLine` 与自动压缩配置。无需 Mod、Claude 二进制补丁或额外模型调用。安装器只合并状态栏和压缩相关字段，保留已有认证、provider、模型、permissions、hooks、插件和主题；不会把公开模板中的 `xxx` 写进你的真实配置。

## 一键安装或重装恢复

要求：Node.js 18+、Claude Code；使用 CC Switch 时还需 `sqlite3` CLI。当前在 macOS / Claude Code 2.1.308 验证。`effort`、`prompt_cache`、`pr` 字段在旧版可能缺失，届时显示 `--`。

```sh
git clone https://github.com/ZoeImport/dot.git ~/CodeSpace/dot
cd ~/CodeSpace/dot
node claude/install.cjs
```

已有仓库时先 `git pull --ff-only`，再运行安装器。使用 CC Switch 时，先退出它再安装，避免它同时保存配置；安装后重新打开 CC Switch 和 Claude Code。重装 Claude Code 通常保留用户目录；若也清理了用户配置，重新运行上面的安装命令。**账号/API key/OAuth 登录仍需自行恢复，仓库不包含凭据。**

只配置 Claude Code，不更新 CC Switch：

```sh
node claude/install.cjs --no-cc-switch
```

安装器部署：

| 文件 | 用途 |
| --- | --- |
| `~/.claude/statusline.sh` | 原生 statusLine 的 shell 入口 |
| `~/.claude/statusline.cjs` | 读取 stdin JSON、计算并输出一行状态 |
| `~/.claude/settings.json` | 合并 statusLine、autoCompactEnabled、autoCompactWindow |
| `~/.claude/backups/native-statusline-*` | 安装前的私有备份，权限 700/600；可能含本机凭据，禁止提交 |
| `~/.cache/claude-native-statusline/` | 每会话 API 时间基线和最近速率；不保存提示词、凭据或 transcript |

检测到 `~/.cc-switch/cc-switch.db` 时，同样更新 `common_config_claude` 和 Claude provider 的状态栏/压缩字段，并在事务中保存，防止 provider 切换时覆盖。provider 的认证、端点、模型名称/描述和 `meta` 不变。已有逐模型压缩阈值会统一改成 400000，避免它覆盖全局阈值；思考档位保留。

## 显示内容与计算口径

示例：`avg 42.5 tok/s | Ctx 280.0k/1M (28%) | Cache 91% | Effort high | PR #34`

- **avg tok/s**：最近一次可观测请求的输出 token 数除以原生累计 API 耗时的增量，包含请求/首字等待，不是纯解码速度，也不是逐秒实时采样。首个有效响应前、无法取得耗时、或中途附加到旧会话的首次采样显示 `--`。并行请求/子代理可能使耗时包含其他请求，因此它是诊断估计值。
- **Ctx**：原生 JSON 的实际上下文计数、窗口与百分比；不根据模型名字伪造上限。输入计数包含 fresh input + cache creation + cache read，百分比遵循原生的输入口径，不额外加 output。
- **Cache**：优先使用原生会话 `prompt_cache.hit_ratio`；缺失时以最近请求 cache read 除以总输入估计。上游不报告缓存时显示 `--`，不把缺失值当作零命中。
- **Effort**：读取原生 `effort.level`，会跟随 `/effort`；缺失显示 `--`。
- **PR / MR**：读取 Claude Code 自己发现的 PR/MR；无值显示 `PR --`。脚本不调用 GitHub、git、模型或外部网络。

## 自动压缩 400k 与真实窗口

安装器设置：

```json
{
  "autoCompactEnabled": true,
  "autoCompactWindow": 400000,
  "statusLine": {
    "type": "command",
    "command": "sh ~/.claude/statusline.sh"
  }
}
```

**400000 是压缩阈值，不是模型窗口声明。** Claude Code 会按模型实际/识别窗口取较小值。原生 `/autocompact` 可查看生效来源和是否被截断；`CLAUDE_CODE_AUTO_COMPACT_WINDOW` 等更高优先级环境设置可能覆盖它。

2026-10-23 实机的 JX 转发自定义 `gpt-6.1-sol` 被 Claude Code 原生识别为 200k，因此面板实际显示 **400k configured / capped to 200k**。本安装器没有伪装模型 ID、改上下文能力或添加切换 hook；只有 provider/CLI 正确声明大于等于 400k 的真实窗口后，400k 阈值才会完整生效。不要用“状态栏显示更大数字”冒充上下文扩容。

## 模型列表与 Codex Fast

本安装器不会更改你的 CC Switch 模型列表或添加 shell model-picker wrapper。`claude/settings.json` 是公开参考模板，不建议直接覆盖到已登录的机器；模型名和描述需要在 provider 的原生 `modelPicker` 中配置，并确认 CLI 实际加载了它。

CC Switch 的 Codex OAuth provider 可开启 **Fast**，元数据字段是 `codexFastMode: true`；其 Responses 转换会写 `service_tier: "priority"`。本机该 OAuth provider 已开启。当前 JX provider 走另一条第三方路由，不能因模型名字是 GPT 就认定使用了 OAuth Fast。不要在 Claude 原生 `/fast`、reasoning effort 和 Codex Fast 之间画等号。本安装器不改变 Fast 开关或服务档位。

## 验证与恢复

```sh
node --test claude/install.test.cjs claude/statusline/statusline.test.cjs
```

进入 Claude Code 后检查状态栏，执行 `/autocompact` 检查 400k 与实际窗口的截断情况。没有请求时 token/s、缓存等显示 `--` 是正常情况。

恢复时从安装输出的私有备份复制回对应文件。若使用 CC Switch，还需在其公共配置/provider 中恢复 statusLine 与 autoCompact 字段；备份 `cc-switch-model-settings.json` 保存了安装前原值，包含私密 provider 数据，切勿上传到公开仓库。不要为恢复本配置而覆盖正在使用的整库数据库。

参考：[Claude status line](https://code.claude.com/docs/en/statusline)、[auto-compact window](https://code.claude.com/docs/en/model-config#set-the-auto-compact-window)、[OpenAI Fast mode](https://developers.openai.com/api/docs/guides/fast-mode)、[CC Switch conversion source](https://github.com/farion1231/cc-switch/blob/79ba7982aa3980b001c0b68efde05505884c1f8b/src-tauri/src/proxy/providers/transform_responses.rs#L2003)。
