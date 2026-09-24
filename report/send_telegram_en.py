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

# fixed send order + English caption per figure (11 paper figures + tightness + hedonic)
FIGURES = [
    ("fig_concentration_apartments", "Demand-velocity distribution & top-10% share"),
    ("fig_s1_dimensions", "Velocity by rooms / building type / weekday"),
    ("fig_wedge_apartments", "Velocity & intent by price quintile"),
    ("fig_demand_map", "Demand map: bubble size = reach (total new views)"),
    ("fig_intent_norm_districts", "Normalized intent by district"),
    ("fig_s2_dimensions", "Intent by rooms / weekday"),
    ("fig_exit_apartments", "Exit-velocity gap & 43-day decomposition"),
    ("fig_exit_dims", "Exit rate by district / rooms"),
    ("fig_tom_dims", "Time on market by district / rooms"),
    ("fig_metrics_panel_apartments", "Four demand signals — district heatmap"),
    ("fig_supply_demand_bands", "Supply vs demand by price band"),
    ("fig_tightness_districts", "Market tightness by district"),
    ("fig_hedonic_results", "Hedonic results: paid-promotion effect & R²"),
]


def _header():
    if not os.path.exists(METRICS):
        return "Uybor apartments — daily demand figures (English)"
    w = json.load(open(METRICS, encoding="utf-8"))["window"]
    return ("\U0001F4CA *Uybor apartments — daily demand figures (English)*\n"
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
