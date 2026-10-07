# -*- coding: utf-8 -*-
"""
paper_figures.py — build the working paper's figures, frozen at a cut-off date.
==============================================================================

    PANEL_END=2026-09-24 python paper_figures.py

Runs pipeline + figures_en on data up to PANEL_END, then copies the figures the
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

# (paper figure number, figure file, caption) — current draft (Uy_bozori, 7 Oct 2026)
PAPER = [
    (1, "fig_concentration_apartments", "Distribution of view velocity and concentration of attention"),
    (2, "fig_s1_dimensions", "View velocity across market segments"),
    (3, "fig_wedge_apartments", "The wedge between price and demand"),
    (4, "fig_intent_norm_districts", "Normalized purchase intent across districts"),
    (5, "fig_s2_dimensions", "Purchase intent across market segments"),
    (6, "fig_exit_apartments", "Market exit probability and its (weak) association with demand"),
    (7, "fig_exit_dims", "Market exit probability across segments"),
    (8, "fig_tom_dims", "Time on market (apartments)"),
    (9, "fig_metrics_panel_apartments", "Heatmap of the four demand signals"),
    (10, "fig_dynamics_districts", "Demand dynamics across three consecutive monthly windows "
                                   "(24th-to-24th): (a) demand reach and (b) click-through rate by district"),
    (11, "fig_supply_demand_bands", "Distribution of demand and supply across price segments"),
    (12, "fig_tightness_districts", "Market tightness across districts"),
]
EXTRA = [("fig_demand_map", "District demand map: (a) reach, (b) intensity (on Telegram; not in this draft)")]


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
    for n, name, cap in PAPER:
        export(os.path.join(figures_en.FIG_DIR, name + ".pdf"), f"Figure{n:02d}_{name[4:]}")
        lines.append(f"Figure {n}. {cap}")
    for name, cap in EXTRA:
        export(os.path.join(figures_en.FIG_DIR, name + ".pdf"), f"Extra_{name[4:]}")
        lines.append(f"Extra. {cap}")
    with open(os.path.join(OUT, "captions.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    shutil.copy(os.path.join(config.BUILD_DIR, "metrics.json"), os.path.join(OUT, "metrics.json"))
    print("[paper_figures]", lines[0])
    print(f"[paper_figures] {len(PAPER)} paper figures + {len(EXTRA)} extra -> {OUT}")


def post():
    """Post the built paper figures (1-12, paper captions) to the Telegram channel
    as a one-off, under a header that marks them as frozen paper figures."""
    import send_telegram as ST
    token = os.environ.get(ST.TOKEN_ENV)
    if not token:
        print(f"SEND FAILED: ${ST.TOKEN_ENV} is not set")
        return 1
    chat = os.environ.get("TELEGRAM_CHAT_EN") or os.environ.get(ST.CHAT_ENV, ST.DEFAULT_CHAT)
    w = json.load(open(os.path.join(OUT, "metrics.json"), encoding="utf-8"))["window"]
    end = w["date_max"]
    header = ("📄 *Working-paper figures — data to "
              f"{pd_date(end)}*\n{w['date_min']} → {end}  ·  {w['n_days']} days  "
              f"·  {w['n_listings']:,} apartments  ·  {w['n_obs']:,} listing-days")
    figs = [(f"Figure{n:02d}_{name[4:]}", f"Figure {n}. {cap}") for n, name, cap in PAPER]
    return ST.deliver(token, chat, OUT, figs, header, os.path.join(OUT, "_png"))


def pd_date(iso):
    """2026-09-24 -> 24 Sep 2026"""
    import datetime as _dt
    return _dt.date.fromisoformat(iso).strftime("%d %b %Y").lstrip("0")


if __name__ == "__main__":
    import sys
    if "--post" in sys.argv:
        sys.exit(post())
    main()
