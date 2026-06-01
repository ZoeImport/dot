---
name: sync-dot
description: 同步本地 OpenCode/OhMyOpenCode 配置与 skills 到 dot 仓库，或从 dot 仓库恢复到本地。支持双向同步、跨平台路径、自动 git commit。
---

# Sync Dot — 配置仓库同步技能

将本地 OpenCode/OhMyOpenCode 配置和 skills 同步到 `~/CodeSpace/dot` 版本仓库（`push`），或从仓库恢复到本地（`pull`）。

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

### 平台路径差异

不同操作系统下本地路径不同，当前支持 Linux 直接映射，其他 OS 询问用户：

| OS | Skills 路径 | OpenCode 配置路径 |
|----|------------|-------------------|
| Linux | `~/.agents/skills/` | `~/.config/opencode/` |
| macOS (待确认) | `~/Library/Application Support/io.opencode/skills/` | `~/Library/Application Support/opencode/` |
| Windows (待确认) | `%APPDATA%\opencode\skills\` | `%APPDATA%\opencode\` |

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
2. 同步 skills：
   ```bash
   rsync -av --delete <local_skills>/ <dot_skills>/
   ```
3. 同步配置文件（逐个 cp）
4. 进入 dot 仓库：
   ```bash
   cd ~/CodeSpace/dot
   ```
5. 收集变更摘要（`git diff --stat` + `git status --short` + `git diff --name-status`）
6. 检查未跟踪文件
7. 构建 commit message，包含：
   - OS、发行版（`lsb_release -d`）、主机名（`hostname`）
   - 每条变更的文件名与状态
   - 时间戳
   - 本地与 dot 的关键差异说明
8. git add + commit + push

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

### pull（dot 仓库 → 本地）

1. `cd ~/CodeSpace/dot && git pull`
2. 反向 rsync skills 到本地
3. cp 配置文件到本地
4. 验证：`diff -rq <dot_skills> <local_skills>`
5. 输出恢复摘要

---

## 安全检查

- **push 前**：检查 dot 是否有未提交变更 → 先提交或询问用户覆盖
- **pull 前**：提示用户本地变更将被覆盖
- **路径不存在**：pull 时自动创建；push 时跳过并 Warn
