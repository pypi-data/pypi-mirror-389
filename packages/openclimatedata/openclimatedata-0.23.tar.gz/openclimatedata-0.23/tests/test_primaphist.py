import os

import pandas as pd
import pytest
from pytest import approx

from openclimatedata import PRIMAPHIST

GITHUB_ACTIONS = os.getenv("GITHUB_ACTIONS") == "true"

versions = PRIMAPHIST.keys()


def test_primaphist():
    for version in versions:
        assert PRIMAPHIST[version].name
        assert PRIMAPHIST[version].doi
        assert PRIMAPHIST[version].published


@pytest.mark.skipif(GITHUB_ACTIONS, reason="Test requires downloading.")
def test_primaphist_2_6_1():
    df = PRIMAPHIST["2.6.1"]["main"].to_dataframe()
    assert df.iloc[0]["1750"] == approx(0.00564)
    assert df.iloc[-1]["2023"] == approx(0.0)

    assert df.iloc[0]["provenance"] == "derived"

    ocdf = PRIMAPHIST["2.6.1"]["main"].to_ocd()
    # First and last value should be the same after re-shaping.
    assert ocdf.iloc[0]["value"] == df.iloc[0]["1750"]
    assert ocdf.iloc[-1]["value"] == df.iloc[-1]["2023"]

    assert ocdf.iloc[0]["provenance"] == "derived"


@pytest.mark.skipif(GITHUB_ACTIONS, reason="Test requires downloading.")
def test_primaphist_2_6():
    df = PRIMAPHIST["2.6"]["main"].to_dataframe()
    assert df.iloc[0]["1750"] == approx(0.00564)
    assert df.iloc[-1]["2023"] == approx(0.0)

    assert df.iloc[0]["provenance"] == "derived"

    ocdf = PRIMAPHIST["2.6"]["main"].to_ocd()
    # First and last value should be the same after re-shaping.
    assert ocdf.iloc[0]["value"] == df.iloc[0]["1750"]
    assert ocdf.iloc[-1]["value"] == df.iloc[-1]["2023"]

    assert ocdf.iloc[0]["provenance"] == "derived"


@pytest.mark.skipif(GITHUB_ACTIONS, reason="Test requires downloading.")
def test_primaphist_2_5_1():
    df = PRIMAPHIST["2.5.1"]["main"].to_dataframe()
    assert df.iloc[0]["1750"] == approx(0.00564)
    assert df.iloc[-1]["2022"] == approx(0.0)

    assert df.iloc[0]["provenance"] == "derived"

    ocdf = PRIMAPHIST["2.5.1"]["main"].to_ocd()
    # First and last value should be the same after re-shaping.
    assert ocdf.iloc[0]["value"] == df.iloc[0]["1750"]
    assert ocdf.iloc[-1]["value"] == df.iloc[-1]["2022"]

    assert ocdf.iloc[0]["provenance"] == "derived"


@pytest.mark.skipif(GITHUB_ACTIONS, reason="Test requires downloading.")
def test_primaphist_2_5():
    df = PRIMAPHIST["2.5"]["main"].to_dataframe()
    assert df.iloc[0]["1750"] == approx(0.00564)
    assert df.iloc[-1]["2022"] == approx(0.0)

    assert df.iloc[0]["provenance"] == "measured"

    ocdf = PRIMAPHIST["2.5"]["main"].to_ocd()
    # First and last value should be the same after re-shaping.
    assert ocdf.iloc[0]["value"] == df.iloc[0]["1750"]
    assert ocdf.iloc[-1]["value"] == df.iloc[-1]["2022"]

    assert ocdf.iloc[0]["provenance"] == "measured"


@pytest.mark.skipif(GITHUB_ACTIONS, reason="Test requires downloading.")
def test_primaphist_2_4_2():
    df = PRIMAPHIST["2.4.2"]["main"].to_dataframe()
    assert df.iloc[0]["1750"] == approx(0.00564)
    assert df.iloc[-1]["2021"] == approx(13.9)

    ocdf = PRIMAPHIST["2.4.2"]["main"].to_ocd()
    # First and last value should be the same after re-shaping.
    assert ocdf.iloc[0]["value"] == df.iloc[0]["1750"]
    assert ocdf.iloc[-1]["value"] == df.iloc[-1]["2021"]

    assert pd.isna(ocdf.iloc[0]["provenance"])


@pytest.mark.skipif(GITHUB_ACTIONS, reason="Test requires downloading.")
def test_primaphist_2_3():
    df = PRIMAPHIST["2.3"]["main"].to_dataframe()
    assert df.iloc[0]["1750"] == approx(0.00564)
    assert df.iloc[-1]["2019"] == approx(15.6)

    ocdf = PRIMAPHIST["2.3"]["main"].to_ocd()
    # First and last value should be the same after re-shaping.
    assert ocdf.iloc[0]["value"] == df.iloc[0]["1750"]
    assert ocdf.iloc[-1]["value"] == df.iloc[-1]["2019"]

    assert pd.isna(ocdf.iloc[0]["provenance"])


@pytest.mark.skipif(GITHUB_ACTIONS, reason="Test requires downloading.")
def test_primaphist_2_2():
    df = PRIMAPHIST["2.2"]["main"].to_dataframe()
    assert df.iloc[0]["1850"] == approx(1.53e-04)
    assert df.iloc[-1]["2018"] == approx(1.99e-02)

    ocdf = PRIMAPHIST["2.2"]["main"].to_ocd()
    # First and last value should be the same after re-shaping.
    assert ocdf.iloc[0]["value"] == df.iloc[0]["1850"]
    assert ocdf.iloc[-1]["value"] == df.iloc[-1]["2018"]

    ocdf_2_3 = PRIMAPHIST["2.3"]["main"].to_ocd()

    # 2.2. ocd table should use the category style of later versions, without 'IPC' prefix
    assert set(ocdf.category.unique()) == set(ocdf_2_3.category.unique())

    # Entities shold use the style of >=2.3 with GWP in parentheses
    entities = set(ocdf.entity.unique())
    assert set(
        [
            "KYOTOGHG (AR4GWP100)",
            "KYOTOGHG (SARGWP100)",
            "FGASES (AR4GWP100)",
            "FGASES (SARGWP100)",
            "HFCS (AR4GWP100)",
            "HFCS (SARGWP100)",
            "PFCS (AR4GWP100)",
            "PFCS (SARGWP100)",
        ]
    ).issubset(entities)

    assert not set(
        [
            "KYOTOGHG",
            "KYOTOGHGAR4",
            "FGASES",
            "FGASESAR4",
            "HFCS",
            "HFCSAR4",
            "PFCS",
            "PFCSAR4",
        ]
    ).issubset(entities)

    assert pd.isna(ocdf.iloc[0]["provenance"])
