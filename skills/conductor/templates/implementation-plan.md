# Plan: <feature name>

> Location: `.plans/<YYYY-MM-DD>-<feature>/plan.md` · Shared state: `ledger.md` in the same directory.
> Any sub-agent must be able to execute its task from its own section + contracts + ledger alone.

## Goal

<one sentence, acceptable/verifiable>

## Global Constraints

<verbatim from the requirement and decision record — repo rules, domain hard constraints, forbidden actions>

## Decision Record

<numbered list of grilled decisions; mark each as user-stated or user-confirmed-inference>

## Tech Selection

> Confirmed by the user in Phase 1. Sub-agents must not introduce dependencies outside this table.

### Candidates compared (from scratch only)

| Candidate | Pros | Cons | Verdict |
|-----------|------|------|---------|

### Final selection

| Choice | Selected | Rationale | Rejected alternatives & why |
|--------|----------|-----------|-----------------------------|
| Language/runtime | | | |
| Framework / key libs | | | |
| Storage | | | |
| New external dependencies | | | |

## Architecture

### Dependency DAG & batches

```
Batch 1: T1, T2, T3   (independent — file ownership disjoint)
Batch 2: T4 (needs T1.Produces), T5 (needs T2.Produces)
...
```

- Isolation per batch: <batch N has X writers → worktree / in-place>
- Integration branch: `<name>`; batch N+1 bases off batch N's merged baseline.

### Interface contracts

| Contract | Producer | Consumer | Exact signature / format |
|----------|----------|----------|--------------------------|

## Model & Cost

| Role | Model | Notes |
|------|-------|-------|
| explore / test / accept | sonnet | latest version |
| dev / review | fable → opus fallback | latest version |

Escalation: 2 failures at tier → escalate one tier or conductor diagnoses the contract.

## Test Scope

| Module | Granularity (unit/integration/e2e) | Must-test paths | Command |
|--------|-----------------------------------|-----------------|---------|

## Repo & Deployment

> Confirmed in Phase 1. This section is the interface contract for the deployment task (a parallel module in the DAG).

- **Repo**: <existing repo path / new repo; mono or multi>
- **Deploy target**: <server/cluster, access method (ssh alias, kubeconfig)>
- **Mechanism**: <systemd / docker compose / k8s / CI pipeline + trigger>
- **Ports**: <service → port map; conflict check against existing services on target>
- **Config & mounts**: <config files, where mounted, secrets handling (never committed)>
- **Service dependencies**: <what talks to what, startup order, health checks>
- **Deploy commands / verification**: <how to deploy and how to verify it's live>

---

## Task N: <name>  (Batch <B>, role sequence: dev → test → accept)

**Files (ownership — no other task in this batch may touch these):**
- `path/to/file`

**Interfaces**
- Consumes: <contract refs with exact signatures>
- Produces: <exact signatures — must be consumed by someone>

**Approach**

<development idea: why this design, key trade-off>

**Implementation requirements**

<hard requirements: error handling, idempotency, conventions to follow>

**Logic flow**

<numbered flow from entry to exit incl. failure branches>

**Steps**

- [ ] <bite-sized step>
- [ ] commit and record branch name in ledger (dev iron rule)

**Acceptance**

```bash
<machine-runnable commands; exit code is the verdict>
```

---

# ledger.md format

```markdown
# Ledger: <feature>

| Task | Status | Branch | Outputs | Verdict |
|------|--------|--------|---------|---------|
| T1 | pending/running/done/blocked | <branch> | <paths + signatures> | <accept agent digest> |

## Batch log
- Batch 1: launched <workflow runId> → merged <commit> → integration check: pass/fail
## Notes
- <contract revisions, plan violations, escalations>
```
