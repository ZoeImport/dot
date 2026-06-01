---
name: unit-test-generate
description: "根据 TestSpec 注释标签生成完备的 Go 单元测试，包含子测试、断言、复杂度评估、基准测试及完整测试文档。适用 dotpen-api 项目。当用户要求"写单元测试"、"补充测试"、"generate tests"、"生成测试"、"加测试"、"补测试"时触发。"
---

# Unit Test Generate — 基于 TestSpec 的 Go 单元测试生成

根据 TestSpec YAML 约定生成完备的 Go 单元测试，包含子测试（`t.Run`）、断言（`testify/assert`）、复杂度评估、Benchmark 及整合到 `~/Downloads/` 的测试文档。遵循双 Agent 工作流：Agent A 生成测试，Agent B 分析 `go test -v` 输出定位失败。

---

## 触发条件

当用户提出以下请求或场景时触发本 Skill：

- "写单元测试"、"生成测试"、"补测试"、"加测试"
- "generate tests"、"add tests"、"write unit tests"
- PR review 要求补充测试覆盖率
- 功能开发完成后需要验证
- 代码变更后需要更新或扩充测试
- TestSpec 中标记 `deprecated` 的方法需要新断言生效

---

## 前置知识 — 项目测试基础设施

### 2.1 `pkgs/testutils` 全量 API

| 函数 | 签名 | 说明 |
|------|------|------|
| `Initialize` | `func(app AppName)` | 初始化测试环境（DB + Redis + 日志），`sync.Once` 保证单次 |
| `Close` | `func()` | 关闭测试环境 |
| `NewCtx` | `func(opts ...Option) *gin.Context` | 创建带 `context.Background` 的 `*gin.Context`，注入 requestID |
| `WithUin` | `func(uin uint) Option` | 注入登录态：生成 JWT token，设置 uin + companyID |
| `OpenFile` | `func(relPath string) (*os.File, error)` | 打开相对当前测试文件的测试数据文件 |
| `TestFilePath` | `func(relPath string) string` | 返回相对当前测试文件的测试数据文件路径 |

**AppName 常量与初始化行为：**

| AppName | 初始化范围 | 配置路径 |
|---------|-----------|----------|
| `AppNameAccount` | DB + Redis | `apps/account/conf/test/config.yaml` |
| `AppNameTeacher` | DB + Redis | `apps/dotteacher/conf/test/config.yaml` |
| `AppNameStudent` | DB + Redis | `apps/dotteacher/conf/test/config.yaml` |
| `AppNameDotpen` | DB + Redis + 任务管理器 | `apps/dotteacher/conf/test/config.yaml` |
| `AppNameExamAPI` | DB + Redis | `apps/examapi/conf/test/config.yaml` |

### 2.2 `testify/assert` 用法

**当前项目实况**：仅使用 `assert.Nil(t, err)`，无子测试、table-driven、Benchmark、`testing.Short()`、build tags、mock 框架。

**本 Skill 引入的断言模板**（不引入 `require` 和 `suite`）：

| 断言 | 用途 |
|------|------|
| `assert.Nil(t, err)` | err == nil |
| `assert.NotNil(t, obj)` | obj != nil |
| `assert.Equal(t, expected, actual)` | 值相等 |
| `assert.NotEqual(t, unexpected, actual)` | 值不等 |
| `assert.True(t, cond)` | 条件为真 |
| `assert.False(t, cond)` | 条件为假 |
| `assert.Empty(t, obj)` | 空值（nil / "" / 0 / 空 slice） |
| `assert.NotEmpty(t, obj)` | 非空 |
| `assert.Error(t, err)` | err != nil |
| `assert.ErrorIs(t, err, target)` | err wraps target error |
| `assert.Len(t, obj, n)` | 长度 == n |
| `assert.Greater(t, a, b)` | a > b |
| `assert.JSONEq(t, expected, actual)` | JSON 语义相等 |

**不引入**：
- `require` — 跳过掩盖后续错误
- `suite` — 当前项目无此模式

### 2.3 Go Native Test Patterns（本 Skill 引入）

| 机制 | 用途 |
|------|------|
| `t.Run` | 子测试，每个 Assertion 一条 |
| Table-driven tests | 同一 Assertion 多组数据时用 |
| `BenchmarkXxx` + `b.ReportAllocs()` | 仅 `BenchmarkReq: true` 且纯计算函数 |
| `testing.Short()` | Integration 测试跳过标记 |
| `//go:build integration` | E2E 测试 build tag |
| **无 mock 框架** | 使用 real DAO + testutils |

---

## TestSpec YAML 约定

TestSpec 存放在 `~/Downloads/_test_spec.md` 整合文件的 YAML frontmatter 中，不在 Go doc comment 中存放完整 Spec。不生成 `_test.md` 到代码仓库。

### 3.1 Go 函数注释中的标记

在函数注释中添加简短的 TestSpec 引用标记：

