---
name: defect-handler
description: 缺陷处理分析验证工作流 - 从场景理解、数据排查、代码定位、修复到测试验证的全流程。当用户报告 bug、缺陷、异常、数据不一致时使用。
---

# 缺陷处理分析验证工作流

从接收缺陷报告到完成修复验证的全流程规范。

## 使用场景

- 用户说"出现一个 bug"、"有个问题"、"数据不对"、"报错了"、"401/500"等
- API 返回非预期结果（错误码、错误数据）
- 前端表现与期望不符，需排查后端逻辑
- 数据不一致（如多出默认值、状态不对等）

## 工作流程

### 第一阶段：场景理解与复现

#### Step 1.1：明确复现步骤

通过提问收集以下信息：

| 问题 | 目的 |
|------|------|
| 具体什么操作后出现的？ | 定位触发入口 |
| 哪个用户/什么角色？ | 确定权限/身份路径 |
| 在哪个页面/哪个端？ | 教师端/家长端/小程序/Web |
| 期望应该是什么？实际是什么？ | 明确偏差 |
| 以前正常过吗？ | 判断回归还是新缺陷 |

**记录到 draft**：将复现步骤、用户信息写入 `.omo/drafts/{bug-slug}.md`。

#### Step 1.2：直接复现（如可复现）

用 curl 或 Playwright 直接复现缺陷：

```bash
# API 缺陷：直接调接口看返回
curl -s 'http://localhost:8080/v4/dotteacher.XXX' \
  -H 'authorization: Bearer <token>' \
  -H 'env: test' \
  -H 'content-type: application/json' \
  --data-raw '{}'
```

**记录关键信息**: token、请求体、响应 body、状态码。

---

### 第二阶段：数据排查

#### Step 2.1：解码 JWT Token（如涉及认证）

```bash
# 解 JWT payload（不含签名验证）
echo '<base64_payload>' | base64 -d 2>/dev/null
```

关键字段含义：
- `c`: UIN（user_identification.id）
- `a`: Audience（user/admin）
- `i`: Issuer（dotpen/yygu）
- `l`: LoginWay

#### Step 2.2：查询数据库确认数据状态

使用 `quick-db-read` skill 查询：

```go
// 示例：查 user_identification
uins, _ := account.NewUserIdentificationDao().GetListByCond(ctx, &account.UserIdentificationCond{
    BaseCond: account.BaseCond{Limit: 10},
    UserID:   3064,
})

// 示例：查 employee 确认角色
emps, _ := account.NewEmployeeDao().GetListByCond(ctx, &account.EmployeeCond{
    UinList: []uint{3157, 3158},
})
```

**查询要点**：
- 查 `user_identification` 看该用户有哪些 UIN
- 查 `employee` 看每个 UIN 的角色
- 查 `parent_identity` 看默认孩子状态
- 查 `user` 确认手机号/用户基础信息

#### Step 2.3：收集日志

从日志中提取关键信息：
- `caller` 定位到文件和行号
- 错误消息中的参数（uin、role、ID 等）
- 请求路径和参数（`uri`、`reqbody`）

#### Step 2.4：启动本地服务端捕获日志（需要时）

**当需要定位服务端行为缺陷时，启动本地后端服务进行日志捕获。**

⚠️ 仅在实际需要排查服务端逻辑时才启动，因为日志流会持续写入 `/tmp`（具体路径以配置文件为准）。

1. **询问用户是否需要启动**：说明目的和影响，确认后再执行
2. **处理端口冲突**：启动失败时检测端口占用，提问用户解决方案：
   ```bash
   lsof -i :<port>  # 查看占用进程
   ```
3. **启动服务并重定向日志**：
   ```bash
   cd /home/zoe/CodeSpace/gitlab/dotpen-api
   make run APP=dotteacher ENV=test > /tmp/dotteacher-debug.log 2>&1 &
   ```
4. **用 curl 触发缺陷 + 实时查看日志**：
   ```bash
   tail -f /tmp/dotteacher-debug.log &
   curl -s 'http://localhost:8080/v4/dotteacher.OcrLayout' \
     -H 'authorization: Bearer <token>' \
     -H 'content-type: application/json' \
     --data-raw '{"request":{"url":"<image-url>"}}'
   # 结束后 kill 后台 tail
   ```
5. **分析日志**：关键搜索 `[OcrLayout]`、`ERROR`、`ErrorContextf`、`caller` 定位代码行

---

