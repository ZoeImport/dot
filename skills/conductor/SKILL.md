---
name: conductor
description: Parallel multi-agent development orchestration. Use when the user brings a dev requirement and wants the full loop of "requirement analysis → grilling → multi-agent development plan → batched parallel execution (explore/dev/test/review/accept) → non-blocking supervision and merge". Triggers include "并行开发", "多个 agent 一起做", "多 agent team", "编排", "orchestrator", "conductor", "调度多个 agent", "写一个开发计划再并行干", "parallel dev", "agent team", even without naming this skill.
---

# Conductor

The main agent is a **conductor**: it never writes business code and never blocks. It grills the requirement into a shared understanding, writes a plan any sub-agent can execute from its own section alone, then drives **batched Workflows** — launch a batch, end the turn, get woken by the task-notification, verify, merge, launch the next batch.

```
Phase 0 analyze → Phase 1 grill → Phase 2 plan → per batch: [Workflow(explore/dev/test/accept) → verify → merge → integration check] → review → done
```

## Phase 0 — Requirement analysis

Extract: goal, scope, constraints, users, references.

- **From scratch** (no technical direction): dispatch one explore agent for light research (comparable solutions, mainstream stacks, known pitfalls) before grilling.
- **Has a reference** (existing repo / competitor / tech direction): review it — structure, stack, reusable modules, pitfalls to avoid. Record "what we reuse, what we deliberately don't".
- **Facts are looked up, never asked**: build commands, repo conventions, CLAUDE.md rules, directory layout, available skills — check the environment yourself.

Output: a 3–10 line requirement summary feeding Phase 1.

## Phase 1 — Grill (eight dimensions)

Invoke the **grilling** skill with the checklist below as its agenda. The checklist is guidance, not a script: skip a dimension that doesn't apply (state why, e.g. "no UI, skipping ③"), go beyond it wherever the requirement is fuzzy, and stop only when every dimension that matters is airtight. One question at a time, each with a recommended answer; facts self-served; **decisions always put to the user**.

**① Business logic (closed loop)** — core user & scenario; full flow from trigger to end incl. branches and failure paths; hard domain constraints (money/permissions/compliance); where the MVP loop closes and how non-MVP parts are marked.

**② Data flow** — sources, stores, sinks; entities, fields, relations; state machine / lifecycle; idempotency and concurrent writes; strong vs eventual consistency.

**③ UI behavior** — views and user paths; per-action feedback (loading/success/failure/empty/disabled); role-based visibility; responsive / cross-platform / a11y needs.

**④ Dev process & tech selection** — build/test/run commands and CI gates; repo conventions (vendoring, soft delete, DDL flow, commit rules); branch/MR flow. **Tech selection always passes through explicit user confirmation before Phase 2 — never a silent default**:
- Existing repo: follow its stack, but still present it in one shot ("inheriting Go 1.x + gin + MySQL, adding nothing new — confirm?") so the user can veto.
- From scratch: present 2–3 candidate stacks (from Phase 0 explore research) as a **pros/cons comparison table** — per candidate: strengths, weaknesses, maturity, fit to the requirement, team familiarity, ecosystem — with one recommended and the reason it beats the others; the user picks.
- **Any new external dependency** (library, service, storage) not already in the repo needs its own line-item confirmation.
The chosen stack + rationale + rejected alternatives go into the Decision Record and the plan's Tech Selection table; sub-agents must not introduce dependencies outside it.

**⑤ Parallel architecture** — module decomposition; dependency DAG; interface contracts (exact signatures/formats); which tasks are truly independent.

**⑥ Model & cost** — show the default table below for one-shot confirmation; only expand if the user wants changes.

**⑦ Test scope** — which modules need tests and at what granularity; tools and commands; must-test paths (money/security/parser/concurrency); per-task acceptance command (definition of done).

**⑧ Repo & deployment** — analyzed from Phase 0, confirmed here: which repo (existing / new, mono / multi) the code lands in; deploy target (which server/cluster, access method) and deploy mechanism (systemd / docker compose / k8s / CI pipeline); ports and how conflicts with existing services are avoided; config files and volume mounts (what is mounted where, secrets handling); inter-service dependency design (what talks to what, startup order, health checks). These answers feed a **dedicated deployment task** (Dockerfile / compose / CI / service files) that enters the DAG as its own module and runs in parallel with dev tasks — its interface contract is the deploy spec confirmed here.

Output: a **decision record** read back to the user. Mark each entry as user-stated or inferred; inferred entries need explicit confirmation. **Do not enter Phase 2 without confirmation.**

### Default model table (versions always resolve to latest)

| Role | Model |
|------|-------|
| explore / test / accept | sonnet |
| dev / review | fable (fallback: opus if fable unavailable) |

Escalation: a task failing twice at its tier is re-dispatched one tier up, or the conductor diagnoses whether the interface contract itself is wrong.

## Phase 2 — Plan

Write the decision record into `.plans/<YYYY-MM-DD>-<feature>/` at the project root:

- **`plan.md`** — from `templates/implementation-plan.md`: goal, global constraints (verbatim), DAG + batches, model table, test scope, and per-task: Files (ownership), Interfaces (Consumes/Produces with exact signatures), approach, implementation requirements, logic flow, bite-sized steps, acceptance commands.
- **`ledger.md`** — shared state: per-task status (pending/running/done/blocked), branch name, output paths, interface signatures, acceptance verdicts. The only channel between agents; sub-agents never read each other's context.