```go
// CalculateScore calculates the assignment score for a student.
//
// TestSpec: assignment-scoring (see ~/Downloads/_test_spec.md)
func CalculateScore(ctx context.Context, assignmentID uint, answers []Answer) (int, error) {
```

### 3.2 完整 YAML 格式示例（简单函数）

```yaml
---
TestSpec:
  Function: CalculateScore
  Version: v2.1.0
  Workflow: assignment-scoring
  VerifyLogic: 将返回的 score 与手动计算结果对比
  ExpectedDuration: 50ms
  TestLevel: integration
  Tags: [db, slow]

  Complexity:
    Best: Time=O(1) Space=O(1)
    Worst: Time=O(n) Space=O(n)
    Average: Time=O(n) Space=O(1)
    Notes: n = len(answers)

  Performance:
    Bottleneck: DB GetByIDs 批量查询 answer key
    BenchmarkReq: false

  TestData:
    - entity: AnswerKey
      table: teacher.answer_keys
      dao: AnswerKeyDao.Create
      fields: { AssignmentID: 899 }
      cleanup: DeleteByIDs

  SideEffects:
    - DBWrite: student_assignments.score 更新

  Constraints:
    async: false
    externalCalls: false
    channels: false
    globalState: none

  Dependencies:
    - DAO: AnswerKeyDao.GetByAssignmentID
    - Auth: student role token

  Assertions:
    - id: AllCorrect
      type: functional
      priority: P0
      group: smoke
      flaky: false
      tolerance: 0
      since: v2.0.0
      desc: 全部正确 → score == FullMark(100)
      states:
        - given: { answers: allCorrect, assignmentID: 899 }
          when: CalculateScore(ctx, 899, allCorrect)
          then: { score: 100, err: nil }

    - id: EmptySubmit
      type: boundary
      priority: P1
      group: regression
      since: v2.0.0
      desc: 空提交 → score == 0
      states:
        - given: { answers: [], assignmentID: 899 }
          when: CalculateScore(ctx, 899, [])
          then: { score: 0, err: nil }

    - id: MissingKey
      type: exception
      priority: P1
      group: regression
      deps: [AllCorrect]
      since: v1.0.0
      deprecated: v3.0.0
      desc: 缺少答案 key → error
      states:
        - given: { assignmentID: 99999 }
          when: CalculateScore(ctx, 99999, any)
          then: { err: ErrAnswerKeyNotFound }
---
```

### 3.3 多维度 Cond 查询断言示例

适用于 List / Search / Page 类函数，每个 cond 字段组合对应独立的 Assertion：

```yaml
  Assertions:
    - id: ListByClassID
      type: functional
      priority: P1
      group: regression
      desc: 仅按班级过滤，单维度 teacher DB 单表查询
      params: { ClassID: uint }
      states:
        - given: { cond: { ClassID: 301 } }
          when: ListStudents(ctx, cond)
          then: { students.length > 0, err: nil }

    - id: ListByClassAndStatus
      type: functional
      priority: P1
      group: regression
      desc: 班级+状态组合，复合条件索引路径
      params: { ClassID: uint, Status: string }
      states:
        - given: { cond: { ClassID: 301, Status: "active" } }
          when: ListStudents(ctx, cond)
          then: { students[0].Status == "active", err: nil }

    - id: ListWithUserInfo
      type: functional
      priority: P2
      group: regression
      desc: 跨库查询 student + 账号（teacher + account DB）
      params: { ClassID: uint, IncludeUserInfo: bool }
      sideEffects: [CrossDB: "teacher.students + account.users"]
      states:
        - given: { cond: { ClassID: 301, IncludeUserInfo: true } }
          when: ListStudents(ctx, cond)
          then: { students[0].Phone != "", err: nil }

    - id: ListAllNoCond
      type: boundary
      priority: P1
      group: regression
      desc: 不传任何条件，走默认分页路径
      params: {}
      states:
        - given: { cond: {} }
          when: ListStudents(ctx, StudentCond{})
          then: { total > 0, err: nil }
```

### 3.4 字段参考

**顶层字段（函数级）：**

| 字段 | 必填 | 值域 | 说明 |
|------|------|------|------|
| `Function` | ✅ | string | 被测函数名 |
| `Version` | ✅ | semver | 当前迭代版本 |
| `Workflow` | ✅ | string | 工作流标识，如 `assignment-scoring` |
| `VerifyLogic` | ✅ | string | 验证逻辑描述 |
| `ExpectedDuration` | ✅ | string | 单次预期耗时，如 `50ms` |
| `TestLevel` | ✅ | `unit` / `integration` / `e2e` | 测试级别 |
| `Tags` | 推荐 | string[] | 如 `[db, slow, network]` |
| `Complexity` | ✅ | object | Best / Worst / Average + Notes |
| `Performance` | 条件 | object | Bottleneck + BenchmarkReq (bool) |
| `TestData[]` | ✅ | 数组 | entity / table / dao / fields / cleanup |
| `SideEffects[]` | 条件 | string[] | DBWrite / CacheSet / QueuePublish |
| `Constraints` | 条件 | object | async / externalCalls / channels / globalState |
| `Dependencies[]` | ✅ | string[] | DAO / Auth / DB 依赖 |

