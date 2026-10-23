# Claude Code 快速配置

本目录提供原生 `statusLine` 与自动压缩配置。无需 Mod、Claude 二进制补丁或额外模型调用。Fish 环境会安装一个原生模型配置启动入口。安装器只合并状态栏和压缩相关字段，保留已有认证、provider、模型、permissions、hooks、插件和主题；不会把公开模板中的 `xxx` 写进你的真实配置。

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
| `~/.claude/launch.cjs` | 读取当前 provider 模型列表，按启动模型声明原生窗口 |
| `~/.config/fish/functions/claude.fish` | Fish 中普通 claude 自动使用该入口；原函数有备份 |
| `~/.claude/settings.json` | 合并 statusLine、autoCompactEnabled、autoCompactWindow |
| `~/.claude/backups/native-statusline-*` | 安装前的私有备份，权限 700/600；可能含本机凭据，禁止提交 |
| `~/.cache/claude-native-statusline/` | 每会话 API 时间基线和最近速率；不保存提示词、凭据或 transcript |

检测到 `~/.cc-switch/cc-switch.db` 时，同样更新 `common_config_claude` 和 Claude provider 的状态栏/压缩字段，并在事务中保存，防止 provider 切换时覆盖。provider 的认证、端点、模型名称/描述和 `meta` 不变。已有逐模型压缩阈值会统一改成 400000，避免它覆盖全局阈值；思考档位保留。

## 显示内容与计算口径

示例：`GPT-6.1-Sol | avg 42.5 tok/s | Ctx 280.0k/1M (28%) | Cache 91% | Effort high | PR #34`

- **模型名**：读取当前会话原生 `model.display_name`，缺失时用 `model.id`；随实际模型变化，过滤终端控制字符。
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

原生 CLI 对未知模型原先回退到 200k；仅设置 autoCompactWindow 不会改变它。现在启动入口按精确 ID 设置原生 CLAUDE_CODE_MAX_CONTEXT_TOKENS：gpt-6.1-sol 为 475000，gpt-6-astra 为 258400，deepseek-v4.1-flash 为 1000000。这是前面核验的 OAuth 有效窗口与 DeepSeek 配置值，不等于更大的公开 API 上限，也不保证第三方网关的大负载容量。没有把不存在的 gpt-5.1-sol 当成同一个 ID。

**会话级限制**：环境变量在启动时选择，不能在同一原生会话的 /model 切换时自动改写。状态栏模型名会随切换更新，但窗口仍为启动声明。请用正确模型新开会话；恢复旧会话也请显式带 --model，避免拿当前默认模型猜旧会话窗口。不带 --model 的恢复会使用原生窗口默认值。未知 ID 不自动扩大窗口。Astra 的 258400 小于400k，压缩仍按该上限截断。

Fish 用户安装后普通 claude 自动加载；其他 shell 可用：

~~~sh
node ~/.claude/launch.cjs --model gpt-6.1-sol
node ~/.claude/launch.cjs --model gpt-6-astra
node ~/.claude/launch.cjs --model deepseek-v4.1-flash
node ~/.claude/launch.cjs --resume SESSION_ID --model gpt-6.1-sol
~~~

启动入口默认 bypassPermissions（沿用本配置的既有偏好）；需要其它模式时显式传 --permission-mode manual/auto。它不加载审批 Mod。2026-10-23 实际启动已验证 Sol 的状态栏为475.0k，/autocompact 显示400k且不再截至200k。

## 模型列表与 Codex Fast

本安装器不会改写 CC Switch 的模型名称、描述与认证。启动入口只生成模型相关的 --settings overlay，凭据留在 CC Switch 的 live settings；使用其 overlay 时清理继承的冲突认证环境。`claude/settings.json` 是公开参考模板，不建议直接覆盖到已登录的机器；模型名和描述需要在 provider 的原生 `modelPicker` 中配置，并确认 CLI 实际加载了它。

CC Switch 的 Codex OAuth provider 可开启 **Fast**，元数据字段是 `codexFastMode: true`；其 Responses 转换会写 `service_tier: "priority"`。本机该 OAuth provider 已开启。当前 JX provider 走另一条第三方路由，不能因模型名字是 GPT 就认定使用了 OAuth Fast。不要在 Claude 原生 `/fast`、reasoning effort 和 Codex Fast 之间画等号。本安装器不改变 Fast 开关或服务档位。

## 验证与恢复

```sh
node --test claude/install.test.cjs claude/launch.test.cjs claude/statusline/statusline.test.cjs
```

进入 Claude Code 后检查状态栏，执行 `/autocompact` 检查 400k 与实际窗口的截断情况。没有请求时 token/s、缓存等显示 `--` 是正常情况。

恢复时从安装输出的私有备份复制回对应文件。若使用 CC Switch，还需在其公共配置/provider 中恢复 statusLine 与 autoCompact 字段；备份 `cc-switch-model-settings.json` 保存了安装前原值，包含私密 provider 数据，切勿上传到公开仓库。不要为恢复本配置而覆盖正在使用的整库数据库。

参考：[Claude status line](https://code.claude.com/docs/en/statusline)、[auto-compact window](https://code.claude.com/docs/en/model-config#set-the-auto-compact-window)、[OpenAI Fast mode](https://developers.openai.com/api/docs/guides/fast-mode)、[CC Switch conversion source](https://github.com/farion1231/cc-switch/blob/79ba7982aa3980b001c0b68efde05505884c1f8b/src-tauri/src/proxy/providers/transform_responses.rs#L2003)。

## DeepSeek 手动双渠道聚合

CC Switch 的“聚合 / Stack”模式可以把两个 provider 的模型同时列进 `/model`；模型 ID 自带 provider 路由信息，选中的请求只去该渠道，不轮询、不自动兜底。

在 CC Switch 保留已有 jxmedia 和 DeepSeek 官方 provider，启用聚合并把两者加入。jxmedia 的 Flash 模型按其实际 ID 配置（本机为 `deepseek-v4.1-flash`），官方按官方列表配置 `deepseek-flash`；两条 DeepSeek 均可声明1M。provider key/账号绑定留在本机，不放进本仓库。现有 GPT 模型可继续作为聚合成员模型发布。

启动入口识别 `ccs-claude-<provider-key>--<model>`，保留 CC Switch 生成的完整聚合列表，不会再被默认 provider 自己的列表覆盖。GPT 原有模型描述优先保留；状态栏仍显示所选模型及渠道。新会话会显式选择解析后的默认模型，避免原生 `sonnet` 默认别名隐含的 `[1m]` 被误套到 GPT Sol。

本机已验证 jxmedia 与官方两条 Flash 请求均返回200，且请求日志的 provider_id 分别对应各自渠道。官方的 `deepseek-flash` 与 jxmedia 的 `deepseek-v4.1-flash` 是不同的上游 ID，本配置不声称两者永远指向相同版本。
