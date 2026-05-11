---
name: reviewcode
description: 对代码进行规范审查，按语言代码块分别分析。当前支持 Go 规则 review；其他语言后续补充。当用户要求 review 代码、检查代码规范时使用。
---

# ReviewCode — 代码 Review 技能

对用户提供（或 Agent 生成）的代码进行规范审查，按语言代码块分别分析。当前仅定义 **Go** 规则；其他语言后续补充。

---

## 触发条件

当用户要求 review 代码、检查代码规范、或在代码提交 / PR 创建前需要自动审查时使用本技能。

---

## Go Review 规则

按严重程度分为 **Error**（必须修复）、**Warning**（建议修复）、**Info**（提示）。

### G-01 类型与常量定义 [Error]

- **枚举类型**必须定义**别名类型**（`type Status string` / `type Role int` 等），禁止直接使用底层原始类型（`string`、`int`）作为业务枚举值传播。
- **常量**必须用 `const` 或枚举 `iota` 定义，禁止在代码中出现硬编码魔法值（如 `status == "normal"`、`role == 2`）；常量须有业务含义注释。

### G-02 导出符号注释与命名 [Error]

- **导出函数、方法、变量、结构体、字段**的注释必须以**自身名字签名开头**（`// Foo does ...`），符合 `go doc` 规范。
- 注释只写业务含义、数据来源与约定；禁止写入对话式用语、协作聊天才出现的提法或与实现无关的「关键词」。
- **导出符号命名禁止以包名作为前缀**：调用方已通过 import 别名获得包名上下文，符号名再重复包名会导致 `pkg.PkgFoo` 形式的冗余。例如 `openai` 包内 `OpenAIClient` → `Client`；`llm` 包内 `LLMClient` → `Client`。同样适用于内部函数（如 `newOpenAIFactory` → `newFactory`）。此规则不适用于业务实体名恰好与包名同词但含义不同的情况（如 `model` 包内 `PromptCond`，`Prompt` 是业务词而非包名）。

### G-02a 注释完整性与表达规范 [Error]

- **注释必须是完整、自解释的陈述句**，禁止出现以下不合规形式：
  - **括号补充式**：如 `息（仅Go层使用，不序列化）`、`状态（正常/异常）`，括号内容应直接融入正文或另起一行完整描述。
  - **片段式/残句**：如 `仅Go层使用`、`不序列化` 缺乏完整语境，读者无法独立理解其含义与边界。
  - **混合技术术语无解释**：在业务注释中混入实现层术语（如 `Go层`）却不说明其来源、用途或边界，导致跨角色阅读困难。
  - **省略号/未完结式**：如 `用于...`、`处理...` 等，需补足具体动词与对象（如 `用于存储用户 Prompt 版本历史`）。
- **正确做法示例**：
  - `// PromptVersion 用于存储用户 Prompt 的版本迭代历史，仅在 Go 服务层内流转，不对外序列化到 HTTP 响应或持久化存储。`
  - 如需强调某一边界或约定，以完整句子形式写明：`// 该字段仅在 Go 服务层内部使用，禁止在 API 响应中序列化输出。`
- **非导出符号（私有字段/方法）**同样须遵循完整表达规范；可省略签名开头，但不得出现上述不合规形式。

### G-03 禁止循环内逐条 SQL [Error]

- 禁止在 `for` 循环内对列表每一项单独执行 insert / delete / update / select 等 GORM 操作（N+1 问题）。
- **正确做法**：批量查询到内存，构建 O(1) 查询的 `map`（使用 `pkgs/utils.ToMap`），在需要相关属性的地方以 `id->obj` 填充，如 `ClassName: classMap[obj.ClassID].Name`。
- 除非需求或评审明确允许逐条查询，否则一律改为批量 + map 组装；确需逐条时须在代码注释中注明原因。

### G-04 DAO 查询与软删 [Error]

- 软删模型（嵌 `gorm.Model` 含 `DeletedAt`）的查询**必须用 `Model(&Entity{})` 起链**，让 GORM 自动加 `deleted_at IS NULL`；禁止仅用 `.Table(tablename)` 导致软删过滤缺失。
- 需要命中已删行时使用 `Unscoped()` 或 `BaseCond.IsDelete`。
- DAO 层禁止用 `Raw` / `Exec` 拼整段 SQL 做常规 CRUD。

### G-05 DAO 方法必备清单与命名 [Error]

