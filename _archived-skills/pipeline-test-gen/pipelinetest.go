// Package pipelinetest holds reusable helpers for AI-driven end-to-end backend
// pipeline tests: polling async state, waiting on a data outcome, and emitting
// staged progress so a long-running integration test is observable.
//
// WHERE THIS GOES: a SHARED, fixed location in the repo (e.g. pkgs/testutils or
// internal/testsupport) — NOT copy-pasted inline into each *_test.go. Inlining
// a `waitUntil` per test is the #1 smell this package removes.
//
// This file is a portable reference. Adapt imports/paths to your repo; keep the
// names so every pipeline test reads the same way.
package pipelinetest

import (
	"fmt"
	"testing"
	"time"
)

// Poll calls cond every `interval` until it returns true or `timeout` elapses.
// On timeout it fails the test with `desc` so the failure says WHAT was awaited,
// not just "timeout". This is the global `waitUntil` — never inline it per test.
//
//	pipelinetest.Poll(t, 60*time.Second, 2*time.Second, "dot_async imported", func() bool {
//	    return countRows(...) > 0
//	})
func Poll(t *testing.T, timeout, interval time.Duration, desc string, cond func() bool) {
	t.Helper()
	deadline := time.Now().Add(timeout)
	for {
		if cond() {
			return
		}
		if time.Now().After(deadline) {
			t.Fatalf("[pipeline] timed out after %s waiting for: %s", timeout, desc)
		}
		time.Sleep(interval)
	}
}

// PollValue is Poll for the common case where the condition also produces the
// value you want. cond returns (value, ok); Poll stops on ok and returns value.
//
//	localID := pipelinetest.PollValue(t, 60*time.Second, 2*time.Second, "import done",
//	    func() (uint, bool) { id := lookup(); return id, id != 0 })
func PollValue[T any](t *testing.T, timeout, interval time.Duration, desc string, cond func() (T, bool)) T {
	t.Helper()
	var out T
	Poll(t, timeout, interval, desc, func() bool {
		v, ok := cond()
		if ok {
			out = v
		}
		return ok
	})
	return out
}

// Stages emits "[STAGE n/total] ..." lines so the test transcript reads like a
// pipeline run. Construct once with the total number of stages, call Begin at
// the top of each phase. Observability is the point: when a 3-minute async test
// hangs, the last STAGE line tells you exactly where.
type Stages struct {
	t     *testing.T
	total int
	n     int
	start time.Time
}

// NewStages starts a staged run with `total` phases.
func NewStages(t *testing.T, total int) *Stages {
	return &Stages{t: t, total: total, start: time.Now()}
}

// Begin logs the next stage header with elapsed wall-clock since the run started.
func (s *Stages) Begin(format string, args ...any) {
	s.t.Helper()
	s.n++
	prefix := fmt.Sprintf("[STAGE %d/%d +%s] ", s.n, s.total, time.Since(s.start).Round(time.Millisecond))
	s.t.Logf(prefix+format, args...)
}

// Done logs a final summary line.
func (s *Stages) Done(format string, args ...any) {
	s.t.Helper()
	prefix := fmt.Sprintf("[STAGE done +%s] ", time.Since(s.start).Round(time.Millisecond))
	s.t.Logf(prefix+format, args...)
}
