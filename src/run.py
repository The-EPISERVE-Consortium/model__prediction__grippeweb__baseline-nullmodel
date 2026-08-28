import json
import sys
import pandas as pd
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
from model import predict

_work  = Path("./work") if Path("./work").exists() else Path("/work")
INPUT  = _work / "input"
OUTPUT = _work / "output"

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

if horizon_weeks <= 0 or n_reference <= 0:
    print(
        "ERROR: config horizon_weeks and n_reference_weeks must both be > 0 "
        f"(got horizon={horizon_weeks}, reference={n_reference})",
        file=sys.stderr,
    )
    sys.exit(1)

print(f"Config: horizon={horizon_weeks} weeks, reference={n_reference} weeks")

# ── Load data ─────────────────────────────────────────────────────────────────
data_path = INPUT / "input.parquet"
if not data_path.exists():
    print("ERROR: /work/input/input.parquet not found", file=sys.stderr)
    sys.exit(1)

df = pd.read_parquet(data_path)
print(f"Loaded {len(df)} rows")

required_cols = {"Erkrankung", "Altersgruppe", "Region", "Kalenderwoche", "Inzidenz"}
missing = required_cols - set(df.columns)
if missing:
    print(f"ERROR: Missing columns: {missing}", file=sys.stderr)
    sys.exit(1)

# ── Convert: filter stratum, parse dates ──────────────────────────────────────
df = df[(df["Region"] == FIXED_REGION) & (df["Altersgruppe"] == FIXED_ALTERSGRUPPE)]
# Parse each Kalenderwoche (YYYY-WNN) as the Monday of the true ISO week,
# using %G (ISO year) and %V (ISO week number) to stay correct across
# year boundaries instead of the Monday-based %W week-of-year.
df["date"] = pd.to_datetime(
    df["Kalenderwoche"].apply(lambda kw: datetime.strptime(kw + "-1", "%G-W%V-%w"))
)

# A malformed Kalenderwoche raises above (strptime has no coerce); if the
# filtered/parsed dataset is empty, fail loudly instead of writing a
# header-only output that the platform would treat as a successful forecast.
if len(df) == 0:
    print(
        f"ERROR: no rows for region={FIXED_REGION}, "
        f"altersgruppe={FIXED_ALTERSGRUPPE} after filtering and parsing",
        file=sys.stderr,
    )
    sys.exit(1)

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
