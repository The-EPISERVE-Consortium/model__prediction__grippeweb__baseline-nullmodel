# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Docker-based forecast container for the **EPISERVE** disease surveillance platform. It implements a **baseline null model**: for each `(Erkrankung, Altersgruppe, Region)` group, it predicts the next N weeks by repeating the mean of the last M observed weeks.

Repository name follows the convention `model__<type>__<dataset>__<variant>`. Published image: `ghcr.io/the-episerve-consortium/model__prediction__grippeweb__baseline-nullmodel`.

## I/O Contract

Every EPISERVE model container reads from and writes to fixed paths. The platform populates input before the container starts and reads output after it exits (exit code 0 = success).

| Path | Direction | Description |
|---|---|---|
| `/work/input/config.json` | → into container | `horizon_weeks`, `n_reference_weeks` |
| `/work/input/data.tsv` | → into container | Input timeseries (tab-separated) |
| `/work/output/predictions.tsv` | ← out of container | Forecast results |

## Commands

```bash
# Install dependencies
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Run tests (local, no Docker)
pytest tests/ -v

# Run a single test
pytest tests/test_model.py::test_mean_values_correct -v

# Build and test with Docker (matches K8s runtime exactly)
docker build -t episerve/forecast-corona:dev .
docker run --rm \
  -v $(pwd)/input:/work/input \
  -v $(pwd)/output:/work/output \
  episerve/forecast-corona:dev
```

## Architecture

| File | Role |
|---|---|
| `src/model.py` | Pure `predict(df, horizon_weeks, n_reference_weeks)` function — no I/O, fully unit-testable |
| `src/run.py` | Docker entrypoint: reads `/work/input/`, runs prediction logic inline, writes `/work/output/predictions.tsv` |
| `tests/test_model.py` | Unit tests covering row count, columns, Modell label, horizon values, mean calculation, Kalenderwoche format |


## Data format

Input TSV columns: `Meldungen`, `Saison`, `Erkrankung`, `Altersgruppe`, `Region`, `Kalenderwoche`, `Inzidenz`

- `Kalenderwoche` format: `YYYY-WWW` (e.g. `"2011-W22"`) — parsed as Monday of that ISO week
- Groups: `(Erkrankung, Altersgruppe, Region)`

Output adds: `Modell` (identifier string), `Horizont_Wochen` (1-based week offset).

## Release

```bash
git tag v0.2.0
git push origin v0.2.0
```

CI (`.github/workflows/publish.yml`) builds the Docker image, runs `pytest tests/ -v` inside the built image, and pushes to GHCR:
- `push` to `master` → `:latest`
- `v*` tag → `:vX.Y.Z` + `:latest`

The image is only published if all tests pass inside the built image.

## Running on Kubernetes manually

Use `run-model.sh` (not checked in to this repo — lives in the platform tooling):

```bash
./run-model.sh \
  -i ghcr.io/the-episerve-consortium/model__prediction__grippeweb__baseline-nullmodel \
  -t v0.1.0 \
  -c ./input/config.json \
  -d ./input/data.tsv \
  -n episerve
```

The script creates a `ConfigMap` from the input files, submits a Kubernetes `Job`, waits for completion (5-minute timeout), copies `/work/output/` to `./output-<jobname>/` locally, prints logs, and cleans up. The Job auto-deletes after 10 minutes.

## Adding a new model

1. Create repo `The-EPISERVE-Consortium/model__prediction__<dataset>__<variant>`
2. Copy the structure from an existing model
3. Replace `src/model.py` with new logic — keep the same `predict()` signature
4. Update `src/run.py` if the input/output format differs
5. Write tests in `tests/test_model.py`
6. Tag a release: `git tag v0.1.0 && git push origin v0.1.0`
