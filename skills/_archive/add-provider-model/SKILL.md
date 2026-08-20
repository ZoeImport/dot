---
name: add-provider-model
description: 添加新的 Provider、向现有 Provider 添加模型、或将 provider 配置同步到 Claude Code settings。当用户说"添加 provider"、"引入新的模型"、"添加 API 提供商"、"配置新的模型提供商"、"add provider"、"往现有供应商添加模型"、"添加模型到现有 provider"、"更换供应商"、"tcc换供应商"时会触发。支持三种操作：1) 添加新的 Provider；2) 向现有 Provider 添加模型；3) 将 opencode 中的 provider 配置同步到 Claude Code settings 文件。会自动查询真实模型参数确保配置准确。
allowed-tools: Bash, Read, Write
---

# Skill: 引入新的 Provider 与 Model

## 功能概述

本 Skill 支持三类操作：
1. **添加新的 Provider** — 创建全新的 provider 配置到 `opencode.json`
2. **向现有 Provider 添加模型** — 在已有 provider 下增加新的模型
3. **同步到 Claude Code settings** — 将 opencode 中的 provider 配置（baseURL/apiKey）同步到 `~/.claude/*.json` settings 文件

---

## 第一步：确定操作类型

```
用户说"添加 provider" / "加模型" / "换供应商"
    │
    ├── "加新的 provider" ──→ 功能一
    ├── "往现有 provider 加模型" ──→ 功能二
    └── "把 opencode 的 X provider 同步到 claude code settings"
         │
         └── 功能三
```

询问用户操作类型：
- "添加新的 Provider" — 在 opencode.json 中创建全新 provider 配置
- "向现有 Provider 添加模型" — 在已有 provider 下增加模型
- "将 opencode 的某个 provider 同步到 Claude Code settings" — 把 provider 的 baseURL/apiKey 写到 `~/.claude/*.json`

---

## 功能一：添加新的 Provider 到 opencode.json

### 步骤 1：询问 SDK 类型
询问这个 provider 支持哪几种 SDK（可多选）：

| SDK 类型 | 说明 | 注意事项 |
|---------|------|---------|
| `@ai-sdk/openai-compatible` | OpenAI 兼容格式 | baseURL 需加 `/v1` 后缀 |
| `@ai-sdk/anthropic` | Anthropic 原生格式 | baseURL 不加 `/v1`，SDK 自动拼接 |

### 步骤 2：询问 Provider 基础信息

**Provider 名称** — 内部标识符，如 `tag`、`mypov`

**API Key**

**Base URL** — 供应商的 API 端点
- OpenAI 兼容格式：`https://api.example.com/v1`
- Anthropic 格式：`https://api.example.com`（不加 `/v1`）

**显示名称** — 给用户看到的名字，如 `Tag (Anthropic 原生)`

### 步骤 3：询问要添加的模型

为每个模型收集信息：

| 字段 | 说明 | 示例 |
|------|------|------|
| `model_id` | API 中的模型 ID | claude-opus-4-6 |
| `name` | **显示名称**（格式：`基础名(provider名)`） | Claude Opus 4.6 (tag) |
| `context_limit` | 上下文窗口大小 | 1000000 |
| `output_limit` | 最大输出 tokens | 128000 |
| `input_modalities` | 支持的输入类型 | text, image |
| `variants` | 模型变体（可选） | medium, high, xhigh, max |

#### 显示名称命名规范
模型的 `name` 字段格式为：`基础名称 (Provider名称)`

示例：
- Provider 名为 `tag`，模型为 `claude-opus-4-6` → 显示名：`Claude Opus 4.6 (tag)`
- Provider 名为 `ppchat`，模型为 `gpt-5.4` → 显示名：`GPT-5.4 (ppchat)`

#### 自动查询真实参数（重要！）
**默认行为：** 每个模型的 `context_limit`、`output_limit`、`modalities`、`variants` 等参数必须**主动从网络查询真实信息**，保证配置完整准确。

