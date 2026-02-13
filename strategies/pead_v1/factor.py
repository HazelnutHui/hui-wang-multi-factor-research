import pandas as pd
import numpy as np

# IMPORTANT: we reuse your existing CachedPEADFactor implementation
# It should provide:
#   - get_earnings(symbol) -> DataFrame
#   - calculate_sue(earnings_df) -> DataFrame with ['date','sue','surprise_std',...]
from backtest.pead_factor_cached import CachedPEADFactor

class ShiftedPEADFactor(CachedPEADFactor):
    """
    PEAD factor with date shift, plus SUE-table caching for performance.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Cache: symbol -> earnings_sue df
        self._sue_table_cache = {}
        # Cache: symbol -> dict(date -> row)
        self._sue_map_cache = {}
        # Signal date shift (days)
        self.date_shift_days = 1

    def _get_sue_table(self, symbol: str) -> pd.DataFrame:
        if symbol in self._sue_table_cache:
            return self._sue_table_cache[symbol]

        earnings = self.get_earnings(symbol)
        if earnings is None or len(earnings) == 0:
            self._sue_table_cache[symbol] = pd.DataFrame()
            self._sue_map_cache[symbol] = {}
            return self._sue_table_cache[symbol]

        tbl = self.calculate_sue(earnings)
        if tbl is None or len(tbl) == 0:
            self._sue_table_cache[symbol] = pd.DataFrame()
            self._sue_map_cache[symbol] = {}
            return self._sue_table_cache[symbol]

        tbl = tbl.copy()
        tbl['date'] = pd.to_datetime(tbl['date'])
        self._sue_table_cache[symbol] = tbl

        # Build map for O(1) lookup
        m = {}
        for _, r in tbl.iterrows():
            d = r['date']
            if pd.isna(d):
                continue
            m[pd.Timestamp(d)] = r
        self._sue_map_cache[symbol] = m

        return tbl

    def get_sue_raw(self, symbol: str, date: str):
        """
        Raw SUE check without threshold filter.

        Returns:
          {
            'has_event': bool,
            'sue': float | None,
            'reason': str
          }
        """
        date_ts = pd.Timestamp(date)
        target_date = date_ts + pd.Timedelta(days=int(self.date_shift_days))

        tbl = self._get_sue_table(symbol)
        if tbl is None or len(tbl) == 0:
            return {'has_event': False, 'sue': None, 'reason': 'no_earnings_data'}

        m = self._sue_map_cache.get(symbol, {})
        row = m.get(pd.Timestamp(target_date))
        if row is None:
            return {'has_event': False, 'sue': None, 'reason': 'no_event_on_date'}

        sue_value = row.get('sue', np.nan)
        if pd.isna(sue_value):
            # Diagnose why NaN
            stdv = row.get('surprise_std', np.nan)
            if pd.isna(stdv):
                reason = 'lookback_insufficient'
            else:
                reason = 'std_nan'
            return {'has_event': True, 'sue': None, 'reason': reason}

        return {'has_event': True, 'sue': float(sue_value), 'reason': 'ok'}

    def get_sue_signal(self, symbol: str, date: str):
        """
        Thresholded SUE used by factor engine.
        """
        info = self.get_sue_raw(symbol, date)
        if not info['has_event'] or info['sue'] is None:
            return None
        sue = info['sue']
        if abs(sue) > self.sue_threshold:
            return sue
        return None
