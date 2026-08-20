---
name: weekly-report
description: 先检测本机存在的 AI 编程工具，再综合 Claude、Codex、Cursor、OpenCode 等工具历史与 Git 提交、测试、MR 和发布记录识别实际工作，交叉校验并生成或更新中文周报；任一数据源缺失时可独立工作。用于“写周报”“生成周报”“总结本周工作”“识别 AI/Agent 历史”“根据 Git 写周报”“weekly report”等请求。
---

# Weekly Report

兼容多种 AI 工具历史与 Git 两类数据源。先探测本机实际存在的工具和历史位置，再并行收集、交叉补全、按业务结果去重，不预设单一工具或主数据源。

## 工作流程

### 1. 锁定时间窗口

- 使用用户时区；默认取本周一 00:00 至下周一 00:00。
- 用户指定“上周”或日期时使用对应的闭开区间。
- 输出并确认绝对日期，避免把文件修改时间当作会话发生时间。

### 2. 检测 AI 工具与历史位置

先进行只读探测，不能因为当前运行在某个工具中就只扫描该工具。结合操作系统检查：

- 命令是否存在：`command -v codex claude cursor opencode aider`；
- 应用是否存在：macOS `/Applications`、Linux desktop entry、Windows 已安装应用；
- 配置、数据和历史目录是否存在；
- 数据目录存在但命令或应用已卸载时，仍将其作为历史来源。

常见候选位置如下，但不要把清单当作固定路径：

- Codex：`~/.codex/sessions/`、`~/.codex/archived_sessions/`、`~/.codex/history.jsonl`；
- Claude Code/Desktop：`~/.claude/projects/`、`~/.claude/transcripts/`、平台对应的 Claude Application Support 数据；
- Cursor：`~/.cursor/`、平台对应的 Cursor `workspaceStorage/`、`globalStorage/`、SQLite 状态库；
- OpenCode：`~/.local/share/opencode/`、`~/.config/opencode/` 中的 session、message、part、transcript 或数据库；
- 其他工具：Windsurf、Cline、Continue、Aider、Copilot 等实际存在的历史或日志目录。

输出本次发现的数据源及缺失项。对 SQLite 等数据库使用只读查询；不要修改、迁移或锁定原始历史库。避免无边界扫描整个用户目录。

### 3. 收集 AI 工具历史

只扫描上一步确认存在的历史源。按各工具的数据格式提取真实时间、会话 ID、项目路径和消息；优先使用记录内部的 timestamp、workspace/cwd/project 字段，不要仅依赖文件名或 mtime。

提取每个会话的：

- 用户的首个有效业务请求，排除环境上下文、skill 正文和系统注入文本；
- 最终回答、任务完成事件和关键工具结果；
- 文件修改、测试、commit、push、tag、部署等落地证据；
- `cwd` 对应的项目或业务模块。

将会话标记为：

- **已完成**：有明确交付物或可验证结果；
- **仅分析/诊断**：定位了问题但未实施修复；
- **未完成/失败**：中断、失败或结论未验证；
- **非工作项**：学习问答、个人环境问题、自动任务等。

同一请求在不同 AI 工具之间的接力、重试、子 Agent 和重复会话按最终业务结果合并，不能按工具数或 session 数计算工作量。

### 4. 收集 Git 与运行证据

对历史中涉及的仓库检查：

```bash
git log --all --since="起始日期" --until="结束日期" --author="作者别名" --oneline
git show --stat <commit>
git status --short
```

从所有相关仓库、分支和 worktree 收集 Git 记录，补充 Agent 历史未覆盖的人工提交。必要时检查测试结果、MR 状态、tag、部署或实际接口返回，以确认影响范围和最终效果。

AI 工具历史可以发现没有 commit 但确实完成的排障、验证、发布或文档交付；Git 可以发现未经过 AI 工具的代码工作。两者冲突时以当前仓库、运行环境和远端状态的可验证事实为准。

若只有一种数据源可用，继续生成周报并明确说明覆盖范围，不因另一种数据源缺失而中止。

### 5. 去重与业务化整理

- 将不同 AI 工具会话与 Git 记录按项目、功能、时间及最终效果关联，不能把同一工作重复写多次。
- 按最终业务效果合并 feat、fix、refactor、验证和发布任务。
- 同一功能的分析、实现、修复、测试、发布通常合并为一条；只有独立业务价值明显时拆分。
- 使用业务语言描述结果，必要时简述 bug 根因。
- 将未落地但有价值的诊断放入“风险与问题”，不要伪装为已完成产出。

### 6. 生成周报

```text
一、本周进展：

1. [业务结果]

二、风险与问题：

[暂无，或经过证据确认的风险]

三、下周计划：

[用户提供]
```

保存到 `weekly-reports/YYYY-Wxx.md`。如果用户只要求识别历史或直接回复，则先输出候选项，不写文件。

## 排除规则

1. 不写 MR 编号、commit hash、Agent/session 数量等内部过程信息。
2. 排除 ReviewCode 自审、纯规范修复、style、纯注释、godoc、swag 去重。
3. 排除 Merge、WIP、stash、快照提交及重复重试。
4. 排除自动晨报、普通学习问答、个人电脑使用问题和未产生业务结果的会话。
5. 代码审查本身不算产出；审查推动并验证完成的实际业务修复可以写最终效果。
6. 不暴露历史中的 API Key、token、密码、内部请求正文或其他敏感信息。

## 下周计划

下周计划必须由用户提供，不可自行推断。缺失时先展示已识别的本周内容，再询问用户。
