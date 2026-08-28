from datetime import timedelta
import pandas as pd


def predict(df: pd.DataFrame, horizon_weeks: int = 4, n_reference_weeks: int = 4) -> pd.DataFrame:
    """
    df must have columns: Erkrankung (str), date (datetime), Inzidenz (float)
    Returns DataFrame with the same columns, one row per (Erkrankung, forecast step).
    Raises ValueError if the input is empty.
    """
    if df.empty:
        raise ValueError("input is empty; cannot produce a forecast")
    rows = []
    for erkrankung, group in df.groupby("Erkrankung"):
        group = group.sort_values("date")
        reference = group.tail(n_reference_weeks)
        mean_inzidenz = reference["Inzidenz"].mean()
        if pd.isna(mean_inzidenz):
            raise ValueError(
                f"reference window for '{erkrankung}' contains non-finite "
                "Inzidenz values; cannot produce a forecast"
            )
        last_date = group["date"].iloc[-1]
        for w in range(1, horizon_weeks + 1):
            rows.append({
                "Erkrankung": erkrankung,
                "date": last_date + timedelta(weeks=w),
                "Inzidenz": round(mean_inzidenz, 2),
            })
    return pd.DataFrame(rows)
