# episerve-model-forecast-corona

Zero-model forecast container for EPISERVE.

Reads the GrippeWeb weekly report table (parquet), predicts the next N weeks
by averaging the last M reference weeks per disease.

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

Both are optional integers ≥ 1, default 4.

## Model card

[`fdo.json`](fdo.json) is the model card, following the EPISERVE
[model-card v1 spec](https://github.com/The-EPISERVE-Consortium/episerve_specs/blob/main/src/episerve_specs/specs/model_card/README.md):
parameters (`episerve:parameters`, a JSON Schema of `config.json`), input and
output files with their columns, resources and documentation. CI checks it
(job `model-card`); locally:

```bash
pip install "git+https://github.com/The-EPISERVE-Consortium/episerve_specs@v0.3.0"
episerve-validate fdo.json
```

The platform reads the card from this repository: the sync flow stores its
sections in the catalog, and the API checks a run's config against
`episerve:parameters` before starting it.

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
