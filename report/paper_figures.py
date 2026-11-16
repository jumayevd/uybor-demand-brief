# -*- coding: utf-8 -*-
"""
paper_figures.py — build the working paper's figures, frozen at a cut-off date.
==============================================================================

    PANEL_START=2026-06-30 PANEL_END=2026-10-31 python paper_figures.py   # July-October 2026

Runs pipeline + figures_en on snapshots within [PANEL_START, PANEL_END], then copies the figures the
paper uses into paper_figures/ under the paper's own numbering, as vector PDF
plus 300-DPI JPG, with captions.txt and the metrics.json behind them (handy for
reading numbers into the text). Figures on Telegram but not in the current
draft are included with an "Extra_" prefix.
"""
import json
import os
import shutil

import fitz  # PyMuPDF

import config
import figures_en
import pipeline

OUT = os.path.join(os.path.dirname(__file__) or ".", "paper_figures")

# (paper figure number, figure file, exported file stem, caption) — draft v22
# (16 figures). Stems of figures already in the LaTeX are kept unchanged (e.g.
# Figure04_intent_* is the paper's Figure 5); new figures are named after their
# v22 number. The paper's numbering lives only in the captions.
PAPER = [
    (1, "fig_concentration_apartments", "Figure01_concentration_apartments",
     "Distribution of view velocity and concentration of attention"),
    (2, "fig_s1_dimensions", "Figure02_s1_dimensions", "View velocity across market segments"),
    (3, "fig_wedge_apartments", "Figure03_wedge_apartments", "The wedge between price and demand"),
    (4, "fig_demand_map", "Extra_demand_map", "Geographic distribution of demand reach in Tashkent"),
    (5, "fig_intent_norm_districts", "Figure04_intent_norm_districts",
     "Normalized purchase intent across districts"),
    (6, "fig_intent_rooms", "Figure06_intent_rooms", "Purchase intent by number of rooms"),
    (7, "fig_exit_apartments", "Figure06_exit_apartments",
     "Market exit probability and its (weak) association with demand"),
    (8, "fig_exit_dims", "Figure07_exit_dims", "Market exit probability across segments"),
    (9, "fig_tom_dims", "Figure08_tom_dims", "Time on market (apartments)"),
    (10, "fig_metrics_panel_apartments", "Figure09_metrics_panel_apartments",
     "Heatmap of the four demand signals"),
    (11, "fig_monthly_views", "Figure11_monthly_views",
     "Supply, demand and their ratio measured by views, Tashkent, by month: (a) active listings, "
     "daily average; (b) new views in the month; (c) new views per active listing-day"),
    (12, "fig_monthly_velocity", "Figure12_monthly_velocity",
     "Supply, demand and their ratio measured by view velocity, Tashkent, by month: (a) active "
     "listings, daily average; (b) new views per day across all listings; (c) median new views "
     "per day per listing (listings active at least 7 days in the month)"),
    (13, "fig_monthly_clicks", "Figure13_monthly_clicks",
     "Supply, demand and their ratio measured by clicks, Tashkent, by month: (a) active listings, "
     "daily average; (b) clicks in the month; (c) clicks per 1,000 active listing-days"),
    (14, "fig_monthly_saves", "Figure14_monthly_saves",
     "Supply, demand and their ratio measured by saves, Tashkent, by month: (a) active listings, "
     "daily average; (b) saves in the month; (c) saves per 1,000 active listing-days"),
    (15, "fig_supply_demand_bands", "Figure11_supply_demand_bands",
     "Distribution of demand and supply across price segments"),
    (16, "fig_tightness_districts", "Figure12_tightness_districts", "Market tightness across districts"),
]
EXTRA = [    # (figure file, caption) for figures built but not in the current draft
    ("fig_s2_dimensions", "Purchase intent by room count and day of week (earlier draft)"),
    ("fig_dynamics_districts",
     "Demand dynamics by district and month: (a) demand reach and (b) click-through rate"),
    ("fig_demand_supply_monthly",
     "Supply, demand and the demand/supply ratio by month"),
    ("fig_clicks_supply_districts",
     "Clicks per 1,000 active listings a day, by district and month"),
    ("fig_saves_supply_districts",
     "Saves per 1,000 active listings a day, by district and month"),
]


