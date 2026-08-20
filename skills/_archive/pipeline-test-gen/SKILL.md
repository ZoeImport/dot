---
name: pipeline-test-gen
description: Use when building an end-to-end integration test for a backend logic chain that spans multiple services, databases, or an async task queue — seeding a source store, running a fetch/import job, mutating state, triggering a sync job, then verifying downstream tables. Use when a flow resists unit testing because it depends on cron timing, task ordering, cross-service callbacks, or multi-DB state, and you want the agent itself to drive the whole chain and assert it.
---

# Pipeline Test Generation

## Overview

A pipeline test drives a **complete backend logic chain** the way production does — across services, databases, and an async task queue — and asserts both the **task lifecycle** and the **downstream data**. The agent itself seeds the source-of-truth, enqueues real jobs, waits on async completion, mutates state to force a diff, and verifies the result.

**Core principle:** a unit test proves a function; a pipeline test proves the *system*. The cost is real infra and waiting — so make the waiting observable, the config externalized, and the cleanup safe.

This skill captures a chain that passed end-to-end: `source DB → service API → async task queue → worker+handler → business DB`. See [example_pipeline_test.go](example_pipeline_test.go) and the shared helpers in [pipelinetest.go](pipelinetest.go).

## Output quality bar

Pipeline tests are long-lived diagnostic artifacts. Generate code that a maintainer can read during an outage:

- **Start with a business-flow banner** before the test. It must name the end-to-end link, validation target, real async mechanism, data-safety boundary, and exact run command. Use the concrete business entities, not generic "source/downstream" placeholders.
- **Use effective data-flow comments.** Comments should explain why data moves between systems, why a mutation proves the fix, and why a value is intentionally invalid/empty. Avoid comments that merely restate the next line.
- **Use readable names.** Variables and funcs should carry domain meaning: `templateBookID`, `companyCopyBookID`, `enqueueKnowClassSyncTask`, `waitCoreTaskSuccess`. Avoid `id1`, `data`, `res`, `doSync`, or over-abbreviated names.
- **Exercise the real mechanism as much as possible.** Prefer production task creators, payloads, queue rows, worker/handler paths, service APIs, and real DAO reads. Only call one method directly when the real boundary is impossible to drive, and mark that compromise in the banner.
- **Assert complete expectations at every stage.** Check initial state, created task count, task type/payload/priority, lifecycle fields, row counts before/after, ownership/tenant boundaries, soft-delete flags, and final data content—not just "no error".
- **Do not discard Go values casually.** Minimize `_`. If a return value is intentionally irrelevant, name it and log or assert why it is irrelevant: `ignoredDuplicateCount` with `t.Logf(...)` is better than `_`.

Use this banner shape, translated to the project's language if needed:

```go
// ==================== 端到端管道测试 ====================
// 链路: exambank(prod book) → book_sync 任务 → 模板书(company_id=0)
//        → PublishBook → 公司副本(+dot_async 行) → know_class_sync 任务 → 副本知识点
//
// 验证目标: PublishBook 给公司副本写的 dot_async 行，使 KnowClassSync 能像
//   question_sync 链路一样覆盖到副本——删空副本本地知识点后，跑一轮 know_class_sync
//   应把知识点重新补回（0 → N）。这正是「公司副本知识点扩散」修复的反向证明。
//
// 真实异步队列: 用生产创建器入队 core_task，轮询任务到终态，由线上 dotworker+dottask
//   执行（examapi 走 core_settings 的远端生产地址）。任务 priority 调高以尽快被消费。
//
// 数据安全: 只对测试公司(pipeCfg.TestCompanyID)产生临时数据；结尾打印链路汇报后软删除。
//   company_id=0 的模板书是合法生产数据，不删。
//
// 运行: 需 dotpen_test + Redis + 线上 worker；CI 用 -short 跳过。
//   go test ./apps/account/services/svcbook/ -run TestPublishKnowClassSyncPipeline -v
// =====================================================
```

## When to use

- A flow spans **2+ stores or services** (e.g. Postgres source → HTTP service → MySQL business DB) and no single unit test covers the seam.
- The behavior depends on **cron timing or selection ordering** — hard to trigger deterministically. Add a targeted injection (e.g. "sync these specific IDs") so the test bypasses the scheduler.
- The write happens in a **callback/handler** after a worker, and you need to prove the async round-trip, not just one function.
- You're validating a **diff/sync**: state A imported, source mutated to B, sync detects A→B.

**Not for:** pure function logic (use a unit test), or anything you can assert without standing up the real services.

## The framework

