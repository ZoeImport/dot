// ==================== End-to-End Pipeline Test ====================
// Link: exambank source question -> question_sync_fetch core_task
//       -> worker+handler import -> local company question
//       -> source knowledge mutation -> know_class_sync core_task
//       -> local knowledge relation.
//
// Validation target: the real async sync path can repair an imported question
//   whose local knowledge relation starts empty. After the source gains one
//   knowledge point, a know_class_sync run must change the downstream relation
//   from 0 -> 1 and preserve the test company boundary.
//
// Real async queue: production task creators insert core_task rows. The online
//   worker+handler consumes them; this test polls task lifecycle first, then
//   polls data landing because callback writes can lag task success.
//
// Data safety: all writes use a dedicated test company and fresh source rows.
//   Cleanup is soft-delete only; reusable reference knowledge rows are not
//   modified or deleted.
//
// Run: requires source DB + business DB + Redis + online worker.
//   go test ./path/to/package -run TestKnowClassSyncCorePipeline -v
// ================================================================
package devtask_test

import (
	"context"
	"fmt"
	"net/http"
	"strings"
	"testing"
	"time"

	"yourrepo/pkgs/pipelinetest" // the shared helper package (Poll, Stages)
	// + your real imports: teacher DAOs, devtask, dbutil, model, gorm/postgres ...

	"github.com/stretchr/testify/assert"
)

// ─────────────────────────────────────────────────────────────────────────────
// Config — EVERYTHING tunable lives here, named, in one block. No magic numbers
// or literals scattered through the test body. New env? change one struct.
// ─────────────────────────────────────────────────────────────────────────────

var pipelineCfg = struct {
	ExamapiBase string // local service under test
	ExamapiAuth string
	QueryAPI    string
	SourceDSN   string // source-of-truth DB the service reads (test_rw, writable)
	KnowPointID int    // a pre-existing reference row we reuse instead of seeding
	CompanyID   uint   // dedicated test tenant for isolation + cleanup scoping

	TaskTimeout time.Duration // async task → terminal state
	DataTimeout time.Duration // callback write lands after task success
	PollEvery   time.Duration // polling cadence — don't hammer; ~2s is plenty
}{
	ExamapiBase: "http://localhost:8087/v3",
	ExamapiAuth: "yg-REDACTED-test-token",
	QueryAPI:    "/examapi.QueryQuestion",
	SourceDSN:   "postgresql://test_rw:REDACTED@host:29127/exambank_test?sslmode=disable",
	KnowPointID: 829,
	CompanyID:   990002,
	TaskTimeout: 180 * time.Second,
	DataTimeout: 60 * time.Second,
	PollEvery:   2 * time.Second,
}

// ─────────────────────────────────────────────────────────────────────────────
// Test
// ─────────────────────────────────────────────────────────────────────────────