def export(src_pdf, stem):
    shutil.copy(src_pdf, os.path.join(OUT, stem + ".pdf"))
    doc = fitz.open(src_pdf)
    pix = doc[0].get_pixmap(matrix=fitz.Matrix(4.17, 4.17))   # ~300 DPI
    with open(os.path.join(OUT, stem + ".jpg"), "wb") as fh:
        fh.write(pix.tobytes("jpg", jpg_quality=95))
    doc.close()


def main():
    pipeline.main()
    figures_en.main()
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    R = json.load(open(os.path.join(config.BUILD_DIR, "metrics.json"), encoding="utf-8"))
    w = R["window"]
    lines = [f"Window: {w['date_min']} to {w['date_max']}  ({w['n_days']} observation days, "
             f"{w['n_listings']:,} apartments, {w['n_obs']:,} listing-days)", ""]
    for n, name, stem, cap in PAPER:
        export(os.path.join(figures_en.FIG_DIR, name + ".pdf"), stem)
        lines.append(f"Figure {n}. {cap}")
    for name, cap in EXTRA:
        export(os.path.join(figures_en.FIG_DIR, name + ".pdf"), f"Extra_{name[4:]}")
        lines.append(f"Extra. {cap} (on Telegram; not in this draft)")
    with open(os.path.join(OUT, "captions.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    shutil.copy(os.path.join(config.BUILD_DIR, "metrics.json"), os.path.join(OUT, "metrics.json"))
    shutil.copy(os.path.join(figures_en.FIG_DIR, "monthly_signals.json"),
                os.path.join(OUT, "monthly_signals.json"))
    print("[paper_figures]", lines[0])
    print(f"[paper_figures] {len(PAPER)} paper figures + {len(EXTRA)} extra -> {OUT}")


def post(which="paper", only=None):
    """Post the built figures to the Telegram channel as a one-off, under a header
    that marks them as frozen paper figures. which: paper (1-12, paper captions),
    extra (figures outside this draft, e.g. the demand map), or all. only: optional
    set of paper figure numbers to send (e.g. {9, 11}); default all of them."""
    import send_telegram as ST
    token = os.environ.get(ST.TOKEN_ENV)
    if not token:
        print(f"SEND FAILED: ${ST.TOKEN_ENV} is not set")
        return 1
    chat = os.environ.get("TELEGRAM_CHAT_EN") or os.environ.get(ST.CHAT_ENV, ST.DEFAULT_CHAT)
    w = json.load(open(os.path.join(OUT, "metrics.json"), encoding="utf-8"))["window"]
    # the first snapshot (~01:00-04:00 Tashkent the next day) opens the window, so the
    # period covered starts the day after it: 30 Jun -> 30 Sep reads 1 Jul - 30 Sep
    import datetime as _dt
    first = (_dt.date.fromisoformat(w["date_min"]) + _dt.timedelta(days=1)).isoformat()
    header = ("📄 *Working-paper figures — "
              f"{pd_date(first)} to {pd_date(w['date_max'])}*\n"
              f"{w['n_days']} daily snapshots  ·  {w['n_listings']:,} apartments  "
              f"·  {w['n_obs']:,} listing-days")
    figs = []
    if which in ("paper", "all"):
        figs += [(stem, f"Figure {n}. {cap}") for n, name, stem, cap in PAPER
                 if not only or n in only]
    if which in ("extra", "all"):
        figs += [(f"Extra_{name[4:]}", cap) for name, cap in EXTRA]
    return ST.deliver(token, chat, OUT, figs, header, os.path.join(OUT, "_png"))


def pd_date(iso):
    """2026-09-24 -> 24 Sep 2026"""
    import datetime as _dt
    return _dt.date.fromisoformat(iso).strftime("%d %b %Y").lstrip("0")


if __name__ == "__main__":
    import sys
    if "--post" in sys.argv:        # --post [paper|extra|all] [--only 9,11]
        i = sys.argv.index("--post")
        which = sys.argv[i + 1] if len(sys.argv) > i + 1 else "paper"
        only = None
        if "--only" in sys.argv:
            j = sys.argv.index("--only")
            arg = sys.argv[j + 1] if len(sys.argv) > j + 1 else ""
            only = {int(x) for x in arg.replace(" ", "").split(",") if x}
        sys.exit(post(which, only))
    main()
