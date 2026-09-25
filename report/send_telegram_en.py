# -*- coding: utf-8 -*-
"""
send_telegram_en.py — post the ENGLISH figure set (figures_en/) to Telegram.
============================================================================

Mirror of send_telegram.py for the English figures. Reuses that module's Bot
API helpers and delivery loop; only the figure directory, captions and header
differ. All 13 English figures are sent (PNG preview + vector PDF each).

Env:
  TELEGRAM_BOT_TOKEN   bot token (shared with the Uzbek sender)
  TELEGRAM_CHAT_EN     channel for the English set; falls back to TELEGRAM_CHAT,
                       then "@chart_automation" (i.e. same channel by default)
"""
import json
import os
import sys

import send_telegram as ST

HERE = os.path.dirname(__file__)
FIG_DIR = os.path.join(HERE, "figures_en")
PNG_DIR = os.path.join(HERE, "figures_en_png")
METRICS = os.path.join(HERE, "build", "metrics.json")
CHAT_EN_ENV = "TELEGRAM_CHAT_EN"

# exactly the paper's figures, in the paper's order, with the paper's captions
# (Housing_Demand draft: Figures 1-12; the hedonic figure is not in the paper)
FIGURES = [
    ("fig_concentration_apartments", "Figure 1. Distribution of view velocity and concentration of attention"),
    ("fig_s1_dimensions", "Figure 2. View velocity across market segments"),
    ("fig_wedge_apartments", "Figure 3. The wedge between price and demand"),
    ("fig_demand_map", "Figure 4. Geographic distribution of demand reach in Tashkent"),
    ("fig_intent_norm_districts", "Figure 5. Normalized purchase intent across districts"),
    ("fig_s2_dimensions", "Figure 6. Purchase intent across market segments"),
    ("fig_exit_apartments", "Figure 7. Demand of exited vs. surviving listings; exit timing around the 43-day term"),
    ("fig_exit_dims", "Figure 8. Monthly exit probability by district and room count"),
    ("fig_tom_dims", "Figure 9. Time on market (apartments)"),
    ("fig_metrics_panel_apartments", "Figure 10. Heatmap of the four demand signals"),
    ("fig_supply_demand_bands", "Figure 11. Distribution of demand and supply across price segments"),
    ("fig_tightness_districts", "Figure 12. Market tightness across districts"),
]


def _header():
    if not os.path.exists(METRICS):
        return "Uybor apartments — paper figures (English)"
    w = json.load(open(METRICS, encoding="utf-8"))["window"]
    return ("\U0001F4CA *Uybor apartments — working-paper figures (English)*\n"
            f"{w['date_min']} → {w['date_max']}  ·  "
            f"{w['n_listings']:,} listings  ·  {w['n_days']} snapshots")


def main(argv=None):
    token = os.environ.get(ST.TOKEN_ENV)
    if not token:
        print(f"SEND FAILED: ${ST.TOKEN_ENV} is not set", file=sys.stderr)
        return 1
    chat = os.environ.get(CHAT_EN_ENV) or os.environ.get(ST.CHAT_ENV, ST.DEFAULT_CHAT)
    return ST.deliver(token, chat, FIG_DIR, FIGURES, _header(), PNG_DIR)


if __name__ == "__main__":
    sys.exit(main())
