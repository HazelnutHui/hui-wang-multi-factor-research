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

Alert channel selftest (dedupe + payload contract):
```bash
python scripts/test_scheduler_alert_channels.py
```

Final closure check:
```bash
python scripts/run_system_closure_check.py
```

## Safety Controls

1. lock file prevents concurrent scheduler instances
2. heartbeat json records running/stopped status
3. optional stop on orchestrator failure
4. optional webhook + command alert channels on failure
5. optional email alert channel on failure
6. alert dedupe window prevents repeated noisy alerts for same failure pattern
7. structured alert payload includes run metadata and recent failure summary

## Outputs

- `audit/auto_research/auto_research_scheduler_heartbeat.json`
- `audit/auto_research/auto_research_scheduler_ledger.csv`
- `audit/auto_research/auto_research_scheduler_ledger.md`
- `audit/auto_research/auto_research_scheduler_alert_state.json`
- `audit/auto_research/<ts>_alert_selftest/scheduler_alert_selftest_report.json`
- `audit/auto_research/<ts>_alert_selftest/scheduler_alert_selftest_report.md`

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
- `alert_recent_failures_limit`
- `alert_email_enabled`
- `alert_email_smtp_host`
- `alert_email_smtp_port`
- `alert_email_use_ssl`
- `alert_email_use_starttls`
- `alert_email_timeout_seconds`
- `alert_email_from`
- `alert_email_to`
- `alert_email_subject_prefix`
- `alert_email_username_env`
- `alert_email_password_env`
- `alert_email_dry_run`
- `alert_email_dry_run_dir`
- `alert_command`

## Alert Payload Contract

Webhook `payload` and `AUTO_RESEARCH_ALERT_JSON` include:
1. scheduler cycle metadata (`cycle`, `scheduler_policy_json`)
2. orchestrator execution metadata (`orchestrator_policy_json`, `orchestrator_execute`)
3. failure metadata (`rc`, `stopped_reason`, `run_dir`, `orchestrator_report_json`)
4. `recent_failures` list from scheduler ledger (bounded by `alert_recent_failures_limit`)

For command channel:
1. `AUTO_RESEARCH_ALERT_MSG` carries human-readable message
2. `AUTO_RESEARCH_ALERT_JSON` carries structured JSON payload

For email channel:
1. SMTP credentials are read from env vars configured by `alert_email_username_env` and `alert_email_password_env`
2. `alert_email_dry_run=true` writes `.eml` files to `alert_email_dry_run_dir` without sending network traffic
