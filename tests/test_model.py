"""
Unit tests for the null model prediction logic.
"""

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from model import predict


SAMPLE_DATA = pd.DataFrame([
    {"Meldungen": 45,  "Saison": "2010/11", "Erkrankung": "ARE", "Altersgruppe": "0-4",  "Region": "Bundesweit", "Kalenderwoche": "2011-W22", "Inzidenz": 28065},
    {"Meldungen": 108, "Saison": "2010/11", "Erkrankung": "ARE", "Altersgruppe": "5-14", "Region": "Bundesweit", "Kalenderwoche": "2011-W22", "Inzidenz": 5267},
    {"Meldungen": 45,  "Saison": "2010/11", "Erkrankung": "ARE", "Altersgruppe": "0-4",  "Region": "Bundesweit", "Kalenderwoche": "2011-W23", "Inzidenz": 27000},
    {"Meldungen": 108, "Saison": "2010/11", "Erkrankung": "ARE", "Altersgruppe": "5-14", "Region": "Bundesweit", "Kalenderwoche": "2011-W23", "Inzidenz": 5100},
    {"Meldungen": 45,  "Saison": "2010/11", "Erkrankung": "ARE", "Altersgruppe": "0-4",  "Region": "Bundesweit", "Kalenderwoche": "2011-W24", "Inzidenz": 26000},
    {"Meldungen": 108, "Saison": "2010/11", "Erkrankung": "ARE", "Altersgruppe": "5-14", "Region": "Bundesweit", "Kalenderwoche": "2011-W24", "Inzidenz": 4900},
    {"Meldungen": 45,  "Saison": "2010/11", "Erkrankung": "ARE", "Altersgruppe": "0-4",  "Region": "Bundesweit", "Kalenderwoche": "2011-W25", "Inzidenz": 25000},
    {"Meldungen": 108, "Saison": "2010/11", "Erkrankung": "ARE", "Altersgruppe": "5-14", "Region": "Bundesweit", "Kalenderwoche": "2011-W25", "Inzidenz": 4700},
])


def test_output_row_count():
    result = predict(SAMPLE_DATA, horizon_weeks=4, n_reference_weeks=4)
    n_groups = SAMPLE_DATA.groupby(["Erkrankung", "Altersgruppe", "Region"]).ngroups
    assert len(result) == 4 * n_groups

def test_output_columns():
    result = predict(SAMPLE_DATA, horizon_weeks=2, n_reference_weeks=2)
    expected_cols = {"Meldungen", "Saison", "Erkrankung", "Altersgruppe",
                     "Region", "Kalenderwoche", "Inzidenz", "Modell", "Horizont_Wochen"}
    assert expected_cols.issubset(set(result.columns))

def test_modell_label():
    result = predict(SAMPLE_DATA, horizon_weeks=1, n_reference_weeks=1)
    assert (result["Modell"] == "baseline-nullmodel").all()

def test_horizont_wochen_values():
    horizon = 3
    result = predict(SAMPLE_DATA, horizon_weeks=horizon, n_reference_weeks=2)
    for group, gdf in result.groupby(["Erkrankung", "Altersgruppe", "Region"]):
        assert sorted(gdf["Horizont_Wochen"].tolist()) == list(range(1, horizon + 1))

def test_mean_values_correct():
    result = predict(SAMPLE_DATA, horizon_weeks=1, n_reference_weeks=2)
    row = result[
        (result["Erkrankung"] == "ARE") &
        (result["Altersgruppe"] == "
        