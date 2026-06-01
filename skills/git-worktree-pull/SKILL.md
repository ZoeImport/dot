# Skill: git-worktree-pull

在指定 git worktree 中拉取新代码。支持选择已有 worktree 或新建 worktree，然后拉取指定分支的最新代码。

## 使用场景

- 用户说"在 worktree 拉代码"
- 用户说"拉取新代码到另一个目录"
- 用户说"worktree pull"
- 用户需要在某个 worktree 目录中 fetch/pull 最新代码

## 工作流程

### 第一步：列出已有 worktrees

```bash
git worktree list
```

展示所有已有 worktree 的路径、commit hash、分支名。

### 第二步：确认操作方式

使用 `question` 工具询问用户：

```
问题1：使用已有 worktree 还是新建？
  - 使用已有 worktree（选择路径）
  - 新建 worktree（输入路径和分支名）

问题2：拉取哪个分支？
  - 输入远程分支名（如 dot-release-2.5、fix/some-branch）

问题3：确认拉取操作？
  - git pull（直接拉取当前分支最新代码）
```

**如果选择已有 worktree**：
- 从 `git worktree list` 输出中选择一个路径
- 在该路径下执行 `git pull`

**如果新建 worktree**：
- 询问新 worktree 的目标路径（默认在仓库同级目录，如 `/home/zoe/CodeSpace/gitlab/dotpen-api-<suffix>`）
- 执行 `git worktree add <path> <branch>` 或 `git worktree add <path> -b <new-branch> <start-point>`
- 然后在新路径下执行 `git pull`

### 第三步：执行拉取

```bash
# 在目标 worktree 目录中执行
git pull
```

使用 Bash 工具的 `workdir` 参数指定 worktree 目录路径，而非 `cd`。

### 第四步：验证结果

```bash
# 在目标 worktree 目录中执行
git log --oneline -3
git status
```

返回最新 commit 信息和工作区状态。

## 注意事项

1. **不要在主 worktree 中 checkout 其他分支** — 主 worktree 可能正在开发，使用 separate worktree 来避免冲突
2. **worktree 路径** — 新建 worktree 时，路径建议在仓库同级目录下，加上有意义的 suffix（如分支名）
3. **已有 worktree 的分支** — 每个 worktree 只能关联一个分支，不能在同一个 worktree 中 checkout 已被其他 worktree 占用的分支
4. **pull 前先确认** — 按照项目 AGENTS.md 的 Git 操作确认规则，pull 前需要用户确认（除非用户已说了"确定"等授权词）
5. **路径一致性** — worktree 内的 `.git` 指向主仓库，确保路径正确

## 错误处理

- **worktree 已被占用**：提示用户该分支已有 worktree，给出路径
- **分支不存在**：先 `git fetch origin` 再尝试 checkout
- **pull 冲突**：提示用户有冲突，需要手动解决
- **路径不存在**：新建 worktree 时用 `git worktree add` 创建

## 示例交互

```
用户: 在worktree拉取2.5的代码

Agent:
1. 执行 git worktree list，发现已有 /home/zoe/CodeSpace/gitlab/dotpen-api-2.5
2. 询问用户：使用已有 worktree 还是新建？
3. 用户选择已有
4. 在 /home/zoe/CodeSpace/gitlab/dotpen-api-2.5 下执行 git pull
5. 验证 git log --oneline -3
6. 返回最新 commit 信息
```

```
用户: 新建一个worktree拉fix/xxx分支

Agent:
1. 执行 git worktree list
2. 询问用户：新 worktree 路径（建议 /home/zoe/CodeSpace/gitlab/dotpen-api-fix-xxx）
3. 执行 git worktree add /home/zoe/CodeSpace/gitlab/dotpen-api-fix-xxx fix/xxx
4. 在新路径下执行 git pull
5. 返回 worktree 信息和最新 commit
```