func TestKnowClassSyncCorePipeline(t *testing.T) {
	// Skip-guard: external infra (service + worker + handler) must be up. Keeps
	// CI green when they aren't — an integration test that can't run is skipped,
	// not failed.
	if !examapiReachable() {
		t.Skip("examapi unreachable on " + pipelineCfg.ExamapiBase + " — skipping E2E")
	}

	ctx := context.Background()
	st := pipelinetest.NewStages(t, 5)
	src := openSourceDB(t) // gorm.Open(postgres...) using pipelineCfg.SourceDSN

	// ── STAGE 1: seed a controllable source row (unique auto-id, no knowledge) ──
	st.Begin("seeding source question (no knowledge)")
	examQID := seedSourceQuestion(t, src) // INSERT ... RETURNING id
	externalID := fmt.Sprintf("%d", examQID)
	t.Cleanup(func() {
		// SOFT delete our own seeded row — never hard-delete shared test data.
		src.Exec("UPDATE exambank_question SET deleted_at = now() WHERE id = ?", examQID)
	})
	t.Logf("[pipeline] seeded source question id=%d external_id=%s", examQID, externalID)

	// ── STAGE 2: enqueue fetch task, assert core_task lifecycle, await import ──
	st.Begin("enqueue fetch task + await async import")
	snap := maxTaskID(t) // increment baseline; auto-ids never reused
	created, err := genFetchTask(ctx, examQID, pipelineCfg.CompanyID)
	assert.NoError(t, err)
	assert.Equal(t, 1, created)
	t.Cleanup(func() { softDeleteTasksAfter(snap) })

	fetchTask := newestTaskAfter(t, snap, "question_sync_fetch")
	assert.Equal(t, pipelineCfg.CompanyID, fetchTask.CompanyID)
	assert.Contains(t, fetchTask.Payload, externalID)
	assert.False(t, fetchTask.IsFinished(), "freshly enqueued task must not be terminal")

	done := waitTaskTerminal(t, fetchTask.ID, pipelineCfg.TaskTimeout)
	assert.True(t, done.IsSuccess(), "fetch task should succeed: status=%s err=%s", done.TaskStatus, done.ErrMsg)
	assert.NotEmpty(t, done.Result)
	assert.NotNil(t, done.EndAt)

	// Callback write may lag task success → poll the DATA outcome, not the clock.
	localQID := pipelinetest.PollValue(t, pipelineCfg.DataTimeout, pipelineCfg.PollEvery,
		"dot_async import lands with source_id", func() (uint, bool) {
			id := lookupImportedLocalID(ctx, pipelineCfg.CompanyID, externalID)
			return id, id != 0
		})
	t.Cleanup(func() { softDeleteImported(localQID, pipelineCfg.CompanyID, externalID) })
	t.Logf("[pipeline] imported local question id=%d for company_id=%d", localQID, pipelineCfg.CompanyID)

	// ── STAGE 3: assert the precondition — no knowledge yet ──
	st.Begin("assert no knowledge before sync")
	assert.Empty(t, knowledgeRels(ctx, localQID), "imported with empty knowledge")

	// ── STAGE 4: mutate the source — ADD knowledge (creates the diff) ──
	st.Begin("add knowledge to source row")
	assert.NoError(t, src.Exec("UPDATE exambank_question SET knowledge_point_ids = ? WHERE id = ?",
		fmt.Sprintf("{%d}", pipelineCfg.KnowPointID), examQID).Error)

	// ── STAGE 5: enqueue sync task, await, assert downstream 0 → ≥1 ──
	st.Begin("enqueue sync task + await knowledge write")
	snap2 := maxTaskID(t)
	created2, err := genSyncTask(ctx, localQID)
	assert.NoError(t, err)
	assert.Equal(t, 1, created2)

	syncTask := newestTaskAfter(t, snap2, "know_class_sync")
	assert.Equal(t, pipelineCfg.CompanyID, syncTask.CompanyID)
	assert.Contains(t, syncTask.Payload, fmt.Sprintf("%d", localQID))
	syncDone := waitTaskTerminal(t, syncTask.ID, pipelineCfg.TaskTimeout)
	assert.True(t, syncDone.IsSuccess(), "sync task should succeed: status=%s err=%s", syncDone.TaskStatus, syncDone.ErrMsg)

	pipelinetest.Poll(t, pipelineCfg.DataTimeout, pipelineCfg.PollEvery,
		"knowledge relation written", func() bool { return len(knowledgeRels(ctx, localQID)) > 0 })

	finalKnowledgeRels := knowledgeRels(ctx, localQID)
	assert.Len(t, finalKnowledgeRels, 1)
	assert.Equal(t, pipelineCfg.KnowPointID, finalKnowledgeRels[0].KnowPointID)
	st.Done("knowledge 0 -> %d for local id=%d", len(finalKnowledgeRels), localQID)
}

// examapiReachable POSTs a trivial query; false → skip the whole E2E.
func examapiReachable() bool {
	req, err := http.NewRequest(http.MethodPost, pipelineCfg.ExamapiBase+pipelineCfg.QueryAPI,
		strings.NewReader(`{"request":{"limit":1,"offset":0}}`))
	if err != nil {
		return false
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", pipelineCfg.ExamapiAuth)
	resp, err := (&http.Client{Timeout: 5 * time.Second}).Do(req)
	if err != nil {
		return false
	}
	defer resp.Body.Close()
	return resp.StatusCode == http.StatusOK
}

// waitTaskTerminal builds on the shared Poll: project glue stays thin, the
// polling contract stays in pipelinetest.
func waitTaskTerminal(t *testing.T, taskID uint, timeout time.Duration) taskEntity {
	t.Helper()
	return pipelinetest.PollValue(t, timeout, pipelineCfg.PollEvery,
		fmt.Sprintf("task %d terminal", taskID), func() (taskEntity, bool) {
			task := getTask(taskID)
			return task, task.IsFinished()
		})
}

// ── project glue (signatures only — wire to your real DAOs/driver) ───────────
// type taskEntity = model.TaskEntity
// func openSourceDB(t *testing.T) *gorm.DB { ... gorm.Open(postgres.Open(pipelineCfg.SourceDSN)) }
// func seedSourceQuestion(t, db) int64       { db.Raw("INSERT ... RETURNING id").Scan(&id) }
// func maxTaskID(t) uint                       { SELECT COALESCE(MAX(id),0) FROM core_task }
// func newestTaskAfter(t, afterID, taskType) taskEntity
// func getTask(id uint) taskEntity
// func genFetchTask / genSyncTask(...) (int, error)  // the real GenXxxTasks creators
// func lookupImportedLocalID / knowledgeRels(...)     // downstream DAO reads
// func softDeleteTasksAfter / softDeleteImported(...) // gorm Delete (soft)
