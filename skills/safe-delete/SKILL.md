---
name: safe-delete
description: 禁止使用 rm -rf / rm 直接删除文件。当用户要求删除、清理、移除文件或目录时，或 agent 在执行操作中需要删除文件时使用。触发词包括"删除"、"清理"、"移除"、"去掉"、"delete"、"remove"、"clean up"、"rm"。所有删除操作必须路由为 mv 到回收目录。
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# Safe Delete (安全删除)

## 概述

**绝对禁止使用 `rm`（包括 `rm -rf`、`rmdir`、`rm -r` 等任何变体）删除文件或目录。**

所有"删除"操作必须使用 `mv` 将文件移动到回收目录，而非真正的删除。

## 核心规则

```
❌ rm -rf /path/to/target          # 禁止
❌ rm /path/to/file                # 禁止
❌ rmdir /path/to/dir              # 禁止
❌ rm -r /path/to/dir              # 禁止
❌ rm -f /path/to/file             # 禁止
❌ rm --recursive /path/to/dir     # 禁止

✅ mv /path/to/target ~/Downloads/Trash/YYYY-MM-DD/   # 正确
✅ mv /path/to/target /tmp/safe-delete-xxxxx/         # 正确（临时文件）
```

## 回收目录结构

```
~/Downloads/Trash/
├── 2026-06-03/          # 日期命名的回收目录
│   ├── deleted-file.txt
│   └── deleted-folder/
├── 2026-06-02/
│   └── old-config.yaml
└── ...
```

## 操作步骤

### Step 1：创建日期回收目录

```bash
mkdir -p ~/Downloads/Trash/$(date +%Y-%m-%d)
```

### Step 2：将目标移动到回收目录

```bash
# 删除单个文件
mv target.txt ~/Downloads/Trash/$(date +%Y-%m-%d)/

# 删除整个目录
mv target-dir/ ~/Downloads/Trash/$(date +%Y-%m-%d)/

# 删除多个文件
mv file1.txt file2.txt dir3/ ~/Downloads/Trash/$(date +%Y-%m-%d)/
```

### 替代路径：/tmp

对于临时构建产物、缓存文件等不需要长期保留的内容，可以使用 `/tmp`：

```bash
mkdir -p /tmp/safe-delete-$(date +%Y-%m-%d)
mv build-output/ /tmp/safe-delete-$(date +%Y-%m-%d)/
```

### Step 3：确认操作成功

```bash
ls ~/Downloads/Trash/$(date +%Y-%m-%d)/
# 确认文件已存在回收目录中
```

## 触发场景

以下场景必须使用本 skill：

| 场景 | 示例 |
|------|------|
| 用户要求"删除"文件 | "把 a.txt 删掉" → `mv a.txt ~/Downloads/Trash/...` |
| 清理临时文件 | "清理 build 目录" → `mv build/ ~/Downloads/Trash/...` |
| 替换/覆盖文件前 | 先 mv 旧文件到回收，再生成新文件 |
| 重构移动代码 | 删除旧文件 → mv 到回收 |
| 清理 git 分支后 | 删除本地文件 → mv 到回收 |
| 测试中清理临时数据 | teardown 中 mv 而非 rm |

## 常见错误与反模式

| ❌ 错误做法 | ✅ 正确做法 |
|------------|------------|
| `rm -rf node_modules` | `mv node_modules /tmp/safe-delete-node_modules/` |
| `rm config.toml` | `mv config.toml ~/Downloads/Trash/$(date +%Y-%m-%d)/` |
| `rmdir empty-dir` | `mv empty-dir ~/Downloads/Trash/$(date +%Y-%m-%d)/` |
| `find . -name "*.tmp" -delete` | `find . -name "*.tmp" -exec mv {} ~/Downloads/Trash/$(date +%Y-%m-%d)/ \;` |
| 用 Python `os.remove()` | 用 `shutil.move()` 到回收目录 |
| 用 Node.js `fs.unlinkSync()` | 用 `fs.rename()` 到回收目录 |

