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

```bash
# 1. OpenCode config
cp opencode/opencode.json ~/.config/opencode/opencode.json
cp opencode/oh-my-openagent.json ~/.config/opencode/oh-my-openagent.json

# 2. Skills
cp -r skills/ ~/.agents/skills/

# 3. Install OpenCode plugins (auto-installed on launch, or manual):
cd ~/.config/opencode && npm install oh-my-openagent@latest
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

```
You are setting up OpenCode from https://github.com/ZoeImport/dot

## Task

1. PROMPT me for the following API keys (one by one, do NOT proceed without my input):
   - Tag API Key (ath) — required for Claude Opus 4.7, Sonnet 4.6, GPT-5.x
   - DeepSeek API Key — required for DeepSeek V4 Pro/Flash
   - Unlimited API Key (yygu.cn) — optional, for free Kimi K2.6 model
   - Figma Personal Access Token — optional, for Figma MCP integration

2. After I provide each key, replace the corresponding `"apiKey": "xxx"` placeholder in `~/.config/opencode/opencode.json`.

3. If I say "skip" or "not now" for any key, leave it as `xxx` — the provider will be unavailable but won't break anything.

4. After all keys are configured, verify the file is valid JSON by running:
   `node -e "JSON.parse(fs.readFileSync('~/.config/opencode/opencode.json','utf8'))"`

5. Report which providers are configured and which are still placeholder.

## Files to Configure

| File | Path |
|------|------|
| OpenCode config | `~/.config/opencode/opencode.json` |
| Agent config | `~/.config/opencode/oh-my-openagent.json` (no keys needed) |
| Skills | `~/.agents/skills/` (already copied) |

## API Key Locations in opencode.json

- `provider.tag-native.options.apiKey` → "xxx" (Tag AI proxy)
- `provider.deepseek.options.apiKey` → "xxx" (DeepSeek official)
- `provider.unlimited.options.apiKey` → "xxx" (Free model proxy)
- `mcp.figma.environment.FIGMA_API_KEY` → "xxx" (Figma integration)

## Verification

After configuration, confirm:
- [ ] Tag provider works (test: `opencode message -m "hello" -p tag-native/gpt-5.4`)
- [ ] DeepSeek provider works
- [ ] JSON is valid (parse check)
- [ ] No remaining "xxx" in apiKey fields (unless intentionally skipped)
```

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
