# dot — AI Agent Configuration Repository

> Personal environment setup for OpenCode/OhMyOpenCode, including provider configs, skills, and agent definitions. Designed to be **public-ready** — all secrets are redacted as `xxx`.

---

## 📖 Human Guide

### Structure

```
dot/
├── README.md
├── opencode/
│   ├── opencode.json            # OpenCode: providers, MCP, agents
│   └── oh-my-openagent.json     # OhMyOpenAgent: agent categories, model routing
└── skills/                      # Agent skill collection
    ├── add-provider-model/
    ├── docx-template/           # DOCX generation via docxtemplater + raw XML
    ├── ... (20+ skills)
```

### Installation (Manual)

> ⚠️ **Repository visibility:** This repo is **public**. If you encounter 404 / access denied errors, check:
> - Did you clone the correct URL? `git clone https://github.com/ZoeImport/dot.git`
> - If you're trying a private fork, ensure your SSH key or token is configured
> - All files are browsable directly on GitHub without cloning: https://github.com/ZoeImport/dot

```bash
# 1. Clone the repo (public, no auth needed)
git clone https://github.com/ZoeImport/dot.git ~/CodeSpace/dot

# 2. OpenCode config
cp -r opencode/* ~/.config/opencode/

# 3. Skills
cp -r skills/ ~/.agents/skills/

# 4. Install OpenCode plugins (required: oh-my-openagent + superpowers):
cd ~/.config/opencode && npm install oh-my-openagent@latest
npm install superpowers@git+https://github.com/obra/superpowers.git

# 5. If plugin auto-install is enabled in opencode.json, skip step 4 —
#    plugins install automatically on first launch (see plugin field in opencode.json)
```

### Required: Configure API Keys

All provider API keys are set to `xxx` for public safety. **You MUST configure them before use:**

| Provider | Config Location | Purpose |
|----------|----------------|---------|
| Tag (ath) | `opencode.json` → `provider.tag-native.options.apiKey` | Claude Opus/Sonnet, GPT-5 |
| DeepSeek | `opencode.json` → `provider.deepseek.options.apiKey` | DeepSeek V4 Pro/Flash |
| Unlimited | `opencode.json` → `provider.unlimited.options.apiKey` | Free models (Kimi K2.6) |
| Figma | `opencode.json` → `mcp.figma.environment.FIGMA_API_KEY` | Figma MCP integration |

**Edit command:**
```bash
# Open with your editor and search for "xxx"
vim ~/.config/opencode/opencode.json
# or: code ~/.config/opencode/opencode.json
```

---

## 🤖 Agent Setup Prompt

> Copy the block below and paste it to your AI agent for one-click setup.
> This prompt handles: repo cloning, plugin installation, skill deployment, API key configuration, and verification.

<details>
<summary><b>📋 Click to copy — English (recommended for all AI agents)</b></summary>

```
You are setting up OpenCode using the config repository https://github.com/ZoeImport/dot

REPOSITORY IS PUBLIC. If git clone or any file fetch returns 404/access denied:
  - Check that the URL is correct (public repo, no auth needed)
  - The repo is browsable at https://github.com/ZoeImport/dot — you can read any file directly
  - If you were given a different URL, ask the user to confirm
  - Do NOT assume the repo is private unless the user explicitly says so

## Phase 1 — Clone and Copy Files

1. Clone the repo:
   `git clone https://github.com/ZoeImport/dot.git ~/CodeSpace/dot`
   If clone fails, ask the user: "Is the repo URL correct? Or is this a private fork with a different URL?"

2. Copy config files:
   `cp -r ~/CodeSpace/dot/opencode/* ~/.config/opencode/`

3. Copy skills:
   `mkdir -p ~/.agents/skills/ && cp -r ~/CodeSpace/dot/skills/* ~/.agents/skills/`

## Phase 2 — Install Plugins

OpenCode.json defines these plugins (auto-install on first launch is supported):
  - `oh-my-openagent@latest` — agent categories, model routing, fallback logic
  - `superpowers@git+https://github.com/obra/superpowers.git` — skill system, brainstorming, subagent-driven development, TDD, verification, and more
  - `opencode-worktree@latest` — worktree management

Run to ensure they're installed:
  `cd ~/.config/opencode && npm install oh-my-openagent@latest superpowers@git+https://github.com/obra/superpowers.git`

## Phase 3 — Configure API Keys

PROMPT me for the following API keys ONE BY ONE. After I provide each one, replace the placeholder in `~/.config/opencode/opencode.json`. Do NOT proceed to the next key before I answer.

  a) Tag API Key (ath) — REQUIRED. Needed for: Claude Opus 4.7, Sonnet 4.6, GPT-5.x
     → Location: `provider.tag-native.options.apiKey`
  b) DeepSeek API Key — REQUIRED. Needed for: DeepSeek V4 Pro/Flash
     → Location: `provider.deepseek.options.apiKey`
  c) Unlimited API Key (yygu.cn) — OPTIONAL. Free Kimi K2.6 model
     → Location: `provider.unlimited.options.apiKey`
  d) Figma Personal Access Token — OPTIONAL. For Figma MCP design integration
     → Location: `mcp.figma.environment.FIGMA_API_KEY`

