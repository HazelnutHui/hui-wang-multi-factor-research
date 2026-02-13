from backtest.factor_factory import lag_date, resolve_factor_date


def test_lag_date_zero():
    assert lag_date("2020-01-15", 0) == "2020-01-15"


def test_lag_date_one():
    assert lag_date("2020-01-15", 1) == "2020-01-14"


def test_lag_date_five():
    assert lag_date("2020-01-15", 5) == "2020-01-10"


def test_resolve_factor_date_global():
    assert resolve_factor_date("2020-01-15", 2, None) == "2020-01-13"


def test_resolve_factor_date_override():
    assert resolve_factor_date("2020-01-15", 2, 5) == "2020-01-10"
