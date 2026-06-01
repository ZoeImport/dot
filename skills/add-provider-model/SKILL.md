---
name: add-provider-model
description: 添加新的 Provider 或向现有 Provider 添加模型。当用户说"添加 provider"、"引入新的模型"、"添加 API 提供商"、"配置新的模型提供商"、"add provider"、"往现有供应商添加模型"、"添加模型到现有 provider"时触发。支持两种操作：1) 添加新的 Provider；2) 向现有 Provider 添加模型。会自动查询真实模型参数确保配置准确。
allowed-tools: Bash, Read, Write
---

# Skill: 引入新的 Provider 与 Model

## 功能概述

本 Skill 支持两类操作：
1. **添加新的 Provider** — 创建全新的 provider 配置
2. **向现有 Provider 添加模型** — 在已有 provider 下增加新的模型

---

## 功能一：添加新的 Provider

### 步骤 1：询问操作类型
询问用户是要"添加新的 Provider"还是"向现有 Provider 添加模型"。

### 步骤 2：询问 SDK 类型
询问这个 provider 支持哪几种 SDK（可多选）：

| SDK 类型 | 说明 | 注意事项 |
|---------|------|---------|
| `@ai-sdk/openai-compatible` | OpenAI 兼容格式 | baseURL 需加 `/v1` 后缀 |
| `@ai-sdk/anthropic` | Anthropic 原生格式 | baseURL 不加 `/v1`，SDK 自动拼接 |

### 步骤 3：询问 Provider 基础信息

**Provider 名称** — 内部标识符，如 `tag`、`mypov`

**API Key**

**Base URL** — 供应商的 API 端点
- OpenAI 兼容格式：`https://api.example.com/v1`
- Anthropic 格式：`https://api.example.com`（不加 `/v1`）

**显示名称** — 给用户看到的名字，如 `Tag (Anthropic 原生)`

### 步骤 4：询问要添加的模型

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

### 步骤 5：确认并写入配置

生成完整的 provider 配置块，展示给用户确认（包含所有通过自动查询获得的真实参数），然后写入 `~/.config/opencode/opencode.json`

---

## 功能二：向现有 Provider 添加模型

### 步骤 1：列出现有 Provider
展示所有已配置的 provider 列表，让用户选择要向哪个 provider 添加模型。

### 步骤 2：询问新的模型信息
按照功能一步骤 4 的方式收集模型信息。

### 步骤 3：确认并更新配置
展示变更内容，写入配置。

---

## 配置格式参考

### openai-compatible 格式
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

### anthropic 格式
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

## 注意事项
- 写入前先读取现有 `opencode.json` 内容
- 写入时合并到现有 provider 中，不要覆盖其他 provider
- 写入后展示最终配置让用户确认
- variants 尽量完整配置，包含 medium/high/xhigh/max 等常见级别
