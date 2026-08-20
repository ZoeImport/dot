---
name: beautifyclaude
description: 同步 Claude Desktop 与 Claude Code 的 MCP 配置，并将 model 名称修正为官方格式。当用户说"同步 mcp"、"对齐 claude 配置"、"beautifyclaude"、"同步 claude desktop 的 mcp"、"修正模型名"时使用。
allowed-tools: Bash, Read, Edit, Write
---

# Skill: beautifyclaude — Claude 配置对齐

将 Claude Desktop 的非业务 MCP 配置同步到 Claude Code，并修正 model 名称为官方标准格式。

---

## 触发条件

用户说"同步 mcp"、"对齐 claude 配置"、"beautifyclaude"、"同步 claude desktop 的 mcp"、"修正模型名"时触发。

---

## 关键文件路径（macOS）

| 文件 | 说明 |
|------|------|
| `~/Library/Application Support/Claude/claude_desktop_config.json` | Claude Desktop 配置（MCP 来源） |
| `~/.claude/settings.json` | Claude Code 用户级配置（model、env、hooks 等） |
| `~/.claude.json` | Claude Code 运行时数据，**实际生效的 MCP 在此** |

### `~/.claude.json` 中 MCP 的两个层级

- **User MCPs**：顶层 `mcpServers` 字段（对所有项目生效）
- **Local MCPs**：`projects.<绝对路径>.mcpServers`（仅对指定项目生效）

截图中显示的 "Local MCPs" 来源是 `~/.claude.json` 的项目级配置，不是 `settings.json`。

---

## ⚠️ 同步范围限制

**不可同步的 MCP 类型：**
- 数据库连接 MCP（包含 connection string、账号密码的任何 MCP）
- 包含业务信息的 MCP（业务库名、内网地址、服务账号等）

**可同步的 MCP 类型：**
- 通用工具类 MCP（如 codegraph、文件系统、搜索等无业务数据的工具）

同步前**必须逐条展示给用户确认**，由用户判断哪些可以同步。

---

## 操作一：同步 MCP 配置

### 步骤 1：读取 Claude Desktop MCP

```bash
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

提取 `mcpServers` 中所有条目。

### 步骤 2：查找 Claude Code 当前项目 MCP

```bash
python3 -c "
import json
with open('/Users/zoe/.claude.json') as f:
    d = json.load(f)
for path, proj in d.get('projects', {}).items():
    if proj.get('mcpServers'):
        print(path, list(proj['mcpServers'].keys()))
"
```

询问用户：要同步到哪个项目？

### 步骤 3：展示差异，由用户决定同步哪些

对比 Desktop 与目标项目的 `mcpServers`，展示：
- 仅存在于 Desktop 的条目（待添加候选）
- 连接字符串不同的条目（需用户判断）

**展示每条后询问用户是否同步，不批量处理。**

### 步骤 4：写入 `~/.claude.json`

**必须用 Python JSON 读写**，不可用文本编辑工具直接操作（Claude Code 进程并发写入会损坏文件）：

```python
import json

path = '/Users/zoe/.claude.json'
with open(path) as f:
    d = json.load(f)

proj = d['projects']['<项目路径>']
proj['mcpServers']['<mcp名称>'] = {
    'command': '...',
    'args': ['...']
}

with open(path, 'w') as f:
    json.dump(d, f, indent=2, ensure_ascii=False)
```

---

## 操作二：修正 model 名称

### 检查当前 model

```bash
python3 -c "import json; d=json.load(open('/Users/zoe/.claude/settings.json')); print(d.get('model','未设置'))"
```

### 官方模型名称对照

| 非标准写法（第三方扩展格式） | 官方标准名称 |
|-----------------------------|-------------|
| `sonnet[1m]` | `claude-sonnet-4-6` |
| `opus[1m]` | `claude-opus-4-8` |
| `haiku[1m]` | `claude-haiku-4-5` |

修正后写入 `~/.claude/settings.json` 的 `"model"` 字段。

---

## 操作三：验证

```bash
python3 -c "import json; json.load(open('/Users/zoe/.claude.json')); print('claude.json OK')"
python3 -c "import json; json.load(open('/Users/zoe/.claude/settings.json')); print('settings.json OK')"
```

完成后提示：建议执行 `sync-dot push` 将 `settings.json` 备份到 dot 仓库。