**Per-Assertion 字段：**

| 字段 | 必填 | 值域 | 说明 |
|------|------|------|------|
| `id` | ✅ | string | 映射到 `t.Run` 名称 |
| `type` | ✅ | `functional` / `boundary` / `exception` / `performance` | 测试分类 |
| `priority` | ✅ | `P0` / `P1` / `P2` / `P3` | CI 分级 |
| `group` | ✅ | `smoke` / `regression` / `full` | 测试分组 |
| `flaky` | 推荐 | boolean | 不稳定标记，true 时自动加 for 循环重试 2 次 |
| `tolerance` | 条件 | 数字+单位(ms/s/%) | 浮点/耗时偏差允许范围 |
| `since` | 推荐 | semver | 断言引入版本 |
| `deprecated` | 条件 | semver | 废弃标记，generator 可选跳过 |
| `params` | 条件 | object | 标识此断言覆盖的 cond 查询维度 |
| `deps` | 条件 | string[] | 顺序依赖，按序排列子测试 |
| `states[]` | ✅ | 数组 | given → when → then 数据流 |

### 3.5 标签枚举字典

**type（测试分类）：**

| 标签 | 中文说明 |
|------|----------|
| `type:functional` | 功能验证 — 正常路径，核心逻辑 |
| `type:boundary` | 边界验证 — 极端值/空/最大/最小 |
| `type:exception` | 异常验证 — 错误路径/panic/超时 |
| `type:performance` | 性能验证 — 耗时/吞吐量基准 |

**priority（优先级）：**

| 标签 | 中文说明 |
|------|----------|
| `priority:P0` | 阻塞门禁 — 失败阻断发布 |
| `priority:P1` | 核心回归 — 每次 CI 必跑 |
| `priority:P2` | 常规验证 — 全量回归时执行 |
| `priority:P3` | 可选验证 — 手动触发时执行 |

**group（测试分组）：**

| 标签 | 中文说明 |
|------|----------|
| `group:smoke` | 冒烟测试 — 快速验证核心流程 |
| `group:regression` | 回归测试 — 完整功能回归 |
| `group:full` | 全量测试 — 包含耗时/不稳定/边界 |

---

## 工作流程

### Step -2: 范围确认（必须向用户提问）

技能触发后，**必须先向用户确认生成范围**，不得直接开始。提问内容：

> 本次是要对**单一功能点**描述生成单元测试，还是对**一批迭代代码**基于需求文档/测试用例生成单元测试？
>
> 选项：
> 1. **单一功能点** — 已有明确函数/方法名，按描述直接生成
> 2. **批量迭代** — 基于 PRD、需求文档、XMind 测试用例，分析变更范围后批量生成
> 3. **补充覆盖** — 对已有测试追加子测试或补充边界/异常场景

根据用户的回答决定后续流程：

| 用户选择 | 后续流程 | 输入来源 |
|----------|----------|----------|
| 单一功能点 | 跳过 Step -1（无需清单），直接进入 Step 0 | 用户提供的函数名/文件路径 |
| 批量迭代 | 执行 Step -1（目标方法清单编制），识别变更范围 | git diff / PRD / XMind / 测试用例 |
| 补充覆盖 | 读取现有 TestSpec + *_test.go，分析缺口 | 现有测试文件 |

