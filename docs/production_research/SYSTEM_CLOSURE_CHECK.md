# System Closure Check Standard

Last updated: 2026-02-21

Purpose:
- run one-command end-of-phase acceptance checks;
- generate a closure report suitable for handoff/audit.

## Script

- `scripts/run_system_closure_check.py`

## Usage

```bash
python scripts/run_system_closure_check.py
```

Optional (skip alert channel selftest):
```bash
python scripts/run_system_closure_check.py --skip-alert-selftest
```

## Outputs

- `audit/system_closure/<ts>_closure/system_closure_report.json`
- `audit/system_closure/<ts>_closure/system_closure_report.md`

## Included Checks

1. session handoff readiness check
2. scheduler alert channel selftest (dedupe + payload contract)
