"""
pipeline.py — Uybor.uz housing-demand data pipeline
====================================================

Turns raw daily-scrape CSVs into (a) two clean panel objects and (b) a single
`metrics.json` containing EVERY number used by the paper and its figures.

Run:  python pipeline.py
Reads:   config.CSV_INPUTS  (list of daily-scrape CSVs)
Writes:  build/L.pkl        one row per listing (listing-level signals)
         build/P.pkl        the full cleaned daily panel (listing-day rows)
         build/metrics.json all headline + district + dimension numbers

The four demand SIGNALS (see README for the research behind each):
  Signal 1  Views & view velocity   — breadth + current intensity of attention
  Signal 2  Clicks & saves          — deliberate, scarce intent
  Signal 3  Exit rate               — flow of stock leaving the market
  Signal 4  Time on market          — duration face of demand

Everything downstream (figures, paper) reads ONLY metrics.json + L.pkl + P.pkl,
so this file is the single source of truth. Change a definition here and the
whole report updates.
"""
import pandas as pd, numpy as np, json, os
import config

os.makedirs(config.BUILD_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# 1. LOAD + STACK all daily scrapes into one long panel
# ---------------------------------------------------------------------------
def load_panel():
    frames = []
    for path, snapshot_date in config.CSV_INPUTS:
        df = pd.read_csv(path, low_memory=False)
        # If a file has no snapshot_date column, stamp it from config.
        if snapshot_date is not None:
            df["snapshot_date"] = snapshot_date
        frames.append(df)
    df = pd.concat(frames, ignore_index=True)
    # one row per (listing, day); keep first if a listing appears twice in a day
    df = df.drop_duplicates(subset=["listing_id", "snapshot_date"], keep="first")
    return df


# ---------------------------------------------------------------------------
# 2. FILTER to Tashkent apartments + plausibility bounds
# ---------------------------------------------------------------------------
def clean(df):
    apt = df[(df.category == config.CATEGORY) & (df.city == config.CITY)].copy()
    apt["snapshot_date"] = pd.to_datetime(apt.snapshot_date)
    apt["posted_at"] = pd.to_datetime(apt.posted_at, errors="coerce").dt.tz_localize(None)
    apt["ppsm"] = apt.price_usd / apt.area_m2
    apt["rooms_n"] = pd.to_numeric(apt.rooms, errors="coerce")
    b = config.BOUNDS
    apt = apt[
        apt.price_usd.between(*b["price_usd"])
        & apt.area_m2.between(*b["area_m2"])
        & apt.rooms_n.between(*b["rooms"])
        & apt.ppsm.between(*b["ppsm"])
    ]
    apt = apt[apt.district.isin(config.DISTRICT_MAP)]
    apt["district_en"] = apt.district.map(config.DISTRICT_MAP)
    # District labels can flicker across snapshots (portal geocoding noise):
    # freeze each listing to its FIRST-observed district so every listing is
    # counted once.
    first_district = (
        apt.sort_values("snapshot_date").groupby("listing_id").district_en.first()
    )
    apt["district_en"] = apt.listing_id.map(first_district)
    return apt


# ---------------------------------------------------------------------------
# 3. LISTING-LEVEL SIGNALS  (one row per listing)
#    views/clicks/favorites are cumulative counters -> flows = last - first
# ---------------------------------------------------------------------------
def listing_level(apt):
    g = apt.sort_values("snapshot_date").groupby("listing_id")
    L = g.agg(
        v0=("views", "first"), v1=("views", "last"),
        c0=("clicks", "first"), c1=("clicks", "last"),
        f0=("favorites", "first"), f1=("favorites", "last"),
        d0=("snapshot_date", "first"), d1=("snapshot_date", "last"),
        district=("district_en", "first"),
        price=("price_usd", "last"), area=("area_m2", "last"),
        rooms=("rooms_n", "last"), newb=("is_new_building", "last"),
        reno=("renovation", "last"), posted=("posted_at", "first"),
    )
    L["days_obs"] = (L.d1 - L.d0).dt.days
    L["nv"] = (L.v1 - L.v0).clip(lower=0)   # new views over the window
    L["nc"] = (L.c1 - L.c0).clip(lower=0)   # new clicks
    L["nf"] = (L.f1 - L.f0).clip(lower=0)   # new favorites
    L = L[L.days_obs >= 1].copy()
    L["vpd"] = L.nv / L.days_obs            # SIGNAL 1: demand velocity
    return L


# ---------------------------------------------------------------------------
# 4. ALL METRICS  ->  metrics.json
# ---------------------------------------------------------------------------
def metrics(apt, L):
    L["rn"] = pd.to_numeric(L.rooms, errors="coerce")
    R = {}
    R["window"] = dict(
        n_days=int(apt.snapshot_date.nunique()),
        date_min=str(apt.snapshot_date.min().date()),
        date_max=str(apt.snapshot_date.max().date()),
        n_listings=int(apt.listing_id.nunique()),
        n_obs=int(len(apt)),
    )

    # ---- SIGNAL 1: views & velocity ----
    R["med_vpd"] = round(float(L.vpd.median()), 1)
    R["mean_vpd"] = round(float(L.vpd.mean()), 1)
    R["ratio"] = round(R["mean_vpd"] / R["med_vpd"], 1)
    vs = np.sort(L.vpd.values)[::-1]; tot = vs.sum(); n = len(vs)
    R["top10"] = round(float(vs[: int(n * .1)].sum() / tot * 100), 1)
    R["top25"] = round(float(vs[: int(n * .25)].sum() / tot * 100), 1)
    R["bot50"] = round(float(vs[int(n * .5):].sum() / tot * 100), 1)
    R["tot_views"] = int(L.nv.sum())

    # ---- SIGNAL 2: clicks & favorites ----
    R["tot_clicks"] = int(L.nc.sum()); R["tot_favs"] = int(L.nf.sum())
    R["ctr"] = round(float(L.nc.sum() / L.nv.sum() * 100), 3)
    R["favr"] = round(float(L.nf.sum() / L.nv.sum() * 100), 3)
    R["pct_noclick"] = round(float((L.nc == 0).mean() * 100), 1)
    R["pct_nofav"] = round(float((L.nf == 0).mean() * 100), 1)
    R["views_per_fav"] = int(L.nv.sum() / max(L.nf.sum(), 1))
    R["clicks_per_fav"] = round(float(L.nc.sum() / max(L.nf.sum(), 1)), 1)

    # ---- SIGNAL 3: exit rate (cohort method) ----
    dates = sorted(apt.snapshot_date.unique())
    wk1 = dates[0] + pd.Timedelta(days=6)      # first-week cohort cutoff
    final = dates[-1]                          # terminal snapshot
    present_final = set(apt[apt.snapshot_date == final].listing_id.unique())
    cohort = set(apt[apt.snapshot_date <= wk1].listing_id.unique())
    exited = cohort - present_final
    R["cohort_n"] = len(cohort); R["exit_n"] = len(exited)
    R["exit_rate"] = round(len(exited) / len(cohort) * 100, 0)
    L["exited"] = L.index.isin(exited); L["incohort"] = L.index.isin(cohort)
    sub = L[L.incohort]
    R["vpd_exit"] = round(float(sub[sub.exited].vpd.median()), 1)
    R["vpd_stay"] = round(float(sub[~sub.exited].vpd.median()), 1)
    R["exit_gap"] = round(R["vpd_exit"] / R["vpd_stay"], 1)

    # exit decomposition against the platform listing term (renewal wall)
    L["tom_completed"] = np.where(L.exited, (L.d1 - L.posted).dt.days, np.nan)
    ex = L[L.exited & L.tom_completed.ge(0)]
    lo, hi = config.LISTING_TERM_DAYS
    early = ex.tom_completed < lo
    wall = ex.tom_completed.between(lo, hi)
    late = ex.tom_completed > hi
    R["exit_early_pct"] = round(float(early.mean() * 100), 1)
    R["exit_wall_pct"] = round(float(wall.mean() * 100), 1)
    R["exit_late_pct"] = round(float(late.mean() * 100), 1)
    R["vpd_early_exit"] = round(float(ex[early].vpd.median()), 1)
    R["vpd_wall_exit"] = round(float(ex[wall].vpd.median()), 1)
    R["vpd_late_exit"] = round(float(ex[late].vpd.median()), 1)

    # ---- SIGNAL 4: time on market ----
    comp = L.loc[L.exited & L.tom_completed.ge(0), "tom_completed"]
    R["tom_med"] = round(float(comp.median()), 0)
    R["tom_n"] = int(comp.notna().sum())
    act = apt[apt.snapshot_date == final].copy()
    act["age"] = (act.snapshot_date - act.posted_at).dt.days
    act["rn"] = pd.to_numeric(act.rooms, errors="coerce")
    R["stockage_med"] = round(float(act.age.median()), 0)

    # ---- DAY-OF-WEEK (consecutive-day pairs only, so scrape gaps don't distort)
    a = apt.sort_values(["listing_id", "snapshot_date"]).copy()
    for c in ["views", "clicks", "favorites"]:
        a[f"{c}_p"] = a.groupby("listing_id")[c].shift(1)
    a["date_p"] = a.groupby("listing_id").snapshot_date.shift(1)
    a["gap"] = (a.snapshot_date - a.date_p).dt.days
    d1 = a[a.gap == 1].copy()
    for c in ["views", "clicks", "favorites"]:
        d1[f"new_{c}"] = (d1[c] - d1[f"{c}_p"]).clip(lower=0)
    d1["dow"] = d1.snapshot_date.dt.dayofweek
    dow = d1.groupby("dow").agg(ld=("listing_id", "size"), v=("new_views", "sum"),
                                c=("new_clicks", "sum"), f=("new_favorites", "sum"))
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    R["dow"] = {days[i]: dict(vpl=round(float(dow.v[i] / dow.ld[i]), 1),
                              cpk=round(float(dow.c[i] / dow.ld[i] * 1000), 2),
                              fpk=round(float(dow.f[i] / dow.ld[i] * 1000), 2),
                              ld=int(dow.ld[i])) for i in dow.index}

    # ---- ROOM-COUNT dimension ----
    rm = L[L.rn.between(1, 5)].groupby("rn").agg(
        vpd=("vpd", "median"), n=("vpd", "size"),
        clicka=("nc", lambda s: (s > 0).mean() * 100),
        fava=("nf", lambda s: (s > 0).mean() * 100))
    R["rooms_dims"] = {int(k): dict(vpd=round(float(v.vpd), 1), n=int(v.n),
                                    clicka=round(float(v.clicka), 1),
                                    fava=round(float(v.fava), 1)) for k, v in rm.iterrows()}
    er = sub[sub.rn.between(1, 5)].groupby("rn").exited.mean() * 100
    R["exit_rooms"] = {int(k): round(float(v), 0) for k, v in er.items()}
    sa = act[act.rn.between(1, 5)].groupby("rn").age.median()
    R["age_rooms"] = {int(k): int(v) for k, v in sa.items()}
    last = apt.sort_values("snapshot_date").groupby("listing_id").last()
    last["rn"] = pd.to_numeric(last.rooms, errors="coerce")
    rv = last.groupby("rn").views.agg(["mean", "median"])
    R["rooms"] = {int(k): dict(mean=int(v["mean"]), med=int(v["median"]))
                  for k, v in rv.iterrows() if k <= 5}

    # ---- NORMALIZED intent by district ----
    di = L.groupby("district").agg(
        n=("nc", "size"),
        clicka=("nc", lambda s: (s > 0).mean() * 100),
        fava=("nf", lambda s: (s > 0).mean() * 100),
        c=("nc", "sum"), f=("nf", "sum"))
    R["intent_norm"] = {d: dict(clicka=round(float(v.clicka), 1),
                                fava=round(float(v.fava), 1),
                                n=int(v.n), c=int(v.c), f=int(v.f))
                        for d, v in di.iterrows()}

    # ---- DISTRICT master table + map inputs ----
    L["ppsm"] = L.price / L.area
    dd = {}
    for d in sorted(L.district.unique()):
        ld = L[L.district == d]
        ids = set(apt[(apt.snapshot_date <= wk1) & (apt.district_en == d)].listing_id.unique())
        exr = len(ids - present_final) / len(ids) * 100 if ids else np.nan
        ag = act[act.district_en == d].age.median()
        comp_d = ld.loc[ld.exited & ld.tom_completed.ge(0), "tom_completed"].median()
        dd[d] = dict(vpd=round(float(ld.vpd.median()), 1),
                     reach=int(ld.nv.sum()),
                     absorp=round(float(exr), 0),
                     age=round(float(ag), 0),
                     tom=round(float(comp_d), 0) if pd.notna(comp_d) else None,
                     pv=round(float(ld.price.median() / ld.vpd.median()), 0),
                     medprice=int(ld.price.median()),
                     ppsm=int(ld.ppsm.median()),
                     clicks=int(ld.nc.sum()), favs=int(ld.nf.sum()),
                     nlist=int(len(ld)),
                     clicka=round(float((ld.nc > 0).mean() * 100), 1),
                     fava=round(float((ld.nf > 0).mean() * 100), 1))
    R["districts"] = dd

    # district view-velocity PERCENTILE (map color) + median coordinates (map position)
    L["vpct"] = L.vpd.rank(pct=True) * 100
    R["vpct"] = {d: round(float(L[L.district == d].vpct.mean()), 1) for d in dd}
    cc = apt.groupby("district_en").agg(lat=("latitude", "median"),
                                        lon=("longitude", "median"))
    R["centroids"] = {d: dict(lat=round(float(v.lat), 4), lon=round(float(v.lon), 4))
                      for d, v in cc.iterrows()}

    # bubble-map positions: start at true centroids, nudge apart so circles stay
    # distinct (Dorling-style), radius ~ sqrt(stock). Keeps displacement < ~1 km.
    names = list(R["centroids"])
    bpos = np.array([[R["centroids"][k]["lon"], R["centroids"][k]["lat"]] for k in names], float)
    orig = bpos.copy()
    maxn = max(dd[k]["nlist"] for k in names)
    brad = np.array([0.004 + 0.014 * (dd[k]["nlist"] / maxn) ** 0.5 for k in names])
    aspect = np.cos(np.radians(41.3))
    for _ in range(300):
        moved = 0
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                dx = (bpos[j, 0] - bpos[i, 0]) * aspect; dy = bpos[j, 1] - bpos[i, 1]
                dist = np.hypot(dx, dy); mind = (brad[i] + brad[j]) * 1.12
                if 1e-9 < dist < mind:
                    push = (mind - dist) / 2; ux, uy = dx / dist, dy / dist
                    bpos[i, 0] -= ux * push / aspect; bpos[i, 1] -= uy * push
                    bpos[j, 0] += ux * push / aspect; bpos[j, 1] += uy * push
                    moved += 1
        bpos += (orig - bpos) * 0.05
        if moved == 0:
            break
    R["map_pos2"] = {names[i]: [round(float(bpos[i, 0]), 5), round(float(bpos[i, 1]), 5)]
                     for i in range(len(names))}
    R["map_rad2"] = {names[i]: round(float(brad[i]), 5) for i in range(len(names))}

    # ---- PRICE BANDS: supply vs demand ----
    L["band"] = pd.cut(L.price, config.PRICE_BANDS, labels=config.PRICE_BAND_LABELS)
    bb = L.groupby("band", observed=True).agg(supply=("vpd", "size"),
                                              medvpd=("vpd", "median"))
    R["bands"] = {str(k): dict(supply=int(v.supply), medvpd=round(float(v.medvpd), 1))
                  for k, v in bb.iterrows()}

    # ---- PRICE QUINTILES (wedge) ----
    L["pq"] = pd.qcut(L.price, 5, labels=["Q1", "Q2", "Q3", "Q4", "Q5"])
    qq = L.groupby("pq", observed=True).agg(
        vpd=("vpd", "median"),
        clicka=("nc", lambda s: (s > 0).mean() * 100),
        fava=("nf", lambda s: (s > 0).mean() * 100),
        pmin=("price", "min"), pmax=("price", "max"))
    R["quintiles"] = {str(k): dict(vpd=round(float(v.vpd), 1),
                                   clicka=round(float(v.clicka), 1),
                                   fava=round(float(v.fava), 1),
                                   pmin=int(v.pmin), pmax=int(v.pmax))
                      for k, v in qq.iterrows()}

    # ---- SEGMENTS ----
    R["nb_sec"] = round(float(L[~L.newb.astype(bool)].vpd.median()), 1)
    R["nb_new"] = round(float(L[L.newb.astype(bool)].vpd.median()), 1)
    R["reno"] = {k: round(float(v), 1) for k, v in L.groupby("reno").vpd.median().items()}

    return R, L


def main():
    df = load_panel()
    apt = clean(df)
    L = listing_level(apt)
    R, L = metrics(apt, L)
    L.to_pickle(os.path.join(config.BUILD_DIR, "L.pkl"))
    apt.to_pickle(os.path.join(config.BUILD_DIR, "P.pkl"))
    with open(os.path.join(config.BUILD_DIR, "metrics.json"), "w") as fh:
        json.dump(R, fh, indent=1, ensure_ascii=False)
    w = R["window"]
    print(f"[pipeline] {w['n_listings']} apartments, {w['n_obs']} listing-days, "
          f"{w['date_min']} to {w['date_max']} ({w['n_days']} snapshots)")
    print(f"[pipeline] wrote build/L.pkl, build/P.pkl, build/metrics.json")


if __name__ == "__main__":
    main()
