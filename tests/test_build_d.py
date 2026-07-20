# -*- coding: utf-8 -*-
import json
import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from refresh_brief import (  # noqa: E402
    D_KEYS, DISTRICTS, build_D, extract_D, inject, load_csv, validate_D,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLE_CSV = os.path.join(ROOT, "uybor_listings_v2_rows.csv")
TEMPLATE = os.path.join(ROOT, "tashkent_demand_brief.template.html")


@pytest.fixture(scope="module")
def D():
    if not os.path.exists(SAMPLE_CSV):
        pytest.skip("sample CSV not present")
    return build_D(load_csv(SAMPLE_CSV))


def test_all_keys_present(D):
    assert list(D) == D_KEYS
    for key in D_KEYS:
        assert D[key], f"{key} is empty"


def test_by_district_is_canonical_twelve(D):
    assert len(D["by_district"]) == 12
    assert set(D["by_district"]) == set(DISTRICTS)


def test_apartments_only(D):
    # every figure is computed on apartments only, so by_category collapses
    assert list(D["by_category"]) == ["Квартира"]


def test_by_newbuild_keys_are_cyrillic(D):
    assert set(D["by_newbuild"]) == {"Вторичка", "Новостройка"}


def test_funnel_monotone(D):
    f = D["funnel"]
    assert f["views"] > 0
    assert f["views"] >= f["clicks"] >= f["favorites"] >= 0


def test_price_tiers_shape(D):
    assert list(D["price_tiers"]) == ["Q1", "Q2", "Q3", "Q4", "Q5"]
    for tier in D["price_tiers"].values():
        assert set(tier) == {"lo", "hi", "vpd_median", "click_rate",
                             "fav_rate", "exit_rate"}


def test_concentration_sane(D):
    c = D["concentration"]
    assert c["top25"] >= c["top10"] > 0
    assert 0 <= c["bottom50"] <= c["top25"]
    assert c["top10"] <= 100 and c["top25"] <= 100


def test_validate_passes(D):
    validate_D(D)


def test_injection_round_trip(D):
    with open(TEMPLATE, encoding="utf-8") as fh:
        html = inject(fh.read(), D)
    assert html.count("const D = ") == 1
    assert "<!-- generated: " in html and " UTC -->" in html
    assert extract_D(html) == json.loads(json.dumps(D))


# ---- synthetic-panel unit tests for the flow logic ----------------------

def _panel():
    """Two Tashkent listings over three days; one counter decreases once."""
    rows = []
    days = ["2026-06-01", "2026-06-02", "2026-06-03"]
    views_a = [100, 150, 140]   # decrease must be clipped, lifetime = 150
    views_b = [10, 30, 60]
    for i, day in enumerate(days):
        for lid, views in ((1, views_a), (2, views_b)):
            rows.append({
                "listing_id": lid, "snapshot_date": day,
                "category": "Квартира", "rooms": 2, "area_m2": 50.0,
                "is_new_building": lid == 2, "renovation": "evro",
                "price_usd": 50000.0 + lid, "district": DISTRICTS[lid],
                "views": views[i], "clicks": i, "favorites": 0,
                "posted_at": "2026-05-01T10:00:00+00:00", "city": "Ташкент",
            })
    return pd.DataFrame(rows)


def test_flows_clipped_and_lifetime_max():
    import refresh_brief
    df = refresh_brief._coerce(_panel())
    df = df.sort_values(["listing_id", "snapshot_date"])
    g = df.groupby("listing_id")
    flow = g["views"].diff().clip(lower=0)
    # listing 1: +50 then a decrease (clipped to 0)
    assert flow[df.listing_id == 1].dropna().tolist() == [50.0, 0.0]
    # lifetime views must use the cumulative max, not the last value
    assert g["views"].max()[1] == 150


def test_build_d_fails_loud_on_degenerate_panel():
    import refresh_brief
    df = refresh_brief._coerce(_panel())
    # a 3-day two-listing panel must abort (no exit cohort / tiny sample),
    # never produce a partial D
    with pytest.raises(refresh_brief.RefreshError):
        build_D(df)


def test_rooms_bucketing():
    from refresh_brief import _room_bucket
    assert _room_bucket(2) == "2"
    assert _room_bucket(2.0) == "2"
    assert _room_bucket(6) == "6+"
    assert _room_bucket(9.0) == "6+"
    assert _room_bucket("studio") == "studio"
    assert _room_bucket("6+") == "6+"
    assert pd.isna(_room_bucket(float("nan")))
