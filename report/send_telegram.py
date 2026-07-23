# -*- coding: utf-8 -*-
"""
send_telegram.py — rasterize the built figures to PNG and post them to a
Telegram channel via the Bot API.
=======================================================================

Each fig_*.pdf in figures/ is rendered to a PNG and sent as a photo to the
channel, in a fixed order, with a human caption. A leading header message
gives the run's window/listing count from build/metrics.json.

Env:
  TELEGRAM_BOT_TOKEN   bot token from @BotFather (never hardcode / never logged)
  TELEGRAM_CHAT        channel, e.g. "@chart_automation" (default below)

Prereqs (one-time, done by you):
  1. Create a bot with @BotFather -> get the token.
  2. Add that bot to the channel as an ADMIN with "Post messages" permission.

Fail-loud: any HTTP error from Telegram aborts non-zero with the API message.
"""
import json
import os
import sys
import time

import fitz  # PyMuPDF
import requests

TOKEN_ENV = "TELEGRAM_BOT_TOKEN"
CHAT_ENV = "TELEGRAM_CHAT"
DEFAULT_CHAT = "@chart_automation"

HERE = os.path.dirname(__file__)
FIG_DIR = os.path.join(HERE, "figures")
PNG_DIR = os.path.join(HERE, "figures_png")
METRICS = os.path.join(HERE, "build", "metrics.json")

# fixed send order + caption per figure (only those present are sent)
FIGURES = [
    ("fig_evidence_map", "Four listing signals validated as demand proxies"),
    ("fig_concentration_apartments", "Demand velocity: distribution & top-decile share"),
    ("fig_s1_dimensions", "View velocity by rooms / build type / day-of-week"),
    ("fig_funnel_apartments", "Attention funnel: views → clicks → favorites"),
    ("fig_wedge_apartments", "Velocity vs intent by price quintile"),
    ("fig_intent_norm_districts", "Normalized click/favorite incidence by district"),
    ("fig_s2_dimensions", "Intent by rooms / day-of-week"),
    ("fig_exit_apartments", "Exit velocity gap + renewal-wall decomposition"),
    ("fig_exit_dims", "Exit rate by district / rooms"),
    ("fig_tom_dims", "Time-on-market wall + stock age by district / rooms"),
    ("fig_metrics_panel_apartments", "District heatmap of the four demand signals"),
    ("fig_supply_demand_bands", "Supply vs demand by price band"),
    ("fig_demand_map", "District demand bubble map + ranked panel"),
]

API = "https://api.telegram.org/bot{token}/{method}"
RASTER_SCALE = 2.5  # PDF points -> px multiplier


def _rasterize(pdf_path, png_path):
    doc = fitz.open(pdf_path)
    pix = doc[0].get_pixmap(matrix=fitz.Matrix(RASTER_SCALE, RASTER_SCALE))
    pix.save(png_path)
    doc.close()


def _post(token, method, data=None, files=None):
    r = requests.post(API.format(token=token, method=method),
                      data=data, files=files, timeout=60)
    body = r.json()
    if not body.get("ok"):
        raise RuntimeError(f"Telegram {method} failed: "
                           f"{body.get('error_code')} {body.get('description')}")
    return body["result"]


def _header():
    if not os.path.exists(METRICS):
        return "Uybor apartments — daily demand figures"
    w = json.load(open(METRICS, encoding="utf-8"))["window"]
    return ("📊 *Uybor apartments — daily demand figures*\n"
            f"{w['date_min']} → {w['date_max']}  ·  "
            f"{w['n_listings']:,} listings  ·  {w['n_days']} snapshots")


def main(argv=None):
    token = os.environ.get(TOKEN_ENV)
    chat = os.environ.get(CHAT_ENV, DEFAULT_CHAT)
    if not token:
        print(f"SEND FAILED: ${TOKEN_ENV} is not set", file=sys.stderr)
        return 1

    present = [(n, cap) for (n, cap) in FIGURES
               if os.path.exists(os.path.join(FIG_DIR, n + ".pdf"))]
    if not present:
        print(f"SEND FAILED: no figures found in {FIG_DIR}", file=sys.stderr)
        return 1

    os.makedirs(PNG_DIR, exist_ok=True)
    try:
        _post(token, "sendMessage",
              data={"chat_id": chat, "text": _header(), "parse_mode": "Markdown"})
        for name, caption in present:
            png = os.path.join(PNG_DIR, name + ".png")
            _rasterize(os.path.join(FIG_DIR, name + ".pdf"), png)
            with open(png, "rb") as fh:
                _post(token, "sendPhoto",
                      data={"chat_id": chat, "caption": caption},
                      files={"photo": fh})
            time.sleep(1)  # stay well under Telegram's rate limits
    except Exception as exc:
        print(f"SEND FAILED: {exc}", file=sys.stderr)
        return 1

    print(f"[telegram] sent {len(present)} figures to {chat}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
