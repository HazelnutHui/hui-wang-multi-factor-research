"""
Factor Factory: standardize cross-sectional signals with consistent rules.
"""

from __future__ import annotations

from typing import Optional, Dict, Iterable, List
import numpy as np
import pandas as pd


def zscore_series(s: pd.Series) -> pd.Series:
    std = s.std(ddof=0)
    if std and not np.isnan(std) and std > 0:
        return (s - s.mean()) / std
    return s * np.nan


def winsorize_series(s: pd.Series, z: Optional[float]) -> pd.Series:
    if z is None:
        return s
    zf = float(z)
    if np.isnan(zf):
        return s
    return s.clip(lower=-zf, upper=zf)


def winsorize_series_pct(s: pd.Series, low: Optional[float], high: Optional[float]) -> pd.Series:
    if low is None or high is None:
        return s
    try:
        low_q = float(low)
        high_q = float(high)
    except Exception:
        return s
    if np.isnan(low_q) or np.isnan(high_q):
        return s
    if low_q <= 0 or high_q >= 1 or low_q >= high_q:
        return s
    lo = s.quantile(low_q)
    hi = s.quantile(high_q)
    return s.clip(lower=lo, upper=hi)


def lag_date(date: str, lag_days: Optional[int]) -> str:
    if not lag_days:
        return date
    d = pd.Timestamp(date) - pd.Timedelta(days=int(lag_days))
    return d.strftime("%Y-%m-%d")


def resolve_factor_date(signal_date: str, global_lag: Optional[int], factor_lag: Optional[int]) -> str:
    if factor_lag is not None:
        return lag_date(signal_date, factor_lag)
    return lag_date(signal_date, global_lag)


def industry_neutral_zscore(
    df: pd.DataFrame,
    value_col: str,
    industry_map: Dict[str, str],
    industry_col: str,
    min_group: int,
) -> pd.Series:
    df = df.copy()
    df[industry_col] = df["symbol"].map(industry_map)
    z = pd.Series(index=df.index, dtype=float)
    for key, grp in df.groupby(industry_col):
        if pd.isna(key) or len(grp) < int(min_group):
            continue
        g = grp[value_col]
        gstd = g.std(ddof=0)
        if gstd and not np.isnan(gstd) and gstd > 0:
            z.loc[grp.index] = (g - g.mean()) / gstd
    if z.isna().any():
        z = z.fillna(zscore_series(df[value_col]))
    return z


def _zscore_safe(s: pd.Series) -> pd.Series:
    std = s.std(ddof=0)
    if std and not np.isnan(std) and std > 0:
        return (s - s.mean()) / std
    return s * 0.0


def neutralize_signal(
    df: pd.DataFrame,
    value_col: str,
    industry_map: Optional[Dict[str, str]] = None,
    industry_col: str = "industry",
    industry_min_group: int = 5,
    neutralize_cols: Optional[Iterable[str]] = None,
) -> pd.Series:
    if df is None or len(df) == 0:
        return pd.Series(dtype=float)

    work = df.copy()
    y = work[value_col].astype(float)

    # Build numeric exposures
    num_cols: List[str] = []
    if neutralize_cols:
        for c in neutralize_cols:
            if c in work.columns:
                num_cols.append(c)

    X_parts = []
    if num_cols:
        num_df = work[num_cols].apply(pd.to_numeric, errors="coerce")
        num_df = num_df.apply(_zscore_safe, axis=0)
        X_parts.append(num_df)

    # Industry dummies (optional)
    if industry_map:
        work[industry_col] = work["symbol"].map(industry_map)
        counts = work[industry_col].value_counts(dropna=True)
        keep = set(counts[counts >= int(industry_min_group)].index)
        ind = work[industry_col].where(work[industry_col].isin(keep), other=np.nan)
        if ind.notna().any():
            dummies = pd.get_dummies(ind, prefix="ind", drop_first=True)
            if len(dummies.columns) > 0:
                X_parts.append(dummies.astype(float))

    if not X_parts:
        return y

    X = pd.concat(X_parts, axis=1)

    # Build regression sample
    mask = y.notna()
    for c in X.columns:
        mask &= X[c].notna()

    if mask.sum() < max(20, len(X.columns) + 5):
        return y

    X_use = X.loc[mask]
    y_use = y.loc[mask]

    X_mat = np.column_stack([np.ones(len(X_use)), X_use.values])
    try:
        beta, _, _, _ = np.linalg.lstsq(X_mat, y_use.values, rcond=None)
    except Exception:
        return y

    y_hat = (X_mat @ beta)
    resid = y_use.values - y_hat
    out = pd.Series(index=work.index, dtype=float)
    out.loc[mask] = resid
    return out


def standardize_signal(
    df: pd.DataFrame,
    value_col: str = "signal",
    use_zscore: bool = False,
    use_rank: bool = False,
    rank_method: str = "average",
    rank_pct: bool = True,
    winsor_z: Optional[float] = None,
    winsor_pct_low: Optional[float] = None,
    winsor_pct_high: Optional[float] = None,
    industry_neutral: bool = False,
    industry_map: Optional[Dict[str, str]] = None,
    industry_col: str = "industry",
    industry_min_group: int = 5,
    neutralize_cols: Optional[Iterable[str]] = None,
    missing_policy: str = "drop",
    fill_value: Optional[float] = None,
) -> pd.DataFrame:
    if df is None or len(df) == 0:
        return df

    # Missing handling
    if missing_policy == "drop":
        df = df.dropna(subset=[value_col])
    elif missing_policy == "fill":
        df[value_col] = df[value_col].fillna(fill_value)
    elif missing_policy == "keep":
        pass
    else:
        raise ValueError(f"unknown missing_policy: {missing_policy}")

    if len(df) == 0:
        return df

    # Percentile winsor (optional, applied before rank/zscore)
    if winsor_pct_low is not None and winsor_pct_high is not None:
        df[value_col] = winsorize_series_pct(df[value_col], winsor_pct_low, winsor_pct_high)

    # Rank transform (optional)
    if use_rank:
        df[value_col] = df[value_col].rank(method=rank_method, pct=rank_pct)
        return df

    if not use_zscore:
        return df

    if neutralize_cols is not None and not isinstance(neutralize_cols, list):
        neutralize_cols = list(neutralize_cols)

    if industry_neutral or (neutralize_cols is not None and len(neutralize_cols) > 0):
        resid = neutralize_signal(
            df,
            value_col=value_col,
            industry_map=industry_map if industry_neutral else None,
            industry_col=industry_col,
            industry_min_group=industry_min_group,
            neutralize_cols=neutralize_cols,
        )
        df[value_col] = resid
        df[value_col] = zscore_series(df[value_col])
    else:
        df[value_col] = zscore_series(df[value_col])

    df[value_col] = winsorize_series(df[value_col], winsor_z)
    return df
