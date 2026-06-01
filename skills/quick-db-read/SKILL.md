---
name: quick-db-read
description: 临时 Go 测试读取 MySQL 数据。创建一次性 `_test.go` 文件，利用 testutils 初始化 DB 连接，通过 DAO 查询数据。🛑 只读，禁止写操作，单次查询 ≤100 行。当需要查询数据库状态、确认数据、排查问题时使用。
---

# Quick DB Read — 临时 Go Test 读取 MySQL 数据

通过项目内的 Go 测试（`_test.go`）+ `testutils` 初始化数据库连接，使用 DAO 查询数据并 `t.Log` 输出。**只读，禁止写操作。**

---

## 铁律（违反立即终止）

1. **🛑 禁止任何写操作** — 不允许 `Create`、`Update`、`Delete`、`Save`、`Raw/Exec` 写 SQL、`INSERT/UPDATE/DELETE`。
2. **📏 单次查询 ≤ 100 行** — 需要 Limit 时用 `GetPageListByCond`（见下文常见错误）。
3. **⚡ 查询必须带精确条件** — 禁止无 WHERE 条件的全表扫描。至少通过 ID、Phone、Uin、UserID 等索引字段过滤。
4. **🧹 用完即删** — 查询完成后立即删除临时 `_test.go` 文件。
5. **✅ 仅用 DAO 查询** — 禁止直接用 `dbutil.Account().Raw(...)` 或 `dbutil.Account().Table(...)`。

---

## 操作步骤

### Step 1：确定查询目标与包路径

| 要查的数据 | `testutils.Initialize` | DAO import | 实体 import |
|---|---|---|---|
| user / employee / student / teacher / parent_identity / class / company | `testutils.AppNameAccount` | `apps/account/models/account` | `apps/account/models/accounttype` |
| dot_question / dot_assignment / dot_paper_test / dot_student_assignment | `testutils.AppNameAccount` | `apps/dotteacher/models/teacher` | `apps/dotteacher/models/teachertype` |

### Step 2：创建临时测试文件

在目标 package 下创建 `<desc>_test.go`，模板：

```go
package <原有package名>

import (
	"testing"

	"github.com/openrpacloud/dotpen-api/apps/account/models/account"
	"github.com/openrpacloud/dotpen-api/apps/account/models/accounttype"
	"github.com/openrpacloud/dotpen-api/pkgs/testutils"
	// teacher 库额外 import:
	// "github.com/openrpacloud/dotpen-api/apps/dotteacher/models/teacher"
	// "github.com/openrpacloud/dotpen-api/apps/dotteacher/models/teachertype"
)

func TestQueryXxx(t *testing.T) {
	testutils.Initialize(testutils.AppNameAccount)
	defer testutils.Close()
	ctx := testutils.NewCtx()

	// ⚠️ 要 Limit 时用 GetPageListByCond，GetListByCond 不处理 Limit！
	users, total, err := account.NewUserDao().GetPageListByCond(ctx, &account.UserCond{
		BaseCond: account.BaseCond{
			Limit:   10,
			Offset:  0,
			OrderBy: []string{"id desc"},
		},
	})
	if err != nil {
		t.Fatal(err)
	}
	t.Logf("total=%d, returned=%d", total, len(users))
	for _, u := range users {
		phone := ""
		if u.Phone != nil {
			phone = *u.Phone
		}
		t.Logf("  id=%-6d phone=%-15s name=%s created_at=%v",
			u.ID, phone, u.Name, u.CreatedAt.Format("2006-01-02 15:04:05"))
	}
}
```

### Step 3：运行测试

```bash
go test -v -run "TestQueryXxx" -count=1 ./apps/<path>/ 2>&1
```

### Step 4：读取结果，删除临时文件

```bash
rm apps/<path>/<desc>_test.go
```

---

## 常用 DAO 查询示例

### 查 User（按手机号，单条）

```go
u, err := account.NewUserDao().GetByCond(ctx, &account.UserCond{Phone: "19391933768"})
if u.ID == 0 {
    t.Log("user not found")
} else {
    t.Logf("user: id=%d, phone=%v, name=%s", u.ID, u.Phone, u.Name)
}
```

### 查 User（最近 N 条 — 用 GetPageListByCond）

```go
users, total, err := account.NewUserDao().GetPageListByCond(ctx, &account.UserCond{
    BaseCond: account.BaseCond{
        Limit:   10,
        Offset:  0,
        OrderBy: []string{"id desc"},
    },
})
t.Logf("total=%d", total)
for _, u := range users {
    t.Logf("  id=%-6d phone=%-15s name=%s", u.ID, u.Phone, u.Name)
}
```

### 查 Employee（按 UserID）

