---
name: deploy-service
description: Trigger a repository's own deployment CI for any service. Use when user wants to deploy services to an environment. Supports GitHub Actions and GitLab CI; environments, services and input names are read live from the target repository's CI definition instead of being hardcoded.
---

# 部署服务触发工作流

触发**目标仓库自己的**部署 CI。环境、服务名与输入参数一律从该仓库的 CI 定义实时读取，
不硬编码任何仓库的服务清单。

## 使用场景

- 用户说"触发部署"、"部署服务"、"deploy"
- 用户指定环境 + 服务名 + 分支/tag

## 第一步：识别目标仓库与其 CI 系统

```bash
git -C <repo> remote -v          # 判定 GitHub 还是 GitLab
ls <repo>/.github/workflows/     # GitHub Actions
ls <repo>/.gitlab-ci.yml         # GitLab CI
```

- 有 `.github/workflows/` → 走 **GitHub Actions**（`gh`）
- 有 `.gitlab-ci.yml` → 走 **GitLab CI**（`glab`）
- 两者都有 → 以实际承载部署的那个为准；判断不了就问用户
- 都没有 → 停下并说明该仓库没有可触发的部署 CI，**不要猜测命令或换别的仓库的命令**

认证：`gh auth status` / `glab auth status`。GitLab 侧本机可能残留过期的
`GITLAB_TOKEN` 环境变量（来自历史 export），glab 会优先读它并返回 `401 invalid_token`，
所以每次调用前先 `unset GITLAB_TOKEN GITLAB_ACCESS_TOKEN OAUTH_TOKEN`。

## 第二步：从 CI 定义读取可用选项

**每次执行前实时读取，不要沿用其他仓库的取值。**

GitHub Actions —— 找带 `workflow_dispatch` 的工作流及其 `inputs`：

```bash
gh workflow list --repo <owner/repo>
gh workflow view <workflow-file> --repo <owner/repo>   # 看 inputs 名称与可选值
```

GitLab CI —— 读 `spec.inputs`：

```bash
grep -A 10 "environment:" .gitlab-ci.yml | grep -A 10 "options:"
grep -A 30 "app:" .gitlab-ci.yml | grep -A 30 "options:"
```

## 第三步：解析用户意图并确认

**每次触发前必须确认参数，得到用户明确同意后才执行。**

```
确认部署以下服务？
- 仓库: <owner/repo>
- CI: GitHub Actions / GitLab CI
- 环境: <environment>
- 服务: <app1>, <app2> ...
- 分支/tag: <ref>
```

`prod` 或任何生产环境要单独二次确认。

## 第四步：触发

GitHub Actions：

```bash
gh workflow run <workflow-file> --repo <owner/repo> --ref <ref> -f <input>=<value> ...
```

注意 `--ref` 选择的是**工作流定义所在的分支**，与要部署的源码 ref 是两回事 ——
源码 ref 通常由 workflow 自己的 input 传入（例如 `-f ref=<40 位完整 SHA>`）。不要混用。

GitLab CI：

```bash
unset GITLAB_TOKEN GITLAB_ACCESS_TOKEN OAUTH_TOKEN
glab ci run --input <name>=<value> --branch <ref>
```

多个服务并行触发（多条命令）。

## 第五步：返回结果

- Run / Pipeline ID 与 URL
- 状态（queued / created / pending / running）

**排队中的 run 属于「未证明」，不要报告成成功或失败。** 需要盯到结论时用
`gh run watch <run-id> --exit-status --repo <owner/repo>` 或 `glab ci view`。

## 错误处理

- **401 invalid_token（GitLab）**：`unset GITLAB_TOKEN GITLAB_ACCESS_TOKEN OAUTH_TOKEN` 后重试
- **找不到 workflow_dispatch / spec.inputs**：该 CI 不支持手动触发，如实告诉用户，不要改用其他仓库的命令
- **输入参数名错误**：回到第二步重新读取，不要靠试错猜参数
- **分支不存在**：确认 ref 后再触发
