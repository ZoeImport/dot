---
name: worktree-check
description: 迭代切换专用工作流——将当前开发分支迁出到独立 worktree，主 worktree 切换到新迭代分支。当用户说"切迭代"、"切版本"、"新建 worktree 切换迭代"、"迁移 worktree"、"迭代结束迁移"时使用。
user-invocable: true
---

# Skill: worktree-check

迭代切换专用工作流：把当前开发分支迁出到独立 worktree，主 worktree 切换到新迭代分支。

## 使用场景

- 用户说"切迭代"、"切版本"、"切到新迭代"
- 用户说"新建 worktree 切换迭代"
- 用户说"迭代结束了，迁移 worktree"
- 当前迭代开发完成，需要切换到新迭代分支

## 核心原则

1. **先释放再迁移**：主 worktree 先切到 `main` 释放当前分支，再为它创建独立 worktree
2. **不自动创建分支**：新迭代分支不存在时，停留在 `main`，告知用户手动处理
3. **改动自动暂存**：未提交改动自动 stash，在新建 worktree 中 pop 恢复

## 参数说明

| 参数 | 说明 | 来源 |
|------|------|------|
| current_branch | 当前开发分支（如 `dev/zzh_2.11`） | `git rev-parse --abbrev-ref HEAD` |
| version | 从当前分支提取的版本号（如 `2.11`） | 从分支名解析 |
| target_branch | 用户指定的新迭代分支（如 `feature/2.12`） | 用户输入 |
| release_branch | 当前版本对应的 release 分支（如 `dot-release-2.11`） | 由 version 推算 |

版本号提取规则：从分支名中匹配 `\d+\.\d+` 模式的版本号。若无法提取出唯一版本号则询问用户指定。

## 工作流程

### 第一步：提取当前分支信息

```bash
git rev-parse --abbrev-ref HEAD        # 当前分支名
git worktree list                        # 列出已有 worktree
git status --short                       # 检查是否有未提交改动
```

从当前分支名提取版本号（如 `dev/zzh_2.11` → `2.11`，`feature/2.6` → `2.6`）。

### 第二步：处理未提交改动

如果有未提交改动，自动 stash：

```bash
git stash push -m "worktree-check: auto stash before migration"
```

### 第三步：询问用户新迭代分支

使用 `question` 工具询问用户：

**Q1:** 新迭代分支名是？
- 输入分支名（如 `feature/2.12`）
- 或选择"暂不确定，先留在 main"

**Q2:** 如果目标分支不存在，告知用户"分支 `${target_branch}` 不存在，当前将停留在 main，请后续手动创建并切换"

### 第四步：主 worktree 切到 main 释放当前分支

```bash
git checkout main
```

### 第五步：创建新 worktree

```bash
git worktree add ../dotpen-api-${version} ${current_branch}
```

### 第六步：在 worktree 恢复 stash 的改动

```bash
# 在新建的 worktree 目录中执行
cd ../dotpen-api-${version}
git stash pop
```

### 第七步：切换主 worktree 到目标分支

```bash
# 在主 worktree 中执行
git checkout ${target_branch}
```

如果目标分支不存在，不创建分支，停留在 `main`。

### 第八步：验证结果

```bash
# 主 worktree
git log --oneline -3
git status

# 新 worktree（在新建的 worktree 目录中执行）
git log --oneline -3
git status
```

## 完整示例

```
当前分支: dev/zzh_2.11
用户: 切迭代，新分支 feature/2.12

Agent:
1. git status → 有未提交改动
2. git stash push -m "worktree-check: auto stash before migration"
3. 用户确认目标: feature/2.12
4. git checkout main
5. git worktree add ../dotpen-api-2.11 dev/zzh_2.11
6. cd ../dotpen-api-2.11 && git stash pop
7. cd 主目录 && git checkout feature/2.12  # 分支已存在
8. 验证主 worktree 和 worktree 状态

结果:
- worktree: /home/zoe/CodeSpace/gitlab/dotpen-api-2.11 @ dev/zzh_2.11
- 主 worktree: /home/zoe/CodeSpace/gitlab/dotpen-api @ feature/2.12
```

```
当前分支: dev/zzh_2.11
用户: 切迭代，还不太清楚新分支名

Agent:
1. git status → 干净
2. 用户选择: "暂不确定"
3. git checkout main
4. git worktree add ../dotpen-api-2.11 dev/zzh_2.11
5. cd 主目录（无 stash 可 pop）
6. 告知: 新分支未指定，当前在 main，请后续手动切换

结果:
- worktree: /home/zoe/CodeSpace/gitlab/dotpen-api-2.11 @ dev/zzh_2.11
- 主 worktree: /home/zoe/CodeSpace/gitlab/dotpen-api @ main
```

## 注意事项

1. **worktree 目录命名**：`../dotpen-api-${version}`，与项目现有 worktree 风格一致
2. **不存在的新分支**：不自动创建，告知用户后停留在 main
3. **当前分支释放**：必须先 checkout main 释放当前分支，否则 git 不允许被 checkout 中的分支被其他 worktree 占用
4. **stash 恢复位置**：在新建的 worktree 中 pop，而非主 worktree
5. **Git 操作确认规则**：按项目 AGENTS.md，push/commit 操作需用户确认；checkout/stash 属本地操作可直接执行。但建议在执行前用 question 做一次整体确认

## 错误处理

| 场景 | 处理方式 |
|------|---------|
| 有未提交改动 | 自动 stash，在新建 worktree 中 pop 恢复 |
| worktree 目录已存在 | 提示用户目录已存在，询问是否复用或使用其他后缀 |
| 分支名不包含版本号 | 询问用户手动指定版本号 |
| 目标分支不存在 | 告知用户后停留在 main |
| stash pop 冲突 | 提示用户在 worktree 中手动解决冲突 |
| main 有未提交改动 | 提示用户先处理 main 的改动，暂不切换 |
