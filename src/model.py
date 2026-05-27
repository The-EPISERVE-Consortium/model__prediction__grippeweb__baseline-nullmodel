from datetime import datetime, timedelta
import pandas as pd

GROUP_COLS = ["Erkrankung", "Altersgruppe", "Region"]


def parse_kalenderwoche(kw_str: str):
    try:
        return datetime.strptime(kw_str + "-1", "%Y-W%W-%w")
    except ValueError:
        return None


def predict(df: pd.DataFrame, horizon_weeks: int = 4, n_reference_weeks: int = 4) -> pd.DataFrame:
    df = df.copy()
    df["_date"] = df["Kalenderwoche"].apply(parse_kalenderwoche)
    df = df.dropna(subset=["_date"]).sort_values("_date")

    rows = []
    for keys, group in df.groupby(GROUP_COLS):
        group = group.sort_values("_date")
        reference = group.tail(n_reference_weeks)

        mean_meldungen = reference["Meldungen"].mean()
        mean_inzidenz = reference["Inzidenz"].mean()
        last_saison = group["Saison"].iloc[-1]
        last_date = group["_date"].iloc[-1]

        for w in range(1, horizon_weeks + 1):
            future_date = last_date + timedelta(weeks=w)
            rows.append({
                "Meldungen": round(mean_meldungen, 2),
                "Saison": last_saison,
                "Erkrankung": keys[0],
                "Altersgruppe": keys[1],
                "Region": keys[2],
                "Kalenderwoche": future_date.strftime("%Y-W%W"),
                "Inzidenz": round(mean_inzidenz, 2),
                "Modell": "baseline-nullmodel",
                "Horizont_Wochen": w,
            })

    return pd.DataFrame(rows)
