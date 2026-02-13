import pandas as pd
import numpy as np

from backtest.factor_factory import standardize_signal, zscore_series, winsorize_series


def test_zscore_basic():
    s = pd.Series([1.0, 2.0, 3.0, 4.0])
    z = zscore_series(s)
    assert np.isclose(z.mean(), 0.0, atol=1e-12)
    assert np.isclose(z.std(ddof=0), 1.0, atol=1e-12)


def test_winsorize_basic():
    s = pd.Series([-5.0, -1.0, 0.0, 2.0, 10.0])
    w = winsorize_series(s, 2.0)
    assert w.min() >= -2.0
    assert w.max() <= 2.0


def test_standardize_noop_when_disabled():
    df = pd.DataFrame({
        "symbol": ["A", "B", "C"],
        "signal": [1.0, 2.0, 3.0],
    })
    out = standardize_signal(df.copy(), use_zscore=False, use_rank=False)
    pd.testing.assert_frame_equal(out, df)


def test_standardize_zscore_and_winsor():
    df = pd.DataFrame({
        "symbol": ["A", "B", "C", "D", "E"],
        "signal": [1.0, 2.0, 3.0, 100.0, -100.0],
    })
    out = standardize_signal(df.copy(), use_zscore=True, winsor_z=2.0)
    assert out["signal"].min() >= -2.0
    assert out["signal"].max() <= 2.0


def test_standardize_rank_pct():
    df = pd.DataFrame({
        "symbol": ["A", "B", "C", "D"],
        "signal": [10.0, 20.0, 30.0, 40.0],
    })
    out = standardize_signal(df.copy(), use_rank=True, rank_pct=True)
    assert out["signal"].min() >= 0.25
    assert out["signal"].max() <= 1.0


def test_missing_policy_fill():
    df = pd.DataFrame({
        "symbol": ["A", "B", "C"],
        "signal": [1.0, None, 3.0],
    })
    out = standardize_signal(
        df.copy(),
        use_rank=True,
        missing_policy="fill",
        fill_value=0.0,
    )
    assert out["signal"].isna().sum() == 0
