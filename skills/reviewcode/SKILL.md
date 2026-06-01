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

### G-03a 禁止多层嵌套 if-and-else 链式降级 [Error]

- 禁止将 3 层及以上的 `if { if { if { ... } } }` 嵌套用于链式降级（如"获取ID → 获取URL → HTTP请求 → 读取body → 计算页数"），每层只在成功时继续、失败时静默跳过。
- **正确做法**：将链式操作封装为独立的 **返回 `(result, error)` 的函数**，每一步失败直接 `return nil, fmt.Errorf(...)`，调用方只需一次 `if err != nil` 即可处理降级。例如：
  ```go
  // 错误：4层嵌套 else
  dividerPage := false
  if req.AppendBlankPage.Value() {
      pt, err := dao.GetByID(ctx, id)
      if err == nil && pt.PDFID != 0 {
          url, err := GetFilePublicURL(pt.PDFID)
          if err == nil {
              resp, err := http.Get(url)
              if err == nil && resp.StatusCode == 200 {
                  // ...继续嵌套
              }
          }
      }
  }

  // 正确：封装函数 + 一行调用
  info, err := GetPDFInfo(pubURL)  // 函数内部每步失败直接 return nil, err
  if err != nil {
      logs.WarnContextf(ctx, "[xxx] GetPDFInfo failed, err: %v", err)
  } else if info.PageCount%2 == 1 {
      dividerPage = true
  }
  ```
- 依赖前置查询（如先查 PaperTest 再取 PDFID 再取 URL）时，前置查询应在调用方完成，将最终 URL 传给通用函数，而非在通用函数内耦合业务逻辑。
- **优先否定条件提前 return，减少 else 嵌套**：当条件为"前置步骤失败则流程无法继续"时，应使用 `if err != nil { return }` 提前退出，而非 `if err == nil { ... } else { ... }` 包裹后续逻辑。这样后续代码始终在"成功路径"上执行，无需层层 else。例如：
  ```go
  // 错误：正向条件嵌套 else
  if id != 0 {
      url, err := GetFilePublicURL(id)
      if err == nil {
          // ...继续
      } else {
          logs.Warn(...)
      }
  }

  // 正确：否定条件提前 return
  if id == 0 {
      logs.ErrorContextf(ctx, "[xxx] id is 0")
      res.Code = errcode.ErrCode_InternalError
      res.Message = "获取失败"
      return res, nil
  }
  url, err := GetFilePublicURL(id)
  if err != nil {
      res.Code = errcode.ErrCode_InternalError
      res.Message = "获取URL失败"
      return res, nil
  }
  // ...后续代码无需 else
  ```
- 当前置步骤属于可选逻辑（获取失败不影响主流程，仅改变某个布尔值）时，仍应避免多层 else 嵌套，改用单层 `if` + 降级日志 + 默认值，而非 `else` 链。

### G-03b 重复逻辑须通过 bool 聚合复用通用方法 [Error]

- **禁止**对同一资源（如同一 PaperTest、同一 PDF 文件）在同一函数内发起多次独立查询或操作，仅因触发条件不同（如"缓存缺失"与"NeedPdfImages"）就各自写一段相似逻辑。
- **正确做法**：用 `bool` 变量聚合所有触发条件，统一判断是否需要执行通用操作，只调用一次通用方法。例如：
  ```go
  // 错误：两段独立逻辑，各自调用 SplitPDFToImages
  if blankMeta.BlankPDFID == 0 {
      urls, _, err := SplitPDFToImages(ctx, pdfURL)
      // ...回填逻辑
  }
  if req.NeedPdfImages.Value() {
      urls, _, err := SplitPDFToImages(ctx, pdfURL)  // 重复调用
      res.ImageIDs = uploadAndGetIDs(urls)
  }

  // 正确：bool 聚合，一次调用
  needSplit := req.NeedPdfImages.Value() ||
      (pt != nil && (pt.PaperResultMeta.BlankPDFID == 0 || len(pt.PaperResultMeta.BlankImagesIDs) == 0))
  if needSplit {
      imageUrls, pageCount, err := SplitPDFToImages(ctx, pdfURL)
      imageIDs, err := UploadImageURLsToFiles(ctx, imageUrls, uin, companyID)
      // 按需分别填充各自目标
      if req.NeedPdfImages.Value() {
          res.ImageIDs = imageIDs
      }
      if pt.PaperResultMeta.BlankPDFID == 0 {
          // 回填 meta
      }
  }
  ```
