# Performance Optimization Backlog (2026-02-21)

Scope:
- non-destructive findings during active rerun window;
- based on code inspection and live run behavior only.

## Verified current behavior

1. `run_walk_forward.py` executes windows serially inside each process.
2. `run_production_gates.py` now supports WF shard parallelism (`--wf-shards`).
3. Each shard process still rebuilds core engine/data path independently.
4. `run_walk_forward.py` writes summary only after factor loop finishes, so progress visibility is low.

## Priority P0 (highest impact)

### P0-1 Reuse engine objects across windows inside shard
- Location: `scripts/run_walk_forward.py` (`run_factor` currently constructs `BacktestEngine` per window).
- Current cost: repeated engine/data setup in every window.
- Proposed change:
  - initialize one `BacktestEngine` per factor per shard;
  - reuse in window loop;
  - clear only per-window transient state.
- Expected gain: noticeable reduction in per-window overhead.

### P0-2 Add incremental checkpoint writes for WF summaries
- Location: `scripts/run_walk_forward.py`.
- Current cost: no `walk_forward_summary.csv` until shard completion.
- Proposed change:
  - append or overwrite summary incrementally after each window;
  - same for universe audit rows.
- Expected gain: better observability; safer resume after interruption.

### P0-3 Enable signal cache option for walk-forward runner
- Current state:
  - signal cache exists in `BacktestEngine` and is wired for segmented runs;
  - walk-forward CLI does not expose `--use-cache/--cache-dir/--refresh-cache`.
- Proposed change:
  - add cache flags to `run_walk_forward.py` and pass into engine config.
- Expected gain: reduce repeated signal computation in reruns and shard runs.

## Priority P1 (medium impact)

### P1-1 Add shard-level progress heartbeat
- Emit lightweight progress lines every N windows to run.log.
- Helps distinguish slow compute vs hang.

### P1-2 Reduce repeated calendar/universe warmup
- Investigate memoizing trading calendar and reusable universe metadata per shard.

### P1-3 Lower I/O overhead in market-cap directory checks
- `BacktestEngine` checks csv existence via `os.listdir` during init.
- Can be replaced with cheaper lazy check or once-per-run memoization.

## Priority P2 (structural)

### P2-1 Deeper parallel model inside walk-forward
- Move from process-per-shard orchestration to built-in worker pool in `run_walk_forward.py`.
- Keep deterministic ordering and manifest integrity.

### P2-2 Add benchmark harness
- Add reproducible benchmark script comparing:
  - baseline serial
  - shard parallel
  - shard + cache
  - engine reuse
- Store benchmark outputs under `analysis/perf_benchmarks/`.

## Guardrails for optimization changes

1. No change to factor math/protocol semantics unless explicitly approved.
2. Preserve freeze/manifest/audit compatibility.
3. Any speed optimization must include before/after timing evidence.
