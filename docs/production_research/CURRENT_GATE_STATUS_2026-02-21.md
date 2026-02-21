# Current Gate Status Snapshot (2026-02-21)

As-of (UTC): 2026-02-21
As-of (local reference): 2026-02-20/2026-02-21 cross-timezone workstation cycle

This snapshot records verified facts for the active production gate cycle.

## 1) Confirmed execution context

- Workstation host: `dell5820`
- Git commit used by active rerun: `919ff34786df073e5b4bd2036068b50fb37a3e1f`
- Active run directory:
  - `audit/workstation_runs/2026-02-21_053448_production_gates_committee_2026-02-21_run1_rerun4`
- Decision tag:
  - `committee_2026-02-21_run1_rerun4`

## 2) What has completed in rerun4

1. Cost stress `x1.5` completed
   - `test_ic_overall=0.05289120889645093`
   - report: `runs/2026-02-21_053448.json`
2. Cost stress `x2.0` completed
   - `test_ic_overall=0.05289120889645059`
   - report: `runs/2026-02-21_054021.json`

## 3) Active phase (in progress)

- Walk-forward stress is running in shard-parallel mode (`--wf-shards 4`):
  - `shard_00`: years `2013,2017,2021,2025`
  - `shard_01`: years `2014,2018,2022`
  - `shard_02`: years `2015,2019,2023`
  - `shard_03`: years `2016,2020,2024`
- `threads=8` was set at wrapper level (`--threads 8`).

## 4) Confirmed resolved blockers in this cycle

1. Python executable mismatch on workstation
- resolved by wrapper preferring `.venv/bin/python`.

2. Freeze mismatch (config hash / git commit mismatch)
- resolved by creating commit-aligned freeze:
  - `runs/freeze/combo_v2_prod_2026-02-21_g919ff34.freeze.json`

3. WF single-process bottleneck
- resolved by adding `--wf-shards` in `scripts/run_production_gates.py`.

## 5) Pending completion criteria

The cycle is only complete when all of the following exist for rerun4:

1. `gate_results/production_gates_2026-02-21_053448/production_gates_report.json`
2. `gate_results/production_gates_2026-02-21_053448/production_gates_report.md`
3. appended row in `gate_results/gate_registry.csv` with rerun4 decision tag
4. finalized stage ledger row in `docs/production_research/STAGE_AUDIT_LOG.md`

## 6) Monitoring commands (non-destructive)

```bash
ssh hui@100.66.103.44
cd ~/projects/hui-wang-multi-factor-research

RUN_DIR=$(ls -td audit/workstation_runs/*committee_2026-02-21_run1_rerun4* | head -n1)
tail -f "$RUN_DIR/run.log"

pgrep -af "run_walk_forward.py --factors combo_v2"
```