If I say "skip" or "not now", leave the value as `"xxx"` — that provider will simply be unavailable without breaking anything.

## Phase 4 — Verify

1. Validate JSON: `node -e "JSON.parse(fs.readFileSync(require('os').homedir()+'/.config/opencode/opencode.json','utf8'))"`
2. Check no remaining real secrets: all apiKey fields should either be "xxx" (placeholder) or a real key the user provided — never accidentally leaked values
3. Confirm plugin registration: `ls ~/.config/opencode/node_modules/ | grep -E 'oh-my-openagent|superpowers|opencode-worktree'`
4. Report which providers are READY (key provided), which are SKIPPED (still xxx), and whether plugins are installed

## Summary Report Template

Send me a summary like:
  ✅ Clone success | Config copied | Skills deployed
  ✅ Plugins: oh-my-openagent, superpowers, opencode-worktree
  🔑 Tag: configured | DeepSeek: configured | Unlimited: skipped | Figma: skipped
  📋 All JSON valid
```
</details>

<details>
<summary><b>📋 点击复制 — 中文版 (适合中文用户/Agent)</b></summary>

```
你正在使用配置仓库 https://github.com/ZoeImport/dot 来设置 OpenCode

本仓库是公开的。如果 git clone 或文件读取返回 404/无权限：
  - 确认 URL 是否正确（公开仓库不需要认证）
  - 可以在 https://github.com/ZoeImport/dot 直接浏览所有文件
  - 如果用户给了其他 URL，请让用户确认
  - 不要假设仓库是私有的，除非用户明确说明

## 第一步 — 克隆和复制文件

1. 克隆仓库：`git clone https://github.com/ZoeImport/dot.git ~/CodeSpace/dot`
2. 复制配置：`cp -r ~/CodeSpace/dot/opencode/* ~/.config/opencode/`
3. 复制技能：`mkdir -p ~/.agents/skills/ && cp -r ~/CodeSpace/dot/skills/* ~/.agents/skills/`

## 第二步 — 安装插件

opencode.json 中定义了以下插件（首次启动会自动安装）：
  - `oh-my-openagent@latest` — Agent 分类、模型路由、回退逻辑
  - `superpowers@git+https://github.com/obra/superpowers.git` — 技能系统、头脑风暴、TDD、验证等
  - `opencode-worktree@latest` — 工作区管理

确保安装：`cd ~/.config/opencode && npm install oh-my-openagent@latest superpowers@git+https://github.com/obra/superpowers.git`

## 第三步 — 配置 API Key

逐个向我询问以下 API Key。每提供一个，立即替换 `~/.config/opencode/opencode.json` 中的占位符。不回答完不上一个问下一个：

  a) Tag API Key (ath) — 必填。用于 Claude Opus 4.7, Sonnet 4.6, GPT-5.x
  b) DeepSeek API Key — 必填。用于 DeepSeek V4 Pro/Flash
  c) Unlimited API Key (yygu.cn) — 可选。免费 Kimi K2.6
  d) Figma Personal Access Token — 可选。Figma MCP 集成

如果我说"跳过"，则保留 `"xxx"`，不影响其他功能。

## 第四步 — 验证

1. `node -e "JSON.parse(fs.readFileSync(require('os').homedir()+'/.config/opencode/opencode.json','utf8'))"`
2. 确认所有 apiKey 要么是 "xxx"（占位）要么是用户提供的真实 Key
3. 确认插件已安装：`ls ~/.config/opencode/node_modules/ | grep -E 'oh-my-openagent|superpowers|opencode-worktree'`
4. 向我汇报哪些提供商已就绪，哪些已跳过
```
</details>

---

## Provider Model Summary

| Provider | Models | Best For |
|----------|--------|----------|
| Tag (ath) | Claude Opus 4.7, Sonnet 4.6, GPT-5.5/5.4 | Critical reasoning, vision |
| DeepSeek | DeepSeek V4 Pro, DeepSeek V4 Flash | General tasks, coding |
| Unlimited | Kimi K2.6 | Free lightweight tasks |

Model routing logic (in `oh-my-openagent.json`): expensive models only for tasks that need them (oracle, ultrabrain), cheaper models for everything else.

---

## Skills Included

| Skill | Description |
|-------|-------------|
| `add-provider-model` | Add new AI provider or model to OpenCode config |
| `agent-browser` | Browser automation CLI for AI agents |
| `defect-handler` | Full bug analysis → fix workflow |
| `deploy-service` | Deploy dotpen-api services (GitLab CI) |
| `docx-template` | Generate DOCX with docxtemplater + raw XML |
| `fix-branch-pr` | Auto-detect target, create fix branch, PR |
| `git-commit-push-pr` | Commit → push → MR automation |
| `git-worktree-pull` | Pull latest code in git worktree |
| `md-to-docx-with-mermaid` | Convert markdown → docx with mermaid diagrams |
| `network-domain-debug` | DNS/network troubleshooting |
| `quick-db-read` | One-shot MySQL read via Go test |
| `review-and-pr` | Code review + commit + PR in one flow |
| `reviewcode` | Go code style review |
| `sync-dot` | Sync local config → this dot repo |
| `technical-solution-doc` | Generate tech design documents |
| `unit-test-generate` | Generate unit tests |
| `weekly-report` | Generate weekly report from GitLab commits |
