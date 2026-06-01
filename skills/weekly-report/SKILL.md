# Weekly Report — 周报生成技能

根据 GitLab 提交自动生成周报。

## 触发条件

当用户说"写周报"、"生成周报"、"总结本周工作"、"weekly report"时使用。

## 工作流程

### 1. 收集提交数据

从所有相关 worktree 目录收集 git 提交：

```bash
# 主仓库
cd /home/zoe/CodeSpace/gitlab/dotpen-api && git log --oneline --since="起始日期" --until="结束日期" --author="$(git config user.name)" | grep -v "Merge\|WIP\|index"

# 2.7 worktree
cd /home/zoe/CodeSpace/gitlab/dotpen-api-2.7 && git log --oneline --since="起始日期" --until="结束日期" --author="$(git config user.name)" | grep -v "Merge"
```

默认日期范围：本周一 ~ 下周一。用户可指定如"上周"。

### 2. 收集 MR 数据

```bash
cd /home/zoe/CodeSpace/gitlab/dotpen-api && glab mr list --all
```

筛选本周的 MR 作为补充参考，但**不写入周报正文**（见排除规则）。

### 3. 分类整理

将提交按功能类别分组（去重同一功能的多条提交）：
- **feat**: 新功能
- **fix**: bug 修复
- **refactor**: 重构

### 4. 生成周报

按以下格式输出：

```
一、本周进展：

1. [功能名]简述
2. ...

二、风险与问题：

暂无

三、下周计划：

[询问用户]
```

保存到 `weekly-reports/YYYY-Wxx.md`。

## 排除规则（必须遵守）

1. **不写 MR 标号**：周报是给团队看的业务总结，不需要 MR#xxx 引用
2. **AI 自审代码不算工作产出**：ReviewCode 规范修复（G-01~G-13 注释/命名/DAO 规范等）是 AI 对自身代码的审阅修正，不是业务功能，不应写入"本周进展"
3. **style/docs 类提交排除**：纯粹的注释补充、godoc 修复、swag 去重不算工作产出
4. **同一功能多提交合并为一行**：如 feat→fix→fix 只保留最终效果描述
5. **去除 Merge/WIP/stash commits**

## 写入原则

- 只写**业务功能**和**实际 bug 修复**
- 描述用业务语言而非技术术语（如"升学制功能"而非"GORM Model起链修复"）
- 但 bug 修复可简述根因（如"WHERE conditions required 修复"）

## 下周计划

必须询问用户，不可自行推断。