- **识别信号**：同一函数内出现两处以上对同一外部服务（HTTP、DAO、存储）的调用，且调用参数相同或高度相似——这是需要提取通用方法并用 bool 聚合的强信号。
- **适用范围**：不限于 PDF 拆图，同样适用于任何"多个条件触发同一操作"的场景（如多处触发同一 DAO 查询、多处上传同一文件等）。

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

### G-21 错误返回前必须写日志 [Error]

- `return nil, fmt.Errorf(...)` 返回前必须先调用 `logs.ErrorContextf` 或 `logs.WarnContextf` 记录错误上下文；禁止静默返回 wrapped error 仅靠调用方感知。
- **正确做法**：
  ```go
  if err != nil {
      logs.ErrorContextf(ctx, "[EditParent] update user phone failed, err: %v", err)
      return nil, fmt.Errorf("[EditParent] update user phone failed, err:%w", err)
  }
  ```
- 例外：DAO 等底层通用方法（直接抛给上层统一处理）可省略；业务 svc 层必须遵守。
- Review 时检查所有 `return nil, fmt.Errorf`（或 `return nil, err`）的前一行是否为对应 `logs.ErrorContextf`；缺失则报 Error。

### G-22 DAO 禁止使用原始 SQL 查询与独立查询函数 [Error]

- 禁止在业务 svc 层直接使用 `dbutil.Account().WithContext(ctx).Where(...)`、`dbutil.Account().Model(&T{}).Update(...)` 等原始查询方法。
- **禁止在 `models/<包>/` 中使用独立的包级查询函数**（如 `GetUserByPhone`、`GetUserByEmail`、`GetCompanyByName` 等），这些函数本质上是将本应属于 DAO 的查询逻辑暴露为裸函数，导致查询分散、难以维护、无法复用 Cond 条件。
  - 例外：DAO 层自身的方法（`BuildCondition`、`GetByCond`、`GetListByCond` 等）属于 DAO 基础设施，不在此限。
  - 例外：仅作为**已有 DAO 方法的外观函数**、且内部直接委托给 DAO 的薄包装（如 `func GetUserByPhone(ctx, phone string) { return NewUserDao().GetByCond(ctx, &UserCond{Phone: phone}) }`），可在**迁移过渡期间**存在，但须在函数注释中标注 `// Deprecated: use account.NewUserDao().GetByCond(ctx, &UserCond{Phone: phone}) instead` 并逐步移除。
- **正确做法**，所有数据库查询都必须通过对应实体的 DAO 方法访问：
  - 单条查询用 `NewXxxDao().GetByCond(ctx, &XxxCond{Field: val})`
  - 列表查询用 `NewXxxDao().GetListByCond(ctx, &XxxCond{Field: val})`
  - 分页列表用 `NewXxxDao().GetPageListByCond(ctx, &XxxCond{...})`
  - 计数用 `NewXxxDao().CountByCond(ctx, &XxxCond{...})`
  - 更新用 `NewXxxDao().UpdateMap(ctx, id, map[string]interface{}{"field": val})`
