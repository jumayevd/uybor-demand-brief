# -*- coding: utf-8 -*-
"""
send_telegram_en.py — post the ENGLISH figure set (figures_en/) to Telegram.
============================================================================

Mirror of send_telegram.py for the English figures. Reuses that module's Bot
API helpers and delivery loop; only the figure directory, captions and header
differ. The paper's figures (13 in the current draft) are sent (PNG preview + vector PDF each).

Env:
  TELEGRAM_BOT_TOKEN   bot token (shared with the Uzbek sender)
  TELEGRAM_CHAT_EN     channel for the English set; falls back to TELEGRAM_CHAT,
                       then "@chart_automation" (i.e. same channel by default)
"""
import json
import os
import sys

import send_telegram as ST
from paper_figures import PAPER

HERE = os.path.dirname(__file__)
FIG_DIR = os.path.join(HERE, "figures_en")
PNG_DIR = os.path.join(HERE, "figures_en_png")
METRICS = os.path.join(HERE, "build", "metrics.json")
CHAT_EN_ENV = "TELEGRAM_CHAT_EN"

# exactly the working paper's figures, in its order and with its captions.
# Single source of truth: paper_figures.PAPER (update it when the draft changes).
FIGURES = [(name, f"Figure {n}. {cap}") for n, name, _stem, cap in PAPER]


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
