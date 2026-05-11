# dot

Zoe 的环境配置仓库。

## Structure

```
dot/
├── README.md
├── opencode/        # OpenCode + oh-my-openagent 配置
│   ├── opencode.json
│   └── oh-my-openagent.json
└── skills/          # Agent skill 集合
```

## 新机器安装步骤

### 1. Hyprland 桌面环境

```bash
bash <(curl -s https://ii.clsty.link/get)
```

备选：
```bash
git clone https://github.com/end-4/dots-hyprland.git
```

### 2. OpenCode 配置

```bash
cp opencode/opencode.json ~/.config/opencode/opencode.json
cp opencode/oh-my-openagent.json ~/.config/opencode/oh-my-openagent.json
```

### 3. 安装 OpenCode 插件

启动 opencode 后，系统会自动安装 `oh-my-openagent` 等插件（配置在 `opencode.json` 的 `plugin` 字段中）。如需手动安装：

```bash
cd ~/.config/opencode && npm install oh-my-openagent@latest
```

### 4. Skills

```bash
cp -r skills/ ~/.agents/skills/
```

## 模型配置策略 (oh-my-openagent)

免费模型优先，付费模型仅用于关键推理任务：

| 类型 | 模型 | 适用 |
|------|------|------|
| 免费（无限） | GLM-5.1, GLM-5, Kimi-K2.6 | 大多数 agent 主力 |
| 付费（Tag） | Claude Opus 4.7 | oracle, ultrabrain (最强推理) |
| 付费（Tag） | Claude Sonnet 4.6 | multimodal-looker (vision) |
| 付费（Tag） | GPT-5.4 | fallback 性价比最优 |