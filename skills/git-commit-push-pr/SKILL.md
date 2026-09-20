---
name: git-commit-push-pr
description: Automate git workflow - commit changes, push to remote, create merge request with assignee, and deploy affected services after MR merged. Use when user wants to commit, push, create PR, or mentions "提交推送创建pr" or "部署MR" workflow.
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

### 第六步：提示合并后部署方式

创建 MR 后，告知用户如何部署：

```
MR #xxx 已创建: <MR链接>
目标分支: <target-branch>

合并后如需部署，告诉我"部署 MR #xxx"，我会：
1. 确认 MR 已合并
2. 分析 MR 的 diff → 自动推断受影响的服务
3. 让你选择环境（test/image）和要部署的服务
4. 触发 pipeline
```

### 第七步：返回最终结果

- PR/MR 链接
- 提交 hash
- 分支名

---

## MR 合并后部署流程

当用户合并 MR 后说"部署 MR #xxx"，执行以下步骤：

### 步骤 A：确认 MR 状态

```bash
glab mr view <id>  # 确认 merged 状态
```

如果未合并，提示"MR #xxx 尚未合并，请先合并后再部署"。

### 步骤 B：分析 MR diff → 推断受影响服务

```bash
glab mr diff <id>  # 获取 MR 的变更文件列表
```

#### B1. 文件 → 服务映射

从 `glab mr diff <id>` 获取变更文件列表，结合目标仓库的目录结构和 `.gitlab-ci.yml` 推断受影响的服务。不同仓库的目录结构不同，不硬编码映射表。**不确定时询问用户。**

#### B2. 服务依赖分析

如果目标仓库有服务聚合关系（某些子服务路由被另一个聚合服务统一挂载），从仓库文档或 `.gitlab-ci.yml` 了解后再判断，不在此预设。

#### B3. 呈现给用户

展示推断结果，**如果不确定，问用户**：

```
根据 MR diff 分析，受影响的文件路径：
  - <path1>
  - <path2>

推断受影响的服务：<svc1>, <svc2>（不确定的已标注）
是否按此执行？或手动调整？
```

### 步骤 C：询问部署参数

```
检测到以下服务受影响：<svc1>, <svc2>, ...
部署环境？test / image
需要部署哪些服务？（默认全选）
确认？
```

### 步骤 D：执行部署

先按目标仓库自己的 CI 定义确认触发方式与参数名（GitLab 读 `.gitlab-ci.yml` 的 `spec.inputs`，GitHub 读 `.github/workflows/*`），**环境名与服务名一律实时读取，不要沿用其他仓库的取值**。目标分支使用 MR 的 `target_branch`（如 `feature/2.10`），并行触发：

```bash
# GitLab
unset GITLAB_TOKEN GITLAB_ACCESS_TOKEN OAUTH_TOKEN
glab ci run --input environment=<env> --input app=<app> --branch <target-branch>

# GitHub
gh workflow run <workflow-file> --ref <target-branch> -f app=<app> -f environment=<env>
```

若目标仓库没有可触发的部署工作流，停下并告诉用户该仓库不支持从 CI 部署，不要猜测命令。

### 步骤 E：返回结果

按以下格式返回，包含创建命令、环境、服务、Pipeline 列表：

```
部署完成 🚀

环境: <environment>
分支: <target-branch>

执行命令:
  <实际执行的触发命令 1>
  <实际执行的触发命令 2>

服务列表:
  - <svc1>
  - <svc2>

Pipelines / Runs:
  - <svc1>: #<id> - <url>
  - <svc2>: #<id> - <url>
```

## 注意事项

1. **不要提交 vendor/** - 除非用户明确要求
2. **遵循项目的 commit 风格** - 查看 git log 了解格式
3. **确认目标分支** - 有些项目用 main，有些用 master
4. **检查远程仓库类型** - GitHub 用 `gh`，GitLab 用 `glab`
5. **如果远程已有 MR/PR** - 只推送更新，不重复创建
6. **严禁直接推送主分支** - 禁止向 `main` / `master` 等主分支直接推送代码。所有代码变更必须通过开发分支 → MR/PR → 合入主分支的流程。如果当前分支是主分支，必须先切出开发分支再推送；如果用户要求直推主分支，必须拒绝并提醒风险

## 示例交互

### 场景一：提交并创建 MR

```
用户: 提交当前改动并创建pr到feature/2.10，reviewer @morehao

Agent:
1. 检查改动：<dir-a>/ 3 files, <dir-b>/ 1 file
2. 询问：
   - commit message → 自动生成
   - PR 标题和描述 → 自动生成
   - reviewer → @morehao
   - 目标分支 → feature/2.10
3. git add -> git commit -> git push
4. glab mr create -> PR #796
5. 提示：
   "MR #796 已创建。合并后如需部署，告诉我就行。"
6. 返回结果
```

### 场景二：合并后部署 MR

```
用户: 部署 MR #796 到 test

Agent:
1. glab mr view 796 → 已合并 ✅
2. glab mr diff 796 → 变更文件列表
3. 结合仓库结构推断受影响服务，不确定时询问用户
4. 建议部署: <svc1>, <svc2> → 用户确认
5. 执行（命令形式取自目标仓库自己的 CI 定义）:
   glab ci run --input environment=test --input app=<svc1> --branch feature/2.10
   glab ci run --input environment=test --input app=<svc2> --branch feature/2.10
6. 返回:

部署完成 🚀

环境: test
分支: feature/2.10

执行命令:
  <实际执行的触发命令 1>
  <实际执行的触发命令 2>

Runs:
  - <svc1>: #<id> - <url>
  - <svc2>: #<id> - <url>
```

## 错误处理

- **无改动**：提示用户没有需要提交的改动
- **推送失败**：检查网络、权限、分支冲突
- **PR已存在**：提示用户 PR 已存在，给出链接
- **CLI未安装**：提示安装 `gh` 或 `glab`