```
Step -1: 目标方法清单编制

A. 识别覆盖范围（按优先级）：
   ① git diff 识别新增/修改文件中的顶层方法
   ② 新增文件中所有导出函数/方法
   ③ 用户指定的方法 / TestSpec deprecation 生效的方法
   ④ internal/apis/ 中关联的 API handler
   ⑤ services/svc*/ 中的接口定义及实现

B. 信息采集（对每个方法记录）：
   - 文件路径 + 行号
   - 函数签名（全路径：包.类型.方法名）
   - 类型归类：api_handler / svc_interface / svc_impl / dao / internal
   - 变更状态：new / modified / maintained
   - TestSpec 状态：has_spec / no_spec

C. 输出清单给用户确认：展示目标方法列表，询问是否完整

D. 确定覆盖顺序：interface → svc_impl → api_handler

Step 0: TestSpec 格式校验 — 检查必填字段，不完整则报错

Step 0.5: 逻辑澄清 + 可行路径分析

A. 通用模糊点提问（不得猜测）：
   当 TestSpec 缺失、函数签名不明确、state 数据流不清晰、
   DAO/表不确定、业务上下文缺失时，必须向用户提问。

B. 可行路径分析（涵盖所有执行分支）：
   逐条阅读源码，识别 9 类路径：
   ① 条件分支 (if/else/switch)
   ② 查询维度组合 (cond 字段)
   ③ 全空/缺省路径
   ④ 跨库/跨表路径 (dbutil.Teacher() + dbutil.Core())
   ⑤ 外部 API 调用 + 降级
   ⑥ 数据转换/计算 (评分策略、格式解析等)
   ⑦ 缓存路径 (命中/未命中/降级)
   ⑧ 异步/消息路径 (MQ/异步任务)
   ⑨ 错误降级路径 (fallback)

   只分析含源码实际处理的分支，不猜测未使用的字段。
   每条路径 → 一条 Assertion，用 question 向用户确认。

Step 1: 解析 TestSpec — 提取 Assertions / Complexity / Performance / TestData

Step 2: 幂等检查 — *_test.go 已存在则提示追加/覆盖

Step 3: 生成文件级标签字典注释（所有 type/priority/group 中文说明）

Step 4: 按 type 分章节排列：functional(P0→P3) → boundary → exception → performance

Step 5: 生成子测试，每个 t.Run 上方注释必含：
       - 场景: 业务场景描述
       - 说明: 断言逻辑描述
       - 查询维度: cond 维度说明（仅 List 类）
       - 数据流: given → when → then
       - 数据依赖: 需要前置的 DAO/表数据
       - flaky=true → for 循环重试 2 次
       - deps 非空 → 按依赖排序

Step 6: Benchmark — 仅 BenchmarkReq=true 且纯计算函数

Step 7: 生成 `~/Downloads/_test_spec.md` — 整合 YAML frontmatter + 标签字典 + 用例表 + 执行方式（追加到文件末尾，不覆盖已有内容）

Step 8: go vet ./path/to/package/

Step 9: go test -v -count=1 -timeout=30s

Step 10: 数据清理（可选）
```

---

## 生成代码结构约定

### 5.0 文件级测试数据域声明（必须 — 先查后声）

每个 `*_test.go` 文件顶部、`package` 声明之后、第一个 `import` 之前，**必须**包含测试数据域注释。

**生成流程**（三步）:

#### Step A: 数据库查询验证

Agent **必须先通过以下方式验证数据的实际存在性**，不得凭猜测填写：

1. **查现有测试文件**: 搜索项目中所有 `*_test.go`，提取常用的 `WithUin(n)`、`assignmentID`、`classID` 等值——这些是已知可用的预置数据
2. **查 DAO 方法**: 如果 testutils 已初始化，可通过 DAO 的 `GetByID` / `GetByCond` / `CountByCond` 查询值是否存在。示例：
   ```go
   // 验证 uin=271 是否在职
   emp, _ := account.NewEmployeeDao().GetByCond(ctx, &EmployeeCond{Uin: 271})
   // emp != nil → uin=271 存在
   ```
3. **查已有数据脚本**: 搜索 `script/test/` 目录下的 SQL 文件，确认哪些 ID 是预置种子数据

#### Step B: 分类标记

对每个使用的 ID/字段值标记置信度：

| 置信度 | 标记 | 说明 |
|--------|------|------|
| ✅ 已查证 | 不标记 | 通过 DAO 查询或现有测试确认存在 |
| ⚠️ 推断 | `(assumed)` | 从业务逻辑推断但未直接查询 |
| ❌ 不存在 | 不存在的值 | 通过 `CountByCond == 0` 确认不存在 |

#### Step C: 生成数据域注释

```go
// ==================== 测试数据域 ====================
// 本文件测试方法: AddStudent, EditStudent, DeleteStudent
// 验证方式: 查询 account.NewEmployeeDao.GetByCond + 参照 apps/account/services/svcstudent/student_test.go
//
// 【已存在数据（已通过 DAO 查询验证）】:
//   uin=8      : Employee 存在，companyID=1，SysRoleAdmin
//                (SELECT * FROM employee WHERE uin=8 → 1 row)
//   uin=271    : Employee 存在，SysRoleParent，已绑定 studentID=100
//                (SELECT * FROM parent_identity WHERE parent_uin=271 → 2 rows)
//   classID=301 : class 存在，grade=3
//                (SELECT * FROM class WHERE id=301 → 1 row)
//   academicYearID=1 : 当前学年
//                (参照 existing_test.go:16 `academicYearID=1` 多次使用)
//
// 【本测试创建的数据（事务后 Cleanup）】:
//   AddStudent 创建: studentID, userID, uinID → DeleteStudent 清理
//   BindParentIdentities 创建: parentIdentityIDs → DeleteParentIdentity 清理
//
// 【不存在的值（已通过 CountByCond=0 确认）】:
//   uin=99999  : Employee 表无此记录 (CountByCond → 0)
//   studentID=99999 : Student 表无此记录
//   phone="19900000000" : User 表无此手机号 (GetByCond.Phone → nil)
//
// 【定义域规则】:
//   functional  → 使用【已存在数据】+【本测试创建的数据】
//   boundary    → 使用【不存在的值】(uin=99999, studentID=0)
//   exception   → 使用【不存在的值】触发错误路径
//   cross-DB    → Teacher DB: classID=301; Account DB: uin=8
// =====================================================
```

