---
name: deploy-service
description: Trigger GitLab CI deployment pipelines for dotpen-api services. Use when user wants to deploy services like dotworker, dotinit, dotteacher etc. Supports different environments (image, test, prod) and branches/tags.
---

# 部署服务触发工作流

通过 GitLab CI 触发 dotpen-api 服务的部署 pipeline。

## 使用场景

- 用户说"触发部署"、"部署服务"、"deploy"
- 用户指定环境+ 服务名 + 分支
- 用户说"部署 dotworker 到 prod"
- 用户说"发布 image 环境，dotworker 和 dotinit，分支 dot-v2.5.1"

## 前置要求

1. **glab CLI** 已安装并配置认证
2. **glab alias** 已配置 `deploy-service` alias：
   ```bash
   glab alias set deploy-service 'ci run --input environment:"$1" --input app:"$2" --branch "$3"'
   ```

验证 alias：
```bash
glab alias list
```

## 参数说明

| 参数 | 说明 | 示例 |
|------|------|------|
| environment | 部署环境 | `image`, `test`, `prod` |
| app | 服务名称 | `dotworker`, `dotinit`, `dotteacher`, `dotpen` 等 |
| branch | 分支或 tag | `main`, `feature-2.5`, `dot-v2.5.1` |

## 工作流程

### 第一步：解析用户意图

从用户请求中提取：
- **environment**: 部署环境（默认 `image`）
- **apps**: 服务列表（可多个）
- **branch**: 分支或 tag名

### 第二步：确认参数（必须执行）

**重要：每次触发前必须先确认参数，得到用户明确同意后才执行。**

使用 `question` 工具询问用户确认：

```
问题：确认部署以下服务？
- 环境: <environment>
- 服务: <app1>, <app2> ...
- 分支/tag: <branch>
- 是否确认执行？

选项：确认执行 / 取消
```

### 第三步：触发 pipeline

对每个服务执行：
```bash
glab deploy-service <environment> <app> <branch/tag>
```

示例：
```bash
# 单服务
glab deploy-service image dotworker dot-v2.5.1

# 多服务（并行执行）
glab deploy-service image dotworker dot-v2.5.1
glab deploy-service image dotinit dot-v2.5.1
```

### 第四步：返回结果

- Pipeline ID
- Pipeline URL
- 状态（created/pending/running）

## 示例交互

```
用户: 触发两个工作流，dot-v2.5.1 下的 image，然后选择 dotworker 与 dotinit

Agent:
1. 解析：environment=image, apps=[dotworker, dotinit], branch=dot-v2.5.1
2. 询问确认：
   - 环境: image
   - 服务: dotworker, dotinit
   - 分支/tag: dot-v2.5.1
   是否确认执行？
3. 用户确认后执行：
   glab deploy-service image dotworker dot-v2.5.1
   glab deploy-service image dotinit dot-v2.5.1
4. 返回：
   - dotworker: Pipeline #4930 - https://git.yygu.cn/dotpen/dotpen-api/-/pipelines/4930
   - dotinit: Pipeline #4931 - https://git.yygu.cn/dotpen/dotpen-api/-/pipelines/4931
```

```
用户: 部署 dotteacher 到 prod，分支 feature-2.5

Agent (询问确认):
- 环境: prod
- 服务: dotteacher
- 分支/tag: feature-2.5
是否确认执行？

用户: 确认

Agent:
glab deploy-service prod dotteacher feature-2.5
```

```
用户: 发布服务

Agent (询问):
- 环境？[image / test / prod]
- 服务？[dotworker / dotinit / dotteacher / dotpen ...]
- 分支？[输入分支或 tag名]
```

## 可用服务与环境（实时读取）

**不要硬编码服务列表！** 每次触发前从 `.gitlab-ci.yml` 文件实时读取。

### 读取方法

从 `.gitlab-ci.yml` 的 `spec.inputs` 部分解析：

```bash
# 读取环境列表（spec.inputs.environment.options）
grep -A 10 "environment:" .gitlab-ci.yml | grep "options:" -A 10

# 读取服务列表（spec.inputs.app.options）
grep -A 30 "app:" .gitlab-ci.yml | grep "options:" -A 30
```

或使用 Read 工具读取 `.gitlab-ci.yml` 后提取 `spec.inputs` 下的 options。

### 示例解析结构

`.gitlab-ci.yml` 结构示意：
```yaml
spec:
  inputs:
    environment:
      options:
        - <env_option_1>
        - <env_option_2>
        - ...
    app:
      options:
        - <app_option_1>
        - <app_option_2>
        - ...
```

每次执行 skill 时：
1. Read `.gitlab-ci.yml`
2. 解析 `spec.inputs.environment.options` 得到可用环境
3. 解析 `spec.inputs.app.options` 得到可用服务
4. 将列表展示给用户选择或确认

## 注意事项

1. **环境区分**：
   - `image`: 构建镜像环境（用于测试镜像构建）
   - `test`: 测试环境
   - `prod`: 生产环境（谨慎使用）

2. **分支/tag**：
   - 可以是分支名（如 `feature-2.5`）
   - 可以是 tag名（如 `dot-v2.5.1`）

3. **多服务并行**：使用多个 Bash 调用并行触发

4. **确认生产部署**：prod 环境建议先确认

## 错误处理

- **alias 未配置**：提示用户配置 `glab alias set deploy-service ...`
- **pipeline 创建失败**：检查 glab 认证、分支是否存在
- **服务名无效**：列出可用服务供用户选择