```go
emps, err := account.NewEmployeeDao().GetListByCond(ctx, &account.EmployeeCond{
    BaseCond: account.BaseCond{Limit: 100},
    UserID:   3059,
})
for _, e := range emps {
    t.Logf("emp: id=%d, uin=%d, role=%s, company=%d", e.ID, e.Uin, e.SysRole, e.CompanyID)
}
```

### 查 ParentIdentity（按 parent_uin）

```go
pis, err := account.NewParentIdentityDao().GetListByCond(ctx, &account.ParentIdentityCond{
    ParentUin: 3149,
})
for _, pi := range pis {
    t.Logf("pi: id=%d, student_id=%d, identity=%s, is_default=%d",
        pi.ID, pi.StudentID, pi.Identity, pi.IsDefault)
}
```

### 查 Student（按 ID）

```go
stu, err := account.NewStudentDao().GetByID(ctx, 2553)
t.Logf("student: id=%d, uin=%d, student_no=%s, class_id=%d",
    stu.ID, stu.Uin, stu.StudentNo, stu.ClassID)
```

### 查 UserIdentification（按 UserID）

```go
uis, err := account.NewUserIdentificationDao().GetListByCond(ctx, &account.UserIdentificationCond{
    BaseCond: account.BaseCond{Limit: 100},
    UserID:   3059,
})
for _, ui := range uis {
    t.Logf("uin: id=%d, subject_id=%d, subject_type=%s", ui.ID, ui.SubjectID, ui.SubjectType)
}
```

### 查 Teacher（按 uin 列表）

```go
teachers, err := account.NewTeacherDao().GetListByCond(ctx, &account.TeacherCond{
    BaseCond: account.BaseCond{Limit: 100},
    Uins:     []uint{3147},
})
for _, t := range teachers {
    t.Logf("teacher: id=%d, uin=%d, user_id=%d", t.ID, t.Uin, t.UserID)
}
```

### 查 Assignment（teacher 库，按 uin）

```go
asgns, err := teacher.NewAssignmentDao().GetListByCond(ctx, &teacher.AssignmentCond{
    BaseCond: teacher.BaseCond{Limit: 10},
    UinList:  []uint{3149},
})
for _, a := range asgns {
    t.Logf("assignment: id=%d, name=%s, uin=%d", a.ID, a.Name, a.Uin)
}
```

### 查 StudentAssignment（teacher 库，按 student_assignment_id）

```go
sas, err := teacher.NewStudentAssignmentDao().GetListByCond(ctx, &teacher.StudentAssignmentCond{
    BaseCond: teacher.BaseCond{Limit: 10},
    IDs:      []uint{123, 456},
})
for _, sa := range sas {
    t.Logf("sa: id=%d, student_id=%d, assignment_id=%d, status=%s",
        sa.ID, sa.StudentID, sa.AssignmentID, sa.Status)
}
```

### 查 PaperTest（teacher 库，按 uin）

```go
pts, err := teacher.NewPaperTestDao().GetListByCond(ctx, &teacher.PaperTestCond{
    BaseCond: teacher.BaseCond{Limit: 10},
    UinList:  []uint{3149},
})
for _, pt := range pts {
    t.Logf("paper_test: id=%d, name=%s, uin=%d", pt.ID, pt.Name, pt.Uin)
}
```

---

## ⚠️ 关键陷阱：GetListByCond 不处理 Limit

`BaseCond.Limit` 和 `Offset` 仅被 `GetPageListByCond` 使用，`GetListByCond` **会忽略它们**！

```go
// ✅ Limit 生效
users, total, err := dao.GetPageListByCond(ctx, &XxxCond{
    BaseCond: BaseCond{Limit: 10, Offset: 0, OrderBy: []string{"id desc"}},
})

// ❌ Limit 被忽略，返回全部数据
users, err := dao.GetListByCond(ctx, &XxxCond{
    BaseCond: BaseCond{Limit: 10},
})
```

**查单条 → `GetByCond` / `GetByID`**（返回单条记录，指针）
**查列表不限量 → `GetListByCond`**（返回全部匹配行）
**查列表限量/分页 → `GetPageListByCond`**（返回 `(list, total, error)`）

---

## 常见错误

| 错误 | 原因 | 解决 |
|---|---|---|
| `package X, got Y` | 临时文件 package 名写错 | 用目标目录原有的 package 名 |
| `undefined: account.NewXxxDao` | 漏 import DAO 包 | 加 `apps/account/models/account` |
| `GetListByCond 未限制行数` | 用了 `GetListByCond` 但传了 Limit | 改用 `GetPageListByCond` |
| `sql: Scan error on column index X` | 实体字段与表结构不匹配 | 确认用了正确的实体类型 |
| `phone 字段是 **string` | User.Phone 是 `*string`，判空用 `u.Phone != nil` | `*u.Phone` 取值 |
| `测试跑太久` | 初始化 DB 连接慢 | 正常，约 1-3 秒 |