- 新建/对齐 DAO 以 `apps/dotteacher/models/teacher/question.go` 为模板：`NewXxxDao`、`TableName`、`DB`、`WithTx`、`Create`、`CreateBatch`、`GetByID`、`GetByIDs`、`UpdateByID`、`UpdateMap`、`UpdateMapBatch`、`SaveBatchOnConflict`、`Delete`、`DeleteByIDs`、`GetByCond`、`GetListByCond`、`GetPageListByCond`、`CountByCond`、`BuildCondition`。
- 条件列表命名统一 **`GetListByCond`**，禁止 `ListByCond`；需要 `[]*Entity` 时在调用方用 **`pkgs/utils.SliceElemsToPtrs`**。
- 事务内操作通过 **`WithTx(tx *gorm.DB)`** 返回新 DAO 实例，在事务内调用 `DeleteByIDs` 等方法，**禁止**在方法名中加 `InTx` 后缀（如 `DeleteByIDsInTx`）；也禁止用 `HardDelete` 表示软删。

### G-06 结构体注释与 gorm.Model [Error]

- 所有结构体须有符合 `go doc` 的注释。
- 新建映射本库表的实体必须**嵌入 `gorm.Model`**（含 `ID`、`CreatedAt`、`UpdatedAt`、`DeletedAt`），禁止手写等价基础字段及重复 tag；若表不使用软删等而偏离约定，须在注释中说明原因并经评审确认。

### G-07 svc 参数与返回约定 [Error]

- **svc 入口**（由 HTTP 调用）第一参数 `*gin.Context`；DAO、可复用内部函数用 `context.Context`。
- `internal/apis` 调 svc 时**只传** `*gin.Context` 与 `req`（及最少扩展参数），**不要**在 apis 层取 `runtime.CompanyID` 等再当独立参数传入；svc 内用 `runtime.xxx(c)` 取。
- **svc 返回值**：`err == nil` 时 `res` 不得为 `nil`；DAO 失败 `return nil, err`，禁止在 svc 内造带 HTTP 码的自定义 `error` 类型。

### G-08 依赖方向 [Error]

- `internal/apis` → `services/svc*` → `models` / `pkgs`。**禁止** `models` 依赖 `apis` 或 `services`。
- **禁止**把仅单 app 使用的逻辑塞进 `pkgs/` 造成循环依赖风险。

### G-09 internal 目录限制 [Error]

- **Web 类项目**（含 `apps/<APP>/internal/` 结构）：`internal/` **只允许** `apis/`、`dto/`、`docs/`、`migrate/`；禁止新增与上述同级的业务包。额外注册/解析等放在 `services/<包名>/`。
- **工具库项目**（如 `yg-go` 等不含 `apps/<APP>/internal/` 结构的项目）：**不限制**包目录结构，但仍需遵守 G-08 依赖方向规则。

### G-09a 包名与变量名语义清晰性 [Error]

- 包名须以**业务含义命名**（如 `prompt`、`llm`、`storage`），禁止使用模糊或过于通用的命名（如 `common`、`helper`、`util`、`misc`）。
- 导出变量、函数、类型名须语义明确，一眼可辨识其用途；禁止仅用缩写或首字母缩略（如 `Pv` → `PromptVersion`、`Rt` → `Runtime`），除非缩写是业界公认惯例（如 `HTTP`、`SQL`、`JSON`、`DAO`）。
- 非导出变量同样须语义清晰，禁止用 `x`、`y`、`tmp`、`data` 等无含义命名。

### G-10 默认实现范围与降级路径日志 [Warning]

- 默认只按当前需求与已确认约定实现；禁止未经用户明确书面要求自行加入：实现退化/降级路径、额外的空值/历史兼容分支。
- **若因非预期空值或降级处理进入默认分支，必须打印明显警告日志**（如 `logs.WarnContextf` 或 `logs.ErrorContextf`），明确说明降级原因、当前处理路径及影响。禁止静默降级导致后续排查困难。

### G-11 模糊查询在 SQL 层 [Error]

- 姓名、班级名等模糊匹配应在 DAO/SQL 层使用 `LIKE`；禁止用 `strings.Contains` 拉全量再在内存匹配（不利于分页与索引）。

### G-12 空容器默认值 [Info]

- map/slice 声明时给出默认空值：`m := map[K]V{}` / `s := make([]T, 0)`，避免仅为补零值的 else 分支。