### 第三阶段：代码定位

#### Step 3.1：确定入口 API

从复现步骤推断调用的 API，在对应 app 的 `internal/apis/apis.go` 或路由文件中找到注册点：

```bash
grep -n "XXX\|UserLogin\|ListAcademicYears" apps/dotteacher/internal/apis/apis.go
```

#### Step 3.2：追踪调用链

按依赖方向追踪：`apis` → `services/svc*` → `models/*`

```
internal/apis/handler.go  (入口，解析请求)
    ↓
services/svcxxx/service.go  (业务逻辑)
    ↓
models/xxx/dao.go  (数据访问)
```

**追踪重点**：
- apis 层：传了什么参数、中间件（`RequireRole`、`PRequireLogin`）
- svc 层：关键判断逻辑、条件分支
- 模型/DAO 层：查询条件、返回结果

#### Step 3.3：标记关键代码段

对每段关键逻辑记录：
- 文件路径 + 行号
- 当前代码（实际内容）
- 这段代码的用途
- 可疑点（是否符合预期）

---

### 第四阶段：完整复现路径与根因分析

#### Step 4.1：绘制数据流

用文字描述完整的请求处理路径，包含每个步骤的**参数值**和**逻辑判断结果**：

```
请求: POST /v4/dotteacher.ListAcademicYears
  Headers: Authorization=Bearer <token: c=3157>
  
Step 1: middleware.LoginStatus()
  token→UIN=3157, State=StateSucc
  
Step 2: InjectDotpenLoginStatus()
  employee.GetEmployeeByUin(3157) → SysRole="sys_parent"
  ls.Role = RoleParent

Step 3: RequireRole("sys_teacher")
  employee.GetEmployeeByUin(3157) → SysRole="sys_parent"
  "sys_parent" != "sys_teacher" → 401 Unauthorized

根因: JWT token 用了 UIN 3157（家长），但接口需要教师身份
```

#### Step 4.2：确认根因

用一句话描述根因，包含：
- 什么文件/函数
- 哪个变量/判断错了
- 正确的应该是什么

#### Step 4.3：代码映射表

| 步骤 | 文件 | 行号 | 代码 | 问题 |
|------|------|------|------|------|
| 生成 token | auth.go | 418 | `uins[0].ID` | 应该是 `luin[0].Uin.ID` |
| 创建家长 | parent.go | 506 | `hasDefault := false` | 应查已有默认 |

---

### 第五阶段：修复

#### Step 5.1：设计修复方案

明确：
- 改什么文件、改什么行
- 怎么改（旧代码 → 新代码）
- 改了之后什么行为变化

#### Step 5.2：实施修复

```go
// Before
token := user.GenerateJwtToken(uins[0].ID, ...)

// After
token := user.GenerateJwtToken(luin[0].Uin.ID, ...)
```

#### Step 5.3：编译验证

```bash
# 编译受影响的 APP
go build ./apps/dotteacher/...
go build ./apps/account/...
```

**编译通过不等于修复完成**。编译验证后必须执行 Step 6 测试验证。**每次代码改动（包括仅改排序、常量、注释等看似微小的变更）都必须跑测试确认无回归，不允许跳过。**

---

### 第六阶段：测试验证

#### Step 6.1：编写单元测试

在已有测试文件中添加用例，覆盖缺陷场景：

```go
t.Run("FixScenario[functional,P0,smoke]", func(t *testing.T) {
    // 1. Setup：创建测试数据
    phone := fmt.Sprintf("138%08d", time.Now().UnixNano()%100000000)
    parentUin, cleanup := createTestParent(t, ctx, phone, "测试")
    defer cleanup()

    // 2. Execute：执行缺陷路径
    res, err := EditParent(ctx, req)
    assert.Nil(t, err)

    // 3. Assert：验证结果符合预期
    pis, _ := account.NewParentIdentityDao().GetListByCond(...)
    assert.Equal(t, 1, defaultCount, "must have exactly one default")
})
```

**测试要点**：
- 测试必须能直接复现缺陷（修复前应 fail）
- 断言要具体（不笼统地 assert.Nil）
- 清理测试数据（defer cleanup）
- 使用唯一 phone/标识避免冲突