- **新增查询条件时，优先在现有 Cond struct 中添加字段并在 BuildCondition 中处理**，而非创建新的独立查询函数。
- 例外：事务内复杂统计查询（需 `Raw`/`Exec`）或 DAO 方法确实无法满足的场景（如跨表连表统计、临时报表查询），须在代码注释中注明原因。
- Review 时检查：
  1. 所有 `dbutil.Account()` 或 `dbutil.Xxx()` 的直接调用，发现则报 Error。
  2. 所有 `models/<包>/` 中以 `func Get*`、`func Exist*`、`func Query*`、`func List*`、`func Count*`、`func Delete*`、`func Update*`、`func Create*`、`func Save*` 开头的**非 DAO 方法**的独立函数声明（即在 `*Dao` struct 以外的方法），发现则报 Error 并建议转为 DAO 方法。
   3. 标注 `// Deprecated:` 的过渡期包装函数可按 Warning 降级处理，但须确保调用方已逐步迁移。

### G-23 日志覆盖分层规范 [Error]

按日志严重度覆盖三个场景，缺少任一均视为违规。

#### G-23a 异常路径必须 ErrorContextf [Error]

- 业务 svc 层所有非预期错误返回前（包括 `return res, nil` 但 `res.Code = ErrCode_InternalError` 的情形），必须先记录 `logs.ErrorContextf(ctx, "[FuncName] ...failed, err: %v", err)`。
- **硬性检查点**：
  - `return nil, fmt.Errorf(...)` → 前一行必须是 `logs.ErrorContextf`
  - `return nil, err`（不含 fmt.Errorf 包装）→ 前一行必须是 `logs.ErrorContextf`
  - `res.Code = errcode.ErrCode_InternalError` / `res.Code = errcode.ErrCode_BadRequest` 时，若该错误不是由 Caller 输入校验直接判断（如"密码错误"、"手机号为空"），而是**内部异常（DB 失败、生成 token 失败、配置缺失等）**，则必须在前一行或前两行有 `logs.ErrorContextf`。
- **例外**：
  - DAO 等底层通用方法已用 `fmt.Errorf("[XxxDao] ... err: %w", err)` 包裹错误信息的，可省略 `logs`（错误信息会由调用方记录）。
  - API 层校验（`Validity` 方法中 `resp.Code = ErrCode_BadRequest` 后 `return`）属于用户输入校验，不要求日志。
- **正确示例**：
  ```go
  // ✅ 内部错误必须记日志
  if err := dao.GetByID(ctx, id); err != nil {
      logs.ErrorContextf(ctx, "[GetUser] GetByID failed, id:%d, err: %v", id, err)
      res.Code = errcode.ErrCode_InternalError
      return res, nil
  }

  // ✅ fmt.Errorf 包装前记日志
  if err != nil {
      logs.ErrorContextf(ctx, "[GetUser] GetByCond failed, err: %v", err)
      return nil, fmt.Errorf("[GetUser] GetByCond failed, err:%w", err)
  }

  // ❌ 错误：内部异常未记日志
  if token == "" {
      res.Code = errcode.ErrCode_InternalError
      res.Message = "生成token失败"
      return res, nil   // 没有 logs.ErrorContextf
  }
  ```

#### G-23b 降级/空值/非预期分支必须 WarnContextf [Warning]

- 当代码遇到**非预期空值、降级处理、条件不满足走默认分支**等场景时，必须使用 `logs.WarnContextf` 记录降级原因与影响。
- **典型场景**：
  - 查询返回空结果但业务允许 `return nil/零值` 继续（如 `user_id == 0` 时返回空数据）→ `logs.WarnContextf(ctx, "[FuncName] user not found, id:%d", id)`
  - 配置缺失使用默认值 → `logs.WarnContextf(ctx, "[FuncName] config missing key:%s, using default:%v", key, defaultVal)`
  - 外部调用失败但走 fallback 路径 → `logs.WarnContextf(ctx, "[FuncName] primary call failed, fallback to default, err:%v", err)`
  - 外部依赖返回异常值但业务容忍继续 → `logs.WarnContextf(ctx, "[FuncName] unexpected value:%v, continuing", val)`
