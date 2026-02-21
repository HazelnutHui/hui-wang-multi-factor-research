# Auto Research Deployment Standard

Last updated: 2026-02-21

Purpose:
- standardize unattended deployment of scheduler/orchestrator on workstation;
- enforce service-level restart behavior and auditable operations.

## Scope

- Linux workstation with `systemd --user`
- scheduler service deployment:
  - `scripts/install_auto_research_scheduler_service.sh`
  - `scripts/manage_auto_research_scheduler_service.sh`

## Install (User Service)

```bash
cd ~/projects/hui-wang-multi-factor-research
bash scripts/install_auto_research_scheduler_service.sh \
  --repo-root "$(pwd)" \
  --policy-json configs/research/auto_research_scheduler_policy.json \
  --enable-now
```

Generated files:
1. `~/.config/systemd/user/auto-research-scheduler.service`
2. `~/.config/auto-research-scheduler/auto-research-scheduler.env`

## Service Operations

```bash
bash scripts/manage_auto_research_scheduler_service.sh --action status
bash scripts/manage_auto_research_scheduler_service.sh --action logs --lines 120
bash scripts/manage_auto_research_scheduler_service.sh --action restart
```

## Credential Injection (Email Alerts)

Edit env file:
`~/.config/auto-research-scheduler/auto-research-scheduler.env`

Example:
```bash
AUTO_RESEARCH_SMTP_USER=your_smtp_user
AUTO_RESEARCH_SMTP_PASS=your_smtp_pass
```

Then restart service:
```bash
bash scripts/manage_auto_research_scheduler_service.sh --action restart
```

## Runtime Audit Paths

1. `audit/auto_research/auto_research_scheduler_heartbeat.json`
2. `audit/auto_research/auto_research_scheduler_ledger.csv`
3. `audit/auto_research/auto_research_scheduler_ledger.md`
4. `audit/auto_research/auto_research_ledger.csv`
5. `audit/auto_research/auto_research_weekly_summary.md`

## Low-Network Mode (Recommended Default)

Before enabling unattended service, switch scheduler policy to low-network:
```bash
bash scripts/switch_auto_research_mode.sh --mode low-network
```

## Rollback

```bash
bash scripts/manage_auto_research_scheduler_service.sh --action disable
rm -f ~/.config/systemd/user/auto-research-scheduler.service
systemctl --user daemon-reload
```