## 编程语言中的安全删除

### Shell
```bash
# ❌ 禁止
rm -rf /path/to/dir
# ✅ 正确
mv /path/to/dir ~/Downloads/Trash/$(date +%Y-%m-%d)/
```

### Python
```python
import shutil, os, datetime
from pathlib import Path

# ❌ 禁止
os.remove("/path/to/file")
shutil.rmtree("/path/to/dir")

# ✅ 正确
trash_dir = Path.home() / "Downloads" / "Trash" / datetime.date.today().isoformat()
trash_dir.mkdir(parents=True, exist_ok=True)
shutil.move("/path/to/file", str(trash_dir / "file"))
shutil.move("/path/to/dir", str(trash_dir / "dir"))
```

### Node.js
```javascript
const fs = require('fs');
const path = require('path');

// ❌ 禁止
fs.unlinkSync('/path/to/file');
fs.rmSync('/path/to/dir', { recursive: true });

// ✅ 正确
const trashDir = path.join(os.homedir(), 'Downloads', 'Trash', 
  new Date().toISOString().slice(0, 10));
fs.mkdirSync(trashDir, { recursive: true });
fs.renameSync('/path/to/file', path.join(trashDir, 'file'));
```

### Go
```go
// ❌ 禁止
os.Remove("/path/to/file")
os.RemoveAll("/path/to/dir")

// ✅ 正确
trashDir := fmt.Sprintf("%s/Downloads/Trash/%s", 
    os.Getenv("HOME"), time.Now().Format("2006-01-02"))
os.MkdirAll(trashDir, 0755)
os.Rename("/path/to/file", trashDir+"/file")
```

## 放弃此规则的借口与正解

| 借口 | 现实 |
|------|------|
| "这只是个临时文件" | 临时文件也 mv 到 `/tmp/`，不要 rm |
| "文件太大了 mv 很慢" | mv 在同文件系统内是 O(1) 重命名，不耗时 |
| "目录里有百万个小文件" | mv 目录本身也是 O(1) 重命名操作 |
| "反正有 git 可以恢复" | git 只跟踪 tracked 文件，untracked/config 无法恢复 |
| "我在 CI/CD 脚本里" | 在临时工作目录 mv 到同级子目录即可，结束后自动清理 |
| "这个文件是生成的，没关系" | 生成的也有调试价值，mv 不增加成本 |
| "先 rm，后续如果需要再 git checkout" | 新文件/未提交文件无法 checkout 恢复 |
| "操作系统 rm 都允许为什么我不能用" | rm 不可逆，mv 可逆，本 skill 要求 100% 可逆操作 |
| "我用的是 rmdir 不是 rm" | rmdir 同样是不可逆删除，禁止 |
| "我用 Python 的 os.remove 不算 rm" | 任何形式的文件删除操作都禁止 |
| "shutil.rmtree 参数递归删除目录" | 同上，任何形式的删除都禁止，必须 mv 到回收 |

## 红旗警告

出现以下想法时，说明你在找借口绕过规则：

- "这次用 rm 没关系，因为..."
- "只是个小文件，rm 更快"
- "我先用 rm，之后可以 git checkout"
- "这是 CI/CD 环境，不用管"
- "这个目录太特殊了，不需要备份"
- "用户说的删除就是用 rm"
- "我在脚本里用 rm -f 清理临时文件"
- "rmdir 不算 rm"

**以上任何想法出现 → 立即停用 rm，改用 mv 到回收目录。**

## 规则优先级

本 skill 的规则优先级高于效率考量：

1. **数据安全优先**：宁可多占用一些磁盘空间，也不要丢失数据
2. **可逆操作优先**：任何文件操作必须可逆
3. **规则无例外**：不存在 "这个场景可以用 rm" 的例外