**必须遵守的规则**:
1. `【已存在数据】`每条必须附带**验证证据**（DAO 查询结果 / 现有测试引用 / SQL 验证）
2. Agent 无法通过 DAO 查询时，至少**引用现有测试中已使用的同一个 ID**，并标记 `(参照 xxx_test.go:行号)`
3. 完全不确认的值**禁止**用于 functional 类型测试——只能用于 boundary/exception
4. 每个 ID 必须注明**所属 DB 连接**（Teacher/Core/Account）

### 5.1 文件级标签字典

### 5.1 文件级标签字典

每个 `TestXxx` 函数上方必须自动生成完整的中文标签字典注释：

```go
// TestCalculateScore 计算学生作业分数
//
// ==================== 标签字典 ====================
// type:functional    功能验证 — 正常路径，核心逻辑
// type:boundary      边界验证 — 极端值/空/最大/最小
// type:exception     异常验证 — 错误路径/panic/超时
// type:performance   性能验证 — 耗时/吞吐量基准
// priority:P0        阻塞门禁 — 失败阻断发布
// priority:P1        核心回归 — 每次 CI 必跑
// priority:P2        常规验证 — 全量回归时执行
// priority:P3        可选验证 — 手动触发时执行
// group:smoke        冒烟测试 — 快速验证核心流程
// group:regression   回归测试 — 完整功能回归
// group:full         全量测试 — 包含耗时/不稳定/边界
// flaky:true         不稳定测试 — 自动重试 2 次
// tolerance:Xms      耗时容忍 — 允许偏差范围
// ==================================================
func TestCalculateScore(t *testing.T) {
```

### 5.2 子测试注释模板（重要）

每个 `t.Run` 上方必须包含以下注释块：

```go
	// [functional][P0][smoke] AllCorrect
	//   场景: 学生提交的作业全部回答正确，验证正常计分支路
	//   说明: 全部正确 → score == FullMark(100)
	//   数据流: answers=allCorrect(10题全对), assignmentID=899
	//           → CalculateScore(ctx, 899, allCorrect)
	//           → score=100, err=nil
	//   数据依赖: AnswerKey(AssignmentID=899) 必须存在
	t.Run("AllCorrect[functional,P0,smoke]", func(t *testing.T) {
```

**对于 List 类函数**，额外包含 `查询维度` 行：

```go
	// [functional][P1][regression] ListByClassID
	//   场景: 按班级 ID 过滤学生列表，单维度查询
	//   查询维度: cond.ClassID
	//   数据流: cond={ClassID:301}
	//           → ListStudents(ctx, cond)
	//           → students.length > 0, err=nil
	//   数据依赖: teacher.students 表中 ClassID=301 的记录
	t.Run("ListByClassID[functional,P1,regression]", func(t *testing.T) {
```

### 5.3 子测试名编码约定

```
格式: <AssertionID>[type,priority,group,可选标签]

规则:
- tags 放在方括号 [] 内，逗号分隔，不含空格
- 每个子测试必须包含 type + priority + group 三标签
- tolerance / flaky 不在名称中编码，仅在 Go 注释中说明
- 方括号是名称的一部分，Go -run 支持正则匹配
```

**运行时过滤：**

```bash
go test -v -run '.*\[functional\].*'      # 按 type
go test -v -run '.*\[P0\].*'              # 按 priority
go test -v -run '.*\[.*smoke.*\].*'       # 按 group
go test -v -run '.*\[P0,.*smoke.*\].*'    # 组合过滤
```

### 5.4 分章节排列

Agent 生成的测试代码中，断言排列顺序固定为：

```
functional (P0 → P1 → P2 → P3) → boundary → exception → performance
```

同 type 内按 priority 从高到低排列。章节间用注释分隔线标注。

### 5.5 完整生成代码示例

