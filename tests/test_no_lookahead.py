import pandas as pd
import numpy as np

from backtest.factor_factory import standardize_signal


def test_standardize_is_cross_sectional_only():
    # Two dates: signals should be standardized within each date only
    df = pd.DataFrame({
        "symbol": ["A", "B", "C", "A", "B", "C"],
        "date": ["2020-01-01"] * 3 + ["2020-01-02"] * 3,
        "signal": [1.0, 2.0, 3.0, 10.0, 20.0, 30.0],
    })

    out = df.copy()
    # Apply per-date standardization (simulate how engine uses it)
    out_list = []
    for d, g in out.groupby("date"):
        out_list.append(standardize_signal(g.copy(), use_zscore=True, use_rank=False))
    out = pd.concat(out_list, ignore_index=True)

    # Each date group should have mean ~0, std ~1
    for d, g in out.groupby("date"):
        assert np.isclose(g["signal"].mean(), 0.0, atol=1e-12)
        assert np.isclose(g["signal"].std(ddof=0), 1.0, atol=1e-12)