Self-check before proceeding — fix any failure:
1. Within each batch, **no two tasks share a file** (file-ownership check). Overlap → split batches or merge tasks.
2. DAG is acyclic; every Produces is consumed by someone.
3. Every task has a machine-runnable acceptance command.
4. Every task is executable from its own section + contracts + ledger alone.

## Phase 3 — Batched execution

One **Workflow** per batch (never the Agent tool for fan-out; never one giant Workflow for the whole plan). Inside a batch, modules flow through `pipeline()` independently — dev → test → accept per module, no barrier between modules.

Skeleton:

```js
export const meta = { name: 'batch-N', description: '...', phases: [
  { title: 'Dev' }, { title: 'Test' }, { title: 'Accept' }] }
const tasks = args.tasks   // [{id, planSection, contracts, ledgerExtract, acceptCmds, needsWorktree}]
const results = await pipeline(tasks,
  t => agent(devPrompt(t), { label: `dev:${t.id}`, phase: 'Dev', model: 'fable',
        isolation: t.needsWorktree ? 'worktree' : undefined, schema: DEV_REPORT }),
  (dev, t) => agent(testPrompt(t, dev), { label: `test:${t.id}`, phase: 'Test', model: 'sonnet', schema: TEST_REPORT }),
  (test, t) => agent(acceptPrompt(t, test), { label: `accept:${t.id}`, phase: 'Accept', model: 'sonnet', schema: VERDICT }))
return results.filter(Boolean)
```

Rules:

- **Isolation** (decided by rule, not asked): read-only roles (explore/review/accept) never isolate. dev/test isolate with `isolation: 'worktree'` **iff the batch has more than one writer**; a lone writer works in place.
- **Dev iron rule**: commit before finishing and report the branch name — worktrees are disposable, branches survive. A dev report without a branch name is incomplete.
- **Acceptance is delegated, never self-performed**: the accept agent runs the task's acceptance commands itself; **exit codes are the truth**, the dev/test agents' claims are only for locating problems. Verdict is structured: commands run, output digest, pass/fail.
- **Conductor loop**: launch Workflow → update ledger → end turn. The task-notification wakes you; read the workflow result plus `journal.jsonl` if anything looks off, update ledger, run the merge protocol, launch the next batch. No polling.
- **Hang guard**: after launching each batch, `ScheduleWakeup` with a long fallback (~1800s). If woken and the workflow is alive, note it and sleep again; if hung, `TaskStop` → fix script → resume with `resumeFromRunId`.
- A BLOCKED task never blocks its siblings — the pipeline keeps other modules flowing; the conductor adjudicates at the batch boundary.

## Phase 4 — Merge protocol (batch boundary)

Per-task acceptance passing is **not** batch passing. In order:

1. All tasks in the batch pass individual acceptance.
2. Conductor merges the reported branches one by one into the integration branch. **A textual conflict is a plan violation** (file ownership was breached) → dispatch a fix agent with both diffs; record in ledger.
3. Dispatch an accept agent for the **post-merge integration check**: run the batch's full acceptance suite on the merged result. This catches semantic conflicts — branches that pass alone but break together (e.g. one changed a signature, another added a call to the old one).
4. Integration check passes → batch is done; the next batch's worktrees branch from this new baseline. **Never launch batch N+1 before batch N's merge + integration check completes.**

## Phase 5 — Supervision & adjustment

Checkpoints are **batches**, not wall-clock estimates — agent runtimes can't be scheduled, so don't pretend. At every batch boundary check three things: progress vs plan, whether any agent's approach drifted from the plan, and any BLOCKED / dangling interface / unaccepted item.

| Situation | Action |
|-----------|--------|
| Task failed (< 2 times) | Resume same model with failure context |
| Task failed twice | Escalate one model tier and re-dispatch, or conductor diagnoses the contract |
| Contract drift (Consumes/Produces mismatch) | Revise plan contract, notify both sides via ledger, re-dispatch consumer |
| Requirement change | Back to Phase 1 for supplemental grilling → update plan → re-dispatch |
| New independent sub-requirement | Append to DAG as a new task/batch; never blocks existing work |
| All batches merged & checked | Full review pass (fable/opus) → clean → final report |

## Sub-agent prompt template

```
You are the <explore|dev|test|review|accept> agent for Task <N>: <name>.
Read ONLY: your task's plan section + the interface contracts + the ledger extract below. Do not read other tasks.
[Background] <goal + this task's constraints, verbatim>
[Implementation requirements] <from plan>
[Logic flow] <from plan>
[Steps] <bite-sized checklist>
[Acceptance] <commands + expected results>
[Return — structured]
- done / not done
- branch name (dev: mandatory) + output file paths + key interface signatures
- test/self-check results (command + output digest)
- blockers and required inputs, if any
- one-line approach summary (for drift detection)
```

## Definition of Done

- [ ] Every task accepted by an accept agent (exit codes, not claims)
- [ ] Every batch merged + post-merge integration check passed
- [ ] No dangling interfaces: every Produces actually consumed
- [ ] Critical paths (money/security/parser/concurrency) tested and green
- [ ] Full review found no load-bearing issues
- [ ] Final report to the user: what was built, where it lives, how to run it, what remains
