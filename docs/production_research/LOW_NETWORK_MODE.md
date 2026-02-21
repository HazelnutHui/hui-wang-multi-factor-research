# Low-Network Mode Standard

Last updated: 2026-02-21

Purpose:
- keep auto-research operations mostly offline;
- avoid real outbound alerts while preserving local auditability.

## Policy Profile

- `configs/research/auto_research_scheduler_policy.low_network.json`

Characteristics:
1. webhook disabled
2. smtp host empty (no real email send)
3. email channel in dry-run mode (writes `.eml` only)
4. local alert command writes to `audit/auto_research/local_alert.log`

## One-Command Switch

```bash
bash scripts/switch_auto_research_mode.sh --mode low-network
```

Restore standard mode:
```bash
bash scripts/switch_auto_research_mode.sh --mode standard
```

Each switch writes audit files under:
- `audit/auto_research/mode_switch/`
