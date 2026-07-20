# -*- coding: utf-8 -*-
"""
Daily refresh of the Tashkent Housing Demand Brief.

Recomputes the aggregate object `D` from the uybor listing-day panel
(Supabase Postgres or a CSV export), validates it, and injects it into the
brief's HTML template. The charts are rendered client-side by Chart.js from
`D`, so replacing that one line is the entire "figure update".

Metric definitions were calibrated against the published brief
(tashkent_demand_brief.template.html) so a rerun on the same data reproduces
the published numbers:

  * flows      : per listing, first difference of the cumulative counters
                 ordered by snapshot_date, clipped at >= 0 ("raw" flow).
                 "Normalized" flow = raw flow / days since previous snapshot
                 (a per-day rate; relevant when a snapshot day is missing).
  * daily      : per snapshot date over NORMALIZED view flows -
                 total = sum, avg = mean, median = median,
                 active_listings = count of flows > 0.
  * vpd        : per-listing demand velocity = sum(raw view flow) / days
                 between first and last snapshot; single-snapshot listings = 0.
  * lifetime   : views = max cumulative counter per listing.
  * funnel/zero: RAW flow sums (views/clicks/favorites).
  * exit       : cohort = listings first seen <= last_date - EXIT_COHORT_DAYS;
                 exited = last seen before the final snapshot date.
  * prices     : per-listing last-snapshot price, kept in [3k, 5M] USD;
                 $/m2 uses last-snapshot area in [10, 2000] m2.
                 (`overall.ppm2_mean` intentionally holds the MEDIAN $/m2 -
                 the published fixture does the same; charts never read it.)
  * districts  : Tashkent city, the 12 canonical districts only.
  * price_tiers: apartment quintiles on the cleaned sample
                 (price 3k-5M, area 15-500 m2).
"""

import argparse
import json
import math
import os
import re
import sys
import tempfile
from datetime import datetime, timezone

import numpy as np
import pandas as pd

TABLE_ENV = "UYBOR_TABLE"
DEFAULT_TABLE = "uybor_listings_v2"
DB_URL_ENV = "SUPABASE_DB_URL"

COLUMNS = [
    "listing_id", "snapshot_date", "category", "rooms", "area_m2",
    "is_new_building", "renovation", "price_usd", "district",
    "views", "clicks", "favorites", "posted_at", "city",
]

CITY = "Ташкент"
DISTRICTS = [
    "Шайхантахурский район", "Янгихаётский район", "Юнусабадский район",
    "Бектемирский район", "Алмазарский район", "Сергелийский район",
    "Мирзо-Улугбекский район", "Чиланзарский район", "Яккасарайский район",
    "Учтепинский район", "Мирабадский район", "Яшнабадский район",
]
NEWBUILD_LABELS = {False: "Вторичка", True: "Новостройка"}

PRICE_LO, PRICE_HI = 3_000, 5_000_000
AREA_LO, AREA_HI = 10, 2_000
TIER_AREA_LO, TIER_AREA_HI = 15, 500
APARTMENT = "Квартира"
EXIT_COHORT_DAYS = 6  # first seen <= last_date - 6d ("observed early enough")

VPD_BINS = [0, 1, 2, 5, 10, 20, 50, np.inf]
VPD_LABELS = ["0-1", "1-2", "2-5", "5-10", "10-20", "20-50", "50+"]

D_KEYS = [
    "daily", "overall", "concentration", "vpd_hist", "exit", "by_category",
    "by_rooms", "by_district", "by_newbuild", "by_renovation", "price_tiers",
    "funnel", "zero",
]

D_LINE_RE = re.compile(r"^const D = .*;\s*$", re.MULTILINE)


class RefreshError(RuntimeError):
    """Any condition that must abort the run without touching the output."""


# ---------------------------------------------------------------- loading

def load_csv(path):
    df = pd.read_csv(path, usecols=COLUMNS)
    return _coerce(df)


