# episerve-model-forecast-corona

Zero-model forecast container for EPISERVE.

Reads a TSV timeseries of disease reports, predicts the next N weeks
by averaging the last M reference weeks per group.

## I/O Contract

| Path | Description |
|---|---|
| `/work/input/config.json` | Run parameters |
| `/work/input/input.parquet` | Input timeseries |
| `/work/output/predictions.tsv` | Forecast output |

### config.json

```json
{
  "horizon_weeks": 4,
  "n_reference_weeks": 4
}
```

## Local Testing

```bash
docker build -t episerve/forecast-corona:dev .

docker run --rm \
  -v $(pwd)/input:/work/input \
  -v $(pwd)/output:/work/output \
  episerve/forecast-corona:dev
```

## Output Format

Each row is one forecast step:
- `Datum` — ISO date (YYYY-MM-DD)
- `Erkrankung` — disease group
- `Inzidenz` — predicted incidence (rounded to 2 decimals)
