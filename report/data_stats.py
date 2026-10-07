# -*- coding: utf-8 -*-
"""
data_stats.py — exact sample statistics for the paper's Data section.
=====================================================================

    python data_stats.py            # window 2026-06-24 .. 2026-09-24
    STATS_END=2026-10-24 python data_stats.py

Uses pipeline.load_panel() (same v1+v2 merge and de-duplication as every
figure) and reports, for two filter sets:
  pipeline : config.BOUNDS (price $30k-$1M, area, rooms, price/m2) - what the figures use
  paper    : price $30k-$1M and 1-8 rooms only (no area / price-per-m2 checks)

Stats: observation days, missing calendar days, listing-days, unique
apartments, listings whose district label changed, total new views / clicks /
saves (first differences of cumulative counters), and counter decreases.
Writes data_stats.json and prints it.
"""
import json
import os

import pandas as pd

import config
import pipeline

START = pd.Timestamp(os.environ.get("STATS_START", "2026-06-24"))
END = pd.Timestamp(os.environ.get("STATS_END", "2026-09-24"))
COUNTERS = ["views", "clicks", "favorites"]


def apply_filters(df, price, rooms=(1, 8), area=None, ppsm=None):
    a = df[(df.category == config.CATEGORY) & (df.city == config.CITY)].copy()
    a["snapshot_date"] = pd.to_datetime(a.snapshot_date)
    a = a[(a.snapshot_date >= START) & (a.snapshot_date <= END)]
    for c in ["price_usd", "area_m2"] + COUNTERS:
        a[c] = pd.to_numeric(a[c], errors="coerce")
    a["rooms_n"] = pd.to_numeric(a.rooms, errors="coerce")
    m = a.price_usd.between(*price) & a.rooms_n.between(*rooms)
    if area:
        m &= a.area_m2.between(*area)
    if ppsm:
        m &= (a.price_usd / a.area_m2).between(*ppsm)
    a = a[m]
    return a[a.district.isin(config.DISTRICT_MAP)]


def daily_profile(s):
    """Per snapshot date: listings observed, and new views from consecutive-day pairs."""
    s = s.copy()
    g = s.groupby("listing_id")
    s["dv"] = g.views.diff().clip(lower=0)
    s["gap"] = g.snapshot_date.diff().dt.days
    out = {}
    for d, x in s.groupby("snapshot_date"):
        pair = x[x.gap == 1]
        out[str(d.date())] = [int(len(x)), int(pair.dv.sum()), int(len(pair))]
    return out   # date -> [listings, new views (1-day pairs), pairs]


def stats(a):
    s = a.sort_values(["listing_id", "snapshot_date"])
    g = s.groupby("listing_id")
    flows = (g[COUNTERS].last() - g[COUNTERS].first()).clip(lower=0)
    diffs = g[COUNTERS].diff()
    dates = pd.to_datetime(sorted(s.snapshot_date.unique()))
    cal = pd.date_range(dates.min(), dates.max(), freq="D")
    return dict(
        first_date=str(dates.min().date()), last_date=str(dates.max().date()),
        calendar_days=len(cal), observation_days=len(dates),
        missing_days=[str(d.date()) for d in cal.difference(dates)],
        listing_days=int(len(s)), apartments=int(s.listing_id.nunique()),
        district_switchers=int((g.district.nunique() > 1).sum()),
        new_views=int(flows.views.sum()), new_clicks=int(flows.clicks.sum()),
        new_saves=int(flows.favorites.sum()),
        consecutive_pairs=int(diffs.views.notna().sum()),
        daily=daily_profile(s),
        counter_decreases={c: int((diffs[c] < 0).sum()) for c in COUNTERS},
    )


def main():
    df = pipeline.load_panel()
    b = config.BOUNDS
    out = {
        "window": [str(START.date()), str(END.date())],
        "pipeline_filters": stats(apply_filters(
            df, price=b["price_usd"], rooms=b["rooms"], area=b["area_m2"], ppsm=b["ppsm"])),
        "paper_filters": stats(apply_filters(df, price=(30_000, 1_000_000), rooms=(1, 8))),
    }
    with open("data_stats.json", "w") as fh:
        json.dump(out, fh, indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
