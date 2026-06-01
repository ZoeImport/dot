---
name: review-and-pr
description: 整合代码审查与 Git 提交工作流 - 先执行 ReviewCode 审查，通过后执行 git-commit-push-pr 流程。当用户说"审查提交创建pr"、"review然后pr"、或需要完整的代码质量检查+提交流程时使用。
---

# Review And PR — 代码审查 + 提交工作流

整合 **ReviewCode** 和 **git-commit-push-pr** 两个 skill 的完整工作流：先审查代码规范，确保编译校验通过后，再执行提交、推送、创建 MR/PR。

---

## 使用场景

- 用户说"审查提交创建pr"
- 用户说"review然后pr"
- 用户说"检查代码然后提交"
- 用户需要完整的代码质量检查 + Git 工作流自动化
- 用户说"切分支提pr"

---

## 工作流程

### 第一步：分支安全检查（G-14）

1. **检查当前分支**
   ```bash
   git branch --show-current
   git branch -vv
   ```

2. **禁止直推的分支列表**
   - `main` / `master`（主干分支）
   - `feature/*`（如 `feature/2.6`、`feature-2.0` 等）
   - `release/*`（如 `release-2.4`、`dot-release-2.5` 等）
   - `dot-release-*`（版本发布分支）
   - 所有带 `release` 或 `feature` 关键词的长期维护分支

3. **分支安全规则**
   - 如果当前在禁止直推的分支：
     - **必须切出新的开发分支**
     - 分支命名：`fix/<issue-desc>` 或 `feat/<feature-desc>`
     - 询问用户目标分支（通常是 `feature/x.x` 或 `main`）
   - 如果已在开发分支：
     - 检查是否从正确的基线分支切出（`git merge-base`）
     - 检查远程是否已有 MR/PR（避免重复创建）

4. **拒绝直推请求**
   - 用户要求向禁止分支直推时，必须拒绝并提醒风险
   - 建议切出开发分支后通过 MR/PR 合入

### 第二步：加载 ReviewCode Skill 进行代码审查

使用 `skill` 工具加载 `reviewcode`：

```
skill(name="reviewcode")
```

审查要点（G-20 编译校验规则）：
- 确认改动文件是否涉及多个 APP
- 检查是否需要执行 `make local APP=<APP>` 和 `make generate-docs APP=<APP>`

### 第三步：执行编译校验

根据 ReviewCode G-20 规则：

1. **编译验证**（按涉及的 APP 分别执行）
   ```bash
   make local APP=dotteacher
   make local APP=dottask
   make local APP=dotworker
   # ...
   ```

2. **文档生成**（如果修改了 DTO 或 handler 注解）
   ```bash
   make generate-docs APP=dotteacher
   make generate-docs APP=dottask
   # ...
   ```

3. **编译失败处理**
   - 不允许靠乱换目录或改命令规避
   - 向用户说明编译失败原因
   - 修复后重新执行编译

### 第四步：检查 vendor 目录和本地开发修改

```bash
git status
```

**必须排除的修改：**

1. **`vendor/` 目录**（G-14）
   - 只提交业务相关文件
   - 如有 vendor 变更，向用户确认是否需要提交（通常不需要）

2. **本地开发调试修改**
   - 场景：开发者在本地调试时修改的配置、URL、调试开关等
   - 特征：
     - 硬编码的本地 IP/端口（如 `http://172.16.0.xx:xxxx`）
     - 被注释掉的调试代码（如 `// playwright.Install()`）
     - 本地环境特定的路径或配置
   - 处理：不提交，保留在工作区供后续本地调试
   - 常见文件：
     - `browser.go`、`playwright` 相关配置
     - 本地 URL/endpoint 硬编码
     - 被临时启用的调试日志/断点

### 第五步：询问用户确认需求

使用 `question` 工具询问：

```
问题1：提交信息（commit message）- 根据改动内容给出建议
问题2：PR 标题和描述 - 建议自动生成（包含编译验证结果）
问题3：需要 @ 的审阅者（GitLab/GitHub 用户名）
问题4：目标分支（默认当前分支的 upstream 或 feature/x.x）
```

### 第六步：执行提交

```bash
# 只添加业务文件，排除 vendor
git add <业务文件路径...>

# 如果编译校验生成了新文件（如 docs），一并添加
git add apps/<APP>/internal/docs/*_docs.go

# 提交
git commit -m "<commit message>"
```

如果是在新分支上第一次提交，可能需要 amend 重做提交以包含生成的文件。

### 第七步：推送到远程

```bash
# 新分支使用 -u
git push -u origin <branch-name>

# 已有上游分支
git push
```

### 第八步：创建 Merge Request

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

## Test
编译验证：
- `make local APP=xxx` ✅
- `make generate-docs APP=xxx` ✅
EOF
)" \
  --assignee <username> \
  --reviewer <username> \
  --target-branch <目标分支> \
  --remove-source-branch
```

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
编译验证：
- `make local` ✅
- `make generate-docs` ✅
EOF
)" \
  --assignee <username> \
  --reviewer <username>
```

### 第九步：返回结果

- MR/PR 链接
- 提交 hash
- 分支名
- 编译验证结果摘要

---

## 完整调用链

```
skill(review-and-pr)
  → skill(reviewcode)  # 加载审查规则
  → make local APP=<APP>  # 编译验证
  → make generate-docs APP=<APP>  # 文档生成
  → git add / git commit  # 提交
  → git push  # 推送
  → glab mr create / gh pr create  # 创建 MR/PR
```

---

## 注意事项

1. **分支安全是第一步** - 严禁在主分支上直接提交或推送
2. **编译校验必须通过** - 使用 `make local` 和 `make generate-docs`，禁止用 `go build ./...`
3. **vendor 目录排除** - 提交前必须检查并排除
4. **本地开发修改排除** - 硬编码 IP/端口、调试开关等不提交
5. **文档生成文件一并提交** - `*_docs.go` 等生成物必须包含在提交中
6. **PR 描述包含验证结果** - 明确列出编译验证通过的 APP
7. **遵循项目 commit 风格** - 查看 git log 了解格式

---

## 错误处理

| 错误 | 处理 |
|------|------|
| 当前在主分支 | 强制切出开发分支，询问目标分支 |
| 编译失败 | 向用户说明原因，修复后重试 |
| vendor 有变更 | 提示用户，通常排除 |
| 本地开发修改 | 识别硬编码 IP/调试代码，不提交 |
| 推送失败 | 检查网络、权限、分支冲突 |
| MR 已存在 | 提示用户 MR 已存在，给出链接 |
| CLI 未安装 | 提示安装 `gh` 或 `glab` |

---

## 示例交互

```
用户: 切分支提pr到feature/2.6

Agent:
1. 检查当前分支 → 在 feature/2.6（需要切出新分支）
2. 切出新分支 fix/dao-soft-delete-filter
3. 加载 ReviewCode skill 审查代码
4. 执行编译校验：
   - make local APP=dotteacher ✅
   - make local APP=dottask ✅
   - make generate-docs APP=dotteacher ✅
5. 检查 vendor → 无变更
6. 询问用户：commit message、PR 描述、@ 谁
7. git add + git commit
8. git push -u origin fix/dao-soft-delete-filter
9. glab mr create --target-branch feature/2.6
10. 返回 MR 链接
```

---

## 与单独 skill 的区别

| Skill | 范围 |
|-------|------|
| `reviewcode` | 只审查代码规范，不执行 Git 操作 |
| `git-commit-push-pr` | 只执行 Git 提交流程，不审查代码 |
| `review-and-pr` | **整合两者**：先审查 → 编译校验 → 提交 → PR |