---
name: db-mcp-installer
description: Use when user mentions "连接数据库"、"database MCP"、"配置数据库"、"数据库 MCP"、"install database mcp"、"add database" or when project needs database access via MCP. Scans project for database connection strings and auto-configures the matching MCP server.
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# DB MCP Installer

## 概述

自动检测项目中的数据库连接信息，匹配并安装对应的 MCP 服务器，配置到 `opencode.json` 或 `.mcp.json`。

## 检测流程

```
用户提到"配数据库" / "数据库 MCP"
    │
    ├── 1. 扫描项目中的数据库连接
    │      ├── .env / .env.* → DATABASE_URL / DB_* / 等
    │      ├── config/*.json / config/*.yaml
    │      ├── docker-compose.yml
    │      ├── application*.yml / application*.properties (Spring)
    │      └── 源码中的连接字符串 (jdbc: / postgresql:// / mysql:// )
    │
    ├── 2. 识别数据库类型
    │      ├── postgresql:// / jdbc:postgresql → PostgreSQL
    │      ├── mysql:// / jdbc:mysql → MySQL
    │      ├── sqlite:// / .db 文件 → SQLite
    │      ├── mssql / jdbc:sqlserver → MSSQL
    │      └── mongodb:// → MongoDB
    │
    ├── 3. 匹配 MCP 服务器
    │      ├── PostgreSQL → @modelcontextprotocol/server-postgres
    │      ├── MySQL → @anthropic/server-mysql / @modelcontextprotocol/server-mysql
    │      ├── SQLite → @modelcontextprotocol/server-sqlite
    │      ├── MSSQL → @modelcontextprotocol/server-mssql
    │      └── MongoDB → @anthropic/server-mongodb
    │
    └── 4. 安装 & 配置
           ├── 检查 opencode.json 是否已有该 MCP
           ├── 已有 → 询问是否使用现有配置
           └── 没有 → npx 安装 + 写入 opencode.json 的 mcp 段
```

## 数据库连接扫描

搜索以下位置（按优先级）：

| 优先级 | 位置 | 搜索方式 |
|--------|------|----------|
| 1 | `.env`, `.env.local`, `.env.*` | Grep `DATABASE_URL`, `DB_`, `PG*`, `MYSQL*` |
| 2 | `config/*.json`, `config/*.yaml` | Grep 连接字符串模式 |
| 3 | `docker-compose.yml` | 解析 `environment` 或 `image` 字段 |
| 4 | `application*.yml`, `application*.properties` | 用于 Spring Boot 项目 |
| 5 | 源码中的硬编码连接 | Grep `://` + `password=` 模式 |
| 6 | `*.sql` 文件中的 `CREATE DATABASE` | 了解预期的数据库类型 |

### 搜索命令示例

```bash
# 搜索 .env 文件中的数据库连接
rg -i "DATABASE_URL|DB_HOST|DB_NAME|PGHOST|MYSQL_HOST" .env* 2>/dev/null

# 搜索配置文件中的 jdbc 连接
rg -i "jdbc:|postgresql://|mysql://|sqlite://|mongodb://" --include "*.yml" --include "*.yaml" --include "*.json" --include "*.properties" -r

# 搜索源码中的连接字符串
rg -i "postgresql://|mysql://|sqlite://|mongodb://" --type-add 'code:*.{go,py,js,ts,java,rs,cs,php}' -t code

# 搜索 docker-compose 中的数据库镜像
rg -i "image:.*(postgres|mysql|mariadb|mssql|mongo|redis)" docker-compose*.yml
```

## 数据库类型 → MCP 映射

| 数据库 | MCP 包 | 连接示例 |
|--------|--------|----------|
| PostgreSQL | `@modelcontextprotocol/server-postgres` | `postgresql://user:pass@host:5432/db` |
| MySQL | `@modelcontextprotocol/server-mysql` | `mysql://user:pass@host:3306/db` |
| SQLite | `@modelcontextprotocol/server-sqlite` | `sqlite:///path/to/db.sqlite` |
| MSSQL | `@modelcontextprotocol/server-mssql` | `Server=host;Database=db;User Id=...` |
| MongoDB | `@modelcontextprotocol/server-mongodb` | `mongodb://user:pass@host:27017/db` |

## 安装与配置

### 安装 MCP 服务器

MCP 服务器通过 `npx` 按需执行，无需全局安装：

```bash
# 验证 MCP 包可访问
npx -y @modelcontextprotocol/server-postgres --help
```

### 写入 opencode.json

在 `opencode.json` 的 `mcp` 段添加配置：

```json
{
  "mcp": {
    "<db-name>": {
      "type": "local",
      "command": [
        "npx",
        "-y",
        "<mcp-package>",
        "<connection-string>"
      ]
    }
  }
}
```

也可写入项目级 `.mcp.json`（如果项目使用）：

```json
{
  "mcpServers": {
    "<db-name>": {
      "command": "npx",
      "args": ["-y", "<mcp-package>", "<connection-string>"]
    }
  }
}
```

### 配置示例

PostgreSQL:
```json
"postgres": {
  "type": "local",
  "command": [
    "npx",
    "-y",
    "@modelcontextprotocol/server-postgres",
    "postgresql://user:pass@localhost:5432/mydb"
  ]
}
```

MySQL:
```json
"mysql": {
  "type": "local",
  "command": [
    "npx",
    "-y",
    "@anthropic/server-mysql",
    "mysql://user:pass@localhost:3306/mydb"
  ]
}
```

## 安全检查

- 连接字符串可能包含密码，**不要**将密码明文写入公开仓库
- 优先使用环境变量引用：`"${DATABASE_URL}"`
- 如果扫描到密码明文，提示用户使用 `.env` 替代

## 示例

用户："帮我配一下项目的数据库"

1. 搜索项目中的 `.env`，找到 `DATABASE_URL=postgresql://admin:pass@prod:5432/app`
2. 检测到 PostgreSQL
3. 检查 `opencode.json` — 已有 `postgres` MCP，询问是否复用
4. 若无，写入新的 PostgreSQL MCP 配置
5. 输出结果摘要