### G-13 生成物禁止手改 [Error]

- `apps/<APP>/internal/docs/*_docs.go` 等 swag 生成物禁止手改；改 DTO/handler 注解后执行 `make generate-docs APP=<APP>`。

### G-14 提交范围与分支安全 [Error]

- `vendor/` 下的修改禁止提交；提交前须检查 `git status` 排除 vendor 变更。
- **严禁向以下分支直接推送或提交代码**：
  - `main` / `master`（主干分支）
  - `feature/*`（如 `feature/2.6`、`feature-2.0` 等）
  - `release/*`（如 `release-2.4`、`dot-release-2.5` 等）
  - `dot-release-*`（版本发布分支）
  - 所有带 `release` 或 `feature` 关键词的长期维护分支
- 所有代码变更必须：
  1. 从目标分支切出独立的开发分支（如 `fix/xxx`、`feat/xxx`）
  2. 在开发分支上完成开发、编译、测试
  3. 创建 MR/PR 合入目标分支
- **切分支命名规范**：
  - 修复问题：`fix/<issue-desc>`（如 `fix/dao-soft-delete-filter`）
  - 新功能：`feat/<feature-desc>`
  - 改进重构：`refactor/<refactor-desc>`
- Review 前须检查：
  1. 当前分支是否为禁止直推的分支，如果是则拒绝并提示切出开发分支
  2. 当前开发分支是从哪个分支切出的（`git merge-base`），确认基线的正确性
  3. 是否已创建对应的 MR/PR（`glab mr list` 或 `gh pr list`），如未创建则提醒用户
  4. MR/PR 当前状态（open / merged / closed），已 merged 的分支不应再有新提交
- **直推请求拒绝**：用户要求向禁止分支直推时，必须拒绝并提醒风险，建议切出开发分支后通过 MR/PR 合入

### G-20 编译与校验 [Error]

- **工作区根目录**：执行终端命令前须在包含 `go.mod` 的模块根目录。
- **合法校验命令**：
  - 编译：`make local` 或 `make local APP=<APP>`（按改动涉及的 APP 分别编译）
  - 文档生成：`make generate-docs` 或 `make generate-docs APP=<APP>`（改 DTO/handler 注解后必须执行）
  - **禁止使用** `go build ./...`、`go run xxx.go` 等非 Makefile 约定命令，除非用户明确要求
- **校验时机**：
  - 新增/修改代码后提交前，必须运行 `make local` 验证编译通过
  - 修改 DTO 或 handler 注解后，必须运行 `make generate-docs` 重新生成文档
  - 受影响的所有 APP 都需分别编译验证（如改了 `dotteacher`，需 `make local APP=dotteacher`）
- **生成物禁止手改**：`apps/<APP>/internal/docs/*_docs.go` 等 swag 生成物禁止手改；改 DTO/handler 注解后执行 `make generate-docs APP=<APP>`

### G-15 物理表名与 Go 命名 [Info]

- 数据库表名字符串可保留 `dot_` 前缀；Go 类型名、表名常量标识符**不带 `Dot` 前缀**（`KnowledgeClass`、`TableNameKnowledgeClass` 而非 `DotKnowledgeClass`）。

### G-16 Find 零行判断 [Warning]

- DAO `GetByID` 等使用 `Find` 返回时，调用方应以 **`.ID != 0`** 判断记录是否命中，而非 `!= nil`（`Find` 对零行返回非 nil 指针指向零值结构体）。

### G-17 独立子服务不可依赖需初始化的全局配置 [Error]

- **独立子服务（如 `dotworker`）禁止引用需在主服务（如 `dotteacher`）初始化的全局配置变量（如 `algo.GlobalAlgoConfig`）**。这会导致子服务无法独立运行、启动时 panic 或配置缺失。
- **正确做法**：将需要的配置值存入任务 `payload`（如 `VariantGenerationTaskPayload.GenInterfaceURL` / `GenInterfaceAuth`），由主服务在构建 payload 时注入；子服务只从 payload 中读取，保证与主服务解耦、可独立测试。
- 适用于所有基于任务队列解耦的架构：主服务负责配置加载与 payload 构建；Worker / Consumer 只消费 payload、不依赖主服务的运行时状态。
- **补充要求**：**Worker 消费 payload 时必须校验关键字段的非空性，并在为空时打印明显警告日志**（如 `logs.WarnContextf` 或 `logs.ErrorContextf`），避免静默降级导致生成任务失败却不知原因。例如 `if payload.GenInterfaceURL == "" { logs.WarnContextf(ctx, "[processor] GenInterfaceURL empty, cannot call external API") }`。

