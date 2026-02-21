# Auto Research Scheduler Standard

Last updated: 2026-02-21

Purpose:
- run `auto_research_orchestrator` continuously by policy schedule;
- provide lock/heartbeat/ledger and failure alert controls;
- support unattended operations with deterministic audit trace.

## Components

- `scripts/auto_research_scheduler.py`
- `configs/research/auto_research_scheduler_policy.json`

## Standard Usage

Run once (smoke check):
```bash
python scripts/auto_research_scheduler.py --run-once
```

Run by policy cadence:
```bash
python scripts/auto_research_scheduler.py
```

## Safety Controls

1. lock file prevents concurrent scheduler instances
2. heartbeat json records running/stopped status
3. optional stop on orchestrator failure
4. optional webhook + command alert channels on failure
5. alert dedupe window prevents repeated noisy alerts for same failure pattern

## Outputs

- `audit/auto_research/auto_research_scheduler_heartbeat.json`
- `audit/auto_research/auto_research_scheduler_ledger.csv`
- `audit/auto_research/auto_research_scheduler_ledger.md`
- `audit/auto_research/auto_research_scheduler_alert_state.json`

## Policy Keys

- `interval_seconds`
- `max_cycles`
- `stop_on_orchestrator_failure`
- `orchestrator_policy_json`
- `orchestrator_execute`
- `lock_file`
- `heartbeat_json`
- `ledger_csv`
- `ledger_md`
- `alert_on_failure`
- `alert_state_json`
- `alert_dedupe_window_seconds`
- `alert_webhook_url`
- `alert_webhook_timeout_seconds`
- `alert_command`
