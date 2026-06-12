---
name: fix-branch-pr
description: 自动检测目标分支、创建 fix 分支、完成改动后提交推送并创建 PR。
---

# Skill: fix-branch-pr

# 修复缺陷分支工作流

自动检测目标分支、创建 fix 分支、完成改动后提交推送并创建 PR。

## 使用场景

- 用户说"创建 fix 分支并提 PR"
- 用户说"切出修复分支"
- 用户说"在某个分支上修复问题然后提 PR"
- 用户指定目标分支（如 `dot-release-2.5`）和改动内容

## 前置要求

1. **git worktree** 已安装
2. **glab CLI** 已安装并配置认证
3. 目标仓库支持 worktree 操作

## 参数说明

| 参数 | 说明 | 示例 |
|------|------|------|
| target_branch | 目标主分支 | `dot-release-2.5`, `main`, `feature-2.5` |
| fix_name | 修复描述（用于分支命名） | `get_book_knowledge_semester_id`, `sql_zzh` |
| reviewer | PR 审阅者 GitLab 用户名 | `morehao`, `songhao` |
| changes | 改动内容描述 | "移除 semester_id 必填校验" |

## 工作流程

### 第一步：解析用户意图

从用户请求中提取：
- **target_branch**: 目标主分支名
- **fix_name**: 修复分支名称后缀（建议格式：`fix/<fix_name>`）
- **reviewer**: 审阅者（可选）
- **changes**: 改动描述（用于 commit 和 PR）

### 第二步：检测/创建目标分支

**检查目标分支是否存在于远程：**
```bash
git fetch origin
git branch -r | grep "origin/<target_branch>"
```

**分支不存在则创建：**
```bash
# 从当前分支或指定基础分支创建
git push origin <base_branch>:<target_branch>
```

**分支已存在则直接使用。**

### 第三步：创建 Worktree

**检查是否已有该 worktree：**
```bash
git worktree list
```

**创建新 worktree（目录名建议：<repo>-<branch>）：**
```bash
# worktree 目录位于仓库同级的相邻目录
git worktree add ../<repo>-<branch_suffix> <target_branch>
```

示例：
```bash
# 仓库目录: /home/zoe/CodeSpace/gitlab/dotpen-api
# worktree: /home/zoe/CodeSpace/gitlab/dotpen-api-2.5
git worktree add ../dotpen-api-2.5 dot-release-2.5
```

### 第四步：在 Worktree 中创建 Fix 分支

在 worktree 目录中执行：
```bash
# 进入 worktree
cd ../<worktree_dir>

# 创建 fix 分支
git checkout -b fix/<fix_name>
```

分支命名约定：`fix/<fix_name>`，如 `fix/get_book_knowledge_semester_id`

### 第五步：完成改动

根据用户需求完成代码改动：
- 编辑文件
- 编译验证（如 `make local APP=<app>`）
- 确保无 lint/编译错误

### 第六步：提交推送

**确认改动范围（排除 vendor/）：**
```bash
git status
git diff
```

**提交改动：**
```bash
git add <业务文件>
git commit -m "fix(<scope>): <改动描述>"
```

**推送分支：**
```bash
git push -u origin fix/<fix_name>
```

### 第七步：创建 PR

使用 glab 创建 MR：
```bash
glab mr create \
  --title "fix(<scope>): <改动描述>" \
  --description "$(cat <<'EOF'
## Summary
<改动摘要>

## Changes
- <改动点1>
- <改动点2>

## Test
<测试说明，如编译验证>
EOF
)" \
  --target-branch <target_branch> \
  --reviewer <reviewer_username>
```

### 第八步：返回结果

- PR URL
- Fix 分支名
- Worktree 目录路径

## 完整示例

```
用户: 通过 worktree 去往 dot-release-2.5 切出 fix 分支提 PR，改动是去掉 GetBookKnowledge 的 semester_id 参数必填校验，@ morehao review

Agent:
1. 检测目标分支:
   git fetch origin
   git branch -r | grep dot-release-2.5  # 已存在

2. 创建 worktree:
   git worktree add ../dotpen-api-2.5 dot-release-2.5

3. 在 worktree 创建 fix 分支:
   cd ../dotpen-api-2.5
   git checkout -b fix/get_book_knowledge_semester_id

4. 完成改动:
   编辑 apps/dotteacher/internal/dto/dtoknowledgeclass/student.go
   移除 Validity 中 SemesterID 校验
   make local APP=dotteacher  # 编译验证

5. 提交推送:
   git add apps/dotteacher/internal/dto/dtoknowledgeclass/student.go
   git commit -m "fix(GetBookKnowledge): 移除 semester_id 必填校验"
   git push -u origin fix/get_book_knowledge_semester_id

6. 创建 PR:
   glab mr create --title "fix(GetBookKnowledge): 移除 semester_id 必填校验" \
     --description "..." --target-branch dot-release-2.5 --reviewer morehao

7. 返回:
   - PR: https://git.yygu.cn/dotpen/dotpen-api/-/merge_requests/674
   - Fix 分支: fix/get_book_knowledge_semester_id
   - Worktree: ../dotpen-api-2.5
```

## 分支不存在时的处理

```
用户: 在 new-feature 分支上创建 fix 分支

Agent:
1. 检测目标分支不存在:
   git fetch origin
   git branch -r | grep new-feature  # 无结果

2. 创建目标分支:
   git push origin main:new-feature

3. 创建 worktree:
   git worktree add ../dotpen-api-new-feature new-feature

4. 后续步骤同上...
```

## 注意事项

1. **分支命名规范**：
   - Fix 分支：`fix/<fix_name>`
   - Feature 分支：`feature/<feature_name>`

2. **Worktree 管理**：
   - Worktree 目录建议放在仓库同级目录
   - 目录命名：`<repo>-<branch_suffix>`
   -完成后可选择保留或删除 worktree

3. **提交规范**：
   - 格式：`fix(<scope>): <description>` 或 `feat(<scope>): <description>`
   - 不要提交 vendor/ 目录

4. **编译验证**：
   - Go 项目：`make local APP=<app>`
   - 确保改动可编译

5. **Git 操作确认规则**（见 AGENTS.md）：
   - push/pull/stash/commit 需询问用户确认
   - 用户预说「确定」「确认」等则无需再问

## 错误处理

- **目标分支不存在**：从基础分支创建后继续
- **Worktree 已存在**：复用现有 worktree
- **编译失败**：修复错误后重新编译
- **PR 创建失败**：检查 reviewer 用户名、分支名
- **远程分支冲突**：提示用户处理冲突

## Worktree 清理（可选）

完成 PR 后可选择清理 worktree：
```bash
git worktree remove ../<worktree_dir>
```