```go
func TestCalculateScore(t *testing.T) {
	testutils.Initialize(testutils.AppNameTeacher)
	defer testutils.Close()
	ctx := testutils.NewCtx(testutils.WithUin(271))

	// ============================================
	// functional — 功能验证，正常路径
	// ============================================

	// [functional][P0][smoke] AllCorrect
	//   场景: 学生提交的作业全部回答正确，验证正常计分支路
	//   说明: 全部正确 → score == FullMark(100)
	//   数据流: answers=allCorrect(10题全对), assignmentID=899
	//           → CalculateScore(ctx, 899, allCorrect)
	//           → score=100, err=nil
	//   数据依赖: AnswerKey(AssignmentID=899) 必须存在
	t.Run("AllCorrect[functional,P0,smoke]", func(t *testing.T) {
		answers := allCorrectAnswers()
		score, err := CalculateScore(ctx, 899, answers)
		assert.Nil(t, err)
		assert.Equal(t, 100, score)
	})

	// [functional][P0][smoke] PartialCorrect
	//   场景: 学生提交的作业部分正确，验证按比例算分的分支
	//   说明: 6/10 正确 → score(60) == FullMark * (6/10)
	//   数据流: answers=6correct4wrong, assignmentID=899
	//           → CalculateScore(ctx, 899, 6correct4wrong)
	//           → score=60, err=nil
	t.Run("PartialCorrect[functional,P0,smoke]", func(t *testing.T) {
		answers := partialCorrectAnswers()
		score, err := CalculateScore(ctx, 899, answers)
		assert.Nil(t, err)
		assert.Equal(t, 60, score)
	})

	// ============================================
	// boundary — 边界验证
	// ============================================

	// [boundary][P1][regression] EmptySubmit
	//   场景: 学生提交空答案，验证空输入边界处理
	//   说明: 空提交 → score == 0, no error
	//   数据流: answers=[] (空 slice), assignmentID=899
	//           → CalculateScore(ctx, 899, [])
	//           → score=0, err=nil
	t.Run("EmptySubmit[boundary,P1,regression]", func(t *testing.T) {
		score, err := CalculateScore(ctx, 899, nil)
		assert.Nil(t, err)
		assert.Equal(t, 0, score)
	})

	// ============================================
	// exception — 异常验证
	// ============================================

	// [exception][P1][regression] MissingKey
	//   场景: 作业未配置答案 key 或关联的 assignment 已删除
	//   说明: 缺少答案 key → error = ErrAnswerKeyNotFound
	//   依赖: AllCorrect（顺序执行，确保 assignment 数据已就绪）
	//   数据流: assignmentID=99999(不存在的ID)
	//           → CalculateScore(ctx, 99999, anyAnswers)
	//           → err=ErrAnswerKeyNotFound
	t.Run("MissingKey[exception,P1,regression]", func(t *testing.T) {
		score, err := CalculateScore(ctx, 99999, anyAnswers)
		assert.Error(t, err)
		assert.ErrorIs(t, err, ErrAnswerKeyNotFound)
		assert.Equal(t, 0, score)
	})

	// [exception][P2][full][flaky] Timeout
	//   场景: 海量题目(1000题)同时提交，触发超时门限
	//   说明: 大量数据超时 → context.DeadlineExceeded
	//   容忍度: 100ms 偏差
	//   数据流: answers=largeSet(1000), assignmentID=899
	//           → CalculateScore(ctx, 899, largeSet)
	//           → err=DeadlineExceeded
	t.Run("Timeout[exception,P2,full,flaky]", func(t *testing.T) {
		if testing.Short() {
			t.Skip("skipping time-sensitive test in short mode")
		}
		for i := 0; i < 2; i++ {
			answers := generateLargeSet(1000)
			_, err := CalculateScore(ctx, 899, answers)
			if err == context.DeadlineExceeded {
				return
			}
		}
		t.Error("expected DeadlineExceeded but never occurred")
	})
}
```

### 5.6 多维度 Cond 查询测试代码示例

```go
func TestListStudents(t *testing.T) {
	testutils.Initialize(testutils.AppNameTeacher)
	defer testutils.Close()
	ctx := testutils.NewCtx(testutils.WithUin(8))

	// =======================================================
	// functional — 功能验证，正常路径
	// =======================================================

	// [functional][P1][regression] ListByClassID
	//   场景: 按班级 ID 过滤学生列表，单维度 teacher DB 单表查询
	//   查询维度: cond.ClassID
	//   数据流: cond={ClassID:301}
	//           → ListStudents(ctx, cond)
	//           → students.length > 0, err=nil
	//   数据依赖: teacher.students 表中 ClassID=301 的记录
	t.Run("ListByClassID[functional,P1,regression]", func(t *testing.T) {
		cond := &StudentCond{ClassID: ptrToUint(301)}
		res, err := ListStudents(ctx, cond)
		assert.Nil(t, err)
		assert.Greater(t, len(res.Students), 0)
	})

	// [functional][P1][regression] ListByClassAndStatus
	//   场景: 班级+状态组合过滤，验证复合条件索引路径
	//   查询维度: cond.ClassID + cond.Status（复合条件）
	//   数据流: cond={ClassID:301, Status:"active"}
	//           → ListStudents(ctx, cond)
	//           → students[0].Status=="active", err=nil
	//   数据依赖: teacher.students 表中 ClassID=301 且 Status="active" 的记录
	t.Run("ListByClassAndStatus[functional,P1,regression]", func(t *testing.T) {
		cond := &StudentCond{ClassID: ptrToUint(301), Status: ptrToString("active")}
		res, err := ListStudents(ctx, cond)
		assert.Nil(t, err)
		for _, s := range res.Students {
			assert.Equal(t, "active", s.Status)
		}
	})

	// [functional][P2][regression] ListWithUserInfo
	//   场景: 查询学生信息附带账号信息，跨 teacher DB + account DB
	//   查询维度: cond.ClassID + cond.IncludeUserInfo（跨库路径）
	//   数据流: cond={ClassID:301, IncludeUserInfo:true}
	//           → ListStudents(ctx, cond)
	//           → students[0].Phone!="", err=nil
	//   数据依赖: teacher.students + account.users 均有对应数据
	t.Run("ListWithUserInfo[functional,P2,regression]", func(t *testing.T) {
		cond := &StudentCond{ClassID: ptrToUint(301), IncludeUserInfo: ptrToBool(true)}
		res, err := ListStudents(ctx, cond)
		assert.Nil(t, err)
		assert.NotEmpty(t, res.Students[0].Phone)
	})

	// =======================================================
	// boundary — 边界验证
	// =======================================================

	// [boundary][P1][regression] ListAllNoCond
	//   场景: 不传任何条件，走默认分页路径
	//   查询维度: cond=空（全量路径）
	//   数据流: cond={}
	//           → ListStudents(ctx, StudentCond{})
	//           → total>0, err=nil
	t.Run("ListAllNoCond[boundary,P1,regression]", func(t *testing.T) {
		res, err := ListStudents(ctx, &StudentCond{})
		assert.Nil(t, err)
		assert.Greater(t, res.Total, 0)
	})

	// [boundary][P1][regression] ListNoMatch
	//   场景: 条件查无结果，验证空结果集处理
	//   查询维度: cond.ClassID（无匹配值）
	//   数据流: cond={ClassID:99999}
	//           → ListStudents(ctx, cond)
	//           → students=[], total=0, err=nil
	t.Run("ListNoMatch[boundary,P1,regression]", func(t *testing.T) {
		cond := &StudentCond{ClassID: ptrToUint(99999)}
		res, err := ListStudents(ctx, cond)
		assert.Nil(t, err)
		assert.Equal(t, 0, len(res.Students))
	})
}
```

