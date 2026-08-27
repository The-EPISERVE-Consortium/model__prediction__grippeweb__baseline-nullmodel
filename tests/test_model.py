import sys
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from model import predict


def make_sample(erkrankungen=("ARE", "ILI"), n_weeks=4):
    start = datetime(2011, 5, 30)  # a Monday
    rows = []
    inzidenz = {"ARE": [28065, 27000, 26000, 25000], "ILI": [5267, 5100, 4900, 4700]}
    for w in range(n_weeks):
        date = start + timedelta(weeks=w)
        for erk in erkrankungen:
            rows.append({"Erkrankung": erk, "date": date, "Inzidenz": inzidenz[erk][w]})
    return pd.DataFrame(rows)


SAMPLE = make_sample()


def test_output_row_count():
    result = predict(SAMPLE, horizon_weeks=4, n_reference_weeks=4)
    assert len(result) == 4 * SAMPLE["Erkrankung"].nunique()


def test_output_columns():
    result = predict(SAMPLE, horizon_weeks=2, n_reference_weeks=2)
    assert set(result.columns) == {"Erkrankung", "date", "Inzidenz"}


def test_rows_per_erkrankung():
    horizon = 3
    result = predict(SAMPLE, horizon_weeks=horizon, n_reference_weeks=2)
    for erkrankung, gdf in result.groupby("Erkrankung"):
        assert len(gdf) == horizon


def test_mean_values_correct():
    result = predict(SAMPLE, horizon_weeks=1, n_reference_weeks=2)
    # last 2 weeks of ARE: 26000 and 25000 → mean = 25500
    row = result[result["Erkrankung"] == "ARE"].iloc[0]
    assert row["Inzidenz"] == 25500.0


def test_single_reference_week():
    result = predict(SAMPLE, horizon_weeks=2, n_reference_weeks=1)
    # last week of ILI: 4700
    rows = result[result["Erkrankung"] == "ILI"]
    assert (rows["Inzidenz"] == 4700.0).all()


def test_future_dates_are_mondays():
    result = predict(SAMPLE, horizon_weeks=4, n_reference_weeks=2)
    assert (result["date"].dt.weekday == 0).all()


def test_future_dates_advance_weekly():
    result = predict(SAMPLE, horizon_weeks=4, n_reference_weeks=2)
    for _, gdf in result.groupby("Erkrankung"):
        dates = sorted(gdf["date"].tolist())
        gaps = [(dates[i+1] - dates[i]).days for i in range(len(dates) - 1)]
        assert all(g == 7 for g in gaps)


def test_nan_reference_raises():
    # NaN in the reference window must not silently propagate into the forecast
    bad = SAMPLE.copy()
    are = bad["Erkrankung"] == "ARE"
    last_are_date = sorted(bad.loc[are, "date"].tolist())[-1]
    bad.loc[are & (bad["date"] == last_are_date), "Inzidenz"] = float("nan")
    with pytest.raises(ValueError):
        predict(bad, horizon_weeks=2, n_reference_weeks=1)
