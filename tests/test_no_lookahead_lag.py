import pandas as pd

from backtest.factor_engine import FactorEngine
from backtest.data_engine import DataEngine
from backtest.universe_builder import UniverseBuilder


class _StubDataEngine(DataEngine):
    def __init__(self, df_by_symbol):
        self._df_by_symbol = df_by_symbol

    def get_price(self, symbol, start_date=None, end_date=None):
        df = self._df_by_symbol.get(symbol)
        if df is None:
            return None
        if start_date is None and end_date is None:
            return df.copy()
        out = df.copy()
        if start_date is not None:
            out = out[out["date"] >= pd.Timestamp(start_date)]
        if end_date is not None:
            out = out[out["date"] <= pd.Timestamp(end_date)]
        return out.reset_index(drop=True)


class _StubUniverseBuilder(UniverseBuilder):
    def __init__(self, data_engine, symbols):
        super().__init__(data_engine, min_market_cap=0, min_dollar_volume=0, min_price=0)
        self._symbols = symbols

    def get_universe(self, date):
        return list(self._symbols)


def test_factor_lag_prevents_lookahead():
    # Construct a price series with a huge jump on 2020-01-03.
    dates = pd.to_datetime(["2020-01-01", "2020-01-02", "2020-01-03"])
    df = pd.DataFrame({
        "date": dates,
        "open": [10.0, 10.0, 1000.0],
        "close": [10.0, 10.0, 1000.0],
        "volume": [1e6, 1e6, 1e6],
    })
    data_engine = _StubDataEngine({"AAA": df})
    universe_builder = _StubUniverseBuilder(data_engine, ["AAA"])

    config = {
        "MOMENTUM_LOOKBACK": 1,
        "MOMENTUM_SKIP": 0,
        "MOMENTUM_USE_MONTHLY": False,
        "MOMENTUM_ZSCORE": False,
        "FACTOR_LAG_DAYS": 1,
        "MIN_MARKET_CAP": 0,
        "MIN_DOLLAR_VOLUME": 0,
        "MIN_PRICE": 0,
    }

    fe = FactorEngine(data_engine, universe_builder, config)

    # Signal date is 2020-01-03, but factor should be computed using 2020-01-02 (lag=1)
    factors = fe.calculate_all_factors("AAA", "2020-01-03")
    assert factors["momentum"] == 0.0
