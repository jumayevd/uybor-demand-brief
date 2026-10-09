# -*- coding: utf-8 -*-
"""
timeseries.py — 3 monthly, district-wise demand trends (24th-to-24th).
======================================================================

Anchors the panel at the 24th of each month (the scraper's natural month
boundary): 24 Jun -> 24 Jul -> 24 Aug -> 24 Sep = three clean months. For each
month and district (plus an OVERALL row) it reports both the LEVEL at the anchor
and the FLOW over the month, so the trend in views / velocity / clicks / saves
is visible month to month.

Run (from report/):  python timeseries.py
Reads   config.CSV_INPUTS (merged v1 + live v2), apartments / Tashkent / bounds.
Writes  timeseries_out/  : CSVs, an .xlsx workbook, and trend PNG charts.
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.ticker import FuncFormatter

import config

mpl.rcParams["font.family"] = "DejaVu Sans"
mpl.rcParams["axes.spines.top"] = False
mpl.rcParams["axes.spines.right"] = False
GOLD, TEAL, RUST, PURP = "#C8A15A", "#2E7D8A", "#B24C3C", "#6B5B95"
GREY, INK = "#9AA0A6", "#2b2b2b"

OUT = os.path.join(os.path.dirname(__file__), "timeseries_out")
os.makedirs(OUT, exist_ok=True)

ANCHORS = ["2026-06-24", "2026-07-24", "2026-08-24", "2026-09-24"]


def load():
    frames = []
    for path, sd in config.CSV_INPUTS:
        df = pd.read_csv(os.path.join(os.path.dirname(__file__), path),
                         usecols=lambda c: c in {
                             "listing_id", "snapshot_date", "category", "city",
                             "district", "price_usd", "area_m2", "rooms",
                             "views", "clicks", "favorites"},
                         low_memory=False)
        if sd is not None:
            df["snapshot_date"] = sd
        frames.append(df)
    df = pd.concat(frames, ignore_index=True)
    df = df[(df.category == config.CATEGORY) & (df.city == config.CITY)]
    df = df[df.district.isin(config.DISTRICT_MAP)].copy()
    df["district_en"] = df.district.map(config.DISTRICT_MAP)
    df["snapshot_date"] = pd.to_datetime(df.snapshot_date)
    for c in ["price_usd", "area_m2", "views", "clicks", "favorites"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["rooms_n"] = pd.to_numeric(df.rooms, errors="coerce")
    df["ppsm"] = df.price_usd / df.area_m2
    b = config.BOUNDS
    df = df[df.price_usd.between(*b["price_usd"]) & df.area_m2.between(*b["area_m2"])
            & df.rooms_n.between(*b["rooms"]) & df.ppsm.between(*b["ppsm"])]
    df = df.drop_duplicates(["listing_id", "snapshot_date"], keep="first")
    fd = df.sort_values("snapshot_date").groupby("listing_id").district_en.first()
    df["district_en"] = df.listing_id.map(fd)
    return df.sort_values(["listing_id", "snapshot_date"])


def resolve_anchors(df):
    avail = pd.to_datetime(sorted(df.snapshot_date.unique()))
    out = []
    for t in ANCHORS:
        t = pd.Timestamp(t)
        if (avail == t).any():
            out.append(t)
        else:                                   # nearest available snapshot
            out.append(avail[np.abs((avail - t).days).argmin()])
    return out


def level(df, t):
    s = df[df.snapshot_date == t]
    return dict(active_listings=int(s.listing_id.nunique()),
                lvl_views_med=round(float(s.views.median()), 1) if len(s) else np.nan)


def flow(df, t0, t1):
    p = df[(df.snapshot_date >= t0) & (df.snapshot_date <= t1)]
    p = p.sort_values(["listing_id", "snapshot_date"])   # first/last below need date order
    g = p.groupby("listing_id").agg(
        v0=("views", "first"), v1=("views", "last"),
        c0=("clicks", "first"), c1=("clicks", "last"),
        f0=("favorites", "first"), f1=("favorites", "last"),
        d0=("snapshot_date", "first"), d1=("snapshot_date", "last"))
    g["days"] = (g.d1 - g.d0).dt.days
    g = g[g.days >= 1]
    g["nv"] = (g.v1 - g.v0).clip(lower=0)
    g["nc"] = (g.c1 - g.c0).clip(lower=0)
    g["nf"] = (g.f1 - g.f0).clip(lower=0)
    nv = float(g.nv.sum())
    return dict(
        days_in_period=int((t1 - t0).days),
        n_listings_period=int(len(g)),
        new_views=int(g.nv.sum()),
        vpd_med=round(float(g.nv.div(g.days).median()), 2) if len(g) else np.nan,
        vpd_mean=round(float(g.nv.div(g.days).mean()), 2) if len(g) else np.nan,
        new_clicks=int(g.nc.sum()), new_favs=int(g.nf.sum()),
        click_rate_pct=round(float((g.nc > 0).mean() * 100), 1) if len(g) else np.nan,
        save_rate_pct=round(float((g.nf > 0).mean() * 100), 1) if len(g) else np.nan,
        ctr_pct=round(g.nc.sum() / nv * 100, 3) if nv else np.nan)


def series(df, anchors, scope):
    rows = []
    for i, t in enumerate(anchors):
        r = dict(scope=scope, month=t.strftime("%b %Y"), anchor_date=str(t.date()))
        r.update(level(df, t))
        if i > 0:
            r["period_start"] = str(anchors[i - 1].date())
            r.update(flow(df, anchors[i - 1], t))
        else:
            r["period_start"] = ""
        rows.append(r)
    return pd.DataFrame(rows)


COLS = ["scope", "month", "anchor_date", "period_start", "days_in_period",
        "active_listings", "n_listings_period", "new_views", "vpd_med", "vpd_mean",
        "new_clicks", "new_favs", "click_rate_pct", "save_rate_pct", "ctr_pct",
        "lvl_views_med"]


def heatmap(dist_df, metric, title, fmt, hi, fname):
    d = dist_df[dist_df[metric].notna()].copy()
    d["lab"] = pd.to_datetime(d.anchor_date).dt.strftime("%b")
    order_cols = list(pd.to_datetime(d.anchor_date).sort_values().dt.strftime("%b").unique())
    piv = d.pivot(index="scope", columns="lab", values=metric)[order_cols]
    piv = piv.loc[piv[order_cols[-1]].sort_values(ascending=False).index]
    arr = piv.to_numpy(float)
    norm = (arr - np.nanmin(arr)) / (np.nanmax(arr) - np.nanmin(arr) + 1e-9)
    cmap = LinearSegmentedColormap.from_list("h", ["#f4efe6", hi])
    fig, ax = plt.subplots(figsize=(5.6, 6.4))
    ax.imshow(norm, cmap=cmap, aspect="auto")
    ax.set_xticks(range(len(piv.columns))); ax.set_xticklabels(piv.columns, fontsize=10)
    ax.set_yticks(range(len(piv.index))); ax.set_yticklabels(piv.index, fontsize=9)
    for i in range(arr.shape[0]):
        for j in range(arr.shape[1]):
            ax.text(j, i, fmt.format(arr[i, j]), ha="center", va="center", fontsize=8.5,
                    color="white" if norm[i, j] > 0.55 else INK,
                    fontweight="bold" if norm[i, j] > 0.8 else "normal")
    ax.set_title(title, fontsize=11, fontweight="bold", loc="left", pad=10)
    ax.set_xlabel("month ending on the 24th", fontsize=8.5, color=GREY)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(length=0)
    plt.tight_layout()
    plt.savefig(os.path.join(OUT, fname), dpi=150, bbox_inches="tight")
    plt.close()


def draw_multihorizon(ax, dist_df, metric, ylabel, title, fmt, thousands=False,
                      title_size=13, label_size=7, tick_size=9.5, legend_title=True,
                      palette=None):
    """Grouped bars on ax: each district, one bar per month-long period.

    Bars are monthly FLOWS, so each is labelled by its period (e.g. Jun-Jul),
    not the end-of-month anchor. thousands=True labels values as e.g. "199k".
    """
    def lab(v):
        return f"{v / 1000:.0f}k" if thousands else fmt.format(v)
    d = dist_df[dist_df[metric].notna()].copy()
    d["anchor_date"] = pd.to_datetime(d.anchor_date)
    d["period"] = (pd.to_datetime(d.period_start).dt.strftime("%b") + "–"
                   + d.anchor_date.dt.strftime("%b"))
    order = (d[["period", "anchor_date"]].drop_duplicates()
             .sort_values("anchor_date").period.tolist())
    piv = d.pivot(index="scope", columns="period", values=metric)[order]
    piv = piv.sort_values(order[-1], ascending=False)
    dists = list(piv.index); x = np.arange(len(dists)); w = 0.8 / len(order)
    palette = (palette or [GOLD, TEAL, RUST, PURP])[:len(order)]
    for k, (per, c) in enumerate(zip(order, palette)):
        vals = piv[per].to_numpy(float)
        off = (k - (len(order) - 1) / 2) * w
        ax.bar(x + off, vals, w, color=c, label=per)
        for xi, v in zip(x + off, vals):
            if np.isfinite(v):
                ax.annotate(lab(v), (xi, v), xytext=(0, 2), textcoords="offset points",
                            ha="center", va="bottom", fontsize=label_size, color=INK)
    ax.set_xticks(x); ax.set_xticklabels(dists, rotation=32, ha="right", fontsize=tick_size)
    ax.set_ylabel(ylabel); ax.set_ylim(0, np.nanmax(piv.values) * 1.16)
    if thousands:
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v / 1000:.0f}k"))
    ax.set_title(title, fontsize=title_size, fontweight="bold", loc="left")
    if legend_title:
        ax.legend(frameon=False, fontsize=10, ncol=len(order), loc="upper right",
                  title="period (24th-to-24th)", title_fontsize=9)
    else:
        ax.legend(frameon=False, fontsize=8.5, ncol=len(order), loc="upper right")


def multihorizon(dist_df, metric, ylabel, title, fmt, fname, thousands=False):
    """Standalone multi-horizon chart for one signal, saved to timeseries_out/."""
    fig, ax = plt.subplots(figsize=(14, 6))
    draw_multihorizon(ax, dist_df, metric, ylabel, title, fmt, thousands)
    plt.tight_layout()
    plt.savefig(os.path.join(OUT, fname), dpi=150, bbox_inches="tight")
    plt.close()


def overall_chart(ov):
    panels = [("new_views", "New views per month (reach)", "{:,.0f}"),
              ("vpd_med", "View velocity (median new views/listing/day)", "{:.2f}"),
              ("new_clicks", "New clicks per month", "{:,.0f}"),
              ("new_favs", "New saves per month", "{:,.0f}"),
              ("ctr_pct", "Click-through (clicks per 100 views)", "{:.2f}"),
              ("active_listings", "Active listings (stock at anchor)", "{:,.0f}")]
    ov = ov.copy(); ov["mlab"] = pd.to_datetime(ov.anchor_date).dt.strftime("%b")
    x = range(len(ov))
    fig, axs = plt.subplots(2, 3, figsize=(14, 7.5)); axs = axs.ravel()
    for ax, (col, title, fmt) in zip(axs, panels):
        y = ov[col]; m = y.notna()
        ax.plot([i for i in x if m.iloc[i]], y[m].to_numpy(float),
                color=TEAL, marker="o", lw=2.3, ms=7)
        for i in x:
            if m.iloc[i]:
                ax.annotate(fmt.format(y.iloc[i]), (i, y.iloc[i]),
                            textcoords="offset points", xytext=(0, 9), ha="center",
                            fontsize=8, color=TEAL, fontweight="bold")
        ax.set_title(title, fontsize=10.5, fontweight="bold", loc="left")
        ax.set_ylim(bottom=0)
        ax.set_xticks(list(x)); ax.set_xticklabels([f"{m}\n2026" for m in ov.mlab], fontsize=8.5)
        ax.set_xlim(-0.4, len(ov) - 0.6)
    fig.suptitle("Tashkent apartments — monthly demand trend (overall, 24th-to-24th)",
                 fontsize=14, fontweight="bold", x=0.02, ha="left")
    plt.tight_layout(rect=(0, 0, 1, 0.97))
    plt.savefig(os.path.join(OUT, "overall_trends.png"), dpi=150, bbox_inches="tight")
    plt.close()


def main():
    df = load()
    anchors = resolve_anchors(df)
    print("[timeseries] anchors:", [str(a.date()) for a in anchors])
    dists = sorted(df.district_en.unique())
    overall = series(df, anchors, "OVERALL")[COLS]
    dist = pd.concat([series(df[df.district_en == d], anchors, d) for d in dists],
                     ignore_index=True)[COLS]

    overall.to_csv(os.path.join(OUT, "ts_overall_monthly.csv"), index=False)
    dist.to_csv(os.path.join(OUT, "ts_district_monthly.csv"), index=False)
    try:
        with pd.ExcelWriter(os.path.join(OUT, "uybor_timeseries_monthly.xlsx"),
                            engine="openpyxl") as w:
            overall.to_excel(w, sheet_name="overall_monthly", index=False)
            dist.to_excel(w, sheet_name="district_monthly", index=False)
        print("[timeseries] wrote xlsx")
    except Exception as e:
        print("[timeseries] xlsx skipped:", e)

    overall_chart(overall)
    heatmap(dist, "vpd_med", "View velocity by district\n(median new views/listing/day)",
            "{:.1f}", TEAL, "heat_velocity.png")
    heatmap(dist, "new_views", "Monthly reach by district\n(new views per month)",
            "{:,.0f}", RUST, "heat_reach.png")
    heatmap(dist, "click_rate_pct", "Click incidence by district\n(% of listings with a click)",
            "{:.0f}%", GOLD, "heat_clickrate.png")
    heatmap(dist, "save_rate_pct", "Save incidence by district\n(% of listings with a save)",
            "{:.0f}%", PURP, "heat_saverate.png")
    # multi-horizon (3-period) comparison for each main monthly signal
    for metric, ylabel, title, fmt, fname, *opt in [
        ("vpd_med", "median new views / listing / day",
         "View velocity by district — three-month comparison", "{:.1f}",
         "multihorizon_velocity.png"),
        ("new_views", "new views in the period",
         "Reach (new views) by district — three-month comparison", "{:,.0f}",
         "multihorizon_reach.png", True),
        ("click_rate_pct", "% of listings with at least one click",
         "Click incidence by district — three-month comparison", "{:.0f}",
         "multihorizon_clicks.png"),
        ("save_rate_pct", "% of listings with at least one save",
         "Save incidence by district — three-month comparison", "{:.0f}",
         "multihorizon_saves.png"),
        ("ctr_pct", "clicks per 100 new views",
         "Click-through rate by district — three-month comparison", "{:.2f}",
         "multihorizon_ctr.png"),
    ]:
        multihorizon(dist, metric, ylabel, title, fmt, fname, thousands=bool(opt and opt[0]))
    print("[timeseries] done ->", OUT)


if __name__ == "__main__":
    main()
