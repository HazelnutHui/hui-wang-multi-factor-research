# Daily Dev + Research Flow Standard

Last updated: 2026-02-22

Purpose:
- align day-to-day development and research work under one repeatable operating flow;
- prevent local over-tuning inside existing data boundaries;
- enforce dual-track execution: fast research track + governed official track.

## 1) Daily Operating Model (Dual Track)

Run both tracks every active research day:

1. Research track (high throughput, non-official)
- objective: generate and rank new hypotheses quickly;
- scope: segmented + short-window WF checks, dry-run validation;
- output: candidate updates and next-run planning artifacts.

2. Official track (governed, low frequency)
- objective: produce committee-grade promotion evidence;
- scope: workstation official wrapper, DQ gate, full production gates;
- output: gate report + governance audit chain + registry updates.

Rule:
- no official decision is made from research-track-only outputs.

## 2) Mandatory Start-of-Day Checklist

1. Confirm current official run status (active vs finished).
2. Confirm canonical DQ input path exists and is fresh:
- `data/research_inputs/combo_v2_dq_input_latest.csv`
3. Confirm active freeze path for official runs.
4. Confirm no placeholder DQ path remains in active plans/policies.

## 3) Research Track SOP (Daytime)

1. Prepare bounded experiment batch:
- max 2-3 discrete values per key parameter;
- avoid continuous micro-tuning.
2. Run fast validation only:
- segmented stability;
- short-window WF sanity (or dry-run command validation).
3. Update candidate queue and next-run plan artifacts.
4. Apply stop rule:
- stop branch after 2 consecutive no-improvement rounds on core metrics.

## 4) Data-Boundary Expansion Rule (Anti-Loop)

To avoid staying trapped in existing data scope:

Trigger expansion proposal when any one condition holds:
1. two consecutive no-improvement rounds;
2. same failure domain repeats in governance/failure-pattern reports;
3. candidate priority scores plateau with unchanged feature families.

When triggered, propose at least one explicit data-extension hypothesis:
1. new factor family needed;
2. required data fields;
3. expected impact;
4. bounded trial plan (small pilot before full-scale ingestion).

Operational add-on:
- before adding any new FMP endpoint into ingestion, run one probe pass via `scripts/fmp_interface_probe.py` and archive ambiguity notes in `docs/production_research/FMP_INTERFACE_PROBE_STANDARD.md`.

## 5) Official Track SOP (Workstation)

1. Ensure DQ gate passes on canonical input.
2. Run official wrapper with new decision tag.
3. Do not bypass official hard checks (`skip-*` forbidden for official runs).
4. After completion, run post-run sync/finalize and governance checks.

## 6) End-of-Day Outputs (Required)

1. latest candidate queue and next-run fixed plan.
2. latest failure pattern summary.
3. if official run happened: gate report + governance check + remediation plan.
4. short daily note:
- what changed;
- what was rejected;
- what is queued for next cycle.

## 7) Minimal Daily Command Skeleton

```bash
cd /Users/hui/quant_score/v4
export PYTHONPATH=$(pwd)

# research track (recommended single entry)
bash scripts/ops_entry.sh daily
# daily brief now probes workstation status first; falls back to local cache if unreachable

# optional: execute rank-1 command after dry-run validation
# bash scripts/ops_entry.sh daily --execute

# status-only (fast, no queue/plan rebuild)
# bash scripts/ops_entry.sh status

# official track (workstation) when approved
# bash scripts/ops_entry.sh official ...
```