**覆盖要求**：
- **缺陷路径**：必须按用户描述的完整复现步骤编写测试用例，确保修复前 fail、修复后 pass
- **相关路径**：分析与该缺陷逻辑相关的其他代码路径（如同类 API、同类条件分支），逐个编写补充用例
  - 例如：`EditParent` 的默认孩子缺陷 → 还需覆盖 `UnbindParentStudent`、`DeleteParentIdentity`、`CreateParent`、`BindParentIdentities` 等同类路径
  - 例如：缺陷涉及删除场景 → 还需覆盖新增、修改等对比场景
- **边界条件**：覆盖空数据（无剩余孩子）、单条数据、多条数据的场景
- **回归验证**：运行受影响的包的全部测试，确保无回归

#### Step 6.2：运行测试

```bash
go test -v -run "TestXxx/FixScenario" -count=1 ./apps/dotteacher/services/svcparent/
```

#### Step 6.3：回归验证

```bash
# 运行受影响的包的全部测试
go test -count=1 ./apps/dotteacher/services/svcparent/...
```

---

## 各阶段检查清单

### 第一阶段
- [ ] 明确了复现步骤
- [ ] 知道了用户/角色/端
- [ ] 确认了期望 vs 实际
- [ ] 用 curl 或 Playwright 复现了缺陷

### 第二阶段
- [ ] 解码了 JWT（如涉及）
- [ ] 查了数据库确认数据状态
- [ ] 收集了相关日志
- [ ] （需要时）启动了本地服务并捕获了调试日志

### 第三阶段
- [ ] 找到了入口 API
- [ ] 追踪了完整调用链
- [ ] 标记了关键代码段

### 第四阶段
- [ ] 绘制了完整数据流
- [ ] 确认了根因
- [ ] 建立了代码映射表

### 第五阶段
- [ ] 设计了修复方案
- [ ] 实施了修复
- [ ] 编译通过

### 第六阶段
- [ ] 编写了复现缺陷的测试
- [ ] 测试通过
- [ ] 回归测试通过

## 工具速查

### 常用 DAO 查询

| 查询目标 | DAO | 条件 | 说明 |
|----------|-----|------|------|
| User 信息 | `account.NewUserDao().GetByCond` | `Phone`、`UserID` | 查用户基础信息 |
| UIN 列表 | `account.NewUserIdentificationDao().GetListByCond` | `UserID`、`Issuer` | 查用户所有身份标识 |
| Employee | `account.NewEmployeeDao().GetListByCond` | `UserID`、`UinList`、`SysRoles` | 查员工角色 |
| ParentIdentity | `account.NewParentIdentityDao().GetListByCond` | `ParentUin`、`StudentIDs` | 查家长绑定关系 |
| Student | `account.NewStudentDao().GetListByCond` | `StudentNos`、`ClassIDs` | 查学生信息 |

### 常用排查命令

```bash
# 解码 JWT
echo '<payload>' | base64 -d 2>/dev/null

# 查路由注册
grep -n "HandlerName" apps/*/internal/apis/apis.go

# 搜索代码
grep -rn "funcName\|variableName" apps/ --include="*.go"
```

```bash
# 启动本地服务并重定向日志到文件
make run APP=dotteacher ENV=test > /tmp/dotteacher-debug.log 2>&1 &

# 实时跟踪日志
tail -f /tmp/dotteacher-debug.log

# 搜索日志中的错误
grep -n "ERROR\|panic\|ErrorContextf" /tmp/dotteacher-debug.log
```

### 关键文件索引

| 类别 | 路径 | 说明 |
|------|------|------|
| Account API 路由 | `apps/account/internal/apis/apis.go` | 注册所有 account 接口 |
| Dotteacher API 路由 | `apps/dotteacher/internal/apis/apis.go` | 注册所有 dotteacher 接口 |
| 登录逻辑 | `apps/account/services/svcauth/auth.go` | 登录成功处理、token 生成 |
| 家长业务 | `apps/dotteacher/services/svcparent/parent.go` | CreateParent/EditParent/ListParents |
| 家长业务(account) | `apps/account/services/svcparent/parent.go` | BindParentIdentities |
| 学生业务 | `apps/dotstudent/services/svcstudent/student.go` | SetDefaultStudent/SwitchParentCompany |
| 角色鉴权 | `apps/account/accountmds/auth_sysadmin.go` | RequireRole/RequireRoles |
| 数据实体 | `apps/account/models/accounttype/employee.go` | SysRole 常量定义 |
| DAO: Employee | `apps/account/models/account/employee.go` | EmployeeDao |
| DAO: ParentIdentity | `apps/account/models/account/parent_identity.go` | ParentIdentityDao |
