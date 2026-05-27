"""
Zero-model forecast: predicts the mean of the last n_reference weeks
for each combination of (Erkrankung, Altersgruppe, Region).
"""

import json
import sys
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

INPUT  = Path("/work/input")
OUTPUT = Path("/work/output")

# ── Load config ───────────────────────────────────────────────────────────────
config_path = INPUT / "config.json"
if not config_path.exists():
    print("ERROR: /work/input/config.json not found", file=sys.stderr)
    sys.exit(1)

config = json.loads(config_path.read_text())
horizon_weeks  = int(config.get("horizon_weeks", 4))
n_reference    = int(config.get("n_reference_weeks", 4))  # how many past weeks to average

print(f"Config: horizon={horizon_weeks} weeks, reference={n_reference} weeks")

# ── Load data ─────────────────────────────────────────────────────────────────
data_path = INPUT / "data.tsv"
if not data_path.exists():
    print("ERROR: /work/input/data.tsv not found", file=sys.stderr)
    sys.exit(1)

df = pd.read_csv(data_path, sep="\t")
print(f"Loaded {len(df)} rows")
print(f"Columns: {list(df.columns)}")

required_cols = {"Meldungen", "Saison", "Erkrankung", "Altersgruppe", "Region", "Kalenderwoche", "Inzidenz"}
missing = required_cols - set(df.columns)
if missing:
    print(f"ERROR: Missing columns: {missing}", file=sys.stderr)
    sys.exit(1)

# ── Parse Kalenderwoche into sortable dates ───────────────────────────────────
def parse_kw(kw_str):
    """Parse '2011-W22' into a datetime (Monday of that week)."""
    try:
        return datetime.strptime(kw_str + "-1", "%Y-W%W-%w")
    except ValueError:
        return None

df["date"] = df["Kalenderwoche"].apply(parse_kw)
df = df.dropna(subset=["date"])
df = df.sort_values("date")

# ── Zero model: mean of last n_reference weeks per group ──────────────────────
group_cols = ["Erkrankung", "Altersgruppe", "Region"]
predictions = []

for group_keys, group_df in df.groupby(group_cols):
    group_df = group_df.sort_values("date")
    reference = group_df.tail(n_reference)

    mean_meldungen = reference["Meldungen"].mean()
    mean_inzidenz  = reference["Inzidenz"].mean()
    last_saison    = group_df["Saison"].iloc[-1]
    last_date      = group_df["date"].iloc[-1]

    for w in range(1, horizon_weeks + 1):
        future_date = last_date + timedelta(weeks=w)
        kw_str = future_date.strftime("%Y-W%W")
        predictions.append({
            "Meldungen":      round(mean_meldungen, 2),
            "Saison":         last_saison,
            "Erkrankung":     group_keys[0],
            "Altersgruppe":   group_keys[1],
            "Region":         group_keys[2],
            "Kalenderwoche":  kw_str,
            "Inzidenz":       round(mean_inzidenz, 2),
            "Modell":         "zero-model",
            "Horizont_Wochen": w,
        })

out_df = pd.DataFrame(predictions)

# ── Write output ──────────────────────────────────────────────────────────────
OUTPUT.mkdir(parents=True, exist_ok=True)
out_path = OUTPUT / "predictions.tsv"
out_df.to_csv(out_path, sep="\t", index=False)

print(f"Written {len(out_df)} prediction rows to {out_path}")
print("Done.")