def load_db(db_url, table):
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)?", table):
        raise RefreshError(f"invalid table name: {table!r}")
    from sqlalchemy import create_engine, text
    query = f'SELECT {", ".join(COLUMNS)} FROM {table}'
    engine = create_engine(db_url, pool_pre_ping=True)
    try:
        with engine.connect() as conn:
            df = pd.read_sql(text(query), conn)
    except Exception as exc:  # never echo the URL (it embeds the password)
        raise RefreshError(f"database read failed: {type(exc).__name__}: {exc}") from exc
    finally:
        engine.dispose()
    return _coerce(df)


def _coerce(df):
    if df.empty:
        raise RefreshError("source returned 0 rows")
    df = df.copy()
    df["snapshot_date"] = pd.to_datetime(df["snapshot_date"])
    posted = pd.to_datetime(df["posted_at"], errors="coerce", utc=True, format="mixed")
    df["posted_at"] = posted.dt.tz_localize(None)
    for col in ("price_usd", "area_m2", "views", "clicks", "favorites"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["is_new_building"] = df["is_new_building"].map(
        {True: True, False: False, "true": True, "false": False,
         "t": True, "f": False, 1: True, 0: False}
    )
    df["rooms"] = df["rooms"].map(_room_bucket)
    return df


def _room_bucket(value):
    if pd.isna(value):
        return np.nan
    s = str(value).strip()
    try:
        n = float(s)
    except ValueError:
        return s  # already labelled: "6+", "studio", "freeLayout"
    if n >= 6:
        return "6+"
    if n >= 1:
        return str(int(n))
    return np.nan


# ---------------------------------------------------------------- rounding

def _f(x):
    x = float(x)
    if not math.isfinite(x):
        raise RefreshError("non-finite value produced while building D")
    return x


def r1(x):
    return round(_f(x), 1)


def r3(x):
    return round(_f(x), 3)


def ri(x):
    return int(round(_f(x)))


# ---------------------------------------------------------- methodology stats

def _methodology_stats(per):
    """Two footnote statistics, computed defensively.

    age_corr   Pearson r between demand velocity and listing age (days on
               market) - the brief's claim that velocity is ~uncorrelated
               with tenure.
    hedonic_r2 R^2 (%) of an OLS hedonic regression of vpd on the listed
               attributes (log price, log area, rooms, category, district,
               renovation, new-build) - how little of demand the attributes
               explain.

    Either key is omitted if it cannot be computed cleanly.
    """
    out = {}

    age = per["dom"].where(per["dom"] >= 0)
    vpd = per["vpd"]
    m = age.notna() & vpd.notna()
    if m.sum() > 30 and vpd[m].std() > 0 and age[m].std() > 0:
        r = float(np.corrcoef(vpd[m].to_numpy(float), age[m].to_numpy(float))[0, 1])
        if math.isfinite(r):
            out["age_corr"] = round(r, 2)

    try:
        hed = per[per["price_c"].notna()
                  & per["area"].between(AREA_LO, AREA_HI)].copy()
        if len(hed) >= 100:
            y = hed["vpd"].to_numpy(dtype=float)
            cols = [np.ones(len(hed)),
                    np.log(hed["price_c"].to_numpy(dtype=float)),
                    np.log(hed["area"].to_numpy(dtype=float))]
            X = np.column_stack(cols)
            for col in ("rooms", "category", "district", "renovation"):
                dummies = pd.get_dummies(hed[col].astype("string"),
                                         drop_first=True, dummy_na=False)
                if dummies.shape[1]:
                    X = np.column_stack([X, dummies.to_numpy(dtype=float)])
            nb = hed["newbuild"].map({True: 1.0, False: 0.0})
            X = np.column_stack([X, nb.to_numpy(dtype=float)])
            ok = np.isfinite(X).all(axis=1) & np.isfinite(y)
            X, y = X[ok], y[ok]
            if len(y) >= 100 and y.std() > 0:
                beta, *_ = np.linalg.lstsq(X, y, rcond=None)
                resid = y - X @ beta
                ss_tot = float(((y - y.mean()) ** 2).sum())
                r2 = 1.0 - float(resid @ resid) / ss_tot if ss_tot > 0 else 0.0
                if math.isfinite(r2):
                    out["hedonic_r2"] = round(min(max(r2, 0.0), 1.0) * 100, 1)
    except Exception:
        pass

    return out


# ---------------------------------------------------------------- build_D

def build_D(df):
    df = df.sort_values(["listing_id", "snapshot_date"], kind="mergesort")
    # Apartments only: every figure in the brief is computed on Квартира
    # listings; other categories (house, commercial, land) are excluded.
    df = df[df["category"] == APARTMENT]
    if df.empty:
        raise RefreshError(f"no rows with category == {APARTMENT!r}")
    n_rows = len(df)
    dupes = df.duplicated(["listing_id", "snapshot_date"]).sum()
    if dupes:
        df = df.drop_duplicates(["listing_id", "snapshot_date"], keep="last")

    g = df.groupby("listing_id")
    gap = g["snapshot_date"].diff().dt.days
    flows_raw, flows_norm = {}, {}
    for col in ("views", "clicks", "favorites"):
        raw = g[col].diff().clip(lower=0)
        flows_raw[col] = raw
        flows_norm[col] = raw / gap
    df = df.assign(
        raw_views=flows_raw["views"], raw_clicks=flows_raw["clicks"],
        raw_favorites=flows_raw["favorites"], norm_views=flows_norm["views"],
    )

    g = df.groupby("listing_id")
    per = pd.DataFrame({
        "first": g["snapshot_date"].min(),
        "last": g["snapshot_date"].max(),
        "views_max": g["views"].max(),
        "raw_views": g["raw_views"].sum(),
        "raw_clicks": g["raw_clicks"].sum(),
        "raw_favorites": g["raw_favorites"].sum(),
        "category": g["category"].last(),
        "rooms": g["rooms"].last(),
        "district": g["district"].last(),
        "city": g["city"].last(),
        "newbuild": g["is_new_building"].last(),
        "renovation": g["renovation"].last(),
        "price": g["price_usd"].last(),
        "area": g["area_m2"].last(),
        "posted": g["posted_at"].last(),
    })
    span = (per["last"] - per["first"]).dt.days
    per["vpd"] = (per["raw_views"] / span.replace(0, np.nan)).fillna(0.0)
    per["price_c"] = per["price"].where(per["price"].between(PRICE_LO, PRICE_HI))
    per["ppm2"] = per["price_c"] / per["area"].where(per["area"].between(AREA_LO, AREA_HI))
    per["dom"] = (per["last"] - per["posted"]).dt.days

    last_date = df["snapshot_date"].max()
    per["in_cohort"] = per["first"] <= last_date - pd.Timedelta(days=EXIT_COHORT_DAYS)
    per["exited"] = per["last"] < last_date

    # snapshot-window metadata for the data-driven prose (the browser cannot
    # derive the window start or missing days from D.daily, which omits the
    # first snapshot date and any gap days)
    snap_dates = sorted(pd.to_datetime(df["snapshot_date"].unique()))
    first_date = snap_dates[0]
    present = set(snap_dates)
    missing_dates = [d.strftime("%Y-%m-%d")
                     for d in pd.date_range(first_date, last_date, freq="D")
                     if d not in present]

    # secondary methodology stats. Best-effort: if a stat cannot be computed
    # cleanly its key is omitted and the prose keeps its static fallback,
    # rather than failing the whole run over a footnote.
    meth = _methodology_stats(per)

    # ---- daily (normalized view flows; the panel's first date has none)
    daily = {}
    for day, day_rows in df.groupby("snapshot_date"):
        nv = day_rows["norm_views"].dropna()
        if nv.empty:
            continue
        daily[day.strftime("%Y-%m-%d")] = {
            "total_new_views": ri(nv.sum()),
            "avg_new_views": r1(nv.mean()),
            "median_new_views": r1(nv.median()),
            "active_listings": int((nv > 0).sum()),
        }
    if not daily:
        raise RefreshError("no daily flows could be computed "
                           "(panel has a single snapshot date?)")

    # ---- overall
    peak_key = max(daily, key=lambda d: daily[d]["total_new_views"])
    overall = {
        "count": int(per.shape[0]),
        "rows": int(n_rows),
        "price_mean": ri(per["price_c"].mean()),
        "price_median": ri(per["price_c"].median()),
        "ppm2_mean": ri(per["ppm2"].median()),  # fixture quirk: holds the median
        "views_mean": ri(per["views_max"].mean()),
        "views_median": ri(per["views_max"].median()),
        "vpd_mean": r1(per["vpd"].mean()),
        "vpd_median": r1(per["vpd"].median()),
        "dom_median": ri(per["dom"].median()),
        "cum_views": ri(per["views_max"].sum()),
        "total_new_views": ri(per["raw_views"].sum()),
        "peak_day": [peak_key, daily[peak_key]],
        "window_start": first_date.strftime("%Y-%m-%d"),
        "window_end": last_date.strftime("%Y-%m-%d"),
        "n_snapshot_dates": int(len(snap_dates)),
        "missing_dates": missing_dates,
        **meth,
    }

    # ---- concentration: top/bottom share of summed vpd, ranked by vpd
    vpd_sorted = per["vpd"].sort_values(ascending=False)
    total_vpd = vpd_sorted.sum()
    if total_vpd <= 0:
        raise RefreshError("total demand velocity is zero")
    n = len(vpd_sorted)
    concentration = {
        "top10": r1(vpd_sorted.iloc[:int(n * 0.10)].sum() / total_vpd * 100),
        "top25": r1(vpd_sorted.iloc[:int(n * 0.25)].sum() / total_vpd * 100),
        "bottom50": r1(vpd_sorted.iloc[int(n * 0.50):].sum() / total_vpd * 100),
    }

    # ---- vpd histogram (all listings)
    hist = pd.cut(per["vpd"], bins=VPD_BINS, labels=VPD_LABELS,
                  include_lowest=True).value_counts()
    vpd_hist = {lab: int(hist.get(lab, 0)) for lab in VPD_LABELS}

    # ---- exit
    cohort = per[per["in_cohort"]]
    if cohort.empty:
        raise RefreshError("exit cohort is empty")
    exited = cohort["exited"]
    exit_block = {
        "exit_rate": r3(exited.mean()),
        "exited_med_vpd": r1(cohort.loc[exited, "vpd"].median()),
        "exited_mean_vpd": r1(cohort.loc[exited, "vpd"].mean()),
        "stay_med_vpd": r1(cohort.loc[~exited, "vpd"].median()),
        "stay_mean_vpd": r1(cohort.loc[~exited, "vpd"].mean()),
        "n": int(len(cohort)),
    }

    def seg(rows):
        seg_cohort = rows[rows["in_cohort"]]
        exit_rate = seg_cohort["exited"].mean() if len(seg_cohort) else 0.0
        ppm2_med = rows["ppm2"].median()
        return {
            "count": int(len(rows)),
            "vpd_median": r1(rows["vpd"].median()),
            "vpd_mean": r1(rows["vpd"].mean()),
            "views_median": ri(rows["views_max"].median()),
            "views_mean": ri(rows["views_max"].mean()),
            "price_median": ri(rows["price_c"].median()),
            "ppm2_median": 0 if pd.isna(ppm2_med) else ri(ppm2_med),
            "exit_rate": r3(exit_rate),
            "dom_median": ri(rows["dom"].median()),
        }

    def by(col, keys=None, sort_desc_by_vpd=False):
        groups = {}
        for key, rows in per.groupby(col):
            if keys is not None and key not in keys:
                continue
            groups[key] = rows
        if sort_desc_by_vpd:
            ordered = sorted(groups, key=lambda k: -groups[k]["vpd"].median())
        else:
            ordered = sorted(groups)
        return {k: seg(groups[k]) for k in ordered}

    by_category = by("category")
    by_rooms = by("rooms")
    by_renovation = by("renovation")
    by_newbuild = {
        NEWBUILD_LABELS[flag]: seg(per[per["newbuild"] == flag])
        for flag in (False, True)
    }

    tash = per[(per["city"] == CITY) & per["district"].isin(DISTRICTS)]
    by_district = {
        k: seg(rows) for k, rows in
        sorted(tash.groupby("district"), key=lambda kv: -kv[1]["vpd"].median())
    }

    # ---- price tiers: apartment quintiles on the cleaned sample
    apt = per[(per["category"] == APARTMENT)
              & per["price"].between(PRICE_LO, PRICE_HI)
              & per["area"].between(TIER_AREA_LO, TIER_AREA_HI)]
    if len(apt) < 50:
        raise RefreshError(f"cleaned apartment sample too small ({len(apt)})")
    tiers = pd.qcut(apt["price"], 5, labels=["Q1", "Q2", "Q3", "Q4", "Q5"])
    price_tiers = {}
    for tier in ("Q1", "Q2", "Q3", "Q4", "Q5"):
        rows = apt[tiers == tier]
        tier_cohort = rows[rows["in_cohort"]]
        price_tiers[tier] = {
            "lo": ri(rows["price"].min()),
            "hi": ri(rows["price"].max()),
            "vpd_median": r1(rows["vpd"].median()),
            "click_rate": r1((rows["raw_clicks"] > 0).mean() * 100),
            "fav_rate": r1((rows["raw_favorites"] > 0).mean() * 100),
            "exit_rate": r3(tier_cohort["exited"].mean() if len(tier_cohort) else 0.0),
        }

    funnel = {
        "views": ri(per["raw_views"].sum()),
        "clicks": ri(per["raw_clicks"].sum()),
        "favorites": ri(per["raw_favorites"].sum()),
    }
    zero = {
        "views_zero": r1((per["raw_views"] == 0).mean() * 100),
        "clicks_zero": r1((per["raw_clicks"] == 0).mean() * 100),
        "favs_zero": r1((per["raw_favorites"] == 0).mean() * 100),
    }

    return {
        "daily": daily, "overall": overall, "concentration": concentration,
        "vpd_hist": vpd_hist, "exit": exit_block, "by_category": by_category,
        "by_rooms": by_rooms, "by_district": by_district,
        "by_newbuild": by_newbuild, "by_renovation": by_renovation,
        "price_tiers": price_tiers, "funnel": funnel, "zero": zero,
    }


# ------------------------------------------------------------- validation

def _walk_finite(node, path="D"):
    if isinstance(node, dict):
        for k, v in node.items():
            _walk_finite(v, f"{path}.{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            _walk_finite(v, f"{path}[{i}]")
    elif isinstance(node, bool) or node is None:
        raise RefreshError(f"unexpected {node!r} at {path}")
    elif isinstance(node, (int, float)):
        if not math.isfinite(node):
            raise RefreshError(f"non-finite number at {path}")
    elif not isinstance(node, str):
        raise RefreshError(f"non-JSON type {type(node).__name__} at {path}")


def extract_D(html_text):
    matches = D_LINE_RE.findall(html_text)
    if len(matches) != 1:
        raise RefreshError(f"expected exactly one 'const D = ...;' line, "
                           f"found {len(matches)}")
    return json.loads(matches[0].strip()[len("const D = "):].rstrip(";"))


def validate_D(d, previous_html_path=None):
    missing = [k for k in D_KEYS if k not in d or not d[k]]
    if missing:
        raise RefreshError(f"missing/empty keys in D: {missing}")
    unexpected = set(d) - set(D_KEYS)
    if unexpected:
        raise RefreshError(f"unexpected keys in D: {sorted(unexpected)}")

    if len(d["by_district"]) != 12:
        raise RefreshError(f"by_district has {len(d['by_district'])} entries, "
                           f"expected 12: {sorted(d['by_district'])}")
    if set(d["by_district"]) != set(DISTRICTS):
        raise RefreshError("by_district keys are not the canonical 12 districts")
    if set(d["by_newbuild"]) != set(NEWBUILD_LABELS.values()):
        raise RefreshError(f"by_newbuild keys wrong: {sorted(d['by_newbuild'])}")

    fn = d["funnel"]
    if not (fn["views"] > 0 and fn["views"] >= fn["clicks"] >= fn["favorites"] >= 0):
        raise RefreshError(f"funnel not monotone: {fn}")

    if set(d["vpd_hist"]) != set(VPD_LABELS):
        raise RefreshError("vpd_hist buckets wrong")
    if set(d["price_tiers"]) != {"Q1", "Q2", "Q3", "Q4", "Q5"}:
        raise RefreshError("price_tiers must be exactly Q1..Q5")

    latest = max(d["daily"])
    if previous_html_path and os.path.exists(previous_html_path):
        try:
            prev = extract_D(open(previous_html_path, encoding="utf-8").read())
            prev_latest = max(prev["daily"])
        except Exception as exc:
            raise RefreshError(
                f"could not read previous output for the regression check: {exc}"
            ) from exc
        if latest < prev_latest:
            raise RefreshError(f"time went backwards: new latest day {latest} "
                               f"< previous {prev_latest}")

    _walk_finite(d)
    return latest


# -------------------------------------------------------------- injection

def inject(template_text, d):
    payload = json.dumps(d, ensure_ascii=False)
    new_line = f"const D = {payload};"
    if len(D_LINE_RE.findall(template_text)) != 1:
        raise RefreshError("template must contain exactly one 'const D = ...;' line")
    html = D_LINE_RE.sub(lambda _m: new_line, template_text, count=1)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    marker = f"<!-- generated: {stamp} UTC -->\n</body>"
    if html.count("</body>") != 1:
        raise RefreshError("template must contain exactly one </body>")
    return html.replace("</body>", marker)


def write_atomic(path, text):
    directory = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(dir=directory, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


# -------------------------------------------------------------------- CLI

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--template", required=True, help="brief HTML template")
    ap.add_argument("--out", required=True, help="output HTML path")
    ap.add_argument("--csv", help="offline mode: read the panel from this CSV")
    ap.add_argument("--db-url", default=None,
                    help=f"Postgres URL (default: ${DB_URL_ENV})")
    args = ap.parse_args(argv)

    try:
        if args.csv:
            source = f"csv:{args.csv}"
            df = load_csv(args.csv)
        else:
            db_url = args.db_url or os.environ.get(DB_URL_ENV)
            if not db_url:
                raise RefreshError(f"no --csv given and ${DB_URL_ENV} is not set")
            table = os.environ.get(TABLE_ENV, DEFAULT_TABLE)
            source = f"db:{table}"
            df = load_db(db_url, table)

        with open(args.template, encoding="utf-8") as fh:
            template_text = fh.read()

        d = build_D(df)
        latest = validate_D(d, previous_html_path=args.out)
        html = inject(template_text, d)
        extract_D(html)  # round-trip: the injected JSON must parse back
        write_atomic(args.out, html)
    except RefreshError as exc:
        print(f"REFRESH FAILED: {exc}", file=sys.stderr)
        return 1

    print(f"OK [{source}]: {d['overall']['count']} listings | "
          f"{len(d['daily'])} days | latest {latest} | "
          f"top10 {d['concentration']['top10']}% | "
          f"vpd_median {d['overall']['vpd_median']} | wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