### G-18 main.go 与 init.go 初始化规范 [Error]

- **`main.go` 与 `init.go` 是应用启动入口，任何改动必须经过用户确认后方可提交**。
- 禁止在未经用户明确书面要求的情况下，在 `main.go` 或 `init.go` 中新增：
  - 数据库表迁移（`DoInitModels`、`DoInitModelsWithDB`、`AutoMigrate`）
  - 第三方服务初始化（LLM provider register、外部 SDK init）
  - 全局配置加载或注入
  - 新的 import 语句引用外部包
- **初始化顺序**：
  1. 配置加载（`config.LoadCoreConfig`）
  2. 数据库连接（`dbtools.InitMutilMySQL`）
  3. 缓存/Redis 初始化
  4. 业务模型迁移（`DoInitModels`）——仅限用户明确要求添加的模块
  5. HTTP 服务启动
- **新增模块初始化流程**：
  - 先在对应模块内实现 `InitDB()` 函数（遵循 G-05 DAO 规范）
  - 向用户确认是否需要在 `main.go` / `init.go` 中调用
  - 用户确认后再添加到 `DoInitModels` 列表或 `DoInitModelsWithDB` 参数
- **禁止静默添加**：任何对启动入口文件的改动，必须在代码生成前向用户提问确认：「是否需要在 main.go/init.go 中初始化该模块？」

### G-19 新增函数复杂度与性能评估 [Warning]

- **新增函数须进行复杂度评估**，包含以下指标：
  - **时间复杂度**：O(n)、O(n²)、O(log n) 等，标注 n 的具体含义（如 `n = len(items)`）
  - **空间复杂度**：O(n)、O(1) 等，标注额外内存开销来源（如临时 map、slice）
  - **三指标评价**：
    - **最好情况**（Best Case）：如空输入、命中缓存等
    - **最坏情况**（Worst Case）：如全量遍历、所有分支命中等
    - **平均情况**（Average Case）：典型业务场景下预期表现
- **性能瓶颈识别**：
  - 标注函数内可能的瓶颈点（如循环内 SQL、大内存分配、阻塞 I/O）
  - 瓶颈点须给出具体优化建议（如改为批量查询、流式处理、异步化）
- **内存可优化设计**：
  - 评估内存分配是否可优化（如预分配 slice 容量 `make([]T, 0, cap)`）
  - 评估是否可用指针减少拷贝开销（如 `[]*T` vs `[]T`）
  - 评估是否有不必要的全局变量或闭包捕获
- **评估输出格式**：
  ```
  ### [函数名] `func Foo(ctx, items []T) ([]Result, error)`
  
  | 指标 | 值 | 说明 |
  |------|-----|------|
  | 时间复杂度 | O(n) | n = len(items)，单次遍历 |
  | 空间复杂度 | O(n) | 结果 slice + 临时 map |
  | 最好情况 | O(1) | items 为空时直接返回 |
  | 最坏情况 | O(n) | 全量遍历 + map 构建 |
  | 平均情况 | O(n) | 业务场景下 items 长度约 100 |
  
  **性能瓶颈**：循环内 `dao.GetByID(ctx, id)` → 改为批量 `GetByIDs`
  **内存优化**：`make([]Result, 0, len(items))` 预分配容量
  ```
- **适用范围**：仅评估**新增函数**或**改动较大的函数**；小改动（如日志、注释）无需评估。

---

## Review 输出格式

对每个代码块按以下格式输出：

```
### [语言] 文件: `path/to/file.go`

| 规则 | 严重度 | 行号 | 当前代码 | 改进建议 |
|------|--------|------|----------|----------|
| G-03 | Error  | 42   | `for ... { dao.GetByID(ctx, id) }` | 批量 `GetByIDs` + `utils.ToMap` |
```

1. 仅报告**违反规则的项**，不重复合规代码。
2. 对同一文件同类违规合并为一条（附带所有行号）。
3. 最后给出 **修复摘要**（按 Error > Warning > Info 优先级排序，列出需改动文件与核心改动点）。

---

## 其他语言（待补充）

- **Python**：TODO
- **TypeScript/JavaScript**：TODO
- **SQL 脚本**：TODO