查询方式：
1. 查阅官方文档（如 https://docs.anthropic.com/en/docs/about-claude/models、https://ai.google.dev/gemini-api/docs/models 等）
2. 调用 API 的 `/v1/models` 端点获取模型列表
3. 如无法查询到精确参数，使用公开的模型规格作为默认值

**用户指定覆盖：** 如果用户在添加时主动指定了某个参数（如 `output_limit=64000`），则以用户指定的为准。

#### Variants 参数参考

**Claude 模型 variants 示例：**
```json
"variants": {
  "medium": { "effort": "medium" },
  "high": { "effort": "high" },
  "xhigh": { "effort": "xhigh" },
  "max": { "effort": "max" }
}
```

**Anthropic thinking 变体（如果有）：**
```json
"variants": {
  "low": { "thinkingConfig": { "thinkingBudget": 8192 } },
  "max": { "thinkingConfig": { "thinkingBudget": 32768 } }
}
```

**Gemini 模型 variants 示例：**
```json
"variants": {
  "low": { "thinkingLevel": "low" },
  "high": { "thinkingLevel": "high" }
}
```

### 步骤 4：确认并写入配置

生成完整的 provider 配置块，展示给用户确认（包含所有通过自动查询获得的真实参数），然后写入 `~/.config/opencode/opencode.json`

---

## 功能二：向现有 Provider 添加模型

### 步骤 1：列出现有 Provider
展示 opencode.json 中所有已配置的 provider 列表，让用户选择要向哪个 provider 添加模型。

### 步骤 2：询问新的模型信息
按照功能一步骤 3 的方式收集模型信息。

### 步骤 3：确认并更新配置
展示变更内容，写入 opencode.json。

### 步骤 4：询问是否需要同步到 Claude Code settings
如果该 provider 的配置（baseURL/apiKey）对 claude code 也有用，询问用户是否要同步。
如果是，走功能三的步骤 2-3。

---

## 功能三：将 opencode provider 配置同步到 Claude Code settings

**触发场景：**
- 用户说"把 tcc 换成 infery 的配置"
- 用户说"把某 provider 的 baseURL/apiKey 同步到 claude code"
- 用户说"改 claude code 的供应商配置"

### 步骤 1：确定来源 provider
1. 读取 `~/.config/opencode/opencode.json` 的 `provider` 段，列出所有 provider
2. 询问用户：从哪个 provider 获取配置？

### 步骤 2：确定目标 Claude Code settings 文件
查找用户的 Claude Code settings 文件：
1. 读取 `~/.config/fish/config.fish`（或其他 shell rc），查找 `alias` 定义中 `--settings` 指向的 `~/.claude/*.json` 文件
2. 也检查 `~/.claude/` 下有哪些 settings JSON 文件（如 `tag.json`、`deepseek.json`、`kimi.json`）
3. 列出所有找到的 settings 文件供用户选择

### 步骤 3：确定 SDK 类型并映射环境变量

根据 opencode provider 的 `npm` 字段确定 SDK 类型，映射到 claude code 的环境变量：

| opencode npm 字段 | Claude Code 环境变量 | 值来源 |
|------------------|---------------------|--------|
| `@ai-sdk/anthropic` | `ANTHROPIC_BASE_URL` | provider options.baseURL（**不加** `/v1`） |
| | `ANTHROPIC_API_KEY` | provider options.apiKey |
| `@ai-sdk/openai-compatible` | `ANTHROPIC_BASE_URL` | provider options.baseURL |
| | `ANTHROPIC_API_KEY` | provider options.apiKey（或 `ANTHROPIC_AUTH_TOKEN`） |
| `@ai-sdk/openai` | `ANTHROPIC_BASE_URL` | provider options.baseURL（含 `/v1`） |
| | `ANTHROPIC_API_KEY` | provider options.apiKey |

