# Workstation Primary Mode (8C/64G)

Last updated: 2026-02-21

Purpose:
- make workstation the default execution environment for heavy research/gate workloads;
- keep local machine for editing, review, and lightweight checks.

## 1) Environment roles

Local (`/Users/hui/quant_score/v4`):
- code editing
- docs maintenance
- quick smoke checks (`--help`, short segment run, dry-run)

Workstation (`~/projects/hui-wang-multi-factor-research`):
- official long runs:
  - `run_walk_forward.py`
  - `run_production_gates.py`
  - heavy segmented batches
- official gate reports and registry generation

## 2) Authoritative execution rule

For official results:
1. run on workstation;
2. save artifacts under workstation repo path;
3. sync selected artifacts back to local;
4. commit docs/code from local after verification.

Do not treat local long-run output as official if workstation policy is active.

## 3) Standard sync model

Code/docs:
- Git only (`commit -> push -> workstation pull --ff-only`)

Data/results/logs:
- `rsync` only

## 4) Official run command (workstation)

```bash
cd ~/projects/hui-wang-multi-factor-research
export PYTHONPATH=$(pwd)

python scripts/run_production_gates.py \
  --strategy configs/strategies/combo_v2_prod.yaml \
  --factor combo_v2 \
  --freeze-file runs/freeze/combo_v2_prod.freeze.json \
  --stress-market-cap-dir data/fmp/market_cap_history \
  --decision-tag committee_ws_official \
  --owner hui \
  --notes "workstation official gate run" \
  --out-dir gate_results
```

## 5) Pull-back artifacts to local

From local machine:
```bash
rsync -avh --progress \
  hui@100.66.103.44:~/projects/hui-wang-multi-factor-research/gate_results/ \
  /Users/hui/quant_score/v4/gate_results/

rsync -avh --progress \
  hui@100.66.103.44:~/projects/hui-wang-multi-factor-research/runs/freeze/ \
  /Users/hui/quant_score/v4/runs/freeze/
```

## 6) Promotion decision files (mandatory)

Must exist before committee decision:
1. `gate_results/production_gates_<ts>/production_gates_report.json`
2. `gate_results/production_gates_<ts>/production_gates_report.md`
3. `gate_results/gate_registry.csv`
4. freeze file used in the run
5. corresponding run manifests

## 7) Failure handling

If gate run fails:
1. do not override `overall_pass` manually;
2. record root cause in gate registry `notes`;
3. rerun with explicit change notes (new `decision-tag`);
4. keep both failed and rerun records.

## 8) Official wrapper workflow

Preferred official run entry:

```bash
bash scripts/workstation_official_run.sh \
  --workflow production_gates \
  --tag committee_YYYY-MM-DD_runN \
  --owner hui \
  --notes "official workstation run" \
  -- \
  --strategy configs/strategies/combo_v2_prod.yaml \
  --factor combo_v2 \
  --freeze-file runs/freeze/combo_v2_prod.freeze.json \
  --out-dir gate_results
```

This automatically writes preflight and run audit artifacts under:
- `audit/workstation_runs/<ts>_<workflow>_<decision_tag>/`