---

## `~/Downloads/_test_spec.md` 整合文档格式

将所有测试的 TestSpec 整合追加到 `~/Downloads/_test_spec.md`，不生成 `_test.md` 到代码仓库。每个测试函数追加一个章节：

```markdown
---
TestSpec:
  Function: CalculateScore
  Version: v2.1.0
  Workflow: assignment-scoring
  TestLevel: integration
  Tags: [db, slow]
  ...
---

# 单元测试文档: <包>.<函数>

## 元数据

| 属性 | 值 |
|------|-----|
| 版本 | v2.1.0 |
| 工作流 | assignment-scoring |
| 测试级别 | integration |
| 被测函数 | `CalculateScore(ctx, assignmentID, answers)` |
| 预期单次耗时 | 50ms |

## 标签字典

| 标签 | 说明 |
|------|------|
| type:functional | 功能验证 — 正常路径，核心逻辑 |
| type:boundary | 边界验证 — 极端值/空/最大/最小 |
| type:exception | 异常验证 — 错误路径/panic/超时 |
| priority:P0 | 阻塞门禁 — 失败阻断发布 |
| priority:P1 | 核心回归 — 每次 CI 必跑 |
| priority:P2 | 常规验证 — 全量回归时执行 |
| priority:P3 | 可选验证 — 手动触发时执行 |
| group:smoke | 冒烟测试 — 快速验证核心流程 |
| group:regression | 回归测试 — 完整功能回归 |
| group:full | 全量测试 — 包含耗时/不稳定/边界 |
| flaky:true | 不稳定测试 — 自动重试 2 次 |
| tolerance:Xms | 耗时容忍 — 允许偏差范围 |

## 测试用例

| ID | 场景描述 | type | priority | group | flaky | 数据流 | 预期 |
|----|----------|------|----------|-------|-------|--------|------|
| AllCorrect | 学生全部回答正确 → 正常计分 | functional | P0 | smoke | false | allCorrect → CalculateScore | score=100 |
| PartialCorrect | 学生部分回答正确 → 按比例算分 | functional | P0 | smoke | false | 6correct4wrong → Calc | score=60 |
| EmptySubmit | 学生提交空答案 → 边界处理 | boundary | P1 | regression | false | [] → Calc | score=0 |
| MissingKey | 作业无答案 key → 异常分支 | exception | P1 | regression | false | id=99999 → Calc | error |

## 前置数据

| 实体 | 创建方式 | 字段 | 清理 |
|------|----------|------|------|
| AnswerKey | AnswerKeyDao.Create | AssignmentID=899 | DeleteByIDs |
| StudentAssignment | StudentAssignmentDao.Create | Uin=271, AssignmentID=899 | DeleteByIDs |

## 执行方式

```bash
# 全部测试
go test -v -count=1 -run TestCalculateScore ./path/to/pkg/

# 按 type
go test -v -run 'TestCalculateScore/.*\[functional\].*' ./path/to/pkg/

# 按 priority
go test -v -run 'TestCalculateScore/.*\[P0\].*' ./path/to/pkg/

# 按 group
go test -v -run 'TestCalculateScore/.*\[.*smoke.*\].*' ./path/to/pkg/

