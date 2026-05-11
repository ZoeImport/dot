---
name: git-commit-push-pr
description: Automate git workflow - commit changes, push to remote, and create merge request with assignee. Use when user wants to commit, push, create PR, or mentions "提交推送创建pr" workflow.
---

# Git 提交、推送、创建 PR 工作流

自动化 git 工作流：提交改动 → 推送到远程 → 创建合并请求（MR/PR）并指定审阅者。

## 使用场景

- 用户说"提交推送创建pr"
- 用户说"commit push and create PR"
- 用户说"创建MR并@某人"
- 用户需要完整的 git 工作流自动化

## 工作流程

### 第一步：收集信息

1. **检查当前状态**
   ```bash
   git status          # 查看未暂存/未提交的改动
   git diff            # 查看具体改动内容
   git log --oneline -5  # 查看最近提交风格
   ```

2. **确认分支信息**
   ```bash
   git branch --show-current           # 当前分支名
   git log main..HEAD --oneline     # 相对于主分支的提交
   ```

3. **确认改动范围**
   - 排除 `vendor/` 目录（除非用户明确要求）
   - 只提交业务相关文件

### 第二步：确认需求

使用 `question` 工具询问用户：

```
问题1：提交信息（commit message）
问题2：PR 标题和描述
问题3：需要 @ 的审阅者（GitLab 用户名，如 @username）
问题4：目标分支（默认 main 或当前分支的 upstream）
```

### 第三步：执行提交

```bash
# 只添加业务文件，排除 vendor
git add <业务文件路径...>

# 提交
git commit -m "<commit message>"
```

### 第四步：推送到远程

```bash
# 如果是新分支，使用 -u 参数
git push -u origin <branch-name>

# 如果已有上游分支
git push
```

### 第五步：创建 Merge Request

使用 `gh` 或 `glab` CLI：

**GitHub (gh):**
```bash
gh pr create \
  --title "<PR标题>" \
  --body "$(cat <<'EOF'
## Summary
<PR描述>

## Changes
- <改动点1>
- <改动点2>

## Test
<测试说明>
EOF
)" \
  --assignee <username> \
  --reviewer <username>
```

**GitLab (glab):**
```bash
glab mr create \
  --title "<PR标题>" \
  --description "$(cat <<'EOF'
## Summary
<PR描述>

## Changes
- <改动点1>
- <改动点2>
EOF
)" \
  --assignee <username> \
  --reviewer <username> \
  --target-branch <目标分支>
```

### 第六步：返回结果

- PR/MR 链接
- 提交 hash
- 分支名

## 注意事项

1. **不要提交 vendor/** - 除非用户明确要求
2. **遵循项目的 commit 风格** - 查看 git log 了解格式
3. **确认目标分支** - 有些项目用 main，有些用 master
4. **检查远程仓库类型** - GitHub 用 `gh`，GitLab 用 `glab`
5. **如果远程已有 MR/PR** - 只推送更新，不重复创建
6. **严禁直接推送主分支** - 禁止向 `main` / `master` 等主分支直接推送代码。所有代码变更必须通过开发分支 → MR/PR → 合入主分支的流程。如果当前分支是主分支，必须先切出开发分支再推送；如果用户要求直推主分支，必须拒绝并提醒风险

## 示例交互

```
用户: 创建一个skill提交推送创建pr并 @某个人

Agent: 
1. 检查当前改动...
2. 询问用户：
   - commit message 是什么？
   - PR 标题和描述？
   - @ 谁？（GitLab/GitHub 用户名）
   - 目标分支？
3. 执行 git add <文件>
4. 执行 git commit -m "<message>"
5. 执行 git push
6. 执行 glab/gh mr create
7. 返回 PR 链接
```

## 错误处理

- **无改动**：提示用户没有需要提交的改动
- **推送失败**：检查网络、权限、分支冲突
- **PR已存在**：提示用户 PR 已存在，给出链接
- **CLI未安装**：提示安装 `gh` 或 `glab`