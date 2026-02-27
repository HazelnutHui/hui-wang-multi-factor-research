#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backtest.backtest_engine import BacktestEngine
from scripts.run_with_config import (
    _build_engine_config,
    _deep_merge,
    _load_yaml,
    _validate_weights,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate live-style latest-date signal snapshot (no full train/test run)."
    )
    parser.add_argument("--strategy", required=True, help="Path to strategy yaml")
    parser.add_argument(
        "--protocol",
        default=str((ROOT / "configs" / "protocol.yaml").resolve()),
        help="Path to protocol yaml",
    )
    args = parser.parse_args()

    protocol_path = Path(args.protocol).resolve()
    strategy_path = Path(args.strategy).resolve()
    protocol = _load_yaml(protocol_path)
    strategy = _load_yaml(strategy_path)
    merged = _deep_merge(protocol, strategy)

    engine_cfg = _build_engine_config(merged, protocol_path.parent)
    weights = _validate_weights(merged.get("factors", {}).get("weights", {}))
    engine = BacktestEngine(engine_cfg)

    periods = merged.get("backtest_periods", {})
    start_date = periods.get("test_start") or periods.get("train_start")
    end_date = periods.get("test_end") or datetime.now(timezone.utc).date().isoformat()
    if not start_date:
        raise SystemExit("missing start date in strategy/protocol config")

    cal = engine._get_trading_calendar(start_date, end_date)
    if cal is None or len(cal) == 0:
        raise SystemExit("no trading calendar dates available for snapshot")
    signal_date = cal[-1].strftime("%Y-%m-%d")

    signals_df = engine._compute_signals_cached(signal_date, weights)
    if signals_df is None:
        raise SystemExit("failed to compute signals")

    strategy_meta = merged.get("strategy", {})
    output_dir = strategy_meta.get("output_dir", "strategies/run_with_config")
    out_root = (ROOT / output_dir).resolve()
    results_dir = out_root / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    snap_path = results_dir / f"live_signals_{ts}.csv"
    latest_path = results_dir / "test_signals_latest.csv"

    signals_df.to_csv(snap_path, index=False)
    signals_df.to_csv(latest_path, index=False)

    print("=" * 70)
    print(f"{strategy_meta.get('name')} live snapshot")
    print("=" * 70)
    print(f"Signal date:       {signal_date}")
    print(f"Rows:              {len(signals_df)}")
    print(f"Saved snapshot:    {snap_path.relative_to(out_root)}")
    print(f"Updated latest:    {latest_path.relative_to(out_root)}")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
