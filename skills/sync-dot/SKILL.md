---
name: sync-dot
description: 同步本地 OpenCode、OhMyOpenAgent、Claude Code 配置与 skills 到 dot 仓库，或从 dot 仓库恢复到本地。支持双向同步、跨平台路径、自动 git commit、用户确认。
---

# Sync Dot — 配置仓库同步技能

将本地 OpenCode、OhMyOpenAgent、Claude Code 配置和 skills 同步到 `~/CodeSpace/dot` 版本仓库（`push`），或从仓库恢复到本地（`pull`）。

---

## 触发条件

当用户说"同步配置"、"同步 dot"、"推配置"、"拉配置"、"sync dot"、"sync skills"、"备份配置"、"恢复配置"时使用本技能。

---

## 同步条目定义

| # | 内容 | 本地路径 | dot 路径 | 模式 |
|---|------|---------|----------|------|
| 1 | Skills | `~/.agents/skills/` | `~/CodeSpace/dot/skills/` | `rsync --delete`（镜像） |
| 2 | OpenCode 配置 | `~/.config/opencode/opencode.json` | `~/CodeSpace/dot/opencode/opencode.json` | `cp`（单文件） |
| 3 | OhMyOpenAgent 配置 | `~/.config/opencode/oh-my-openagent.json` | `~/CodeSpace/dot/opencode/oh-my-openagent.json` | `cp`（单文件） |
| 4 | Claude Code 配置 | `~/.claude/settings.json` | `~/CodeSpace/dot/claude/settings.json` | `cp`（单文件，需脱敏） |

### 平台路径差异

不同操作系统下本地路径不同，当前支持 Linux 直接映射，其他 OS 询问用户：

| OS | Skills 路径 | OpenCode 配置路径 | Claude Code 配置路径 |
|----|------------|-------------------|----------------------|
| Linux | `~/.agents/skills/` | `~/.config/opencode/` | `~/.claude/settings.json` |
| macOS (待确认) | `~/Library/Application Support/io.opencode/skills/` | `~/Library/Application Support/opencode/` | 待确认 |
| Windows (待确认) | `%APPDATA%\opencode\skills\` | `%APPDATA%\opencode\` | 待确认 |

OhMyOpenAgent 配置文件 `oh-my-openagent.json` 与 OpenCode 配置在同目录下，平台路径与上述 "OpenCode 配置路径" 相同。

**平台检测**：
```bash
uname -s | grep -qi linux && echo linux
uname -s | grep -qi darwin && echo darwin
uname -s | grep -qi mingw && echo windows
```

若 OS 未定义，向用户询问本地各条目的实际路径。

---

## 操作流程

### push（本地 → dot 仓库）

1. 检测 OS 并确定本地路径
1.5 **用户确认** — 在执行同步前，询问用户：
   > 「是否同步以下内容？(y/N)」
   > Skills → OpenCode + Claude Code skills
   > OpenCode 配置 → opencode.json + oh-my-openagent.json
   > Claude Code 配置 → settings.json
   >
   > 如果用户回答 n/N，跳过整个同步流程
   > 如果用户回答 y/Y，继续执行
2. 同步 skills：
   ```bash
   rsync -av --delete <local_skills>/ <dot_skills>/
   ```
3. 同步配置文件（逐个 cp）
3.5 同步 Claude Code 配置：
   ```bash
   mkdir -p ~/CodeSpace/dot/claude/
   cp ~/.claude/settings.json ~/CodeSpace/dot/claude/settings.json
   ```
3.6 **过滤密钥** — 对 Claude settings.json 执行密钥脱敏：
   - 扫描 `claude/settings.json` 中 `env` 段，替换以下字段为 `"xxx"`：
     - `ANTHROPIC_API_KEY`
     - `ANTHROPIC_BASE_URL`（第三方 API 地址属于保密信息）
   - 已有 `"xxx"` 占位符的不重复处理
4. **🔐 过滤密钥** — 对所有 JSON 配置执行密钥脱敏处理：
   - 扫描 `opencode.json` 和 `oh-my-openagent.json` 中所有字段
   - 匹配以下 key 名称（大小写不敏感）的值，替换为占位符：
     - `apiKey` / `api_key` → `"xxx"`
     - `baseURL` / `base_url` → `"xxx"`（API 地址同样保密）
     - `token` / `secret` / `password` / `auth` → `"xxx"`
     - 包含 `figma` 且匹配上述规则的 → `"******"`
   - 已有 `"xxx"` 或 `"******"` 占位符的不重复处理
   - 确保 dot 仓库中**不会出现任何真实密钥或 API 地址**
5. 进入 dot 仓库：
   ```bash
   cd ~/CodeSpace/dot
   ```
6. 收集变更摘要（`git diff --stat` + `git status --short` + `git diff --name-status`）
7. 检查未跟踪文件
8. 构建 commit message，包含：
   - OS、发行版（`lsb_release -d`）、主机名（`hostname`）
   - 每条变更的文件名与状态
   - 时间戳
   - 本地与 dot 的关键差异说明
9. git add + commit + push

**Commit message 模板**：
```
sync: push <内容摘要>