# 组合（P0 + smoke）
go test -v -run 'TestCalculateScore/.*\[P0,.*smoke.*\].*' ./path/to/pkg/
```

## 测试结果

> 执行后填写

| 总用例 | 通过 | 失败 | 跳过 |
|--------|------|------|------|
| — | — | — | — |

备注：
```

---

## Agent B 分析流程

Agent B 负责读取 `go test -v` 输出并对照 TestSpec 定位失败：

```
Step 1: 读取 `~/Downloads/_test_spec.md` 中对应章节的 TestSpec（获取断言列表）
Step 2: 执行 go test -v -count=1 -timeout=30s，捕获输出
Step 3: 解析输出（=== RUN / --- PASS / --- FAIL / file:line）
Step 4: 将 FAIL 的子测试名与 TestSpec.Assertions[].id 匹配
Step 5: 输出分析报告：
        - 失败断言 id + type + priority + group
        - 对应代码行号（来自 go test stack trace）
        - 失败原因分析（given → when → then 哪一步出错）
        - 修复建议
```

**Agent B 不做**：猜测代码行号、修改代码。

---

## 注意事项

1. **`Initialize` 内部 `sync.Once`** — 同一测试文件中只能初始化一次，多个测试函数共享 `Initialize`/`Close` 调用。
2. **`WithUin` 的 uin 必须在测试 DB 中真实存在** — 使用前确认对应账号在测试库中有数据。
3. **Integration 测试需要真实 DB/Redis 连接** — 确保配置文件路径正确，测试环境可访问。
4. **不引入 mock 框架** — 使用 real DAO + `testutils`，保持与项目现有测试风格一致。
5. **子测试名编码** — `[]` 需正确配对，逗号分隔，不含空格。格式严格为 `<id>[type,priority,group]`。
6. **`assert` 而非 `require`** — 不使用 `require` 避免跳过掩盖后续错误，不使用 `suite`。
7. **非导出函数** — 仅在 `internal` 包中通过导出的 `TestXxx` 间接覆盖，不直接为私有函数生成 `_test.go`。
8. **TestMain 统一初始化（关键性能优化）** — 若一个包有多个 `TestXxx` 函数，**必须**将 `Initialize`/`Close` 放到 `TestMain` 中统一管理。实例：

    ```go
    func TestMain(m *testing.M) {
        testutils.Initialize(testutils.AppNameAccount)
        code := m.Run()
        testutils.Close()
        os.Exit(code)
    }
    ```
    
    不要在单个 `TestXxx` 中重复调用 `Initialize`/`Close`。`Initialize` 每次调用都会重新打开数据库连接（core/account/teacher 共 3 个 DB），单个包中 3 个 Test 函数就会打开 9 次连接，浪费约 20 秒。`TestMain` 只在进程启动时打开一次，所有子测试共享。
    
    附加说明：
    - `testutils.Initialize` 内部用 `sync.Once` 保证 `initializer` 实例只创建一次，但 `initializer.Initialize()` 在 `sync.Once` 块**外部**执行，故每次直接调用 `Initialize` 都会重复打开 DB 连接。
    - `Close()` 是幂等的，`TestMain` 中仅需调用一次。
    - 对于有 `Email` 等需要在多层校验/去重函数中使用的字段，确保传值一致（如 `AddTeacher` 的 `existTeacherListPhoneOrEmail` 会在 `email=""` 时生成 `WHERE OR email = ''` 误匹配所有空邮箱用户，必须传随机 <email>）。
9. **Benchmark 只针对纯计算函数** — 有 DB 依赖的函数不生成 Benchmark，由 TestSpec 的 `BenchmarkReq` 控制。
10. **测试文档不放入代码仓库** — 所有测试的 TestSpec 整合追加到 `~/Downloads/_test_spec.md`，不在代码仓库中生成 `_test.md` 文件。`_test.go` 注释中引用标记指向 `~/Downloads/_test_spec.md`。

---

## 错误处理

| 错误场景 | 处理方式 |
|----------|----------|
| TestSpec 缺失或格式不完整 | 报错并提示缺失的必填字段，要求用户补充后再执行 |
| 函数签名与 TestSpec 不匹配 | 报错并对比差异，要求用户更正 |
| `*_test.go` 已存在 | 提示追加还是覆盖，由用户选择；追加时合并新 Assertion，去重 id |
| `go vet` 失败 | 列出错误详情，修复源码后重试 |
| `go test` 失败 | 执行 Agent B 分析流程，输出失败报告 |
| TestData 中 DAO 不存在 | 报错并要求用户确认正确的 DAO 路径 |
| `testutils.Initialize` 两次调用 | 不报错（`sync.Once` 安全），但应提醒检查是否有冗余 |
| flaky 测试不稳定 | 在 Go 注释中标记 `[flaky]`，代码中用 for 循环重试 2 次 |
| `WithUin` 的 uin 在测试库不存在 | 提示用户确认 uin 值或准备对应测试数据 |