- **正确示例**：
  ```go
  // ✅ 空结果降级记 Warn
  if len(students) == 0 {
      logs.WarnContextf(ctx, "[ListMyStudents] no students found for class:%d", classID)
      return []StudentItem{}, nil
  }

  // ❌ 错误：降级路径无任何日志
  if token == "" {
      token = fallbackToken  // 静默降级，排查时无从得知
  }
  ```

#### G-23c 关键业务流程路径至少 InfoContextf [Info]

- **关键业务路径**（如登录成功、资源创建/删除、数据导入完成等）应使用 `logs.InfoContextf` 记录关键节点与上下文（请求方、资源 ID、状态等）。
- **典型场景**：
  - 用户登录成功 → `logs.InfoContextf(ctx, "[LoginByPhone] login success, uin:%d", uin)`
  - 资源创建完成 → `logs.InfoContextf(ctx, "[CreateStudent] student created, id:%d, no:%s", stu.ID, stu.StudentNo)`
  - 批处理完成 → `logs.InfoContextf(ctx, "[BatchImport] import completed, count:%d, failed:%d", success, failed)`
- **何时可省略**：辅助函数、基础工具函数、高频无状态调用（如简单的 getter/setter）。
- Review 时检查新增加的 svc 入口函数和业务流程函数是否在关键路径上缺少 `InfoContextf`。

#### 综合 Review 检查清单

审查新增代码时，对每条路径逐级检查：

```
路径类型 → 应记录 → 严重度
内部错误 → ErrorContextf → Error
降级/空值 → WarnContextf → Warning
正常关键路径 → InfoContextf → Info
用户输入校验失败 → 允许不记 → —
```

---

## Review 输出格式

对每个代码块按以下格式输出：

```
### [语言] 文件: `path/to/file.go`

| 规则ID | 严重度 | 行号列表 | 当前代码片段 | 改进建议 |
|--------|--------|----------|--------------|----------|
| G-03   | Error  | 42, 87, 103 | `for ... { dao.GetByID(ctx, id) }` | 批量 `GetByIDs` + `utils.ToMap` |
| G-03b  | Error  | 215, 248 | `SplitPDFToImages(ctx, pdfURL)` × 2 | bool 聚合 `needSplit`，一次调用 |
```

**输出规则：**

1. **规则ID 必须精确**：使用完整规则编号（如 `G-03b`、`G-02a`），禁止只写 `G-03` 而实际违反的是 `G-03b`。
2. **行号列表必须完整**：同一违规的所有相关行号用逗号分隔列在同一行，如 `42, 87, 103`；禁止只写第一行而遗漏其余行。
3. **同文件同规则合并**：同一文件内同一规则的多处违规合并为一条，行号列表包含所有违规位置。
4. **当前代码片段**：摘录最能代表违规的核心代码行（不超过一行），用反引号包裹。
5. 仅报告**违反规则的项**，不重复合规代码。
6. 最后给出 **修复摘要**，格式如下：

```
## 修复摘要

### Error（必须修复）
- [ ] `path/to/file.go` 行 42, 87, 103 — [G-03] 循环内逐条 SQL，改为批量 GetByIDs + map
- [ ] `path/to/file.go` 行 215, 248 — [G-03b] SplitPDFToImages 重复调用，用 bool 聚合

### Warning（建议修复）
- [ ] `path/to/file.go` 行 310 — [G-10] 静默降级缺少警告日志

### Info（提示）
- [ ] `path/to/file.go` 行 55 — [G-12] slice 未预分配容量
```

修复摘要中每条格式：`文件路径 行 <行号列表> — [规则ID] 简要描述`，方便 agent 直接定位并修复。

---

## 其他语言（待补充）

- **Python**：TODO
- **TypeScript/JavaScript**：TODO
- **SQL 脚本**：TODO