### 步骤 4：保留原有模型配置
Claude Code 的 settings 文件中通常还包含模型相关变量（如 `ANTHROPIC_DEFAULT_OPUS_MODEL` 等），**这些不要动**，只替换 baseURL 和 API Key。

### 步骤 5：确认并写入
1. 展示将要做的变更（旧值 → 新值）
2. 用户确认后写入 `~/.claude/*.json`
3. 验证 JSON 合法性：`python3 -c "import json; json.load(open('~/.claude/xxx.json')); print('OK')"`

---

## 配置格式参考

### opencode.json — openai-compatible 格式
```json
"provider_name": {
  "npm": "@ai-sdk/openai-compatible",
  "name": "显示名称",
  "options": {
    "baseURL": "https://api.example.com/v1",
    "apiKey": "sk-xxx"
  },
  "models": {
    "model_id": {
      "name": "基础名称 (provider名)",
      "limit": {
        "context": 1000000,
        "output": 128000
      },
      "modalities": {
        "input": ["text", "image"],
        "output": ["text"]
      },
      "variants": {
        "medium": { "effort": "medium" },
        "high": { "effort": "high" }
      }
    }
  }
}
```

### opencode.json — anthropic 格式
```json
"provider_name": {
  "npm": "@ai-sdk/anthropic",
  "name": "显示名称",
  "options": {
    "baseURL": "https://api.example.com",
    "apiKey": "sk-xxx"
  },
  "models": {
    "model_id": {
      "name": "基础名称 (provider名)",
      "limit": {
        "context": 1000000,
        "output": 128000
      },
      "modalities": {
        "input": ["text", "image"],
        "output": ["text"]
      },
      "variants": {
        "high": { "effort": "high" },
        "xhigh": { "effort": "xhigh" }
      }
    }
  }
}
```

### Claude Code settings 格式
```json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "env": {
    "ANTHROPIC_BASE_URL": "https://api.example.com",
    "ANTHROPIC_API_KEY": "sk-xxx",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "claude-opus-4-7",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "claude-sonnet-4-6",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "claude-haiku-4-5"
  }
}
```

## 注意事项
- **opencode.json** 写入前先读取现有内容，合并到现有 provider 中，不要覆盖其他 provider
- **Claude Code settings** 只替换 baseURL 和 API Key，保留原有的模型配置变量
- 写入后展示最终配置让用户确认
- variants 尽量完整配置，包含 medium/high/xhigh/max 等常见级别

---

## 额外步骤：更新 OhMyOpenAgent Model Routing

添加 Provider/Model 后，`opencode.json` 的变更**不会自动同步**到 `oh-my-openagent.json`。

`oh-my-openagent.json` 是控制 agent model routing 的独立文件（OhMyOpenAgent 插件实际使用它做模型分发），而 `opencode.json` 的 `provider` 段只是定义模型本身。**两者各自独立生效。**

### 何时需要更新 oh-my-openagent.json

| 场景 | 需要更新？ |
|------|-----------|
| 只是新增一个 provider，不改 agent 路由 | ❌ 不需要 |
| 新增 model 后想分配给某些 agent 使用 | ✅ 需要更新 agent 的 `model` 或 `fallback_models` |
| 新增 provider 后想把部分 agent 切过去 | ✅ 需要更新对应 agent 的 `model` 字段 |

### 操作方式

更新完成后，询问用户：「是否需要将新加的 model/provider 配置到某些 agent 的 model routing？如果需要，要更新哪些 agent？」

如需更新：
1. 读取 `~/.config/opencode/oh-my-openagent.json`
2. 找到对应 agent 的 `model` 或 `fallback_models` 字段
3. 写入新的 `{provider}/{model_id}` 格式引用
4. 验证 JSON 合法性

### 同步提醒

配置更新后建议执行 `sync-dot push` 将本地配置同步到 dot 仓库。