1. **Map the data path FIRST — don't guess.** `curl` the live endpoint (a 500 once revealed a missing DB connection — the test would have lied), inspect source schemas (DB MCP / `information_schema`) for NOT-NULL columns and a reusable reference row, and find **where writes happen** (worker vs handler). A worker reaching into a business DB is an architecture smell the pipeline test surfaces. Write the banner only after this map is accurate.
2. **Externalize ALL config** into one named block — endpoints, DSNs, auth, reference IDs, a test tenant id, every timeout/interval. Zero literals in the body; new env = edit one struct.
3. **Seed in the source of truth** with a fresh unique id (not a shared row you'd mutate-and-restore); set only NOT-NULL-without-default columns. If the test runtime can't reach the source store, open it directly with the vendored driver + DSN from config.
4. **Drive the REAL queue, then poll.** Enqueue via the production creator; assert the lifecycle — new task is `pending`, poll to terminal, assert `success`/`Result`/`EndAt` — then poll the **data outcome** separately (callbacks lag task success; wait on the row, not the clock). For determinism without daemons, call `worker.Execute`+`handler.Handle` directly instead (less realistic, fully deterministic), and state that tradeoff in the banner.
5. **Force the diff, assert 0 → N.** Mutate the source or downstream state so the sync has something meaningful to repair, enqueue the sync job, await it, and assert the downstream table changed from the expected baseline to the exact expected content. Snapshot `MAX(id)` first so you only see this run's rows.
6. **Make every phase observable** — `pipelinetest.Stages.Begin(...)` once per real phase, with the total count matching the planned flow. The last `[STAGE n/N]` line is your debugger when a 3-min async test hangs. Do not use stage logs as casual progress spam; stage boundaries should match business transitions.
7. **Clean up with soft-delete, idempotently** — `t.Cleanup` right after each write; **never hard-delete shared data** (`deleted_at`). Fresh per-run ids keep it re-runnable.
8. **Skip-guard for CI** — `t.Skip` when infra is unreachable; can't-run ≠ fail.

## Quick reference

| Concern | Do this |
|---|---|
| Waiting | `pipelinetest.Poll` / `PollValue` from a shared package — never inline `for { sleep }` |
| Config | one named struct/const block at top; zero literals in body |
| Observability | `pipelinetest.Stages` — `[STAGE n/N +elapsed] ...` per phase |
| Naming | Domain-specific names for vars and funcs; no `id1`, `data`, `res`, or mystery `_` |
| Comments | Business/data-flow intent, invalid/empty value meaning, cleanup scope |
| Find created rows | snapshot `MAX(id)` before, query `id > snap` after |
| Async assert | task `pending` → poll terminal → assert `success`/`Result`/`EndAt`; then poll data |
| Stage design | One stage per business transition; total count accurate; assert expected data at each stage |
| Cleanup | `t.Cleanup` + soft-delete only; unique ids per run |
| CI safety | `t.Skip` when infra unreachable |
| Source seeding | unique id, only NOT-NULL-no-default cols, vendored driver + DSN |

## Performance & resource notes

- **Poll cadence ~2s, two-tier timeouts:** task-terminal (worker pickup, ~180s) vs data-landed (callback lag, ~60s) — don't reuse one number. Keep both in config.
- **Reuse one source-DB connection** per test; polls are cheap reads, not new opens.
- **Assert resources, not just correctness:** capture task `Cost`/duration, row counts, batch sizes and bound them — a pipeline test is the natural place to catch N+1 or runaway growth ("one task, ≤N rows, < X s").
- **Background long async waits;** never block on foreground sleeps.

## Common mistakes

| Mistake | Fix |
|---|---|
| `waitUntil` copy-pasted inline in each test | One `Poll` in a shared package; project glue stays thin |
| Magic numbers/URLs scattered in the body | One externalized config block |
| Asserting a racy intermediate state (`running`) | Assert only `pending` (just enqueued) and the terminal state |
| Polling the clock then reading once | Poll the **data outcome** until present |
| Hard-deleting seeded rows in shared DBs | Soft-delete (`deleted_at`); it's a hard rule, not a preference |
| No stage logging → silent 3-min hang | `Stages.Begin` at every phase |
| Stage count drifts from reality | Define stages from the business flow, then keep `NewStages(t, N)` in sync |
| `_` hides useful returned data | Name the value and log/assert why it is intentionally unused |
| Generic names obscure the chain | Use names from the business domain and queue/task vocabulary |
| Comments narrate syntax | Replace with data-flow comments that explain intent, proof, and safety |
| Calling only the target method | Drive the production creator/queue/worker/service path unless impossible; document any shortcut |
| Test fails when infra is down | `t.Skip` guard |
| Writing the test before mapping the data path | `curl` + schema inspection first; the map is half the work |
| Worker reads business DB to make the call | Resolve inputs at enqueue time, pass via payload; keep the worker thin (the pipeline test exposes this) |

## Real-world impact

This pattern took a "can't really test it — it's a cron with ordering" flow to a deterministic, re-runnable, fully-asserted E2E that also **surfaced two architecture bugs** the unit tests never could: a service missing a DB connection, and a worker reaching into a business DB it shouldn't. Pipeline tests pay for their setup cost by testing the seams where real systems break.
