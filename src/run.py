import json
import sys
import pandas as pd
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
from model import predict

INPUT  = Path("/work/input")
OUTPUT = Path("/work/output")

FIXED_REGION      = "Bundesweit"
FIXED_ALTERSGRUPPE = "15-34"

# ── Load config ───────────────────────────────────────────────────────────────
config_path = INPUT / "config.json"
if not config_path.exists():
    print("ERROR: /work/input/config.json not found", file=sys.stderr)
    sys.exit(1)

config        = json.loads(config_path.read_text())
horizon_weeks = int(config.get("horizon_weeks", 4))
n_reference   = int(config.get("n_reference_weeks", 4))

print(f"Config: horizon={horizon_weeks} weeks, reference={n_reference} weeks")

# ── Load data ─────────────────────────────────────────────────────────────────
data_path = INPUT / "data.tsv"
if not data_path.exists():
    print("ERROR: /work/input/data.tsv not found", file=sys.stderr)
    sys.exit(1)

df = pd.read_csv(data_path, sep="\t")
print(f"Loaded {len(df)} rows")

required_cols = {"Erkrankung", "Altersgruppe", "Region", "Kalenderwoche", "Inzidenz"}
missing = required_cols - set(df.columns)
if missing:
    print(f"ERROR: Missing columns: {missing}", file=sys.stderr)
    sys.exit(1)

# ── Convert: filter stratum, parse dates ──────────────────────────────────────
df = df[(df["Region"] == FIXED_REGION) & (df["Altersgruppe"] == FIXED_ALTERSGRUPPE)]
df["date"] = pd.to_datetime(
    df["Kalenderwoche"].apply(lambda kw: datetime.strptime(kw + "-1", "%Y-W%W-%w")),
    errors="coerce",
)
df = df.dropna(subset=["date"])

# ── Predict ───────────────────────────────────────────────────────────────────
predictions = predict(
    df[["Erkrankung", "date", "Inzidenz"]],
    horizon_weeks=horizon_weeks,
    n_reference_weeks=n_reference,
)

# ── Convert to output format ──────────────────────────────────────────────────
out_df = predictions.copy()
out_df["Datum"] = out_df["date"].dt.strftime("%Y-%m-%d")
out_df = out_df[["Datum", "Erkrankung", "Inzidenz"]]

# ── Write output ──────────────────────────────────────────────────────────────
OUTPUT.mkdir(parents=True, exist_ok=True)
out_path = OUTPUT / "predictions.tsv"
out_df.to_csv(out_path, sep="\t", index=False)

print(f"Written {len(out_df)} prediction rows to {out_path}")
print("Done.")
