# V4 Context Pack (OpenClaw)

Last updated: 2026-03-10

## Project Identity
- Repo: `/Users/hui/quant_score/v4`
- Theme: US equities daily-frequency multi-factor research with governance-first workflow.

## Canonical Batch Baseline
- Formal batch: `batchA100_logic100_formal_v1`
- Canonical run id: `2026-02-28_095939_batchA100_logic100_formal_v1`
- Canonical output path:
  - `segment_results/factor_factory/2026-02-28_095939_batchA100_logic100_formal_v1`

## 100-Factor Consolidated Facts
- Final availability: `100/100`
- Implementation split:
  - `native=75`
  - `alias_proxy=18`
  - `proxy=7`
- Exact duplicate IC-vector groups in canonical set: `0`

## Active Single-Factor Policy (Hard Rules v1.0)
- Mandatory sequence:
  - `SF-L1` segmented strict
  - `SF-L2` fixed train/test
  - hard filter (`test_ic <= 0` removed from main combo pool)
  - `SF-L3` walk-forward on survivors
  - WF/cost filters
  - grade A/B/C
- Key gates:
  - `SF-L2`: `test_ic > 0` required for main combo
  - `SF-L3`: positive-window ratio `>= 60%`, no 3 consecutive negative windows
  - cost-adjusted OOS must stay positive
- Grade:
  - `A`: `test_ic >= 0.006`
  - `B`: `0 < test_ic < 0.006`
  - `C`: otherwise
- Main combo admission: grades `A/B` only.

## Global Comparability Baseline
- `REBALANCE_FREQ=5`
- `HOLDING_PERIOD=3`
- `REBALANCE_MODE=None`

## Execution Topology
- Workstation runtime repo:
  - `~/projects/hui-wang-multi-factor-research`
- Workstation clean sync repo:
  - `~/projects/v4_clean`
- Do not force-sync runtime repo during active jobs.

## Agent Execution Boundary
- Approved entrypoint:
  - `agent/scripts/agent_gateway.py`
- Approval file:
  - `configs/research/factory_queue/run_approval.json`
- Audit root:
  - `audit/agent_gateway/`

## FMP Callable Data Baseline
- Stable callable endpoints baseline: `156`
- Sampled unique fields baseline: `824`
- Default-allow fields: `751`
- Reference:
  - `docs/production_research/FMP_CALLABLE_DATA_REFERENCE_2026-03-07.md`
