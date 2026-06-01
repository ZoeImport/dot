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

| 变更路径 | 影响服务 |
|----------|----------|
| `apps/account/...` | `account` |
| `apps/dotteacher/...` | `dotteacher` |
| `apps/dotstudent/...` | `dotstudent` |
| `apps/dotworker/...` | `dotworker` |
| `apps/dottask/...` | `dottask` |
| `apps/dotinit/...` | `dotinit` |
| `apps/dotpen/...` | `dotpen` |
| `apps/dryang/...` | `dryang` |
| `apps/aigc/...` 等 | `aiagents` / `chat` |
| `pkgs/...` 或 `.gitlab-ci.yml` | **所有服务** |

#### B2. 服务依赖分析

部分子服务被聚合到更大服务中，部署聚合服务即可包含子服务变更：

| 子服务 | 被聚合到 | 说明 |
|--------|----------|------|
| `account` | `dotpen` | account 路由注册到 dotpen |
| `dotteacher` | `dotpen` | dotteacher 路由注册到 dotpen |
| `dotstudent` | `dotpen` | dotstudent 路由注册到 dotpen |
| `dotmigration` | `dotpen` | 迁移逻辑 |
| `dotinit` | （独立） | 独立部署 |
| `dotworker` | （独立） | 独立部署 |
| `dottask` | （独立） | 独立部署 |

**简化规则：** 如果受影响的服务列表中同时包含 `account` / `dotteacher` / `dotstudent` 和 `dotpen`，只需保留 `dotpen`。

#### B3. 呈现给用户

展示推断结果及简化建议，**如果不确定，问用户**：

```
根据 MR diff 分析，受影响的原始服务：
  - account (apps/account/)
  - dotteacher (apps/dotteacher/)
  - dottask (apps/dottask/)

依赖简化建议：
  - account + dotteacher → 被 dotpen 聚合
  - dottask → 独立部署

最终建议部署：dotpen, dottask
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

目标分支使用 MR 的 `target_branch`（如 `feature/2.10`），并行触发：

```bash
glab deploy-service <environment> <app> <target-branch>
glab deploy-service <environment> <app2> <target-branch>
```

### 步骤 E：返回结果

按以下格式返回，包含创建命令、环境、服务、Pipeline 列表：

```
部署完成 🚀

环境: test
分支: feature/2.10

执行命令:
  glab deploy-service test dotpen feature/2.10
  glab deploy-service test dottask feature/2.10

服务列表:
  - dotpen (聚合 account + dotteacher)
  - dottask

Pipelines:
  - dotpen: Pipeline #6501 - https://git.yygu.cn/dotpen/dotpen-api/-/pipelines/6501
  - dottask: Pipeline #6502 - https://git.yygu.cn/dotpen/dotpen-api/-/pipelines/6502
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
1. 检查改动：apps/dotteacher/ 3 files, apps/account/ 1 file
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
2. glab mr diff 796 → 变更文件 → 原始服务: account, dotteacher, dottask
3. 依赖分析: account+dotteacher → dotpen 聚合, dottask 独立
4. 建议部署: dotpen, dottask → 用户确认
5. 执行:
   glab deploy-service test dotpen feature/2.10
   glab deploy-service test dottask feature/2.10
6. 返回:

部署完成 🚀

环境: test
分支: feature/2.10

执行命令:
  glab deploy-service test dotpen feature/2.10
  glab deploy-service test dottask feature/2.10

服务列表:
  - dotpen (聚合 account + dotteacher)
  - dottask

Pipelines:
  - dotpen: Pipeline #6501 - https://git.yygu.cn/.../pipelines/6501
  - dottask: Pipeline #6502 - https://git.yygu.cn/.../pipelines/6502
```

## 错误处理

- **无改动**：提示用户没有需要提交的改动
- **推送失败**：检查网络、权限、分支冲突
- **PR已存在**：提示用户 PR 已存在，给出链接
- **CLI未安装**：提示安装 `gh` 或 `glab`