OS: <os>/<distro> | <hostname>
Time: <timestamp>
Dot SHA: <before> → <after>

变更清单:
<git diff --name-status>

差异说明:
- <关键差异>
```

**密钥过滤脚本参考（Python）：**
```python
import json

def redact_secrets(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            key_lower = k.lower()
            secret_fields = ['apikey', 'api_key', 'token', 'secret', 'password', 'auth']
            if any(kw in key_lower for kw in secret_fields):
                if isinstance(v, str) and v not in ('xxx', '******', ''):
                    obj[k] = '******' if 'figma' in key_lower else 'xxx'
            else:
                redact_secrets(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for item in obj:
            redact_secrets(item, path)
    return obj
```

### pull（dot 仓库 → 本地）

1. `cd ~/CodeSpace/dot && git pull`
2. 反向 rsync skills 到本地
3. cp 配置文件到本地
4. 验证：`diff -rq <dot_skills> <local_skills>`
5. **Claude Code 配置恢复**: 如果 `~/CodeSpace/dot/claude/settings.json` 存在，询问用户是否恢复：
   - 如果用户确认：`cp ~/CodeSpace/dot/claude/settings.json ~/.claude/settings.json`
   - 然后提示用户补全 ANTHROPIC_API_KEY
6. **🔑 检查并补全 API Key** — 扫描本地配置中被脱敏的密钥字段，逐个提示用户：

   扫描逻辑：
   - 递归遍历 `opencode.json`，找出所有值为 `"xxx"` 或 `"******"` 的字段
   - 通过字段名和上下文判断该密钥属于哪个 provider/MCP

   对每个缺失密钥，向用户提问：
   > 「`{provider}.{field}` 的密钥当前为占位符，请输入真实密钥（或输入 `skip` 跳过）」

   **特殊情况处理：**
   - 如果用户输入 `skip`，保留占位符（该供应商不可用但不影响其他功能）
   - 如果整个 provider 的 apiKey 被跳过，可进一步询问：「是否需要从配置中移除该 provider？」
   - 用户输入的密钥直接写入本地文件，**不会回传到 dot 仓库**
6. 输出恢复摘要，报告每个 provider 的状态（已配置/已跳过）

---

## ⚠️ 重要说明：opencode.json 与 oh-my-openagent.json 的关系

这两个文件**各自独立生效**，不要混淆：

| 文件 | 作用 | 控制谁 |
|------|------|--------|
| `opencode.json` → `provider` 段 | 定义模型、API Key、baseURL | 模型本身的接入配置 |
| `opencode.json` → `agent` 段 | 定义 agent 的 fallback_models | OpenCode 原生 agent 回退策略 |
| `oh-my-openagent.json` → `agents` 段 | 定义每个 agent 使用的 model + variant + fallback | **OhMyOpenAgent 插件的实际 model routing** |

**关键要点：**
- 只改 `opencode.json` 的 `agent` 段，不改 `oh-my-openagent.json`，agent 路由**不会生效**
- 只改 `oh-my-openagent.json`，不改 `opencode.json` 的 `provider` 段，模型**接不进来**
- **修改 agent 路由时，`oh-my-openagent.json` 才是真正生效的配置**

**变更示例（agent 模型切换）：**
```bash
# 需要同步修改这两处，agent 路由才会生效：
# 1. ~/.config/opencode/oh-my-openagent.json  → agents.{name}.model
# 2. ~/.config/opencode/opencode.json          → agent.{name}.fallback_models（备选，用于原生回退）
```

---

## 安全检查

- **push 前**：检查 dot 是否有未提交变更 → 先提交或询问用户覆盖
- **pull 前**：提示用户本地变更将被覆盖
- **路径不存在**：pull 时自动创建；push 时跳过并 Warn
